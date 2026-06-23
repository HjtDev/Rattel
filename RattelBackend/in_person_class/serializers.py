from rest_framework import serializers

from .models import Category, InPersonClass, InPersonClassRegistration, TimeRange


class InPersonClassRegistrationCartSerializer(serializers.ModelSerializer):
    picture = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = InPersonClassRegistration
        fields = ('name', 'picture')

    def get_name(self, obj: InPersonClassRegistration):
        return obj.in_person_class.title

    def get_picture(self, obj: InPersonClassRegistration):
        request = self.context.get('request', None)
        if obj.in_person_class.thumbnail and obj.in_person_class.thumbnail.name:
            url = obj.in_person_class.thumbnail.url
            return request.build_absolute_uri(url) if request else url
        return None


class TimeRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeRange
        fields = ('id', 'label')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug')


class InPersonClassListSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    available_times = TimeRangeSerializer(many=True, read_only=True)
    thumbnail = serializers.SerializerMethodField()
    discount = serializers.IntegerField(read_only=True)

    class Meta:
        model = InPersonClass
        fields = (
            'id',
            'thumbnail',
            'title',
            'short_description',
            'price',
            'new_price',
            'discount',
            'available_times',
            'categories',
            'start_date',
            'end_date',
        )

    def get_thumbnail(self, obj: InPersonClass):
        request = self.context.get('request', None)
        if obj.thumbnail and obj.thumbnail.name:
            url = obj.thumbnail.url
            return request.build_absolute_uri(url) if request else url
        return None


class InPersonClassRegistrationSerializer(serializers.ModelSerializer):
    in_person_class = InPersonClassListSerializer(read_only=True)
    time_range = TimeRangeSerializer(read_only=True)
    registered_count = serializers.SerializerMethodField()

    class Meta:
        model = InPersonClassRegistration
        fields = (
            'id',
            'in_person_class',
            'time_range',
            'start_date',
            'end_date',
            'price',
            'new_price',
            'registered_count',
            'created_at',
        )
        read_only_fields = fields

    def get_registered_count(self, obj: InPersonClassRegistration) -> int:
        return obj.bought_by.count()
