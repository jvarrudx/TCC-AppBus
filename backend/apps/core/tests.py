"""
Automated Tests for Authentication, Student Onboarding, Party/Role, and LGPD.
Includes specific security audit tests:
1. Anti-Spoofing of IP and User-Agent in consent proof (LGPD).
2. Password hashing verification (no plaintext passwords).
3. Transaction atomicity (zero orphan records on failure).
"""

from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import (
    UsuarioAuth,
    Pessoa,
    Cliente,
    Instituicao,
    Aluno,
    Administrador,
    Documento_Legal,
    Registro_Consentimento,
    TipoStatusAprovacao,
    TipoDocumentoLegal,
    ModeloVeiculo,
    Onibus,
    Rota,
)


class AlunoOnboardingTestCase(TestCase):
    """Testes de Onboarding de Aluno, Party/Role, Multi-tenancy e LGPD."""

    def setUp(self):
        self.client = APIClient()

        # Criação do Tenant (Prefeitura / Cliente)
        self.cliente = Cliente.objects.create(
            cnpj="12.345.678/0001-90",
            razao_social="Prefeitura Municipal de Teste",
            nome_fantasia="Prefeitura de Teste",
            ativo=True
        )

        # Criação da Instituição de Ensino
        self.instituicao = Instituicao.objects.create(
            cliente=self.cliente,
            nome="Universidade Estadual de Teste",
            sigla="UET",
            ativo=True
        )

        # Criação do Documento Legal vigente
        self.documento = Documento_Legal.objects.create(
            tipo=TipoDocumentoLegal.TERMOS_DE_USO,
            versao="1.0-2026",
            conteudo="Termos de Uso e Política de Privacidade do AppBus.",
            ativo=True
        )

        self.url_registro = reverse('aluno_registro')
        self.url_token = reverse('token_obtain_pair')

    def test_onboarding_aluno_maior_idade_sucesso(self):
        """Valida onboarding atômico com sucesso para titular maior de 18 anos."""
        payload = {
            "email": "aluno.maior@universidade.edu.br",
            "password": "SenhaSegura123!",
            "nome": "João da Silva Sauro",
            "cpf": "123.456.789-00",
            "data_nascimento": "2000-05-15",
            "cliente_id": self.cliente.id,
            "instituicao_id": self.instituicao.id,
            "matricula": "20261001",
            "termo_aceito": True,
            "documento_legal_id": self.documento.id
        }

        response = self.client.post(self.url_registro, payload, format='json', HTTP_USER_AGENT="AppBus-PWA/1.0")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("aluno", response.data)
        self.assertEqual(response.data["aluno"]["status_aprovacao"], TipoStatusAprovacao.PENDENTE)

        # 1. Validação da criação do UsuarioAuth e HASH DE SENHA
        usuario = UsuarioAuth.objects.get(email="aluno.maior@universidade.edu.br")
        self.assertTrue(usuario.check_password("SenhaSegura123!"))
        self.assertNotEqual(usuario.password, "SenhaSegura123!")  # Nunca texto puro!
        self.assertTrue(usuario.password.startswith("pbkdf2_") or usuario.password.startswith("argon2"))
        self.assertTrue(usuario.ativo)

        # 2. Validação do Party (Pessoa)
        pessoa = Pessoa.objects.get(usuario=usuario)
        self.assertEqual(pessoa.nome, "João da Silva Sauro")
        self.assertEqual(pessoa.cpf, "123.456.789-00")

        # 3. Validação do Role (Aluno)
        aluno = Aluno.objects.get(pessoa=pessoa)
        self.assertEqual(aluno.cliente, self.cliente)
        self.assertEqual(aluno.instituicao, self.instituicao)
        self.assertEqual(aluno.matricula, "20261001")
        self.assertEqual(aluno.status_aprovacao, TipoStatusAprovacao.PENDENTE)

        # 4. Validação da Prova de Consentimento LGPD (Registro_Consentimento)
        consentimento = Registro_Consentimento.objects.get(pessoa=pessoa)
        self.assertEqual(consentimento.documento, self.documento)
        self.assertTrue(consentimento.consentimento_concedido)
        self.assertEqual(consentimento.user_agent, "AppBus-PWA/1.0")
        self.assertIsNotNone(consentimento.ip_address)

        # 5. Validação de Login com claims customizadas de Multi-Tenancy
        login_payload = {
            "email": "aluno.maior@universidade.edu.br",
            "password": "SenhaSegura123!"
        }
        login_res = self.client.post(self.url_token, login_payload, format='json')
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_res.data)
        self.assertIn("refresh", login_res.data)
        self.assertEqual(login_res.data["user"]["role"], "aluno")
        self.assertEqual(login_res.data["user"]["cliente_id"], self.cliente.id)
        self.assertEqual(login_res.data["user"]["status_aprovacao"], TipoStatusAprovacao.PENDENTE)

    def test_tentativa_spoofing_ip_user_agent_ignorado(self):
        """
        Auditoria de Segurança 1:
        Valida que qualquer tentativa de forjar ip_address ou user_agent
        no corpo JSON é terminantemente ignorada, persistindo apenas os dados
        reais do cabeçalho da conexão HTTP (LGPD Anti-Spoofing).
        """
        payload = {
            "email": "auditoria.spoof@universidade.edu.br",
            "password": "SenhaSegura123!",
            "nome": "Tentativa Spoofing",
            "cpf": "100.200.300-40",
            "data_nascimento": "1998-10-10",
            "cliente_id": self.cliente.id,
            "instituicao_id": self.instituicao.id,
            "matricula": "20269999",
            "termo_aceito": True,
            # Tentativa de injeção no payload JSON:
            "ip_address": "6.6.6.6",
            "user_agent": "HackerBot/9.9"
        }

        # Requisição vindo de um IP e User-Agent legítimos da camada de rede:
        response = self.client.post(
            self.url_registro,
            payload,
            format='json',
            REMOTE_ADDR="192.168.10.50",
            HTTP_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        usuario = UsuarioAuth.objects.get(email="auditoria.spoof@universidade.edu.br")
        pessoa = Pessoa.objects.get(usuario=usuario)
        consentimento = Registro_Consentimento.objects.get(pessoa=pessoa)

        # O consentimento gravou os dados do HEADER HTTP, NUNCA o que foi passado no JSON
        self.assertEqual(consentimento.ip_address, "192.168.10.50")
        self.assertNotEqual(consentimento.ip_address, "6.6.6.6")
        self.assertEqual(consentimento.user_agent, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0")
        self.assertNotEqual(consentimento.user_agent, "HackerBot/9.9")

    def test_senha_nunca_salva_em_texto_puro(self):
        """
        Auditoria de Segurança 3:
        Valida que nenhuma senha trafegue ou seja armazenada em texto puro no banco.
        """
        payload = {
            "email": "auditoria.senha@universidade.edu.br",
            "password": "MinhaSenhaSuperSecreta2026!",
            "nome": "Auditoria de Senha",
            "cpf": "200.300.400-50",
            "data_nascimento": "2001-01-01",
            "cliente_id": self.cliente.id,
            "instituicao_id": self.instituicao.id,
            "matricula": "20268888",
            "termo_aceito": True
        }

        response = self.client.post(self.url_registro, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        usuario = UsuarioAuth.objects.get(email="auditoria.senha@universidade.edu.br")
        # Garante que o valor no banco é um hash criptográfico válido
        self.assertNotEqual(usuario.password, "MinhaSenhaSuperSecreta2026!")
        self.assertTrue(usuario.check_password("MinhaSenhaSuperSecreta2026!"))

    def test_transacao_atomica_reverte_tudo_em_falha(self):
        """
        Auditoria de Segurança 2:
        Simula uma falha inesperada na última etapa (criação do Aluno) para assegurar
        que transaction.atomic reverta 100% dos dados, não deixando UsuarioAuth nem Pessoa órfãos.
        """
        payload = {
            "email": "falha.atomica@universidade.edu.br",
            "password": "SenhaSegura123!",
            "nome": "Teste Atomicidade",
            "cpf": "300.400.500-60",
            "data_nascimento": "2002-02-02",
            "cliente_id": self.cliente.id,
            "instituicao_id": self.instituicao.id,
            "matricula": "20267777",
            "termo_aceito": True
        }

        # Mock da criação de Aluno para disparar uma exceção intencional no meio da transação
        with patch('apps.core.models.Aluno.objects.create', side_effect=RuntimeError("Falha simulada no banco")):
            with self.assertRaises(RuntimeError):
                self.client.post(self.url_registro, payload, format='json')

        # Assegura que nada foi persistido no banco (zero registros órfãos)
        self.assertFalse(UsuarioAuth.objects.filter(email="falha.atomica@universidade.edu.br").exists())
        self.assertFalse(Pessoa.objects.filter(cpf="300.400.500-60").exists())
        self.assertFalse(Registro_Consentimento.objects.filter(pessoa__nome="Teste Atomicidade").exists())

    def test_onboarding_menor_idade_sem_responsavel_falha(self):
        """Valida que menores de 18 anos são rejeitados se não informarem o CPF do responsável (LGPD)."""
        payload = {
            "email": "menor@escola.edu.br",
            "password": "SenhaSegura123!",
            "nome": "Adolescente de Menor",
            "cpf": "111.222.333-44",
            "data_nascimento": "2010-01-01",  # Menor de 18 anos
            "cliente_id": self.cliente.id,
            "instituicao_id": self.instituicao.id,
            "matricula": "20261002",
            "termo_aceito": True,
            "responsavel_legal_cpf": ""  # Ausente propositalmente
        }

        response = self.client.post(self.url_registro, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("responsavel_legal_cpf", response.data)

        # Garante atomicidade: nenhum registro deve ter sido criado
        self.assertFalse(UsuarioAuth.objects.filter(email="menor@escola.edu.br").exists())
        self.assertFalse(Pessoa.objects.filter(cpf="111.222.333-44").exists())

    def test_onboarding_menor_idade_com_responsavel_sucesso(self):
        """Valida onboarding com sucesso para menor de idade com CPF de responsável informado."""
        payload = {
            "email": "menor.valido@escola.edu.br",
            "password": "SenhaSegura123!",
            "nome": "Adolescente Estudante",
            "cpf": "999.888.777-66",
            "data_nascimento": "2010-01-01",
            "cliente_id": self.cliente.id,
            "instituicao_id": self.instituicao.id,
            "matricula": "20261003",
            "termo_aceito": True,
            "responsavel_legal_cpf": "555.444.333-22"
        }

        response = self.client.post(self.url_registro, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        usuario = UsuarioAuth.objects.get(email="menor.valido@escola.edu.br")
        pessoa = Pessoa.objects.get(usuario=usuario)
        consentimento = Registro_Consentimento.objects.get(pessoa=pessoa)
        self.assertEqual(consentimento.responsavel_legal_cpf, "555.444.333-22")

    def test_recusa_sem_consentimento_termos(self):
        """Valida que cadastro sem aceite de termos é rejeitado (LGPD Opt-in obrigatório)."""
        payload = {
            "email": "sem.termo@universidade.edu.br",
            "password": "SenhaSegura123!",
            "nome": "Candidato Sem Termo",
            "cpf": "888.777.666-55",
            "data_nascimento": "1999-01-01",
            "cliente_id": self.cliente.id,
            "instituicao_id": self.instituicao.id,
            "matricula": "20261004",
            "termo_aceito": False
        }

        response = self.client.post(self.url_registro, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("termo_aceito", response.data)


# ==============================================================================
# 2. TESTES DE ISOLAMENTO MULTI-TENANT (Etapa 2.2 - agent.md 2.1)
# ==============================================================================

class MultiTenantIsolationTestCase(TestCase):
    """
    Testes de Segurança e Isolamento Multi-Tenant (Zero Trust).
    Garante que nunca haja Data Leakage entre prefeituras e que qualquer
    tentativa de Payload Injection seja bloqueada pelo TenantBaseViewSet.
    """

    def setUp(self):
        self.client = APIClient()

        # 1. Criação dos Clientes (Prefeituras A e B)
        self.prefeitura_a = Cliente.objects.create(
            cnpj="11.111.111/0001-11",
            razao_social="Prefeitura Municipal Alfa",
            nome_fantasia="Prefeitura Alfa",
            ativo=True
        )
        self.prefeitura_b = Cliente.objects.create(
            cnpj="22.222.222/0001-22",
            razao_social="Prefeitura Municipal Beta",
            nome_fantasia="Prefeitura Beta",
            ativo=True
        )

        # 2. Modelo de Veículo Global (Catálogo)
        self.modelo_veiculo = ModeloVeiculo.objects.create(
            marca="Marcopolo",
            nome="Viaggio 1050",
            ativo=True
        )

        # 3. Administrador Municipal da Prefeitura Alfa
        self.user_admin_a = UsuarioAuth.objects.create_user(
            email="admin@prefeitura-alfa.sp.gov.br",
            password="SenhaSegura123!",
            is_staff=True
        )
        self.pessoa_admin_a = Pessoa.objects.create(
            usuario=self.user_admin_a,
            nome="Gestor Alfa",
            cpf="111.111.111-11",
            data_nascimento="1980-01-01"
        )
        self.admin_alfa = Administrador.objects.create(
            pessoa=self.pessoa_admin_a,
            cliente=self.prefeitura_a,
            cargo="Secretário de Transporte",
            ativo=True
        )

        # 4. Administrador Municipal da Prefeitura Beta
        self.user_admin_b = UsuarioAuth.objects.create_user(
            email="admin@prefeitura-beta.sp.gov.br",
            password="SenhaSegura123!",
            is_staff=True
        )
        self.pessoa_admin_b = Pessoa.objects.create(
            usuario=self.user_admin_b,
            nome="Gestor Beta",
            cpf="222.222.222-22",
            data_nascimento="1985-05-05"
        )
        self.admin_beta = Administrador.objects.create(
            pessoa=self.pessoa_admin_b,
            cliente=self.prefeitura_b,
            cargo="Coordenador de Frotas",
            ativo=True
        )

        # 5. Veículos das Prefeituras A e B
        self.onibus_a = Onibus.objects.create(
            cliente=self.prefeitura_a,
            modelo=self.modelo_veiculo,
            placa="ALF-1001",
            capacidade=44,
            ativo=True
        )
        self.onibus_b = Onibus.objects.create(
            cliente=self.prefeitura_b,
            modelo=self.modelo_veiculo,
            placa="BET-2002",
            capacidade=50,
            ativo=True
        )

        self.url_onibus_list = "/api/veiculos/onibus/"
        self.url_onibus_detail_a = f"/api/veiculos/onibus/{self.onibus_a.id}/"
        self.url_onibus_detail_b = f"/api/veiculos/onibus/{self.onibus_b.id}/"

    def test_bloqueio_requisicao_anonima(self):
        """Zero Trust: Endpoints com escopo de tenant exigem autenticação obrigatória."""
        response = self.client.get(self.url_onibus_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_isolamento_leitura_nao_vaza_dados_outro_tenant(self):
        """
        Isolamento Multi-tenant (agent.md 2.1):
        O gestor da Prefeitura Alfa NUNCA deve receber ônibus da Prefeitura Beta no get_queryset.
        """
        self.client.force_authenticate(user=self.user_admin_a)
        response = self.client.get(self.url_onibus_list)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # O resultado deve conter exclusivamente o ônibus da Prefeitura Alfa
        placas_retornadas = [item["placa"] for item in response.data]
        self.assertIn("ALF-1001", placas_retornadas)
        self.assertNotIn("BET-2002", placas_retornadas)

    def test_tentativa_acesso_direto_id_outro_tenant_retorna_404(self):
        """
        Segurança anti-enumeração:
        Tentar acessar diretamente por ID um registro de outra prefeitura retorna 404 (Not Found).
        """
        self.client.force_authenticate(user=self.user_admin_a)
        # Gestor Alfa tentando consultar o Ônibus da Prefeitura Beta
        response = self.client.get(self.url_onibus_detail_b)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_prevencao_payload_injection_cliente_id_no_post(self):
        """
        Blindagem de Escrita (agent.md 2.1):
        Mesmo que o JSON contenha 'cliente_id' da Prefeitura Beta, o backend
        injetará forçosamente a Prefeitura Alfa do usuário autenticado no perform_create.
        """
        self.client.force_authenticate(user=self.user_admin_a)

        payload_malicioso = {
            "modelo": self.modelo_veiculo.id,
            "placa": "INJ-9999",
            "capacidade": 42,
            # Tentativa de injeção: Forçar criação na Prefeitura Beta
            "cliente_id": self.prefeitura_b.id
        }

        response = self.client.post(self.url_onibus_list, payload_malicioso, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        novo_onibus = Onibus.objects.get(placa="INJ-9999")
        # O ônibus DEVE pertencer à Prefeitura Alfa (usuário logado) e NÃO à Prefeitura Beta
        self.assertEqual(novo_onibus.cliente, self.prefeitura_a)
        self.assertNotEqual(novo_onibus.cliente, self.prefeitura_b)

    def test_prevencao_troca_tenant_no_patch(self):
        """
        Imutabilidade de Tenant:
        Tentar reatribuir um ônibus existente para outra prefeitura via PATCH é ignorado.
        """
        self.client.force_authenticate(user=self.user_admin_a)

        response = self.client.patch(
            self.url_onibus_detail_a,
            {"cliente_id": self.prefeitura_b.id, "capacidade": 46},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.onibus_a.refresh_from_db()
        self.assertEqual(self.onibus_a.capacidade, 46)
        # Permanece com o tenant da Prefeitura Alfa
        self.assertEqual(self.onibus_a.cliente, self.prefeitura_a)

    def test_usuario_sem_tenant_acesso_negado(self):
        """Usuário autenticado mas sem vínculo a nenhuma prefeitura tem acesso negado (403)."""
        usuario_sem_role = UsuarioAuth.objects.create_user(
            email="sem.tenant@teste.com",
            password="SenhaSegura123!"
        )
        self.client.force_authenticate(user=usuario_sem_role)

        response = self.client.get(self.url_onibus_list)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

