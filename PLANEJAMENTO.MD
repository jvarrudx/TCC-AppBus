# Plano de Ação e Arquitetura de Software: Sistema de Gestão de Transporte Intermunicipal

## 1. Contexto e Arquitetura do Projeto
O sistema tem como objetivo a gestão de embarque e a previsão de demanda para o transporte universitário intermunicipal. A arquitetura adotada é baseada em microsserviços (desacoplada), focada em alta performance e segurança.

**Stack Tecnológica Consolidada:**
*   **Backend:** Python 3.x, Django, Django REST Framework (DRF).
*   **Autenticação:** JSON Web Tokens (JWT) utilizando a biblioteca `djangorestframework-simplejwt`, garantindo uma API *stateless*.
*   **Frontend:** JavaScript, Vue 3 (Composition API e Vite) empacotado como *Progressive Web App* (PWA).
*   **Banco de Dados:** PostgreSQL.
*   **Geração de QR Code:** Abordagem otimizada. O backend gera apenas um token criptografado; o Vue 3 renderiza o QR Code nativamente na tela do dispositivo, economizando banda de rede.
*   **Infraestrutura:** Docker e Docker Compose.

---

## 2. Estrutura de Diretórios Recomendada (Monorepo)
Para facilitar o controle de versão e a orquestração com Docker, a melhor prática é utilizar uma estrutura de *Monorepo*, mantendo o frontend e o backend no mesmo repositório, mas em contêineres isolados.

    transporte-universitario-mvp/
    ├── .git/
    ├── docker-compose.yml       # Orquestrador unificado (DB, Backend, Frontend)
    ├── .env                     # Variáveis de ambiente globais (ignorado no Git)
    ├── .gitignore
    ├── backend/                 # Aplicação Django
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   ├── core/                # Configurações do Django (settings.py, urls.py)
    │   ├── api/                 # App com os endpoints REST, serializers e views
    │   └── manage.py
    └── frontend/                # Aplicação Vue 3 + Vite
        ├── Dockerfile
        ├── package.json
        ├── vite.config.js       # Configuração do Vite e PWA
        ├── public/              # Ícones e manifest.json do PWA
        └── src/
            ├── assets/          # CSS e imagens
            ├── components/      # Componentes reutilizáveis
            ├── views/           # Telas (Login, Dashboard Estudante, Dashboard Motorista)
            ├── router/          # Vue Router (proteção de rotas com JWT)
            └── services/        # Configuração do Axios para chamadas à API

---

## 3. Plano de Ação: Etapas Iniciais (Fundação e Backend)

### Etapa 1: Configuração do Ambiente e Controle de Versão (Semana 1)
*Objetivo: Garantir um ambiente de desenvolvimento padronizado e isolado via Docker.*
*   **1.1. Repositório:** Inicializar o repositório Git e definir a estratégia de *branching* (ex: *GitFlow*) para viabilizar o desenvolvimento colaborativo simultâneo.
*   **1.2. Dockerização Inicial:** 
    *   Criar o `Dockerfile` do Django e o `Dockerfile` do Vue 3.
    *   Configurar o `docker-compose.yml` mapeando os volumes e portas para os 3 serviços: `db` (PostgreSQL na porta 5432), `backend` (Django na 8000) e `frontend` (Vue Vite na 5173).
*   **1.3. Variáveis de Ambiente:** Estruturar o arquivo `.env` para isolar credenciais de banco de dados e chaves secretas do JWT.

### Etapa 2: Modelagem e Configuração do Banco de Dados (Semanas 1 e 2)
*Objetivo: Traduzir o Diagrama Entidade-Relacionamento (DER) para os modelos do ORM do Django.*
*   **2.1. Modelos de Usuário Customizados:** Estender o `AbstractUser` do Django para suportar os perfis e permissões de acesso (`Role` = Estudante, Motorista).
*   **2.2. Construção dos Modelos (Models):**
    *   `Rota` e `Veiculo`.
    *   `Viagem`: Instância de uma rota em uma data/hora específica.
    *   `Embarque` (Tabela associativa): Relaciona Estudante e Viagem, incluindo os campos `status` (Confirmado, Cancelado, Embarcado) e `timestamp_embarque`.
*   **2.3. Migrações e Seeds:** Gerar as *migrations* e criar um *script* de dados fictícios para facilitar os testes iniciais de rota e validação.

### Etapa 3: Desenvolvimento da API REST e Regras de Negócio (Semanas 2 e 3)
*Objetivo: Criar os contratos (Endpoints) consumíveis pelo Vue 3.*
*   **3.1. Implementação do JWT:** Configurar o `SimpleJWT` no Django para emitir *Access* e *Refresh Tokens* nas rotas de login.
*   **3.2. Endpoints CRUD Básicos:** Desenvolver as *Views* e *Serializers* para listagem de viagens, confirmação de embarque e *dashboard* do motorista.
*   **3.3. Implementação da "Trava de 2 Horas" (Lógica Core):**
    *   Sobrescrever o método de validação no *serializer* de Embarque. O backend deve validar a diferença de tempo entre a hora atual e a hora da viagem, bloqueando alterações com um retorno `HTTP 400 Bad Request` se o limite de 2 horas for ultrapassado.
*   **3.4. Lógica de Segurança do QR Code:** Desenvolver a rotina que gera um *token* criptografado único por viagem confirmada, que será enviado como resposta JSON para o frontend.

---

## 4. Etapas Futuras (Visão Geral)

### Etapa 4: Estruturação do Frontend (Vue 3) e Integração API
*   Configuração do Vite, definição do Vue Router com *Navigation Guards* (verificando o JWT na sessão) e consumo dos endpoints do Django utilizando a biblioteca `Axios`.

### Etapa 5: Renderização do QR Code e Leitura (Mobile-First)
*   Utilizar biblioteca do ecossistema Vue (ex: `qrcode.vue`) para ler o *token* provido pela API e desenhar o código de barras bidimensional na tela do estudante. 
*   Implementar a rotina de leitura via câmera HTML5 nativa diretamente no painel do motorista.

### Etapa 6: Configuração PWA e Testes de Software
*   Configuração do `manifest.json` e registro de *Service Workers* para garantir o comportamento mobile e opções de cache offline. 
*   Escrita de testes automatizados (Pytest no Django) cobrindo exaustivamente os cenários limítrofes da trava de horário.