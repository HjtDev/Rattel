"""
URL configuration for RattelBackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.http import JsonResponse
from .views import TinyMCEImageUploadView


def healthz(_request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('healthz/', healthz),
    path('api/v1/editor/upload/', TinyMCEImageUploadView.as_view(), name='editor-upload'),
    path('api/v1/users/', include('users.urls')),
    path('api/v1/payment/', include('payment.urls', namespace='payment')),
    path('api/v1/auth/', include('authentication.urls', namespace='authentication')),
    path('api/v1/site/', include('siteconfig.urls', namespace='siteconfig')),
    path('api/v1/courses/', include('courses.urls', namespace='courses')),
    path('api/v1/cart/', include('cart.urls', namespace='cart')),
    path('api/v1/tickets/', include('tickets.urls', namespace='tickets')),
    path('api/v1/blog/', include('blog.urls', namespace='blog')),
    path('api/v1/gallery/', include('gallery.urls', namespace='gallery')),
    path('api/v1/subscriptions/', include('subscriptions.urls', namespace='subscriptions')),
    path('api/v1/class/automatic/', include('automatic_class.urls', namespace='automatic')),
    path('api/v1/class/in-person/', include('in_person_class.urls', namespace='in_person_class')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
