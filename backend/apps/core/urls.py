"""
URL routing for AppBus Core Application.
"""

from django.urls import path
from apps.core.views import (
    HealthCheckView,
    AlunoRegistroView,
    DocumentoLegalVigenteListView,
)

urlpatterns = [
    # Infraestrutura
    path('health/', HealthCheckView.as_view(), name='health_check'),

    # Autenticação e Onboarding de Alunos (Etapa 2.1)
    path('auth/registro-aluno/', AlunoRegistroView.as_view(), name='aluno_registro'),

    # Governança e LGPD
    path('documentos-legais/vigentes/', DocumentoLegalVigenteListView.as_view(), name='documentos_legais_vigentes'),
]
