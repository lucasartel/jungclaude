"""
╔══════════════════════════════════════════════════════════════╗
║                   CLAUDE JUNG v2.0                           ║
║              Interface Web com Streamlit                      ║
╚══════════════════════════════════════════════════════════════╝

Interface web interativa para o sistema Claude Jung v2.0

Autor: Claude & Você
Data: 2025
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Any, Optional
import json

# Importar o sistema Claude Jung
from jung_claude_v2v import (
    ClaudeJung,
    ConversationMode,
    FactType,
    PsychicMode,
    logger
)

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Claude Jung v2.0",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# ESTILOS CUSTOMIZADOS
# =============================================================================

st.markdown("""
<style>
    /* Tema principal */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Container de chat */
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    
    .chat-message.user {
        background-color: #2b5876;
        color: white;
    }
    
    .chat-message.assistant {
        background-color: #4e4376;
        color: white;
    }
    
    /* Badges */
    .stat-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.25rem;
    }
    
    /* Títulos */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #1e1e2e;
    }
    
    /* Botões */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    .stButton>button:hover {
        opacity: 0.8;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# INICIALIZAÇÃO DO SISTEMA
# =============================================================================

@st.cache_resource
def initialize_jung():
    """Inicializa o sistema Claude Jung (cache para não recarregar)"""
    return ClaudeJung()

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def format_fact_type(fact_type: FactType) -> str:
    """Formata tipo de fato com emoji"""
    emojis = {
        FactType.PERSONAL: "👤",
        FactType.PREFERENCE: "❤️",
        FactType.GOAL: "🎯",
        FactType.EXPERIENCE: "📚",
        FactType.RELATIONSHIP: "👥",
        FactType.BEHAVIOR: "🔄",
        FactType.EMOTION: "😊",
        FactType.BELIEF: "💭",
        FactType.SKILL: "⚡",
        FactType.CHALLENGE: "⚠️",
    }
    return f"{emojis.get(fact_type, '📌')} {fact_type.value}"

def create_stats_chart(stats: Dict[str, Any]) -> Optional[go.Figure]:
    """Cria gráfico de estatísticas"""
    mem_stats = stats.get('memory', {})
    
    # Distribuição de tipos de fatos
    fact_types = mem_stats.get('fact_type_distribution', {})
    
    if fact_types:
        fig = go.Figure(data=[
            go.Bar(
                x=list(fact_types.keys()),
                y=list(fact_types.values()),
                marker_color='rgb(102, 126, 234)',
                text=list(fact_types.values()),
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="Distribuição de Tipos de Fatos",
            xaxis_title="Tipo",
            yaxis_title="Quantidade",
            template="plotly_dark",
            height=400
        )
        
        return fig
    
    return None

def create_confidence_chart(jung: ClaudeJung) -> Optional[go.Figure]:
    """Cria gráfico de confiança dos fatos"""
    try:
        all_facts = jung.memory.vector_store.get()
        
        if not all_facts or not all_facts.get('metadatas'):
            return None
        
        metadatas = all_facts.get('metadatas', [])
        confidences = [float(m.get('confidence', 0.5)) for m in metadatas]
        
        if not confidences:
            return None
        
        fig = go.Figure(data=[
            go.Histogram(
                x=confidences,
                nbinsx=20,
                marker_color='rgb(118, 75, 162)',
            )
        ])
        
        fig.update_layout(
            title="Distribuição de Confiança dos Fatos",
            xaxis_title="Confiança",
            yaxis_title="Quantidade",
            template="plotly_dark",
            height=400
        )
        
        return fig
    except Exception as e:
        logger.error(f"Erro ao criar gráfico de confiança: {e}")
        return None

def create_timeline_chart(conversations: List) -> Optional[go.Figure]:
    """Cria linha do tempo das conversas"""
    if not conversations:
        return None
    
    dates = []
    message_counts = []
    
    for conv in conversations:
        dates.append(conv.start_time)
        message_counts.append(len(conv.messages))
    
    fig = go.Figure(data=[
        go.Scatter(
            x=dates,
            y=message_counts,
            mode='lines+markers',
            marker=dict(size=10, color='rgb(102, 126, 234)'),
            line=dict(color='rgb(118, 75, 162)', width=2)
        )
    ])
    
    fig.update_layout(
        title="Linha do Tempo das Conversas",
        xaxis_title="Data",
        yaxis_title="Mensagens por Conversa",
        template="plotly_dark",
        height=400
    )
    
    return fig

# =============================================================================
# COMPONENTES DA INTERFACE
# =============================================================================

def render_header():
    """Renderiza cabeçalho da página"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='font-size: 3rem; margin: 0;'>🧠 CLAUDE JUNG v2.0</h1>
            <p style='font-size: 1.2rem; color: #888; margin-top: 0.5rem;'>
                Sistema de Memória Persistente com IA
            </p>
        </div>
        """, unsafe_allow_html=True)

def render_sidebar(jung: ClaudeJung):
    """Renderiza barra lateral com controles"""
    with st.sidebar:
        st.markdown("## ⚙️ Configurações")
        
        # Seletor de modo de conversa
        mode = st.selectbox(
            "Modo de Conversa",
            options=[m.value for m in ConversationMode],
            index=0
        )
        
        st.session_state.conversation_mode = ConversationMode(mode)
        
        st.markdown("---")
        
        # Estatísticas rápidas
        st.markdown("## 📊 Estatísticas")
        
        stats = jung.get_stats()
        mem_stats = stats.get('memory', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total de Fatos", mem_stats.get('total_facts', 0))
            st.metric("Conversas", stats.get('conversations', 0))
        
        with col2:
            st.metric("Confiança Média", f"{mem_stats.get('avg_confidence', 0):.2f}")
            cache_stats = mem_stats.get('cache_stats', {})
            st.metric("Hit Rate", f"{cache_stats.get('hit_rate', 0)*100:.0f}%")
        
        st.markdown("---")
        
        # Controles
        st.markdown("## 🎛️ Controles")
        
        if st.button("🔄 Consolidar Memória", use_container_width=True):
            with st.spinner("Consolidando memória..."):
                removed = jung.memory.consolidate_memory()
                st.success(f"✅ {removed} fatos consolidados!")
        
        if st.button("💾 Salvar Estado", use_container_width=True):
            jung.save()
            st.success("✅ Estado salvo!")
        
        if st.button("🗑️ Limpar Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation = None
            st.rerun()
        
        st.markdown("---")
        
        # Assistentes Psíquicos
        if jung.psychic_assistants:
            st.markdown("## 🔮 Assistentes Psíquicos")
            
            for name, assistant in jung.psychic_assistants.assistants.items():
                emoji = "🟢" if assistant.mode == PsychicMode.ACTIVE else "⚫"
                st.markdown(f"{emoji} **{assistant.name}**")
                st.caption(f"_{assistant.role}_")

def render_chat(jung: ClaudeJung):
    """Renderiza área de chat"""
    st.markdown("## 💬 Conversa")
    
    # Container para mensagens
    chat_container = st.container()
    
    # Renderizar histórico
    with chat_container:
        for msg in st.session_state.messages:
            role = msg['role']
            content = msg['content']
            
            if role == "user":
                st.markdown(f"""
                <div class="chat-message user">
                    <strong>👤 Você:</strong><br>
                    {content}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant">
                    <strong>🧠 Claude Jung:</strong><br>
                    {content}
                </div>
                """, unsafe_allow_html=True)
    
    # Input de mensagem
    user_input = st.chat_input("Digite sua mensagem...")
    
    if user_input:
        # Adicionar mensagem do usuário
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Processar com Claude Jung
        with st.spinner("🤔 Pensando..."):
            # Criar ou usar conversa existente
            if st.session_state.conversation is None:
                st.session_state.conversation = jung.start_conversation(
                    st.session_state.conversation_mode
                )
            
            # Gerar resposta
            response = jung.chat(
                user_input,
                st.session_state.conversation
            )
            
            # Adicionar resposta
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })
        
        # Recarregar página para mostrar nova mensagem
        st.rerun()

def render_memories_tab(jung: ClaudeJung):
    """Renderiza aba de memórias"""
    st.markdown("## 🧠 Memórias Armazenadas")
    
    # ✅ CORREÇÃO: Buscar fatos corretamente
    try:
        # Tentar acessar os fatos do banco vetorial
        all_facts = jung.memory.vector_store.get()
        
        if not all_facts or not all_facts.get('metadatas'):
            st.info("Nenhuma memória armazenada ainda. Comece uma conversa!")
            return
        
        # Converter para lista de dicionários
        facts_data = []
        metadatas = all_facts.get('metadatas', [])
        documents = all_facts.get('documents', [])
        
        for i, metadata in enumerate(metadatas):
            fact_dict = {
                'content': documents[i] if i < len(documents) else '',
                'type': metadata.get('type', 'personal'),
                'confidence': float(metadata.get('confidence', 0.5)),
                'importance': float(metadata.get('importance', 0.5)),
                'timestamp': metadata.get('timestamp', datetime.now().isoformat()),
                'source': metadata.get('source', 'unknown')
            }
            facts_data.append(fact_dict)
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar memórias: {e}")
        logger.error(f"Erro em render_memories_tab: {e}", exc_info=True)
        return
    
    if not facts_data:
        st.info("Nenhuma memória armazenada ainda. Comece uma conversa!")
        return
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fact_type_filter = st.multiselect(
            "Filtrar por Tipo",
            options=[ft.value for ft in FactType],
            default=[]
        )
    
    with col2:
        min_confidence = st.slider(
            "Confiança Mínima",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1
        )
    
    with col3:
        search_query = st.text_input("🔍 Buscar em memórias")
    
    # Filtrar fatos
    filtered_facts = facts_data
    
    if fact_type_filter:
        filtered_facts = [
            f for f in filtered_facts
            if f['type'] in fact_type_filter
        ]
    
    filtered_facts = [
        f for f in filtered_facts
        if f['confidence'] >= min_confidence
    ]
    
    if search_query:
        filtered_facts = [
            f for f in filtered_facts
            if search_query.lower() in f['content'].lower()
        ]
    
    # Mostrar estatísticas
    st.markdown(f"**Total:** {len(filtered_facts)} fatos encontrados")
    
    # Mostrar fatos
    sorted_facts = sorted(filtered_facts, key=lambda x: x['importance'], reverse=True)[:50]
    
    for fact in sorted_facts:
        # Converter tipo string para FactType
        try:
            fact_type_obj = FactType(fact['type'])
        except:
            fact_type_obj = FactType.PERSONAL
        
        fact_type_display = format_fact_type(fact_type_obj)
        
        with st.expander(f"{fact_type_display} {fact['content'][:100]}..."):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Conteúdo:** {fact['content']}")
                st.markdown(f"**Fonte:** {fact['source']}")
            
            with col2:
                st.metric("Confiança", f"{fact['confidence']:.2f}")
                st.metric("Importância", f"{fact['importance']:.2f}")
                
                # Formatar timestamp
                try:
                    if isinstance(fact['timestamp'], str):
                        timestamp = datetime.fromisoformat(fact['timestamp'])
                    else:
                        timestamp = fact['timestamp']
                    st.markdown(f"**Criado:** {timestamp.strftime('%Y-%m-%d %H:%M')}")
                except:
                    st.markdown(f"**Criado:** {fact['timestamp']}")

def render_analytics_tab(jung: ClaudeJung):
    """Renderiza aba de análises"""
    st.markdown("## 📊 Análises e Insights")
    
    stats = jung.get_stats()
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de tipos de fatos
        fig1 = create_stats_chart(stats)
        if fig1:
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Nenhum dado disponível para gráfico de tipos de fatos")
    
    with col2:
        # Gráfico de confiança
        fig2 = create_confidence_chart(jung)
        if fig2:
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Nenhum dado disponível para gráfico de confiança")
    
    # Timeline de conversas
    fig3 = create_timeline_chart(jung.memory.conversations)
    if fig3:
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Nenhuma conversa registrada ainda")
    
    # Insights dos assistentes
    if jung.psychic_assistants:
        st.markdown("### 🔮 Insights dos Assistentes Psíquicos")
        
        insights = jung.psychic_assistants.get_active_insights()
        
        if insights:
            for name, assistant_insights in insights.items():
                with st.expander(f"**{name}**", expanded=True):
                    for insight in assistant_insights:
                        st.markdown(f"💭 _{insight}_")
        else:
            st.info("Nenhum insight disponível ainda. Continue conversando!")

def render_settings_tab(jung: ClaudeJung):
    """Renderiza aba de configurações"""
    st.markdown("## ⚙️ Configurações Avançadas")
    
    # Configurações do sistema
    st.markdown("### 🔧 Parâmetros do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_temp = st.slider(
            "Temperatura",
            min_value=0.0,
            max_value=2.0,
            value=jung.config.temperature,
            step=0.1
        )
        jung.config.temperature = new_temp
        
        new_top_k = st.number_input(
            "Top-K (busca)",
            min_value=1,
            max_value=50,
            value=jung.config.search_top_k
        )
        jung.config.search_top_k = new_top_k
    
    with col2:
        new_tokens = st.number_input(
            "Max Tokens",
            min_value=100,
            max_value=4096,
            value=jung.config.max_tokens
        )
        jung.config.max_tokens = new_tokens
        
        psychic_enabled = st.checkbox(
            "Assistentes Psíquicos",
            value=jung.config.enable_psychic_assistants
        )
        jung.config.enable_psychic_assistants = psychic_enabled
    
    st.markdown("---")
    
    # Exportar/Importar
    st.markdown("### 💾 Backup e Restauração")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Exportar Memórias (JSON)", use_container_width=True):
            try:
                all_facts = jung.memory.vector_store.get()
                
                export_data = {
                    'facts': [],
                    'conversations': len(jung.memory.conversations),
                    'exported_at': datetime.now().isoformat()
                }
                
                if all_facts and all_facts.get('metadatas'):
                    metadatas = all_facts.get('metadatas', [])
                    documents = all_facts.get('documents', [])
                    
                    for i, metadata in enumerate(metadatas):
                        export_data['facts'].append({
                            'content': documents[i] if i < len(documents) else '',
                            'type': metadata.get('type', 'personal'),
                            'confidence': float(metadata.get('confidence', 0.5)),
                            'importance': float(metadata.get('importance', 0.5)),
                            'timestamp': metadata.get('timestamp', datetime.now().isoformat())
                        })
                
                st.download_button(
                    label="💾 Download",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"claude_jung_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ Erro ao exportar: {e}")
    
    with col2:
        uploaded_file = st.file_uploader("📤 Importar Memórias", type=['json'])
        if uploaded_file:
            st.warning("⚠️ Funcionalidade de importação em desenvolvimento")

# =============================================================================
# APLICAÇÃO PRINCIPAL
# =============================================================================

def main():
    """Função principal da aplicação"""
    
    # Inicializar sistema
    jung = initialize_jung()
    
    # Inicializar session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'conversation' not in st.session_state:
        st.session_state.conversation = None
    
    if 'conversation_mode' not in st.session_state:
        st.session_state.conversation_mode = ConversationMode.CASUAL
    
    # Renderizar cabeçalho
    render_header()
    
    # Renderizar sidebar
    render_sidebar(jung)
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs([
        "💬 Chat",
        "🧠 Memórias",
        "📊 Análises",
        "⚙️ Configurações"
    ])
    
    with tab1:
        render_chat(jung)
    
    with tab2:
        render_memories_tab(jung)
    
    with tab3:
        render_analytics_tab(jung)
    
    with tab4:
        render_settings_tab(jung)

# =============================================================================
# PONTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    main()