# Plano de Desenvolvimento - AppBus (TCC)

Este documento traduz o planejamento arquitetural e o escopo do TCC em um roteiro prático de desenvolvimento de software. Siga estas etapas sequencialmente junto ao seu assistente de IA.

## Fase 1: Fundação, Infraestrutura e Modelagem de Dados
*O objetivo desta fase é ter o banco de dados rodando e a modelagem estrita (ERM) refletida no código do backend.*

- [x] **Etapa 1.1: Setup do Ambiente Docker**
  - Criar `docker-compose.yml` contendo os serviços: `db` (PostgreSQL 15+), `web` (Django/Gunicorn) e `frontend` (Vue/Vite).
  - Configurar variáveis de ambiente (`.env`) para senhas e chaves secretas.
- [x] **Etapa 1.2: Setup do Projeto Django**
  - Iniciar o projeto Django e o app principal (ex: `core`).
  - Configurar conexão com o PostgreSQL.
  - Instalar e configurar `djangorestframework`, `djangorestframework-simplejwt` e `django-cors-headers`.
- [x] **Etapa 1.3: Modelagem de Dados (Custom User e LGPD)**
  - Implementar Enums (Status Viagem, Método Validação, etc.) usando `models.TextChoices`.
  - Criar o modelo customizado `Usuario_Auth` (substituindo o User padrão do Django).
  - Criar as tabelas de Governança: `Documento_Legal` e `Registro_Consentimento`.
- [x] **Etapa 1.4: Modelagem de Dados (Party/Role e Domínios)**
  - Criar os modelos de Endereço (UF, Cidade, Bairro, Endereco).
  - Implementar o "Party": Tabela `Pessoa` (1:1 com `Usuario_Auth`).
  - Implementar os "Roles": Tabelas `Cliente`, `Instituicao`, `Administrador`, `Aluno` e `Motorista`.
- [x] **Etapa 1.5: Modelagem de Dados (Operação)**
  - Criar os modelos de Frota e Rota: `Modelo_Veiculo`, `Onibus`, `Rota`, `Rota_Instituicao`.
  - Criar os modelos Transacionais: `Viagem`, `Previsao_Viagem`, `Embarque`.
  - Gerar e aplicar as migrações (`makemigrations` e `migrate`).

## Fase 2: Construção da API RESTful e Lógica de Negócio
*Foco na criação dos endpoints que o Vue.js consumirá, garantindo a segurança e o Multi-tenancy.*

- [x] **Etapa 2.1: Autenticação e Onboarding de Alunos**
  - Criar endpoint de registro de Aluno (recebe dados pessoais, senha e aceite dos termos).
  - Implementar a transação atômica (`transaction.atomic`) para salvar nas tabelas: Usuario_Auth -> Pessoa -> Aluno -> Registro_Consentimento.
  - Configurar os endpoints de login JWT (geração e refresh de token).
- [x] **Etapa 2.2: Middlewares e Isolamento Multi-tenant**
  - Sobrescrever o `get_queryset` nas Views do DRF para garantir que usuários de um Cliente (prefeitura) só vejam dados onde `cliente_id == seu_cliente_id`.
- [x] **Etapa 2.3: Endpoints de Gestão (CRUDs Básicos)**
  - Criar ViewSets e Serializers para: Veículos, Motoristas, Rotas, Escolas e Gestão de Alunos (Aprovação de Fila).
- [x] **Etapa 2.4: Lógica de Privacidade (LGPD)**
  - Criar endpoint para o Aluno solicitar exclusão.
  - Implementar a lógica de Anonimização (mascarar nome, CPF, setar `anonimizado=True`, inativar usuário auth), sem usar o comando `DELETE` no banco.
- [x] **Etapa 2.5: Fluxos Operacionais Core (Endpoints)**
  - Endpoint para **Predição de Demanda**: Requisição PATCH para "Vou/Não Vou".
  - Endpoint de **Instanciação de Viagem**: Abertura de viagem pelo motorista.
  - Endpoints de **Embarque**:
    - Via QR Code (valida UUID do ônibus, aluno, rota).
    - Via Motorista (Manual).
  - Endpoint de **Dashboard do Motorista**: Retorna agregação (COUNT) de alunos previstos vs embarcados.

## Fase 3: Frontend PWA - Infraestrutura e Painéis Web (Admin/Motorista)
*Início da construção visual utilizando Vue.js.*
Atuando como Engenheiro Frontend Sênior e Especialista em UI/UX, iniciaremos agora a "Fase 3: Frontend PWA" do nosso projeto AppBus. O backend (Django REST) está 100% concluído e blindado.

### Diretrizes Arquiteturais e de Design (Invioláveis)
- **Tech Stack:** Vue 3 (Composition API com `<script setup>`), Vite, Quasar Framework, Pinia e Axios.
- **Abordagem UI/UX:** "Mobile-First" extremo. A interface será um PWA utilizado principalmente por estudantes e motoristas em trânsito. O design deve ser *Clean*, com botões grandes e navegação fluida em telas pequenas.
- **Identidade Visual (Tema):** 
  - Fundo predominante: Modo Escuro (Preto ou Azul muito escuro, ex: `#121212` ou `#0B0F19`).
  - Cor de Destaque (Primary): Amarelo Ônibus Escolar (ex: `#F2C037` ou `#FFC107`).
  - Todo o texto primário deve ter alto contraste (branco/gelo) e as chamadas para ação (CTAs) usarão o amarelo de destaque.
  
- [x] **Etapa 3.1: Setup do Vue.js + PWA**
  - Iniciar projeto Vue 3 (Composition API, Vite).
  - Configurar `vite-plugin-pwa` para gerar o Service Worker básico, Manifest (ícones, nome, tema) e habilitar instalação do PWA.
  - Configurar o Vue Router e o gerenciamento de estado (Pinia).
  - Configurar o Axios (interceptors para injetar JWT Token e lidar com refresh).
- [x] **Etapa 3.2: Telas de Autenticação**
  - Tela de Login (Diferenciando visualmente ou logicamente perfis: Aluno, Motorista, Gestor).
  - Tela de Auto-cadastro (Com lógica condicional: se < 18 anos, exibir campo CPF do Responsável; checkbox obrigatório para Termos de Uso).
- [x] **Etapa 3.3: Dashboard do Cliente (Web Admin)**
  - Tela de Fila de Aprovação (Listar alunos pendentes -> Botões Aprovar/Rejeitar).
  - Tela de Gestão de Frota e Rotas.
  - Tela de Geração de QR Code (Exibe o UUID do veículo formatado em QR Code para impressão em PDF).
- [x] **Etapa 3.4: Painel do Motorista (Offline-First Parcial)**
  - Interface simplificada, botões grandes e de alto contraste.
  - Tela "Iniciar Viagem" (Selecionar Rota e Ônibus).
  - Tela "Em Andamento": Exibição do contador (X Previstos / Y Embarcados).
  - Implementar lista de validação manual (Busca pelo nome do aluno -> Check-in).
  - Lógica de contingência Offline-First para enfileirar check-ins manuais no dispositivo (`localStorage`) com auto-sincronização na reconexão.

## Fase 4: Módulo do Aluno e Validação PWA
*A experiência do usuário final e os recursos de hardware do dispositivo.*

- [ ] **Etapa 4.1: Painel Principal do Aluno e Predição**
  - Interface estilo "Mobile First".
  - Exibição de cards de viagem do dia.
  - Botões de seleção rápida (Toggle): "Vou na Ida" / "Não vou na Volta". (Dispara PATCH automático para a API).
- [ ] **Etapa 4.2: Leitor de QR Code (Embarque Óptico)**
  - Integrar biblioteca de leitura óptica (ex: `html5-qrcode` ou `vue-qrcode-reader`).
  - Lógica: Ao clicar em "Embarcar", abrir câmera -> ler UUID -> disparar POST para API -> Exibir Tela Verde (Sucesso) ou Vermelha (Erro).
- [ ] **Etapa 4.3: Tela de Perfil e LGPD**
  - Visualização de dados do perfil.
  - Botão "Gerenciar Privacidade" -> Opção para "Revogar Consentimento e Excluir Conta" (Aciona o endpoint de anonimização do backend).
- [ ] **Etapa 4.4: Testes e Refinamento MVP**
  - Testes de concorrência: simular múltiplos check-ins simultâneos (validação do MVCC do PostgreSQL).
  - Auditoria no PWA pelo Lighthouse (Chrome) para validar cache e instalabilidade.