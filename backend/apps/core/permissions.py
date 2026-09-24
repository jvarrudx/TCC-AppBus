"""
Custom DRF Permissions for AppBus Multi-Tenant and Role-Based Access Control.

Architectural Guidelines (agent.md):
- Zero Trust Security: Access is strictly controlled based on the user's active role.
- Roles: Administrador, Motorista, Aluno.
- Municipal Management: Only active Administradores of the tenant may create/update/delete
  resources (Buses, Routes, Drivers, Schools) and approve/reject Student applications.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.core.mixins import get_user_cliente


class IsTenantAdmin(BasePermission):
    """
    Permissão que concede acesso exclusivamente a Administradores Municipais
    ativos da prefeitura vinculada ao usuário autenticado, ou a Superusuários.
    
    Impede que Alunos e Motoristas acessem rotas de gestão administrativa
    (aprovação de alunos, cadastro de frota, rotas, etc.).
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        if hasattr(user, 'pessoa'):
            pessoa = user.pessoa
            if hasattr(pessoa, 'administrador') and pessoa.administrador.ativo:
                return True

        return False


class IsTenantAdminOrReadOnly(BasePermission):
    """
    Permissão que autoriza leitura (GET, HEAD, OPTIONS) para qualquer usuário
    autenticado que pertença ao mesmo Tenant (ex: Alunos e Motoristas consultando rotas),
    mas restringe operações de escrita (POST, PUT, PATCH, DELETE) exclusivamente
    a Administradores Municipais ou Superusuários.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Superusuário tem acesso completo
        if user.is_superuser:
            return True

        # Métodos seguros de leitura
        if request.method in SAFE_METHODS:
            # Qualquer usuário com tenant vinculado pode ler (filtrado por get_queryset)
            return get_user_cliente(user) is not None

        # Métodos de modificação exigem papel de Administrador
        if hasattr(user, 'pessoa'):
            pessoa = user.pessoa
            if hasattr(pessoa, 'administrador') and pessoa.administrador.ativo:
                return True

        return False


class IsMotoristaOuAdmin(BasePermission):
    """
    Permite acesso a Motoristas municipais ativos ou Administradores.
    Útil para endpoints operacionais de viagem e dashboard do motorista.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        if hasattr(user, 'pessoa'):
            pessoa = user.pessoa
            if hasattr(pessoa, 'administrador') and pessoa.administrador.ativo:
                return True
            if hasattr(pessoa, 'motorista') and pessoa.motorista.ativo:
                return True

        return False


class IsAluno(BasePermission):
    """
    Permite acesso exclusivamente a usuários com papel de Aluno.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return hasattr(user, 'pessoa') and hasattr(user.pessoa, 'aluno')


class IsMotorista(BasePermission):
    """
    Permite acesso exclusivamente a Motoristas da frota municipal ativos.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return hasattr(user, 'pessoa') and hasattr(user.pessoa, 'motorista') and user.pessoa.motorista.ativo

