from django.urls import path
from . import views


app_name = 'courses'

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course-list'),
    path('my-courses/', views.MyCoursesView.as_view(), name='my-courses'),
    path('saved-courses/', views.MySavedCoursesView.as_view(), name='saved-courses'),
    path('teachers/', views.TeacherListView.as_view(), name='teacher-list'),
    path('continue-watching/', views.ContinueWatchingView.as_view(), name='continue-watching'),
    path('<uuid:course_id>/', views.CourseDetailView.as_view(), name='course-detail'),
    path('<uuid:course_id>/toggle-save/', views.ToggleSaveCourseView.as_view(), name='toggle-save'),
    path('<uuid:course_id>/progress/', views.CourseProgressView.as_view(), name='course-progress'),
    path('<uuid:course_id>/episodes/<int:episode_id>/mark-watched/', views.MarkEpisodeWatchedView.as_view(), name='mark-episode-watched'),
]
