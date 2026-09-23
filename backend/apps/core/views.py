"""
Core API Views for AppBus.

Architectural Guidelines (agent.md):
- Multi-tenancy (2.1): CustomTokenObtainPairView embeds cliente_id and role.
- Party/Role Pattern (2.2): AlunoRegistroView guarantees atomic creation of
  UsuarioAuth -> Pessoa -> Aluno -> Registro_Consentimento.
- LGPD Compliance (2.3):
  1. No client-supplied IP/User-Agent in payload; strictly inferred from HTTP request headers.
  2. Legal documents list for informed consent prior to onboarding.
  3. No plaintext passwords.
"""

import logging
from django.db import transaction, connection
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.models import Documento_Legal, Aluno
from apps.core.serializers import (
    CustomTokenObtainPairSerializer,
    AlunoRegistroSerializer,
    AlunoDetalheResponseSerializer,
    DocumentoLegalSerializer,
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
