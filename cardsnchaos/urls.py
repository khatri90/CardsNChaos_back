"""
URL configuration for cardsnchaos project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    """Health check endpoint for deployment platform"""
    return JsonResponse({'status': 'healthy', 'service': 'cardsnchaos-backend'})

urlpatterns = [
    path('', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
]
