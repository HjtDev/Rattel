from django.urls import path, re_path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.BlogListView.as_view(), name='blog-list'),
    path('meta/', views.BlogMetaView.as_view(), name='blog-meta'),
    path('saved-posts/', views.MySavedBlogPostsView.as_view(), name='saved-posts'),
    re_path(r'^(?P<slug>[-\w]+)/$', views.BlogDetailView.as_view(), name='blog-detail'),
    re_path(r'^(?P<slug>[-\w]+)/view-count/$', views.BlogViewCountView.as_view(), name='blog-view-count'),
    re_path(r'^(?P<slug>[-\w]+)/toggle-save/$', views.ToggleSaveBlogPostView.as_view(), name='toggle-save'),
    re_path(r'^(?P<slug>[-\w]+)/comments/$', views.BlogCommentListCreateView.as_view(), name='blog-comments'),
]
