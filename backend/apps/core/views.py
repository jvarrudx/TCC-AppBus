"""
Core API Views.
Includes health check to verify database connectivity.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.db import connection

class HealthCheckView(APIView):
    """
    Health check endpoint to verify API and PostgreSQL database status.
    Accessible publicly without authentication.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        db_ok = False
        db_error = None
        try:
            # Check database connection
            connection.ensure_connection()
            db_ok = True
        except Exception as e:
            db_error = str(e)

        payload = {
            "status": "healthy" if db_ok else "unhealthy",
            "service": "AppBus Backend API",
            "version": "1.0.0",
            "database": {
                "connected": db_ok,
                "engine": connection.vendor,
                "error": db_error
            }
        }

        http_status = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(payload, status=http_status)
