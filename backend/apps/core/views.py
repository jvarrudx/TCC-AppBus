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
from django.utils import timezone
from rest_framework import generics, viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
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
    TipoStatusAprovacao,
)
from apps.core.mixins import TenantBaseViewSet, get_user_cliente
from apps.core.permissions import (
    IsTenantAdmin,
    IsTenantAdminOrReadOnly,
    IsMotoristaOuAdmin,
)
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
    AlunoGestaoListSerializer,
    AlunoGestaoDetailSerializer,
    AlunoDecisaoSerializer,
    MotoristaCreateSerializer,
    RotaCreateUpdateSerializer,
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
# 5. VIEWSETS CORE COM ISOLAMENTO MULTI-TENANT & GESTÃO (Etapas 2.2 e 2.3)
# ==============================================================================

class InstituicaoViewSet(TenantBaseViewSet):
    """
    Gestão de Instituições de Ensino vinculadas ao município (Tenant).
    Leitura autorizada para usuários do mesmo município; escrita restrita a administradores.
    """
    permission_classes = [IsTenantAdminOrReadOnly]
    queryset = Instituicao.objects.select_related('endereco').all()
    serializer_class = InstituicaoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'sigla']
    ordering = ['nome']


class ModeloVeiculoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Catálogo Global de Modelos de Veículos (Marcopolo, Mercedes-Benz, etc.).
    Não possui cliente_id; acessível como leitura compartilhada para todos os municípios.
    """
    permission_classes = [IsAuthenticated]
    queryset = ModeloVeiculo.objects.filter(ativo=True)
    serializer_class = ModeloVeiculoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['marca', 'nome']
    ordering = ['marca', 'nome']


class OnibusViewSet(TenantBaseViewSet):
    """
    Gestão da Frota Municipal de Ônibus.
    Isolamento estrito: um administrador da "Prefeitura A" só acessa os veículos
    da "Prefeitura A". O payload cliente_id é sumariamente ignorado na criação.
    """
    permission_classes = [IsTenantAdminOrReadOnly]
    queryset = Onibus.objects.select_related('modelo', 'cliente').all()
    serializer_class = OnibusSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['placa', 'modelo__nome', 'modelo__marca']
    ordering = ['placa']


class MotoristaViewSet(TenantBaseViewSet):
    """
    Gestão de Motoristas Municipais.
    Padrão Party/Role: vincula a entidade Pessoa e o papel de Motorista à prefeitura do usuário.
    Criação atômica pelo Administrador Municipal via MotoristaCreateSerializer.
    """
    permission_classes = [IsTenantAdminOrReadOnly]
    queryset = Motorista.objects.select_related('pessoa__usuario', 'cliente').all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['pessoa__nome', 'pessoa__cpf', 'cnh']
    ordering = ['pessoa__nome']

    def get_serializer_class(self):
        if self.action == 'create':
            return MotoristaCreateSerializer
        return MotoristaSerializer


class RotaViewSet(TenantBaseViewSet):
    """
    Gestão das Rotas e Itinerários Municipais.
    Suporte a inserção transacional e ordenação de paradas de instituições (RotaInstituicao).
    """
    permission_classes = [IsTenantAdminOrReadOnly]
    queryset = Rota.objects.prefetch_related('rota_instituicoes__instituicao').all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome']
    ordering = ['nome']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RotaCreateUpdateSerializer
        return RotaSerializer


# ==============================================================================
# 6. GESTÃO DE ALUNOS & FILA DE APROVAÇÃO (Etapa 2.3 - agent.md 2.1, 2.2, 2.5)
# ==============================================================================

class AlunoViewSet(TenantBaseViewSet):
    """
    Painel de Gestão e Auditoria de Alunos Passageiros da Prefeitura.
    
    Regras Estritas de Segurança (agent.md):
    1. Acesso restrito a Administradores Municipais da prefeitura (IsTenantAdmin).
    2. Isolamento por Tenant: lista e avalia exclusivamente alunos do seu próprio município.
    3. Fila de Aprovação (Workflow):
       - GET /api/alunos/fila-pendente/ : Retorna alunos que aguardam validação do gestor.
       - POST /api/alunos/{id}/aprovar/ : Concede aprovação, gravando avaliador e timestamp.
       - POST /api/alunos/{id}/rejeitar/ : Nega a solicitação de transporte, gravando avaliador.
    """
    permission_classes = [IsTenantAdmin]
    queryset = Aluno.objects.select_related('pessoa__usuario', 'instituicao', 'avaliado_por__pessoa').all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['pessoa__nome', 'pessoa__cpf', 'matricula', 'instituicao__nome']
    ordering_fields = ['data_solicitacao', 'data_decisao', 'status_aprovacao']
    ordering = ['-data_solicitacao']

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status_aprovacao=status_param.lower().strip())

        inst_id = self.request.query_params.get('instituicao_id')
        if inst_id and str(inst_id).isdigit():
            qs = qs.filter(instituicao_id=int(inst_id))

        return qs

    def get_serializer_class(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            return AlunoGestaoDetailSerializer
        if self.action in ['aprovar', 'rejeitar']:
            return AlunoDecisaoSerializer
        return AlunoGestaoListSerializer

    @action(detail=False, methods=['get'], url_path='fila-pendente')
    def fila_pendente(self, request):
        """
        Retorna exclusivamente os alunos em fila com status 'pendente',
        ordenados cronologicamente por ordem de solicitação (FIFO).
        """
        alunos_pendentes = self.get_queryset().filter(
            status_aprovacao=TipoStatusAprovacao.PENDENTE
        ).order_by('data_solicitacao')

        page = self.paginate_queryset(alunos_pendentes)
        if page is not None:
            serializer = AlunoGestaoListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AlunoGestaoListSerializer(alunos_pendentes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='aprovar')
    def aprovar(self, request, pk=None):
        """
        Aprova o cadastro do estudante universitário para utilização do transporte.
        Registra a data da decisão e o administrador responsável pela auditoria.
        """
        aluno = self.get_object()

        # Resolução do Administrador autenticado responsável pela aprovação
        admin = None
        if hasattr(request.user, 'pessoa') and hasattr(request.user.pessoa, 'administrador'):
            admin = request.user.pessoa.administrador

        aluno.status_aprovacao = TipoStatusAprovacao.APROVADO
        aluno.data_decisao = timezone.now()
        aluno.avaliado_por = admin
        aluno.save(update_fields=['status_aprovacao', 'data_decisao', 'avaliado_por'])

        logger.info(
            f"[Fila Alunos] Aluno ID={aluno.id} ({aluno.pessoa.nome}) APROVADO "
            f"por Administrador={admin} no Tenant={aluno.cliente_id}."
        )
        return Response(
            AlunoGestaoDetailSerializer(aluno).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='rejeitar')
    def rejeitar(self, request, pk=None):
        """
        Rejeita a solicitação cadastral do estudante universitário.
        Registra a data da decisão e o administrador avaliador.
        """
        aluno = self.get_object()

        admin = None
        if hasattr(request.user, 'pessoa') and hasattr(request.user.pessoa, 'administrador'):
            admin = request.user.pessoa.administrador

        aluno.status_aprovacao = TipoStatusAprovacao.REJEITADO
        aluno.data_decisao = timezone.now()
        aluno.avaliado_por = admin
        aluno.save(update_fields=['status_aprovacao', 'data_decisao', 'avaliado_por'])

        logger.info(
            f"[Fila Alunos] Aluno ID={aluno.id} ({aluno.pessoa.nome}) REJEITADO "
            f"por Administrador={admin} no Tenant={aluno.cliente_id}."
        )
        return Response(
            AlunoGestaoDetailSerializer(aluno).data,
            status=status.HTTP_200_OK
        )

