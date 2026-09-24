"""
Serializers for AppBus Core & Authentication.

Architectural Guidelines (agent.md):
- Multi-tenancy (2.1): All operational data partitioned by cliente_id.
- Party/Role Pattern (2.2): Atomic transaction creating UsuarioAuth -> Pessoa -> Aluno -> Registro_Consentimento.
- LGPD Compliance (2.3):
  1. Mandatory consent proof with IP and User-Agent extracted EXCLUSIVELY from HTTP headers (never payload).
  2. Minor age validation: mandatory responsavel_legal_cpf for age < 18.
  3. No plaintext passwords: passwords hashed with Argon2 / PBKDF2 via create_user().
"""

import logging
from datetime import date
from django.db import transaction
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from apps.core.models import (
    UsuarioAuth,
    Pessoa,
    Cliente,
    Instituicao,
    Aluno,
    Motorista,
    Administrador,
    Endereco,
    Bairro,
    Documento_Legal,
    Registro_Consentimento,
    TipoStatusAprovacao,
    TipoDocumentoLegal,
    ModeloVeiculo,
    Onibus,
    Rota,
    RotaInstituicao,
    Viagem,
    PrevisaoViagem,
    Embarque,
    SentidoViagem,
    StatusViagem,
    MetodoValidacao,
)

logger = logging.getLogger(__name__)


def get_client_ip(request) -> str:
    """
    LGPD Compliance (agent.md 2.3):
    Extrai o endereço IP real do cliente a partir dos cabeçalhos HTTP do socket ou proxy reverso.
    Nunca aceita IP via corpo da requisição JSON (evita spoofing da prova de consentimento).
    """
    if not request:
        return '127.0.0.1'

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Pega o primeiro IP da cadeia (cliente real)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


# ==============================================================================
# 1. JWT CUSTOM TOKEN SERIALIZER (agent.md 2.1 Multi-tenancy & Claims)
# ==============================================================================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer customizado para login JWT.
    Enriquece o payload do token com perfil civil (Pessoa), papel ativo (Role)
    e partição do município (cliente_id) para suportar o Multi-tenancy no frontend.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Regra LGPD: Verificar se o usuário está ativo
        if not user.ativo:
            raise AuthenticationFailed("Esta conta foi desativada ou anonimizada conforme a LGPD.")

        # Injeção de Claims de Autenticação e Multi-Tenancy
        token['email'] = user.email
        token['is_superuser'] = user.is_superuser
        token['is_staff'] = user.is_staff

        # Extração dos dados do padrão Party/Role
        if hasattr(user, 'pessoa'):
            pessoa = user.pessoa
            token['pessoa_id'] = pessoa.id
            token['nome'] = pessoa.nome
            token['anonimizado'] = pessoa.anonimizado

            # Identificação do papel (Role) e segregação Multi-tenant
            if hasattr(pessoa, 'aluno'):
                token['role'] = 'aluno'
                token['aluno_id'] = pessoa.aluno.id
                token['cliente_id'] = pessoa.aluno.cliente_id
                token['status_aprovacao'] = pessoa.aluno.status_aprovacao
            elif hasattr(pessoa, 'motorista'):
                token['role'] = 'motorista'
                token['motorista_id'] = pessoa.motorista.id
                token['cliente_id'] = pessoa.motorista.cliente_id
            elif hasattr(pessoa, 'administrador'):
                token['role'] = 'administrador'
                token['administrador_id'] = pessoa.administrador.id
                token['cliente_id'] = pessoa.administrador.cliente_id
            else:
                token['role'] = 'usuario'
                token['cliente_id'] = None
        else:
            token['role'] = 'superuser' if user.is_superuser else 'indefinido'
            token['cliente_id'] = None

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Bloqueio LGPD de contas desativadas
        if not self.user.ativo:
            raise AuthenticationFailed("Conta desativada ou anonimizada conforme a LGPD.")

        # Resposta amigável com metadados adicionais para o cliente Vue (PWA)
        pessoa_data = None
        role = 'usuario'
        cliente_id = None
        status_aprovacao = None

        if hasattr(self.user, 'pessoa'):
            pessoa = self.user.pessoa
            if hasattr(pessoa, 'aluno'):
                role = 'aluno'
                cliente_id = pessoa.aluno.cliente_id
                status_aprovacao = pessoa.aluno.status_aprovacao
            elif hasattr(pessoa, 'motorista'):
                role = 'motorista'
                cliente_id = pessoa.motorista.cliente_id
            elif hasattr(pessoa, 'administrador'):
                role = 'administrador'
                cliente_id = pessoa.administrador.cliente_id

            pessoa_data = {
                "id": pessoa.id,
                "nome": pessoa.nome,
                "cpf": pessoa.cpf,
                "anonimizado": pessoa.anonimizado,
            }

        data['user'] = {
            "id": self.user.id,
            "email": self.user.email,
            "role": role,
            "cliente_id": cliente_id,
            "status_aprovacao": status_aprovacao,
            "pessoa": pessoa_data
        }
        return data


# ==============================================================================
# 2. DOCUMENTOS LEGAIS (LGPD - Termos de Uso e Consentimento)
# ==============================================================================

class DocumentoLegalSerializer(serializers.ModelSerializer):
    """Exibição pública de documentos vigentes para aceite de termos."""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = Documento_Legal
        fields = ['id', 'tipo', 'tipo_display', 'versao', 'conteudo', 'data_publicacao', 'ativo']


# ==============================================================================
# 3. ONBOARDING DE ALUNOS (Etapa 2.1 - Party/Role, LGPD & Transação Atômica)
# ==============================================================================

class AlunoRegistroSerializer(serializers.Serializer):
    """
    Serializer de Onboarding de Alunos.
    
    Implementa as diretrizes estritas do agent.md:
    1. Party/Role Pattern (2.2): Dados civis residem em Pessoa, credenciais em UsuarioAuth, papel em Aluno.
    2. Transação Atômica (2.2): Cria simultaneamente UsuarioAuth -> Pessoa -> Aluno -> Registro_Consentimento.
    3. Multi-tenancy (2.1): Valida cliente_id e vínculo com a Instituicao de ensino.
    4. LGPD Compliance (2.3):
       - IP e User-Agent são OBRIGATORIAMENTE inferidos dos cabeçalhos HTTP da requisição (nunca aceitos no payload).
       - Exige CPF do responsável legal para menores de 18 anos.
       - Senha criptografada obrigatoriamente via UsuarioAuth.objects.create_user().
    """
    # 1. Credenciais de Acesso (UsuarioAuth)
    email = serializers.EmailField(
        required=True,
        help_text="Endereço de e-mail institucional ou pessoal para login."
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text="Senha de acesso (mínimo de 8 caracteres)."
    )

    # 2. Identidade Civil (Pessoa - Party)
    nome = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Nome completo civil do estudante."
    )
    cpf = serializers.CharField(
        max_length=14,
        required=True,
        help_text="CPF no formato 000.000.000-00 ou 11 dígitos numéricos."
    )
    data_nascimento = serializers.DateField(
        required=True,
        help_text="Data de nascimento para cômputo de maioridade conforme a LGPD."
    )

    # 3. Endereço Residencial (Opcional)
    logradouro = serializers.CharField(max_length=255, required=False, allow_blank=True)
    numero = serializers.CharField(max_length=20, required=False, allow_blank=True)
    complemento = serializers.CharField(max_length=100, required=False, allow_blank=True)
    cep = serializers.CharField(max_length=9, required=False, allow_blank=True)
    bairro_id = serializers.IntegerField(required=False, allow_null=True)

    # 4. Papel Estudantil e Multi-Tenancy (Aluno - Role)
    cliente_id = serializers.IntegerField(
        required=True,
        help_text="ID da Prefeitura ou Empresa conveniada prestadora do transporte (Multi-tenant)."
    )
    instituicao_id = serializers.IntegerField(
        required=True,
        help_text="ID da Faculdade ou Escola atendida."
    )
    matricula = serializers.CharField(
        max_length=50,
        required=True,
        help_text="Número de matrícula na instituição de ensino."
    )

    # 5. Governança e Consentimento (LGPD)
    documento_legal_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID do Documento Legal vigente. Se omitido, usará o Termo de Uso ativo mais recente."
    )
    termo_aceito = serializers.BooleanField(
        required=True,
        help_text="Consentimento expresso e inequívoco dos Termos de Uso e Política de Privacidade."
    )
    responsavel_legal_cpf = serializers.CharField(
        max_length=14,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Obrigatório pela LGPD se o titular tiver menos de 18 anos na data do cadastro."
    )

    # NOTA DE SEGURANÇA LGPD:
    # Os campos ip_address e user_agent NÃO existem neste serializer para impedir
    # que o usuário injete ou forje evidências de consentimento no payload JSON.

    def validate_email(self, value):
        email_clean = value.lower().strip()
        if UsuarioAuth.objects.filter(email=email_clean).exists():
            raise serializers.ValidationError("Este endereço de e-mail já está cadastrado no sistema.")
        return email_clean

    def validate_password(self, value):
        """Valida a complexidade da senha usando os validadores do Django."""
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def validate_cpf(self, value):
        cpf_clean = ''.join(filter(str.isdigit, value))
        if len(cpf_clean) != 11:
            raise serializers.ValidationError("O CPF deve conter exatamente 11 dígitos numéricos.")
        cpf_formatado = f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
        if Pessoa.objects.filter(cpf=cpf_formatado).exists():
            raise serializers.ValidationError("Este CPF já está cadastrado no sistema.")
        return cpf_formatado

    def validate_termo_aceito(self, value):
        if not value:
            raise serializers.ValidationError(
                "LGPD: O consentimento expresso aos Termos de Uso é obrigatório para realização do cadastro."
            )
        return value

    def validate(self, attrs):
        # 1. Validação Multi-tenant do Cliente (Prefeitura)
        cliente_id = attrs.get('cliente_id')
        try:
            cliente = Cliente.objects.get(id=cliente_id, ativo=True)
            attrs['cliente_obj'] = cliente
        except Cliente.DoesNotExist:
            raise serializers.ValidationError({"cliente_id": "Cliente/Prefeitura não encontrado ou inativo."})

        # 2. Validação da Instituição e seu vínculo com o Cliente
        instituicao_id = attrs.get('instituicao_id')
        try:
            instituicao = Instituicao.objects.get(id=instituicao_id, ativo=True)
            if instituicao.cliente_id != cliente.id:
                raise serializers.ValidationError({
                    "instituicao_id": "A instituição informada não pertence ao município/cliente selecionado."
                })
            attrs['instituicao_obj'] = instituicao
        except Instituicao.DoesNotExist:
            raise serializers.ValidationError({"instituicao_id": "Instituição de ensino não encontrada ou inativa."})

        # 3. Unicidade de Matrícula no Cliente
        matricula = attrs.get('matricula')
        if Aluno.objects.filter(cliente=cliente, matricula=matricula).exists():
            raise serializers.ValidationError({
                "matricula": f"Já existe um aluno cadastrado com a matrícula '{matricula}' nesta prefeitura."
            })

        # 4. Validação LGPD de Menores de Idade (agent.md 2.3)
        data_nascimento = attrs.get('data_nascimento')
        hoje = date.today()
        idade = hoje.year - data_nascimento.year - (
            (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day)
        )
        attrs['is_menor'] = idade < 18

        responsavel_cpf = attrs.get('responsavel_legal_cpf')
        if attrs['is_menor']:
            if not responsavel_cpf or not responsavel_cpf.strip():
                raise serializers.ValidationError({
                    "responsavel_legal_cpf": (
                        "LGPD Compliance: Para titulares menores de 18 anos, "
                        "o fornecimento do CPF do responsável legal é obrigatório."
                    )
                })
            resp_digits = ''.join(filter(str.isdigit, responsavel_cpf))
            if len(resp_digits) != 11:
                raise serializers.ValidationError({
                    "responsavel_legal_cpf": "O CPF do responsável legal deve conter 11 dígitos numéricos."
                })
            attrs['responsavel_legal_cpf'] = f"{resp_digits[:3]}.{resp_digits[3:6]}.{resp_digits[6:9]}-{resp_digits[9:]}"

        # 5. Validação do Documento Legal Vigente
        doc_id = attrs.get('documento_legal_id')
        if doc_id:
            try:
                documento = Documento_Legal.objects.get(id=doc_id, ativo=True)
            except Documento_Legal.DoesNotExist:
                raise serializers.ValidationError({"documento_legal_id": "Documento legal informado não é válido ou foi revogado."})
        else:
            documento = Documento_Legal.objects.filter(
                tipo=TipoDocumentoLegal.TERMOS_DE_USO,
                ativo=True
            ).order_by('-data_publicacao').first()

            if not documento:
                documento = Documento_Legal.objects.create(
                    tipo=TipoDocumentoLegal.TERMOS_DE_USO,
                    versao="1.0-2026",
                    conteudo="Termos de Uso e Política de Privacidade do AppBus conforme a LGPD.",
                    ativo=True
                )
        attrs['documento_obj'] = documento

        return attrs

    def create(self, validated_data):
        """
        Execução estrita da transação atômica (agent.md 2.2):
        Garante a criação consistente e indissociável de:
        1. UsuarioAuth (com hash seguro de senha via create_user)
        2. Pessoa (Party)
        3. Aluno (Role)
        4. Registro_Consentimento (LGPD com IP e User-Agent capturados da requisição HTTP)
        """
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError(
                "Falha de segurança LGPD: Objeto de requisição HTTP ausente no contexto do serializer."
            )

        # LGPD: IP e User-Agent inferidos EXCLUSIVAMENTE dos cabeçalhos HTTP
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Desconhecido')

        email = validated_data['email']
        password = validated_data['password']
        nome = validated_data['nome']
        cpf = validated_data['cpf']
        data_nascimento = validated_data['data_nascimento']

        cliente = validated_data['cliente_obj']
        instituicao = validated_data['instituicao_obj']
        matricula = validated_data['matricula']
        documento = validated_data['documento_obj']
        responsavel_cpf = validated_data.get('responsavel_legal_cpf')

        # Endereço (se fornecido)
        endereco_obj = None
        logradouro = validated_data.get('logradouro')
        numero = validated_data.get('numero')
        cep = validated_data.get('cep')
        bairro_id = validated_data.get('bairro_id')

        # TRANSAÇÃO ATÔMICA: Se qualquer inserção falhar, nada é persistido
        with transaction.atomic():
            # 1. Criação do Usuário com HASH CRIPTOGRÁFICO DE SENHA (create_user)
            usuario = UsuarioAuth.objects.create_user(
                email=email,
                password=password,
                ativo=True,
                is_staff=False,
                is_superuser=False
            )

            # 2. Criação opcional de Endereço
            if logradouro and numero and bairro_id:
                try:
                    bairro = Bairro.objects.get(id=bairro_id)
                    endereco_obj = Endereco.objects.create(
                        logradouro=logradouro,
                        numero=numero,
                        complemento=validated_data.get('complemento', ''),
                        cep=cep or '00000-000',
                        bairro=bairro
                    )
                except Bairro.DoesNotExist:
                    pass

            # 3. Criação da Entidade Central 'Party' (Pessoa)
            pessoa = Pessoa.objects.create(
                usuario=usuario,
                nome=nome,
                cpf=cpf,
                data_nascimento=data_nascimento,
                endereco=endereco_obj,
                anonimizado=False
            )

            # 4. Criação do Papel 'Role' (Aluno)
            aluno = Aluno.objects.create(
                pessoa=pessoa,
                cliente=cliente,
                instituicao=instituicao,
                matricula=matricula,
                status_aprovacao=TipoStatusAprovacao.PENDENTE
            )

            # 5. Prova de Consentimento LGPD (Registro_Consentimento)
            consentimento = Registro_Consentimento.objects.create(
                pessoa=pessoa,
                documento=documento,
                consentimento_concedido=True,
                responsavel_legal_cpf=responsavel_cpf,
                ip_address=ip_address,
                user_agent=user_agent
            )

            logger.info(
                f"[Onboarding Aluno] Cadastro atômico concluído com sucesso. "
                f"Aluno ID={aluno.id}, Pessoa ID={pessoa.id}, Cliente ID={cliente.id}, "
                f"Consentimento ID={consentimento.id}, LGPD IP={ip_address}"
            )

        return aluno


class AlunoDetalheResponseSerializer(serializers.ModelSerializer):
    """Serializer para retorno resumido dos dados cadastrados do Aluno."""
    nome = serializers.CharField(source='pessoa.nome', read_only=True)
    cpf = serializers.CharField(source='pessoa.cpf', read_only=True)
    email = serializers.CharField(source='pessoa.usuario.email', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome_fantasia', read_only=True)
    instituicao_nome = serializers.CharField(source='instituicao.nome', read_only=True)
    status_aprovacao_display = serializers.CharField(source='get_status_aprovacao_display', read_only=True)

    class Meta:
        model = Aluno
        fields = [
            'id',
            'nome',
            'email',
            'cpf',
            'matricula',
            'cliente_id',
            'cliente_nome',
            'instituicao_id',
            'instituicao_nome',
            'status_aprovacao',
            'status_aprovacao_display',
            'data_solicitacao'
        ]


# ==============================================================================
# 4. ENTIDADES CORE MULTI-TENANT (Etapa 2.2 - Gestão e Operação)
# ==============================================================================

class InstituicaoSerializer(serializers.ModelSerializer):
    """Serializer para Instituições de Ensino com escopo de tenant."""
    cliente_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Instituicao
        fields = ['id', 'cliente_id', 'nome', 'sigla', 'endereco', 'ativo']


class ModeloVeiculoSerializer(serializers.ModelSerializer):
    """Catálogo global de modelos de veículos rodoviários."""
    class Meta:
        model = ModeloVeiculo
        fields = ['id', 'marca', 'nome', 'ativo', 'created_at', 'updated_at']


class OnibusSerializer(serializers.ModelSerializer):
    """
    Serializer para Veículos da Frota Municipal.
    O cliente_id e qr_code_uuid são estritamente somente leitura para evitar manipulação.
    """
    cliente_id = serializers.IntegerField(read_only=True)
    qr_code_uuid = serializers.UUIDField(read_only=True)
    modelo_detalhe = ModeloVeiculoSerializer(source='modelo', read_only=True)

    class Meta:
        model = Onibus
        fields = [
            'id',
            'cliente_id',
            'modelo',
            'modelo_detalhe',
            'placa',
            'capacidade',
            'qr_code_uuid',
            'ativo',
            'created_at',
            'updated_at'
        ]


class MotoristaSerializer(serializers.ModelSerializer):
    """
    Serializer para Motoristas municipais seguindo o padrão Party/Role.
    Dados civis extraídos da entidade Pessoa.
    """
    cliente_id = serializers.IntegerField(read_only=True)
    nome = serializers.CharField(source='pessoa.nome', read_only=True)
    cpf = serializers.CharField(source='pessoa.cpf', read_only=True)

    class Meta:
        model = Motorista
        fields = [
            'id',
            'cliente_id',
            'pessoa_id',
            'nome',
            'cpf',
            'cnh',
            'categoria_cnh',
            'ativo'
        ]


class RotaInstituicaoSerializer(serializers.ModelSerializer):
    """Mapeamento de paradas de instituições em uma rota."""
    instituicao_nome = serializers.CharField(source='instituicao.nome', read_only=True)

    class Meta:
        model = RotaInstituicao
        fields = ['id', 'instituicao', 'instituicao_nome', 'ordem_parada']


class RotaSerializer(serializers.ModelSerializer):
    """
    Serializer para Rotas municipais com instituições agregadas.
    """
    cliente_id = serializers.IntegerField(read_only=True)
    paradas = RotaInstituicaoSerializer(source='rota_instituicoes', many=True, read_only=True)

    class Meta:
        model = Rota
        fields = [
            'id',
            'cliente_id',
            'nome',
            'ativo',
            'paradas',
            'created_at',
            'updated_at'
        ]


# ==============================================================================
# 5. SERIALIZERS DE GESTÃO ADMINISTRATIVA (Etapa 2.3 - Painel da Prefeitura)
# ==============================================================================

class AlunoGestaoListSerializer(serializers.ModelSerializer):
    """
    Serializer otimizado para o Painel da Prefeitura (listagem da fila de aprovação e gestão de alunos).
    """
    nome = serializers.CharField(source='pessoa.nome', read_only=True)
    cpf = serializers.CharField(source='pessoa.cpf', read_only=True)
    email = serializers.CharField(source='pessoa.usuario.email', read_only=True)
    instituicao_nome = serializers.CharField(source='instituicao.nome', read_only=True)
    instituicao_sigla = serializers.CharField(source='instituicao.sigla', read_only=True)
    status_aprovacao_display = serializers.CharField(source='get_status_aprovacao_display', read_only=True)
    avaliado_por_nome = serializers.CharField(source='avaliado_por.pessoa.nome', read_only=True, default=None)

    class Meta:
        model = Aluno
        fields = [
            'id',
            'nome',
            'email',
            'cpf',
            'matricula',
            'instituicao_id',
            'instituicao_nome',
            'instituicao_sigla',
            'status_aprovacao',
            'status_aprovacao_display',
            'data_solicitacao',
            'data_decisao',
            'avaliado_por_id',
            'avaliado_por_nome',
        ]


class AlunoGestaoDetailSerializer(AlunoGestaoListSerializer):
    """
    Serializer detalhado com dados civis completos para análise de conformidade pelo gestor municipal.
    """
    data_nascimento = serializers.DateField(source='pessoa.data_nascimento', read_only=True)
    is_menor_idade = serializers.BooleanField(source='pessoa.is_menor_idade', read_only=True)
    responsavel_legal_cpf = serializers.SerializerMethodField()

    class Meta(AlunoGestaoListSerializer.Meta):
        fields = AlunoGestaoListSerializer.Meta.fields + [
            'data_nascimento',
            'is_menor_idade',
            'responsavel_legal_cpf',
        ]

    def get_responsavel_legal_cpf(self, obj):
        consentimento = obj.pessoa.consentimentos.order_by('-data_consentimento').first()
        return consentimento.responsavel_legal_cpf if consentimento else None


class AlunoDecisaoSerializer(serializers.Serializer):
    """Serializer para validação de payload em ações de aprovação e rejeição de alunos."""
    motivo = serializers.CharField(required=False, allow_blank=True, default='')


class MotoristaCreateSerializer(serializers.ModelSerializer):
    """
    Criação de Motorista pelo Administrador Municipal.
    Padrão Party/Role (agent.md 2.2):
    Criação atômica de UsuarioAuth -> Pessoa -> Motorista.
    """
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    nome = serializers.CharField(write_only=True, max_length=255)
    cpf = serializers.CharField(write_only=True, max_length=14)
    data_nascimento = serializers.DateField(write_only=True)

    nome_completo = serializers.CharField(source='pessoa.nome', read_only=True)
    cpf_formatado = serializers.CharField(source='pessoa.cpf', read_only=True)
    email_login = serializers.CharField(source='pessoa.usuario.email', read_only=True)

    class Meta:
        model = Motorista
        fields = [
            'id',
            'email',
            'password',
            'nome',
            'cpf',
            'data_nascimento',
            'cnh',
            'categoria_cnh',
            'ativo',
            'nome_completo',
            'cpf_formatado',
            'email_login',
        ]

    def validate_email(self, value):
        email_clean = value.lower().strip()
        if UsuarioAuth.objects.filter(email=email_clean).exists():
            raise serializers.ValidationError("Este e-mail já está cadastrado no sistema.")
        return email_clean

    def validate_cpf(self, value):
        cpf_clean = ''.join(filter(str.isdigit, value))
        if len(cpf_clean) != 11:
            raise serializers.ValidationError("CPF inválido. Deve conter exatamente 11 dígitos numéricos.")
        cpf_formatado = f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
        if Pessoa.objects.filter(cpf=cpf_formatado).exists():
            raise serializers.ValidationError("Já existe uma pessoa cadastrada com este CPF.")
        return cpf_formatado

    def validate_cnh(self, value):
        cnh_clean = str(value).strip()
        if Motorista.objects.filter(cnh=cnh_clean).exists():
            raise serializers.ValidationError("Já existe um motorista cadastrado com esta CNH.")
        return cnh_clean

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as err:
            raise serializers.ValidationError(list(err.messages))
        return value

    def create(self, validated_data):
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        nome = validated_data.pop('nome')
        cpf = validated_data.pop('cpf')
        data_nascimento = validated_data.pop('data_nascimento')
        cliente = validated_data.pop('cliente')  # Injetado pelo perform_create do TenantBaseViewSet

        with transaction.atomic():
            usuario = UsuarioAuth.objects.create_user(
                email=email,
                password=password,
                is_staff=False,
                is_superuser=False
            )
            pessoa = Pessoa.objects.create(
                usuario=usuario,
                nome=nome,
                cpf=cpf,
                data_nascimento=data_nascimento
            )
            motorista = Motorista.objects.create(
                pessoa=pessoa,
                cliente=cliente,
                cnh=validated_data.get('cnh'),
                categoria_cnh=validated_data.get('categoria_cnh', 'D'),
                ativo=validated_data.get('ativo', True)
            )
            logger.info(f"[Party/Role] Motorista ID={motorista.id} criado com sucesso para Tenant={cliente.id}")
            return motorista


class ParadaInputSerializer(serializers.Serializer):
    """Representação de uma parada em uma rota para entrada via API."""
    instituicao_id = serializers.IntegerField()
    ordem_parada = serializers.IntegerField(default=1)


class RotaCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação e atualização de Rotas municipais com gerenciamento
    transacional de suas paradas de instituições (RotaInstituicao).
    """
    cliente_id = serializers.IntegerField(read_only=True)
    paradas = ParadaInputSerializer(many=True, required=False, write_only=True)
    paradas_detalhe = RotaInstituicaoSerializer(source='rota_instituicoes', many=True, read_only=True)

    class Meta:
        model = Rota
        fields = [
            'id',
            'cliente_id',
            'nome',
            'ativo',
            'paradas',
            'paradas_detalhe',
            'created_at',
            'updated_at'
        ]

    def create(self, validated_data):
        paradas_data = validated_data.pop('paradas', [])
        cliente = validated_data.pop('cliente')

        with transaction.atomic():
            rota = Rota.objects.create(cliente=cliente, **validated_data)
            self._salvar_paradas(rota, cliente, paradas_data)
            return rota

    def update(self, instance, validated_data):
        paradas_data = validated_data.pop('paradas', None)
        validated_data.pop('cliente', None)

        with transaction.atomic():
            for attr, val in validated_data.items():
                setattr(instance, attr, val)
            instance.save()

            if paradas_data is not None:
                instance.rota_instituicoes.all().delete()
                self._salvar_paradas(instance, instance.cliente, paradas_data)

            return instance

    def _salvar_paradas(self, rota, cliente, paradas_data):
        for item in paradas_data:
            inst_id = item['instituicao_id']
            ordem = item.get('ordem_parada', 1)
            instituicao = Instituicao.objects.filter(id=inst_id, cliente=cliente).first()
            if not instituicao:
                raise serializers.ValidationError(
                    {"paradas": f"Instituição ID={inst_id} não pertence à sua prefeitura ou não existe."}
                )
            RotaInstituicao.objects.create(
                rota=rota,
                instituicao=instituicao,
                ordem_parada=ordem
            )


# ==============================================================================
# 6. LGPD & ANONIMIZAÇÃO DE CONTA (Etapa 2.4 - agent.md 2.3)
# ==============================================================================

class AnonimizacaoContaSerializer(serializers.Serializer):
    """
    Serializer para o endpoint de auto-exclusão e anonimização de conta do titular.
    Exige confirmação expressa e senha do usuário para evitar exclusões acidentais ou maliciosas.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        help_text="Senha atual do titular para confirmação de identidade."
    )
    confirmacao = serializers.BooleanField(
        required=True,
        help_text="Confirmação expressa da revogação de consentimento e anonimização irreversível dos dados."
    )

    def validate_confirmacao(self, value):
        if not value:
            raise serializers.ValidationError(
                "A confirmação expressa é obrigatória para processar a anonimização dos dados."
            )
        return value

    def validate_password(self, value):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            raise serializers.ValidationError("Usuário não autenticado.")

        if not request.user.check_password(value):
            raise serializers.ValidationError("Senha incorreta. Não foi possível confirmar a titularidade da conta.")
        return value


# ==============================================================================
# 7. SERIALIZERS OPERACIONAIS CORE (Etapa 2.5 - Predição, Viagem, Embarque)
# ==============================================================================

class PrevisaoViagemSerializer(serializers.ModelSerializer):
    """Serializer para predição de demanda estudantil ('Vou / Não Vou')."""
    aluno_id = serializers.IntegerField(read_only=True)
    aluno_nome = serializers.CharField(source='aluno.pessoa.nome', read_only=True)

    class Meta:
        model = PrevisaoViagem
        fields = [
            'id',
            'aluno_id',
            'aluno_nome',
            'data',
            'vai_ida',
            'vai_volta',
            'ativo',
            'created_at',
            'updated_at',
        ]


class IniciarViagemSerializer(serializers.Serializer):
    """Payload para motorista instanciar uma viagem diária."""
    rota_id = serializers.IntegerField(required=True)
    onibus_id = serializers.IntegerField(required=True)
    sentido = serializers.ChoiceField(choices=SentidoViagem.choices, required=True)


class ViagemDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado de uma Viagem para motorista e gestores."""
    rota_nome = serializers.CharField(source='rota.nome', read_only=True)
    onibus_placa = serializers.CharField(source='onibus.placa', read_only=True)
    capacidade_onibus = serializers.IntegerField(source='onibus.capacidade', read_only=True)
    motorista_nome = serializers.CharField(source='motorista.pessoa.nome', read_only=True)
    sentido_display = serializers.CharField(source='get_sentido_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Viagem
        fields = [
            'id',
            'rota_id',
            'rota_nome',
            'onibus_id',
            'onibus_placa',
            'capacidade_onibus',
            'motorista_id',
            'motorista_nome',
            'sentido',
            'sentido_display',
            'status',
            'status_display',
            'data',
            'hora_inicio',
            'hora_fim',
            'ativo',
            'created_at',
        ]


class EmbarqueQRCodeSerializer(serializers.Serializer):
    """Payload para check-in óptico do aluno via leitura de QR Code do ônibus."""
    qr_code_uuid = serializers.UUIDField(required=True)


class EmbarqueManualSerializer(serializers.Serializer):
    """Payload para check-in manual efetuado pelo motorista no app."""
    viagem_id = serializers.IntegerField(required=True)
    aluno_id = serializers.IntegerField(required=True)


class EmbarqueResponseSerializer(serializers.ModelSerializer):
    """Serializer para retorno de confirmação de embarque."""
    aluno_nome = serializers.CharField(source='aluno.pessoa.nome', read_only=True)
    matricula = serializers.CharField(source='aluno.matricula', read_only=True)
    metodo_validacao_display = serializers.CharField(source='get_metodo_validacao_display', read_only=True)
    onibus_placa = serializers.CharField(source='viagem.onibus.placa', read_only=True)
    rota_nome = serializers.CharField(source='viagem.rota.nome', read_only=True)

    class Meta:
        model = Embarque
        fields = [
            'id',
            'viagem_id',
            'rota_nome',
            'onibus_placa',
            'aluno_id',
            'aluno_nome',
            'matricula',
            'metodo_validacao',
            'metodo_validacao_display',
            'timestamp',
        ]


class DashboardViagemResponseSerializer(serializers.Serializer):
    """Retorno estruturado do dashboard em tempo real do motorista."""
    viagem_id = serializers.IntegerField()
    rota_nome = serializers.CharField()
    onibus_placa = serializers.CharField()
    motorista_nome = serializers.CharField()
    sentido = serializers.CharField()
    sentido_display = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    data = serializers.DateField()
    hora_inicio = serializers.DateTimeField()
    capacidade_onibus = serializers.IntegerField()
    total_previstos = serializers.IntegerField()
    total_embarcados = serializers.IntegerField()
    vagas_restantes = serializers.IntegerField()
    percentual_ocupacao = serializers.FloatField()




