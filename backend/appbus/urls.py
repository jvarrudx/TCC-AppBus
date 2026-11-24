"""
Root URL configuration for AppBus project.
"""

from django.contrib import admin
from django.urls import path, include
from apps.core.views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomLogoutView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT Authentication Endpoints (OWASP ASVS / LGPD Cookies HttpOnly)
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/logout/', CustomLogoutView.as_view(), name='token_logout'),

    # Core app routes
    path('api/', include('apps.core.urls')),
]
