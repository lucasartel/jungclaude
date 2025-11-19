"""
telegram_bot.py - Bot Telegram Jung Claude com GROK-2
=====================================================

Bot completo integrado com jung_core.py para análise junguiana via Telegram.
VERSÃO ATUALIZADA: Usa GROK-2 para análises arquetípicas profundas.

Comandos disponíveis:
- /start - Iniciar conversa
- /help - Ajuda
- /stats - Ver suas estatísticas
- /analise - Gerar análise completa
- /conflitos - Ver conflitos arquetípicos
- /reset - Reiniciar conversa
- /admin - Dashboard admin (apenas admins)
- /arquetipo - Ver info sobre arquétipos

Autor: Sistema Jung Claude
Versão: 3.0 - GROK-2 + Arquétipos Profundos
"""

import os
import logging
from typing import Optional
from datetime import datetime

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
# CONFIGURAÇÃO DE LOGGING
# ============================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================
# INICIALIZAÇÃO GLOBAL
# ============================================================

# Instâncias globais (serão usadas em todos os handlers)
db = DatabaseManager()
engine = JungianEngine(db)

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
    
    user_hash, user_name, telegram_id = get_user_info(update)
    
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
/analise \\- Gerar análise completa
/conflitos \\- Ver conflitos identificados
/arquetipo \\- Info sobre arquétipos
/reset \\- Reiniciar conversa

Vamos começar? 🌟
"""
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='MarkdownV2'
    )
    
    logger.info(f"✅ Usuário {user_name} ({telegram_id}) iniciou o bot")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do comando /help"""
    
    help_text = """
📚 *COMANDOS DISPONÍVEIS*

🎯 *Principais:*
/start \\- Iniciar ou reiniciar o bot
/help \\- Ver esta mensagem de ajuda

📊 *Estatísticas:*
/stats \\- Ver suas estatísticas \\(mensagens, memórias, conflitos\\)
/analise \\- Gerar análise junguiana completa
/conflitos \\- Ver conflitos arquetípicos identificados

🎭 *Arquétipos:*
/arquetipo \\- Listar todos os arquétipos
/arquetipo \\[nome\\] \\- Ver info sobre um arquétipo específico

Exemplos:
• `/arquetipo Herói`
• `/arquetipo Sombra`

🔄 *Utilidades:*
/reset \\- Limpar histórico e recomeçar

⚡ *SISTEMA GROK\\-2:*
Este bot usa GROK\\-2 para análises arquetípicas profundas e detecção de conflitos internos\\.

💡 *Dica:* Apenas converse naturalmente\\! O sistema identifica padrões automaticamente\\.
"""
    
    await update.message.reply_text(
        help_text,
        parse_mode='MarkdownV2'
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do comando /stats"""
    
    user_hash, user_name, telegram_id = get_user_info(update)
    
    # Buscar estatísticas
    stats = db.get_user_stats(user_hash)
    memory_count = db.count_memories(user_hash)
    conflicts = db.get_user_conflicts(user_hash, limit=1000)
    analyses = db.get_user_analyses(user_hash)
    
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
• Análises completas: {len(analyses)}

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


async def analise_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do comando /analise"""
    
    user_hash, user_name, telegram_id = get_user_info(update)
    
    memory_count = db.count_memories(user_hash)
    
    # Verificar se tem memórias suficientes
    if memory_count < Config.MIN_MEMORIES_FOR_ANALYSIS:
        await update.message.reply_text(
            f"⚠️ Você precisa de pelo menos *{Config.MIN_MEMORIES_FOR_ANALYSIS} conversas* para gerar uma análise completa\\.\n\n"
            f"Atualmente você tem *{memory_count} conversas*\\.\n\n"
            f"Continue conversando comigo\\! 💬",
            parse_mode='MarkdownV2'
        )
        return
    
    # Perguntar qual modelo usar
    keyboard = [
        [
            InlineKeyboardButton("⚡ GROK-2 (Recomendado)", callback_data="analise_grok-2-1212"),
        ],
        [
            InlineKeyboardButton("🚀 GPT-4o (Alternativo)", callback_data="analise_gpt-4o"),
            InlineKeyboardButton("💨 GPT-4o-mini (Rápido)", callback_data="analise_gpt-4o-mini")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🔮 *GERAR ANÁLISE COMPLETA*\n\n"
        f"Você tem *{memory_count} conversas* registradas\\.\n\n"
        f"⚡ *GROK\\-2:* Análise arquetípica profunda \\(recomendado\\)\n"
        f"🚀 *GPT\\-4o:* Análise detalhada tradicional\n"
        f"💨 *GPT\\-4o\\-mini:* Análise rápida\n\n"
        f"Escolha o modelo:",
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )


async def conflitos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do comando /conflitos"""
    
    user_hash, user_name, telegram_id = get_user_info(update)
    
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
    
    conflicts_text += "💡 Use /analise para uma visão completa\\!"
    
    await update.message.reply_text(
        conflicts_text,
        parse_mode='MarkdownV2'
    )


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do comando /reset"""
    
    user_hash, user_name, telegram_id = get_user_info(update)
    
    # Criar botões de confirmação
    keyboard = [
        [
            InlineKeyboardButton("✅ Sim, limpar tudo", callback_data="reset_confirm"),
            InlineKeyboardButton("❌ Cancelar", callback_data="reset_cancel")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    memory_count = db.count_memories(user_hash)
    
    await update.message.reply_text(
        f"⚠️ *ATENÇÃO*\n\n"
        f"Você está prestes a *deletar TODAS* as suas conversas e análises\\.\n\n"
        f"📊 Dados que serão perdidos:\n"
        f"• {memory_count} memórias de conversas\n"
        f"• Todos os conflitos identificados\n"
        f"• Todas as análises geradas\n\n"
        f"Esta ação *NÃO PODE SER DESFEITA*\\.\n\n"
        f"Tem certeza?",
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )


async def arquetipo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do comando /arquetipo [nome]"""
    
    # Verificar se foi passado um nome
    if not context.args:
        # Listar todos os arquétipos
        archetypes_list = "🎭 *ARQUÉTIPOS DISPONÍVEIS*\n\n"
        
        for name, info in Config.ARCHETYPES.items():
            emoji = info['emoji']
            archetypes_list += f"{emoji} {escape_markdown(name)}\n"
        
        archetypes_list += f"\n💡 Use `/arquetipo [nome]` para ver detalhes\\.\n"
        archetypes_list += f"Exemplo: `/arquetipo Herói`"
        
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


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do comando /admin (apenas para admins)"""
    
    user_hash, user_name, telegram_id = get_user_info(update)
    
    if not is_admin(telegram_id):
        await update.message.reply_text(
            "🔒 Este comando é restrito a administradores\\.",
            parse_mode='MarkdownV2'
        )
        return
    
    # Estatísticas gerais
    all_users = db.get_all_users(platform="telegram")
    total_messages = sum(u['total_messages'] for u in all_users)
    
    cursor = db.sqlite_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM archetype_conflicts WHERE platform = 'telegram'")
    total_conflicts = cursor.fetchone()[0]
    
    admin_text = f"""
🔧 *PAINEL ADMINISTRATIVO*

📊 *Estatísticas Gerais:*
• Total de usuários: {len(all_users)}
• Total de mensagens: {total_messages}
• Total de conflitos: {total_conflicts}

⚡ *Sistema:* GROK\\-2 \\(1212\\)

👥 *Usuários Recentes:*
"""
    
    for user in all_users[:5]:
        admin_text += f"\n• {escape_markdown(user['user_name'])}"
        admin_text += f"\n  💬 {user['total_messages']} mensagens"
    
    admin_text += f"\n\n💡 Acesse o dashboard completo em:\n`streamlit run admin_telegram.py`"
    
    await update.message.reply_text(
        admin_text,
        parse_mode='MarkdownV2'
    )


# ============================================================
# HANDLER DE MENSAGENS (CONVERSAÇÃO COM GROK-2)
# ============================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler de mensagens de texto (conversação principal com GROK-2)"""
    
    user_hash, user_name, telegram_id = get_user_info(update)
    user_message = update.message.text
    
    logger.info(f"📨 Mensagem de {user_name}: {user_message[:50]}...")
    
    # Mostrar "digitando..."
    await update.message.chat.send_action("typing")
    
    # ========================================
    # ✅ MUDANÇA PRINCIPAL: Usar GROK-2-1212
    # ========================================
    try:
        logger.info(f"⚡ Processando com GROK-2...")
        
        result = engine.process_message(
            user_hash=user_hash,
            user_name=user_name,
            message=user_message,
            platform="telegram",
            model="grok-4-fast-reasoning"  # ✅ GROK-2 (NOME CORRETO)
        )
        
        logger.info(f"✅ GROK-2 processou em {result.get('processing_time', 'N/A')}s")
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar com GROK-2: {e}")
        
        # Fallback para GPT-4o-mini
        logger.info(f"🔄 Fallback para GPT-4o-mini...")
        
        result = engine.process_message(
            user_hash=user_hash,
            user_name=user_name,
            message=user_message,
            platform="telegram",
            model="gpt-4o-mini"
        )
    
    # Enviar resposta
    await update.message.reply_text(result['response'])
    
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
    
    logger.info(f"✅ Resposta enviada para {user_name}")


# ============================================================
# HANDLER DE CALLBACKS (BOTÕES)
# ============================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler de botões inline (callbacks)"""
    
    query = update.callback_query
    await query.answer()
    
    user_hash, user_name, telegram_id = get_user_info(update)
    
    # ========== ANÁLISE ==========
    if query.data.startswith("analise_"):
        model = query.data.replace("analise_", "")
        
        model_names = {
            "grok-4-fast-reasoning": "GROK-2 (1212)",  # ✅ CORRETO
            "gpt-4o": "GPT-4o",
            "gpt-4o-mini": "GPT-4o-mini"
        }
        
        model_display = model_names.get(model, model.upper())
        
        await query.edit_message_text(
            f"🔮 Gerando análise com *{escape_markdown(model_display)}*\\.\\.\\.\n\n"
            f"Isso pode levar 30\\-60 segundos\\. Aguarde\\!",
            parse_mode='MarkdownV2'
        )
        
        # Gerar análise
        analysis = engine.generate_full_analysis(
            user_hash=user_hash,
            user_name=user_name,
            platform="telegram",
            model=model
        )
        
        if analysis:
            # Formatar e enviar análise
            analysis_text = f"✅ *ANÁLISE JUNGUIANA COMPLETA*\n\n"
            analysis_text += f"🤖 *Modelo:* {escape_markdown(model_display)}\n"
            analysis_text += f"🧬 *MBTI:* `{analysis['mbti']}`\n"
            analysis_text += f"🎭 *Fase:* {analysis['phase']}/5\n\n"
            
            if analysis.get('archetypes'):
                archetypes_str = ', '.join(analysis['archetypes'])
                analysis_text += f"⭐ *Arquétipos Dominantes:*\n{escape_markdown(archetypes_str)}\n\n"
            
            analysis_text += "━━━━━━━━━━━━━━━━\n\n"
            
            # Enviar primeira mensagem
            await query.edit_message_text(
                analysis_text,
                parse_mode='MarkdownV2'
            )
            
            # Enviar análise completa (pode ser longa, então dividir)
            insights = analysis['insights']
            
            # Dividir em chunks de 4000 caracteres (limite do Telegram é 4096)
            chunks = [insights[i:i+3500] for i in range(0, len(insights), 3500)]
            
            for chunk in chunks:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=chunk
                )
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="✅ Análise concluída\\!\n\nUse /stats para ver suas estatísticas atualizadas\\.",
                parse_mode='MarkdownV2'
            )
        
        else:
            await query.edit_message_text(
                "❌ Erro ao gerar análise\\. Tente novamente mais tarde\\.",
                parse_mode='MarkdownV2'
            )
    
    # ========== RESET ==========
    elif query.data == "reset_confirm":
        await query.edit_message_text(
            "⚠️ *FUNÇÃO DESABILITADA*\n\n"
            "Por segurança, a função de reset completo está desabilitada\\.\n\n"
            "Se realmente deseja limpar seus dados, entre em contato com o administrador\\.",
            parse_mode='MarkdownV2'
        )
    
    elif query.data == "reset_cancel":
        await query.edit_message_text(
            "✅ Operação cancelada\\. Seus dados estão seguros\\!",
            parse_mode='MarkdownV2'
        )


# ============================================================
# HANDLER DE ERROS
# ============================================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler global de erros"""
    
    logger.error(f"❌ Erro: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Ocorreu um erro inesperado\\. Por favor, tente novamente\\.\n\n"
            "_O sistema está usando GROK\\-2\\. Se persistir, contate o administrador\\._",
            parse_mode='MarkdownV2'
        )


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
    
    # Criar aplicação
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # ========== REGISTRAR HANDLERS ==========
    
    # Comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("analise", analise_command))
    application.add_handler(CommandHandler("conflitos", conflitos_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CommandHandler("arquetipo", arquetipo_command))
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Callbacks (botões)
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Mensagens de texto (conversação)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Erros
    application.add_error_handler(error_handler)
    
    # ========== INICIAR BOT ==========
    
    logger.info("✅ Bot inicializado com sucesso!")
    logger.info(f"⚡ Sistema: GROK-2 (1212)")
    logger.info(f"📊 Usuários cadastrados: {len(db.get_all_users(platform='telegram'))}")
    
    # Rodar bot (polling)
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
    finally:
        db.close()
        logger.info("👋 Até logo!")