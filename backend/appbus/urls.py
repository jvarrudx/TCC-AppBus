"""
Root URL configuration for AppBus project.
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from apps.core.views import CustomTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT Authentication Endpoints (com claims enriquecidas para Multi-tenancy)
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Core app routes
    path('api/', include('apps.core.urls')),
]
