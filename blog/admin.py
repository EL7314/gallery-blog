from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Post, PostImage


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1
    fields = ['image', 'caption', 'order']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ['name', 'slug']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'created_at', 'is_published']
    list_filter = ['category', 'is_published', 'created_at']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    inlines = [PostImageInline]
