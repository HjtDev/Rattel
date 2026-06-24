from django.urls import path

from . import views

app_name = 'quiz'

urlpatterns = [
    # Admin
    path('admin/categories/', views.AdminCategoryListView.as_view(), name='admin-categories'),
    path('admin/', views.AdminQuizListCreateView.as_view(), name='admin-quiz-list'),
    path('admin/<uuid:quiz_id>/', views.AdminQuizDetailView.as_view(), name='admin-quiz-detail'),
    path('admin/<uuid:quiz_id>/questions/', views.AdminQuizQuestionListView.as_view(), name='admin-quiz-questions'),
    path('admin/<uuid:quiz_id>/requirements/', views.AdminQuizRequirementListView.as_view(), name='admin-quiz-requirements'),
    path('admin/questions/reorder/', views.AdminQuestionReorderView.as_view(), name='admin-question-reorder'),
    path('admin/questions/<uuid:question_id>/', views.AdminQuestionDetailView.as_view(), name='admin-question-detail'),
    path('admin/requirements/<int:req_id>/', views.AdminQuizRequirementDetailView.as_view(), name='admin-requirement-detail'),
    path('admin/<uuid:quiz_id>/participants/', views.AdminQuizParticipantsView.as_view(), name='admin-quiz-participants'),

    # User — static paths before UUID patterns
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
    path('my-attempts/', views.MyAttemptsView.as_view(), name='my-attempts'),

    # User — UUID paths
    path('', views.QuizListView.as_view(), name='quiz-list'),
    path('<uuid:quiz_id>/', views.QuizDetailView.as_view(), name='quiz-detail'),
    path('<uuid:quiz_id>/start/', views.QuizStartView.as_view(), name='quiz-start'),
    path('<uuid:quiz_id>/submit/<uuid:attempt_id>/', views.QuizSubmitAnswerView.as_view(), name='quiz-submit'),
    path('<uuid:quiz_id>/finish/<uuid:attempt_id>/', views.QuizFinishView.as_view(), name='quiz-finish'),
]
