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
from datetime import date
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
    Viagem,
    PrevisaoViagem,
    Embarque,
    TipoStatusAprovacao,
    SentidoViagem,
    StatusViagem,
    MetodoValidacao,
)
from apps.core.mixins import TenantBaseViewSet, get_user_cliente
from apps.core.permissions import (
    IsTenantAdmin,
    IsTenantAdminOrReadOnly,
    IsMotoristaOuAdmin,
    IsAluno,
    IsMotorista,
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
    AnonimizacaoContaSerializer,
    PrevisaoViagemSerializer,
    IniciarViagemSerializer,
    ViagemDetailSerializer,
    EmbarqueQRCodeSerializer,
    EmbarqueManualSerializer,
    EmbarqueResponseSerializer,
    DashboardViagemResponseSerializer,
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


class AnonimizacaoContaView(APIView):
    """
    Endpoint de Auto-Exclusão e Anonimização de Conta do Titular (POST /api/auth/solicitar-exclusao/).
    Atendimento ao Direito de Eliminação de Dados Pessoais (LGPD Art. 18, VI).
    
    Regras Estritas de Segurança (agent.md 2.3):
    1. Zero Hard Deletes: Não executa .delete() no banco de dados.
    2. Mascaramento Irreversível de PII:
       - Pessoa.nome = "Usuário Anonimizado"
       - Pessoa.cpf = None
       - Pessoa.data_nascimento = None
       - Pessoa.endereco = None
       - Pessoa.anonimizado = True
       - Aluno.matricula = f"ANON_{id}" (se aplicável)
    3. Revogação de Credenciais:
       - UsuarioAuth.ativo = False
       - UsuarioAuth.set_unusable_password()
       - UsuarioAuth.email = f"anonimizado_{id}@appbus.local"
    4. Preservação de Histórico de Auditoria:
       - Mantém registros de Viagem, PrevisaoViagem e Embarque intactos
         para comprovação de serviço junto às prefeituras e órgãos fiscais.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = AnonimizacaoContaSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not hasattr(user, 'pessoa'):
            return Response(
                {"erro": "Usuário não possui perfil civil vinculado para anonimização."},
                status=status.HTTP_400_BAD_REQUEST
            )

        pessoa = user.pessoa
        if pessoa.anonimizado:
            return Response(
                {"mensagem": "Esta conta já se encontra devidamente anonimizada."},
                status=status.HTTP_200_OK
            )

        # Executa a rotina de anonimização (No Hard Deletes)
        pessoa.anonimizar()

        logger.info(
            f"[LGPD Anonimização] Conta de Pessoa ID={pessoa.id} e Usuario ID={user.id} "
            f"anonimizada com sucesso a pedido do titular."
        )

        return Response(
            {
                "mensagem": "Sua conta e dados pessoais foram anonimizados com sucesso conforme a LGPD. Seu acesso foi revogado.",
                "anonimizado": True
            },
            status=status.HTTP_200_OK
        )



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


# ==============================================================================
# 7. FLUXOS OPERACIONAIS CORE (Etapa 2.5 - agent.md 2.4, 2.5)
# ==============================================================================

class PredicaoDemandaView(APIView):
    """
    Endpoint de Predição de Demanda estudantil ("Vou/Não Vou").
    Rota: /api/operacao/predicao/ (GET, POST, PATCH)
    Permite ao aluno universitário autenticado declarar ou atualizar sua intenção
    diária de embarque, alimentando os algoritmos de alocação de frota.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Retorna a previsão do aluno para a data solicitada (ou data atual)."""
        if not hasattr(request.user, 'pessoa') or not hasattr(request.user.pessoa, 'aluno'):
            return Response(
                {"erro": "Acesso negado: Apenas alunos podem consultar previsão de demanda."},
                status=status.HTTP_403_FORBIDDEN
            )
        aluno = request.user.pessoa.aluno
        data_str = request.query_params.get('data')
        if data_str:
            try:
                data_alvo = date.fromisoformat(data_str)
            except ValueError:
                return Response({"erro": "Formato de data inválido. Use AAAA-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            data_alvo = date.today()

        previsao = PrevisaoViagem.objects.filter(aluno=aluno, data=data_alvo, ativo=True).first()
        if not previsao:
            return Response({
                "aluno_id": aluno.id,
                "data": data_alvo,
                "vai_ida": False,
                "vai_volta": False,
                "registrado": False
            }, status=status.HTTP_200_OK)

        return Response(PrevisaoViagemSerializer(previsao).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        return self._salvar_predicao(request)

    def patch(self, request, *args, **kwargs):
        return self._salvar_predicao(request)

    def _salvar_predicao(self, request):
        if not hasattr(request.user, 'pessoa') or not hasattr(request.user.pessoa, 'aluno'):
            return Response(
                {"erro": "Acesso negado: Apenas alunos vinculados podem registrar previsão de demanda."},
                status=status.HTTP_403_FORBIDDEN
            )
        aluno = request.user.pessoa.aluno
        if aluno.status_aprovacao != TipoStatusAprovacao.APROVADO:
            return Response(
                {"erro": "Seu cadastro ainda não foi aprovado pela prefeitura municipal para uso do transporte."},
                status=status.HTTP_400_BAD_REQUEST
            )

        data_val = request.data.get('data')
        if not data_val:
            return Response({"data": ["O campo data é obrigatório."]}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data_obj = date.fromisoformat(str(data_val))
        except ValueError:
            return Response({"data": ["Data inválida. Use o formato AAAA-MM-DD."]}, status=status.HTTP_400_BAD_REQUEST)

        vai_ida = bool(request.data.get('vai_ida', False))
        vai_volta = bool(request.data.get('vai_volta', False))

        previsao, created = PrevisaoViagem.objects.update_or_create(
            aluno=aluno,
            data=data_obj,
            defaults={
                'vai_ida': vai_ida,
                'vai_volta': vai_volta,
                'ativo': True
            }
        )

        logger.info(
            f"[Predição de Demanda] Aluno ID={aluno.id} ({aluno.pessoa.nome}) atualizou previsão para {data_obj}: "
            f"vai_ida={vai_ida}, vai_volta={vai_volta}."
        )

        serializer = PrevisaoViagemSerializer(previsao)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class IniciarViagemView(APIView):
    """
    Instanciação de Viagem pelo Motorista.
    Rota: /api/operacao/viagem/iniciar/ (POST)
    Cria uma Viagem no status 'em_andamento', associando o ônibus, a rota e o sentido.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        motorista = None
        if hasattr(user, 'pessoa') and hasattr(user.pessoa, 'motorista') and user.pessoa.motorista.ativo:
            motorista = user.pessoa.motorista
        elif user.is_superuser:
            pass
        else:
            return Response(
                {"erro": "Acesso negado: Apenas motoristas da frota municipal podem iniciar viagens."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = IniciarViagemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rota_id = serializer.validated_data['rota_id']
        onibus_id = serializer.validated_data['onibus_id']
        sentido = serializer.validated_data['sentido']

        cliente = motorista.cliente if motorista else None

        # Validação Multi-tenant: garante que a Rota e o Ônibus pertencem ao mesmo município
        rota_qs = Rota.objects.filter(id=rota_id, ativo=True)
        onibus_qs = Onibus.objects.filter(id=onibus_id, ativo=True)
        if cliente:
            rota_qs = rota_qs.filter(cliente=cliente)
            onibus_qs = onibus_qs.filter(cliente=cliente)

        rota = rota_qs.first()
        if not rota:
            return Response(
                {"erro": "Rota informada não existe, está inativa ou pertence a outro município."},
                status=status.HTTP_400_BAD_REQUEST
            )

        onibus = onibus_qs.first()
        if not onibus:
            return Response(
                {"erro": "Ônibus informado não existe, está inativo ou pertence a outro município."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Regra de concorrência: ônibus não pode ter duas viagens em andamento no mesmo dia
        if Viagem.objects.filter(onibus=onibus, status=StatusViagem.EM_ANDAMENTO, data=date.today()).exists():
            return Response(
                {"erro": f"O ônibus de placa {onibus.placa} já possui uma viagem em andamento no dia de hoje."},
                status=status.HTTP_400_BAD_REQUEST
            )

        viagem = Viagem.objects.create(
            rota=rota,
            onibus=onibus,
            motorista=motorista,
            sentido=sentido,
            status=StatusViagem.EM_ANDAMENTO,
            data=date.today(),
            hora_inicio=timezone.now(),
            ativo=True
        )

        logger.info(
            f"[Operação Viagem] Viagem ID={viagem.id} INICIADA pelo Motorista ID={motorista.id if motorista else 'SU'} "
            f"na Rota='{rota.nome}' com Ônibus='{onibus.placa}' no sentido='{sentido}'."
        )

        return Response(ViagemDetailSerializer(viagem).data, status=status.HTTP_201_CREATED)


class ConcluirViagemView(APIView):
    """
    Encerramento operacional de uma Viagem pelo motorista ou gestor.
    Rota: /api/operacao/viagem/<int:pk>/concluir/ (POST)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None, *args, **kwargs):
        viagem = Viagem.objects.filter(id=pk).first()
        if not viagem:
            return Response({"erro": "Viagem não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        # Multi-tenant check
        user_cliente = get_user_cliente(request.user)
        if not request.user.is_superuser and user_cliente and user_cliente.id != viagem.rota.cliente_id:
            return Response({"erro": "Acesso negado: Viagem de outro município."}, status=status.HTTP_403_FORBIDDEN)

        if viagem.status != StatusViagem.EM_ANDAMENTO:
            return Response(
                {"erro": f"Esta viagem não pode ser concluída pois está com status '{viagem.get_status_display()}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        viagem.status = StatusViagem.CONCLUIDA
        viagem.hora_fim = timezone.now()
        viagem.save(update_fields=['status', 'hora_fim', 'updated_at'])

        logger.info(f"[Operação Viagem] Viagem ID={viagem.id} CONCLUÍDA com sucesso.")
        return Response(ViagemDetailSerializer(viagem).data, status=status.HTTP_200_OK)


class EmbarqueQRCodeView(APIView):
    """
    Validação de Embarque Óptico via Leitura de QR Code pelo Aluno.
    Rota: /api/operacao/embarque/qrcode/ (POST)
    Localiza o ônibus pelo UUID óptico, verifica a viagem em andamento e registra o embarque.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        if not hasattr(user, 'pessoa') or not hasattr(user.pessoa, 'aluno'):
            return Response(
                {"erro": "Apenas alunos cadastrados podem realizar check-in por QR Code."},
                status=status.HTTP_403_FORBIDDEN
            )

        aluno = user.pessoa.aluno
        if aluno.status_aprovacao != TipoStatusAprovacao.APROVADO:
            return Response(
                {"erro": "Seu cadastro precisa estar aprovado pela prefeitura para validar embarques."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = EmbarqueQRCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        qr_code_uuid = serializer.validated_data['qr_code_uuid']

        onibus = Onibus.objects.filter(qr_code_uuid=qr_code_uuid, ativo=True).first()
        if not onibus:
            return Response(
                {"erro": "QR Code inválido: nenhum veículo correspondente foi localizado ou o veículo está inativo."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Multi-tenant: Garante que o ônibus é do mesmo município do aluno
        if onibus.cliente_id != aluno.cliente_id:
            return Response(
                {"erro": "Acesso negado: Este ônibus pertence a outro município."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Localiza a viagem em andamento para este ônibus hoje
        viagem = Viagem.objects.filter(
            onibus=onibus,
            status=StatusViagem.EM_ANDAMENTO,
            data=date.today()
        ).first()

        if not viagem:
            return Response(
                {"erro": "Não há nenhuma viagem em andamento para este ônibus no momento. Aguarde o motorista iniciar a viagem."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Anti-fraude: impede duplicidade de embarque na mesma viagem
        if Embarque.objects.filter(viagem=viagem, aluno=aluno).exists():
            return Response(
                {"erro": "Embarque já registrado anteriormente nesta viagem."},
                status=status.HTTP_400_BAD_REQUEST
            )

        embarque = Embarque.objects.create(
            viagem=viagem,
            aluno=aluno,
            metodo_validacao=MetodoValidacao.QR_CODE_APP,
            timestamp=timezone.now(),
            ativo=True
        )

        logger.info(
            f"[Embarque QR Code] Aluno ID={aluno.id} ({aluno.pessoa.nome}) embarcou com sucesso no Ônibus={onibus.placa} "
            f"na Viagem ID={viagem.id}."
        )

        return Response(EmbarqueResponseSerializer(embarque).data, status=status.HTTP_201_CREATED)


class EmbarqueManualView(APIView):
    """
    Check-in Manual efetuado pelo Motorista no app.
    Rota: /api/operacao/embarque/manual/ (POST)
    Permite validar embarque de alunos em casos de contingência (sem bateria ou sem sinal).
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        motorista = None
        if hasattr(user, 'pessoa') and hasattr(user.pessoa, 'motorista') and user.pessoa.motorista.ativo:
            motorista = user.pessoa.motorista
        elif user.is_superuser:
            pass
        else:
            return Response(
                {"erro": "Acesso negado: Apenas motoristas da frota municipal podem realizar check-in manual."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = EmbarqueManualSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        viagem_id = serializer.validated_data['viagem_id']
        aluno_id = serializer.validated_data['aluno_id']

        viagem = Viagem.objects.select_related('rota__cliente', 'onibus').filter(id=viagem_id).first()
        if not viagem:
            return Response({"erro": "Viagem não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if viagem.status != StatusViagem.EM_ANDAMENTO:
            return Response(
                {"erro": f"Esta viagem não está em andamento (status atual: {viagem.get_status_display()})."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if motorista and viagem.onibus.cliente_id != motorista.cliente_id:
            return Response(
                {"erro": "Acesso negado: Esta viagem pertence a outro município."},
                status=status.HTTP_403_FORBIDDEN
            )

        aluno = Aluno.objects.filter(id=aluno_id, cliente=viagem.rota.cliente).first()
        if not aluno:
            return Response(
                {"erro": "Aluno não encontrado ou não pertence ao município desta viagem."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Anti-fraude: impede duplicidade
        if Embarque.objects.filter(viagem=viagem, aluno=aluno).exists():
            return Response(
                {"erro": f"O aluno {aluno.pessoa.nome} já possui embarque registrado nesta viagem."},
                status=status.HTTP_400_BAD_REQUEST
            )

        embarque = Embarque.objects.create(
            viagem=viagem,
            aluno=aluno,
            metodo_validacao=MetodoValidacao.MANUAL_MOTORISTA,
            timestamp=timezone.now(),
            ativo=True
        )

        logger.info(
            f"[Embarque Manual] Motorista registrou embarque manual para Aluno ID={aluno.id} "
            f"na Viagem ID={viagem.id}."
        )

        return Response(EmbarqueResponseSerializer(embarque).data, status=status.HTTP_201_CREATED)


class DashboardViagemView(APIView):
    """
    Dashboard em Tempo Real do Motorista (agent.md 2.5 Performance Constraints).
    Rota: /api/operacao/viagem/<int:pk>/dashboard/ (GET)
    Executa agregações diretas via COUNT() no banco de dados sem trafegar listas no frontend.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None, *args, **kwargs):
        viagem = Viagem.objects.select_related(
            'rota__cliente',
            'onibus',
            'motorista__pessoa'
        ).filter(id=pk).first()

        if not viagem:
            return Response({"erro": "Viagem não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        # Isolamento Multi-tenant
        user_cliente = get_user_cliente(request.user)
        if not request.user.is_superuser and user_cliente and user_cliente.id != viagem.rota.cliente_id:
            return Response({"erro": "Acesso negado: Viagem pertencente a outro município."}, status=status.HTTP_403_FORBIDDEN)

        # Agregações diretas no PostgreSQL (agent.md 2.5)
        total_embarcados = viagem.embarques.filter(ativo=True).count()

        # Contagem de alunos com intenção confirmada para a data e sentido da viagem
        predicoes_qs = PrevisaoViagem.objects.filter(
            data=viagem.data,
            aluno__cliente=viagem.rota.cliente,
            ativo=True
        )
        if viagem.sentido == SentidoViagem.IDA:
            total_previstos = predicoes_qs.filter(vai_ida=True).count()
        else:
            total_previstos = predicoes_qs.filter(vai_volta=True).count()

        capacidade = viagem.onibus.capacidade
        vagas_restantes = max(0, capacidade - total_embarcados)
        ocupacao = round((total_embarcados / capacidade) * 100, 1) if capacidade > 0 else 0.0

        dados_dashboard = {
            "viagem_id": viagem.id,
            "rota_nome": viagem.rota.nome,
            "onibus_placa": viagem.onibus.placa,
            "motorista_nome": viagem.motorista.pessoa.nome if viagem.motorista else "Não atribuído",
            "sentido": viagem.sentido,
            "sentido_display": viagem.get_sentido_display(),
            "status": viagem.status,
            "status_display": viagem.get_status_display(),
            "data": viagem.data,
            "hora_inicio": viagem.hora_inicio,
            "capacidade_onibus": capacidade,
            "total_previstos": total_previstos,
            "total_embarcados": total_embarcados,
            "vagas_restantes": vagas_restantes,
            "percentual_ocupacao": ocupacao,
        }

        return Response(DashboardViagemResponseSerializer(dados_dashboard).data, status=status.HTTP_200_OK)


