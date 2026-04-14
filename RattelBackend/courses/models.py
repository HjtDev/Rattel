import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from tinymce.models import HTMLField


class Course(models.Model):
    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        indexes = [
            models.Index(fields=['teacher', 'created_at']),
            models.Index(fields=['difficulty', 'age_group']),
            models.Index(fields=['category']),
        ]

    class DifficultyChoices(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'

    class AgeGroupChoices(models.TextChoices):
        KID = 'kid', 'Kid'
        TEEN = 'teen', 'Teen'
        ADULT = 'adult', 'Adult'
        ALL = 'all', 'All'

    class CategoryChoices(models.TextChoices):
        NAGHME = 'naghme', 'Naghme'
        HAFEZE = 'hafeze', 'Hafeze'
        ANDISHE = 'andishe', 'Andishe'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, verbose_name='Course ID')

    name = models.CharField(max_length=255, verbose_name='Title')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='courses_taught', verbose_name='Teacher')
    bought_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='purchased_courses', blank=True, verbose_name='Bought By')

    short_description = HTMLField(verbose_name='Short Description')
    long_description = HTMLField(verbose_name='Long Description')

    intro_video = models.FileField(upload_to='courses/intros/', blank=True, null=True, verbose_name='Course Intro Video')

    price = models.PositiveIntegerField(validators=[MinValueValidator(0)], verbose_name='Price (Toman)')
    new_price = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name='Discounted Price (0 = no discount)')

    extra_sells = models.PositiveIntegerField(default=0, verbose_name='Extra Sells (outside site)')

    difficulty = models.CharField(max_length=20, choices=DifficultyChoices.choices, verbose_name='Difficulty')
    age_group = models.CharField(max_length=10, choices=AgeGroupChoices.choices, verbose_name='Age Group')
    category = models.CharField(max_length=20, choices=CategoryChoices.choices, verbose_name='Category')

    rating = models.PositiveIntegerField(validators=[MinValueValidator(0)], verbose_name='Rating')

    total_time = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name='Total Time(H)', help_text='Time it takes to finish this course')

    is_visible = models.BooleanField(default=True, verbose_name='Visible', help_text='If disabled purchasing items of this model will be disabled too.')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    @property
    def discount(self):
        """Calculate the discount percentage.

        Returns:
            int: Discount percentage (0-100), 0 if no discount.
        """
        if self.new_price and self.new_price < self.price and self.price > 0:
            return round((1 - self.new_price / self.price) * 100)
        return 0

    @property
    def total_sell(self):
        """Return total number of sells including off-site purchases.

        Returns:
            int: Sum of bought_by count and extra_sells.
        """
        return self.bought_by.count() + self.extra_sells

    def __str__(self):
        return self.name

    def add_user(self, user):
        """On successful purchase this method is used to add user to the bought_by

        Args:
            user: User instance to add.
        """
        self.bought_by.add(user)

    def has_access_to_course(self, user) -> bool:
        """Checks if a user has access to course data or not

        Args:
            user: User instance to check.

        Returns:
            bool: True if user has access to course, False otherwise.
        """
        return self.teacher == user or self.bought_by.filter(pk=user.pk).exists()



class Chapter(models.Model):
    class Meta:
        verbose_name = 'Chapter'
        verbose_name_plural = 'Chapters'
        ordering = ['course', 'order']

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='chapters', verbose_name='Course')

    title = models.CharField(max_length=255, verbose_name='Title')
    description = HTMLField(blank=True, verbose_name='Description')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Order')

    number_of_files = models.PositiveIntegerField(default=0, verbose_name='Number of Files')
    number_of_videos = models.PositiveIntegerField(default=0, verbose_name='Number of Videos')

    is_free = models.BooleanField(default=False, verbose_name='Free Preview')
    is_visible = models.BooleanField(default=True, verbose_name='Visible')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    def __str__(self):
        return f'{self.course.name} — {self.title}'


class Episode(models.Model):
    class Meta:
        verbose_name = 'Episode'
        verbose_name_plural = 'Episodes'
        ordering = ['chapter', 'id']

    class EpisodeType(models.TextChoices):
        VIDEO = 'video', 'Video'
        NOTE = 'note', 'Note'
        ATTACHMENT = 'attachment', 'Attachment'

    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='episodes', verbose_name='Chapter')

    title = models.CharField(max_length=255, verbose_name='Title')
    type = models.CharField(max_length=20, choices=EpisodeType.choices, verbose_name='Type')
    file = models.FileField(upload_to='courses/episodes/', verbose_name='File')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    
    counted = models.BooleanField(default=False, verbose_name='Counted')

    def __str__(self):
        return f'{self.chapter} — {self.title}'
    
    def save(self, *args, **kwargs):
        if self.counted:
            return super().save(*args, **kwargs)
        
        if self.type == self.EpisodeType.VIDEO:
            self.chapter.number_of_videos += 1
        else:
            self.chapter.number_of_files += 1
        
        self.chapter.save()
        
        return super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        if not self.counted:
            return super().delete(*args, **kwargs)
        
        if self.type == self.EpisodeType.VIDEO:
            self.chapter.number_of_videos -= 1
        else:
            self.chapter.number_of_files -= 1
            
        self.chapter.save()
        
        return super().delete(*args, **kwargs)
            
