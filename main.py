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
from telegram_bot import BotState, start_command, help_command, stats_command, mbti_command, desenvolvimento_command, reset_command
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
# LIFECYCLE MANAGER
# ============================================================================

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
    
    # Iniciar polling (em background task para não bloquear o FastAPI)
    # Nota: Em produção com webhook seria diferente, mas para polling:
    asyncio.create_task(telegram_app.updater.start_polling())
    
    logger.info("✅ Bot Telegram iniciado e rodando!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Parando Bot Telegram...")
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
