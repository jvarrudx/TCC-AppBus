# 🚌 AppBus — Sistema PWA para Gestão do Transporte Universitário Intermunicipal

> **Trabalho de Conclusão de Curso (TCC)** — Bacharelado em Sistemas de Informação  
> **Instituição:** Universidade do Estado de Minas Gerais (UEMG) – Unidade Passos (2026)  
> **Autores:** João Victor Costa Arruda · Roberto Henrique Duarte  
> **Orientador:** Prof. Eduardo Henrique Marques Ferreira

O **AppBus** é uma aplicação web progressiva (**PWA — *Progressive Web App***) integrada a uma **API RESTful** voltada para a gestão do transporte universitário intermunicipal. O sistema permite estimar a ocupação diária dos veículos antes da partida, organizar a prioridade de retorno dos estudantes, validar embarques por **QR Code** (com contingência manual e operação *offline-first* no **Modo Rodovia**) e assegurar a conformidade nativa com a **LGPD** (*Lei nº 13.709/2018*) em arquitetura **Multi-Tenant**.

---

## 📋 Sumário

1. [Principais Funcionalidades](#-principais-funcionalidades)
2. [Arquitetura e Stack Tecnológica](#-arquitetura-e-stack-tecnológica)
3. [Estrutura do Repositório](#-estrutura-do-repositório)
4. [Pré-requisitos](#-pré-requisitos)
5. [Passo a Passo para Rodar o Projeto (Docker — Recomendado)](#-passo-a-passo-para-rodar-o-projeto-docker--recomendado)
6. [Roteiro de Validação para a Banca Avaliadora](#-roteiro-de-validação-para-a-banca-avaliadora)
7. [Executando a Suíte de Testes Automatizados](#-executando-a-suíte-de-testes-automatizados)
8. [Execução Alternativa (Modo Desenvolvimento / Sem Docker)](#-execução-alternativa-modo-desenvolvimento--sem-docker)
9. [Comandos Úteis e Solução de Problemas (Troubleshooting)](#-comandos-úteis-e-solução-de-problemas-troubleshooting)

---

## ✨ Principais Funcionalidades

- **Estimativa de Ocupação (*"Vou / Não vou"*):** Estudantes sinalizam com um toque a intenção de viagem para **Ida** e **Volta**, gerando previsão de lotação antes da partida.
- **Prioridade de Ciclo e Fila de Espera:** Quem confirmou ou embarcou na ida recebe prioridade assegurada no retorno (`GARANTIDA`), seguido por ordem cronológica (`CONFIRMADA`) e fila transparente (`FILA_ESPERA #N`).
- **Embarque Óptico via QR Code:** Cada ônibus possui um cartaz A4 com QR Code único (`qr_code_uuid`); o estudante realiza o *check-in* pela câmera do celular (com suporte à lanterna) sob bloqueio pessimista **MVCC** (`select_for_update`), impedindo superlotação e duplo embarque.
- **Painel do Motorista e *Modo Rodovia* (*Offline-First*):** KPIs em tempo real, embarque manual de contingência (com CPF mascarado) e fila local persistida via Workbox + `localStorage` para continuar operando em trechos de rodovia sem sinal 4G, com sincronização automática na reconexão.
- **Mural de Avisos com *Quick Replies*:** Canal oficial que substitui grupos informais de mensagens, permitindo ao motorista disparar alertas padronizados com 1 toque.
- **Gestão Municipal Multi-Tenant:** Isolamento estrito por município (`cliente_id`), fila auditável de aprovação de estudantes (`PENDENTE` / `APROVADO` / `REJEITADO`), cadastro de frota/rotas e emissão do cartaz A4 do QR Code.
- **Conformidade LGPD (*Privacy by Design*):** Coleta mínima de dados, prova imutável de consentimento no servidor (versão do termo, timestamp, IP e *User-Agent*), exigência condicional de CPF do responsável legal para menores de 18 anos e anonimização irreversível (`Pessoa.anonimizar()`) sem *hard deletes*, preservando estatísticas públicas.
- **Sessão Segura (Zero Disk Storage):** `access_token` mantido exclusivamente em memória RAM (Pinia) e `refresh_token` rotativo em Cookie `HttpOnly` com *blacklist* no logout.

---

## 🏗️ Arquitetura e Stack Tecnológica

O ambiente é orquestrado via **Docker Compose** em **4 contêineres**:

| Serviço (`docker-compose`) | Contêiner | Tecnologia | Porta | Papel |
| :--- | :--- | :--- | :---: | :--- |
| **`db`** | `appbus_db` | PostgreSQL 15 Alpine | `5432` | Banco relacional ACID com controle de concorrência MVCC |
| **`web`** | `appbus_backend` | Python 3.11 · Django · DRF · SimpleJWT | `8000` | API RESTful, regras de negócio, RBAC, Multi-tenancy e LGPD |
| **`frontend`** | `appbus_frontend` | Node 20 · Vue 3 · Quasar 2 · Vite · Workbox | `5173` | Interface PWA *mobile-first* servida em **HTTPS** |
| **`tunnel`** | `appbus_tunnel` | Cloudflare Tunnel (`cloudflared`) | — | Túnel HTTPS público (`*.trycloudflare.com`) para testar câmera/PWA no celular |

---

## 📁 Estrutura do Repositório

```text
TCC-AppBus/
├── backend/                     # API RESTful em Django + DRF
│   ├── appbus/                  # Configurações principais (settings.py, urls.py)
│   ├── apps/core/               # Modelos (21 entidades), views, serializers, permissões e 50 testes
│   ├── Dockerfile
│   ├── manage.py
│   └── requirements.txt
├── frontend/                    # Aplicação PWA em Vue 3 + Quasar 2 + Vite
│   ├── public/                  # Ícones e manifestos estáticos do PWA
│   ├── src/
│   │   ├── boot/                # Configuração Axios + refresh automático via Cookie HttpOnly
│   │   ├── pages/               # Telas de Aluno, Motorista, Gestor, Mural, Login e Registro
│   │   ├── router/              # Rotas e guardas RBAC por perfil
│   │   └── stores/              # Estado global (Pinia)
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js           # Configuração Vite, HTTPS (basicSsl), proxy /api e Workbox PWA
├── prints_tcc/                  # Diagramas (Casos de Uso, DER, Contêineres) e capturas de tela
├── .env.example                 # Modelo de variáveis de ambiente
├── docker-compose.yml           # Orquestração dos 4 serviços (db, web, frontend, tunnel)
└── README.md
```

---

## 🔧 Pré-requisitos

Para executar o projeto pelo método recomendado (**Docker**), você precisará apenas de:

- **[Git](https://git-scm.com/downloads)**
- **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** (Windows / macOS) ou **Docker Engine + Docker Compose v2** (Linux)

> [!TIP]
> Verifique se o Docker está ativo antes de começar executando `docker --version` e `docker compose version` no terminal.

---

## 🚀 Passo a Passo para Rodar o Projeto (Docker — Recomendado)

Siga os passos na ordem abaixo a partir do seu terminal (**PowerShell** no Windows ou **Bash/Zsh** no Linux/macOS).

### Passo 1 — Clonar o repositório

```bash
git clone https://github.com/jvarrudx/TCC-AppBus.git
cd TCC-AppBus
```

### Passo 2 — Criar o arquivo de variáveis de ambiente (`.env`)

Copie o arquivo de exemplo `.env.example` para `.env`:

**No Linux / macOS:**
```bash
cp .env.example .env
```

**No Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

Abra o arquivo `.env` gerado e confira os valores (para avaliação local, basta definir uma senha e uma chave secreta):

```env
# PostgreSQL Configuration
POSTGRES_DB=appbus_db
POSTGRES_USER=appbus_user
POSTGRES_PASSWORD=appbus_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Django Configuration
DJANGO_SECRET_KEY=chave-secreta-local-appbus-tcc-2026
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,web,backend

# CORS Configuration
CORS_ALLOWED_ORIGINS=https://localhost:5173,http://localhost:5173,https://127.0.0.1:5173,http://127.0.0.1:5173
```

> [!NOTE]
> O `CORS_ALLOWED_ORIGINS` inclui `https://localhost:5173` porque o frontend utiliza HTTPS (via `@vitejs/plugin-basic-ssl`) para liberar o Service Worker do PWA e a API da câmera do leitor de QR Code.

### Passo 3 — Construir as imagens, gerar o build do PWA e subir os contêineres

Como a pasta `frontend/dist/` não é versionada no Git e o contêiner `frontend` serve o PWA compilado (`npm run preview`), execute os 3 comandos abaixo na primeira inicialização:

```bash
# 1. Constrói as imagens do backend e do frontend
docker compose build

# 2. Gera o build de produção do PWA (cria frontend/dist com Service Worker Workbox)
docker compose run --rm frontend npm run build

# 3. Sobe todos os 4 serviços em segundo plano
docker compose up -d
```

Verifique se todos os contêineres estão ativos (`Up` / `healthy`):

```bash
docker compose ps
```

### Passo 4 — Aplicar as migrações do banco de dados

Execute as migrações do Django no PostgreSQL 15:

```bash
docker compose exec web python manage.py migrate
```

Para confirmar que a API e o banco de dados estão saudáveis, acesse no navegador (ou via `curl`):

- `http://localhost:8000/api/health/` — deve retornar HTTP `200 OK`.

### Passo 5 — Popular dados iniciais de demonstração (para testar os 3 perfis)

Como o banco inicia vazio, você pode escolher **uma das duas opções** abaixo:

#### Opção A — Carga rápida automatizada (Recomendada para a Banca)

O comando abaixo cria, de forma idempotente, um cenário completo pronto para testes: **1 Prefeitura (Tenant)**, **1 Instituição (UEMG Passos)**, **Documentos Legais LGPD vigentes**, **1 Modelo de Veículo**, **1 Ônibus com QR Code**, **1 Rota** e **3 usuários prontos para login** (Gestor, Motorista e Estudante aprovado).

**No Linux / macOS:**
```bash
docker compose exec -T web python manage.py shell << 'EOF'
from datetime import date
from apps.core.models import (
    Cliente, Instituicao, Documento_Legal, TipoDocumentoLegal,
    UsuarioAuth, Pessoa, Administrador, Motorista, Aluno,
    TipoStatusAprovacao, ModeloVeiculo, Onibus, Rota, RotaInstituicao
)

cliente, _ = Cliente.objects.get_or_create(
    cnpj="18.241.778/0001-58",
    defaults={"razao_social": "Prefeitura Municipal de Demonstração", "nome_fantasia": "Prefeitura Demo (AppBus)", "ativo": True}
)
instituicao, _ = Instituicao.objects.get_or_create(
    cliente=cliente, nome="Universidade do Estado de Minas Gerais",
    defaults={"sigla": "UEMG Passos", "ativo": True}
)
Documento_Legal.objects.get_or_create(
    tipo=TipoDocumentoLegal.TERMOS_DE_USO, versao="1.0",
    defaults={"conteudo": "Termos de Uso vigentes do sistema AppBus.", "ativo": True}
)
Documento_Legal.objects.get_or_create(
    tipo=TipoDocumentoLegal.POLITICA_PRIVACIDADE, versao="1.0",
    defaults={"conteudo": "Política de Privacidade e Proteção de Dados (LGPD) do AppBus.", "ativo": True}
)
modelo, _ = ModeloVeiculo.objects.get_or_create(marca="Marcopolo", nome="Viaggio 1050", defaults={"ativo": True})
onibus, _ = Onibus.objects.get_or_create(
    placa="ABC-1D23", defaults={"cliente": cliente, "modelo": modelo, "capacidade": 44, "ativo": True}
)
rota, _ = Rota.objects.get_or_create(cliente=cliente, nome="Rota Noturna — Centro x UEMG Passos", defaults={"ativo": True})
RotaInstituicao.objects.get_or_create(rota=rota, instituicao=instituicao, defaults={"ordem_parada": 1})

def criar_usuario(email, senha, nome, cpf, nasc, is_staff=False, is_super=False):
    u, created = UsuarioAuth.objects.get_or_create(email=email, defaults={"is_staff": is_staff, "is_superuser": is_super, "ativo": True})
    if created:
        u.set_password(senha)
        u.save()
    p, _ = Pessoa.objects.get_or_create(usuario=u, defaults={"nome": nome, "cpf": cpf, "data_nascimento": nasc})
    return u, p

_, p_admin = criar_usuario("gestor@appbus.local", "AppBus@2026", "Carlos Gestor Municipal", "111.111.111-11", date(1985, 5, 10), True, True)
Administrador.objects.get_or_create(pessoa=p_admin, defaults={"cliente": cliente, "cargo": "Coordenador de Transporte", "ativo": True})

_, p_mot = criar_usuario("motorista@appbus.local", "AppBus@2026", "José Motorista", "222.222.222-22", date(1980, 3, 20))
Motorista.objects.get_or_create(pessoa=p_mot, defaults={"cliente": cliente, "cnh": "12345678901", "categoria_cnh": "D", "ativo": True})

_, p_alu = criar_usuario("aluno@appbus.local", "AppBus@2026", "Ana Estudante UEMG", "333.333.333-33", date(2003, 8, 15))
Aluno.objects.get_or_create(
    pessoa=p_alu,
    defaults={"cliente": cliente, "instituicao": instituicao, "matricula": "20260001", "status_aprovacao": TipoStatusAprovacao.APROVADO}
)
print("Ambiente de demonstração AppBus criado com sucesso!")
EOF
```

**No Windows (PowerShell):**
```powershell
@'
from datetime import date
from apps.core.models import (
    Cliente, Instituicao, Documento_Legal, TipoDocumentoLegal,
    UsuarioAuth, Pessoa, Administrador, Motorista, Aluno,
    TipoStatusAprovacao, ModeloVeiculo, Onibus, Rota, RotaInstituicao
)

cliente, _ = Cliente.objects.get_or_create(
    cnpj="18.241.778/0001-58",
    defaults={"razao_social": "Prefeitura Municipal de Demonstração", "nome_fantasia": "Prefeitura Demo (AppBus)", "ativo": True}
)
instituicao, _ = Instituicao.objects.get_or_create(
    cliente=cliente, nome="Universidade do Estado de Minas Gerais",
    defaults={"sigla": "UEMG Passos", "ativo": True}
)
Documento_Legal.objects.get_or_create(
    tipo=TipoDocumentoLegal.TERMOS_DE_USO, versao="1.0",
    defaults={"conteudo": "Termos de Uso vigentes do sistema AppBus.", "ativo": True}
)
Documento_Legal.objects.get_or_create(
    tipo=TipoDocumentoLegal.POLITICA_PRIVACIDADE, versao="1.0",
    defaults={"conteudo": "Política de Privacidade e Proteção de Dados (LGPD) do AppBus.", "ativo": True}
)
modelo, _ = ModeloVeiculo.objects.get_or_create(marca="Marcopolo", nome="Viaggio 1050", defaults={"ativo": True})
onibus, _ = Onibus.objects.get_or_create(
    placa="ABC-1D23", defaults={"cliente": cliente, "modelo": modelo, "capacidade": 44, "ativo": True}
)
rota, _ = Rota.objects.get_or_create(cliente=cliente, nome="Rota Noturna — Centro x UEMG Passos", defaults={"ativo": True})
RotaInstituicao.objects.get_or_create(rota=rota, instituicao=instituicao, defaults={"ordem_parada": 1})

def criar_usuario(email, senha, nome, cpf, nasc, is_staff=False, is_super=False):
    u, created = UsuarioAuth.objects.get_or_create(email=email, defaults={"is_staff": is_staff, "is_superuser": is_super, "ativo": True})
    if created:
        u.set_password(senha)
        u.save()
    p, _ = Pessoa.objects.get_or_create(usuario=u, defaults={"nome": nome, "cpf": cpf, "data_nascimento": nasc})
    return u, p

_, p_admin = criar_usuario("gestor@appbus.local", "AppBus@2026", "Carlos Gestor Municipal", "111.111.111-11", date(1985, 5, 10), True, True)
Administrador.objects.get_or_create(pessoa=p_admin, defaults={"cliente": cliente, "cargo": "Coordenador de Transporte", "ativo": True})

_, p_mot = criar_usuario("motorista@appbus.local", "AppBus@2026", "José Motorista", "222.222.222-22", date(1980, 3, 20))
Motorista.objects.get_or_create(pessoa=p_mot, defaults={"cliente": cliente, "cnh": "12345678901", "categoria_cnh": "D", "ativo": True})

_, p_alu = criar_usuario("aluno@appbus.local", "AppBus@2026", "Ana Estudante UEMG", "333.333.333-33", date(2003, 8, 15))
Aluno.objects.get_or_create(
    pessoa=p_alu,
    defaults={"cliente": cliente, "instituicao": instituicao, "matricula": "20260001", "status_aprovacao": TipoStatusAprovacao.APROVADO}
)
print("Ambiente de demonstração AppBus criado com sucesso!")
'@ | docker compose exec -T web python manage.py shell
```

Credenciais criadas pela carga rápida:

| Perfil | E-mail | Senha | Acesso |
| :--- | :--- | :--- | :--- |
| **Gestor Municipal (+ Django Admin)** | `gestor@appbus.local` | `AppBus@2026` | AppBus (`/admin/*`) e Django Admin (`/admin/`) |
| **Motorista** | `motorista@appbus.local` | `AppBus@2026` | Painel Operacional (`/motorista`) e Mural (`/mural`) |
| **Estudante (Aprovado)** | `aluno@appbus.local` | `AppBus@2026` | Painel do Aluno (`/`), Leitor QR e Perfil LGPD |

#### Opção B — Criação manual via Django Admin

Caso prefira criar apenas um superusuário e cadastrar os registros manualmente:

```bash
docker compose exec web python manage.py createsuperuser
```

Depois, acesse `http://localhost:8000/admin/` e cadastre: `Cliente`, `Instituicao`, `Documento_Legal` (ativos), `ModeloVeiculo`, `Pessoa` e o vínculo em `Administrador`.

### Passo 6 — Acessar a Aplicação

| Serviço | Endereço | Observação |
| :--- | :--- | :--- |
| **AppBus PWA (Local)** | **`https://localhost:5173`** | Use **`https://`** (não `http://`) |
| **Django Admin** | `http://localhost:8000/admin/` | Painel técnico do backend |
| **Healthcheck da API** | `http://localhost:8000/api/health/` | Status da API e conexão com o PostgreSQL |

> [!IMPORTANT]
> **Aviso de certificado SSL no acesso local (`https://localhost:5173`):**  
> Como o ambiente local gera um certificado SSL autoassinado para permitir o uso da câmera e do PWA em `localhost`, o navegador exibirá o aviso *"Sua conexão não é particular"*. Clique em **"Avançado"** → **"Ir para localhost (não seguro)"** para abrir normalmente.

#### 📱 Testando no Smartphone (Câmera QR Code + Instalação PWA)

O contêiner `tunnel` (Cloudflare Tunnel) gera automaticamente um endereço **HTTPS válido** (sem aviso de certificado) apontando para o AppBus local. Para obter o link:

```bash
docker compose logs tunnel
```

Procure no log por uma URL no formato `https://xxxx-xxxx.trycloudflare.com` e abra diretamente no navegador do celular (Chrome/Safari) para testar a leitura real de QR Code e a instalação na tela inicial ("Adicionar à tela inicial").

---

## 🧪 Roteiro de Usos

Com o ambiente rodando e os dados da **Opção A** carregados, sugerimos o roteiro abaixo (cerca de 5 minutos) para explorar todos os requisitos centrais do TCC:

1. **Auto-Cadastro e LGPD (`/registro`):**
   - Na tela de login, clique em **"Solicitar Acesso / Cadastrar"**.
   - Preencha um novo aluno e teste uma data de nascimento de **menor de 18 anos**: observe a exibição automática do campo obrigatório **CPF do Responsável Legal** (Art. 14 da LGPD) e os **Termos de Uso / Política de Privacidade** vigentes.
2. **Gestor Municipal (`gestor@appbus.local`):**
   - Acesse **Fila de Aprovação** (`/admin/aprovacoes`) para aprovar ou rejeitar o aluno recém-cadastrado.
   - Acesse **Gestão de Frota e Rotas** (`/admin/frota`) para visualizar/cadastrar ônibus, motoristas e rotas.
   - Acesse **Emissão de QR Code** (`/admin/qrcode`) para visualizar e imprimir/exportar o **Cartaz A4** do ônibus `ABC-1D23`.
3. **Estudante (`aluno@appbus.local`):**
   - Na tela inicial (`/`), alterne os botões **"Vou na Ida"** e **"Volto no Ônibus"** e observe o cálculo imediato da **Prioridade de Ciclo** (`GARANTIDA` / `CONFIRMADA` / `FILA_ESPERA`).
   - Acesse **Embarque Óptico** (`/aluno/qrcode`) para abrir o leitor de QR Code com opção de lanterna.
   - Acesse **Perfil & Privacidade** (`/aluno/perfil`) para conferir os consentimentos LGPD e o fluxo de solicitação de exclusão/anonimização.
4. **Motorista (`motorista@appbus.local`) e *Modo Rodovia*:**
   - Em **Painel do Motorista** (`/motorista`), inicie uma viagem selecionando a rota e o ônibus `ABC-1D23`.
   - Acompanhe os 4 KPIs (*Previstos*, *Embarcados*, *Vagas Livres* e *Ocupação %*) e teste o **embarque manual de contingência** (buscando pelo nome do aluno, com CPF mascarado).
   - *(Teste do Modo Rodovia)* Abra o **DevTools do navegador (`F12`) → aba Network → marque "Offline"**, realize um embarque manual offline e depois desmarque "Offline" para observar a sincronização automática da fila local.
   - Acesse o **Mural de Avisos** (`/mural`) e dispare um comunicado via **Quick Replies** (1 toque).

---

## ✅ Executando a Suíte de Testes Automatizados

O backend possui **50 testes automatizados** distribuídos em **11 suítes** (`backend/apps/core/tests.py`), executados diretamente contra o **PostgreSQL 15 real** em contêiner (validando inclusive o bloqueio pessimista **MVCC** sob concorrência multithread com `ThreadPoolExecutor`):

```bash
docker compose exec web python manage.py test apps.core --verbosity=2
```

**Cenários verificados pela suíte:**
- **Segurança & Multi-Tenancy:** Isolamento entre prefeituras (`cliente_id`), retorno `404` em acesso cruzado por ID, Zero-Trust RBAC (`401`/`403`) e autenticação por Cookie `HttpOnly`.
- **Governança LGPD:** Atomicidade do cadastro em múltiplas tabelas, anti-*spoofing* de IP/*User-Agent*, proteção para menores de 18 anos e anonimização irreversível (`Pessoa.anonimizar()`) preservando o histórico de `Embarque`.
- **Operação & Comunicação:** Intenção *"Vou/Não vou"*, Prioridade de Ciclo, Fila de Espera, QR Code, *check-in* manual e Mural de Avisos.
- **Estresse de Concorrência (MVCC):** 8 threads disputando simultaneamente 3 vagas restantes e 5 cliques duplicados simultâneos (*double-tap*), garantindo zero superlotação e zero duplo *check-in*.

---

## 💻 Execução Alternativa (Modo Desenvolvimento / Sem Docker)

Caso deseje rodar o projeto diretamente na máquina hospedeira (sem Docker), certifique-se de ter **Python 3.11+**, **Node.js 20+** e **PostgreSQL 15** instalados:

1. **Banco de Dados:** Crie o banco `appbus_db` e o usuário `appbus_user` no PostgreSQL local e altere `POSTGRES_HOST=localhost` no arquivo `.env`.
2. **Backend (Django):**
   ```bash
   cd backend
   python -m venv .venv
   # Ative o ambiente virtual:
   # Linux/macOS: source .venv/bin/activate
   # Windows (PowerShell): .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver 0.0.0.0:8000
   ```
3. **Frontend (Vue/Quasar):**
   - Em `frontend/vite.config.js`, ajuste temporariamente o proxy `/api` de `http://web:8000` para `http://localhost:8000`.
   - Execute:
     ```bash
     cd frontend
     npm install
     npm run dev -- --host
     ```
   - Acesse `https://localhost:5173`.

---

## 🛠️ Comandos Úteis e Solução de Problemas (Troubleshooting)

### Comandos úteis do Docker Compose

| Ação | Comando |
| :--- | :--- |
| Ver logs em tempo real (todos os serviços) | `docker compose logs -f` |
| Ver logs apenas do backend ou do túnel HTTPS | `docker compose logs -f web` / `docker compose logs tunnel` |
| Parar os contêineres (mantendo os dados do banco) | `docker compose down` |
| Parar e **apagar todo o banco de dados** (reset limpo) | `docker compose down -v` |
| Recompilar o frontend após alterações de código | `docker compose run --rm frontend npm run build && docker compose restart frontend` |

### Solução de problemas comuns

- **Erro no contêiner `frontend` indicando pasta `dist` não encontrada:**  
  Execute `docker compose run --rm frontend npm run build` e depois `docker compose restart frontend`.
- **A tela não abre em `http://localhost:5173`:**  
  Use **`https://localhost:5173`** (com `https`) e aceite o certificado autoassinado clicando em *Avançado → Prosseguir*.
- **Conflito de porta (`port is already allocated` nas portas `5432`, `8000` ou `5173`):**  
  Verifique se já existe um PostgreSQL ou servidor rodando localmente na máquina. Para a porta do banco, basta alterar `POSTGRES_PORT=5433` no `.env` e reiniciar com `docker compose up -d`.
- **Câmera do leitor de QR Code bloqueada no celular:**  
  Navegadores móveis só liberam a câmera (`getUserMedia`) em contextos **HTTPS confiáveis**. Utilize a URL gerada pelo contêiner `tunnel` (`docker compose logs tunnel`).
