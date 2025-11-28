import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import logging
import os
import sys
from dotenv import load_dotenv

# Adicionar diretório atual ao PYTHONPATH para garantir que admin_web seja encontrado
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar o bot
from telegram_bot import bot_state, start_command, help_command, stats_command, mbti_command, desenvolvimento_command, reset_command
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Importar rotas do admin (serão criadas)
# from admin_web.routes import router as admin_router

load_dotenv()

# Configuração de Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================================
# PROACTIVE MESSAGE SCHEDULER
# ============================================================================

async def proactive_message_scheduler(telegram_app):
    """
    Loop contínuo que verifica e envia mensagens proativas a cada 30 minutos.

    Funcionalidades:
    - Verifica todos os usuários cadastrados
    - Identifica usuários inativos (>3h sem enviar mensagem)
    - Gera mensagens proativas personalizadas usando Jung Proactive Advanced
    - Envia via Telegram
    - Respeita cooldown de 6h entre mensagens proativas
    """

    logger.info("🔄 Scheduler de mensagens proativas iniciado!")

    # Aguardar 1 minuto para garantir que o bot está completamente inicializado
    await asyncio.sleep(60)

    while True:
        try:
            logger.info("🔍 [PROATIVO] Verificando usuários elegíveis para mensagens proativas...")

            # Buscar todos os usuários
            try:
                users = bot_state.db.get_all_users()
                logger.info(f"   📊 Total de usuários cadastrados: {len(users)}")
            except Exception as e:
                logger.error(f"   ❌ Erro ao buscar usuários: {e}")
                await asyncio.sleep(30 * 60)  # Aguardar 30 min e tentar novamente
                continue

            proactive_sent_count = 0

            for user in users:
                try:
                    user_id = user.get('user_id')
                    user_name = user.get('user_name', 'Usuário')
                    platform_id = user.get('platform_id')  # ✅ CRÍTICO: Telegram ID real

                    if not user_id or not platform_id:
                        logger.warning(f"   ⚠️  [PROATIVO] Usuário sem user_id ou platform_id: {user_name}")
                        continue

                    # Verificar e gerar mensagem proativa (sistema já faz todas as validações internas)
                    message = bot_state.proactive.check_and_generate_advanced_message(
                        user_id=user_id,
                        user_name=user_name
                    )

                    if message:
                        # ✅ FIX: Usar platform_id (telegram_id) como chat_id, não user_id (hash)
                        try:
                            telegram_id = int(platform_id)  # Converter para inteiro

                            await telegram_app.bot.send_message(
                                chat_id=telegram_id,  # ✅ CORRIGIDO: usa telegram_id real
                                text=message,
                                parse_mode='Markdown'
                            )
                            logger.info(f"   ✅ [PROATIVO] Mensagem enviada para {user_name} (telegram_id={telegram_id})")
                            proactive_sent_count += 1

                            # Pequeno delay entre envios para evitar rate limit
                            await asyncio.sleep(2)

                        except ValueError as e:
                            logger.error(f"   ❌ [PROATIVO] platform_id inválido para {user_name}: {platform_id} - {e}")
                        except Exception as e:
                            logger.error(f"   ❌ [PROATIVO] Erro ao enviar para {user_name} (telegram_id={platform_id}): {e}")

                except Exception as e:
                    logger.error(f"   ❌ [PROATIVO] Erro ao processar usuário: {e}")
                    continue

            logger.info(f"✅ [PROATIVO] Ciclo completo. Mensagens enviadas: {proactive_sent_count}")
            logger.info(f"⏰ [PROATIVO] Próxima verificação em 30 minutos...")

            # Aguardar 30 minutos antes de próxima verificação
            await asyncio.sleep(30 * 60)

        except Exception as e:
            logger.error(f"❌ [PROATIVO] Erro crítico no scheduler: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Em caso de erro, aguardar 5 minutos e tentar novamente
            await asyncio.sleep(5 * 60)

# ============================================================================
# LIFECYCLE MANAGER
# ============================================================================

async def setup_bot_commands(telegram_app):
    """
    Configura os comandos do bot que aparecem no menu do Telegram.
    Remove comandos antigos e define apenas os comandos atuais.
    """
    from telegram import BotCommand

    commands = [
        BotCommand("start", "Iniciar conversa com Jung"),
        BotCommand("help", "Ver comandos disponíveis"),
        BotCommand("stats", "Ver estatísticas do agente"),
        BotCommand("mbti", "Ver análise MBTI de personalidade"),
        BotCommand("desenvolvimento", "Ver estado de desenvolvimento do agente"),
        BotCommand("reset", "Resetar conversa (apaga todo histórico)")
    ]

    await telegram_app.bot.set_my_commands(commands)
    logger.info(f"✅ Comandos do bot configurados: {[cmd.command for cmd in commands]}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação (Bot + API)"""

    # 1. Iniciar Bot Telegram
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN não encontrado!")
        yield
        return

    logger.info("🤖 Inicializando Bot Telegram...")
    telegram_app = Application.builder().token(telegram_token).build()

    # Registrar handlers (apenas comandos essenciais)
    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("stats", stats_command))
    telegram_app.add_handler(CommandHandler("mbti", mbti_command))
    telegram_app.add_handler(CommandHandler("desenvolvimento", desenvolvimento_command))
    telegram_app.add_handler(CommandHandler("reset", reset_command))

    # Handler de mensagens (precisamos importar a função handle_message se ela existir,
    # ou definir aqui se estiver dentro do main no original.
    # Vou assumir que precisamos mover a lógica de main() do telegram_bot.py para cá ou expor o handler)
    from telegram_bot import handle_message
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Iniciar bot em modo assíncrono
    await telegram_app.initialize()
    await telegram_app.start()

    # Configurar comandos visíveis no menu do Telegram
    await setup_bot_commands(telegram_app)

    # Iniciar polling (em background task para não bloquear o FastAPI)
    # Nota: Em produção com webhook seria diferente, mas para polling:
    asyncio.create_task(telegram_app.updater.start_polling())

    logger.info("✅ Bot Telegram iniciado e rodando!")

    # ✨ Iniciar scheduler de mensagens proativas
    proactive_task = asyncio.create_task(proactive_message_scheduler(telegram_app))
    logger.info("✅ Scheduler de mensagens proativas ativado!")

    yield

    # Shutdown
    logger.info("🛑 Parando Bot Telegram...")
    proactive_task.cancel()  # Cancelar task proativa
    try:
        await proactive_task
    except asyncio.CancelledError:
        logger.info("✅ Scheduler proativo cancelado")

    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="Jung Claude Admin", lifespan=lifespan)

# ============================================================================
# ROTAS BÁSICAS
# ============================================================================

@app.get("/")
async def root():
    """Rota raiz - redireciona para o admin"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/admin")

@app.get("/health")
async def health_check():
    """Health check endpoint para monitoramento"""
    return {
        "status": "healthy",
        "service": "Jung Claude Bot + Admin",
        "bot_running": True
    }

@app.get("/test/proactive")
async def test_proactive():
    """
    ENDPOINT DE DIAGNÓSTICO DO SISTEMA PROATIVO

    Acesse: https://seu-railway-url/test/proactive

    Retorna informações detalhadas sobre:
    - Usuários cadastrados
    - Elegibilidade para mensagens proativas
    - Mensagens geradas (sem enviar)
    - Erros encontrados
    - Timezone e cálculos de tempo
    """

    results = []
    from datetime import datetime

    try:
        # Informações de timezone
        now_local = datetime.now()
        now_utc = datetime.utcnow()

        timezone_info = {
            "server_time_local": now_local.strftime("%Y-%m-%d %H:%M:%S"),
            "server_time_utc": now_utc.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone_offset_hours": round((now_local - now_utc).total_seconds() / 3600, 1)
        }

        # Buscar todos os usuários
        users = bot_state.db.get_all_users()

        results.append({
            "step": "get_users",
            "status": "success",
            "total_users": len(users)
        })

        # Testar cada usuário
        for user in users:
            user_id = user.get('user_id')
            user_name = user.get('user_name', 'Usuário')
            platform_id = user.get('platform_id')
            last_seen_str = user.get('last_seen')

            # Calcular tempo de inatividade MANUALMENTE
            hours_inactive = None
            if last_seen_str:
                try:
                    last_seen_dt = datetime.fromisoformat(last_seen_str)
                    # SQLite retorna UTC, comparar com UTC
                    delta = now_utc - last_seen_dt
                    hours_inactive = round(delta.total_seconds() / 3600, 2)
                except Exception as e:
                    logger.error(f"Error parsing last_seen for {user_name}: {e}")

            user_result = {
                "user_name": user_name,
                "user_id": user_id[:8] if user_id else None,
                "platform_id": platform_id,
                "last_seen_utc": last_seen_str,
                "hours_inactive": hours_inactive,
                "total_messages": user.get('total_messages', 0),
                "requirements": {
                    "min_conversations": 3,
                    "min_inactivity_hours": 3,
                    "cooldown_hours": 6
                }
            }

            # Verificar campos obrigatórios
            if not user_id or not platform_id:
                user_result["error"] = "Missing user_id or platform_id"
                results.append(user_result)
                continue

            # Verificar elegibilidade MANUALMENTE
            # (sem chamar check_and_generate para evitar logs confusos)

            # 1. Conversas suficientes?
            total_convs = len(bot_state.db.get_user_conversations(user_id, limit=1000))
            user_result["total_conversations"] = total_convs
            user_result["has_enough_conversations"] = total_convs >= 3

            # 2. Inatividade suficiente?
            user_result["has_enough_inactivity"] = hours_inactive and hours_inactive >= 3

            # 3. Cooldown OK?
            cursor = bot_state.db.conn.cursor()
            cursor.execute("""
                SELECT timestamp FROM proactive_approaches
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (user_id,))
            last_proactive = cursor.fetchone()

            if last_proactive:
                last_proactive_dt = datetime.fromisoformat(last_proactive['timestamp'])
                hours_since_proactive = round((now_utc - last_proactive_dt).total_seconds() / 3600, 2)
                user_result["hours_since_last_proactive"] = hours_since_proactive
                user_result["cooldown_ok"] = hours_since_proactive >= 6
            else:
                user_result["hours_since_last_proactive"] = None
                user_result["cooldown_ok"] = True  # Nunca recebeu = OK

            # Resultado final
            is_eligible = (
                user_result["has_enough_conversations"] and
                user_result["has_enough_inactivity"] and
                user_result["cooldown_ok"]
            )
            user_result["eligible"] = is_eligible

            if is_eligible:
                user_result["status"] = "ELIGIBLE - Ready to receive proactive message"
            else:
                blockers = []
                if not user_result["has_enough_conversations"]:
                    blockers.append(f"Only {total_convs}/3 conversations")
                if not user_result["has_enough_inactivity"]:
                    blockers.append(f"Only {hours_inactive:.1f}h/3h inactive")
                if not user_result["cooldown_ok"]:
                    blockers.append(f"Cooldown {user_result['hours_since_last_proactive']:.1f}h/6h")
                user_result["status"] = f"NOT ELIGIBLE: {', '.join(blockers)}"

            results.append(user_result)

        return {
            "status": "success",
            "timezone": timezone_info,
            "results": results
        }

    except Exception as e:
        logger.error(f"Error in test_proactive endpoint: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "results": results
        }

# Montar arquivos estáticos (apenas se o diretório existir)
static_dir = "admin_web/static"
if os.path.exists(static_dir) and os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"✅ Diretório static montado: {static_dir}")
else:
    logger.warning(f"⚠️  Diretório static não encontrado: {static_dir} - Continuando sem arquivos estáticos")

# Importar e incluir rotas do admin (opcional)
try:
    from admin_web.routes import router as admin_router
    app.include_router(admin_router)
    logger.info("✅ Rotas do admin web carregadas")
except Exception as e:
    import traceback
    logger.error(f"❌ Erro ao carregar admin web: {e}")
    logger.error(f"Traceback completo:\n{traceback.format_exc()}")
    logger.warning("⚠️  Admin web não disponível - Apenas bot Telegram funcionará")


if __name__ == "__main__":
    # Rodar com uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
