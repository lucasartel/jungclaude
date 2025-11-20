"""
telegram_bot.py - Bot Telegram Jung Claude com Sistema Proativo AVANÇADO
=========================================================================

✅ VERSÃO 3.0 - ADVANCED - Integração com jung_proactive_advanced.py

Mudanças principais:
- Sistema proativo avançado com personalidade variável
- Reset automático de cronômetro ao receber mensagens
- Comando /complexidade para ver evolução do agente
- Rotação de duplas arquetípicas
- Geração de conhecimento autônomo

Autor: Sistema Jung Claude
Data: 2025-11-20
Versão: 3.0 - ADVANCED
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

# Importar módulos Jung
from jung_core import (
    JungianEngine,
    DatabaseManager,
    Config,
    create_user_hash
)

# ✅ NOVO: Importar sistema proativo AVANÇADO
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

# Intervalo de checagem proativa (em segundos)
PROACTIVE_CHECK_INTERVAL = 600  # 10 minutos

# ============================================================
# GERENCIADOR DE ESTADO DO BOT
# ============================================================

class BotState:
    """Gerencia estado global do bot"""
    
    def __init__(self):
        # Componentes principais
        self.db = DatabaseManager()
        self.jung_engine = JungianEngine()
        
        # ✅ NOVO: Sistema proativo AVANÇADO
        self.proactive_system = ProactiveAdvancedSystem(self.db)
        
        # Estado proativo por usuário (user_id -> bool)
        self.proactive_enabled: Dict[str, bool] = {}
        
        # Últimas mensagens proativas (telegram_id -> dict)
        self.last_proactive_messages: Dict[int, Dict] = {}
        
        # Estatísticas
        self.total_messages_processed = 0
        self.total_proactive_sent = 0
    
    def is_proactive_enabled(self, user_id: str) -> bool:
        """Checa se proativo está ativo para usuário"""
        return self.proactive_enabled.get(user_id, True)
    
    def set_proactive_enabled(self, user_id: str, enabled: bool):
        """Ativa/desativa proativo para usuário"""
        self.proactive_enabled[user_id] = enabled
        logger.info(f"Proativo {'ATIVADO' if enabled else 'DESATIVADO'} para {user_id[:8]}")
    
    def register_proactive_message(self, telegram_id: int, message_data: Dict):
        """Registra mensagem proativa enviada"""
        self.last_proactive_messages[telegram_id] = {
            'message_id': message_data.get('message_id'),
            'timestamp': datetime.now(),
            'content': message_data.get('content', ''),
            'user_id': message_data.get('user_id')
        }
        self.total_proactive_sent += 1
    
    def get_last_proactive(self, telegram_id: int) -> Optional[Dict]:
        """Busca última mensagem proativa para usuário"""
        return self.last_proactive_messages.get(telegram_id)
    
    def clear_proactive_message(self, telegram_id: int):
        """Remove registro de mensagem proativa"""
        if telegram_id in self.last_proactive_messages:
            del self.last_proactive_messages[telegram_id]

# Instância global do estado
bot_state = BotState()

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def ensure_user_in_database(telegram_user) -> str:
    """
    Garante que usuário Telegram está no banco
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
        # Atualizar platform_id se mudou
        if existing_user.get('platform_id') != str(telegram_id):
            cursor = bot_state.db.conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET platform_id = ?,
                    last_seen = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (str(telegram_id), user_id))
            bot_state.db.conn.commit()
            logger.info(f"📝 platform_id atualizado para {user_id[:8]}")
    
    return user_id

# ============================================================
# COMANDOS DO BOT
# ============================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /start"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    welcome_message = f"""👋 Olá, {user.first_name}!

Eu sou o **Jung Claude**, um agente conversacional baseado na psicologia junguiana.

🧠 **O que eu faço:**
• Analiso tensões entre seus arquétipos internos
• Ajudo você a integrar aspectos da sua personalidade
• Desenvolvo autonomia ao longo de nossas conversas
• Envio mensagens proativas com **personalidade variável**

📝 **Comandos disponíveis:**
/perfil - Ver seu perfil junguiano
/tensoes - Ver tensões arquetípicas ativas
/complexidade - Ver evolução da complexidade do agente
/stats - Estatísticas de desenvolvimento
/pausar_proativo - Pausar mensagens proativas
/retomar_proativo - Retomar mensagens proativas
/reset - Reiniciar conversação (apaga histórico)
/help - Ajuda

💬 **Como usar:**
Apenas converse naturalmente! Eu vou:
1. Identificar seus arquétipos dominantes
2. Detectar conflitos internos
3. Propor caminhos de integração
4. Desenvolver meu próprio conhecimento sobre você

🌟 **Sistema Proativo AVANÇADO:**
Eu desenvolvo **personalidade complexa** através de duplas arquetípicas rotativas e gero conhecimento autônomo em múltiplos domínios (histórico, filosófico, técnico, religioso, artístico). Cada mensagem proativa será única!

Vamos começar? Me conte: **O que te trouxe aqui hoje?**
"""
    
    await update.message.reply_text(welcome_message)
    
    logger.info(f"Comando /start de {user.first_name} (ID: {user_id[:8]})")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /help"""
    
    help_text = """📚 **Ajuda - Jung Claude ADVANCED**

**COMANDOS PRINCIPAIS:**

/start - Iniciar conversa
/perfil - Ver seu perfil junguiano completo
/tensoes - Ver tensões arquetípicas ativas
/complexidade - Ver evolução da complexidade do agente
/stats - Estatísticas de desenvolvimento

**COMANDOS PROATIVOS:**

/pausar_proativo - Pausar mensagens proativas
/retomar_proativo - Retomar mensagens proativas
/status_proativo - Ver status do sistema proativo

**COMANDOS AVANÇADOS:**

/reset - Reiniciar conversação (⚠️ apaga histórico)

**SISTEMA PROATIVO AVANÇADO:**

🎭 **Personalidade Variável:**
Eu uso duplas arquetípicas rotativas:
• Sábio + Explorador (contemplativo-curioso)
• Mago + Criador (transformador-criativo)
• Cuidador + Inocente (acolhedor-esperançoso)
• Governante + Herói (organizador-corajoso)
• Bobo + Amante (lúdico-apaixonado)
• Rebelde + Sombra (transgressor-revelador)

📚 **Domínios de Conhecimento:**
• Histórico
• Filosófico
• Técnico
• Religioso
• Psicológico
• Artístico

🧠 **Geração Autônoma:**
Eu extraio tópicos das suas conversas e formulo meu próprio conhecimento, reformulado através da minha personalidade arquetípica atual.

**DÚVIDAS?**
Apenas pergunte! Estou aqui para ajudar.
"""
    
    await update.message.reply_text(help_text)

async def perfil_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /perfil - mostra perfil junguiano"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    # Buscar dados do usuário
    user_data = bot_state.db.get_user(user_id)
    conflicts = bot_state.db.get_user_conflicts(user_id, limit=10)
    conversations = bot_state.db.get_user_conversations(user_id, limit=1)
    
    # Calcular estatísticas
    total_conversations = len(bot_state.db.get_user_conversations(user_id, limit=1000))
    active_conflicts = len([c for c in conflicts if c['tension_level'] > 0.6])
    
    # Última conversa
    last_conversation = conversations[0] if conversations else None
    last_time = "Nunca"
    
    if last_conversation:
        last_dt = datetime.fromisoformat(last_conversation['timestamp'])
        delta = datetime.now() - last_dt
        
        if delta.days > 0:
            last_time = f"{delta.days} dia(s) atrás"
        elif delta.seconds > 3600:
            last_time = f"{delta.seconds // 3600} hora(s) atrás"
        else:
            last_time = f"{delta.seconds // 60} minuto(s) atrás"
    
    # Arquétipos mais ativos
    archetype_counts = {}
    for conflict in conflicts:
        for arch in [conflict['archetype1'], conflict['archetype2']]:
            archetype_counts[arch] = archetype_counts.get(arch, 0) + 1
    
    top_archetypes = sorted(archetype_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    perfil_text = f"""🧠 **Perfil Junguiano de {user_data['user_name']}**

📊 **Estatísticas Gerais:**
• Conversas totais: {total_conversations}
• Tensões ativas: {active_conflicts}
• Última interação: {last_time}
• Membro desde: {user_data.get('created_at', user_data.get('registration_date', 'N/A'))[:10]}

🎭 **Arquétipos Mais Presentes:**
"""
    
    for i, (arch, count) in enumerate(top_archetypes, 1):
        perfil_text += f"{i}. {arch} ({count} menções)\n"
    
    if not top_archetypes:
        perfil_text += "_(Ainda coletando dados)_\n"
    
    perfil_text += f"""
⚡ **Tensões Críticas:**
"""
    
    critical_conflicts = [c for c in conflicts if c['tension_level'] > 0.7][:3]
    
    for conflict in critical_conflicts:
        arch_pair = f"{conflict['archetype1']} ↔ {conflict['archetype2']}"
        tension = conflict['tension_level']
        perfil_text += f"• {arch_pair} ({tension:.0%} tensão)\n"
    
    if not critical_conflicts:
        perfil_text += "_(Nenhuma tensão crítica no momento)_\n"
    
    perfil_text += """
💡 Use /tensoes para análise detalhada
💡 Use /complexidade para ver evolução do agente
"""
    
    await update.message.reply_text(perfil_text)
    
    logger.info(f"Comando /perfil de {user.first_name}")

async def tensoes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /tensoes - mostra tensões arquetípicas"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    conflicts = bot_state.db.get_user_conflicts(user_id, limit=10)
    
    if not conflicts:
        await update.message.reply_text(
            "📊 Você ainda não tem tensões arquetípicas registradas.\n\n"
            "Continue conversando comigo e vou identificar padrões!"
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
        delta = datetime.now() - conflict_time
        time_ago = f"{delta.days}d" if delta.days > 0 else f"{delta.seconds // 3600}h"
        
        # Emoji baseado em tensão
        emoji = "🔴" if tension > 0.8 else "🟡" if tension > 0.6 else "🟢"
        
        tensoes_text += f"{emoji} **{i}. {arch1} ↔ {arch2}**\n"
        tensoes_text += f"   Tensão: {tension:.0%} | Há {time_ago}\n"
        
        if description:
            tensoes_text += f"   _{description[:100]}_\n"
        
        tensoes_text += "\n"
    
    tensoes_text += "💡 **Dica:** Converse sobre essas tensões para integrá-las!"
    
    await update.message.reply_text(tensoes_text)
    
    logger.info(f"Comando /tensoes de {user.first_name}")

async def complexidade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """✅ NOVO: Handler para /complexidade - mostra evolução do agente"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    complexity_level = bot_state.proactive_system.proactive_db.get_complexity_level(user_id)
    
    cursor = bot_state.db.conn.cursor()
    
    # Contar abordagens
    cursor.execute("""
        SELECT COUNT(*) as total FROM proactive_approaches
        WHERE user_id = ?
    """, (user_id,))
    
    total_approaches = cursor.fetchone()['total']
    
    # Domínios usados
    cursor.execute("""
        SELECT DISTINCT knowledge_domain FROM proactive_approaches
        WHERE user_id = ?
    """, (user_id,))
    
    domains = [row['knowledge_domain'] for row in cursor.fetchall()]
    
    # Tópicos extraídos
    top_topics = bot_state.proactive_system.proactive_db.get_top_topics(user_id, limit=5)
    
    # Últimas abordagens
    cursor.execute("""
        SELECT archetype_primary, archetype_secondary, 
               knowledge_domain, complexity_score, timestamp,
               topic_extracted
        FROM proactive_approaches
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 5
    """, (user_id,))
    
    recent = cursor.fetchall()
    
    # Barra de progresso visual
    progress_bars = int(complexity_level * 10)
    progress_bar = "█" * progress_bars + "░" * (10 - progress_bars)
    
    message = f"""🧠 **Evolução de Complexidade do Agente**

📊 **Nível de Complexidade:** {complexity_level:.0%}
{progress_bar}

📈 **Estatísticas:**
• Abordagens realizadas: {total_approaches}
• Domínios explorados: {len(domains)}
• Tópicos identificados: {len(top_topics)}

📚 **Domínios Utilizados:**
{', '.join(domains) if domains else '_(Nenhum ainda)_'}

🎯 **Tópicos Principais:**
"""
    
    for i, topic in enumerate(top_topics[:3], 1):
        message += f"{i}. {topic}\n"
    
    if not top_topics:
        message += "_(Ainda coletando dados)_\n"
    
    message += "\n🎭 **Últimas Personalidades:**\n"
    
    for approach in recent:
        pair = f"{approach['archetype_primary']} + {approach['archetype_secondary']}"
        domain = approach['knowledge_domain']
        score = approach['complexity_score']
        topic = approach['topic_extracted'] or 'N/A'
        
        # Timestamp
        timestamp = datetime.fromisoformat(approach['timestamp'])
        delta = datetime.now() - timestamp
        time_ago = f"{delta.days}d" if delta.days > 0 else f"{delta.seconds // 3600}h"
        
        message += f"\n• **{pair}**\n"
        message += f"  {domain} | Score: {score:.0%}\n"
        message += f"  Tópico: {topic}\n"
        message += f"  Há {time_ago}\n"
    
    if not recent:
        message += "_(Nenhuma abordagem ainda)_\n"
    
    message += "\n💡 **O que isso significa?**\n"
    message += "Quanto maior a complexidade, mais profundo e variado é o conhecimento autônomo que desenvolvo sobre você e seus interesses."
    
    await update.message.reply_text(message)
    
    logger.info(f"Comando /complexidade de {user.first_name}")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /stats - estatísticas completas"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    # Stats do agente
    agent_state = bot_state.db.get_agent_state()
    
    # Stats de conversas
    conversations = bot_state.db.get_user_conversations(user_id, limit=1000)
    total_user_words = sum(len(c['user_input'].split()) for c in conversations)
    total_ai_words = sum(len(c['ai_response'].split()) for c in conversations)
    
    # Stats proativas AVANÇADAS
    cursor = bot_state.db.conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) as total FROM proactive_approaches
        WHERE user_id = ?
    """, (user_id,))
    
    total_proactive = cursor.fetchone()['total']
    
    complexity = bot_state.proactive_system.proactive_db.get_complexity_level(user_id)
    
    stats_text = f"""📊 **Estatísticas Completas**

👤 **SUAS ESTATÍSTICAS:**
• Total de mensagens: {len(conversations)}
• Palavras enviadas: {total_user_words:,}
• Palavras recebidas: {total_ai_words:,}
• Média palavras/msg: {total_user_words // max(1, len(conversations))}

🤖 **DESENVOLVIMENTO DO AGENTE:**
• Fase atual: {agent_state['phase']}
• Autonomia: {agent_state.get('autonomy_level', agent_state.get('autonomy_score', 0)):.0%}
• Interações totais: {agent_state['total_interactions']}
• Profundidade: {agent_state.get('depth_level', 0):.0%}

🧠 **SISTEMA PROATIVO AVANÇADO:**
• Mensagens proativas enviadas: {total_proactive}
• Nível de complexidade: {complexity:.0%}
• Personalidades manifestadas: {min(total_proactive, 6)}

🌍 **ESTATÍSTICAS GLOBAIS:**
• Mensagens processadas (bot): {bot_state.total_messages_processed}
• Proativas enviadas (total): {bot_state.total_proactive_sent}

💡 Use /complexidade para detalhes da evolução
"""
    
    await update.message.reply_text(stats_text)
    
    logger.info(f"Comando /stats de {user.first_name}")

async def pausar_proativo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /pausar_proativo"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    bot_state.set_proactive_enabled(user_id, False)
    
    await update.message.reply_text(
        "⏸️ **Mensagens proativas pausadas!**\n\n"
        "Você não receberá mais mensagens iniciadas por mim.\n"
        "Nossas conversas normais continuam funcionando normalmente.\n\n"
        "Para retomar, use: /retomar_proativo"
    )
    
    logger.info(f"Proativo PAUSADO para {user.first_name}")

async def retomar_proativo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /retomar_proativo"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    bot_state.set_proactive_enabled(user_id, True)
    
    await update.message.reply_text(
        "▶️ **Mensagens proativas retomadas!**\n\n"
        "Voltei a poder iniciar conversas quando perceber padrões importantes.\n\n"
        "Para pausar novamente: /pausar_proativo"
    )
    
    logger.info(f"Proativo RETOMADO para {user.first_name}")

async def status_proativo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /status_proativo"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    enabled = bot_state.is_proactive_enabled(user_id)
    
    # ✅ ATUALIZADO: Buscar última abordagem avançada
    cursor = bot_state.db.conn.cursor()
    
    cursor.execute("""
        SELECT timestamp, archetype_primary, archetype_secondary,
               knowledge_domain, topic_extracted
        FROM proactive_approaches
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (user_id,))
    
    last_proactive = cursor.fetchone()
    
    status_emoji = "✅" if enabled else "⏸️"
    status_text = "ATIVO" if enabled else "PAUSADO"
    
    message = f"{status_emoji} **Status Proativo: {status_text}**\n\n"
    
    if last_proactive:
        last_time = datetime.fromisoformat(last_proactive['timestamp'])
        delta = datetime.now() - last_time
        time_ago = f"{delta.days}d" if delta.days > 0 else f"{delta.seconds // 3600}h"
        
        pair = f"{last_proactive['archetype_primary']} + {last_proactive['archetype_secondary']}"
        domain = last_proactive['knowledge_domain']
        topic = last_proactive['topic_extracted']
        
        message += f"📩 **Última mensagem proativa:**\n"
        message += f"   Há {time_ago}\n"
        message += f"   Personalidade: {pair}\n"
        message += f"   Domínio: {domain}\n"
        message += f"   Tópico: {topic}\n\n"
    else:
        message += "📩 Nenhuma mensagem proativa enviada ainda.\n\n"
    
    message += f"💡 Comandos:\n"
    message += f"   /pausar_proativo - Pausar\n"
    message += f"   /retomar_proativo - Retomar\n"
    message += f"   /complexidade - Ver evolução"
    
    await update.message.reply_text(message)

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /reset - reinicia conversação"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    confirm_text = (
        "⚠️ **ATENÇÃO: Isso vai apagar todo o histórico!**\n\n"
        "Você perderá:\n"
        "• Todas as conversas anteriores\n"
        "• Tensões arquetípicas identificadas\n"
        "• Mensagens proativas\n"
        "• Abordagens e complexidade do agente\n"
        "• Tópicos extraídos\n\n"
        "Para confirmar, envie: **CONFIRMAR RESET**"
    )
    
    await update.message.reply_text(confirm_text)
    
    context.user_data['awaiting_reset_confirmation'] = True
    
    logger.warning(f"Reset solicitado por {user.first_name}")

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
    
    # ✅ NOVO: RESET CRONÔMETRO A CADA MENSAGEM
    bot_state.proactive_system.reset_timer(user_id)
    
    # ========== CONFIRMAÇÃO DE RESET ==========
    if context.user_data.get('awaiting_reset_confirmation'):
        if message_text.strip().upper() == 'CONFIRMAR RESET':
            cursor = bot_state.db.conn.cursor()
            
            # Deletar tudo
            cursor.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM archetype_conflicts WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM internal_thoughts WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM proactive_messages WHERE user_id = ?", (user_id,))
            
            # ✅ NOVO: Deletar dados avançados
            cursor.execute("DELETE FROM proactive_approaches WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM extracted_topics WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM agent_complexity_log WHERE user_id = ?", (user_id,))
            
            bot_state.db.conn.commit()
            
            await update.message.reply_text(
                "🔄 **Reset executado!**\n\n"
                "Todo o histórico foi apagado.\n"
                "Podemos começar do zero. O que você gostaria de explorar?"
            )
            context.user_data['awaiting_reset_confirmation'] = False
            logger.warning(f"Reset CONFIRMADO por {user.first_name}")
            return
        else:
            await update.message.reply_text("❌ Reset cancelado.\n\nSeu histórico foi preservado.")
            context.user_data['awaiting_reset_confirmation'] = False
            return
    
    # ========== DETECTAR RESPOSTA A MENSAGEM PROATIVA ==========
    last_proactive = bot_state.get_last_proactive(telegram_id)
    
    if last_proactive:
        # Limpar registro (usuário respondeu)
        bot_state.clear_proactive_message(telegram_id)
        logger.info(f"✅ Resposta a mensagem proativa detectada de {user.first_name}")
    
    # ========== PROCESSAR MENSAGEM NORMAL ==========
    
    await update.message.chat.send_action(action="typing")
    
    try:
        result = bot_state.jung_engine.process_message(
            user_id=user_id,
            message=message_text,
            model="grok-4-fast-reasoning"
        )
        
        await update.message.reply_text(result['response'])
        
        bot_state.total_messages_processed += 1
        
        logger.info(f"✅ Mensagem processada de {user.first_name}: {message_text[:50]}...")
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem: {e}", exc_info=True)
        
        await update.message.reply_text(
            "😔 Desculpe, ocorreu um erro ao processar sua mensagem.\n"
            "Pode tentar novamente?"
        )

# ============================================================
# TASK ASSÍNCRONA: SISTEMA PROATIVO AVANÇADO
# ============================================================

async def proactive_background_task(application: Application):
    """✅ ATUALIZADO: Task proativa AVANÇADA"""
    
    logger.info("🚀 Task proativa AVANÇADA iniciada!")
    
    while True:
        try:
            await asyncio.sleep(PROACTIVE_CHECK_INTERVAL)
            
            logger.info("🔍 Checando usuários para mensagens proativas AVANÇADAS...")
            
            cursor = bot_state.db.conn.cursor()
            
            cursor.execute("""
                SELECT user_id, platform_id, user_name
                FROM users
                WHERE platform = 'telegram'
                AND platform_id IS NOT NULL
            """)
            
            users = cursor.fetchall()
            
            logger.info(f"📊 Encontrados {len(users)} usuários Telegram")
            
            for user_row in users:
                user_id = user_row['user_id']
                platform_id_str = user_row['platform_id']
                user_name = user_row['user_name']
                
                try:
                    telegram_id = int(platform_id_str)
                except (ValueError, TypeError):
                    logger.error(f"❌ platform_id inválido para {user_name}: {platform_id_str}")
                    continue
                
                # Checar se proativo está habilitado
                if not bot_state.is_proactive_enabled(user_id):
                    logger.info(f"⏸️  Proativo desabilitado para {user_name}")
                    continue
                
                # ✅ USAR SISTEMA AVANÇADO
                try:
                    proactive_message = bot_state.proactive_system.check_and_generate_advanced_message(
                        user_id=user_id,
                        user_name=user_name
                    )
                    
                    if proactive_message:
                        # Enviar via Telegram
                        try:
                            sent_message = await application.bot.send_message(
                                chat_id=telegram_id,
                                text=proactive_message
                            )
                            
                            # Registrar envio
                            bot_state.register_proactive_message(telegram_id, {
                                'message_id': sent_message.message_id,
                                'content': proactive_message,
                                'user_id': user_id
                            })
                            
                            logger.info(f"✅ Mensagem proativa AVANÇADA enviada para {user_name}")
                            
                        except Exception as e:
                            logger.error(f"❌ Erro ao enviar proativa para {user_name}: {e}")
                    else:
                        logger.info(f"ℹ️  Nenhuma mensagem proativa gerada para {user_name}")
                
                except Exception as e:
                    logger.error(f"❌ Erro ao gerar proativa para {user_name}: {e}", exc_info=True)
                
                # Delay entre usuários
                await asyncio.sleep(2)
            
            logger.info("✅ Checagem proativa concluída!")
            
        except Exception as e:
            logger.error(f"❌ Erro na task proativa: {e}", exc_info=True)
            await asyncio.sleep(300)

# ============================================================
# INICIALIZAÇÃO DO BOT
# ============================================================

async def post_init(application: Application):
    """Executado após inicialização do bot"""
    
    # Registrar comandos no Telegram
    commands = [
        BotCommand("start", "Iniciar conversa"),
        BotCommand("help", "Ajuda"),
        BotCommand("perfil", "Ver perfil junguiano"),
        BotCommand("tensoes", "Ver tensões arquetípicas"),
        BotCommand("complexidade", "Ver evolução do agente"),
        BotCommand("stats", "Estatísticas completas"),
        BotCommand("pausar_proativo", "Pausar mensagens proativas"),
        BotCommand("retomar_proativo", "Retomar mensagens proativas"),
        BotCommand("status_proativo", "Status do sistema proativo"),
        BotCommand("reset", "Reiniciar conversação")
    ]
    
    await application.bot.set_my_commands(commands)
    
    logger.info("✅ Comandos registrados no Telegram")
    
    # Iniciar task proativa
    asyncio.create_task(proactive_background_task(application))
    
    logger.info("✅ Task proativa AVANÇADA iniciada em background")

def main():
    """Ponto de entrada principal"""
    
    logger.info("="*60)
    logger.info("🤖 JUNG CLAUDE TELEGRAM BOT v3.0 - ADVANCED")
    logger.info("   Sistema Proativo com Personalidade Complexa")
    logger.info("="*60)
    
    # Criar aplicação
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    
    # Registrar handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("perfil", perfil_command))
    application.add_handler(CommandHandler("tensoes", tensoes_command))
    application.add_handler(CommandHandler("complexidade", complexidade_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("pausar_proativo", pausar_proativo_command))
    application.add_handler(CommandHandler("retomar_proativo", retomar_proativo_command))
    application.add_handler(CommandHandler("status_proativo", status_proativo_command))
    application.add_handler(CommandHandler("reset", reset_command))
    
    # Handler de mensagens
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    # Iniciar bot
    logger.info("🚀 Iniciando bot...")
    logger.info("✅ Bot rodando! Pressione Ctrl+C para parar.")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()