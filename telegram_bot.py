"""
telegram_bot.py - Bot Telegram Jung Claude HÍBRIDO PREMIUM
===========================================================

✅ VERSÃO 4.0.1 - HÍBRIDO PREMIUM + SISTEMA PROATIVO (CORRIGIDO)
   Integração com jung_core.py v4.0 (ChromaDB + OpenAI Embeddings + SQLite)
   Sistema Proativo Avançado com personalidades arquetípicas rotativas

Mudanças principais:
- Compatibilidade total com HybridDatabaseManager
- Busca semântica REAL via ChromaDB
- Extração automática de fatos
- Detecção de padrões comportamentais
- Sistema de desenvolvimento do agente
- Comandos aprimorados para visualização de memória
- ✅ SISTEMA PROATIVO AVANÇADO (jung_proactive_advanced.py)
- 🔧 CORREÇÃO: send_to_xai() agora usa argumento 'prompt' corretamente

Autor: Sistema Jung Claude
Data: 2025-11-21
Versão: 4.0.1 - HÍBRIDO PREMIUM + PROATIVO (CORRIGIDO)
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from dotenv import load_dotenv

# Importar módulos Jung HÍBRIDOS
from jung_core import (
    JungianEngine,
    HybridDatabaseManager,
    Config,
    create_user_hash,
    format_conflict_for_display,
    format_archetype_info
)

# ✅ IMPORTAR SISTEMA PROATIVO AVANÇADO
from jung_proactive_advanced import ProactiveAdvancedSystem

# ============================================================
# CONFIGURAÇÃO DE LOGGING
# ============================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURAÇÕES
# ============================================================

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN não encontrado no .env")

# IDs de administradores (opcional)
ADMIN_IDS = Config.TELEGRAM_ADMIN_IDS

# ============================================================
# GERENCIADOR DE ESTADO DO BOT
# ============================================================

class BotState:
    """Gerencia estado global do bot HÍBRIDO + PROATIVO"""
    
    def __init__(self):
        # Componentes principais HÍBRIDOS
        self.db = HybridDatabaseManager()
        self.jung_engine = JungianEngine(db=self.db)
        
        # ✅ Sistema Proativo Avançado
        self.proactive = None  # Inicializado depois com bot instance
        
        # Histórico de chat por usuário (para contexto)
        # telegram_id -> List[Dict{"role": str, "content": str}]
        self.chat_histories: Dict[int, List[Dict]] = {}
        
        # Estatísticas
        self.total_messages_processed = 0
        self.total_semantic_searches = 0
        self.total_proactive_messages_sent = 0
        
        logger.info("✅ BotState HÍBRIDO + PROATIVO inicializado")
    
    def get_chat_history(self, telegram_id: int) -> List[Dict]:
        """Retorna histórico de chat do usuário"""
        return self.chat_histories.get(telegram_id, [])
    
    def add_to_chat_history(self, telegram_id: int, role: str, content: str):
        """Adiciona mensagem ao histórico"""
        if telegram_id not in self.chat_histories:
            self.chat_histories[telegram_id] = []
        
        self.chat_histories[telegram_id].append({
            "role": role,
            "content": content
        })
        
        # Limitar histórico a últimas 20 mensagens
        if len(self.chat_histories[telegram_id]) > 20:
            self.chat_histories[telegram_id] = self.chat_histories[telegram_id][-20:]
    
    def clear_chat_history(self, telegram_id: int):
        """Limpa histórico de chat"""
        if telegram_id in self.chat_histories:
            del self.chat_histories[telegram_id]
            logger.info(f"🗑️ Histórico limpo para telegram_id={telegram_id}")

# Instância global do estado
bot_state = BotState()

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def ensure_user_in_database(telegram_user) -> str:
    """
    Garante que usuário Telegram está no banco HÍBRIDO
    Retorna user_id (hash)
    """
    
    telegram_id = telegram_user.id
    username = telegram_user.username or f"user_{telegram_id}"
    full_name = f"{telegram_user.first_name or ''} {telegram_user.last_name or ''}".strip()
    
    user_id = create_user_hash(username)
    
    # Checar se já existe
    existing_user = bot_state.db.get_user(user_id)
    
    if not existing_user:
        bot_state.db.create_user(
            user_id=user_id,
            user_name=full_name or username,
            platform='telegram',
            platform_id=str(telegram_id)
        )
        logger.info(f"✨ Novo usuário criado: {full_name} ({user_id[:8]})")
    else:
        # Atualizar last_seen
        cursor = bot_state.db.conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET last_seen = CURRENT_TIMESTAMP,
                platform_id = ?
            WHERE user_id = ?
        """, (str(telegram_id), user_id))
        bot_state.db.conn.commit()
    
    return user_id

def format_time_delta(dt: datetime) -> str:
    """Formata diferença de tempo de forma amigável"""
    delta = datetime.now() - dt
    
    if delta.days > 0:
        return f"{delta.days} dia(s) atrás"
    elif delta.seconds >= 3600:
        return f"{delta.seconds // 3600} hora(s) atrás"
    elif delta.seconds >= 60:
        return f"{delta.seconds // 60} minuto(s) atrás"
    else:
        return "agora mesmo"

# ============================================================
# COMANDOS DO BOT
# ============================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /start"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    # Buscar dados do usuário
    user_data = bot_state.db.get_user(user_id)
    stats = bot_state.db.get_user_stats(user_id)
    
    is_new_user = stats and stats['total_messages'] == 0
    
    if is_new_user:
        welcome_message = f"""👋 Olá, {user.first_name}!

Bem-vindo ao **Jung Claude v4.0 HÍBRIDO PREMIUM**!

🧠 **O que eu faço:**
• Uso **ChromaDB + OpenAI Embeddings** para memória semântica avançada
• Analiso tensões entre seus arquétipos internos
• Extraio fatos estruturados das suas conversas
• Detecto padrões comportamentais ao longo do tempo
• Desenvolvo autonomia e complexidade própria
• 🌟 **Sistema Proativo**: Posso iniciar conversas quando você está inativo!

🗄️ **Arquitetura Híbrida:**
• **ChromaDB**: Busca semântica com embeddings OpenAI
• **SQLite**: Fatos, padrões, desenvolvimento do agente

📝 **Comandos disponíveis:**
/perfil - Ver seu perfil junguiano completo
/memoria - Ver memórias semânticas mais relevantes
/fatos - Ver fatos estruturados extraídos sobre você
/padroes - Ver padrões comportamentais detectados
/tensoes - Ver tensões arquetípicas ativas
/stats - Estatísticas de desenvolvimento
/arquetipo [nome] - Informações sobre um arquétipo
/reset - Reiniciar conversação (apaga histórico)
/help - Ajuda completa

💬 **Como usar:**
Apenas converse naturalmente! Eu vou:
1. Buscar semanticamente em todas as nossas conversas passadas
2. Identificar seus arquétipos dominantes
3. Detectar conflitos internos
4. Extrair fatos e padrões sobre você
5. Propor caminhos de integração
6. 🌟 Iniciar conversas quando você estiver inativo (após 10 conversas)

Vamos começar? **O que te trouxe aqui hoje?**
"""
    else:
        last_interaction = datetime.fromisoformat(stats['first_interaction'])
        time_since = format_time_delta(last_interaction)
        
        welcome_message = f"""🌟 Olá novamente, {user.first_name}!

📊 **Suas estatísticas:**
• Conversas: {stats['total_messages']}
• Primeira interação: {time_since}
• Sessões: {user_data.get('total_sessions', 1)}

🧠 Tenho memórias semânticas e fatos estruturados sobre você.

Use /memoria para ver memórias relevantes ou /fatos para ver o que aprendi sobre você.

**No que posso ajudar hoje?**
"""
    
    await update.message.reply_text(welcome_message)
    
    logger.info(f"Comando /start de {user.first_name} (ID: {user_id[:8]})")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /help"""
    
    help_text = """📚 **Ajuda - Jung Claude v4.0 HÍBRIDO PREMIUM**

**COMANDOS PRINCIPAIS:**

/start - Iniciar/Reiniciar conversa
/perfil - Ver seu perfil junguiano completo
/memoria - Ver memórias semânticas mais relevantes
/fatos - Ver fatos estruturados extraídos sobre você
/padroes - Ver padrões comportamentais detectados
/tensoes - Ver tensões arquetípicas ativas

**COMANDOS DE ANÁLISE:**

/stats - Estatísticas de desenvolvimento do agente
/arquetipo [nome] - Informações sobre um arquétipo
/buscar [termo] - Buscar semanticamente nas memórias

**COMANDOS AVANÇADOS:**

/reset - Reiniciar conversação (⚠️ apaga histórico)
/limpar_chat - Limpar apenas histórico da conversa atual

**SISTEMA HÍBRIDO:**

🗄️ **ChromaDB:**
Uso OpenAI Embeddings (text-embedding-3-small) para busca semântica REAL. Quando você fala sobre algo, busco em todas as nossas conversas passadas temas similares.

🗄️ **SQLite:**
Extraio e armazeno fatos estruturados:
• Profissão, empresa, formação
• Traços de personalidade
• Preferências (música, filmes, comida...)
• Relacionamentos
• Eventos da vida

🧠 **Detecção de Padrões:**
Analiso suas conversas para identificar padrões recorrentes e temas que aparecem frequentemente.

🌟 **Sistema Proativo:**
Após 10 conversas, posso iniciar conversas quando você está inativo (12h+). Cada mensagem proativa usa uma personalidade arquetípica diferente e conhecimento autônomo sobre tópicos do seu interesse!

**DÚVIDAS?**
Apenas pergunte! Estou aqui para ajudar.
"""
    
    await update.message.reply_text(help_text)

async def perfil_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /perfil - mostra perfil junguiano completo"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    # Buscar dados
    user_data = bot_state.db.get_user(user_id)
    stats = bot_state.db.get_user_stats(user_id)
    conflicts = bot_state.db.get_user_conflicts(user_id, limit=10)
    
    # Buscar fatos
    cursor = bot_state.db.conn.cursor()
    cursor.execute("""
        SELECT fact_category, COUNT(*) as count
        FROM user_facts
        WHERE user_id = ? AND is_current = 1
        GROUP BY fact_category
    """, (user_id,))
    
    facts_by_category = {row['fact_category']: row['count'] for row in cursor.fetchall()}
    
    # Buscar padrões
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM user_patterns
        WHERE user_id = ? AND confidence_score > 0.6
    """, (user_id,))
    
    pattern_count = cursor.fetchone()['count']
    
    # Arquétipos mais ativos
    archetype_counts = {}
    for conflict in conflicts:
        for arch in [conflict['archetype1'], conflict['archetype2']]:
            archetype_counts[arch] = archetype_counts.get(arch, 0) + 1
    
    top_archetypes = sorted(archetype_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # Tensões ativas
    active_conflicts = [c for c in conflicts if c['tension_level'] > 0.6]
    
    # Montar mensagem
    perfil_text = f"""🧠 **Perfil Junguiano de {user_data['user_name']}**

📊 **Estatísticas Gerais:**
• Conversas totais: {stats['total_messages']}
• Sessões: {stats.get('total_sessions', user_data.get('total_sessions', 1))}
• Tensões ativas: {len(active_conflicts)}
• Fatos conhecidos: {sum(facts_by_category.values())}
• Padrões detectados: {pattern_count}
• Membro desde: {user_data.get('created_at', user_data.get('registration_date', 'N/A'))[:10]}

🎭 **Arquétipos Mais Presentes:**
"""
    
    if top_archetypes:
        for i, (arch, count) in enumerate(top_archetypes, 1):
            emoji = Config.ARCHETYPES.get(arch, {}).get('emoji', '❓')
            perfil_text += f"{i}. {emoji} {arch} ({count} menções)\n"
    else:
        perfil_text += "_(Ainda coletando dados)_\n"
    
    perfil_text += f"\n📚 **Conhecimento Estruturado:**\n"
    
    for category, count in facts_by_category.items():
        perfil_text += f"• {category}: {count} fato(s)\n"
    
    if not facts_by_category:
        perfil_text += "_(Nenhum fato extraído ainda)_\n"
    
    perfil_text += f"\n⚡ **Tensões Críticas:**\n"
    
    for conflict in active_conflicts[:3]:
        arch_pair = f"{conflict['archetype1']} ↔ {conflict['archetype2']}"
        tension = conflict['tension_level']
        perfil_text += f"• {arch_pair} ({tension:.0%} tensão)\n"
    
    if not active_conflicts:
        perfil_text += "_(Nenhuma tensão crítica no momento)_\n"
    
    perfil_text += f"""
💡 **Próximos passos:**
• /memoria - Ver memórias semânticas
• /fatos - Ver fatos detalhados
• /padroes - Ver padrões comportamentais
• /tensoes - Análise detalhada de tensões
"""
    
    await update.message.reply_text(perfil_text)
    
    logger.info(f"Comando /perfil de {user.first_name}")

async def memoria_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /memoria - mostra memórias semânticas"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    # Verificar se há argumento (query)
    query = " ".join(context.args) if context.args else None
    
    if not query:
        # Sem query específica, mostrar últimas conversas
        conversations = bot_state.db.get_user_conversations(user_id, limit=5)
        
        if not conversations:
            await update.message.reply_text(
                "📚 Você ainda não tem memórias registradas.\n\n"
                "Continue conversando comigo!"
            )
            return
        
        memoria_text = "📚 **Suas Últimas Memórias:**\n\n"
        
        for i, conv in enumerate(conversations, 1):
            timestamp = datetime.fromisoformat(conv['timestamp'])
            time_ago = format_time_delta(timestamp)
            
            user_input = conv['user_input'][:80] + "..." if len(conv['user_input']) > 80 else conv['user_input']
            
            memoria_text += f"{i}. **{time_ago}**\n"
            memoria_text += f"   Você: _{user_input}_\n\n"
        
        memoria_text += "💡 Use `/memoria [termo]` para buscar semanticamente memórias sobre um tema específico"
        
    else:
        # Query específica - busca semântica
        if not bot_state.db.chroma_enabled:
            await update.message.reply_text(
                "❌ Busca semântica não disponível (ChromaDB desabilitado).\n\n"
                "Use /fatos para ver informações estruturadas."
            )
            return
        
        bot_state.total_semantic_searches += 1
        
        memories = bot_state.db.semantic_search(user_id, query, k=5)
        
        if not memories:
            await update.message.reply_text(
                f"🔍 Nenhuma memória encontrada para: **{query}**\n\n"
                "Tente outro termo ou continue conversando comigo!"
            )
            return
        
        memoria_text = f"🔍 **Memórias sobre: {query}**\n\n"
        
        for i, mem in enumerate(memories, 1):
            score = mem.get('similarity_score', 0)
            timestamp = mem['timestamp'][:10] if mem.get('timestamp') else 'N/A'
            user_input = mem['user_input'][:100] + "..." if len(mem['user_input']) > 100 else mem['user_input']
            
            memoria_text += f"{i}. **Similaridade: {score:.0%}** | {timestamp}\n"
            memoria_text += f"   _{user_input}_\n\n"
        
        memoria_text += f"💡 Total de {len(memories)} memória(s) relevante(s) encontrada(s)"
    
    await update.message.reply_text(memoria_text)
    
    logger.info(f"Comando /memoria de {user.first_name} (query={query})")

async def fatos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /fatos - mostra fatos estruturados extraídos"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    cursor = bot_state.db.conn.cursor()
    
    # Buscar fatos atuais
    cursor.execute("""
        SELECT fact_category, fact_key, fact_value, first_mentioned_at
        FROM user_facts
        WHERE user_id = ? AND is_current = 1
        ORDER BY fact_category, fact_key
    """, (user_id,))
    
    facts = cursor.fetchall()
    
    if not facts:
        await update.message.reply_text(
            "📋 Ainda não extraí fatos estruturados sobre você.\n\n"
            "Continue conversando e vou identificar:\n"
            "• Profissão e formação\n"
            "• Traços de personalidade\n"
            "• Preferências\n"
            "• Relacionamentos\n"
            "• Eventos da vida"
        )
        return
    
    # Agrupar por categoria
    facts_by_category = {}
    for fact in facts:
        category = fact['fact_category']
        if category not in facts_by_category:
            facts_by_category[category] = []
        
        facts_by_category[category].append({
            'key': fact['fact_key'],
            'value': fact['fact_value'],
            'first_mentioned': fact['first_mentioned_at']
        })
    
    fatos_text = "📋 **Fatos Estruturados Sobre Você:**\n\n"
    
    category_emojis = {
        'TRABALHO': '💼',
        'PERSONALIDADE': '🎭',
        'RELACIONAMENTO': '❤️',
        'PREFERÊNCIAS': '⭐',
        'EVENTOS': '📅'
    }
    
    for category, items in facts_by_category.items():
        emoji = category_emojis.get(category, '📌')
        fatos_text += f"{emoji} **{category}:**\n"
        
        for item in items[:5]:  # Limitar a 5 por categoria
            fatos_text += f"  • {item['key']}: {item['value'][:80]}\n"
        
        if len(items) > 5:
            fatos_text += f"  _(+{len(items) - 5} outro(s))_\n"
        
        fatos_text += "\n"
    
    fatos_text += f"💡 Total de {len(facts)} fato(s) extraído(s)"
    
    await update.message.reply_text(fatos_text)
    
    logger.info(f"Comando /fatos de {user.first_name}")

async def padroes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /padroes - mostra padrões comportamentais detectados"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    cursor = bot_state.db.conn.cursor()
    
    cursor.execute("""
        SELECT pattern_name, pattern_description, frequency_count, 
               confidence_score, first_detected_at, last_occurrence_at
        FROM user_patterns
        WHERE user_id = ? AND confidence_score > 0.5
        ORDER BY confidence_score DESC, frequency_count DESC
        LIMIT 10
    """, (user_id,))
    
    patterns = cursor.fetchall()
    
    if not patterns:
        await update.message.reply_text(
            "🔍 Ainda não detectei padrões comportamentais suficientes.\n\n"
            "Padrões são identificados quando você:\n"
            "• Menciona temas recorrentes\n"
            "• Demonstra comportamentos consistentes\n"
            "• Expressa preferências repetidas\n\n"
            "Continue conversando comigo!"
        )
        return
    
    padroes_text = "🔍 **Padrões Comportamentais Detectados:**\n\n"
    
    for i, pattern in enumerate(patterns, 1):
        name = pattern['pattern_name'].replace('tema_', '')
        description = pattern['pattern_description']
        frequency = pattern['frequency_count']
        confidence = pattern['confidence_score']
        
        first = datetime.fromisoformat(pattern['first_detected_at'])
        last = datetime.fromisoformat(pattern['last_occurrence_at'])
        
        time_span = (last - first).days
        
        # Emoji baseado em confiança
        if confidence > 0.8:
            emoji = "🔴"
        elif confidence > 0.6:
            emoji = "🟡"
        else:
            emoji = "🟢"
        
        padroes_text += f"{emoji} **{i}. {name.title()}**\n"
        padroes_text += f"   {description}\n"
        padroes_text += f"   Frequência: {frequency}x | Confiança: {confidence:.0%}\n"
        padroes_text += f"   Período: {time_span} dia(s)\n\n"
    
    padroes_text += "💡 Use /memoria para ver conversas relacionadas a esses padrões"
    
    await update.message.reply_text(padroes_text)
    
    logger.info(f"Comando /padroes de {user.first_name}")

async def tensoes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /tensoes - mostra tensões arquetípicas"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    conflicts = bot_state.db.get_user_conflicts(user_id, limit=10)
    
    if not conflicts:
        await update.message.reply_text(
            "📊 Você ainda não tem tensões arquetípicas registradas.\n\n"
            "Continue conversando comigo e vou identificar conflitos internos!"
        )
        return
    
    tensoes_text = "⚡ **Suas Tensões Arquetípicas:**\n\n"
    
    for i, conflict in enumerate(conflicts[:5], 1):
        arch1 = conflict['archetype1']
        arch2 = conflict['archetype2']
        tension = conflict['tension_level']
        description = conflict.get('description', '')
        
        # Timestamp
        conflict_time = datetime.fromisoformat(conflict['timestamp'])
        time_ago = format_time_delta(conflict_time)
        
        # Emojis
        emoji1 = Config.ARCHETYPES.get(arch1, {}).get('emoji', '❓')
        emoji2 = Config.ARCHETYPES.get(arch2, {}).get('emoji', '❓')
        
        # Emoji de tensão
        if tension > 0.8:
            tension_emoji = "🔴"
        elif tension > 0.6:
            tension_emoji = "🟡"
        else:
            tension_emoji = "🟢"
        
        tensoes_text += f"{tension_emoji} **{i}. {emoji1} {arch1} ↔ {emoji2} {arch2}**\n"
        tensoes_text += f"   Tensão: {tension:.0%} | {time_ago}\n"
        
        if description:
            tensoes_text += f"   _{description[:100]}_\n"
        
        tensoes_text += "\n"
    
    tensoes_text += "💡 **Dica:** Converse sobre essas tensões para integrá-las!\n"
    tensoes_text += "💡 Use /arquetipo [nome] para entender melhor cada arquétipo"
    
    await update.message.reply_text(tensoes_text)
    
    logger.info(f"Comando /tensoes de {user.first_name}")

async def arquetipo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /arquetipo - mostra informações sobre um arquétipo"""
    
    if not context.args:
        # Listar todos os arquétipos
        arquetipo_text = "🎭 **Arquétipos Disponíveis:**\n\n"
        
        for name, info in Config.ARCHETYPES.items():
            emoji = info.get('emoji', '❓')
            description = info.get('description', '')
            
            arquetipo_text += f"{emoji} **{name}**\n"
            arquetipo_text += f"   {description}\n\n"
        
        arquetipo_text += "💡 Use `/arquetipo [nome]` para detalhes completos"
        
        await update.message.reply_text(arquetipo_text)
        return
    
    # Nome do arquétipo solicitado
    archetype_name = " ".join(context.args).title()
    
    # Buscar no dicionário
    archetype_info = None
    for name in Config.ARCHETYPES:
        if name.lower() == archetype_name.lower():
            archetype_name = name
            archetype_info = Config.ARCHETYPES[name]
            break
    
    if not archetype_info:
        await update.message.reply_text(
            f"❓ Arquétipo '{archetype_name}' não encontrado.\n\n"
            "Use /arquetipo para ver lista completa."
        )
        return
    
    info_text = format_archetype_info(archetype_name)
    
    await update.message.reply_text(info_text)
    
    logger.info(f"Comando /arquetipo {archetype_name} de {update.effective_user.first_name}")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /stats - estatísticas completas"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    # Stats do usuário
    user_data = bot_state.db.get_user(user_id)
    user_stats = bot_state.db.get_user_stats(user_id)
    
    # Stats do agente
    agent_state = bot_state.db.get_agent_state()
    
    # Stats de conversas
    conversations = bot_state.db.get_user_conversations(user_id, limit=1000)
    total_user_words = sum(len(c['user_input'].split()) for c in conversations)
    total_ai_words = sum(len(c['ai_response'].split()) for c in conversations)
    
    # Stats de fatos e padrões
    cursor = bot_state.db.conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) as count FROM user_facts
        WHERE user_id = ? AND is_current = 1
    """, (user_id,))
    total_facts = cursor.fetchone()['count']
    
    cursor.execute("""
        SELECT COUNT(*) as count FROM user_patterns
        WHERE user_id = ? AND confidence_score > 0.6
    """, (user_id,))
    total_patterns = cursor.fetchone()['count']
    
    stats_text = f"""📊 **Estatísticas Completas**

👤 **SUAS ESTATÍSTICAS:**
• Total de mensagens: {user_stats['total_messages']}
• Palavras enviadas: {total_user_words:,}
• Palavras recebidas: {total_ai_words:,}
• Média palavras/msg: {total_user_words // max(1, user_stats['total_messages'])}
• Fatos extraídos: {total_facts}
• Padrões detectados: {total_patterns}
• Sessões: {user_stats.get('total_sessions', user_data.get('total_sessions', 1))}

🤖 **DESENVOLVIMENTO DO AGENTE:**
• Fase atual: {agent_state['phase']}/5
• Auto-consciência: {agent_state['self_awareness_score']:.0%}
• Complexidade moral: {agent_state['moral_complexity_score']:.0%}
• Profundidade emocional: {agent_state['emotional_depth_score']:.0%}
• Autonomia: {agent_state['autonomy_score']:.0%}
• Interações totais: {agent_state['total_interactions']}

🗄️ **SISTEMA HÍBRIDO:**
• ChromaDB: {'ATIVO ✅' if bot_state.db.chroma_enabled else 'INATIVO ❌'}
• Buscas semânticas realizadas: {bot_state.total_semantic_searches}
• Modelo de embeddings: {Config.EMBEDDING_MODEL}

🌟 **SISTEMA PROATIVO:**
• Mensagens proativas enviadas: {bot_state.total_proactive_messages_sent}
• Status: {'ATIVO ✅' if user_stats['total_messages'] >= 10 else f'INATIVO (faltam {10 - user_stats["total_messages"]} conversas)'}

🌍 **ESTATÍSTICAS GLOBAIS DO BOT:**
• Mensagens processadas: {bot_state.total_messages_processed}

💡 Use /perfil para análise junguiana completa
💡 Use /memoria para buscar semanticamente nas conversas
"""
    
    await update.message.reply_text(stats_text)
    
    logger.info(f"Comando /stats de {user.first_name}")

async def buscar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /buscar - busca semântica"""
    
    if not context.args:
        await update.message.reply_text(
            "🔍 **Busca Semântica**\n\n"
            "Use: `/buscar [termo]`\n\n"
            "Exemplo: `/buscar trabalho`"
        )
        return
    
    query = " ".join(context.args)
    
    # Usar comando /memoria com query
    context.args = query.split()
    await memoria_command(update, context)

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /reset - reinicia conversação"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    confirm_text = (
        "⚠️ **ATENÇÃO: Isso vai apagar TODO o histórico!**\n\n"
        "Você perderá:\n"
        "• Todas as conversas anteriores\n"
        "• Tensões arquetípicas identificadas\n"
        "• Fatos estruturados extraídos\n"
        "• Padrões comportamentais detectados\n"
        "• Memórias semânticas no ChromaDB\n\n"
        "Para confirmar, envie: **CONFIRMAR RESET**"
    )
    
    await update.message.reply_text(confirm_text)
    
    context.user_data['awaiting_reset_confirmation'] = True
    
    logger.warning(f"Reset solicitado por {user.first_name}")

async def limpar_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /limpar_chat - limpa apenas histórico da conversa atual"""
    
    telegram_id = update.effective_user.id
    
    bot_state.clear_chat_history(telegram_id)
    
    await update.message.reply_text(
        "🗑️ **Histórico da conversa atual limpo!**\n\n"
        "Suas memórias no banco de dados foram preservadas.\n"
        "Apenas o contexto da conversa atual foi resetado."
    )
    
    logger.info(f"Chat limpo para {update.effective_user.first_name}")

# ============================================================
# HANDLER DE MENSAGENS
# ============================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler principal de mensagens de texto"""
    
    user = update.effective_user
    telegram_id = user.id
    message_text = update.message.text
    
    # Garantir usuário no banco
    user_id = ensure_user_in_database(user)
    
    # ✅ RESET CRONÔMETRO PROATIVO (importante!)
    if bot_state.proactive:
        bot_state.proactive.reset_timer(user_id)
    
    # ========== CONFIRMAÇÃO DE RESET ==========
    if context.user_data.get('awaiting_reset_confirmation'):
        if message_text.strip().upper() == 'CONFIRMAR RESET':
            cursor = bot_state.db.conn.cursor()
            
            # Deletar tudo do SQLite
            cursor.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM archetype_conflicts WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM user_facts WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM user_patterns WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM user_milestones WHERE user_id = ?", (user_id,))
            
            bot_state.db.conn.commit()
            
            # Deletar do ChromaDB (se habilitado)
            if bot_state.db.chroma_enabled:
                try:
                    # Buscar IDs dos documentos do usuário
                    results = bot_state.db.vectorstore._collection.get(
                        where={"user_id": user_id}
                    )
                    
                    if results and results.get('ids'):
                        bot_state.db.vectorstore._collection.delete(
                            ids=results['ids']
                        )
                        logger.info(f"🗑️ {len(results['ids'])} documentos removidos do ChromaDB")
                except Exception as e:
                    logger.error(f"❌ Erro ao deletar do ChromaDB: {e}")
            
            # Limpar histórico de chat
            bot_state.clear_chat_history(telegram_id)
            
            await update.message.reply_text(
                "🔄 **Reset executado!**\n\n"
                "Todo o histórico foi apagado (SQLite + ChromaDB).\n"
                "Podemos começar do zero. O que você gostaria de explorar?"
            )
            context.user_data['awaiting_reset_confirmation'] = False
            logger.warning(f"Reset CONFIRMADO por {user.first_name}")
            return
        else:
            await update.message.reply_text("❌ Reset cancelado.\n\nSeu histórico foi preservado.")
            context.user_data['awaiting_reset_confirmation'] = False
            return
    
    # ========== PROCESSAR MENSAGEM NORMAL ==========
    
    await update.message.chat.send_action(action="typing")
    
    # Adicionar ao histórico
    bot_state.add_to_chat_history(telegram_id, "user", message_text)
    
    # Buscar histórico completo
    chat_history = bot_state.get_chat_history(telegram_id)
    
    try:
        # Processar com JungianEngine (passa chat_history)
        result = bot_state.jung_engine.process_message(
            user_id=user_id,
            message=message_text,
            model="grok-4-fast-reasoning",
            chat_history=chat_history
        )
        
        response = result['response']
        
        # Adicionar resposta ao histórico
        bot_state.add_to_chat_history(telegram_id, "assistant", response)
        
        # Enviar resposta
        await update.message.reply_text(response)
        
        # Detectar padrões periodicamente
        if bot_state.total_messages_processed % 10 == 0:
            bot_state.db.detect_and_save_patterns(user_id)
        
        bot_state.total_messages_processed += 1
        
        # Log com informações de conflito
        conflict_info = ""
        if result.get('conflicts'):
            conflict_info = f" | Conflitos: {len(result['conflicts'])}"
        
        logger.info(f"✅ Mensagem processada de {user.first_name}: {message_text[:50]}...{conflict_info}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem: {e}", exc_info=True)
        
        await update.message.reply_text(
            "😔 Desculpe, ocorreu um erro ao processar sua mensagem.\n"
            "Pode tentar novamente?"
        )

# ============================================================
# ✅ SISTEMA PROATIVO - VERIFICAÇÃO PERIÓDICA
# ============================================================

async def check_inactive_users(context: ContextTypes.DEFAULT_TYPE):
    """
    Verificação periódica de usuários inativos
    Executada automaticamente pelo scheduler a cada 3 minutos (teste)
    """
    
    if not bot_state.proactive:
        logger.warning("⚠️ Sistema proativo não inicializado")
        return
    
    try:
        logger.info("="*60)
        logger.info("⏰ VERIFICAÇÃO PROATIVA INICIADA")
        logger.info("="*60)
        
        # ✅ SLEEP REMOVIDO - Scheduler já controla o intervalo
        
        logger.info("🔍 Verificando usuários para mensagens proativas...")
        
        # Buscar todos os usuários do Telegram
        all_users = bot_state.db.get_all_users(platform='telegram')
        
        logger.info(f"👥 Total de usuários: {len(all_users)}")
        
        messages_sent = 0
        
        for user in all_users:
            user_id = user['user_id']
            user_name = user['user_name']
            platform_id = user.get('platform_id')
            
            if not platform_id:
                continue
            
            try:
                telegram_id = int(platform_id)
            except (ValueError, TypeError):
                logger.warning(f"⚠️ platform_id inválido para {user_name}")
                continue
            
            # Verificar se deve enviar mensagem proativa
            proactive_message = bot_state.proactive.check_and_generate_advanced_message(
                user_id=user_id,
                user_name=user_name
            )
            
            if proactive_message:
                try:
                    await context.bot.send_message(
                        chat_id=telegram_id,
                        text=proactive_message
                    )
                    messages_sent += 1
                    bot_state.total_proactive_messages_sent += 1
                    
                    logger.info(f"📨 Mensagem proativa enviada para {user_name}")
                    
                    # Aguardar 2 segundos entre mensagens (anti-spam Telegram)
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao enviar proativa para {user_name}: {e}")
        
        if messages_sent > 0:
            logger.info(f"✅ {messages_sent} mensagem(ns) proativa(s) enviada(s)")
        else:
            logger.info("⏰ Nenhuma mensagem proativa necessária neste momento")
        
        logger.info("="*60)
        logger.info("")
            
    except Exception as e:
        logger.error(f"❌ Erro na verificação de usuários inativos: {e}", exc_info=True)

# ============================================================
# COMANDOS DE ADMINISTRAÇÃO (OPCIONAL)
# ============================================================

async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /admin_stats - estatísticas globais (apenas admins)"""
    
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Comando disponível apenas para administradores.")
        return
    
    # Buscar estatísticas globais
    all_users = bot_state.db.get_all_users(platform='telegram')
    
    total_users = len(all_users)
    total_conversations = sum(u.get('total_messages', 0) for u in all_users)
    
    # Stats do ChromaDB
    chroma_docs = 0
    if bot_state.db.chroma_enabled:
        try:
            all_docs = bot_state.db.vectorstore._collection.get()
            chroma_docs = len(all_docs.get('documents', []))
        except:
            pass
    
    # Stats do agente
    agent_state = bot_state.db.get_agent_state()
    
    admin_text = f"""👑 **Estatísticas Administrativas**

👥 **USUÁRIOS:**
• Total de usuários: {total_users}
• Conversas totais: {total_conversations}
• Média conversas/usuário: {total_conversations // max(1, total_users)}

🗄️ **BANCO DE DADOS:**
• ChromaDB: {'ATIVO ✅' if bot_state.db.chroma_enabled else 'INATIVO ❌'}
• Documentos no ChromaDB: {chroma_docs}
• Buscas semânticas: {bot_state.total_semantic_searches}

🤖 **AGENTE:**
• Fase: {agent_state['phase']}/5
• Interações totais: {agent_state['total_interactions']}
• Autonomia: {agent_state['autonomy_score']:.0%}

🌟 **SISTEMA PROATIVO:**
• Mensagens enviadas: {bot_state.total_proactive_messages_sent}

🌍 **BOT:**
• Mensagens processadas: {bot_state.total_messages_processed}
"""
    
    await update.message.reply_text(admin_text)
    
    logger.info(f"Comando /admin_stats de admin ID={user_id}")

# ============================================================
# INICIALIZAÇÃO DO BOT
# ============================================================

async def post_init(application: Application):
    """Executado após inicialização do bot"""
    
    # Registrar comandos no Telegram
    commands = [
        BotCommand("start", "Iniciar conversa"),
        BotCommand("help", "Ajuda completa"),
        BotCommand("perfil", "Ver perfil junguiano"),
        BotCommand("memoria", "Ver memórias semânticas"),
        BotCommand("fatos", "Ver fatos estruturados"),
        BotCommand("padroes", "Ver padrões comportamentais"),
        BotCommand("tensoes", "Ver tensões arquetípicas"),
        BotCommand("stats", "Estatísticas completas"),
        BotCommand("arquetipo", "Info sobre arquétipo"),
        BotCommand("buscar", "Buscar semanticamente"),
        BotCommand("limpar_chat", "Limpar histórico da conversa"),
        BotCommand("reset", "Reiniciar conversação")
    ]
    
    await application.bot.set_my_commands(commands)
    logger.info("✅ Comandos registrados no Telegram")
    
    # ✅ INICIALIZAR SISTEMA PROATIVO
    bot_state.proactive = ProactiveAdvancedSystem(bot_state.db)
    logger.info("✅ Sistema Proativo Avançado inicializado")
    
    # ✅ CONFIGURAR SCHEDULER (verificar a cada 3 minutos - TESTE)
    job_queue = application.job_queue
    job_queue.run_repeating(
        check_inactive_users,
        interval=180,  # 3 minutos em segundos (180s)
        first=60  # Primeira verificação após 1 minuto
    )
    
    logger.info("✅ Scheduler proativo ativado (verificação a cada 3min - TESTE)")

def main():
    """Ponto de entrada principal"""
    
    logger.info("="*60)
    logger.info("🤖 JUNG CLAUDE TELEGRAM BOT v4.0.1 - HÍBRIDO PREMIUM + PROATIVO")
    logger.info("   ChromaDB + OpenAI Embeddings + SQLite + Sistema Proativo")
    logger.info("   🔧 CORREÇÃO: send_to_xai() corrigido")
    logger.info("="*60)
    
    # Validar configuração
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"❌ Erro de configuração: {e}")
        return
    
    # Criar aplicação
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    
    # Registrar handlers de comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("perfil", perfil_command))
    application.add_handler(CommandHandler("memoria", memoria_command))
    application.add_handler(CommandHandler("fatos", fatos_command))
    application.add_handler(CommandHandler("padroes", padroes_command))
    application.add_handler(CommandHandler("tensoes", tensoes_command))
    application.add_handler(CommandHandler("arquetipo", arquetipo_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("buscar", buscar_command))
    application.add_handler(CommandHandler("limpar_chat", limpar_chat_command))
    application.add_handler(CommandHandler("reset", reset_command))
    
    # Comandos de administração (opcional)
    if ADMIN_IDS:
        application.add_handler(CommandHandler("admin_stats", admin_stats_command))
    
    # Handler de mensagens
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    # Iniciar bot
    logger.info("🚀 Iniciando bot...")
    logger.info(f"✅ ChromaDB: {'ATIVO' if bot_state.db.chroma_enabled else 'INATIVO'}")
    logger.info(f"✅ Modelo Embeddings: {Config.EMBEDDING_MODEL}")
    logger.info(f"✅ Sistema Proativo: ATIVO (verificação a cada 3min - TESTE)")
    logger.info("✅ Bot rodando! Pressione Ctrl+C para parar.")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()