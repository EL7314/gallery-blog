from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='分类名')
    slug = models.SlugField(unique=True, verbose_name='标识')

    class Meta:
        verbose_name = '分类'
        verbose_name_plural = '分类'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog:category', args=[self.slug])


class Post(models.Model):
    COVER_CHOICES = [
        ('top', '封面上，标题下'),
        ('left', '封面左，标题右'),
        ('right', '标题左，封面右'),
        ('bg', '封面全宽背景'),
    ]
    title = models.CharField(max_length=200, verbose_name='标题')
    slug = models.SlugField(unique=True, verbose_name='标识')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='分类', related_name='posts')
    content = models.TextField(blank=True, verbose_name='正文')
    cover_layout = models.CharField(max_length=20, choices=COVER_CHOICES, default='top', verbose_name='封面布局')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_published = models.BooleanField(default=True, verbose_name='已发布')
    order = models.IntegerField(default=0, verbose_name='排序')

    class Meta:
        verbose_name = '文章'
        verbose_name_plural = '文章'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:detail', args=[self.slug])

    @property
    def first_image(self):
        cover = self.images.filter(is_cover=True).first()
        if cover:
            return cover.image
        first = self.images.first()
        return first.image if first else None


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images', verbose_name='所属文章')
    image = models.ImageField(upload_to='images/%Y/%m/', verbose_name='图片')
    caption = models.CharField(max_length=200, blank=True, verbose_name='图注')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_cover = models.BooleanField(default=False, verbose_name='封面图')

    class Meta:
        verbose_name = '文章图片'
        verbose_name_plural = '文章图片'
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.post.title} - 图片{self.order}'


class ContentBlock(models.Model):
    """内容块：段落文本或图片，支持单独布局"""
    BLOCK_TEXT = 'text'
    BLOCK_IMAGE = 'image'
    BLOCK_TYPE_CHOICES = [
        (BLOCK_TEXT, '文字'),
        (BLOCK_IMAGE, '图片'),
    ]
    LAYOUT_CHOICES = [
        ('top-bottom', '上图下文'),
        ('bottom-top', '上文下图'),
        ('left-right', '左图右文'),
        ('right-left', '左文右图'),
        ('float-left', '文字环绕'),
        ('full', '仅内容'),
    ]

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='blocks', verbose_name='所属文章')
    block_type = models.CharField(max_length=10, choices=BLOCK_TYPE_CHOICES, default=BLOCK_TEXT, verbose_name='块类型')
    subtitle = models.CharField(max_length=200, blank=True, verbose_name='小标题')
    content = models.TextField(blank=True, verbose_name='文字内容')
    image = models.ForeignKey(PostImage, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name='引用图片')
    layout = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default='full', verbose_name='图文布局')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')

    class Meta:
        verbose_name = '内容块'
        verbose_name_plural = '内容块'
        ordering = ['order']

    def __str__(self):
        return f'{self.post.title} - 块{self.order} ({self.get_block_type_display()})'


class SiteSetting(models.Model):
    background_image = models.ImageField(upload_to='settings/', blank=True, verbose_name='背景壁纸')

    class Meta:
        verbose_name = '站点设置'
        verbose_name_plural = '站点设置'

    def __str__(self):
        return '站点设置'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
