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
            raise ValueError('Users must have a username')
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
        f'user_{instance.username}',
        filename
    )

def validate_username(username):
    if not GetDataMixin.validate_username(username):
        raise ValidationError(
            'Username must: (1) start with a letter, '
            '(2) be 3-30 characters long, '
            '(3) contain only letters, numbers, underscores, and dots.'
        )
    
def validate_user_phone(phone: str):
    if not GetDataMixin.validate_phone(phone):
        raise ValidationError('Phone number must be a 11 digit starting with 09.')

class User(AbstractBaseUser, PermissionsMixin):
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
        ]
        
    username = models.CharField(max_length=30, unique=True, verbose_name='Username', validators=[validate_username])
    email = models.EmailField(max_length=255, blank=True, null=True, unique=True, verbose_name='Email')
    name = models.CharField(max_length=60, verbose_name='Name')
    phone = models.CharField(max_length=11, blank=False, null=False, unique=True, validators=[validate_user_phone], verbose_name='Phone number', help_text='Example: 09123456789')
    profile_picture = ResizedImageField(upload_to=profile_directory_path, blank=True, null=True, verbose_name='Profile Picture')
    
    score = models.PositiveIntegerField(default=10, verbose_name='Score', help_text='For evaluating user rank')
    
    is_active = models.BooleanField(default=True, verbose_name='Active')
    is_staff = models.BooleanField(default=False, verbose_name='Staff')
    is_superuser = models.BooleanField(default=False, verbose_name='Superuser')
    
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Date Joined')
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['name', 'phone']
    
    def __str__(self):
        return self.name
    
def validate_national_code(national_code: str):
    if national_code and GetDataMixin.NATIONAL_CODE_REGEX.fullmatch(national_code) is None:
        raise ValidationError('National code must be 10 digit string.')
    

class Profile(models.Model):
    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
    
    class RoleChoices(models.TextChoices):
        STUDENT = 'student', 'Student'
        TEACHER = 'teacher', 'Teacher'
        
    class GenderChoices(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='User')
    
    role = models.CharField(max_length=10, choices=RoleChoices.choices, default=RoleChoices.STUDENT, verbose_name='Role')
    gender = models.CharField(max_length=10, choices=GenderChoices.choices, blank=True, null=True, verbose_name='Gender')
    
    national_code = models.CharField(max_length=10, blank=True, null=True, validators=[validate_national_code], verbose_name='National Code')
    
    education = models.TextField(max_length=150, blank=True, null=True, verbose_name='Education')
    had_other_classes = models.TextField(max_length=500, blank=True, null=True, verbose_name='Had other classes: Where')
    memorized = models.TextField(max_length=300, blank=True, null=True, verbose_name='Memorized', help_text='How much Quran this person memorized.')
    
    invited_by = models.CharField(max_length=60, blank=True, null=True, verbose_name='Invited by')
    
    birthday = models.DateField(blank=True, null=True, verbose_name='Birthday')
    city = models.CharField(max_length=120, blank=True, null=True, verbose_name='Province/City')
    
    telegram_id = models.CharField(max_length=50, blank=True, null=True, verbose_name='Telegram ID')
    eitaa_id = models.CharField(max_length=50, blank=True, null=True, verbose_name='Eitaa ID')
    instagram_id = models.CharField(max_length=50, blank=True, null=True, verbose_name='Instagram ID')
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    
class UserSettings(models.Model):
    class Meta:
        verbose_name = 'Setting'
        verbose_name_plural = 'Settings'
        
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings', verbose_name='User')
    
    profile_visible = models.BooleanField(default=True, verbose_name='Profile visible')
    email_on_login = models.BooleanField(default=False, verbose_name='Email on login')
    email_on_payment = models.BooleanField(default=False, verbose_name='Email on payment')
    sms_on_payment = models.BooleanField(default=True, verbose_name='SMS on payment')
    
    def __str__(self):
        return f"{self.user.username}'s Settings"
