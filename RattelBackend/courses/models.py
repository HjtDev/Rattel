import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from tinymce.models import HTMLField
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _


class Course(models.Model):
    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')
        indexes = [
            models.Index(fields=['teacher', 'created_at']),
            models.Index(fields=['difficulty', 'age_group']),
            models.Index(fields=['category']),
        ]

    class DifficultyChoices(models.TextChoices):
        BEGINNER = 'beginner', _('Beginner')
        INTERMEDIATE = 'intermediate', _('Intermediate')
        ADVANCED = 'advanced', _('Advanced')

    class AgeGroupChoices(models.TextChoices):
        KID = 'kid', _('Kid')
        TEEN = 'teen', _('Teen')
        ADULT = 'adult', _('Adult')
        ALL = 'all', _('All')

    class CategoryChoices(models.TextChoices):
        NAGHME = 'naghme', _('Naghme')
        HAFEZE = 'hafeze', _('Hafeze')
        ANDISHE = 'andishe', _('Andishe')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, verbose_name=_('Course ID'))

    name = models.CharField(max_length=255, verbose_name=_('Title'))
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='courses_taught', verbose_name=_('Teacher'))
    bought_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='purchased_courses', blank=True, verbose_name=_('Bought By'))
    saved_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='saved_courses', blank=True, verbose_name=_('Saved By'))

    short_description = HTMLField(verbose_name=_('Short Description'))
    long_description = HTMLField(verbose_name=_('Long Description'))

    intro_video = models.FileField(upload_to='courses/intros/', blank=True, null=True, verbose_name=_('Course Intro Video'))
    image = models.FileField(upload_to='courses/images/', blank=True, null=True, verbose_name=_('Course Image/Banner'))

    price = models.PositiveIntegerField(validators=[MinValueValidator(0)], verbose_name=_('Price (Toman)'))
    new_price = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name=_('Discounted Price (0 = no discount)'))

    extra_sells = models.PositiveIntegerField(default=0, verbose_name=_('Extra Sells (outside site)'))

    difficulty = models.CharField(max_length=20, choices=DifficultyChoices.choices, verbose_name=_('Difficulty'))
    age_group = models.CharField(max_length=10, choices=AgeGroupChoices.choices, verbose_name=_('Age Group'))
    category = models.CharField(max_length=20, choices=CategoryChoices.choices, verbose_name=_('Category'))

    rating = models.PositiveIntegerField(validators=[MinValueValidator(0)], verbose_name=_('Rating'))

    total_time = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name=_('Total Time(H)'), help_text=_('Time it takes to finish this course'))

    is_visible = models.BooleanField(default=True, verbose_name=_('Visible'), help_text=_('If disabled purchasing items of this model will be disabled too.'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    @classproperty
    def CART_SERIALIZER(cls):
        from courses.serializers import CourseCartSerializer
        return CourseCartSerializer

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

    def get_user_progress(self, user):
        """
        Calculate user's progress for this course.
        
        Args:
            user: User instance
            
        Returns:
            dict: Progress information including:
                - completed: Number of completed episodes
                - total: Total number of episodes
                - percentage: Completion percentage (0-100)
                - last_episode: Last watched episode object or None
                - next_episode: Next episode to watch or None
        """
        from .progress_models import EpisodeProgress
        
        # Get all episode IDs for this course
        all_episodes = Episode.objects.filter(
            chapter__course=self,
            chapter__is_visible=True
        ).order_by('chapter__order', 'id')
        
        total_episodes = all_episodes.count()
        
        if total_episodes == 0:
            return {
                'completed': 0,
                'total': 0,
                'percentage': 0,
                'last_episode': None,
                'next_episode': None,
            }
        
        # Get completed episodes
        completed_count = EpisodeProgress.objects.filter(
            course=self,
            user=user,
            is_completed=True
        ).count()
        
        # Get last watched episode
        last_progress = EpisodeProgress.objects.filter(
            course=self,
            user=user
        ).order_by('-last_watched_at').first()
        
        last_episode = last_progress.episode if last_progress else None
        
        # Find next episode to watch
        next_episode = None
        if last_episode:
            # Get all episodes after the last watched one
            try:
                last_episode_index = list(all_episodes).index(last_episode)
                if last_episode_index + 1 < total_episodes:
                    next_episode = all_episodes[last_episode_index + 1]
            except (ValueError, IndexError):
                pass
        
        # If no next episode found or no last episode, start from beginning
        if not next_episode and completed_count < total_episodes:
            # Find first unwatched episode
            watched_episode_ids = EpisodeProgress.objects.filter(
                course=self,
                user=user,
                is_completed=True
            ).values_list('episode_id', flat=True)
            
            for episode in all_episodes:
                if episode.id not in watched_episode_ids:
                    next_episode = episode
                    break
        
        percentage = round((completed_count / total_episodes) * 100, 1) if total_episodes > 0 else 0
        
        return {
            'completed': completed_count,
            'total': total_episodes,
            'percentage': percentage,
            'last_episode': {
                'id': last_episode.id,
                'title': last_episode.title,
                'type': last_episode.type,
            } if last_episode else None,
            'next_episode': {
                'id': next_episode.id,
                'title': next_episode.title,
                'type': next_episode.type,
            } if next_episode else None,
        }




class Chapter(models.Model):
    class Meta:
        verbose_name = _('Chapter')
        verbose_name_plural = _('Chapters')
        ordering = ['course', 'order']

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='chapters', verbose_name=_('Course'))

    title = models.CharField(max_length=255, verbose_name=_('Title'))
    description = HTMLField(blank=True, verbose_name=_('Description'))
    order = models.PositiveSmallIntegerField(default=0, verbose_name=_('Order'))

    number_of_files = models.PositiveIntegerField(default=0, verbose_name=_('Number of Files'))
    number_of_videos = models.PositiveIntegerField(default=0, verbose_name=_('Number of Videos'))

    is_free = models.BooleanField(default=False, verbose_name=_('Free Preview'))
    is_visible = models.BooleanField(default=True, verbose_name=_('Visible'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    def __str__(self):
        return f'{self.course.name} — {self.title}'


class Episode(models.Model):
    class Meta:
        verbose_name = _('Episode')
        verbose_name_plural = _('Episodes')
        ordering = ['chapter', 'id']

    class EpisodeType(models.TextChoices):
        VIDEO = 'video', _('Video')
        NOTE = 'note', _('Note')
        ATTACHMENT = 'attachment', _('Attachment')

    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='episodes', verbose_name=_('Chapter'))

    title = models.CharField(max_length=255, verbose_name=_('Title'))
    type = models.CharField(max_length=20, choices=EpisodeType.choices, verbose_name=_('Type'))
    file = models.FileField(upload_to='courses/episodes/', verbose_name=_('File'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    
    counted = models.BooleanField(default=False, verbose_name=_('Counted'))

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
            
