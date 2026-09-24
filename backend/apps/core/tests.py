"""
Suíte Completa de Testes Automatizados para AppBus (Etapas 2.1 a 2.4).
Perspectiva: Engenheiro de Qualidade (QA) Sênior e Especialista em Segurança da Informação.

Cenários Críticos Cobertos:
1. Multi-Tenant Data Leakage: Isolamento estrito entre Prefeituras A e B (anti-vazamento e 404 em ID direto).
2. Transação Atômica: Rollback integral na falha de criação em 4 tabelas (zero dados órfãos).
3. Privacidade & Anonimização LGPD: Direito ao esquecimento sem Hard Deletes (preservação de histórico).
4. Anti-Spoofing LGPD: Injeção de IP/User-Agent no payload é sumariamente neutralizada.
5. Zero Trust: Acesso anônimo rejeitado com 401 Unauthorized em todos os endpoints de negócio.
6. RBAC & Gestão: Fila de aprovação, auditoria de decisões, criação de motoristas e rotas.
"""

from datetime import date
from unittest.mock import patch
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.models import (
    UsuarioAuth,
    Pessoa,
    Cliente,
    Instituicao,
    Aluno,
    Administrador,
    Motorista,
    ModeloVeiculo,
    Onibus,
    Rota,
    RotaInstituicao,
    Viagem,
    PrevisaoViagem,
    Embarque,
    Documento_Legal,
    Registro_Consentimento,
    TipoStatusAprovacao,
    TipoDocumentoLegal,
    SentidoViagem,
    StatusViagem,
    MetodoValidacao,
)


# ==============================================================================
# 1. TESTE DE FUGA DE DADOS (MULTI-TENANCY DATA LEAKAGE)
# ==============================================================================

class MultiTenantDataLeakageAPITestCase(APITestCase):
    """
    Cenário 1: Teste de Fuga de Dados entre Municípios distintos (Prefeitura A vs Prefeitura B).
    Garante que nenhum registro transacional ou de frota vaze entre prefeituras
    e que tentativas de acesso direto por ID a registros alheios resultem em 404 Not Found.
    """

    def setUp(self):
        # 1. Criação dos Clientes (Tenants)
        self.prefeitura_a = Cliente.objects.create(
            cnpj="11.111.111/0001-11",
            razao_social="Prefeitura Municipal A",
            nome_fantasia="Prefeitura A",
            ativo=True
        )
        self.prefeitura_b = Cliente.objects.create(
            cnpj="22.222.222/0001-22",
            razao_social="Prefeitura Municipal B",
            nome_fantasia="Prefeitura B",
            ativo=True
        )

        # 2. Modelo de Veículo Global (Catálogo)
        self.modelo = ModeloVeiculo.objects.create(
            marca="Marcopolo",
            nome="Viaggio 1050",
            ativo=True
        )

        # 3. Gestor Municipal A (Prefeitura A)
        self.user_gestor_a = UsuarioAuth.objects.create_user(
            email="gestor@prefeitura-a.sp.gov.br",
            password="SenhaSeguraPrefeituraA123!",
            is_staff=True
        )
        self.pessoa_gestor_a = Pessoa.objects.create(
            usuario=self.user_gestor_a,
            nome="Carlos Gestor A",
            cpf="111.111.111-11",
            data_nascimento="1980-01-01"
        )
        self.admin_a = Administrador.objects.create(
            pessoa=self.pessoa_gestor_a,
            cliente=self.prefeitura_a,
            cargo="Secretário de Transporte",
            ativo=True
        )

        # 4. Gestor Municipal B (Prefeitura B)
        self.user_gestor_b = UsuarioAuth.objects.create_user(
            email="gestor@prefeitura-b.sp.gov.br",
            password="SenhaSeguraPrefeituraB123!",
            is_staff=True
        )
        self.pessoa_gestor_b = Pessoa.objects.create(
            usuario=self.user_gestor_b,
            nome="Roberto Gestor B",
            cpf="222.222.222-22",
            data_nascimento="1982-05-10"
        )
        self.admin_b = Administrador.objects.create(
            pessoa=self.pessoa_gestor_b,
            cliente=self.prefeitura_b,
            cargo="Coordenador de Frotas",
            ativo=True
        )

        # 5. Gestor A cria Ônibus e Rota na Prefeitura A
        self.onibus_a = Onibus.objects.create(
            cliente=self.prefeitura_a,
            modelo=self.modelo,
            placa="AAA-1111",
            capacidade=44,
            ativo=True
        )
        self.rota_a = Rota.objects.create(
            cliente=self.prefeitura_a,
            nome="Linha Noturna Prefeitura A",
            ativo=True
        )

        # 6. Ônibus e Rota na Prefeitura B
        self.onibus_b = Onibus.objects.create(
            cliente=self.prefeitura_b,
            modelo=self.modelo,
            placa="BBB-2222",
            capacidade=50,
            ativo=True
        )

    def test_gestor_b_faz_get_e_nao_enxerga_onibus_prefeitura_a(self):
        """Asserção 1: O Gestor B consulta autocarros e o queryset NÃO contém o autocarro da Prefeitura A."""
        self.client.force_authenticate(user=self.user_gestor_b)
        response = self.client.get('/api/veiculos/onibus/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        placas = [item['placa'] for item in response.data]
        self.assertIn("BBB-2222", placas)
        self.assertNotIn("AAA-1111", placas)

    def test_gestor_b_faz_get_e_nao_enxerga_rotas_prefeitura_a(self):
        """Asserção 1.1: O Gestor B consulta rotas e não visualiza rotas da Prefeitura A."""
        self.client.force_authenticate(user=self.user_gestor_b)
        response = self.client.get('/api/rotas/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        nomes_rotas = [item['nome'] for item in response.data]
        self.assertNotIn("Linha Noturna Prefeitura A", nomes_rotas)

    def test_gestor_b_tentativa_patch_injetando_id_onibus_prefeitura_a_retorna_404(self):
        """Asserção 2: O Gestor B tenta fazer PATCH injetando o ID do ônibus de A -> 404 Not Found."""
        self.client.force_authenticate(user=self.user_gestor_b)
        url_onibus_a = f'/api/veiculos/onibus/{self.onibus_a.id}/'

        response = self.client.patch(url_onibus_a, {"capacidade": 99}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Integridade do banco: capacidade original mantida
        self.onibus_a.refresh_from_db()
        self.assertEqual(self.onibus_a.capacidade, 44)

    def test_gestor_b_tentativa_delete_injetando_id_onibus_prefeitura_a_retorna_404(self):
        """Asserção 2.1: O Gestor B tenta fazer DELETE injetando o ID do ônibus de A -> 404 Not Found."""
        self.client.force_authenticate(user=self.user_gestor_b)
        url_onibus_a = f'/api/veiculos/onibus/{self.onibus_a.id}/'

        response = self.client.delete(url_onibus_a)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Registro permanece íntegro
        self.assertTrue(Onibus.objects.filter(id=self.onibus_a.id).exists())


# ==============================================================================
# 2. TESTE DE FALHA NA TRANSAÇÃO ATÔMICA (CADASTRO DE ALUNO)
# ==============================================================================

class TransacaoAtomicaCadastroAlunoAPITestCase(APITestCase):
    """
    Cenário 2: Teste de Falha na Transação Atômica de Cadastro de Aluno.
    Garante que se qualquer etapa da inserção sequencial falhar (ex: RegistroConsentimento),
    o rollback do banco de dados reverta 100% dos dados, deixando ZERO registros órfãos.
    """

    def setUp(self):
        self.cliente = Cliente.objects.create(
            cnpj="99.999.999/0001-99",
            razao_social="Prefeitura Municipal Atomic Test",
            nome_fantasia="Prefeitura Atomic",
            ativo=True
        )
        self.instituicao = Instituicao.objects.create(
            cliente=self.cliente,
            nome="Faculdade de Tecnologia de Teste",
            sigla="FATEC-TEST",
            ativo=True
        )
        self.documento = Documento_Legal.objects.create(
            tipo=TipoDocumentoLegal.TERMOS_DE_USO,
            versao="1.0-2026",
            conteudo="Termos de Uso Oficiais",
            ativo=True
        )
        self.url_registro = '/api/auth/registro-aluno/'

    def test_falha_na_criacao_do_consentimento_executa_rollback_completo(self):
        """
        Simula submissão de payload de cadastro completo, mas injeta falha crítica
        no Registro_Consentimento (última etapa). Comprova zero registros órfãos.
        """
        payload = {
            "email": "aluno.falha.consentimento@faculdade.edu.br",
            "password": "SenhaSeguraAtomic123!",
            "nome": "Candidato Falha Consentimento",
            "cpf": "100.200.300-40",
            "data_nascimento": "2000-01-01",
            "cliente_id": self.cliente.id,
            "instituicao_id": self.instituicao.id,
            "matricula": "ATOMIC-001",
            "termo_aceito": True,
            "documento_legal_id": self.documento.id
        }

        # Mock da última etapa (Registro_Consentimento) para disparar falha intencional
        with patch('apps.core.models.Registro_Consentimento.objects.create', side_effect=RuntimeError("Falha crítica no consentimento")):
            with self.assertRaises(RuntimeError):
                self.client.post(self.url_registro, payload, format='json')

        # Asserções Exigidas: ZERO REGISTROS ÓRFÃOS (count == 0 em todas as tabelas)
        self.assertEqual(UsuarioAuth.objects.filter(email="aluno.falha.consentimento@faculdade.edu.br").count(), 0)
        self.assertEqual(Pessoa.objects.filter(cpf="100.200.300-40").count(), 0)
        self.assertEqual(Aluno.objects.filter(matricula="ATOMIC-001").count(), 0)
        self.assertEqual(Registro_Consentimento.objects.filter(pessoa__nome="Candidato Falha Consentimento").count(), 0)

    def test_falha_na_criacao_do_aluno_executa_rollback_completo(self):
        """
        Simula falha na criação da entidade Aluno. Comprova que UsuarioAuth e Pessoa não sobram órfãos.
        """
        payload = {
            "email": "aluno.falha.aluno@faculdade.edu.br",
            "password": "SenhaSeguraAtomic123!",
            "nome": "Candidato Falha Aluno",
            "cpf": "200.300.400-50",
            "data_nascimento": "2001-02-02",
            "cliente_id": self.cliente.id,
            "instituicao_id": self.instituicao.id,
            "matricula": "ATOMIC-002",
            "termo_aceito": True,
            "documento_legal_id": self.documento.id
        }

        with patch('apps.core.models.Aluno.objects.create', side_effect=RuntimeError("Falha simulada na criação do Aluno")):
            with self.assertRaises(RuntimeError):
                self.client.post(self.url_registro, payload, format='json')

        self.assertEqual(UsuarioAuth.objects.filter(email="aluno.falha.aluno@faculdade.edu.br").count(), 0)
        self.assertEqual(Pessoa.objects.filter(cpf="200.300.400-50").count(), 0)
        self.assertEqual(Aluno.objects.filter(matricula="ATOMIC-002").count(), 0)


# ==============================================================================
# 3. TESTE DO FLUXO DE ANONIMIZAÇÃO (LGPD - DIREITO AO ESQUECIMENTO)
# ==============================================================================

class LGPDAnonimizacaoDireitoAoEsquecimentoAPITestCase(APITestCase):
    """
    Cenário 3: Teste do Fluxo de Anonimização (LGPD Art. 18, VI).
    Valida mascaramento irreversível de PII, revogação de acesso e a REGRA DE OURO
    da inexistência de Hard Deletes (preservação dos registros e IDs históricos).
    """

    def setUp(self):
        # 1. Tenant e Escola
        self.cliente = Cliente.objects.create(
            cnpj="55.555.555/0001-55",
            razao_social="Prefeitura Municipal LGPD Test",
            nome_fantasia="Prefeitura LGPD",
            ativo=True
        )
        self.instituicao = Instituicao.objects.create(
            cliente=self.cliente,
            nome="Centro Universitário LGPD",
            sigla="UNILGPD",
            ativo=True
        )

        # 2. Aluno autenticado com dados civis completos
        self.senha_aluno = "SenhaForteTitular2026!"
        self.usuario_aluno = UsuarioAuth.objects.create_user(
            email="aluno.titular@unilgpd.edu.br",
            password=self.senha_aluno,
            ativo=True
        )
        self.pessoa_aluno = Pessoa.objects.create(
            usuario=self.usuario_aluno,
            nome="Mariana Souza Oliveira",
            cpf="333.444.555-66",
            data_nascimento="2000-10-25",
            anonimizado=False
        )
        self.aluno = Aluno.objects.create(
            pessoa=self.pessoa_aluno,
            cliente=self.cliente,
            instituicao=self.instituicao,
            matricula="MAT-LGPD-2026",
            status_aprovacao=TipoStatusAprovacao.APROVADO
        )

        # 3. Histórico Operacional (Frota, Rota, Viagem e Embarque)
        self.modelo = ModeloVeiculo.objects.create(marca="Mercedes-Benz", nome="OF-1721")
        self.onibus = Onibus.objects.create(cliente=self.cliente, modelo=self.modelo, placa="LGP-2026", capacidade=40)
        self.rota = Rota.objects.create(cliente=self.cliente, nome="Rota Universitária Central")
        self.user_mot = UsuarioAuth.objects.create_user(email="mot.lgpd@prefeitura.gov.br", password="SenhaMotorista123!")
        self.pessoa_mot = Pessoa.objects.create(usuario=self.user_mot, nome="Motorista Teste", cpf="999.888.777-11")
        self.motorista = Motorista.objects.create(pessoa=self.pessoa_mot, cliente=self.cliente, cnh="11223344556")

        self.viagem = Viagem.objects.create(
            rota=self.rota,
            onibus=self.onibus,
            motorista=self.motorista,
            sentido=SentidoViagem.IDA,
            status=StatusViagem.CONCLUIDA,
            data=date.today(),
            hora_inicio=timezone.now()
        )
        self.previsao = PrevisaoViagem.objects.create(
            aluno=self.aluno,
            data=date.today(),
            vai_ida=True,
            vai_volta=True
        )
        self.embarque = Embarque.objects.create(
            viagem=self.viagem,
            aluno=self.aluno,
            metodo_validacao=MetodoValidacao.QR_CODE_APP,
            timestamp=timezone.now()
        )

        self.url_exclusao = '/api/auth/solicitar-exclusao/'

    def test_fluxo_completo_anonimizacao_sem_hard_deletes(self):
        """
        Executa solicitação de exclusão/anonimização pelo aluno e valida todas as asserções:
        1. Status HTTP 200 OK.
        2. pessoa.anonimizado == True e usuario.is_active == False.
        3. Nome mascarado ("Anonimizado" / "Usuário Anonimizado") e CPF nulo.
        4. IDs primários de Pessoa e Aluno intactos (NO HARD DELETE).
        5. UsuarioAuth associado com is_active=False e ativo=False.
        """
        pessoa_id_original = self.pessoa_aluno.id
        aluno_id_original = self.aluno.id
        embarque_id_original = self.embarque.id

        self.client.force_authenticate(user=self.usuario_aluno)
        payload = {"password": self.senha_aluno, "confirmacao": True}

        response = self.client.post(self.url_exclusao, payload, format='json')

        # Asserção 1: Retorna 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("anonimizado"))

        # Asserção 2 e 3: Pessoa mascarada e desvinculada de dados pessoais
        self.pessoa_aluno.refresh_from_db()
        self.assertTrue(self.pessoa_aluno.anonimizado)
        self.assertIn("Anonimizado", self.pessoa_aluno.nome)
        self.assertIsNone(self.pessoa_aluno.cpf)
        self.assertIsNone(self.pessoa_aluno.data_nascimento)
        self.assertIsNone(self.pessoa_aluno.endereco)

        # Asserção 4: IDs primários preservados intactos (NO HARD DELETES)
        self.assertEqual(self.pessoa_aluno.id, pessoa_id_original)
        self.assertEqual(self.aluno.id, aluno_id_original)
        self.assertTrue(Pessoa.objects.filter(id=pessoa_id_original).exists())
        self.assertTrue(Aluno.objects.filter(id=aluno_id_original).exists())
        self.assertTrue(Embarque.objects.filter(id=embarque_id_original).exists())

        # Asserção 5: UsuarioAuth inativo e com senha revogada
        self.usuario_aluno.refresh_from_db()
        self.assertFalse(self.usuario_aluno.is_active)
        self.assertFalse(self.usuario_aluno.ativo)
        self.assertFalse(self.usuario_aluno.has_usable_password())
        self.assertTrue(self.usuario_aluno.email.startswith("anonimizado_"))

        # Asserção Adicional: Bloqueio de login subsequente
        login_resp = self.client.post('/api/token/', {
            "email": "aluno.titular@unilgpd.edu.br",
            "password": self.senha_aluno
        }, format='json')
        self.assertEqual(login_resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ==============================================================================
# 4. TESTE DE SEGURANÇA LGPD (INJEÇÃO DE IP/USER-AGENT)
# ==============================================================================

class LGPDAntiSpoofingConsentimentoAPITestCase(APITestCase):
    """
    Cenário 4: Teste de Anti-Spoofing de Consentimento LGPD.
    Garante que tentativas maliciosas de forjar a prova de consentimento enviando
    'ip_address' e 'user_agent' no JSON do request sejam desconsideradas, e que
    o backend grave EXCLUSIVAMENTE os dados reais dos cabeçalhos HTTP.
    """

    def setUp(self):
        self.cliente = Cliente.objects.create(
            cnpj="77.777.777/0001-77",
            razao_social="Prefeitura Anti-Spoofing",
            ativo=True
        )
        self.instituicao = Instituicao.objects.create(
            cliente=self.cliente,
            nome="Faculdade de Segurança",
            sigla="FACSEG",
            ativo=True
        )
        self.documento = Documento_Legal.objects.create(
            tipo=TipoDocumentoLegal.TERMOS_DE_USO,
            versao="1.0-2026",
            conteudo="Termos de Uso",
            ativo=True
        )
        self.url_registro = '/api/auth/registro-aluno/'

    def test_ignora_ip_e_user_agent_injetados_no_payload_e_usa_cabecalho_http_real(self):
        """
        Asserções:
        1. API processa o registro com sucesso (201 Created), ignorando os campos falsos no JSON.
        2. No banco, RegistroConsentimento armazena o IP e User-Agent reais dos cabeçalhos HTTP.
        """
        payload_com_injecao = {
            "email": "vitima.spoofing@facseg.edu.br",
            "password": "SenhaSegura123!",
            "nome": "Candidato Anti Spoofing",
            "cpf": "777.666.555-44",
            "data_nascimento": "1999-09-09",
            "cliente_id": self.cliente.id,
            "instituicao_id": self.instituicao.id,
            "matricula": "SEC-2026-01",
            "termo_aceito": True,
            "documento_legal_id": self.documento.id,
            # Tentativa de injeção de consentimento forjado:
            "ip_address": "198.51.100.99",
            "user_agent": "HackerBot/1.0 (Spoofed Machine)"
        }

        # Requisição enviada com cabeçalhos HTTP reais de cliente legítimo
        headers_reais = {
            "REMOTE_ADDR": "203.0.113.42",
            "HTTP_USER_AGENT": "AppBus-Mobile-PWA/2.4 (Android 14; Pixel 8)"
        }

        response = self.client.post(
            self.url_registro,
            payload_com_injecao,
            format='json',
            **headers_reais
        )

        # Asserção 1: Sucesso no processamento
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Asserção 2: Validação no banco de dados
        pessoa = Pessoa.objects.get(cpf="777.666.555-44")
        consentimento = Registro_Consentimento.objects.get(pessoa=pessoa)

        # O IP forjado (198.51.100.99) NÃO deve ter sido gravado
        self.assertNotEqual(consentimento.ip_address, "198.51.100.99")
        # O User-Agent forjado ("HackerBot/1.0") NÃO deve ter sido gravado
        self.assertNotEqual(consentimento.user_agent, "HackerBot/1.0 (Spoofed Machine)")

        # Os valores gravados DEVEM ser os provenientes da requisição HTTP real
        self.assertEqual(consentimento.ip_address, "203.0.113.42")
        self.assertEqual(consentimento.user_agent, "AppBus-Mobile-PWA/2.4 (Android 14; Pixel 8)")


# ==============================================================================
# 5. AUTENTICAÇÃO BASE (ZERO TRUST)
# ==============================================================================

class ZeroTrustAutenticacaoBaseAPITestCase(APITestCase):
    """
    Cenário 5: Teste de Arquitetura Zero Trust.
    Garante que qualquer requisição anônima (sem token JWT válido) seja
    bloqueada sumariamente com status HTTP 401 Unauthorized.
    """

    def test_usuario_anonimo_bloqueado_em_instituicoes(self):
        """Bloqueio de anônimo em /api/instituicoes/ -> 401 Unauthorized."""
        response = self.client.get('/api/instituicoes/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_anonimo_bloqueado_em_onibus(self):
        """Bloqueio de anônimo em /api/veiculos/onibus/ -> 401 Unauthorized."""
        response = self.client.get('/api/veiculos/onibus/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_anonimo_bloqueado_em_rotas(self):
        """Bloqueio de anônimo em /api/rotas/ -> 401 Unauthorized."""
        response = self.client.get('/api/rotas/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_anonimo_bloqueado_em_motoristas(self):
        """Bloqueio de anônimo em /api/motoristas/ -> 401 Unauthorized."""
        response = self.client.get('/api/motoristas/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_anonimo_bloqueado_em_alunos(self):
        """Bloqueio de anônimo em /api/alunos/ -> 401 Unauthorized."""
        response = self.client.get('/api/alunos/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ==============================================================================
# 6. GESTÃO MUNICIPAL, FILA DE APROVAÇÃO E RBAC
# ==============================================================================

class GestaoFilaAprovacaoERBACAPITestCase(APITestCase):
    """
    Testes de Gestão e Auditoria de Alunos (Fila de Aprovação),
    Permissões Granulares (IsTenantAdmin) e CRUDs Operacionais.
    """

    def setUp(self):
        # 1. Tenants (Prefeituras Alfa e Beta)
        self.prefeitura_a = Cliente.objects.create(
            cnpj="10.000.000/0001-10",
            razao_social="Prefeitura Municipal Alfa",
            ativo=True
        )
        self.prefeitura_b = Cliente.objects.create(
            cnpj="20.000.000/0001-20",
            razao_social="Prefeitura Municipal Beta",
            ativo=True
        )

        # 2. Instituições
        self.inst_a = Instituicao.objects.create(
            cliente=self.prefeitura_a,
            nome="Faculdade Alfa",
            sigla="FALFA",
            ativo=True
        )
        self.inst_b = Instituicao.objects.create(
            cliente=self.prefeitura_b,
            nome="Faculdade Beta",
            sigla="FBETA",
            ativo=True
        )

        # 3. Gestor Administrador Alfa
        self.user_admin_a = UsuarioAuth.objects.create_user(
            email="admin.alfa@prefeitura.gov.br",
            password="SenhaSegura123!",
            is_staff=True
        )
        self.pessoa_admin_a = Pessoa.objects.create(
            usuario=self.user_admin_a,
            nome="Gestor Alfa",
            cpf="444.333.222-11",
            data_nascimento="1980-01-01"
        )
        self.admin_alfa = Administrador.objects.create(
            pessoa=self.pessoa_admin_a,
            cliente=self.prefeitura_a,
            cargo="Secretário de Transporte",
            ativo=True
        )

        # 4. Aluno Pendente Alfa
        self.user_aluno_a = UsuarioAuth.objects.create_user(
            email="aluno.alfa@faculdade.edu.br",
            password="SenhaSegura123!"
        )
        self.pessoa_aluno_a = Pessoa.objects.create(
            usuario=self.user_aluno_a,
            nome="Juliana Estudante Alfa",
            cpf="555.444.333-22",
            data_nascimento="2002-03-15"
        )
        self.aluno_pendente_a = Aluno.objects.create(
            pessoa=self.pessoa_aluno_a,
            cliente=self.prefeitura_a,
            instituicao=self.inst_a,
            matricula="MAT-ALFA-01",
            status_aprovacao=TipoStatusAprovacao.PENDENTE
        )

        # 5. Aluno Pendente Beta
        self.user_aluno_b = UsuarioAuth.objects.create_user(
            email="aluno.beta@faculdade.edu.br",
            password="SenhaSegura123!"
        )
        self.pessoa_aluno_b = Pessoa.objects.create(
            usuario=self.user_aluno_b,
            nome="Lucas Estudante Beta",
            cpf="666.555.444-33",
            data_nascimento="2001-04-20"
        )
        self.aluno_pendente_b = Aluno.objects.create(
            pessoa=self.pessoa_aluno_b,
            cliente=self.prefeitura_b,
            instituicao=self.inst_b,
            matricula="MAT-BETA-02",
            status_aprovacao=TipoStatusAprovacao.PENDENTE
        )

    def test_admin_visualiza_fila_pendente_com_isolamento_tenant(self):
        """Admin visualiza a fila pendente retornando apenas alunos de seu município."""
        self.client.force_authenticate(user=self.user_admin_a)
        response = self.client.get('/api/alunos/fila-pendente/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        matriculas = [item['matricula'] for item in response.data]
        self.assertIn("MAT-ALFA-01", matriculas)
        self.assertNotIn("MAT-BETA-02", matriculas)

    def test_admin_aprova_aluno_com_sucesso_e_auditoria(self):
        """Admin aprova aluno registrando status_aprovacao='aprovado', data_decisao e avaliador."""
        self.client.force_authenticate(user=self.user_admin_a)
        url_aprovar = f"/api/alunos/{self.aluno_pendente_a.id}/aprovar/"

        response = self.client.post(url_aprovar, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.aluno_pendente_a.refresh_from_db()
        self.assertEqual(self.aluno_pendente_a.status_aprovacao, TipoStatusAprovacao.APROVADO)
        self.assertIsNotNone(self.aluno_pendente_a.data_decisao)
        self.assertEqual(self.aluno_pendente_a.avaliado_por, self.admin_alfa)

    def test_admin_rejeita_aluno_com_sucesso(self):
        """Admin rejeita solicitação registrando status_aprovacao='rejeitado' e auditoria."""
        self.client.force_authenticate(user=self.user_admin_a)
        url_rejeitar = f"/api/alunos/{self.aluno_pendente_a.id}/rejeitar/"

        response = self.client.post(url_rejeitar, {"motivo": "Documentação inconsistente"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.aluno_pendente_a.refresh_from_db()
        self.assertEqual(self.aluno_pendente_a.status_aprovacao, TipoStatusAprovacao.REJEITADO)
        self.assertIsNotNone(self.aluno_pendente_a.data_decisao)
        self.assertEqual(self.aluno_pendente_a.avaliado_por, self.admin_alfa)

    def test_aluno_bloqueado_ao_tentar_acessar_gestao_ou_aprovar(self):
        """Aluno recebe 403 Forbidden ao tentar listar painel de alunos ou aprovar."""
        self.client.force_authenticate(user=self.user_aluno_a)

        resp_list = self.client.get('/api/alunos/')
        self.assertEqual(resp_list.status_code, status.HTTP_403_FORBIDDEN)

        resp_aprovar = self.client.post(f"/api/alunos/{self.aluno_pendente_a.id}/aprovar/", {}, format='json')
        self.assertEqual(resp_aprovar.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cadastra_motorista_party_role_atomico(self):
        """Admin cadastra Motorista criando atomicamente UsuarioAuth, Pessoa e Motorista."""
        self.client.force_authenticate(user=self.user_admin_a)

        payload_motorista = {
            "email": "motorista.jose@prefeitura-alfa.sp.gov.br",
            "password": "SenhaForteMotorista2026!",
            "nome": "José Motorista Alfa",
            "cpf": "999.777.555-33",
            "data_nascimento": "1975-06-20",
            "cnh": "55667788990",
            "categoria_cnh": "D",
            "ativo": True
        }

        response = self.client.post('/api/motoristas/', payload_motorista, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        usuario = UsuarioAuth.objects.get(email="motorista.jose@prefeitura-alfa.sp.gov.br")
        self.assertTrue(usuario.check_password("SenhaForteMotorista2026!"))

        pessoa = Pessoa.objects.get(usuario=usuario)
        self.assertEqual(pessoa.nome, "José Motorista Alfa")

        motorista = Motorista.objects.get(pessoa=pessoa)
        self.assertEqual(motorista.cnh, "55667788990")
        self.assertEqual(motorista.cliente, self.prefeitura_a)

    def test_aluno_pode_ler_rotas_mas_nao_pode_criar(self):
        """Aluno pode consultar rotas de seu município, mas tem criação bloqueada (IsTenantAdminOrReadOnly)."""
        rota = Rota.objects.create(cliente=self.prefeitura_a, nome="Linha Circular Campus", ativo=True)

        self.client.force_authenticate(user=self.user_aluno_a)

        resp_get = self.client.get('/api/rotas/')
        self.assertEqual(resp_get.status_code, status.HTTP_200_OK)

        resp_post = self.client.post('/api/rotas/', {"nome": "Linha Ilegal"}, format='json')
        self.assertEqual(resp_post.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cadastra_rota_com_paradas_ordenadas(self):
        """Admin cadastra rota vinculando instituições com ordem de parada."""
        self.client.force_authenticate(user=self.user_admin_a)

        payload = {
            "nome": "Rota Alfa Express",
            "ativo": True,
            "paradas": [
                {"instituicao_id": self.inst_a.id, "ordem_parada": 1}
            ]
        }

        response = self.client.post('/api/rotas/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        rota = Rota.objects.get(nome="Rota Alfa Express")
        self.assertEqual(rota.cliente, self.prefeitura_a)
        self.assertEqual(rota.rota_instituicoes.count(), 1)
        self.assertEqual(rota.rota_instituicoes.first().instituicao, self.inst_a)

    def test_admin_rejeitado_ao_vincular_instituicao_outro_tenant(self):
        """Multi-tenant: Admin não pode incluir em sua rota uma instituição pertencente a outra prefeitura."""
        self.client.force_authenticate(user=self.user_admin_a)

        payload_invalido = {
            "nome": "Rota Invasora",
            "paradas": [
                {"instituicao_id": self.inst_b.id, "ordem_parada": 1}
            ]
        }

        response = self.client.post('/api/rotas/', payload_invalido, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("paradas", response.data)


# ==============================================================================
# 7. VALIDAÇÕES LGPD DE MENORES E PROVAS DE CONSENTIMENTO
# ==============================================================================

class AlunoOnboardingValidacoesAPITestCase(APITestCase):
    """
    Testes de regras LGPD complementares:
    - Menores de 18 anos exigem CPF do responsável legal.
    - Opt-in obrigatório (termo_aceito=True).
    - Criptografia de senhas (nunca texto puro).
    """

    def setUp(self):
        self.cliente = Cliente.objects.create(
            cnpj="88.888.888/0001-88",
            razao_social="Prefeitura Validações LGPD",
            ativo=True
        )
        self.instituicao = Instituicao.objects.create(
            cliente=self.cliente,
            nome="Escola Técnica Municipal",
            sigla="ETEC-MUN",
            ativo=True
        )
        self.url_registro = '/api/auth/registro-aluno/'

    def test_onboarding_menor_idade_sem_responsavel_falha(self):
        """Menor de 18 anos é rejeitado se não informar CPF do responsável legal (LGPD)."""
        payload = {
            "email": "menor.sem.cpf@escola.edu.br",
            "password": "SenhaSegura123!",
            "nome": "Estudante Menor",
            "cpf": "111.222.333-44",
            "data_nascimento": "2010-01-01",  # Menor de 18 anos
            "cliente_id": self.cliente.id,
            "instituicao_id": self.instituicao.id,
            "matricula": "MENOR-01",
            "termo_aceito": True,
            "responsavel_legal_cpf": ""
        }

        response = self.client.post(self.url_registro, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("responsavel_legal_cpf", response.data)

        # Atomicidade
        self.assertFalse(UsuarioAuth.objects.filter(email="menor.sem.cpf@escola.edu.br").exists())

    def test_onboarding_menor_idade_com_responsavel_sucesso(self):
        """Menor de 18 anos com CPF de responsável informado é cadastrado com sucesso."""
        payload = {
            "email": "menor.com.cpf@escola.edu.br",
            "password": "SenhaSegura123!",
            "nome": "Estudante Apoiado",
            "cpf": "999.888.777-66",
            "data_nascimento": "2010-01-01",
            "cliente_id": self.cliente.id,
            "instituicao_id": self.instituicao.id,
            "matricula": "MENOR-02",
            "termo_aceito": True,
            "responsavel_legal_cpf": "555.444.333-22"
        }

        response = self.client.post(self.url_registro, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        usuario = UsuarioAuth.objects.get(email="menor.com.cpf@escola.edu.br")
        pessoa = Pessoa.objects.get(usuario=usuario)
        consentimento = Registro_Consentimento.objects.get(pessoa=pessoa)
        self.assertEqual(consentimento.responsavel_legal_cpf, "555.444.333-22")

    def test_recusa_sem_consentimento_termos(self):
        """Cadastro sem consentimento expresso dos Termos de Uso é rejeitado."""
        payload = {
            "email": "sem.termo@faculdade.edu.br",
            "password": "SenhaSegura123!",
            "nome": "Candidato Sem Termo",
            "cpf": "888.777.666-55",
            "data_nascimento": "1999-01-01",
            "cliente_id": self.cliente.id,
            "instituicao_id": self.instituicao.id,
            "matricula": "TERMO-01",
            "termo_aceito": False
        }

        response = self.client.post(self.url_registro, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("termo_aceito", response.data)

    def test_senha_nunca_armazenada_em_texto_puro(self):
        """Valida que a senha é persistida exclusivamente como hash criptográfico."""
        payload = {
            "email": "teste.hash@faculdade.edu.br",
            "password": "SenhaUltraSecreta2026!",
            "nome": "Usuario Hash",
            "cpf": "444.555.666-77",
            "data_nascimento": "2000-01-01",
            "cliente_id": self.cliente.id,
            "instituicao_id": self.instituicao.id,
            "matricula": "HASH-01",
            "termo_aceito": True
        }

        response = self.client.post(self.url_registro, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        usuario = UsuarioAuth.objects.get(email="teste.hash@faculdade.edu.br")
        self.assertNotEqual(usuario.password, "SenhaUltraSecreta2026!")
        self.assertTrue(usuario.check_password("SenhaUltraSecreta2026!"))
        self.assertTrue(usuario.password.startswith("pbkdf2_") or usuario.password.startswith("argon2"))


# ==============================================================================
# 8. TESTES DE FLUXOS OPERACIONAIS CORE (Etapa 2.5 - agent.md 2.4, 2.5)
# ==============================================================================

class OperacaoCoreAPITestCase(APITestCase):
    """
    Testes de Fluxos Operacionais Core:
    1. Predição de Demanda ("Vou/Não Vou") com update_or_create idempotente.
    2. Instanciação e Conclusão de Viagens pelo motorista.
    3. Check-in Óptico (QR Code) e Manual com proteção anti-duplicidade em transaction.atomic().
    4. Dashboard em Tempo Real do Motorista com contagens agregadas (COUNT) no PostgreSQL.
    """

    def setUp(self):
        # 1. Tenant e Escola
        self.cliente = Cliente.objects.create(
            cnpj="60.000.000/0001-60",
            razao_social="Prefeitura Operacional",
            nome_fantasia="Prefeitura Operacional",
            ativo=True
        )
        self.instituicao = Instituicao.objects.create(
            cliente=self.cliente,
            nome="Centro Tecnológico de Operações",
            sigla="CTO",
            ativo=True
        )

        # 2. Modelo, Frota e Rota
        self.modelo = ModeloVeiculo.objects.create(marca="Marcopolo", nome="Paradiso 1200")
        self.onibus = Onibus.objects.create(
            cliente=self.cliente,
            modelo=self.modelo,
            placa="OPE-2026",
            capacidade=44,
            ativo=True
        )
        self.rota = Rota.objects.create(
            cliente=self.cliente,
            nome="Rota 01 - Universitária Expressa",
            ativo=True
        )

        # 3. Motorista Autenticado
        self.user_motorista = UsuarioAuth.objects.create_user(
            email="motorista.operacao@prefeitura.gov.br",
            password="SenhaMotorista2026!"
        )
        self.pessoa_motorista = Pessoa.objects.create(
            usuario=self.user_motorista,
            nome="Marcos Motorista Operacional",
            cpf="789.789.789-78",
            data_nascimento="1979-08-10"
        )
        self.motorista = Motorista.objects.create(
            pessoa=self.pessoa_motorista,
            cliente=self.cliente,
            cnh="77889900112",
            categoria_cnh="D",
            ativo=True
        )

        # 4. Aluno Aprovado (Passageiro)
        self.user_aluno = UsuarioAuth.objects.create_user(
            email="aluno.operacao@cto.edu.br",
            password="SenhaAluno2026!"
        )
        self.pessoa_aluno = Pessoa.objects.create(
            usuario=self.user_aluno,
            nome="Camila Estudante Operacional",
            cpf="321.321.321-32",
            data_nascimento="2002-12-05"
        )
        self.aluno = Aluno.objects.create(
            pessoa=self.pessoa_aluno,
            cliente=self.cliente,
            instituicao=self.instituicao,
            matricula="MAT-OPE-01",
            status_aprovacao=TipoStatusAprovacao.APROVADO
        )

        # 5. Aluno com Cadastro Pendente (Sem Aprovação)
        self.user_aluno_pendente = UsuarioAuth.objects.create_user(
            email="aluno.pendente.ope@cto.edu.br",
            password="SenhaAluno2026!"
        )
        self.pessoa_aluno_pendente = Pessoa.objects.create(
            usuario=self.user_aluno_pendente,
            nome="Pedro Aluno Pendente",
            cpf="654.654.654-65",
            data_nascimento="2003-01-15"
        )
        self.aluno_pendente = Aluno.objects.create(
            pessoa=self.pessoa_aluno_pendente,
            cliente=self.cliente,
            instituicao=self.instituicao,
            matricula="MAT-OPE-PEND",
            status_aprovacao=TipoStatusAprovacao.PENDENTE
        )

    def test_predicao_demanda_aluno_aprovado_update_or_create(self):
        """
        Aluno aprovado declara e depois atualiza intenção ('Vou/Não Vou').
        Valida idempotência e atualização no mesmo dia sem criar duplicidades.
        """
        self.client.force_authenticate(user=self.user_aluno)
        hoje = date.today()

        # 1. Criação inicial da previsão
        payload_1 = {"data": str(hoje), "vai_ida": True, "vai_volta": False}
        resp_1 = self.client.post('/api/operacao/predicao/', payload_1, format='json')
        self.assertEqual(resp_1.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resp_1.data['vai_ida'])
        self.assertFalse(resp_1.data['vai_volta'])

        # 2. Atualização via PATCH para o mesmo dia
        payload_2 = {"data": str(hoje), "vai_ida": False, "vai_volta": True}
        resp_2 = self.client.patch('/api/operacao/predicao/', payload_2, format='json')
        self.assertEqual(resp_2.status_code, status.HTTP_200_OK)
        self.assertFalse(resp_2.data['vai_ida'])
        self.assertTrue(resp_2.data['vai_volta'])

        # Comprova que a constraint unique_together (aluno, data) manteve apenas 1 registro
        self.assertEqual(PrevisaoViagem.objects.filter(aluno=self.aluno, data=hoje).count(), 1)

    def test_predicao_demanda_aluno_pendente_bloqueada(self):
        """Aluno sem aprovação cadastral não pode registrar previsão de viagem."""
        self.client.force_authenticate(user=self.user_aluno_pendente)
        payload = {"data": str(date.today()), "vai_ida": True, "vai_volta": True}

        response = self.client.post('/api/operacao/predicao/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("erro", response.data)

    def test_motorista_inicia_viagem_com_sucesso(self):
        """Motorista inicia viagem definindo rota, ônibus e sentido."""
        self.client.force_authenticate(user=self.user_motorista)
        payload = {
            "rota_id": self.rota.id,
            "onibus_id": self.onibus.id,
            "sentido": SentidoViagem.IDA
        }

        response = self.client.post('/api/operacao/viagem/iniciar/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], StatusViagem.EM_ANDAMENTO)
        self.assertIsNotNone(response.data['hora_inicio'])

        # Validação no banco
        viagem = Viagem.objects.get(id=response.data['id'])
        self.assertEqual(viagem.motorista, self.motorista)
        self.assertEqual(viagem.status, StatusViagem.EM_ANDAMENTO)

    def test_motorista_bloqueado_ao_tentar_usar_rota_outro_municipio(self):
        """Multi-tenant: Motorista não pode iniciar viagem com rota pertencente a outra prefeitura."""
        outro_cliente = Cliente.objects.create(cnpj="91.919.919/0001-91", razao_social="Outra Prefeitura")
        rota_alheia = Rota.objects.create(cliente=outro_cliente, nome="Rota Forasteira")

        self.client.force_authenticate(user=self.user_motorista)
        payload = {
            "rota_id": rota_alheia.id,
            "onibus_id": self.onibus.id,
            "sentido": SentidoViagem.IDA
        }

        response = self.client.post('/api/operacao/viagem/iniciar/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkin_optico_qrcode_aluno_sucesso_e_antifraude(self):
        """
        Aluno escaneia o QR Code do ônibus da viagem ativa.
        Registra o embarque e barra tentativa subsequente de duplicidade (anti-fraude).
        """
        # Inicia viagem para o ônibus
        viagem = Viagem.objects.create(
            rota=self.rota,
            onibus=self.onibus,
            motorista=self.motorista,
            sentido=SentidoViagem.IDA,
            status=StatusViagem.EM_ANDAMENTO,
            data=date.today(),
            hora_inicio=timezone.now()
        )

        self.client.force_authenticate(user=self.user_aluno)
        payload = {"qr_code_uuid": str(self.onibus.qr_code_uuid)}

        # 1. Primeiro check-in: Sucesso (201 Created)
        resp_1 = self.client.post('/api/operacao/embarque/qrcode/', payload, format='json')
        self.assertEqual(resp_1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp_1.data['metodo_validacao'], MetodoValidacao.QR_CODE_APP)

        # 2. Tentativa duplicada: Anti-fraude bloqueia (400 Bad Request)
        resp_2 = self.client.post('/api/operacao/embarque/qrcode/', payload, format='json')
        self.assertEqual(resp_2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("erro", resp_2.data)

        # Comprova que só há 1 registro no banco
        self.assertEqual(Embarque.objects.filter(viagem=viagem, aluno=self.aluno).count(), 1)

    def test_checkin_manual_motorista_sucesso_e_antifraude(self):
        """
        Motorista efetua check-in manual de aluno.
        Garante bloqueio em caso de reenvio para a mesma viagem.
        """
        viagem = Viagem.objects.create(
            rota=self.rota,
            onibus=self.onibus,
            motorista=self.motorista,
            sentido=SentidoViagem.VOLTA,
            status=StatusViagem.EM_ANDAMENTO,
            data=date.today(),
            hora_inicio=timezone.now()
        )

        self.client.force_authenticate(user=self.user_motorista)
        payload = {"viagem_id": viagem.id, "aluno_id": self.aluno.id}

        # 1. Primeiro check-in manual: Sucesso
        resp_1 = self.client.post('/api/operacao/embarque/manual/', payload, format='json')
        self.assertEqual(resp_1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp_1.data['metodo_validacao'], MetodoValidacao.MANUAL_MOTORISTA)

        # 2. Reenvio: Anti-fraude
        resp_2 = self.client.post('/api/operacao/embarque/manual/', payload, format='json')
        self.assertEqual(resp_2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dashboard_motorista_agregacoes_em_tempo_real(self):
        """
        Dashboard em tempo real: valida contagem agregada de alunos previstos
        e embarcados sem download de listas (agent.md 2.5).
        """
        hoje = date.today()
        # Registra previsão positiva do aluno na IDA
        PrevisaoViagem.objects.create(
            aluno=self.aluno,
            data=hoje,
            vai_ida=True,
            vai_volta=False
        )

        viagem = Viagem.objects.create(
            rota=self.rota,
            onibus=self.onibus,
            motorista=self.motorista,
            sentido=SentidoViagem.IDA,
            status=StatusViagem.EM_ANDAMENTO,
            data=hoje,
            hora_inicio=timezone.now()
        )

        # Registra embarque
        Embarque.objects.create(
            viagem=viagem,
            aluno=self.aluno,
            metodo_validacao=MetodoValidacao.QR_CODE_APP
        )

        self.client.force_authenticate(user=self.user_motorista)
        url_dashboard = f'/api/operacao/viagem/{viagem.id}/dashboard/'

        response = self.client.get(url_dashboard)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Asserções de Agregação
        self.assertEqual(response.data['total_previstos'], 1)
        self.assertEqual(response.data['total_embarcados'], 1)
        self.assertEqual(response.data['capacidade_onibus'], 44)
        self.assertEqual(response.data['vagas_restantes'], 43)
        self.assertAlmostEqual(response.data['percentual_ocupacao'], round((1 / 44) * 100, 1), places=1)

    def test_conclusao_de_viagem_e_bloqueio_embarque_posterior(self):
        """Conclusão da viagem pelo motorista encerra o ciclo e impede novos embarques."""
        viagem = Viagem.objects.create(
            rota=self.rota,
            onibus=self.onibus,
            motorista=self.motorista,
            sentido=SentidoViagem.IDA,
            status=StatusViagem.EM_ANDAMENTO,
            data=date.today(),
            hora_inicio=timezone.now()
        )

        self.client.force_authenticate(user=self.user_motorista)
        url_concluir = f'/api/operacao/viagem/{viagem.id}/concluir/'

        response = self.client.post(url_concluir)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], StatusViagem.CONCLUIDA)

        # Tentativa de embarque em viagem já concluída é bloqueada
        self.client.force_authenticate(user=self.user_aluno)
        payload = {"qr_code_uuid": str(self.onibus.qr_code_uuid)}
        resp_embarque = self.client.post('/api/operacao/embarque/qrcode/', payload, format='json')
        self.assertEqual(resp_embarque.status_code, status.HTTP_400_BAD_REQUEST)

