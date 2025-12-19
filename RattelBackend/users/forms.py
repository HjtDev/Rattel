from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User
from RattelBackend.mixins import GetDataMixin


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'name', 'email', 'profile_picture', 'is_active', 'is_staff', 'is_superuser')
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        if self.instance.pk:
            if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('Username is in use.')
        else:
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError('Username is in use.')
        
        if not GetDataMixin.validate_username(username):
            raise forms.ValidationError('Username must start with an alphabetic character. Username must be between 3..30 characters. Username must not contain special characters.')
        
        return username


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'name', 'email', 'profile_picture', 'is_active', 'is_staff', 'is_superuser')
