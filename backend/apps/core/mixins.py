"""
Multi-Tenant Isolation Mixins and Base ViewSets for AppBus.

Architectural Guidelines (agent.md 2.1):
- Zero Trust Security: Every query, ViewSet, and operation MUST be isolated by user's cliente_id.
- Overwrite get_queryset in DRF to enforce this based on request.user.pessoa.cliente_id.
- Prevent Payload Injection: Override perform_create and perform_update to ignore any
  cliente_id sent in request body, forcing the user's authenticated tenant.
"""

import logging
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from apps.core.models import Cliente

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. UTILITÁRIO DE RESOLUÇÃO DE TENANT (Party/Role -> Cliente)
# ==============================================================================

def get_user_cliente(user) -> Cliente | None:
    """
    Descobre e retorna com segurança o Cliente (Prefeitura/Empresa conveniada)
    vinculado ao usuário autenticado, navegando pelo padrão Party/Role.

    Hierarquia inspecionada:
    UsuarioAuth <-> Pessoa (Party) <-> Roles [Administrador | Aluno | Motorista] -> Cliente
    """
    if not user or not user.is_authenticated:
        return None

    if hasattr(user, 'pessoa'):
        pessoa = user.pessoa
        # 1. Administrador Municipal (Gestor do Contrato)
        if hasattr(pessoa, 'administrador') and pessoa.administrador.ativo:
            return pessoa.administrador.cliente
        # 2. Motorista da Frota
        if hasattr(pessoa, 'motorista') and pessoa.motorista.ativo:
            return pessoa.motorista.cliente
        # 3. Aluno / Universitário passageiro
        if hasattr(pessoa, 'aluno'):
            return pessoa.aluno.cliente

    return None


def get_user_cliente_id(user) -> int | None:
    """Retorna o ID do cliente/prefeitura associado ao usuário."""
    cliente = get_user_cliente(user)
    return cliente.id if cliente else None


# ==============================================================================
# 2. VIEWSET BASE COM ISOLAMENTO MULTI-TENANT (TenantBaseViewSet)
# ==============================================================================

class TenantBaseViewSet(viewsets.ModelViewSet):
    """
    Classe Base para todos os ViewSets transacionais e de gestão do AppBus.
    
    Garantias Arquiteturais Estritas (agent.md 2.1):
    1. Zero Trust: Apenas usuários autenticados têm acesso (IsAuthenticated).
    2. Isolamento de Leitura (get_queryset): Filtra obrigatoriamente os registros
       pelo cliente_id do usuário autenticado. Um gestor da "Prefeitura A" NUNCA
       receberá dados da "Prefeitura B".
    3. Blindagem de Escrita (perform_create & perform_update): Descarta qualquer
       'cliente' ou 'cliente_id' enviado no corpo JSON da requisição (Payload Injection)
       e injeta imperativamente o Tenant do usuário logado.
    """
    permission_classes = [IsAuthenticated]

    def get_tenant(self) -> Cliente:
        """
        Recupera o Tenant ativo da sessão/token JWT.
        Lança PermissionDenied caso o usuário não tenha vínculo legítimo com uma prefeitura ativa.
        """
        user = self.request.user
        cliente = get_user_cliente(user)

        if cliente:
            return cliente

        # Tratamento especial para Superusuários / Desenvolvedores AppBus
        if user.is_superuser:
            # Permite simulação/filtro de tenant específico via cabeçalho HTTP 'X-Tenant-ID'
            tenant_header = self.request.META.get('HTTP_X_TENANT_ID')
            if tenant_header and str(tenant_header).isdigit():
                try:
                    return Cliente.objects.get(id=int(tenant_header), ativo=True)
                except Cliente.DoesNotExist:
                    raise PermissionDenied(f"Tenant '{tenant_header}' informado no header X-Tenant-ID não existe ou está inativo.")
            return None

        # Falha de segurança: usuário sem Tenant vinculado
        logger.warning(f"[Security Warning] Usuário ID={user.id} ({user.email}) tentou acessar endpoint com escopo de tenant sem vínculo ativo.")
        raise PermissionDenied("Acesso negado: Sua conta não está vinculada a nenhuma prefeitura ou cliente ativo.")

    def get_queryset(self):
        """
        Sobrescreve o get_queryset do DRF para garantir segregação estrita por tenant.
        """
        qs = super().get_queryset()
        user = self.request.user

        # Superusuário sem header X-Tenant-ID tem visão global de suporte
        if user.is_superuser and not self.request.META.get('HTTP_X_TENANT_ID'):
            return qs

        cliente = self.get_tenant()
        if not cliente:
            return qs.none()

        model = qs.model

        # 1. Entidades com chave direta para Cliente (Onibus, Rota, Instituicao, Motorista, Aluno, Administrador)
        if hasattr(model, 'cliente'):
            return qs.filter(cliente=cliente)
        elif hasattr(model, 'cliente_id'):
            return qs.filter(cliente_id=cliente.id)
        elif model == Cliente:
            return qs.filter(id=cliente.id)

        # 2. Entidades relacionais de segundo nível (Viagem, RotaInstituicao, PrevisaoViagem, Embarque)
        model_name = model.__name__
        if model_name in ('Viagem', 'RotaInstituicao'):
            return qs.filter(rota__cliente=cliente)
        elif model_name == 'PrevisaoViagem':
            return qs.filter(aluno__cliente=cliente)
        elif model_name == 'Embarque':
            return qs.filter(viagem__rota__cliente=cliente)

        # Fallback de segurança: se o modelo não puder ser segregado por tenant, bloqueia
        logger.error(f"[Multi-tenant Error] O modelo '{model_name}' não possui mapeamento de segregação multi-tenant configurado.")
        return qs.none()

    def perform_create(self, serializer):
        """
        Prevenção contra Payload Injection (agent.md 2.1):
        Qualquer campo 'cliente' ou 'cliente_id' enviado no JSON pelo cliente é
        completamente desconsiderado. O backend injeta forçosamente o cliente do usuário logado.
        """
        cliente = self.get_tenant()
        model = serializer.Meta.model

        if hasattr(model, 'cliente'):
            serializer.save(cliente=cliente)
            logger.info(
                f"[Tenant Isolation] Inserção de {model.__name__} forçada com cliente_id={cliente.id} "
                f"para usuário {self.request.user.email}."
            )
        else:
            serializer.save()

    def perform_update(self, serializer):
        """
        Garante a imutabilidade do Tenant durante operações de atualização (PUT/PATCH).
        Impede que um usuário reatribua um registro a outro cliente/prefeitura.
        """
        cliente = self.get_tenant()
        model = serializer.Meta.model

        if hasattr(model, 'cliente'):
            # Força o cliente original do usuário, rejeitando transferências entre prefeituras
            serializer.save(cliente=cliente)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        """
        Garante que a deleção respeite as regras de integridade e escopo do tenant.
        """
        cliente = self.get_tenant()
        if hasattr(instance, 'cliente') and instance.cliente_id != cliente.id:
            raise PermissionDenied("Acesso negado: Você não pode remover registros pertencentes a outra prefeitura.")
        super().perform_destroy(instance)
