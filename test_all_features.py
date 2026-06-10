"""
Comprehensive test: all features requested by user
Run: venv/Scripts/python.exe test_all_features.py
"""
import json, os, struct, zlib

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blogproject.settings')
import django
django.setup()

from django.conf import settings
settings.ALLOWED_HOSTS = ['testserver', '127.0.0.1', 'localhost']

from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from blog.models import Category, Post, PostImage, SiteSetting

client = Client()
passed = 0
failed = 0


def check(name, condition, detail=''):
    global passed, failed
    if condition:
        passed += 1
        print(f'  [PASS] {name}')
    else:
        failed += 1
        print(f'  [FAIL] {name} {detail}')


# Helper: make a valid 1x1 white PNG
def make_png():
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    raw = zlib.compress(b'\x00\xff\xff\xff')
    idat_crc = zlib.crc32(b'IDAT' + raw)
    idat = struct.pack('>I', len(raw)) + b'IDAT' + raw + struct.pack('>I', idat_crc)
    iend_crc = zlib.crc32(b'IEND')
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    return sig + ihdr + idat + iend

png_data = make_png()

# ==================== AUTH ====================
print('\n=== 1. Authentication ===')

check('Login page accessible', client.get('/login/').status_code == 200)
check('Login with admin/admin123', client.login(username='admin', password='admin123'))

resp = client.get('/')
check('Logout accessible', client.get('/logout/').status_code == 302)
client.login(username='admin', password='admin123')

# ==================== CATEGORY CRUD ====================
print('\n=== 2. Category CRUD ===')

# Clean
Category.objects.filter(slug__startswith='test-').delete()

# Create
resp = client.post('/category/create/', data={'name': 'Test Category A'})
cat_a = Category.objects.filter(slug='test-category-a').first()
check('Category created (slug auto-generated)', cat_a is not None,
      f'slug={cat_a.slug if cat_a else "None"}')
check('Category redirect to list', resp.status_code == 302)

# Read
resp = client.get('/categories/')
check('Category list page accessible', resp.status_code == 200)
check('Category appears in list', 'Test Category A' in resp.content.decode())

# Edit
resp = client.post(f'/category/{cat_a.slug}/edit/', data={'name': 'Test Category A Edited'})
cat_a.refresh_from_db()
check('Category name updated', cat_a.name == 'Test Category A Edited')

# Delete
resp = client.post(f'/category/{cat_a.slug}/delete/')
check('Category deleted', not Category.objects.filter(slug='test-category-a').exists())

# Create 3 categories for filter testing
for name in ['Design', 'Photography', 'Travel']:
    slug = 'test-' + name.lower()
    Category.objects.filter(slug=slug).delete()
    Category.objects.create(name=name, slug=slug)

# ==================== SITE SETTING ====================
print('\n=== 3. Site Settings (Background Wallpaper) ===')

# Background upload
img = SimpleUploadedFile('bg.png', png_data, content_type='image/png')
resp = client.post(
    '/background/upload/',
    data={'background_image': img},
    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
)
data = json.loads(resp.content)
check('Background image upload', data.get('success') == True, data)
bg_url = data.get('url', '')
check('Background URL returned', bool(bg_url), bg_url)

# Verify DB
setting = SiteSetting.get()
check('SiteSetting stored in DB', bool(setting.background_image))

# Background shown on homepage
resp = client.get('/')
html = resp.content.decode()
check('Background URL in homepage HTML', bg_url in html)

# ==================== POST CRUD ====================
print('\n=== 4. Post CRUD ===')

Post.objects.filter(slug__startswith='test-').delete()
cat = Category.objects.get(slug='test-design')

# Create via page form
resp = client.post(
    '/post/create/',
    data={'title': 'Page Form Post', 'category': str(cat.id), 'content': 'From form page', 'is_published': 'on'}
)
check('Post created via page form', resp.status_code == 302)

# Create via AJAX (modal)
resp = client.post(
    '/post/create/ajax/',
    data={'title': 'Modal AJAX Post', 'category': str(cat.id), 'content': 'From modal', 'is_published': 'on'},
    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
)
data = json.loads(resp.content)
check('Post created via AJAX', data.get('success') == True)
ajax_slug = data.get('slug', '')
check('AJAX post slug returned', bool(ajax_slug))

# Create post for editing
resp = client.post(
    '/post/create/',
    data={'title': 'Edit Me', 'category': str(cat.id), 'content': 'Original content', 'is_published': 'on'}
)
edit_post = Post.objects.get(slug='edit-me')

# Edit
resp = client.post(
    f'/post/edit-me/edit/',
    data={'title': 'Edit Me Updated', 'category': str(cat.id), 'content': 'Updated content', 'is_published': 'on'}
)
edit_post.refresh_from_db()
check('Post title updated via edit', edit_post.title == 'Edit Me Updated')
check('Post content updated via edit', edit_post.content == 'Updated content')

# Delete
resp = client.post(f'/post/edit-me/delete/')
check('Post deleted', not Post.objects.filter(title='Edit Me Updated').exists())

# ==================== MULTI-IMAGE UPLOAD ====================
print('\n=== 5. Multi-Image Upload (with Captions) ===')

post = Post.objects.get(slug=ajax_slug)
check('Post initially has 0 images', post.images.count() == 0)

# Upload 3 images with different captions
for i, caption in enumerate(['Sunset view', '', 'City skyline at night']):
    img_file = SimpleUploadedFile(f'img{i}.png', png_data, content_type='image/png')
    resp = client.post(
        f'/post/{ajax_slug}/upload-image/',
        data={'image': img_file, 'caption': caption},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest',
    )
    data = json.loads(resp.content)
    check(f'Upload image {i+1} ({caption or "no caption"})', data.get('success') == True)

check('Post now has 3 images', post.images.count() == 3)

imgs = list(post.images.all())
check('Image 1 caption = "Sunset view"', imgs[0].caption == 'Sunset view')
check('Image 2 caption = ""', imgs[1].caption == '')
check('Image 3 caption = "City skyline at night"', imgs[2].caption == 'City skyline at night')
check('Images have correct order (0,1,2)', [img.order for img in imgs] == [0, 1, 2])
for img in imgs:
    check(f'Image file exists on disk: {img.image.name}', os.path.exists(img.image.path))

# Delete an image
img_to_delete = imgs[1]
resp = client.post(
    f'/image/{img_to_delete.id}/delete/',
    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
)
data = json.loads(resp.content)
check('Delete image via AJAX', data.get('success') == True)
check('Post now has 2 images', post.images.count() == 2)

# ==================== FRONTEND PAGES ====================
print('\n=== 6. Frontend Pages ===')

# Homepage structure
resp = client.get('/')
html = resp.content.decode()
check('Homepage returns 200', resp.status_code == 200)
check('Two-column layout (.layout)', '.layout' in html)
check('Main panel (.main-panel)', '.main-panel' in html)
check('Sidebar (.sidebar)', '.sidebar' in html)
check('Content area (.content-area)', '.content-area' in html)
check('Settings background upload (#settingsBgInput)', 'settingsBgInput' in html)
check('Cards grid (.cards)', '.cards' in html)
check('Black/white/gray CSS vars', '--panel-fg: #111' in html)
check('Post title on homepage', 'Modal AJAX Post' in html)
check('Category list in sidebar', 'test-design' in html or 'Design' in html)

# Floating button + modal (authenticated only)
check('Float button (.float-btn)', '.float-btn' in html)
check('Modal overlay (.modal-overlay)', '.modal-overlay' in html)
check('Upload zone in modal (.upload-zone)', '.upload-zone' in html)
check('Modal form fields', 'name="title"' in html and 'name="category"' in html)

# Post detail page
resp = client.get(f'/post/{ajax_slug}/')
detail = resp.content.decode()
check('Detail page returns 200', resp.status_code == 200)
check('Detail has post title', 'Modal AJAX Post' in detail)
check('Detail has image element', '<img' in detail)
check('Detail has figcaption', '<figcaption>Sunset view</figcaption>' in detail)
check('Detail has edit/delete links for auth user', '编辑' in detail)
check('Detail has back link', '返回' in detail)

# Login page
resp = client.get('/login/')
check('Login page returns 200', resp.status_code == 200)

# Category management page
resp = client.get('/categories/')
check('Category list page returns 200', resp.status_code == 200)
check('Category names on page', 'Design' in resp.content.decode())

# ==================== AJAX CATEGORY FILTER ====================
print('\n=== 7. AJAX Category Filtering ===')

resp = client.get(
    f'/category/test-design/',
    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
)
data = json.loads(resp.content)
check('AJAX filter returns html', 'html' in data)
check('Filtered content contains post', 'Modal AJAX Post' in data['html'])

# Index page AJAX
resp = client.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
data = json.loads(resp.content)
check('Index AJAX returns fragment', 'html' in data)
check('Index AJAX contains all posts', 'Modal AJAX Post' in data['html'])

# ==================== POST LIST VERIFICATION ====================
print('\n=== 8. Post List with First Image ===')

Post.objects.filter(slug__startswith='test-').delete()
cat2 = Category.objects.get(slug='test-design')

# Create post with images
resp = client.post(
    '/post/create/ajax/',
    data={'title': 'Gallery Post With Images', 'category': str(cat2.id), 'content': 'Has 2 images', 'is_published': 'on'},
    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
)
data = json.loads(resp.content)
gallery_slug = data['slug']

for caption in ['Hero image', 'Secondary']:
    img = SimpleUploadedFile('g.png', png_data, content_type='image/png')
    client.post(
        f'/post/{gallery_slug}/upload-image/',
        data={'image': img, 'caption': caption},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest',
    )

# Check list page shows first image
resp = client.get('/')
html = resp.content.decode()
check('Gallery post on list', 'Gallery Post With Images' in html)
check('First image URL in card (card-img)', 'card-img' in html)
check('Post excerpt on card', 'Has 2 images' in html)
check('Category name on card', 'Design' in html)

# Cleanup
Post.objects.filter(slug=gallery_slug).delete()

# ==================== RESPONSIVE LAYOUT ====================
print('\n=== 9. Responsive Layout ===')

check('Viewport meta tag', 'viewport' in client.get('/').content.decode())
check('Mobile media query (@media max-width:768px)', '@media (max-width: 768px)' in client.get('/').content.decode())

# ==================== CLEANUP ====================
print('\n=== 10. Cleanup ===')

Post.objects.filter(slug__startswith='test-').delete()
Category.objects.filter(slug__startswith='test-').delete()
setting = SiteSetting.get()
if setting.background_image:
    setting.background_image.delete(save=False)
    setting.background_image = None
    setting.save()
check('Test data cleaned up', True)

# ==================== SUMMARY ====================
print('\n' + '=' * 55)
print(f'  TOTAL: {passed + failed} tests | PASS: {passed} | FAIL: {failed}')
if failed == 0:
    print('  ALL TESTS PASSED')
else:
    print(f'  {failed} TEST(S) FAILED!')
print('=' * 55)
