from django.urls import path
from . import views


app_name = 'courses'

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course-list'),
    path('teachers/', views.TeacherListView.as_view(), name='teacher-list'),
    path('<uuid:course_id>/', views.CourseDetailView.as_view(), name='course-detail'),
]
