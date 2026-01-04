from rest_framework.serializers import ModelSerializer, SerializerMethodField
from .models import User, Profile, UserSettings


class ProfileSerializer(ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            'role', 'gender', 'national_code',
            'education', 'had_other_classes', 'memorized',
            'invited_by', 'birthday', 'city',
            'telegram_id', 'eitaa_id', 'instagram_id'
        )
        read_only_fields = ('role',)


class UserSettingsSerializer(ModelSerializer):
    class Meta:
        model = UserSettings
        fields = ('profile_visible', 'email_on_login', 'email_on_payment', 'sms_on_payment')


class UserProfileBuilderMixin:
    """Can be added to any class that has the profile_picture in serializer fields."""
    __slots__ = ()
    
    profile_picture = SerializerMethodField()
    
    def get_profile_picture(self, instance):
        """Builds a full URL to profile picture if it exists."""
        if not instance.profile_picture:
            return None
        
        if hasattr(self, 'context'):
            req = self.context.get('request', None)
            if req:
                return req.build_absolute_uri(instance.profile_picture.url)
        
        return instance.profile_picture.url


class BaseUserSerializer(ModelSerializer, UserProfileBuilderMixin):
    """Base user serializer contains all the base fields"""
    
    class Meta:
        model = User
        fields = ('username', 'email', 'name', 'phone', 'profile_picture', 'score')
        read_only_fields = ('phone', 'score')
    
    def update(self, instance, validated_data):
        profile_picture = validated_data.pop('profile_picture', None)
        
        instance = super().update(instance, validated_data)
        
        if profile_picture:
            instance.profile_picture = profile_picture
            instance.save(update_fields=['profile_picture'])
        
        return instance


class FullUserSerializer(BaseUserSerializer):
    """Serialize the user instance fully with profile and settings"""
    profile = SerializerMethodField()
    settings = SerializerMethodField()
    
    class Meta:
        model = User
        fields = BaseUserSerializer.Meta.fields + ('profile', 'settings')
    
    def get_profile(self, instance: User):
        """Serialize the user profile info."""
        try:
            if hasattr(instance, 'profile') and instance.profile:
                return ProfileSerializer(instance.profile).data
        except Profile.DoesNotExist:
            pass
        return None
    
    def get_settings(self, instance: User):
        """Serialize the user settings"""
        try:
            if hasattr(instance, 'settings') and instance.settings:
                return UserSettingsSerializer(instance.settings).data
        except UserSettings.DoesNotExist:
            pass
        return None
    
    def update(self, instance, validated_data):
        """Saves the validated_data to instance when updating it partially"""
        profile_picture = validated_data.pop('profile_picture', None)
        
        instance = super().update(instance, validated_data)
        
        if profile_picture:
            instance.profile_picture = profile_picture
            instance.save(update_fields=['profile_picture'])
        
        return instance
