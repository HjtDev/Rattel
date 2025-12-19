from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .forms import CustomUserCreationForm, CustomUserChangeForm
from django.contrib.auth.models import Group


admin.site.unregister(Group)

@admin.register(User)
class UserAdmin(UserAdmin):
    ordering = ['date_joined']
    
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    
    search_fields = [
        'username',
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
        ('General', {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('name', 'email', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        ('General', {'fields': ('username', 'password1', 'password2')}),
        ('Personal Info', {'fields': ('name', 'email', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
