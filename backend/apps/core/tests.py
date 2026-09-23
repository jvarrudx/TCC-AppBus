"""
Automated Tests for Authentication, Student Onboarding, Party/Role, and LGPD.
"""

from datetime import date
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
    Documento_Legal,
    Registro_Consentimento,
    TipoStatusAprovacao,
    TipoDocumentoLegal,
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

        # 1. Validação da criação do UsuarioAuth
        usuario = UsuarioAuth.objects.get(email="aluno.maior@universidade.edu.br")
        self.assertTrue(usuario.check_password("SenhaSegura123!"))
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
