import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv

# Importar o bot
from telegram_bot import BotState, start_command, help_command, perfil_command, memoria_command, fatos_command, padroes_command, tensoes_command, arquetipo_command, stats_command, buscar_command, reset_command
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

    # Registrar handlers (copiado do telegram_bot.py original)
    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("perfil", perfil_command))
    telegram_app.add_handler(CommandHandler("memoria", memoria_command))
    telegram_app.add_handler(CommandHandler("fatos", fatos_command))
    telegram_app.add_handler(CommandHandler("padroes", padroes_command))
    telegram_app.add_handler(CommandHandler("tensoes", tensoes_command))
    telegram_app.add_handler(CommandHandler("arquetipo", arquetipo_command))
    telegram_app.add_handler(CommandHandler("stats", stats_command))
    telegram_app.add_handler(CommandHandler("buscar", buscar_command))
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

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory="admin_web/static"), name="static")

# Importar e incluir rotas do admin
from admin_web.routes import router as admin_router
app.include_router(admin_router)

if __name__ == "__main__":
    # Rodar com uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
