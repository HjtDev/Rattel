from django.contrib import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from jalali_date import datetime2jalali
from jalali_date.fields import JalaliDateField, SplitJalaliDateTimeField
from jalali_date.widgets import AdminJalaliDateWidget, AdminSplitJalaliDateTime

from .models import BlogPost, BlogComment, BlogCategory, BlogTag

_JALALI_FORMFIELD_OVERRIDES = {
    models.DateField: {'form_class': JalaliDateField, 'widget': AdminJalaliDateWidget},
    models.DateTimeField: {'form_class': SplitJalaliDateTimeField, 'widget': AdminSplitJalaliDateTime},
}


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES
    list_display = ('name', 'slug', 'created_at_jalali')
    list_display_links = ('name',)
    ordering = ('name',)
    readonly_fields = ('created_at',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')
    fieldsets = (
        (_('Basic Info'), {'fields': ('name', 'slug')}),
        (_('System Info'), {'fields': ('created_at',)}),
    )

    @admin.display(description=_('Created At'))
    def created_at_jalali(self, obj):
        return datetime2jalali(timezone.localtime(obj.created_at)).strftime('%Y/%m/%d %H:%M')


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES
    list_display = ('name', 'slug', 'created_at_jalali')
    list_display_links = ('name',)
    ordering = ('name',)
    readonly_fields = ('created_at',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')
    fieldsets = (
        (_('Basic Info'), {'fields': ('name', 'slug')}),
        (_('System Info'), {'fields': ('created_at',)}),
    )

    @admin.display(description=_('Created At'))
    def created_at_jalali(self, obj):
        return datetime2jalali(timezone.localtime(obj.created_at)).strftime('%Y/%m/%d %H:%M')


class BlogCommentInline(admin.TabularInline):
    model = BlogComment
    fk_name = 'post'
    extra = 0
    fields = ('user', 'content', 'reply_to', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES
    list_display = (
        'title',
        'author',
        'category',
        'view_count',
        'saved_by_count',
        'comments_count',
        'is_visible',
        'published_at_jalali',
        'created_at_jalali',
    )
    list_display_links = ('title',)
    list_filter = ('is_visible', 'category', 'tags', 'author', 'published_at', 'created_at')
    ordering = ('-published_at', '-created_at')
    date_hierarchy = 'published_at'
    readonly_fields = ('id', 'view_count', 'created_at', 'updated_at')
    autocomplete_fields = ('author', 'category', 'tags', 'saved_by')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'slug', 'short_description', 'description')
    filter_horizontal = ('tags', 'saved_by')
    inlines = (BlogCommentInline,)
    actions = ('make_visible', 'make_hidden')
    fieldsets = (
        (_('Primary Content'), {
            'fields': ('id', 'title', 'slug', 'author', 'thumbnail', 'ttr')
        }),
        (_('Body'), {
            'fields': ('short_description', 'description', 'conclusion')
        }),
        (_('Classification'), {
            'fields': ('category', 'tags')
        }),
        (_('Publishing & Visibility'), {
            'fields': ('is_visible', 'published_at')
        }),
        (_('Engagement'), {
            'fields': ('view_count', 'saved_by')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

    @admin.display(description=_('Published At'))
    def published_at_jalali(self, obj):
        return datetime2jalali(timezone.localtime(obj.published_at)).strftime('%Y/%m/%d %H:%M') if obj.published_at else '—'

    @admin.display(description=_('Created At'))
    def created_at_jalali(self, obj):
        return datetime2jalali(timezone.localtime(obj.created_at)).strftime('%Y/%m/%d %H:%M')

    @admin.display(description=_('Saved By'))
    def saved_by_count(self, obj):
        return obj.saved_by.count()

    @admin.display(description=_('Comments'))
    def comments_count(self, obj):
        return obj.comments.count()

    @admin.action(description=_('Mark selected posts as visible'))
    def make_visible(self, request, queryset):
        updated = queryset.update(is_visible=True)
        self.message_user(request, _('Updated %(count)d post(s).') % {'count': updated})

    @admin.action(description=_('Mark selected posts as hidden'))
    def make_hidden(self, request, queryset):
        updated = queryset.update(is_visible=False)
        self.message_user(request, _('Updated %(count)d post(s).') % {'count': updated})


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES
    list_display = ('short_post_title', 'user', 'is_reply', 'reply_to', 'created_at_jalali')
    list_display_links = ('short_post_title',)
    list_filter = ('created_at', 'post', 'user')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    autocomplete_fields = ('post', 'user', 'reply_to')
    date_hierarchy = 'created_at'
    search_fields = ('content', 'user__name', 'post__title')
    fieldsets = (
        (_('Comment'), {'fields': ('post', 'user', 'reply_to', 'content')}),
        (_('System Info'), {'fields': ('created_at',)}),
    )

    @admin.display(description=_('Created At'))
    def created_at_jalali(self, obj):
        return datetime2jalali(timezone.localtime(obj.created_at)).strftime('%Y/%m/%d %H:%M')

    @admin.display(description=_('Post'))
    def short_post_title(self, obj):
        return obj.post.title

    @admin.display(boolean=True, description=_('Reply'))
    def is_reply(self, obj):
        return obj.reply_to_id is not None
