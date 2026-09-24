"""
Core API Views for AppBus.

Architectural Guidelines (agent.md):
- Multi-tenancy (2.1):
  - CustomTokenObtainPairView embeds cliente_id and role into JWT claims.
  - TenantBaseViewSet enforces Zero-Trust isolation by filtering all querysets by request.user.pessoa.cliente_id.
  - Perform_create and perform_update strictly inject the user's tenant, preventing payload injection.
- Party/Role Pattern (2.2):
  - AlunoRegistroView guarantees atomic creation of UsuarioAuth -> Pessoa -> Aluno -> Registro_Consentimento.
- LGPD Compliance (2.3):
  - No client-supplied IP/User-Agent in payload; strictly inferred from HTTP request headers.
  - Legal documents list for informed consent prior to onboarding.
  - Passwords strictly hashed.
"""

import logging
from django.db import transaction, connection
from rest_framework import generics, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.models import (
    Documento_Legal,
    Aluno,
    Instituicao,
    ModeloVeiculo,
    Onibus,
    Motorista,
    Rota,
)
from apps.core.mixins import TenantBaseViewSet, get_user_cliente
from apps.core.serializers import (
    CustomTokenObtainPairSerializer,
    AlunoRegistroSerializer,
    AlunoDetalheResponseSerializer,
    DocumentoLegalSerializer,
    InstituicaoSerializer,
    ModeloVeiculoSerializer,
    OnibusSerializer,
    MotoristaSerializer,
    RotaSerializer,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. INFRAESTRUTURA & HEALTH CHECK
# ==============================================================================

class HealthCheckView(APIView):
    """
    Health check endpoint para validação do status do backend e PostgreSQL.
    Acesso público sem autenticação.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        db_ok = False
        db_error = None
        try:
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


# ==============================================================================
# 2. AUTENTICAÇÃO JWT CUSTOMIZADA (agent.md 2.1 Multi-Tenancy & Claims)
# ==============================================================================

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Endpoint de Login JWT (POST /api/token/).
    Retorna access e refresh tokens com claims customizadas de Multi-tenancy
    (cliente_id, role, pessoa_id, nome, status_aprovacao).
    """
    serializer_class = CustomTokenObtainPairSerializer


# ==============================================================================
# 3. ONBOARDING E CADASTRO DE ALUNOS (Etapa 2.1 - Party/Role & LGPD)
# ==============================================================================

class AlunoRegistroView(generics.CreateAPIView):
    """
    Endpoint de Auto-Cadastro de Alunos (POST /api/auth/registro-aluno/).
    
    Auditoria e Regras Arquiteturais Estritas:
    1. LGPD: IP e User-Agent são OBRIGATORIAMENTE inferidos do objeto HTTP request
       (nunca aceitos nem lidos do corpo JSON da requisição).
    2. Transação Atômica: Toda a operação é executada dentro de transaction.atomic,
       assegurando que falhas não deixem registros órfãos nas 4 tabelas envolvidas
       (UsuarioAuth, Pessoa, Aluno, Registro_Consentimento).
    3. Senhas Seguras: Senha criptografada via create_user() com algoritmo de hash
       (PBKDF2/Argon2), nunca armazenada em texto puro.
    """
    permission_classes = [AllowAny]
    serializer_class = AlunoRegistroSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # Injeta estritamente o request no contexto para extração segura de IP/User-Agent
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        try:
            aluno = serializer.save()
        except Exception as e:
            logger.error(f"[Onboarding Aluno Erro] Falha crítica na transação de cadastro: {str(e)}", exc_info=True)
            raise e

        # Formatação estruturada da resposta para o cliente PWA
        response_data = {
            "mensagem": "Cadastro realizado com sucesso! Sua solicitação foi enviada para aprovação da prefeitura.",
            "aluno": AlunoDetalheResponseSerializer(aluno).data
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


# ==============================================================================
# 4. GOVERNANÇA LGPD (Exibição de Termos de Uso Vigentes)
# ==============================================================================

class DocumentoLegalVigenteListView(generics.ListAPIView):
    """
    Endpoint público (GET /api/documentos-legais/vigentes/).
    Lista os Termos de Uso e Políticas de Privacidade ativos para que o frontend
    PWA exiba ao aluno durante o cadastro e obtenha o consentimento informado.
    """
    permission_classes = [AllowAny]
    serializer_class = DocumentoLegalSerializer
    queryset = Documento_Legal.objects.filter(ativo=True).order_by('-data_publicacao')


# ==============================================================================
# 5. VIEWSETS CORE COM ISOLAMENTO MULTI-TENANT (Etapa 2.2 - agent.md 2.1)
# ==============================================================================

class InstituicaoViewSet(TenantBaseViewSet):
    """
    Gestão de Instituições de Ensino vinculadas ao município (Tenant).
    Herda isolamento completo de leitura e escrita de TenantBaseViewSet.
    """
    queryset = Instituicao.objects.all()
    serializer_class = InstituicaoSerializer


class ModeloVeiculoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Catálogo Global de Modelos de Veículos (Marcopolo, Mercedes-Benz, etc.).
    Não possui cliente_id; acessível como leitura compartilhada para todos os municípios.
    """
    permission_classes = [IsAuthenticated]
    queryset = ModeloVeiculo.objects.filter(ativo=True)
    serializer_class = ModeloVeiculoSerializer


class OnibusViewSet(TenantBaseViewSet):
    """
    Gestão da Frota Municipal de Ônibus.
    Isolamento estrito: um administrador da "Prefeitura A" só acessa os veículos
    da "Prefeitura A". O payload cliente_id é sumariamente ignorado na criação.
    """
    queryset = Onibus.objects.select_related('modelo', 'cliente').all()
    serializer_class = OnibusSerializer


class MotoristaViewSet(TenantBaseViewSet):
    """
    Gestão de Motoristas Municipais.
    Padrão Party/Role: vincula a entidade Pessoa e o papel de Motorista à prefeitura do usuário.
    """
    queryset = Motorista.objects.select_related('pessoa', 'cliente').all()
    serializer_class = MotoristaSerializer


class RotaViewSet(TenantBaseViewSet):
    """
    Gestão das Rotas e Itinerários Municipais.
    """
    queryset = Rota.objects.prefetch_related('rota_instituicoes__instituicao').all()
    serializer_class = RotaSerializer
