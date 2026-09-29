"""
URL routing for AppBus Core Application.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.core.views import (
    HealthCheckView,
    AlunoRegistroView,
    DocumentoLegalVigenteListView,
    DadosAdesaoPublicView,
    InstituicaoViewSet,
    ModeloVeiculoViewSet,
    OnibusViewSet,
    MotoristaViewSet,
    RotaViewSet,
    AlunoViewSet,
    AnonimizacaoContaView,
    PredicaoDemandaView,
    IniciarViagemView,
    ConcluirViagemView,
    EmbarqueQRCodeView,
    EmbarqueManualView,
    DashboardViagemView,
)

# Router para endpoints RESTful Multi-Tenant
router = DefaultRouter()
router.register('instituicoes', InstituicaoViewSet, basename='instituicao')
router.register('veiculos/modelos', ModeloVeiculoViewSet, basename='modelo_veiculo')
router.register('veiculos/onibus', OnibusViewSet, basename='onibus')
router.register('motoristas', MotoristaViewSet, basename='motorista')
router.register('rotas', RotaViewSet, basename='rota')
router.register('alunos', AlunoViewSet, basename='aluno')

urlpatterns = [
    # Infraestrutura
    path('health/', HealthCheckView.as_view(), name='health_check'),

    # Autenticação e Onboarding de Alunos (Etapa 2.1 & 3.2)
    path('auth/registro-aluno/', AlunoRegistroView.as_view(), name='aluno_registro'),
    path('public/dados-adesao/', DadosAdesaoPublicView.as_view(), name='dados_adesao_public'),

    # Governança e LGPD (Etapa 2.4 - Direito ao Esquecimento sem Hard Deletes)
    path('documentos-legais/vigentes/', DocumentoLegalVigenteListView.as_view(), name='documentos_legais_vigentes'),
    path('auth/solicitar-exclusao/', AnonimizacaoContaView.as_view(), name='solicitar_exclusao'),

    # Fluxos Operacionais Core (Etapa 2.5 - Predição, Viagem, Embarque e Dashboard)
    path('operacao/predicao/', PredicaoDemandaView.as_view(), name='operacao_predicao'),
    path('operacao/viagem/iniciar/', IniciarViagemView.as_view(), name='operacao_viagem_iniciar'),
    path('operacao/viagem/<int:pk>/concluir/', ConcluirViagemView.as_view(), name='operacao_viagem_concluir'),
    path('operacao/viagem/<int:pk>/dashboard/', DashboardViagemView.as_view(), name='operacao_viagem_dashboard'),
    path('operacao/embarque/qrcode/', EmbarqueQRCodeView.as_view(), name='operacao_embarque_qrcode'),
    path('operacao/embarque/manual/', EmbarqueManualView.as_view(), name='operacao_embarque_manual'),

    # Endpoints de Gestão com Isolamento Multi-Tenant (Etapa 2.2)
    path('', include(router.urls)),
]
