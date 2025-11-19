"""
telegram_bot.py - Bot Telegram Jung Claude com GROK-2 (FIXED v2)
==============================================================

Bot completo integrado com jung_core.py para análise junguiana via Telegram.
VERSÃO CORRIGIDA: Argumentos posicionais para process_message().

Autor: Sistema Jung Claude
Versão: 3.2 - GROK-2 + Argumentos Posicionais Fix
"""

import os
import logging
import traceback
from typing import Optional
from datetime import datetime
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

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
# CONFIGURAÇÃO DE LOGGING DETALHADO
# ============================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================
# INICIALIZAÇÃO GLOBAL COM VALIDAÇÃO
# ============================================================

# Validar configurações antes de iniciar
try:
    Config.validate()
    logger.info("✅ Configurações validadas")
except Exception as e:
    logger.error(f"❌ Erro ao validar configurações: {e}")
    raise

# Instâncias globais
try:
    db = DatabaseManager()
    logger.info("✅ DatabaseManager inicializado")
except Exception as e:
    logger.error(f"❌ Erro ao inicializar DatabaseManager: {e}")
    raise

try:
    engine = JungianEngine(db)
    logger.info("✅ JungianEngine inicializado")
except Exception as e:
    logger.error(f"❌ Erro ao inicializar JungianEngine: {e}")
    raise

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def get_user_info(update: Update) -> tuple:
    """Extrai informações do usuário"""
    user = update.effective_user
    
    # ID do Telegram como identificador único
    user_hash = create_user_hash(str(user.id))
    
    # Nome completo ou username
    user_name = user.full_name or user.username or f"User_{user.id}"
    
    return user_hash, user_name, user.id


def is_admin(telegram_id: int) -> bool:
    """Verifica se usuário é admin"""
    return telegram_id in Config.TELEGRAM_ADMIN_IDS


def escape_markdown(text: str) -> str:
    """Escapa caracteres especiais do Markdown V2"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


# ============================================================
# HANDLERS DE COMANDOS
# ============================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do comando /start"""
    
    try:
        user_hash, user_name, telegram_id = get_user_info(update)
        
        logger.info(f"📨 /start de {user_name} ({telegram_id})")
        
        welcome_message = f"""
👋 Olá, *{escape_markdown(user_name)}*\\!

Sou o *Jung Claude*, um terapeuta junguiano especializado em análise arquetípica\\.

🧠 *O que posso fazer:*
• Ouvir suas preocupações com empatia
• Identificar padrões arquetípicos
• Detectar conflitos internos
• Ajudar na integração da psique

💬 *Como usar:*
Simplesmente me envie uma mensagem sobre o que está pensando, sentindo ou vivenciando\\. Não há formato certo ou errado \\- apenas seja autêntico\\.

⚡ *SISTEMA GROK\\-2:*
Agora uso GROK\\-2 para análises mais profundas e arquetípicas\\!

📋 *Comandos disponíveis:*
/help \\- Ver todos os comandos
/stats \\- Ver suas estatísticas
/conflitos \\- Ver conflitos identificados
/arquetipo \\- Info sobre arquétipos

Vamos começar? 🌟
"""
        
        await update.message.reply_text(
            welcome_message,
            parse_mode='MarkdownV2'
        )
        
        logger.info(f"✅ /start respondido para {user_name}")
        
    except Exception as e:
        logger.error(f"❌ Erro em /start: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text(
            "❌ Erro ao processar comando /start. Por favor, tente novamente."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do comando /help"""
    
    try:
        logger.info(f"📨 /help de {update.effective_user.id}")
        
        help_text = """
📚 *COMANDOS DISPONÍVEIS*

🎯 *Principais:*
/start \\- Iniciar ou reiniciar o bot
/help \\- Ver esta mensagem de ajuda

📊 *Estatísticas:*
/stats \\- Ver suas estatísticas \\(mensagens, memórias, conflitos\\)
/conflitos \\- Ver conflitos arquetípicos identificados

🎭 *Arquétipos:*
/arquetipo \\- Listar todos os arquétipos
/arquetipo \\[nome\\] \\- Ver info sobre um arquétipo específico

Exemplos:
• `/arquetipo Persona`
• `/arquetipo Sombra`

⚡ *SISTEMA GROK\\-2:*
Este bot usa GROK\\-2 para análises arquetípicas profundas e detecção de conflitos internos\\.

💡 *Dica:* Apenas converse naturalmente\\! O sistema identifica padrões automaticamente\\.
"""
        
        await update.message.reply_text(
            help_text,
            parse_mode='MarkdownV2'
        )
        
        logger.info(f"✅ /help respondido")
        
    except Exception as e:
        logger.error(f"❌ Erro em /help: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text(
            "❌ Erro ao processar comando /help. Por favor, tente novamente."
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do comando /stats"""
    
    try:
        user_hash, user_name, telegram_id = get_user_info(update)
        
        logger.info(f"📨 /stats de {user_name} ({telegram_id})")
        
        # Buscar estatísticas
        stats = db.get_user_stats(user_hash)
        memory_count = db.count_memories(user_hash)
        conflicts = db.get_user_conflicts(user_hash, limit=1000)
        
        if not stats:
            await update.message.reply_text(
                "📊 Você ainda não tem estatísticas\\. Comece uma conversa comigo\\!",
                parse_mode='MarkdownV2'
            )
            return
        
        # Formatar data
        first_interaction = datetime.fromisoformat(stats['first_interaction'])
        days_active = (datetime.now() - first_interaction).days
        
        stats_text = f"""
📊 *SUAS ESTATÍSTICAS*

👤 *Usuário:* {escape_markdown(user_name)}
🆔 *ID:* `{user_hash}`

💬 *Conversas:*
• Mensagens enviadas: {stats['total_messages']}
• Memórias registradas: {memory_count}
• Dias ativo: {days_active}

⚡ *Análise Arquetípica:*
• Conflitos identificados: {len(conflicts)}

🤖 *Modelo:* GROK\\-2 \\(1212\\)

📅 *Primeira interação:* {escape_markdown(first_interaction.strftime('%d/%m/%Y'))}
"""
        
        # Adicionar arquétipos mais frequentes
        if conflicts:
            archetype_count = {}
            for c in conflicts:
                arch1 = c['archetype1']
                arch2 = c['archetype2']
                archetype_count[arch1] = archetype_count.get(arch1, 0) + 1
                archetype_count[arch2] = archetype_count.get(arch2, 0) + 1
            
            top_3 = sorted(archetype_count.items(), key=lambda x: x[1], reverse=True)[:3]
            
            stats_text += "\n🎭 *Arquétipos mais ativos:*\n"
            for arch, count in top_3:
                emoji = Config.ARCHETYPES.get(arch, {}).get('emoji', '❓')
                stats_text += f"• {emoji} {escape_markdown(arch)}: {count}x\n"
        
        await update.message.reply_text(
            stats_text,
            parse_mode='MarkdownV2'
        )
        
        logger.info(f"✅ /stats respondido para {user_name}")
        
    except Exception as e:
        logger.error(f"❌ Erro em /stats: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text(
            "❌ Erro ao processar comando /stats. Por favor, tente novamente."
        )


async def conflitos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do comando /conflitos"""
    
    try:
        user_hash, user_name, telegram_id = get_user_info(update)
        
        logger.info(f"📨 /conflitos de {user_name} ({telegram_id})")
        
        conflicts = db.get_user_conflicts(user_hash, limit=10)
        
        if not conflicts:
            await update.message.reply_text(
                "ℹ️ Nenhum conflito arquetípico identificado ainda\\.\n\n"
                "Continue conversando e o sistema GROK\\-2 detectará padrões automaticamente\\!",
                parse_mode='MarkdownV2'
            )
            return
        
        # Formatar conflitos
        conflicts_text = f"⚡ *CONFLITOS ARQUETÍPICOS* \\({len(conflicts)}\\)\n\n"
        conflicts_text += f"_Detectados pelo sistema GROK\\-2_\n\n"
        
        for i, c in enumerate(conflicts[:5], 1):
            arch1 = c['archetype1']
            arch2 = c['archetype2']
            trigger = c.get('trigger', 'Não especificado')
            
            emoji1 = Config.ARCHETYPES.get(arch1, {}).get('emoji', '❓')
            emoji2 = Config.ARCHETYPES.get(arch2, {}).get('emoji', '❓')
            
            timestamp = datetime.fromisoformat(c['timestamp'])
            date_str = timestamp.strftime('%d/%m/%Y')
            
            conflicts_text += f"{i}\\. {emoji1} *{escape_markdown(arch1)}* vs {emoji2} *{escape_markdown(arch2)}*\n"
            conflicts_text += f"   📅 {escape_markdown(date_str)}\n"
            conflicts_text += f"   🎯 _{escape_markdown(trigger)}_\n\n"
        
        if len(conflicts) > 5:
            conflicts_text += f"_\\.\\.\\. e mais {len(conflicts) - 5} conflito\\(s\\)_\n\n"
        
        conflicts_text += "💡 Continue conversando para detectar novos padrões\\!"
        
        await update.message.reply_text(
            conflicts_text,
            parse_mode='MarkdownV2'
        )
        
        logger.info(f"✅ /conflitos respondido para {user_name}")
        
    except Exception as e:
        logger.error(f"❌ Erro em /conflitos: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text(
            "❌ Erro ao processar comando /conflitos. Por favor, tente novamente."
        )


async def arquetipo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do comando /arquetipo [nome]"""
    
    try:
        logger.info(f"📨 /arquetipo de {update.effective_user.id}")
        
        # Verificar se foi passado um nome
        if not context.args:
            # Listar todos os arquétipos
            archetypes_list = "🎭 *ARQUÉTIPOS DISPONÍVEIS*\n\n"
            
            for name, info in Config.ARCHETYPES.items():
                emoji = info['emoji']
                archetypes_list += f"{emoji} {escape_markdown(name)}\n"
            
            archetypes_list += f"\n💡 Use `/arquetipo [nome]` para ver detalhes\\.\n"
            archetypes_list += f"Exemplo: `/arquetipo Persona`"
            
            await update.message.reply_text(
                archetypes_list,
                parse_mode='MarkdownV2'
            )
            return
        
        # Buscar arquétipo específico
        archetype_name = " ".join(context.args).title()
        
        if archetype_name not in Config.ARCHETYPES:
            await update.message.reply_text(
                f"❓ Arquétipo '{escape_markdown(archetype_name)}' não encontrado\\.\n\n"
                f"Use `/arquetipo` sem argumentos para ver a lista completa\\.",
                parse_mode='MarkdownV2'
            )
            return
        
        # Formatar informações
        info = Config.ARCHETYPES[archetype_name]
        
        archetype_text = f"{info['emoji']} *{escape_markdown(archetype_name).upper()}*\n\n"
        archetype_text += f"📖 *Descrição:*\n{escape_markdown(info['description'])}\n\n"
        archetype_text += f"🌑 *Sombra:*\n{escape_markdown(info['shadow'])}\n\n"
        archetype_text += f"🔑 *Palavras\\-chave:*\n{escape_markdown(', '.join(info['keywords']))}"
        
        await update.message.reply_text(
            archetype_text,
            parse_mode='MarkdownV2'
        )
        
        logger.info(f"✅ /arquetipo respondido")
        
    except Exception as e:
        logger.error(f"❌ Erro em /arquetipo: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text(
            "❌ Erro ao processar comando /arquetipo. Por favor, tente novamente."
        )


# ============================================================
# HANDLER DE MENSAGENS - CORRIGIDO
# ============================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler de mensagens de texto (conversação principal com GROK-2)"""
    
    try:
        user_hash, user_name, telegram_id = get_user_info(update)
        user_message = update.message.text
        
        logger.info(f"📨 Mensagem de {user_name} ({telegram_id}): {user_message[:50]}...")
        
        # Mostrar "digitando..."
        await update.message.chat.send_action("typing")
        
        # Processar com GROK-2
        logger.info(f"⚡ Processando com GROK-2...")
        start_time = time.time()
        
        try:
            # CORREÇÃO: Usar argumentos posicionais em vez de nomeados
            result = engine.process_message(
                user_hash,          # user_hash (posicional)
                user_name,          # user_name (posicional)
                user_message,       # message (posicional)
                "telegram",         # platform (posicional)
                "grok-4-fast-reasoning"      # model (posicional)
            )
            
            processing_time = time.time() - start_time
            logger.info(f"✅ GROK-2 processou em {processing_time:.2f}s")
            
        except Exception as api_error:
            logger.error(f"❌ Erro ao processar com GROK-2: {api_error}")
            logger.error(traceback.format_exc())
            
            # Fallback para GPT-4o-mini
            logger.info(f"🔄 Fallback para GPT-4o-mini...")
            
            try:
                # CORREÇÃO: Usar argumentos posicionais também no fallback
                result = engine.process_message(
                    user_hash,          # user_hash (posicional)
                    user_name,          # user_name (posicional)
                    user_message,       # message (posicional)
                    "telegram",         # platform (posicional)
                    "gpt-4o-mini"      # model (posicional)
                )
                
                logger.info(f"✅ Fallback bem-sucedido")
                
            except Exception as fallback_error:
                logger.error(f"❌ Fallback também falhou: {fallback_error}")
                logger.error(traceback.format_exc())
                raise  # Re-lança para ser pego pelo except externo
        
        # Enviar resposta
        await update.message.reply_text(result['response'])
        logger.info(f"✅ Resposta enviada para {user_name}")
        
        # Se detectou conflito, notificar
        if result.get('conflict'):
            conflict = result['conflict']
            
            arch1 = conflict['archetype1']
            arch2 = conflict['archetype2']
            
            emoji1 = Config.ARCHETYPES.get(arch1, {}).get('emoji', '❓')
            emoji2 = Config.ARCHETYPES.get(arch2, {}).get('emoji', '❓')
            
            conflict_notification = (
                f"⚡ *Conflito Arquetípico Detectado*\n\n"
                f"{emoji1} *{escape_markdown(arch1)}* vs {emoji2} *{escape_markdown(arch2)}*\n\n"
                f"🎯 _{escape_markdown(conflict.get('trigger', 'Tensão identificada'))}_\n\n"
                f"💡 Este conflito foi registrado\\. Use /conflitos para ver o histórico\\.\n\n"
                f"_Detectado por GROK\\-2_"
            )
            
            await update.message.reply_text(
                conflict_notification,
                parse_mode='MarkdownV2'
            )
            
            logger.info(f"⚡ Conflito notificado: {arch1} vs {arch2}")
        
    except Exception as e:
        logger.error(f"❌ ERRO CRÍTICO em handle_message: {e}")
        logger.error(f"❌ Tipo do erro: {type(e).__name__}")
        logger.error(f"❌ Traceback completo:")
        logger.error(traceback.format_exc())
        
        # Enviar mensagem de erro ao usuário
        await update.message.reply_text(
            "❌ Ocorreu um erro inesperado\\. Por favor, tente novamente\\.\n\n"
            f"_Erro: {escape_markdown(str(e)[:100])}_\n\n"
            "Se persistir, contate o administrador\\.",
            parse_mode='MarkdownV2'
        )


# ============================================================
# HANDLER DE ERROS GLOBAL
# ============================================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler global de erros"""
    
    logger.error(f"❌ ERRO GLOBAL: {context.error}")
    logger.error(f"❌ Tipo: {type(context.error).__name__}")
    logger.error(traceback.format_exc())
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                f"❌ Erro inesperado: {escape_markdown(str(context.error)[:100])}\n\n"
                "Por favor, tente novamente\\.\n\n"
                "_O sistema está usando GROK\\-2\\. Se persistir, contate o administrador\\._",
                parse_mode='MarkdownV2'
            )
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem de erro: {e}")


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def main():
    """Função principal - inicializa e roda o bot"""
    
    # Validar configurações
    if not Config.TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN não encontrado no .env!")
        return
    
    if not Config.XAI_API_KEY:
        logger.error("❌ XAI_API_KEY não encontrado no .env!")
        logger.error("   GROK-2 não funcionará sem essa chave!")
        return
    
    logger.info("🤖 Iniciando Jung Claude Bot com GROK-2...")
    logger.info(f"📊 Configurações:")
    logger.info(f"   - XAI_API_KEY: {'✅ Configurada' if Config.XAI_API_KEY else '❌ Faltando'}")
    logger.info(f"   - OPENAI_API_KEY: {'✅ Configurada' if Config.OPENAI_API_KEY else '❌ Faltando'}")
    logger.info(f"   - TELEGRAM_BOT_TOKEN: {'✅ Configurado' if Config.TELEGRAM_BOT_TOKEN else '❌ Faltando'}")
    
    # Criar aplicação
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # ========== REGISTRAR HANDLERS ==========
    
    # Comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("conflitos", conflitos_command))
    application.add_handler(CommandHandler("arquetipo", arquetipo_command))
    
    # Mensagens de texto (conversação)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Erros
    application.add_error_handler(error_handler)
    
    # ========== INICIAR BOT ==========
    
    logger.info("✅ Bot inicializado com sucesso!")
    logger.info(f"⚡ Sistema: GROK-2 (1212)")
    logger.info(f"📊 Usuários cadastrados: {len(db.get_all_users(platform='telegram'))}")
    
    # Rodar bot (polling)
    logger.info("🚀 Iniciando polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


# ============================================================
# PONTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Bot encerrado pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        logger.error(traceback.format_exc())
    finally:
        db.close()
        logger.info("👋 Até logo!")