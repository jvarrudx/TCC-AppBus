"""
Django Admin configurations for AppBus Core, Address Domain, Party/Role, and Roles.
"""

from django.contrib import admin
from apps.core.models import (
    # Auth & Party
    UsuarioAuth,
    Pessoa,
    # Governance & LGPD
    Documento_Legal,
    Registro_Consentimento,
    # Address Domain
    UF,
    Cidade,
    Bairro,
    Endereco,
    # Tenants & Roles
    Cliente,
    Instituicao,
    Administrador,
    Aluno,
    Motorista,
)


# ==============================================================================
# 1. Autenticação & Identidade Central
# ==============================================================================

@admin.register(UsuarioAuth)
class UsuarioAuthAdmin(admin.ModelAdmin):
    list_display = ('email', 'ativo', 'is_staff', 'is_superuser', 'data_cadastro')
    list_filter = ('ativo', 'is_staff', 'is_superuser')
    search_fields = ('email',)
    ordering = ('-data_cadastro',)
    readonly_fields = ('data_cadastro', 'data_atualizacao')


@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'data_nascimento', 'anonimizado', 'data_cadastro')
    list_filter = ('anonimizado',)
    search_fields = ('nome', 'cpf')
    ordering = ('nome',)
    readonly_fields = ('data_cadastro',)


# ==============================================================================
# 2. Governança & LGPD
# ==============================================================================

@admin.register(Documento_Legal)
class DocumentoLegalAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'versao', 'ativo', 'data_publicacao')
    list_filter = ('tipo', 'ativo')
    search_fields = ('versao', 'conteudo')
    ordering = ('-data_publicacao',)


@admin.register(Registro_Consentimento)
class RegistroConsentimentoAdmin(admin.ModelAdmin):
    list_display = ('pessoa', 'documento', 'consentimento_concedido', 'responsavel_legal_cpf', 'ip_address', 'data_consentimento')
    list_filter = ('consentimento_concedido', 'documento')
    search_fields = ('pessoa__nome', 'pessoa__cpf', 'responsavel_legal_cpf', 'ip_address')
    ordering = ('-data_consentimento',)
    readonly_fields = ('data_consentimento',)


# ==============================================================================
# 3. Domínio Territorial (Endereço)
# ==============================================================================

@admin.register(UF)
class UFAdmin(admin.ModelAdmin):
    list_display = ('sigla', 'nome')
    search_fields = ('sigla', 'nome')


@admin.register(Cidade)
class CidadeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'uf')
    list_filter = ('uf',)
    search_fields = ('nome',)


@admin.register(Bairro)
class BairroAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cidade')
    list_filter = ('cidade__uf', 'cidade')
    search_fields = ('nome', 'cidade__nome')


@admin.register(Endereco)
class EnderecoAdmin(admin.ModelAdmin):
    list_display = ('logradouro', 'numero', 'complemento', 'bairro', 'cep')
    search_fields = ('logradouro', 'cep', 'bairro__nome')


# ==============================================================================
# 4. Multi-Tenancy & Roles
# ==============================================================================

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('razao_social', 'nome_fantasia', 'cnpj', 'ativo', 'data_cadastro')
    list_filter = ('ativo',)
    search_fields = ('razao_social', 'nome_fantasia', 'cnpj')
    ordering = ('razao_social',)
    readonly_fields = ('data_cadastro',)


@admin.register(Instituicao)
class InstituicaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sigla', 'cliente', 'ativo')
    list_filter = ('cliente', 'ativo')
    search_fields = ('nome', 'sigla')


@admin.register(Administrador)
class AdministradorAdmin(admin.ModelAdmin):
    list_display = ('pessoa', 'cliente', 'cargo', 'ativo')
    list_filter = ('cliente', 'ativo')
    search_fields = ('pessoa__nome', 'cargo')


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('pessoa', 'matricula', 'instituicao', 'cliente', 'status_aprovacao', 'data_solicitacao')
    list_filter = ('cliente', 'instituicao', 'status_aprovacao')
    search_fields = ('pessoa__nome', 'matricula')
    readonly_fields = ('data_solicitacao',)


@admin.register(Motorista)
class MotoristaAdmin(admin.ModelAdmin):
    list_display = ('pessoa', 'cliente', 'cnh', 'categoria_cnh', 'ativo')
    list_filter = ('cliente', 'ativo', 'categoria_cnh')
    search_fields = ('pessoa__nome', 'cnh')
