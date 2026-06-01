from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from users.serializers import QuickUserSerializer
from .models import Course, Chapter, Episode
import logging
logger = logging.getLogger(__name__)


class CourseCartSerializer(serializers.ModelSerializer):
    picture = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ('name', 'picture')

    def get_picture(self, obj: Course):
        request = self.context.get('request', None)
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url


class EpisodeSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = Episode
        fields = ('id', 'title', 'type', 'file')

    def get_file(self, obj: Episode):
        """
        Returns a full URL if request context was available, a relative URL if not..

        Args:
            obj: Course instance.

        Returns:
            str: Static/Relative URL.
        """
        request = self.context.get('request', None)

        if obj.chapter.is_free:
            load_url = True
        elif request.user.is_authenticated and obj.chapter.course.has_access_to_course(request.user):
            load_url = True
        else:
            load_url = False

        if not load_url:
            return 'hidden'

        if request:
            return request.build_absolute_uri(obj.file.url)

        return obj.file.url


class ChapterSerializer(serializers.ModelSerializer):
    episodes = serializers.SerializerMethodField()

    class Meta:
        model = Chapter
        fields = (
            'id',
            'title',
            'description',
            'order',
            'number_of_files',
            'number_of_videos',
            'is_free',
            'is_visible',
            'episodes',
        )

    def get_episodes(self, obj: Chapter):
        return EpisodeSerializer(obj.episodes.all(), many=True, context=self.context, read_only=True).data


class CourseListSerializer(serializers.ModelSerializer):
    teacher = QuickUserSerializer(read_only=True)
    number_of_episodes = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            'id',
            'name',
            'image',
            'price',
            'new_price',
            'difficulty',
            'category',
            'short_description',
            'number_of_episodes',
            'total_time',
            'rating',
            'total_sell',
            'teacher',
            'is_saved',
            'progress',
        )

    def get_number_of_episodes(self, obj):
        """Return total episode count across all chapters.

        Args:
            obj: Course instance.

        Returns:
            int: Total number of episodes.
        """
        return sum(ch.number_of_videos + ch.number_of_files for ch in obj.chapters.all())

    def get_is_saved(self, obj):
        """Check if the requesting user has saved this course.

        Args:
            obj: Course instance.

        Returns:
            bool: True if user has saved the course, False otherwise.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.saved_by.filter(pk=request.user.pk).exists()
        return False


    def get_progress(self, obj):
        """Get user's progress for this course if authenticated.

        Args:
            obj: Course instance.

        Returns:
            dict or None: Progress information or None if not authenticated.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Only calculate progress if user has access to the course
            if obj.has_access_to_course(request.user):
                progress = obj.get_user_progress(request.user)
                return progress
        return None


class CourseDetailSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField()
    teacher = QuickUserSerializer(read_only=True)
    chapters = serializers.SerializerMethodField()
    discount = serializers.IntegerField(read_only=True)
    total_sell = serializers.IntegerField(read_only=True)
    number_of_episodes = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    is_owned = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            'id',
            'content_type',
            'name',
            'image',
            'teacher',
            'short_description',
            'long_description',
            'intro_video',
            'price',
            'new_price',
            'discount',
            'difficulty',
            'age_group',
            'category',
            'rating',
            'total_time',
            'total_sell',
            'number_of_episodes',
            'chapters',
            'is_saved',
            'is_owned',
            'progress',
            'created_at',
            'updated_at',
        )

    def get_content_type(self, obj):
        return ContentType.objects.get_for_model(obj).id

    def get_chapters(self, obj):
        return ChapterSerializer(obj.chapters.prefetch_related('episodes').filter(is_visible=True), many=True, read_only=True, context=self.context).data

    def get_number_of_episodes(self, obj):
        """Return total episode count across all chapters.

        Args:
            obj: Course instance.

        Returns:
            int: Total number of episodes.
        """
        return sum(ch.number_of_videos + ch.number_of_files for ch in obj.chapters.filter(is_visible=True))

    def get_is_saved(self, obj):
        """Check if the requesting user has saved this course.

        Args:
            obj: Course instance.

        Returns:
            bool: True if user has saved the course, False otherwise.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.saved_by.filter(pk=request.user.pk).exists()
        return False

    def get_is_owned(self, obj: Course):
        """Check if the requesting user has owned this course.

        Args:
            obj: Course instance.

        Returns:
            bool: True if user has owned the course, False otherwise.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.bought_by.filter(id=request.user.id).exists()
        return False



    def get_progress(self, obj):
        """Get user's progress for this course if authenticated.

        Args:
            obj: Course instance.

        Returns:
            dict or None: Progress information or None if not authenticated.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Only calculate progress if user has access to the course
            if obj.has_access_to_course(request.user):
                progress = obj.get_user_progress(request.user)
                return progress
        return None
