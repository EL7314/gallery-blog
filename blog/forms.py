from django import forms
from .models import Post, PostImage, Category, SiteSetting, ContentBlock


class PostForm(forms.ModelForm):
    cover_image = forms.ImageField(required=False, label='封面图片')
    class Meta:
        model = Post
        fields = ['title', 'category', 'content', 'is_published', 'cover_layout']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'input', 'placeholder': '标题'}),
            'category': forms.Select(attrs={'class': 'input'}),
            'content': forms.Textarea(attrs={'class': 'textarea', 'rows': 6, 'placeholder': '正文内容...'}),
            'cover_layout': forms.Select(attrs={'class': 'input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cover_layout'].required = False


class PostImageForm(forms.ModelForm):
    class Meta:
        model = PostImage
        fields = ['image', 'caption']


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
        }


class ContentBlockForm(forms.ModelForm):
    class Meta:
        model = ContentBlock
        fields = ['block_type', 'subtitle', 'content', 'image', 'layout']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['subtitle'].required = False


class BackgroundForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = ['background_image']
