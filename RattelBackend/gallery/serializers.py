from rest_framework import serializers

from .models import Gallery, GalleryContent


class GalleryContentSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = GalleryContent
        fields = ('id', 'content_type', 'file', 'embed_code', 'order', 'created_at', 'updated_at')

    def get_file(self, obj):
        request = self.context.get('request')
        file_obj = obj.image or obj.video or obj.audio
        if not file_obj:
            return None
        url = file_obj.url
        return request.build_absolute_uri(url) if request else url


class GalleryListSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Gallery
        fields = ('id', 'title', 'thumbnail')

    def get_thumbnail(self, obj):
        request = self.context.get('request')
        if not obj.thumbnail:
            return None
        url = obj.thumbnail.url
        return request.build_absolute_uri(url) if request else url


class GalleryDetailSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()

    class Meta:
        model = Gallery
        fields = ('id', 'title', 'thumbnail', 'content', 'created_at', 'updated_at')

    def get_thumbnail(self, obj):
        request = self.context.get('request')
        if not obj.thumbnail:
            return None
        url = obj.thumbnail.url
        return request.build_absolute_uri(url) if request else url

    def get_content(self, obj):
        return GalleryContentSerializer(
            obj.content.all().order_by('order'),
            many=True,
            context=self.context
        ).data
