from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.BlogListView.as_view(), name='blog-list'),
    path('meta/', views.BlogMetaView.as_view(), name='blog-meta'),
    path('saved-posts/', views.MySavedBlogPostsView.as_view(), name='saved-posts'),
    path('<uuid:post_id>/', views.BlogDetailView.as_view(), name='blog-detail'),
    path('<uuid:post_id>/view-count/', views.BlogViewCountView.as_view(), name='blog-view-count'),
    path('<uuid:post_id>/toggle-save/', views.ToggleSaveBlogPostView.as_view(), name='toggle-save'),
    path('<uuid:post_id>/comments/', views.BlogCommentListCreateView.as_view(), name='blog-comments'),
]
