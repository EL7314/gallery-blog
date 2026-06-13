from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # 公开
    path('', views.post_list, name='index'),
    path('search/', views.search_posts, name='search'),

    # 分类管理（具体路由在 <slug> 之前）
    path('categories/', views.category_list, name='category_list'),
    path('category/create/', views.category_create, name='category_create'),
    path('category/<slug:slug>/edit/', views.category_edit, name='category_edit'),
    path('category/<slug:slug>/delete/', views.category_delete, name='category_delete'),
    path('category/<slug:slug>/', views.category_posts, name='category'),

    # 登录
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # 文章管理（create/ajax 在 <slug> 之前）
    path('post/create/', views.post_create, name='post_create'),
    path('post/create/ajax/', views.ajax_create_post, name='ajax_create_post'),
    path('post/reorder/', views.post_reorder, name='post_reorder'),
    path('post/<slug:slug>/pin/', views.post_toggle_pin, name='post_toggle_pin'),
    path('post/<slug:slug>/edit/', views.post_edit, name='post_edit'),
    path('post/<slug:slug>/delete/', views.post_delete, name='post_delete'),
    path('post/<slug:slug>/upload-image/', views.ajax_upload_image, name='ajax_upload'),
    # 文章详情 slug 路由放最后
    path('post/<slug:slug>/', views.post_detail, name='detail'),

    # 图片操作
    path('image/<int:image_id>/delete/', views.ajax_delete_image, name='ajax_delete_image'),
    path('image/<int:image_id>/cover/', views.ajax_set_cover, name='ajax_set_cover'),

    # 内容块管理
    path('block/<slug:slug>/create/', views.block_create, name='block_create'),
    path('block/<int:block_id>/update/', views.block_update, name='block_update'),
    path('block/<int:block_id>/delete/', views.block_delete, name='block_delete'),
    path('block/<slug:slug>/reorder/', views.block_reorder, name='block_reorder'),

    # 背景壁纸
    path('background/upload/', views.upload_background, name='upload_background'),
]
