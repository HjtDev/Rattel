from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django_resized import ResizedImageField
from django.core.exceptions import ValidationError
from RattelBackend.mixins import GetDataMixin
import os


class UserManager(BaseUserManager):
    
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Users must have a username number')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, password, **extra_fields)


def profile_directory_path(instance, filename):
    return os.path.join(
        'Profiles',
        f'user_{instance.id}',
        filename
    )

def validate_username(username):
    if not GetDataMixin.validate_username(username):
        raise ValidationError('Username must start with an alphabetic character. Username must be between 3..30 characters. Username must not contain special characters.')

class User(AbstractBaseUser, PermissionsMixin):
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        
    username = models.CharField(max_length=30, unique=True, verbose_name='Username', validators=[validate_username])
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name='Email')
    name = models.CharField(max_length=60, verbose_name='Name')
    profile_picture = ResizedImageField(upload_to=profile_directory_path, blank=True, null=True, verbose_name='Profile Picture')
    
    is_active = models.BooleanField(default=True, verbose_name='Active')
    is_staff = models.BooleanField(default=False, verbose_name='Staff')
    is_superuser = models.BooleanField(default=False, verbose_name='Superuser')
    
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Date Joined')
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['name']
    
    def __str__(self):
        return self.name
    
