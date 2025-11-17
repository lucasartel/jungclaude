"""
admin_telegram.py - Dashboard Administrativo para Telegram
==========================================================

Dashboard Streamlit para monitorar usuários do Bot Telegram.
Compatível com jung_core.py (versão unificada).

Funcionalidades:
- Visualizar todos os usuários do Telegram
- Acompanhar conversas e conflitos
- Gerar análises individuais
- Estatísticas gerais do bot

Autor: Sistema Jung Claude
Versão: 2.0 - Integrado com jung_core.py
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
        if datetime.fromisoformat(u['last_interaction']) > yesterday
    )
    
    # Total de conflitos
    cursor = db.sqlite_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM archetype_conflicts WHERE platform = 'telegram'")
    total_conflicts = cursor.fetchone()[0]
    
    # Total de análises
    cursor.execute("SELECT COUNT(*) FROM full_analyses WHERE platform = 'telegram'")
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


def get_user_archetype_summary(user_hash: str) -> str:
    """Retorna resumo dos arquétipos do usuário"""
    conflicts = db.get_user_conflicts(user_hash, limit=100)
    
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
    
    user_hash = user['user_hash']
    user_name = user['user_name']
    
    # Estatísticas
    total_messages = user['total_messages']
    last_interaction = format_timestamp(user['last_interaction'])
    
    # Arquétipos
    archetypes = get_user_archetype_summary(user_hash)
    
    # Contar memórias
    memory_count = db.count_memories(user_hash)
    
    # Card
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        
        with col1:
            st.markdown(f"### 👤 {user_name}")
            st.caption(f"🆔 `{user_hash}`")
        
        with col2:
            st.metric("💬 Mensagens", total_messages)
            st.caption(f"📝 {memory_count} memórias")
        
        with col3:
            st.metric("⏰ Última interação", last_interaction)
        
        with col4:
            if st.button("🔍 Ver Detalhes", key=f"view_{user_hash}"):
                st.session_state.selected_user = user_hash
                st.session_state.selected_user_name = user_name
                st.rerun()
        
        # Arquétipos
        if archetypes != "Nenhum arquétipo identificado ainda":
            st.markdown(f"**Arquétipos:** {archetypes}")
        
        st.divider()


def render_conversation_history(user_hash: str, limit: int = 20):
    """Renderiza histórico de conversas"""
    
    memories = db.get_user_memories(user_hash, limit)
    
    if not memories:
        st.warning("Nenhuma conversa registrada ainda.")
        return
    
    st.subheader(f"💬 Últimas {len(memories)} conversas")
    
    for i, memory in enumerate(reversed(memories)):
        # Separar User e Assistant
        parts = memory['text'].split('\nAssistant: ')
        
        if len(parts) == 2:
            user_msg = parts[0].replace('User: ', '').strip()
            assistant_msg = parts[1].strip()
            
            # Timestamp
            timestamp = format_timestamp(memory['timestamp'])
            
            with st.expander(f"📅 {timestamp} - {user_msg[:50]}..."):
                st.markdown("**👤 Usuário:**")
                st.info(user_msg)
                
                st.markdown("**🤖 Jung Claude:**")
                st.success(assistant_msg)


def render_conflicts_history(user_hash: str, limit: int = 10):
    """Renderiza histórico de conflitos"""
    
    conflicts = db.get_user_conflicts(user_hash, limit)
    
    if not conflicts:
        st.info("Nenhum conflito arquetípico registrado ainda.")
        return
    
    st.subheader(f"⚡ Conflitos Arquetípicos ({len(conflicts)})")
    
    for conflict in conflicts:
        timestamp = format_timestamp(conflict['timestamp'])
        
        with st.expander(f"⚔️ {conflict['archetype1']} vs {conflict['archetype2']} - {timestamp}"):
            st.markdown(format_conflict_for_display(conflict))
            
            # Mostrar resolução se houver
            if conflict.get('resolution'):
                st.markdown("**✅ Resolução:**")
                st.success(conflict['resolution'])


def render_analyses_history(user_hash: str):
    """Renderiza histórico de análises completas"""
    
    analyses = db.get_user_analyses(user_hash)
    
    if not analyses:
        st.info("Nenhuma análise completa gerada ainda.")
        return
    
    st.subheader(f"📊 Análises Completas ({len(analyses)})")
    
    for analysis in analyses:
        timestamp = format_timestamp(analysis['timestamp'])
        
        with st.expander(f"📖 Análise de {timestamp}"):
            st.markdown(f"**🧬 MBTI:** `{analysis['mbti']}`")
            st.markdown(f"**🎭 Fase:** {analysis['phase']}/5")
            
            if analysis['dominant_archetypes']:
                st.markdown(f"**⭐ Arquétipos Dominantes:** {analysis['dominant_archetypes']}")
            
            st.divider()
            st.markdown(analysis['full_analysis'])


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
    ["Última interação", "Mais mensagens", "Nome"],
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
    if order_by == "Última interação":
        users.sort(key=lambda x: x['last_interaction'], reverse=True)
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
    user_hash = st.session_state.selected_user
    user_name = st.session_state.selected_user_name
    
    # Header do usuário
    st.header(f"👤 {user_name}")
    st.caption(f"🆔 `{user_hash}`")
    
    # Estatísticas do usuário
    stats = db.get_user_stats(user_hash)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💬 Mensagens", stats['total_messages'])
    
    with col2:
        memory_count = db.count_memories(user_hash)
        st.metric("📝 Memórias", memory_count)
    
    with col3:
        conflicts_count = len(db.get_user_conflicts(user_hash, limit=1000))
        st.metric("⚡ Conflitos", conflicts_count)
    
    with col4:
        analyses_count = len(db.get_user_analyses(user_hash))
        st.metric("📊 Análises", analyses_count)
    
    st.divider()
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Conversas",
        "⚡ Conflitos",
        "📊 Análises",
        "🎭 Arquétipos",
        "🔮 Gerar Nova Análise"
    ])
    
    # TAB 1: Conversas
    with tab1:
        render_conversation_history(user_hash, limit=30)
    
    # TAB 2: Conflitos
    with tab2:
        render_conflicts_history(user_hash, limit=20)
    
    # TAB 3: Análises
    with tab3:
        render_analyses_history(user_hash)
    
    # TAB 4: Arquétipos
    with tab4:
        st.subheader("🎭 Biblioteca de Arquétipos")
        
        st.markdown("""
        Aqui estão todos os arquétipos junguianos que o sistema pode identificar.
        Clique em um para ver detalhes.
        """)
        
        # Organizar em grid 3 colunas
        archetypes = list(Config.ARCHETYPES.keys())
        cols = st.columns(3)
        
        for i, archetype in enumerate(archetypes):
            with cols[i % 3]:
                with st.expander(f"{Config.ARCHETYPES[archetype]['emoji']} {archetype}"):
                    st.markdown(format_archetype_info(archetype))
    
    # TAB 5: Gerar Nova Análise
    with tab5:
        st.subheader("🔮 Gerar Análise Junguiana Completa")
        
        memory_count = db.count_memories(user_hash)
        
        if memory_count < Config.MIN_MEMORIES_FOR_ANALYSIS:
            st.warning(
                f"⚠️ Este usuário precisa de pelo menos **{Config.MIN_MEMORIES_FOR_ANALYSIS} conversas** "
                f"para gerar uma análise completa.\n\n"
                f"Atualmente tem apenas **{memory_count} conversas**."
            )
        else:
            st.success(
                f"✅ Este usuário tem **{memory_count} conversas** registradas. "
                f"Pronto para análise!"
            )
            
            # Seletor de modelo
            model = st.selectbox(
                "🤖 Escolha o modelo para análise:",
                ["gpt-4o", "gpt-4o-mini", "grok-beta"],
                index=0,
                help="GPT-4o oferece análises mais profundas, mas é mais caro."
            )
            
            if st.button("🚀 Gerar Análise Completa", type="primary", use_container_width=True):
                with st.spinner("🧠 Analisando psique do usuário... (pode levar 30-60 segundos)"):
                    analysis = engine.generate_full_analysis(
                        user_hash=user_hash,
                        user_name=user_name,
                        platform="telegram",
                        model=model
                    )
                
                if analysis:
                    st.success("✅ Análise gerada com sucesso!")
                    
                    # Exibir análise
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("🧬 MBTI", analysis['mbti'])
                    
                    with col2:
                        st.metric("🎭 Fase da Jornada", f"{analysis['phase']}/5")
                    
                    if analysis.get('archetypes'):
                        st.markdown(f"**⭐ Arquétipos Dominantes:** {', '.join(analysis['archetypes'])}")
                    
                    st.markdown("---")
                    st.markdown("### 📖 Análise Completa")
                    st.markdown(analysis['insights'])
                    
                    # Opção de baixar
                    analysis_text = f"""
# Análise Junguiana Completa
**Usuário:** {user_name}
**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
**MBTI:** {analysis['mbti']}
**Fase:** {analysis['phase']}/5

{analysis['insights']}
"""
                    
                    st.download_button(
                        label="💾 Baixar Análise (TXT)",
                        data=analysis_text,
                        file_name=f"analise_jung_{user_name}_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )
                
                else:
                    st.error("❌ Erro ao gerar análise. Verifique os logs.")

# ============================================================
# FOOTER
# ============================================================

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.caption("🧠 **Jung Bot Admin v2.0**")

with col2:
    st.caption(f"🗄️ Database: `{Config.SQLITE_PATH}`")

with col3:
    if st.button("🗑️ Limpar Cache"):
        st.cache_resource.clear()
        st.success("Cache limpo!")
        st.rerun()