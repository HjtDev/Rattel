from django.utils.timesince import timesince
from rest_framework import serializers
from users.serializers import QuickUserSerializer
from .models import BlogPost, BlogComment, BlogCategory, BlogTag


class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = ('id', 'name', 'slug')


class BlogTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogTag
        fields = ('id', 'name', 'slug')


class BlogPostListSerializer(serializers.ModelSerializer):
    author = QuickUserSerializer(read_only=True)
    category = BlogCategorySerializer(read_only=True)
    tags = BlogTagSerializer(read_only=True, many=True)
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = (
            'id',
            'title',
            'slug',
            'short_description',
            'thumbnail',
            'view_count',
            'author',
            'ttr',
            'category',
            'tags',
            'is_saved',
            'published_at',
            'created_at',
        )

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.saved_by.filter(pk=request.user.pk).exists()
        return False


class BlogCommentSerializer(serializers.ModelSerializer):
    user = QuickUserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = BlogComment
        fields = ('id', 'user', 'created_at', 'content', 'reply_to', 'replies')

    def get_replies(self, obj):
        replies = obj.replies.select_related('user').all()
        return BlogCommentSerializer(replies, many=True, context=self.context).data


class BlogPostDetailSerializer(serializers.ModelSerializer):
    author = QuickUserSerializer(read_only=True)
    category = BlogCategorySerializer(read_only=True)
    tags = BlogTagSerializer(read_only=True, many=True)
    comments = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    time_since = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = (
            'id',
            'title',
            'slug',
            'short_description',
            'description',
            'conclusion',
            'thumbnail',
            'view_count',
            'author',
            'ttr',
            'category',
            'tags',
            'is_saved',
            'time_since',
            'comments',
            'published_at',
            'created_at',
            'updated_at',
        )

    def get_time_since(self, obj):
        source_time = obj.published_at or obj.created_at
        return timesince(source_time)

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.saved_by.filter(pk=request.user.pk).exists()
        return False

    def get_comments(self, obj):
        top_level = obj.comments.select_related('user').filter(reply_to__isnull=True)
        return BlogCommentSerializer(top_level, many=True, context=self.context).data
