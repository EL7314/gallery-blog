import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from .models import Post, Category, PostImage, SiteSetting, ContentBlock
from .forms import PostForm, PostImageForm, CategoryForm, BackgroundForm, ContentBlockForm


# ── 公开页面 ──

def post_list(request):
    category_slug = request.GET.get('category')
    query = request.GET.get('q', '').strip()
    posts = Post.objects.filter(is_published=True).select_related('category').prefetch_related('images')
    categories = Category.objects.all()
    setting = SiteSetting.get()

    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    if query:
        posts = posts.filter(title__icontains=query)

    ctx = {
        'posts': posts,
        'categories': categories,
        'current_category': category_slug,
        'search_query': query,
        'setting': setting,
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('blog/_post_cards.html', ctx, request)
        return JsonResponse({'html': html})

    return render(request, 'blog/post_list.html', ctx)


def search_posts(request):
    """Dedicated search endpoint for AJAX"""
    query = request.GET.get('q', '').strip()
    posts = Post.objects.filter(is_published=True).select_related('category').prefetch_related('images')
    categories = Category.objects.all()
    setting = SiteSetting.get()

    if query:
        posts = posts.filter(title__icontains=query)

    ctx = {
        'posts': posts,
        'categories': categories,
        'search_query': query,
        'setting': setting,
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('blog/_post_cards.html', ctx, request)
        return JsonResponse({'html': html})

    return render(request, 'blog/post_list.html', ctx)


def post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.prefetch_related('images'),
        slug=slug, is_published=True
    )
    categories = Category.objects.all()
    setting = SiteSetting.get()
    return render(request, 'blog/post_detail.html', {
        'post': post,
        'categories': categories,
        'setting': setting,
    })


# ── 登录 ──

def login_view(request):
    categories = Category.objects.all()
    setting = SiteSetting.get()
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    return render(request, 'blog/login.html', {
        'form': form,
        'categories': categories,
        'setting': setting,
    })


def logout_view(request):
    auth_logout(request)
    return redirect('blog:index')


# ── 文章管理 ──

@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            base_slug = slugify(post.title)
            if not base_slug:
                base_slug = 'post'
            post.slug = base_slug
            base = post.slug
            n = 1
            while Post.objects.filter(slug=post.slug).exists():
                post.slug = f'{base}-{n}'
                n += 1
            # Ensure published by default when checkbox not in form
            if 'is_published' not in request.POST:
                post.is_published = True
            post.save()
            # Handle cover image
            cover_file = form.cleaned_data.get('cover_image')
            if cover_file:
                img = PostImage(post=post, image=cover_file, caption='', is_cover=True, order=0)
                img.save()
            return redirect('blog:post_edit', slug=post.slug)
    else:
        form = PostForm()
    categories = Category.objects.all()
    setting = SiteSetting.get()
    return render(request, 'blog/post_form.html', {
        'form': form,
        'action': '创建',
        'categories': categories,
        'setting': setting,
    })


@login_required
def post_edit(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            # Handle cover image
            cover_file = form.cleaned_data.get('cover_image')
            if cover_file:
                # Replace old cover
                PostImage.objects.filter(post=post, is_cover=True).update(is_cover=False)
                img = PostImage(post=post, image=cover_file, caption='', is_cover=True, order=0)
                img.save()
            return redirect('blog:detail', slug=post.slug)
    else:
        form = PostForm(instance=post)
    categories = Category.objects.all()
    setting = SiteSetting.get()
    return render(request, 'blog/post_form.html', {
        'form': form,
        'post': post,
        'action': '编辑',
        'categories': categories,
        'setting': setting,
    })


@login_required
@require_POST
def post_delete(request, slug):
    post = get_object_or_404(Post, slug=slug)
    post.delete()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('blog:index')


@login_required
@require_POST
def post_reorder(request):
    """收到 JSON: {order: [{id: 1}, {id: 2}, ...]}"""
    data = json.loads(request.body)
    for item in data.get('order', []):
        Post.objects.filter(id=item['id']).update(order=item.get('order', 0))
    return JsonResponse({'success': True})


# ── AJAX 创建文章 ──

@login_required
@require_POST
def ajax_create_post(request):
    form = PostForm(request.POST)
    if form.is_valid():
        post = form.save(commit=False)
        base_slug = slugify(post.title)
        if not base_slug:
            base_slug = 'post'
        post.slug = base_slug
        base = post.slug
        n = 1
        while Post.objects.filter(slug=post.slug).exists():
            post.slug = f'{base}-{n}'
            n += 1
        post.save()
        return JsonResponse({
            'success': True,
            'slug': post.slug,
        })
    return JsonResponse({'success': False, 'errors': form.errors.as_json()})


# ── AJAX 图片上传 ──

@login_required
@require_POST
def ajax_upload_image(request, slug):
    post = get_object_or_404(Post, slug=slug)
    form = PostImageForm(request.POST, request.FILES)
    if form.is_valid():
        img = form.save(commit=False)
        img.post = post
        img.order = post.images.count()
        img.save()
        return JsonResponse({
            'success': True,
            'id': img.id,
            'url': img.image.url,
            'caption': img.caption,
            'is_cover': img.is_cover,
        })
    return JsonResponse({'success': False, 'errors': form.errors})


@login_required
@require_POST
def ajax_delete_image(request, image_id):
    img = get_object_or_404(PostImage, id=image_id)
    img.image.delete(save=False)
    img.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def ajax_set_cover(request, image_id):
    img = get_object_or_404(PostImage, id=image_id)
    # Clear existing cover in this post
    PostImage.objects.filter(post=img.post).update(is_cover=False)
    # Set new cover
    img.is_cover = True
    img.save()
    return JsonResponse({'success': True})


# ── 背景壁纸上传 ──

@login_required
@require_POST
def upload_background(request):
    setting = SiteSetting.get()
    form = BackgroundForm(request.POST, request.FILES, instance=setting)
    if form.is_valid():
        form.save()
        return JsonResponse({
            'success': True,
            'url': setting.background_image.url,
        })
    return JsonResponse({'success': False})


# ── AJAX 内容块管理 ──

@login_required
@require_POST
def block_create(request, slug):
    post = get_object_or_404(Post, slug=slug)
    form = ContentBlockForm(request.POST)
    if form.is_valid():
        block = form.save(commit=False)
        block.post = post
        block.order = post.blocks.count()
        block.save()
        return JsonResponse({'success': True, 'id': block.id, 'block_type': block.block_type,
                             'content': block.content, 'layout': block.layout,
                             'image_url': block.image.image.url if block.image else ''})
    return JsonResponse({'success': False, 'errors': str(form.errors)})


@login_required
@require_POST
def block_update(request, block_id):
    block = get_object_or_404(ContentBlock, id=block_id)
    form = ContentBlockForm(request.POST, instance=block)
    if form.is_valid():
        updated = form.save()
        return JsonResponse({'success': True, 'content': updated.content, 'layout': updated.layout})
    return JsonResponse({'success': False, 'errors': str(form.errors)})


@login_required
@require_POST
def block_delete(request, block_id):
    block = get_object_or_404(ContentBlock, id=block_id)
    block.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def block_reorder(request, slug):
    """reorder: JSON [{id: N, order: M}, ...]"""
    post = get_object_or_404(Post, slug=slug)
    data = json.loads(request.body)
    for item in data:
        ContentBlock.objects.filter(id=item['id'], post=post).update(order=item['order'])
    return JsonResponse({'success': True})


# ── 分类管理 ──

@login_required
def category_list(request):
    categories = Category.objects.all()
    setting = SiteSetting.get()
    return render(request, 'blog/category_list.html', {
        'categories': categories,
        'setting': setting,
    })


@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.slug = slugify(cat.name)
            cat.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'name': cat.name, 'slug': cat.slug})
            return redirect('blog:category_list')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': str(form.errors)})
    else:
        form = CategoryForm()
    categories = Category.objects.all()
    setting = SiteSetting.get()
    return render(request, 'blog/category_form.html', {
        'form': form,
        'action': '创建',
        'categories': categories,
        'setting': setting,
    })


@login_required
def category_edit(request, slug):
    cat = get_object_or_404(Category, slug=slug)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'name': cat.name, 'slug': cat.slug})
            return redirect('blog:category_list')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': str(form.errors)})
    else:
        form = CategoryForm(instance=cat)
    categories = Category.objects.all()
    setting = SiteSetting.get()
    return render(request, 'blog/category_form.html', {
        'form': form,
        'action': '编辑',
        'categories': categories,
        'setting': setting,
    })


@login_required
@require_POST
def category_delete(request, slug):
    cat = get_object_or_404(Category, slug=slug)
    cat.delete()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('blog:category_list')


def category_posts(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = category.posts.filter(is_published=True).prefetch_related('images')
    categories = Category.objects.all()
    setting = SiteSetting.get()
    ctx = {
        'posts': posts,
        'categories': categories,
        'current_category': slug,
        'setting': setting,
    }
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('blog/_post_cards.html', ctx, request)
        return JsonResponse({'html': html})
    return render(request, 'blog/post_list.html', ctx)
