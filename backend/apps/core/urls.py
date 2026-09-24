"""
URL routing for AppBus Core Application.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.core.views import (
    HealthCheckView,
    AlunoRegistroView,
    DocumentoLegalVigenteListView,
    InstituicaoViewSet,
    ModeloVeiculoViewSet,
    OnibusViewSet,
    MotoristaViewSet,
    RotaViewSet,
)

# Router para endpoints RESTful Multi-Tenant
router = DefaultRouter()
router.register('instituicoes', InstituicaoViewSet, basename='instituicao')
router.register('veiculos/modelos', ModeloVeiculoViewSet, basename='modelo_veiculo')
router.register('veiculos/onibus', OnibusViewSet, basename='onibus')
router.register('motoristas', MotoristaViewSet, basename='motorista')
router.register('rotas', RotaViewSet, basename='rota')

urlpatterns = [
    # Infraestrutura
    path('health/', HealthCheckView.as_view(), name='health_check'),

    # Autenticação e Onboarding de Alunos (Etapa 2.1)
    path('auth/registro-aluno/', AlunoRegistroView.as_view(), name='aluno_registro'),

    # Governança e LGPD
    path('documentos-legais/vigentes/', DocumentoLegalVigenteListView.as_view(), name='documentos_legais_vigentes'),

    # Endpoints de Gestão com Isolamento Multi-Tenant (Etapa 2.2)
    path('', include(router.urls)),
]
