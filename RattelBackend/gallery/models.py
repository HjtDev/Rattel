import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from RattelBackend.cache import invalidate_cache


class Gallery(models.Model):
    class Meta:
        verbose_name = _('Gallery')
        verbose_name_plural = _('Galleries')
        ordering = ('-created_at',)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, verbose_name=_('Gallery ID'))
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    thumbnail = models.FileField(upload_to='gallery/thumbnails/', verbose_name=_('Thumbnail'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invalidate_cache('gallery_list')
        invalidate_cache('gallery_detail')

    def delete(self, *args, **kwargs):
        thumbnail = self.thumbnail
        result = super().delete(*args, **kwargs)
        if thumbnail and thumbnail.name:
            thumbnail.delete(save=False)
        invalidate_cache('gallery_list')
        invalidate_cache('gallery_detail')
        return result


class GalleryContent(models.Model):
    class ContentType(models.TextChoices):
        IMAGE = 'image', _('Image')
        VIDEO = 'video', _('Video')
        AUDIO = 'audio', _('Audio')
        EMBED = 'embed', _('Embed')

    class Meta:
        verbose_name = _('Gallery Content')
        verbose_name_plural = _('Gallery Contents')
        ordering = ('order', 'id')

    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE, related_name='content', verbose_name=_('Gallery'))
    content_type = models.CharField(max_length=10, choices=ContentType.choices, verbose_name=_('Content Type'))
    image = models.FileField(upload_to='gallery/content/images/', blank=True, null=True, verbose_name=_('Image'))
    video = models.FileField(upload_to='gallery/content/videos/', blank=True, null=True, verbose_name=_('Video'))
    audio = models.FileField(upload_to='gallery/content/audio/', blank=True, null=True, verbose_name=_('Audio'))
    embed_code = models.TextField(blank=True, default='', verbose_name=_('Embed Code'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    def __str__(self):
        return f'{self.gallery} - {self.content_type} #{self.order}'

    def clean(self):
        field_by_type = {
            self.ContentType.IMAGE: self.image,
            self.ContentType.VIDEO: self.video,
            self.ContentType.AUDIO: self.audio,
            self.ContentType.EMBED: self.embed_code,
        }

        if self.content_type not in field_by_type:
            raise ValidationError({'content_type': _('Invalid content type.')})

        selected_value = field_by_type[self.content_type]
        if self.content_type == self.ContentType.EMBED:
            if not isinstance(selected_value, str) or not selected_value.strip():
                raise ValidationError({'embed_code': _('Embed code is required for embed content type.')})
        elif not selected_value:
            raise ValidationError({self.content_type: _('File is required for selected content type.')})

        if self.content_type != self.ContentType.IMAGE and self.image:
            raise ValidationError({'image': _('Image must be empty unless content type is image.')})
        if self.content_type != self.ContentType.VIDEO and self.video:
            raise ValidationError({'video': _('Video must be empty unless content type is video.')})
        if self.content_type != self.ContentType.AUDIO and self.audio:
            raise ValidationError({'audio': _('Audio must be empty unless content type is audio.')})
        if self.content_type != self.ContentType.EMBED and self.embed_code:
            raise ValidationError({'embed_code': _('Embed code must be empty unless content type is embed.')})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        invalidate_cache('gallery_list')
        invalidate_cache('gallery_detail')

    def delete(self, *args, **kwargs):
        image = self.image
        video = self.video
        audio = self.audio
        result = super().delete(*args, **kwargs)
        for file_obj in (image, video, audio):
            if file_obj and file_obj.name:
                file_obj.delete(save=False)
        invalidate_cache('gallery_list')
        invalidate_cache('gallery_detail')
        return result
