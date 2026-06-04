from django.urls import path
from .views import (
    AdminCallLogCreateView,
    AdminClassRequestDetailView,
    AdminClassRequestListView,
    AdminPlanDetailView,
    AdminPlanListView,
    AdminStepUpdateView,
    ClassRequestView,
    MyPlanView,
    MyProgressView,
    StepCompleteView,
    StepReportDelayView,
    TodayStepsView,
)

app_name = 'automatic_class'

urlpatterns = [
    # User — class request
    path('request/', ClassRequestView.as_view(), name='class-request'),

    # User — plan & steps
    path('my-plan/', MyPlanView.as_view(), name='my-plan'),
    path('today/', TodayStepsView.as_view(), name='today-steps'),
    path('progress/', MyProgressView.as_view(), name='my-progress'),
    path('steps/<uuid:step_id>/complete/', StepCompleteView.as_view(), name='step-complete'),
    path('steps/<uuid:step_id>/report/', StepReportDelayView.as_view(), name='step-report'),

    # Admin — class requests
    path('admin/requests/', AdminClassRequestListView.as_view(), name='admin-requests'),
    path('admin/requests/<uuid:request_id>/', AdminClassRequestDetailView.as_view(), name='admin-request-detail'),

    # Admin — plans
    path('admin/plans/', AdminPlanListView.as_view(), name='admin-plans'),
    path('admin/plans/<uuid:plan_id>/', AdminPlanDetailView.as_view(), name='admin-plan-detail'),

    # Admin — step override
    path('admin/steps/<uuid:step_id>/', AdminStepUpdateView.as_view(), name='admin-step-update'),

    # Admin — call log
    path('admin/calls/', AdminCallLogCreateView.as_view(), name='admin-call-log'),
]
