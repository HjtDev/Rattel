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
        return None


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

    class Meta:
        model = Course
        fields = (
            'id',
            'name',
            'price',
            'new_price',
            'difficulty',
            'short_description',
            'number_of_episodes',
            'total_time',
            'rating',
            'total_sell',
            'teacher',
        )

    def get_number_of_episodes(self, obj):
        """Return total episode count across all chapters.

        Args:
            obj: Course instance.

        Returns:
            int: Total number of episodes.
        """
        return sum(ch.number_of_videos + ch.number_of_files for ch in obj.chapters.all())


class CourseDetailSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField()
    teacher = QuickUserSerializer(read_only=True)
    chapters = serializers.SerializerMethodField()
    discount = serializers.IntegerField(read_only=True)
    total_sell = serializers.IntegerField(read_only=True)
    number_of_episodes = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            'id',
            'content_type',
            'name',
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
