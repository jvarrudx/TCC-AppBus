"""
AppBus Core Data Models.

Architectural Guidelines (agent.md):
- Multi-tenancy (2.1): Strict isolation by cliente_id across tenants (Prefeituras/Empresas).
- Party/Role Pattern (2.2): Usuario_Auth (Auth) <-> Pessoa (Party/Core Identity) <-> Roles (Aluno, Motorista, Administrador).
  No civil or address data is stored in the role tables.
- LGPD Compliance (2.3): Prova de consentimento (Registro_Consentimento) and No Hard Deletes (Anonimização).
- Performance Constraints (2.5): PostgreSQL TextChoices enums to prevent lookup joins.
"""

import uuid
from datetime import date
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.exceptions import ValidationError


# ==============================================================================
# 1. ENUMS (PostgreSQL TextChoices - Performance Constraint 2.5)
# ==============================================================================

class TipoDocumentoLegal(models.TextChoices):
    """Tipos de documentos legais para governança e LGPD."""
    TERMOS_DE_USO = 'TERMOS_DE_USO', 'Termos de Uso'
    POLITICA_PRIVACIDADE = 'POLITICA_PRIVACIDADE', 'Política de Privacidade'


class SentidoViagem(models.TextChoices):
    """Sentido da viagem na rota."""
    IDA = 'ida', 'Casa -> Instituição'
    VOLTA = 'volta', 'Instituição -> Casa'


class StatusViagem(models.TextChoices):
    """Ciclo de vida operacional da viagem."""
    AGENDADA = 'agendada', 'Agendada'
    EM_ANDAMENTO = 'em_andamento', 'Em Andamento'
    CONCLUIDA = 'concluida', 'Concluída'
    CANCELADA = 'cancelada', 'Cancelada'


class MetodoValidacao(models.TextChoices):
    """Método de validação do embarque do passageiro."""
    QR_CODE_APP = 'qr_code_app', 'QR Code (App Aluno)'
    MANUAL_MOTORISTA = 'manual_motorista', 'Manual (Motorista)'


class TipoStatusAprovacao(models.TextChoices):
    """Status de aprovação cadastral do aluno pela prefeitura/cliente."""
    PENDENTE = 'PENDENTE', 'Pendente de Aprovação'
    APROVADO = 'APROVADO', 'Aprovado'
    REJEITADO = 'REJEITADO', 'Rejeitado'


# Aliases para retrocompatibilidade
TipoSentidoViagem = SentidoViagem
TipoStatusViagem = StatusViagem
TipoMetodoValidacao = MetodoValidacao


# ==============================================================================
# 2. DOMÍNIO DE ENDEREÇO (Normalização Territorial)
# ==============================================================================

class UF(models.Model):
    """Unidade Federativa."""
    sigla = models.CharField(max_length=2, unique=True, verbose_name="Sigla (UF)")
    nome = models.CharField(max_length=50, verbose_name="Nome do Estado")

    class Meta:
        db_table = 'uf'
        verbose_name = 'Unidade Federativa'
        verbose_name_plural = 'Unidades Federativas'
        ordering = ['sigla']

    def __str__(self):
        return f"{self.sigla} - {self.nome}"


class Cidade(models.Model):
    """Município vinculado a uma UF."""
    nome = models.CharField(max_length=100, verbose_name="Nome da Cidade")
    uf = models.ForeignKey(
        UF,
        on_delete=models.PROTECT,
        related_name='cidades',
        verbose_name="UF"
    )

    class Meta:
        db_table = 'cidade'
        verbose_name = 'Cidade'
        verbose_name_plural = 'Cidades'
        unique_together = ('nome', 'uf')
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome}/{self.uf.sigla}"


class Bairro(models.Model):
    """Bairro vinculado a uma cidade."""
    nome = models.CharField(max_length=100, verbose_name="Nome do Bairro")
    cidade = models.ForeignKey(
        Cidade,
        on_delete=models.PROTECT,
        related_name='bairros',
        verbose_name="Cidade"
    )

    class Meta:
        db_table = 'bairro'
        verbose_name = 'Bairro'
        verbose_name_plural = 'Bairros'
        unique_together = ('nome', 'cidade')
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.cidade})"


class Endereco(models.Model):
    """Endereço estruturado e normalizado."""
    logradouro = models.CharField(max_length=255, verbose_name="Logradouro (Rua, Av, etc.)")
    numero = models.CharField(max_length=20, verbose_name="Número")
    complemento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Complemento")
    cep = models.CharField(max_length=9, verbose_name="CEP", help_text="Formato: 00000-000")
    bairro = models.ForeignKey(
        Bairro,
        on_delete=models.PROTECT,
        related_name='enderecos',
        verbose_name="Bairro"
    )

    class Meta:
        db_table = 'endereco'
        verbose_name = 'Endereço'
        verbose_name_plural = 'Endereços'

    def __str__(self):
        comp = f", {self.complemento}" if self.complemento else ""
        return f"{self.logradouro}, {self.numero}{comp} - {self.bairro}"


# ==============================================================================
# 3. AUTENTICAÇÃO (Custom User Model - agent.md 2.2 / 3)
# ==============================================================================

class UsuarioAuthManager(BaseUserManager):
    """
    Manager customizado para Usuario_Auth onde o email é o identificador único
    para autenticação no lugar de username.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O endereço de e-mail é obrigatório.')
        
        email = self.normalize_email(email).lower()
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('ativo', True)
        
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('ativo', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superusuário deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusuário deve ter is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class UsuarioAuth(AbstractBaseUser, PermissionsMixin):
    """
    Custom User Model desacoplado de dados civis (Party/Role Pattern).
    Armazena estritamente credenciais e permissões de acesso ao sistema.
    
    LGPD (No Hard Deletes):
    - Em caso de exclusão de conta, 'ativo' é definido como False para revogar
      qualquer acesso sem destruir os registros relacionais de auditoria.
    """
    email = models.EmailField(
        unique=True,
        max_length=255,
        verbose_name="E-mail",
        help_text="Identificador único para login."
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="LGPD: Usuários desativados têm login bloqueado sem exclusão de dados históricos."
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Acesso Administrativo",
        help_text="Indica se o usuário pode acessar a área administrativa do Django."
    )
    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Cadastro"
    )
    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Atualização"
    )

    objects = UsuarioAuthManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'usuario_auth'
        verbose_name = 'Usuário de Autenticação'
        verbose_name_plural = 'Usuários de Autenticação'

    def __str__(self):
        return self.email

    @property
    def is_active(self):
        """Compatibilidade direta com backends de autenticação do Django e SimpleJWT."""
        return self.ativo

    @is_active.setter
    def is_active(self, value):
        self.ativo = value


# Alias para retrocompatibilidade com agent.md
Usuario_Auth = UsuarioAuth


# ==============================================================================
# 4. PARTY (Identidade Central - Party/Role Pattern)
# ==============================================================================

class Pessoa(models.Model):
    """
    Padrão Party/Role: Entidade central ('Party') que representa a identidade civil.
    Relaciona-se 1:1 com UsuarioAuth e serve de âncora para os 'Roles'
    (Aluno, Motorista, Administrador).

    LGPD:
    - Centraliza PII (nome, CPF, data de nascimento, endereço residencial).
    - Suporta anonimização rigorosa via método anonimizar().
    """
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='pessoa',
        verbose_name="Credenciais de Acesso"
    )
    nome = models.CharField(
        max_length=255,
        verbose_name="Nome Completo"
    )
    cpf = models.CharField(
        max_length=14,
        unique=True,
        null=True,
        blank=True,
        verbose_name="CPF",
        help_text="Formato: 000.000.000-00. Pode ser nulo quando anonimizado via LGPD."
    )
    data_nascimento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Nascimento"
    )
    endereco = models.ForeignKey(
        Endereco,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pessoas',
        verbose_name="Endereço Residencial"
    )
    anonimizado = models.BooleanField(
        default=False,
        verbose_name="Anonimizado (LGPD)",
        help_text="Indica se os dados identificáveis foram mascarados por solicitação do titular."
    )
    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Cadastro"
    )

    class Meta:
        db_table = 'pessoa'
        verbose_name = 'Pessoa (Identidade)'
        verbose_name_plural = 'Pessoas'

    def __str__(self):
        return f"{self.nome} ({'Anonimizado' if self.anonimizado else self.cpf or 'Sem CPF'})"

    @property
    def cliente_id(self):
        """
        Facilitador arquitetural para Multi-tenancy (agent.md 2.1):
        Permite acessar request.user.pessoa.cliente_id independentemente do papel
        (Administrador, Aluno ou Motorista).
        """
        if hasattr(self, 'aluno'):
            return self.aluno.cliente_id
        if hasattr(self, 'motorista'):
            return self.motorista.cliente_id
        if hasattr(self, 'administrador'):
            return self.administrador.cliente_id
        return None

    def is_menor_idade(self) -> bool:
        """
        Verifica se a pessoa é menor de 18 anos conforme a LGPD.
        Utilizado para validação obrigatória do 'responsavel_legal_cpf'.
        """
        if not self.data_nascimento:
            return False
        hoje = date.today()
        idade = hoje.year - self.data_nascimento.year - (
            (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )
        return idade < 18

    def anonimizar(self):
        """
        LGPD (No Hard Deletes - agent.md 2.3):
        1. Inativa Usuario_Auth (bloqueio de login).
        2. Seta Pessoa.anonimizado = True.
        3. Mascara PII (nome = 'Usuário Anonimizado', limpa CPF, data de nascimento e endereço).
        4. Preserva IDs para resguardar o histórico imutável de Embarques.
        """
        self.nome = "Usuário Anonimizado"
        self.cpf = None
        self.data_nascimento = None
        self.endereco = None
        self.anonimizado = True
        self.save()

        # Inativa as credenciais de autenticação
        if self.usuario:
            self.usuario.ativo = False
            self.usuario.save()


# ==============================================================================
# 5. GOVERNANÇA & LGPD (agent.md 2.3 / 3)
# ==============================================================================

class Documento_Legal(models.Model):
    """
    Armazena as versões vigentes e históricas de Termos de Uso e Políticas de Privacidade.
    Garante compliance e rastreabilidade jurídica.
    """
    tipo = models.CharField(
        max_length=30,
        choices=TipoDocumentoLegal.choices,
        verbose_name="Tipo de Documento"
    )
    versao = models.CharField(
        max_length=20,
        verbose_name="Versão do Documento",
        help_text="Ex: '1.0', '2.0-2026'"
    )
    conteudo = models.TextField(
        verbose_name="Conteúdo Textual / Markdown",
        help_text="Texto completo do documento legal aceito pelo usuário."
    )
    data_publicacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Publicação"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Documento Vigente",
        help_text="Indica se esta versão é a exigida para novos cadastros."
    )

    class Meta:
        db_table = 'documento_legal'
        verbose_name = 'Documento Legal'
        verbose_name_plural = 'Documentos Legais'
        unique_together = ('tipo', 'versao')

    def __str__(self):
        return f"{self.get_tipo_display()} - Versão {self.versao} ({'Vigente' if self.ativo else 'Arquivado'})"


class Registro_Consentimento(models.Model):
    """
    LGPD (Consent Proof - agent.md 2.3):
    Evidência técnica irrefutável do consentimento fornecido pelo titular ou responsável legal.
    
    Regras estritas:
    - Armazena IP, User-Agent e data/hora do aceite.
    - Se a Pessoa for menor de 18 anos, 'responsavel_legal_cpf' é MANDATÓRIO.
    - Utiliza on_delete=models.PROTECT para impedir a deleção acidental deste registro de auditoria.
    """
    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.PROTECT,
        related_name='consentimentos',
        verbose_name="Pessoa Titular"
    )
    documento = models.ForeignKey(
        Documento_Legal,
        on_delete=models.PROTECT,
        related_name='registros_consentimento',
        verbose_name="Documento Legal Vinculado"
    )
    consentimento_concedido = models.BooleanField(
        default=True,
        verbose_name="Consentimento Concedido",
        help_text="Sinalização explícita do titular (Opt-in)."
    )
    responsavel_legal_cpf = models.CharField(
        max_length=14,
        blank=True,
        null=True,
        verbose_name="CPF do Responsável Legal",
        help_text="Obrigatório para menores de 18 anos segundo as regras LGPD do AppBus."
    )
    ip_address = models.GenericIPAddressField(
        verbose_name="Endereço IP da Conexão"
    )
    user_agent = models.TextField(
        verbose_name="User-Agent do Navegador/App"
    )
    data_consentimento = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data e Hora do Consentimento"
    )

    class Meta:
        db_table = 'registro_consentimento'
        verbose_name = 'Registro de Consentimento'
        verbose_name_plural = 'Registros de Consentimento'

    def __str__(self):
        return f"Consentimento {self.pessoa.nome} - Doc: {self.documento.versao} em {self.data_consentimento.strftime('%d/%m/%Y %H:%M')}"

    def clean(self):
        """Validação estrita de compliance LGPD para menores de idade."""
        super().clean()
        if self.pessoa and self.pessoa.is_menor_idade():
            if not self.responsavel_legal_cpf:
                raise ValidationError({
                    'responsavel_legal_cpf': 'Conforme a LGPD, o CPF do responsável legal é obrigatório para menores de 18 anos.'
                })


# Aliases para compatibilidade PascalCase
RegistroConsentimento = Registro_Consentimento
DocumentoLegal = Documento_Legal


# ==============================================================================
# 6. MULTI-TENANCY & ROLES (agent.md 2.1, 2.2, 3)
# ==============================================================================

class Cliente(models.Model):
    """
    Pilar Multi-Tenancy (Tenant Root):
    Representa a Prefeitura Municipal ou Empresa conveniada prestadora do serviço.
    Todas as rotas, viagens, frotas e papéis estão segregados por este ID.
    """
    cnpj = models.CharField(
        max_length=18,
        unique=True,
        verbose_name="CNPJ",
        help_text="Formato: 00.000.000/0000-00"
    )
    razao_social = models.CharField(
        max_length=255,
        verbose_name="Razão Social"
    )
    nome_fantasia = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nome Fantasia / Município"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Cadastro"
    )

    class Meta:
        db_table = 'cliente'
        verbose_name = 'Cliente (Tenant/Município)'
        verbose_name_plural = 'Clientes (Tenants/Municípios)'
        ordering = ['razao_social']

    def __str__(self):
        return self.nome_fantasia or self.razao_social


class Instituicao(models.Model):
    """
    Instituição de Ensino (Universidade / Faculdade / Escola) atendida pela rota.
    Vinculada ao Cliente (município).
    """
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='instituicoes',
        verbose_name="Cliente / Prefeitura"
    )
    nome = models.CharField(
        max_length=255,
        verbose_name="Nome da Instituição"
    )
    sigla = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Sigla (Ex: USP, UNESP, FATEC)"
    )
    endereco = models.ForeignKey(
        Endereco,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instituicoes',
        verbose_name="Endereço da Instituição"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )

    class Meta:
        db_table = 'instituicao'
        verbose_name = 'Instituição de Ensino'
        verbose_name_plural = 'Instituições de Ensino'
        ordering = ['nome']

    def __str__(self):
        sigla_txt = f" ({self.sigla})" if self.sigla else ""
        return f"{self.nome}{sigla_txt} - {self.cliente}"


class Administrador(models.Model):
    """
    Papel (Role) de Administrador / Gestor do Transporte Municipal.
    Segregado estritamente por cliente_id (Multi-Tenancy).
    """
    pessoa = models.OneToOneField(
        Pessoa,
        on_delete=models.PROTECT,
        related_name='administrador',
        verbose_name="Pessoa (Identidade)"
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='administradores',
        verbose_name="Cliente / Prefeitura Administrada"
    )
    cargo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Cargo / Função"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )

    class Meta:
        db_table = 'administrador'
        verbose_name = 'Administrador Municipal'
        verbose_name_plural = 'Administradores Municipais'

    def __str__(self):
        return f"Admin: {self.pessoa.nome} - {self.cliente}"


class Aluno(models.Model):
    """
    Papel (Role) de Aluno / Universitário passageiro.
    
    Party/Role Pattern:
    - Não armazena nome, CPF ou endereço diretamente (residem em Pessoa).
    - Armazena exclusivamente o vínculo estudantil com a Prefeitura (cliente) e a Faculdade (instituicao).
    
    Multi-tenancy:
    - Particionado por cliente_id.
    """
    pessoa = models.OneToOneField(
        Pessoa,
        on_delete=models.PROTECT,
        related_name='aluno',
        verbose_name="Pessoa (Identidade)"
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='alunos',
        verbose_name="Cliente / Prefeitura Conveniada"
    )
    instituicao = models.ForeignKey(
        Instituicao,
        on_delete=models.PROTECT,
        related_name='alunos',
        verbose_name="Instituição de Ensino"
    )
    matricula = models.CharField(
        max_length=50,
        verbose_name="Matrícula Estudantil"
    )
    status_aprovacao = models.CharField(
        max_length=20,
        choices=TipoStatusAprovacao.choices,
        default=TipoStatusAprovacao.PENDENTE,
        verbose_name="Status de Aprovação Cadastral"
    )
    data_solicitacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Solicitação"
    )
    data_decisao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data da Avaliação"
    )
    avaliado_por = models.ForeignKey(
        Administrador,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alunos_avaliados',
        verbose_name="Avaliador Responsável"
    )

    class Meta:
        db_table = 'aluno'
        verbose_name = 'Aluno (Passageiro)'
        verbose_name_plural = 'Alunos (Passageiros)'
        unique_together = ('cliente', 'matricula')

    def __str__(self):
        return f"Aluno: {self.pessoa.nome} ({self.matricula}) - {self.get_status_aprovacao_display()}"


class Motorista(models.Model):
    """
    Papel (Role) de Motorista do Ônibus Universitário.
    
    Party/Role Pattern:
    - Dados civis residem em Pessoa.
    - Armazena dados operacionais específicos da função (CNH, Categoria).
    
    Multi-tenancy:
    - Particionado por cliente_id.
    """
    pessoa = models.OneToOneField(
        Pessoa,
        on_delete=models.PROTECT,
        related_name='motorista',
        verbose_name="Pessoa (Identidade)"
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='motoristas',
        verbose_name="Cliente / Prefeitura Vinculada"
    )
    cnh = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número do Registro CNH"
    )
    categoria_cnh = models.CharField(
        max_length=5,
        default='D',
        verbose_name="Categoria CNH"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )

    class Meta:
        db_table = 'motorista'
        verbose_name = 'Motorista'
        verbose_name_plural = 'Motoristas'

    def __str__(self):
        return f"Motorista: {self.pessoa.nome} (CNH: {self.cnh} - {self.categoria_cnh})"


# ==============================================================================
# 7. MODELOS DE FROTA E ROTAS (Etapa 1.5 - agent.md 3)
# ==============================================================================

class ModeloVeiculo(models.Model):
    """
    Modelo e fabricante do veículo rodoviário (ex: Marcopolo Paradiso, Caio Apache).
    """
    marca = models.CharField(
        max_length=100,
        verbose_name="Marca / Fabricante"
    )
    nome = models.CharField(
        max_length=100,
        verbose_name="Modelo"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )

    class Meta:
        db_table = 'modelo_veiculo'
        verbose_name = 'Modelo de Veículo'
        verbose_name_plural = 'Modelos de Veículos'
        ordering = ['marca', 'nome']

    def __str__(self):
        return f"{self.marca} {self.nome}"


class Onibus(models.Model):
    """
    Veículo da frota operacional vinculado ao Cliente (Prefeitura/Empresa).
    
    Multi-tenancy:
    - Segregado por cliente_id.
    - Contém UUID imutável para geração do QR Code de embarque óptico.
    """
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='onibus',
        verbose_name="Cliente / Prefeitura"
    )
    modelo = models.ForeignKey(
        ModeloVeiculo,
        on_delete=models.PROTECT,
        related_name='onibus',
        verbose_name="Modelo do Veículo"
    )
    placa = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Placa do Veículo"
    )
    capacidade = models.PositiveIntegerField(
        verbose_name="Capacidade de Passageiros Sentados"
    )
    qr_code_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name="UUID do QR Code"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )

    class Meta:
        db_table = 'onibus'
        verbose_name = 'Ônibus'
        verbose_name_plural = 'Ônibus'
        ordering = ['placa']

    def __str__(self):
        return f"Ônibus {self.placa} ({self.modelo}) - {self.cliente}"


class Rota(models.Model):
    """
    Itinerário planejado para transporte dos estudantes universitários.
    
    Multi-tenancy:
    - Segregado por cliente_id.
    """
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='rotas',
        verbose_name="Cliente / Prefeitura"
    )
    nome = models.CharField(
        max_length=150,
        verbose_name="Nome da Rota"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )

    class Meta:
        db_table = 'rota'
        verbose_name = 'Rota'
        verbose_name_plural = 'Rotas'
        ordering = ['nome']

    def __str__(self):
        return f"Rota: {self.nome} ({self.cliente})"


class RotaInstituicao(models.Model):
    """
    Tabela associativa que mapeia as instituições atendidas por uma rota e sua ordem de parada.
    """
    rota = models.ForeignKey(
        Rota,
        on_delete=models.CASCADE,
        related_name='rota_instituicoes',
        verbose_name="Rota"
    )
    instituicao = models.ForeignKey(
        Instituicao,
        on_delete=models.PROTECT,
        related_name='rota_instituicoes',
        verbose_name="Instituição de Ensino"
    )
    ordem_parada = models.PositiveIntegerField(
        verbose_name="Ordem de Parada"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )

    class Meta:
        db_table = 'rota_instituicao'
        verbose_name = 'Instituição da Rota'
        verbose_name_plural = 'Instituições da Rota'
        unique_together = ('rota', 'instituicao')
        ordering = ['ordem_parada']

    def __str__(self):
        return f"{self.rota.nome} -> Parada {self.ordem_parada}: {self.instituicao.nome}"


# ==============================================================================
# 8. MODELOS TRANSACIONAIS (EVENTOS E OPERAÇÃO)
# ==============================================================================

class Viagem(models.Model):
    """
    Instanciação da operação diária de uma rota com ônibus e motorista alocados.
    
    Multi-tenancy:
    - O vínculo do cliente é garantido através de Rota/Onibus/Motorista.
    """
    rota = models.ForeignKey(
        Rota,
        on_delete=models.PROTECT,
        related_name='viagens',
        verbose_name="Rota"
    )
    onibus = models.ForeignKey(
        Onibus,
        on_delete=models.PROTECT,
        related_name='viagens',
        verbose_name="Ônibus"
    )
    motorista = models.ForeignKey(
        Motorista,
        on_delete=models.PROTECT,
        related_name='viagens',
        verbose_name="Motorista"
    )
    sentido = models.CharField(
        max_length=10,
        choices=SentidoViagem.choices,
        verbose_name="Sentido da Viagem"
    )
    status = models.CharField(
        max_length=20,
        choices=StatusViagem.choices,
        default=StatusViagem.AGENDADA,
        verbose_name="Status da Viagem"
    )
    data = models.DateField(
        verbose_name="Data da Viagem"
    )
    hora_inicio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Horário de Início"
    )
    hora_fim = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Horário de Fim"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )

    class Meta:
        db_table = 'viagem'
        verbose_name = 'Viagem'
        verbose_name_plural = 'Viagens'
        ordering = ['-data', '-created_at']

    def __str__(self):
        return f"Viagem {self.data} - {self.rota.nome} ({self.get_sentido_display()}) [{self.get_status_display()}]"


class PrevisaoViagem(models.Model):
    """
    Previsão de demanda registrada pelo aluno ("Vou / Não Vou").
    
    Regra Crítica:
    - Constraint de unicidade ['aluno', 'data'] para impedir duplicidade de intenções no mesmo dia.
    """
    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        related_name='previsoes_viagem',
        verbose_name="Aluno"
    )
    data = models.DateField(
        verbose_name="Data Prevista"
    )
    vai_ida = models.BooleanField(
        default=False,
        verbose_name="Vai na Ida"
    )
    vai_volta = models.BooleanField(
        default=False,
        verbose_name="Vai na Volta"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )

    class Meta:
        db_table = 'previsao_viagem'
        verbose_name = 'Previsão de Viagem'
        verbose_name_plural = 'Previsões de Viagens'
        unique_together = ('aluno', 'data')
        ordering = ['-data']

    def __str__(self):
        return f"Previsão {self.data}: {self.aluno.pessoa.nome} (Ida: {'Sim' if self.vai_ida else 'Não'}, Volta: {'Sim' if self.vai_volta else 'Não'})"


class Embarque(models.Model):
    """
    Registro físico ou manual de embarque do aluno no ônibus durante uma viagem.
    
    LGPD (Auditoria Imutável):
    - Chaves protegidas por on_delete=models.PROTECT para evitar perda de logs
      históricos mesmo se um perfil de aluno for anonimizado.
    """
    viagem = models.ForeignKey(
        Viagem,
        on_delete=models.PROTECT,
        related_name='embarques',
        verbose_name="Viagem"
    )
    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.PROTECT,
        related_name='embarques',
        verbose_name="Aluno"
    )
    metodo_validacao = models.CharField(
        max_length=20,
        choices=MetodoValidacao.choices,
        default=MetodoValidacao.QR_CODE_APP,
        verbose_name="Método de Validação"
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        verbose_name="Horário do Embarque"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )

    class Meta:
        db_table = 'embarque'
        verbose_name = 'Embarque'
        verbose_name_plural = 'Embarques'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Embarque: {self.aluno.pessoa.nome} na {self.viagem.rota.nome} via {self.get_metodo_validacao_display()} às {self.timestamp.strftime('%H:%M:%S')}"

