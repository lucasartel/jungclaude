"""
admin_telegram.py - Dashboard Administrativo para Telegram
==========================================================

✅ VERSÃO 2.1 - CORRIGIDA PARA COMPATIBILIDADE COM jung_core.py v3.3

Correções aplicadas:
- Usa get_user_conversations() ao invés de get_user_memories()
- Corrige db.conn ao invés de db.sqlite_conn
- Usa user_id ao invés de user_hash
- Usa last_seen ao invés de last_interaction
- Remove método generate_full_analysis (não implementado)
- Ajusta formato de exibição de conversas

Autor: Sistema Jung Claude
Versão: 2.1 - CORRIGIDA
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict

# Imports do jung_core
from jung_core import (
    Config,
    DatabaseManager,
    JungianEngine,
    create_user_hash,
    format_conflict_for_display,
    format_archetype_info
)

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Jung Bot Admin - Telegram",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# INICIALIZAÇÃO
# ============================================================

@st.cache_resource
def init_system():
    """Inicializa DatabaseManager e JungianEngine (cache para performance)"""
    db = DatabaseManager()
    engine = JungianEngine(db)
    return db, engine

db, engine = init_system()

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def get_telegram_stats() -> Dict:
    """Retorna estatísticas gerais do bot Telegram"""
    
    all_users = db.get_all_users(platform="telegram")
    
    total_users = len(all_users)
    total_messages = sum(u['total_messages'] for u in all_users)
    
    # Usuários ativos (últimas 24h)
    yesterday = datetime.now() - timedelta(days=1)
    active_24h = sum(
        1 for u in all_users 
        if u.get('last_seen') and datetime.fromisoformat(u['last_seen']) > yesterday
    )
    
    # Total de conflitos
    cursor = db.conn.cursor()  # ✅ CORRIGIDO: db.conn
    cursor.execute("SELECT COUNT(*) FROM archetype_conflicts")
    total_conflicts = cursor.fetchone()[0]
    
    # Total de análises
    cursor.execute("SELECT COUNT(*) FROM full_analyses")
    total_analyses = cursor.fetchone()[0]
    
    return {
        'total_users': total_users,
        'total_messages': total_messages,
        'active_24h': active_24h,
        'total_conflicts': total_conflicts,
        'total_analyses': total_analyses
    }


def format_timestamp(iso_timestamp: str) -> str:
    """Formata timestamp ISO para exibição"""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        now = datetime.now()
        diff = now - dt
        
        if diff.days == 0:
            if diff.seconds < 60:
                return "Agora mesmo"
            elif diff.seconds < 3600:
                mins = diff.seconds // 60
                return f"Há {mins} min"
            else:
                hours = diff.seconds // 3600
                return f"Há {hours}h"
        elif diff.days == 1:
            return "Ontem"
        elif diff.days < 7:
            return f"Há {diff.days} dias"
        else:
            return dt.strftime("%d/%m/%Y")
    except:
        return iso_timestamp


def get_user_archetype_summary(user_id: str) -> str:  # ✅ user_id
    """Retorna resumo dos arquétipos do usuário"""
    conflicts = db.get_user_conflicts(user_id, limit=100)
    
    if not conflicts:
        return "Nenhum arquétipo identificado ainda"
    
    # Contar frequência de cada arquétipo
    archetype_count = {}
    for c in conflicts:
        arch1 = c['archetype1']
        arch2 = c['archetype2']
        
        archetype_count[arch1] = archetype_count.get(arch1, 0) + 1
        archetype_count[arch2] = archetype_count.get(arch2, 0) + 1
    
    # Top 3 arquétipos
    top_archetypes = sorted(archetype_count.items(), key=lambda x: x[1], reverse=True)[:3]
    
    result = []
    for arch, count in top_archetypes:
        emoji = Config.ARCHETYPES.get(arch, {}).get('emoji', '❓')
        result.append(f"{emoji} {arch} ({count}x)")
    
    return " • ".join(result)


def render_user_card(user: Dict):
    """Renderiza card de usuário"""
    
    user_id = user['user_id']  # ✅ CORRIGIDO
    user_name = user['user_name']
    
    # Estatísticas
    total_messages = user['total_messages']
    last_seen = format_timestamp(user.get('last_seen', user.get('registration_date', '')))  # ✅ CORRIGIDO
    
    # Arquétipos
    archetypes = get_user_archetype_summary(user_id)
    
    # Contar conversas
    conv_count = db.count_conversations(user_id)  # ✅ CORRIGIDO
    
    # Card
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        
        with col1:
            st.markdown(f"### 👤 {user_name}")
            st.caption(f"🆔 `{user_id[:16]}...`")
        
        with col2:
            st.metric("💬 Mensagens", total_messages)
            st.caption(f"📝 {conv_count} conversas")
        
        with col3:
            st.metric("⏰ Última atividade", last_seen)
        
        with col4:
            if st.button("🔍 Ver Detalhes", key=f"view_{user_id}"):
                st.session_state.selected_user = user_id
                st.session_state.selected_user_name = user_name
                st.rerun()
        
        # Arquétipos
        if archetypes != "Nenhum arquétipo identificado ainda":
            st.markdown(f"**Arquétipos:** {archetypes}")
        
        st.divider()


def render_conversation_history(user_id: str, limit: int = 20):  # ✅ user_id
    """Renderiza histórico de conversas"""
    
    conversations = db.get_user_conversations(user_id, limit)  # ✅ CORRIGIDO
    
    if not conversations:
        st.warning("Nenhuma conversa registrada ainda.")
        return
    
    st.subheader(f"💬 Últimas {len(conversations)} conversas")
    
    for i, conv in enumerate(reversed(conversations)):
        # ✅ AJUSTADO para formato do banco
        user_msg = conv['user_input']
        assistant_msg = conv['ai_response']
        timestamp = format_timestamp(conv['timestamp'])
        
        with st.expander(f"📅 {timestamp} - {user_msg[:50]}..."):
            st.markdown("**👤 Usuário:**")
            st.info(user_msg)
            
            st.markdown("**🤖 Jung Claude:**")
            st.success(assistant_msg)
            
            # Mostrar métricas se houver
            if conv.get('tension_level') and conv['tension_level'] > 0:
                st.caption(f"⚡ Tensão: {conv['tension_level']:.0%}")


def render_conflicts_history(user_id: str, limit: int = 10):  # ✅ user_id
    """Renderiza histórico de conflitos"""
    
    conflicts = db.get_user_conflicts(user_id, limit)
    
    if not conflicts:
        st.info("Nenhum conflito arquetípico registrado ainda.")
        return
    
    st.subheader(f"⚡ Conflitos Arquetípicos ({len(conflicts)})")
    
    for conflict in conflicts:
        timestamp = format_timestamp(conflict['timestamp'])
        
        with st.expander(f"⚔️ {conflict['archetype1']} vs {conflict['archetype2']} - {timestamp}"):
            st.markdown(f"**Tipo:** {conflict.get('conflict_type', 'N/A')}")
            st.markdown(f"**Tensão:** {conflict.get('tension_level', 0):.0%}")
            st.markdown(f"**Descrição:** {conflict.get('description', 'N/A')}")


def render_analyses_history(user_id: str):  # ✅ user_id
    """Renderiza histórico de análises completas"""
    
    analyses = db.get_user_analyses(user_id)
    
    if not analyses:
        st.info("Nenhuma análise completa gerada ainda.")
        return
    
    st.subheader(f"📊 Análises Completas ({len(analyses)})")
    
    for analysis in analyses:
        timestamp = format_timestamp(analysis['timestamp'])
        
        with st.expander(f"📖 Análise de {timestamp}"):
            st.markdown(f"**🧬 MBTI:** `{analysis.get('mbti', 'N/A')}`")
            st.markdown(f"**🎭 Fase:** {analysis.get('phase', 1)}/5")
            
            if analysis.get('dominant_archetypes'):
                st.markdown(f"**⭐ Arquétipos Dominantes:** {analysis['dominant_archetypes']}")
            
            st.divider()
            st.markdown(analysis.get('full_analysis', 'Sem análise'))


# ============================================================
# INTERFACE PRINCIPAL
# ============================================================

# Header
st.title("📊 Jung Bot Admin - Telegram")
st.caption("Dashboard administrativo para monitorar o bot Telegram")

# ========== SIDEBAR ==========

st.sidebar.title("⚙️ Controles")

# Botão de atualizar
if st.sidebar.button("🔄 Atualizar Dados", use_container_width=True):
    st.cache_resource.clear()
    st.rerun()

st.sidebar.divider()

# Estatísticas gerais
stats = get_telegram_stats()

st.sidebar.subheader("📈 Estatísticas Gerais")
st.sidebar.metric("👥 Usuários Totais", stats['total_users'])
st.sidebar.metric("💬 Mensagens Totais", stats['total_messages'])
st.sidebar.metric("🟢 Ativos (24h)", stats['active_24h'])
st.sidebar.metric("⚡ Conflitos", stats['total_conflicts'])
st.sidebar.metric("📊 Análises", stats['total_analyses'])

st.sidebar.divider()

# Filtros
st.sidebar.subheader("🔍 Filtros")

order_by = st.sidebar.selectbox(
    "Ordenar por:",
    ["Última atividade", "Mais mensagens", "Nome"],
    index=0
)

min_messages = st.sidebar.number_input(
    "Mínimo de mensagens:",
    min_value=0,
    value=0,
    step=1
)

st.sidebar.divider()

# Botão voltar (se estiver vendo detalhes)
if 'selected_user' in st.session_state:
    if st.sidebar.button("⬅️ Voltar para lista", use_container_width=True):
        del st.session_state.selected_user
        del st.session_state.selected_user_name
        st.rerun()

# ========== CONTEÚDO PRINCIPAL ==========

# Se nenhum usuário selecionado → mostrar lista
if 'selected_user' not in st.session_state:
    
    st.header("👥 Usuários do Bot Telegram")
    
    # Buscar usuários
    users = db.get_all_users(platform="telegram")
    
    # Filtrar por mínimo de mensagens
    if min_messages > 0:
        users = [u for u in users if u['total_messages'] >= min_messages]
    
    # Ordenar
    if order_by == "Última atividade":
        users.sort(key=lambda x: x.get('last_seen', ''), reverse=True)  # ✅ CORRIGIDO
    elif order_by == "Mais mensagens":
        users.sort(key=lambda x: x['total_messages'], reverse=True)
    else:  # Nome
        users.sort(key=lambda x: x['user_name'])
    
    # Exibir total
    st.info(f"📋 Exibindo {len(users)} usuário(s)")
    
    # Renderizar cards
    if users:
        for user in users:
            render_user_card(user)
    else:
        st.warning("Nenhum usuário encontrado com os filtros aplicados.")

# Se usuário selecionado → mostrar detalhes
else:
    user_id = st.session_state.selected_user  # ✅ CORRIGIDO
    user_name = st.session_state.selected_user_name
    
    # Header do usuário
    st.header(f"👤 {user_name}")
    st.caption(f"🆔 `{user_id}`")
    
    # Estatísticas do usuário
    stats = db.get_user_stats(user_id)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💬 Mensagens", stats['total_messages'])
    
    with col2:
        conv_count = db.count_conversations(user_id)  # ✅ CORRIGIDO
        st.metric("📝 Conversas", conv_count)
    
    with col3:
        conflicts_count = len(db.get_user_conflicts(user_id, limit=1000))
        st.metric("⚡ Conflitos", conflicts_count)
    
    with col4:
        analyses_count = len(db.get_user_analyses(user_id))
        st.metric("📊 Análises", analyses_count)
    
    st.divider()
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([  # ✅ REMOVIDA TAB "Gerar Nova Análise"
        "💬 Conversas",
        "⚡ Conflitos",
        "📊 Análises",
        "🎭 Arquétipos"
    ])
    
    # TAB 1: Conversas
    with tab1:
        render_conversation_history(user_id, limit=30)
    
    # TAB 2: Conflitos
    with tab2:
        render_conflicts_history(user_id, limit=20)
    
    # TAB 3: Análises
    with tab3:
        render_analyses_history(user_id)
    
    # TAB 4: Arquétipos
    with tab4:
        st.subheader("🎭 Biblioteca de Arquétipos")
        
        st.markdown("""
        Aqui estão todos os arquétipos junguianos que o sistema pode identificar.
        Clique em um para ver detalhes.
        """)
        
        # Organizar em grid 2 colunas
        archetypes = list(Config.ARCHETYPES.keys())
        cols = st.columns(2)
        
        for i, archetype in enumerate(archetypes):
            with cols[i % 2]:
                with st.expander(f"{Config.ARCHETYPES[archetype]['emoji']} {archetype}"):
                    st.markdown(format_archetype_info(archetype))

# ============================================================
# FOOTER
# ============================================================

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.caption("🧠 **Jung Bot Admin v2.1 - CORRIGIDO**")

with col2:
    st.caption(f"🗄️ Database: `{Config.SQLITE_PATH}`")

with col3:
    if st.button("🗑️ Limpar Cache"):
        st.cache_resource.clear()
        st.success("Cache limpo!")
        st.rerun()