import uuid
from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from tinymce.models import HTMLField
from RattelBackend.cache import invalidate_cache


class BlogCategory(models.Model):
    name = models.CharField(max_length=120, unique=True, verbose_name=_('Name'))
    slug = models.SlugField(max_length=140, unique=True, verbose_name=_('Slug'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    class Meta:
        verbose_name = _('Blog Category')
        verbose_name_plural = _('Blog Categories')
        ordering = ('name',)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invalidate_cache('blog_meta')
        invalidate_cache('blog_list')


class BlogTag(models.Model):
    name = models.CharField(max_length=80, unique=True, verbose_name=_('Name'))
    slug = models.SlugField(max_length=100, unique=True, verbose_name=_('Slug'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    class Meta:
        verbose_name = _('Blog Tag')
        verbose_name_plural = _('Blog Tags')
        ordering = ('name',)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invalidate_cache('blog_meta')
        invalidate_cache('blog_list')


class BlogPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, verbose_name=_('Blog ID'))
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    slug = models.SlugField(max_length=280, unique=True, allow_unicode=True, verbose_name=_('Slug'))
    short_description = HTMLField(verbose_name=_('Short Description'))
    description = HTMLField(verbose_name=_('Description'))
    conclusion = HTMLField(blank=True, verbose_name=_('Conclusion'))
    thumbnail = models.ImageField(upload_to='blog/thumbnails/', blank=True, null=True, verbose_name=_('Thumbnail'))
    view_count = models.PositiveIntegerField(default=0, verbose_name=_('View Count'))
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='blog_posts', verbose_name=_('Author'))
    ttr = models.PositiveSmallIntegerField(default=1, verbose_name=_('Time To Read (Minutes)'))
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, related_name='posts', null=True, blank=True, verbose_name=_('Category'))
    tags = models.ManyToManyField(BlogTag, related_name='posts', blank=True, verbose_name=_('Tags'))
    saved_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='saved_blog_posts', blank=True, verbose_name=_('Saved By'))
    is_visible = models.BooleanField(default=True, verbose_name=_('Visible'))
    published_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Published At'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _('Blog Post')
        verbose_name_plural = _('Blog Posts')
        ordering = ('-published_at', '-created_at')
        indexes = [
            models.Index(fields=['is_visible', 'published_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['view_count', '-created_at']),
            models.Index(fields=['slug']),
            models.Index(fields=['title']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.slug:
            self.slug = slugify(self.slug, allow_unicode=True)
        else:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)
        invalidate_cache('blog_list')
        invalidate_cache('blog_detail')
        invalidate_cache('my_saved_blog_posts')

    def delete(self, *args, **kwargs):
        if self.thumbnail and self.thumbnail.name:
            self.thumbnail.delete(save=False)
        return super().delete(*args, **kwargs)


class BlogComment(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments', verbose_name=_('Post'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blog_comments', verbose_name=_('User'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    content = models.TextField(verbose_name=_('Content'))
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='replies',
        null=True,
        blank=True,
        verbose_name=_('Reply To')
    )

    class Meta:
        verbose_name = _('Blog Comment')
        verbose_name_plural = _('Blog Comments')
        ordering = ('created_at',)
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['reply_to']),
        ]

    def __str__(self):
        return f'{self.user} -> {self.post}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invalidate_cache('blog_comments')
        invalidate_cache('blog_detail')
