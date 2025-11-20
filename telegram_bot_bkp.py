"""
telegram_bot.py - Bot Telegram Jung Claude com Sistema Proativo
================================================================

✅ VERSÃO CORRIGIDA - Integração completa com jung_core.py v3.2

Mudanças:
- Assinatura process_message() corrigida (sem user_name)
- Uso correto de create_user() com platform_id
- Compatível com JungianEngine() sem db explícito
- Todos os imports e chamadas validados

Autor: Sistema Jung Claude
Data: 2025-11-19
Versão: 2.1 - CORRIGIDO
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

from jung_proactive_bkp import ProactiveModule

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
PROACTIVE_CHECK_INTERVAL = 3600  # 1 hora

# ============================================================
# GERENCIADOR DE ESTADO DO BOT
# ============================================================

class BotState:
    """Gerencia estado global do bot"""
    
    def __init__(self):
        # ✅ CORRIGIDO: JungianEngine sem parâmetro db
        self.db = DatabaseManager()
        self.jung_engine = JungianEngine()  # ✅ Usa db interno
        self.proactive_module = ProactiveModule()
        
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
    ✅ CORRIGIDO: Usa create_user() com platform_id STRING
    
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
        # ✅ CORRIGIDO: Usar create_user() ao invés de register_user()
        bot_state.db.create_user(
            user_id=user_id,
            user_name=full_name or username,
            platform='telegram',
            platform_id=str(telegram_id)  # ✅ STRING
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

def get_user_id_from_telegram_id(telegram_id: int) -> Optional[str]:
    """
    ✅ CORRIGIDO: Busca user_id a partir do telegram_id
    Usa platform_id como STRING
    """
    
    cursor = bot_state.db.conn.cursor()
    
    cursor.execute("""
        SELECT user_id FROM users
        WHERE platform = 'telegram'
        AND platform_id = ?
        LIMIT 1
    """, (str(telegram_id),))  # ✅ STRING
    
    row = cursor.fetchone()
    
    return row['user_id'] if row else None

def get_telegram_id_from_user_id(user_id: str) -> Optional[int]:
    """
    ✅ CORRIGIDO: Busca telegram_id a partir do user_id
    Converte platform_id STRING para INT
    """
    
    cursor = bot_state.db.conn.cursor()
    
    cursor.execute("""
        SELECT platform_id FROM users
        WHERE user_id = ?
        AND platform = 'telegram'
        LIMIT 1
    """, (user_id,))
    
    row = cursor.fetchone()
    
    if row and row['platform_id']:
        try:
            return int(row['platform_id'])  # ✅ Converter para int
        except (ValueError, TypeError):
            logger.error(f"❌ platform_id inválido para {user_id[:8]}: {row['platform_id']}")
            return None
    
    return None

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
• Envio mensagens proativas quando percebo padrões importantes

📝 **Comandos disponíveis:**
/perfil - Ver seu perfil junguiano
/tensoes - Ver tensões arquetípicas ativas
/pausar_proativo - Pausar mensagens proativas
/retomar_proativo - Retomar mensagens proativas
/stats - Estatísticas de desenvolvimento
/reset - Reiniciar conversação (apaga histórico)
/help - Ajuda

💬 **Como usar:**
Apenas converse naturalmente! Eu vou:
1. Identificar seus arquétipos dominantes
2. Detectar conflitos internos
3. Propor caminhos de integração
4. Desenvolver meu próprio entendimento sobre você

🌟 **Sistema Proativo:**
Às vezes, eu vou iniciar conversas quando perceber padrões importantes ou quando houver tensões não resolvidas. Você pode pausar isso a qualquer momento com /pausar_proativo.

Vamos começar? Me conte: **O que te trouxe aqui hoje?**
"""
    
    await update.message.reply_text(welcome_message)
    
    logger.info(f"Comando /start de {user.first_name} (ID: {user_id[:8]})")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /help"""
    
    help_text = """📚 **Ajuda - Jung Claude**

**COMANDOS PRINCIPAIS:**

/start - Iniciar conversa
/perfil - Ver seu perfil junguiano completo
/tensoes - Ver tensões arquetípicas ativas
/stats - Estatísticas de desenvolvimento (suas e do agente)

**COMANDOS PROATIVOS:**

/pausar_proativo - Pausar mensagens proativas temporariamente
/retomar_proativo - Retomar mensagens proativas
/status_proativo - Ver status do sistema proativo

**COMANDOS AVANÇADOS:**

/reset - Reiniciar conversação (⚠️ apaga histórico)
/export - Exportar suas conversas (em breve)

**COMO FUNCIONA:**

1️⃣ **Conversas Normais:**
Você manda mensagens, eu respondo analisando seus arquétipos.

2️⃣ **Detecção de Tensões:**
Eu identifico conflitos entre arquétipos (ex: Herói vs Sombra).

3️⃣ **Mensagens Proativas:**
Se você ficar inativo por >24h e houver tensões não resolvidas, eu posso iniciar uma conversa.

4️⃣ **Desenvolvimento do Agente:**
Eu evoluo ao longo de nossas conversas, ganhando autonomia e profundidade.

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
💡 Use /tensoes para ver análise detalhada das tensões.
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

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /stats - estatísticas completas"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    # Stats do agente
    agent_state = bot_state.db.get_agent_state()
    
    # Stats proativas
    proactive_stats = bot_state.proactive_module.get_user_proactive_stats(user_id)
    
    # Stats de conversas
    conversations = bot_state.db.get_user_conversations(user_id, limit=1000)
    total_user_words = sum(len(c['user_input'].split()) for c in conversations)
    total_ai_words = sum(len(c['ai_response'].split()) for c in conversations)
    
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

💬 **SISTEMA PROATIVO:**
• Mensagens proativas enviadas: {proactive_stats['total_proactive_messages']}
• Taxa de resposta: {proactive_stats['response_rate']:.0%}
• Engajamento médio: {proactive_stats['avg_engagement_score']:.0%}
• Pensamentos internos: {proactive_stats['total_internal_thoughts']}

🌍 **ESTATÍSTICAS GLOBAIS:**
• Mensagens processadas (bot): {bot_state.total_messages_processed}
• Proativas enviadas (total): {bot_state.total_proactive_sent}

🎯 **PRÓXIMOS MARCOS:**
"""
    
    milestones = bot_state.db.get_milestones(limit=3)
    
    for milestone in milestones:
        stats_text += f"• {milestone['description']}\n"
    
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
    last_proactive = bot_state.proactive_module.proactive_db.get_last_proactive_message(user_id)
    
    status_emoji = "✅" if enabled else "⏸️"
    status_text = "ATIVO" if enabled else "PAUSADO"
    
    message = f"{status_emoji} **Status Proativo: {status_text}**\n\n"
    
    if last_proactive:
        last_time = datetime.fromisoformat(last_proactive['timestamp'])
        delta = datetime.now() - last_time
        time_ago = f"{delta.days}d" if delta.days > 0 else f"{delta.seconds // 3600}h"
        
        message += f"📩 **Última mensagem proativa:**\n"
        message += f"   Há {time_ago}\n"
        message += f"   Tipo: {last_proactive['trigger_type']}\n"
        message += f"   Respondida: {'Sim' if last_proactive['user_responded'] else 'Não'}\n\n"
    else:
        message += "📩 Nenhuma mensagem proativa enviada ainda.\n\n"
    
    message += f"💡 Comandos:\n"
    message += f"   /pausar_proativo - Pausar\n"
    message += f"   /retomar_proativo - Retomar"
    
    await update.message.reply_text(message)

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /reset - reinicia conversação"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)
    
    # Confirmar reset
    confirm_text = (
        "⚠️ **ATENÇÃO: Isso vai apagar todo o histórico de conversas!**\n\n"
        "Você perderá:\n"
        "• Todas as conversas anteriores\n"
        "• Tensões arquetípicas identificadas\n"
        "• Mensagens proativas\n"
        "• Pensamentos internos\n\n"
        "Para confirmar, envie: **CONFIRMAR RESET**"
    )
    
    await update.message.reply_text(confirm_text)
    
    # Armazenar estado de confirmação
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
    
    # ========== CONFIRMAÇÃO DE RESET ==========
    if context.user_data.get('awaiting_reset_confirmation'):
        if message_text.strip().upper() == 'CONFIRMAR RESET':
            # Executar reset
            cursor = bot_state.db.conn.cursor()
            
            # Deletar conversas
            cursor.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
            
            # Deletar tensões
            cursor.execute("DELETE FROM archetype_conflicts WHERE user_id = ?", (user_id,))
            
            # Deletar pensamentos proativos
            cursor.execute("DELETE FROM internal_thoughts WHERE user_id = ?", (user_id,))
            
            # Deletar mensagens proativas
            cursor.execute("DELETE FROM proactive_messages WHERE user_id = ?", (user_id,))
            
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
            await update.message.reply_text(
                "❌ Reset cancelado.\n\n"
                "Seu histórico foi preservado."
            )
            context.user_data['awaiting_reset_confirmation'] = False
            return
    
    # ========== DETECTAR RESPOSTA A MENSAGEM PROATIVA ==========
    last_proactive = bot_state.get_last_proactive(telegram_id)
    
    if last_proactive:
        # Usuário está respondendo a mensagem proativa
        proactive_user_id = last_proactive['user_id']
        
        # Processar resposta
        bot_state.proactive_module.process_user_response(proactive_user_id, message_text)
        
        # Limpar registro
        bot_state.clear_proactive_message(telegram_id)
        
        logger.info(f"✅ Resposta a mensagem proativa detectada de {user.first_name}")
    
    # ========== PROCESSAR MENSAGEM NORMAL ==========
    
    # Enviar indicador "digitando..."
    await update.message.chat.send_action(action="typing")
    
    try:
        # ✅ CORRIGIDO: process_message() SEM user_name
        result = bot_state.jung_engine.process_message(
            user_id=user_id,
            message=message_text,
            model="grok-4-fast-reasoning"
        )
        
        # Enviar resposta
        await update.message.reply_text(result['response'])
        
        # Atualizar estatísticas
        bot_state.total_messages_processed += 1
        
        # Log
        logger.info(
            f"✅ Mensagem processada de {user.first_name}: "
            f"{message_text[:50]}..."
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem: {e}", exc_info=True)
        
        await update.message.reply_text(
            "😔 Desculpe, ocorreu um erro ao processar sua mensagem.\n"
            "Pode tentar novamente?"
        )

# ============================================================
# TASK ASSÍNCRONA: SISTEMA PROATIVO
# ============================================================

async def proactive_background_task(application: Application):
    """
    ✅ CORRIGIDO: Task proativa com platform_id STRING
    """
    
    logger.info("🚀 Task proativa iniciada!")
    
    while True:
        try:
            await asyncio.sleep(PROACTIVE_CHECK_INTERVAL)
            
            logger.info("🔍 Checando usuários para mensagens proativas...")
            
            # Buscar todos os usuários Telegram
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
                
                # ✅ CONVERTER platform_id PARA INT
                try:
                    telegram_id = int(platform_id_str)
                except (ValueError, TypeError):
                    logger.error(f"❌ platform_id inválido para {user_name}: {platform_id_str}")
                    continue
                
                # Checar se proativo está habilitado
                if not bot_state.is_proactive_enabled(user_id):
                    logger.info(f"⏸️  Proativo desabilitado para {user_name}")
                    continue
                
                # Tentar gerar mensagem proativa
                try:
                    proactive_message = bot_state.proactive_module.check_and_generate_message(
                        user_id=user_id,
                        model="grok-4-fast-reasoning"
                    )
                    
                    if proactive_message:
                        # Enviar via Telegram
                        try:
                            sent_message = await application.bot.send_message(
                                chat_id=telegram_id,
                                text=proactive_message.content
                            )
                            
                            # Registrar envio
                            bot_state.register_proactive_message(telegram_id, {
                                'message_id': proactive_message.source_thought_id,
                                'content': proactive_message.content,
                                'user_id': user_id
                            })
                            
                            logger.info(f"✅ Mensagem proativa enviada para {user_name}")
                            
                        except Exception as e:
                            logger.error(f"❌ Erro ao enviar proativa para {user_name}: {e}")
                    else:
                        logger.info(f"ℹ️  Nenhuma mensagem proativa gerada para {user_name}")
                
                except Exception as e:
                    logger.error(f"❌ Erro ao gerar proativa para {user_name}: {e}", exc_info=True)
                
                # Pequeno delay entre usuários
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
    
    logger.info("✅ Task proativa iniciada em background")

def main():
    """Ponto de entrada principal"""
    
    logger.info("="*60)
    logger.info("🤖 JUNG CLAUDE TELEGRAM BOT v2.1 - CORRIGIDO")
    logger.info("   Integração completa com jung_core.py v3.2")
    logger.info("="*60)
    
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
    application.add_handler(CommandHandler("tensoes", tensoes_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("pausar_proativo", pausar_proativo_command))
    application.add_handler(CommandHandler("retomar_proativo", retomar_proativo_command))
    application.add_handler(CommandHandler("status_proativo", status_proativo_command))
    application.add_handler(CommandHandler("reset", reset_command))
    
    # Handler de mensagens de texto
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    # Iniciar bot
    logger.info("🚀 Iniciando bot...")
    logger.info("✅ Bot rodando! Pressione Ctrl+C para parar.")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()