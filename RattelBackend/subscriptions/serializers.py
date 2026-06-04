from rest_framework import serializers
from .models import Plan


class PlanCartSerializer(serializers.ModelSerializer):
    picture = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = ('name', 'picture')

    def get_picture(self, obj: Plan):
        request = self.context.get('request')
        if obj.picture and obj.picture.name:
            if request:
                return request.build_absolute_uri(obj.picture.url)
            return obj.picture.url
        return None


class PlanSerializer(serializers.ModelSerializer):
    discount = serializers.IntegerField(read_only=True)
    picture = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = (
            'name',
            'description',
            'picture',
            'price',
            'new_price',
            'discount',
            'duration_days',
            'has_early_news_access',
            'has_quiz_access',
            'online_class_limit',
            'is_visible',
            'created_at',
            'updated_at',
        )

    def get_picture(self, obj: Plan):
        request = self.context.get('request')
        if obj.picture and obj.picture.name:
            if request:
                return request.build_absolute_uri(obj.picture.url)
            return obj.picture.url
        return None
