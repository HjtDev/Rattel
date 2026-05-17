from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile, UserSettings
from .forms import CustomUserCreationForm, CustomUserChangeForm
from django.contrib.auth.models import Group


admin.site.unregister(Group)

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
    verbose_name = _('User Profile')
    verbose_name_plural = _('User Profiles')
    

class UserSettingsInline(admin.StackedInline):
    model = UserSettings
    can_delete = False
    extra = 0
    verbose_name = _('User Settings')
    verbose_name_plural = _('User Settings')


@admin.register(User)
class UserAdmin(UserAdmin):
    ordering = ['date_joined']
    inlines = (ProfileInline, UserSettingsInline)
    
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    
    search_fields = [
        'username',
        'phone',
        'name',
        'email'
    ]
    
    list_display = [
        'id',
        'username',
        'name',
        'email',
        'is_active',
        'is_staff',
    ]
    
    fieldsets = (
        (_('General'), {'fields': ('username', 'password')}),
        (_('Personal Info'), {'fields': ('name', 'phone', 'email', 'profile_picture', 'course_history')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        (_('Dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (_('General'), {'fields': ('username', 'password1', 'password2')}),
        (_('Personal Info'), {'fields': ('name', 'email', 'profile_picture')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        (_('Dates'), {'fields': ('last_login', 'date_joined')}),
    )
