# -*- coding: utf-8 -*-
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

os.makedirs('prints_tcc', exist_ok=True)

# ==============================================================================
# FIGURA 7: Arquitetura Inicial e Orquestração de Contêineres
# ==============================================================================
def gerar_figura_7():
    fig, ax = plt.subplots(figsize=(15, 10), dpi=300)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 10)
    ax.axis('off')
    fig.patch.set_facecolor('#FFFFFF')

    # Cores
    c_docker_bg = '#F8FAFC'
    c_docker_border = '#0284C7'
    c_card_bg = '#FFFFFF'
    c_card_border = '#CBD5E1'
    c_client_bg = '#EFF6FF'
    c_client_border = '#3B82F6'
    c_accent_front = '#0D9488'
    c_accent_back = '#4F46E5'
    c_accent_db = '#2563EB'
    c_accent_tunnel = '#EA580C'

    # 1. Caixa Camada de Clientes (Dispositivos)
    ax.add_patch(patches.FancyBboxPatch((0.8, 8.1), 13.4, 1.5, boxstyle="round,pad=0.1,rounding_size=0.15",
                                        facecolor=c_client_bg, edgecolor=c_client_border, linewidth=1.5, linestyle='--'))
    ax.text(1.2, 9.35, "CAMADA DE APRESENTAÇÃO / DISPOSITIVOS CLIENTES (USUÁRIOS)", fontsize=10, fontweight='bold', color='#1E3A8A')

    # Clientes individuais
    clients = [
        (1.2, "Discente / Estudante (Mobile PWA)\n• Carteirinha Digital & QR Code de Embarque\n• Predição 'Vou/Não vou' & Fila de Espera\n• Mural de Avisos Assíncrono"),
        (5.8, "Motorista / Condutor (Modo Rodovia)\n• Painel de Bordo & Lista Nominal Offline\n• Validação Óptica de Presença (Câmera)\n• Quick Replies (Alertas de 1 Toque)"),
        (10.4, "Gestor Municipal (Web Desktop)\n• Painel Administrativo de Linhas e Frotas\n• Homologação Cadastral Discente\n• Relatórios e Auditoria Multi-tenant")
    ]
    for x, txt in clients:
        ax.add_patch(patches.FancyBboxPatch((x, 8.25), 3.8, 0.95, boxstyle="round,pad=0.08,rounding_size=0.1",
                                            facecolor='#FFFFFF', edgecolor='#93C5FD', linewidth=1.2))
        ax.text(x + 0.15, 8.75, txt, fontsize=7.5, verticalalignment='center', color='#1E293B', linespacing=1.3)

    # 2. Grande Caixa: Docker Host & Rede Bridge
    ax.add_patch(patches.FancyBboxPatch((0.8, 0.4), 13.4, 7.3, boxstyle="round,pad=0.15,rounding_size=0.2",
                                        facecolor=c_docker_bg, edgecolor=c_docker_border, linewidth=2))
    ax.text(1.2, 7.35, "ORQUESTRAÇÃO DOCKER COMPOSE  —  Rede Bridge Isolada: appbus_net", fontsize=11, fontweight='bold', color='#0369A1')

    # Contêiner Frontend
    ax.add_patch(patches.FancyBboxPatch((1.2, 4.3), 3.8, 2.7, boxstyle="round,pad=0.1,rounding_size=0.15",
                                        facecolor=c_card_bg, edgecolor=c_accent_front, linewidth=1.8))
    ax.add_patch(patches.Rectangle((1.2, 6.6), 3.8, 0.4, facecolor=c_accent_front, edgecolor='none'))
    ax.text(3.1, 6.8, "appbus_frontend (Porta 5173)", fontsize=9.5, fontweight='bold', color='#FFFFFF', ha='center', va='center')
    front_text = (
        "• Vue.js 3 (Composition API) & Vite\n"
        "• Quasar Framework (Mobile-First UI)\n"
        "• Pinia Store (Gerenciamento de Estado)\n"
        "• Axios Client (withCredentials: true)\n"
        "• Service Worker (Google Workbox Cache)\n"
        "• LocalStorage Resiliente (Modo Offline):\n"
        "   - appbus_offline_checkins\n"
        "   - appbus_active_trip_snapshot\n"
        "   - appbus_active_trip_students"
    )
    ax.text(1.4, 5.4, front_text, fontsize=7.5, color='#334155', linespacing=1.35)

    # Contêiner Tunnel Cloudflare
    ax.add_patch(patches.FancyBboxPatch((1.2, 1.0), 3.8, 2.8, boxstyle="round,pad=0.1,rounding_size=0.15",
                                        facecolor=c_card_bg, edgecolor=c_accent_tunnel, linewidth=1.8))
    ax.add_patch(patches.Rectangle((1.2, 3.4), 3.8, 0.4, facecolor=c_accent_tunnel, edgecolor='none'))
    ax.text(3.1, 3.6, "appbus_tunnel (Cloudflare)", fontsize=9.5, fontweight='bold', color='#FFFFFF', ha='center', va='center')
    tunnel_text = (
        "• Imagem: cloudflare/cloudflared\n"
        "• Túnel Seguro HTTPS Remoto\n"
        "• Roteamento para https://frontend:5173\n"
        "• Habilita permissão de Câmera/PWA\n"
        "  em dispositivos móveis reais na rede\n"
        "  celular para leitura do QR Code"
    )
    ax.text(1.4, 2.15, tunnel_text, fontsize=7.8, color='#334155', linespacing=1.35)

    # Contêiner Backend
    ax.add_patch(patches.FancyBboxPatch((5.8, 1.0), 4.2, 6.0, boxstyle="round,pad=0.1,rounding_size=0.15",
                                        facecolor=c_card_bg, edgecolor=c_accent_back, linewidth=1.8))
    ax.add_patch(patches.Rectangle((5.8, 6.6), 4.2, 0.4, facecolor=c_accent_back, edgecolor='none'))
    ax.text(7.9, 6.8, "appbus_backend (Porta 8000)", fontsize=9.5, fontweight='bold', color='#FFFFFF', ha='center', va='center')
    back_text = (
        "CAMADA DE APLICAÇÃO E REGRAS DE NEGÓCIO\n\n"
        "• Python 3.11-slim & Django 5.x\n"
        "• Django REST Framework (DRF RESTful API)\n"
        "• Autenticação Stateless (SimpleJWT):\n"
        "   - Token de Acesso em Memória Volátil\n"
        "   - Refresh Token em Cookie HttpOnly + Secure\n"
        "• Isolamento Lógico Multi-Tenant:\n"
        "   - TenantBaseViewSet (Filtro por cliente_id)\n"
        "• Controle de Concorrência & Atomicidade:\n"
        "   - select_for_update (Trava anti-superlotação)\n"
        "   - Algoritmo de Prioridade de Ciclo e Fila\n"
        "• Módulo de Privacidade & Governança LGPD:\n"
        "   - Provas de Consentimento (IP, User-Agent)\n"
        "   - Anonimização Transacional Irreversível"
    )
    ax.text(6.0, 3.7, back_text, fontsize=7.5, color='#334155', linespacing=1.32)

    # Contêiner Banco de Dados
    ax.add_patch(patches.FancyBboxPatch((10.7, 2.2), 3.2, 4.8, boxstyle="round,pad=0.1,rounding_size=0.15",
                                        facecolor=c_card_bg, edgecolor=c_accent_db, linewidth=1.8))
    ax.add_patch(patches.Rectangle((10.7, 6.6), 3.2, 0.4, facecolor=c_accent_db, edgecolor='none'))
    ax.text(12.3, 6.8, "appbus_db (Porta 5432)", fontsize=9.5, fontweight='bold', color='#FFFFFF', ha='center', va='center')
    db_text = (
        "CAMADA DE PERSISTÊNCIA\n\n"
        "• PostgreSQL 15-alpine\n"
        "• 21 Entidades Relacionais\n"
        "• Padrão Party / Role\n"
        "• Multi-Version Concurrency\n"
        "  Control (MVCC)\n"
        "• Healthcheck Automatizado\n"
        "  (pg_isready)\n"
        "• Integridade Referencial\n"
        "• Índices Otimizados por Rota\n\n"
        "VOLUME PERSISTENTE:\n"
        "• postgres_data"
    )
    ax.text(10.9, 4.3, db_text, fontsize=7.8, color='#334155', linespacing=1.32)

    # Setas e Conexões
    # Clientes -> Frontend
    ax.annotate('', xy=(3.1, 7.0), xytext=(3.1, 8.1),
                arrowprops=dict(arrowstyle="<->", color="#0284C7", lw=1.8))
    ax.text(3.2, 7.6, "HTTPS / PWA", fontsize=8, color='#0369A1', fontweight='bold')

    # Tunnel -> Frontend
    ax.annotate('', xy=(3.1, 4.3), xytext=(3.1, 3.8),
                arrowprops=dict(arrowstyle="->", color="#EA580C", lw=1.8))
    ax.text(3.2, 4.05, "Proxy HTTPS", fontsize=7.5, color='#C2410C')

    # Frontend <-> Backend
    ax.annotate('', xy=(5.8, 5.2), xytext=(5.0, 5.2),
                arrowprops=dict(arrowstyle="<->", color="#4F46E5", lw=2))
    ax.text(5.4, 5.4, "REST / JSON\n(JWT Cookies)", fontsize=7.5, color='#4338CA', ha='center')

    # Backend <-> Database
    ax.annotate('', xy=(10.7, 4.6), xytext=(10.0, 4.6),
                arrowprops=dict(arrowstyle="<->", color="#2563EB", lw=2))
    ax.text(10.35, 4.8, "TCP / SQL\n(psycopg2)", fontsize=7.5, color='#1D4ED8', ha='center')

    # Salvar imagem
    out_path = os.path.join('prints_tcc', 'Figura_07_Arquitetura_Inicial_e_Orquestracao_Docker.png')
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, facecolor='#FFFFFF')
    plt.close()
    print(f"Figura 7 gerada com sucesso em: {out_path}")

# ==============================================================================
# FIGURA 6: Diagrama Entidade-Relacionamento (DER)
# ==============================================================================
def gerar_figura_6():
    fig, ax = plt.subplots(figsize=(16, 11), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 11)
    ax.axis('off')
    fig.patch.set_facecolor('#FFFFFF')

    # Cores de grupos
    bg_color = '#F8FAFC'
    border_color = '#94A3B8'

    # Paleta de entidades por domínio
    c_geo = ('#E0F2FE', '#0284C7', '#0369A1')      # Localização
    c_party = ('#EEF2FF', '#6366F1', '#4338CA')    # Party/Role & Auth
    c_priv = ('#FEF3C7', '#D97706', '#92400E')     # LGPD & Privacidade
    c_frota = ('#DCFCE7', '#16A34A', '#15803D')    # Frota & Rota
    c_op = ('#FEE2E2', '#DC2626', '#991B1B')       # Operação Diária & Viagem

    # Função auxiliar para desenhar tabela DER
    def draw_entity(x, y, w, h, title, pk_fields, other_fields, theme):
        bg, border, header_c = theme
        # Box principal
        ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.08",
                                            facecolor='#FFFFFF', edgecolor=border, linewidth=1.4))
        # Header
        hh = 0.42
        ax.add_patch(patches.Rectangle((x, y + h - hh), w, hh, facecolor=header_c, edgecolor='none'))
        ax.text(x + w/2, y + h - hh/2, title, fontsize=8, fontweight='bold', color='#FFFFFF', ha='center', va='center')
        
        # Atributos
        lines = []
        for pk in pk_fields:
            lines.append(f"[PK] {pk}")
        for of in other_fields:
            lines.append(f"  {of}")
        
        txt_content = "\n".join(lines)
        ax.text(x + 0.1, y + h - hh - 0.12, txt_content, fontsize=6.5, color='#1E293B', va='top', linespacing=1.28)

    # 1. Agrupador: LOCALIZAÇÃO
    ax.add_patch(patches.FancyBboxPatch((0.4, 7.8), 3.2, 2.9, boxstyle="round,pad=0.1,rounding_size=0.1",
                                        facecolor=bg_color, edgecolor=border_color, linestyle=':'))
    ax.text(0.6, 10.45, "LOCALIZAÇÃO & ENDEREÇAMENTO", fontsize=8, fontweight='bold', color='#475569')
    draw_entity(0.6, 9.3, 2.8, 1.0, "UF", ["sigla (PK)"], ["nome"], c_geo)
    draw_entity(0.6, 8.0, 2.8, 1.1, "Cidade", ["id (PK)"], ["nome", "uf_sigla (FK)"], c_geo)

    # 2. Agrupador: NÚCLEO MULTI-TENANT & PARTY/ROLE
    ax.add_patch(patches.FancyBboxPatch((4.0, 6.0), 7.6, 4.7, boxstyle="round,pad=0.1,rounding_size=0.1",
                                        facecolor=bg_color, edgecolor=border_color, linestyle=':'))
    ax.text(4.2, 10.45, "NÚCLEO MULTI-TENANT & PADRÃO PARTY / ROLE", fontsize=8, fontweight='bold', color='#475569')
    draw_entity(4.2, 8.9, 3.4, 1.4, "Cliente (Tenant Base)", ["id (PK UUID)"], ["nome, cnpj, ativo", "cidade_id (FK)", "configuracoes_json"], c_party)
    draw_entity(4.2, 6.3, 3.4, 2.4, "Pessoa (Party)", ["id (PK UUID)"], ["cliente_id (FK Tenant)", "nome_completo, cpf", "data_nascimento", "telefone, email", "nome_mae", "endereco_id (FK)", "is_anonimizado"], c_party)
    draw_entity(8.0, 8.9, 3.4, 1.4, "UsuarioAuth", ["id (PK)"], ["email, password_hash", "is_active, is_staff", "cliente_id (FK Tenant)"], c_party)
    
    # Papéis derivados de Pessoa
    draw_entity(8.0, 7.6, 1.6, 1.1, "Aluno (Role)", ["id (PK)"], ["pessoa_id (FK 1:1)", "matricula, turno"], c_party)
    draw_entity(9.8, 7.6, 1.6, 1.1, "Motorista", ["id (PK)"], ["pessoa_id (FK 1:1)", "cnh, categoria"], c_party)
    draw_entity(8.0, 6.3, 3.4, 1.1, "Administrador", ["id (PK)"], ["pessoa_id (FK 1:1)", "cargo, nivel_acesso"], c_party)

    # 3. Agrupador: GOVERNANÇA E LGPD
    ax.add_patch(patches.FancyBboxPatch((12.0, 6.0), 3.6, 4.7, boxstyle="round,pad=0.1,rounding_size=0.1",
                                        facecolor=bg_color, edgecolor=border_color, linestyle=':'))
    ax.text(12.2, 10.45, "GOVERNANÇA & PRIVACIDADE LGPD", fontsize=8, fontweight='bold', color='#475569')
    draw_entity(12.2, 8.7, 3.2, 1.6, "Documento_Legal", ["id (PK UUID)"], ["tipo (TERMOS/PRIVACIDADE)", "versao, conteudo_html", "data_vigencia, ativo"], c_priv)
    draw_entity(12.2, 6.3, 3.2, 2.2, "Registro_Consentimento", ["id (PK UUID)"], ["aluno_id (FK)", "documento_id (FK)", "data_consentimento", "ip_origem, user_agent", "responsavel_cpf", "responsavel_nome"], c_priv)

    # 4. Agrupador: FROTA E ROTAS
    ax.add_patch(patches.FancyBboxPatch((0.4, 0.4), 6.8, 5.3, boxstyle="round,pad=0.1,rounding_size=0.1",
                                        facecolor=bg_color, edgecolor=border_color, linestyle=':'))
    ax.text(0.6, 5.45, "FROTA, INSTITUIÇÕES & LINHAS", fontsize=8, fontweight='bold', color='#475569')
    draw_entity(0.6, 3.9, 3.0, 1.3, "ModeloVeiculo", ["id (PK)"], ["marca, modelo", "capacidade_assentos"], c_frota)
    draw_entity(0.6, 2.2, 3.0, 1.5, "Onibus", ["id (PK UUID)"], ["cliente_id (FK)", "placa, renavam, prefixo", "modelo_id (FK)", "ativo"], c_frota)
    draw_entity(3.9, 3.9, 3.1, 1.3, "Instituicao", ["id (PK UUID)"], ["nome, sigla", "campus, cidade_id (FK)"], c_frota)
    draw_entity(3.9, 2.0, 3.1, 1.7, "Rota", ["id (PK UUID)"], ["cliente_id (FK)", "nome, codigo, turno", "origem, destino"], c_frota)
    draw_entity(0.6, 0.7, 6.4, 1.1, "RotaInstituicao", ["id (PK)"], ["rota_id (FK)", "instituicao_id (FK)", "ordem_parada"], c_frota)

    # 5. Agrupador: OPERAÇÃO DIÁRIA & VIAGENS
    ax.add_patch(patches.FancyBboxPatch((7.6, 0.4), 8.0, 5.3, boxstyle="round,pad=0.1,rounding_size=0.1",
                                        facecolor=bg_color, edgecolor=border_color, linestyle=':'))
    ax.text(7.8, 5.45, "OPERAÇÃO DIÁRIA, PREDIÇÃO & CHECK-IN", fontsize=8, fontweight='bold', color='#475569')
    draw_entity(7.8, 3.6, 3.6, 1.7, "Viagem", ["id (PK UUID)"], ["rota_id (FK)", "onibus_id (FK)", "motorista_id (FK)", "data, horario_saida", "sentido, status"], c_op)
    draw_entity(7.8, 0.7, 3.6, 2.7, "PrevisaoViagem", ["id (PK UUID)"], ["viagem_id (FK)", "aluno_id (FK)", "vai_embarcar (BOOL)", "prioridade_ciclo (BOOL)", "na_fila_espera (BOOL)", "ordem_fila", "data_registro"], c_op)
    draw_entity(11.8, 2.6, 3.6, 2.7, "Embarque", ["id (PK UUID)"], ["viagem_id (FK)", "aluno_id (FK)", "motorista_id (FK)", "horario_checkin", "metodo (QR_CODE/MANUAL)", "sincronizado_offline (BOOL)"], c_op)
    draw_entity(11.8, 0.7, 3.6, 1.7, "Aviso (Mural)", ["id (PK UUID)"], ["cliente_id (FK)", "autor_id (FK)", "rota_id (FK Null)", "titulo, mensagem", "tipo (URGENTE/ATRASO/...)"], c_op)

    # Conectores conceituais (Relacionamentos)
    lines_rel = [
        # (x1, y1, x2, y2, label)
        (5.9, 8.9, 5.9, 8.7, "1:N"),       # Cliente -> Pessoa
        (7.6, 7.5, 8.0, 7.8, "1:1"),       # Pessoa -> Aluno
        (7.6, 7.2, 9.8, 8.0, "1:1"),       # Pessoa -> Motorista
        (7.6, 6.8, 8.0, 6.8, "1:1"),       # Pessoa -> Administrador
        (9.6, 7.6, 12.2, 7.4, "1:N"),      # Aluno -> Consentimento
        (13.8, 8.7, 13.8, 8.5, "1:N"),     # DocLegal -> Consentimento
        (2.1, 2.2, 3.9, 2.8, "1:N"),       # Onibus / Rota
        (5.4, 2.0, 7.8, 4.4, "1:N"),       # Rota -> Viagem
        (9.6, 3.6, 9.6, 3.4, "1:N"),       # Viagem -> PrevisaoViagem
        (11.4, 4.4, 11.8, 4.4, "1:N"),     # Viagem -> Embarque
    ]
    for x1, y1, x2, y2, lbl in lines_rel:
        ax.plot([x1, x2], [y1, y2], color='#64748B', lw=1.2, linestyle='--')
        ax.text((x1+x2)/2, (y1+y2)/2, lbl, fontsize=6.5, color='#475569', ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.1', facecolor='#FFFFFF', edgecolor='#CBD5E1', lw=0.5))

    out_path = os.path.join('prints_tcc', 'Figura_06_Diagrama_Entidade_Relacionamento_DER.png')
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, facecolor='#FFFFFF')
    plt.close()
    print(f"Figura 6 gerada com sucesso em: {out_path}")

if __name__ == '__main__':
    gerar_figura_6()
    gerar_figura_7()
