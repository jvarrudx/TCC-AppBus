# Plano de Ação e Arquitetura de Software: Sistema de Gestão de Transporte Intermunicipal

## 1. Contexto do Projeto
O sistema tem como objetivo a gestão de embarque e a previsão de demanda para o transporte universitário intermunicipal. A arquitetura adotada é baseada em microsserviços (desacoplada), consistindo em uma API RESTful no backend responsável pelas regras de negócio rigorosas (como a trava de 2 horas) e um *Progressive Web App* (PWA) no frontend voltado para a experiência *mobile-first* e leitura de QR Codes. Todo o ambiente de execução local será padronizado utilizando contêineres.

**Stack Tecnológica:**
*   **Backend:** Python 3.x, Django, Django REST Framework (DRF).
*   **Frontend:** JavaScript, Vue.js, PWA (Service Workers).
*   **Banco de Dados:** PostgreSQL.
*   **Infraestrutura:** Docker e Docker Compose.

---

## 2. Plano de Ação: Etapas Iniciais (Fundação e Backend)

### Etapa 1: Configuração do Ambiente e Controle de Versão (Semana 1)
*Objetivo: Garantir que todos os desenvolvedores trabalhem no mesmo ambiente sem conflitos de dependências.*
*   **1.1. Repositório:** Inicializar o repositório Git (GitHub/GitLab) e definir a estratégia de *branching* (ex: *GitFlow* ou *Trunk-based development*) para garantir uma colaboração fluida na escrita do código entre você e o Bebeto.
*   **1.2. Dockerização Inicial:** 
    *   Criar o `Dockerfile` para o serviço do Django.
    *   Criar o `Dockerfile` para o serviço do Vue.js.
    *   Configurar o `docker-compose.yml` orquestrando 3 serviços: `db` (PostgreSQL), `backend` (Django) e `frontend` (Vue).
*   **1.3. Variáveis de Ambiente:** Estruturar o arquivo `.env` para isolar credenciais de banco de dados, chaves secretas e configurações de *debug*.

### Etapa 2: Modelagem e Configuração do Banco de Dados (Semanas 1 e 2)
*Objetivo: Traduzir o Diagrama Entidade-Relacionamento (DER) para os modelos do ORM do Django.*
*   **2.1. Modelos de Usuário Customizados:** Estender o `AbstractUser` do Django para suportar múltiplos perfis (`Role` = Estudante, Motorista, Administrador).
*   **2.2. Construção dos Modelos (Models):**
    *   `Rota`: Origem, destino e horários padrão.
    *   `Veiculo`: Placa, capacidade máxima (assentos).
    *   `Viagem`: Instância de uma rota em uma data/hora específica, associada a um veículo e motorista.
    *   `Embarque` (Tabela associativa): Relaciona Estudante e Viagem. Campos críticos: `status` (Pendente, Confirmado, Cancelado, Embarcado) e `timestamp_embarque`.
*   **2.3. Migrações e Dados Iniciais:** Gerar as *migrations* e criar um *script* de *seeds* (dados fictícios) para popular o banco de dados local rapidamente durante os testes.

### Etapa 3: Desenvolvimento da API e Regras de Negócio (Semanas 2 e 3)
*Objetivo: Criar os contratos (Endpoints) que o frontend irá consumir e garantir a segurança dos dados.*
*   **3.1. Autenticação e Autorização:** Implementar segurança baseada em *tokens* (JWT - JSON Web Tokens).
*   **3.2. Endpoints CRUD Básicos (Views e Serializers):** 
    *   Listagem de viagens disponíveis (Filtro por data e rota).
    *   Criação/Cancelamento da intenção de embarque pelo estudante.
    *   Listagem de passageiros para o *dashboard* do motorista.
*   **3.3. Implementação da "Trava de 2 Horas" (Business Logic):**
    *   Sobrescrever o método de validação no *serializer* de Embarque. A lógica deve atuar em bloco: verificar o horário atual contra o horário da `Viagem` e retornar um `HTTP 400 Bad Request` se a diferença for menor ou igual a 2 horas.
*   **3.4. Lógica do QR Code:** Desenvolver a rotina criptográfica no backend que gera um *hash* ou *token* seguro e temporário que represente a confirmação daquele aluno para aquela viagem específica.

---

## 3. Etapas Futuras (Visão Geral)

### Etapa 4: Estruturação do Frontend (Vue.js) e Layout Mobile-First
*   Configuração do projeto Vue.js, definição do sistema de roteamento protegido (*Vue Router*) e consumo da API via `Axios` ou `Fetch`. Construção das telas de Login, Dashboard do Estudante e Dashboard do Motorista.

### Etapa 5: PWA, Service Workers e Integração de Câmera
*   Geração do `manifest.json`, configuração dos *Service Workers* para estratégias de *cache* (ícones, estrutura da página) e implementação da biblioteca de leitura de QR Code utilizando a API de câmera HTML5 no painel do motorista.

### Etapa 6: Testes, Refatoração e Preparação para o Deploy
*   Escrita de testes automatizados no Django (Pytest) para garantir que a trava temporal nunca falhe. Testes de integração na leitura do QR Code.