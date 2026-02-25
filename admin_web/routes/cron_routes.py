"""
Rotas para processamento periódico via Cron Jobs do Railway.
Substitui as antigas rotinas assíncronas do main.py.
"""
import logging
import os
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Security, Request
from fastapi.security.api_key import APIKeyHeader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cron", tags=["Cron Jobs"])

# Segurança via Header
CRON_SECRET_KEY = os.getenv("CRON_SECRET_KEY", "dev-secret-key")
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def verify_cron_key(api_key: str = Security(api_key_header)):
    if not api_key:
        logger.warning("Tentativa de acesso ao cron sem chave válida")
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    # Remover o prefixo Bearer se presente
    clean_key = api_key.replace("Bearer ", "").strip()
    
    if clean_key != CRON_SECRET_KEY:
        logger.warning("Chave de cron inválida")
        raise HTTPException(status_code=403, detail="Invalid cron secret key")
    
    return clean_key

@router.post("/rumination", dependencies=[Depends(verify_cron_key)])
async def trigger_rumination():
    """Aciona o job de Sonho e Ruminação (antigo scheduler de 12h)"""
    logger.info("⚙️ CRON: Acionando Job de Ruminação e Motor Onírico")
    try:
        # Importando aqui para evitar loops circulares
        from rumination_scheduler import run_rumination_job
        # run_rumination_job é síncrona
        await asyncio.to_thread(run_rumination_job)
        return {"status": "success", "message": "Rumination and Dreams job completed"}
    except Exception as e:
        logger.error(f"❌ CRON Rumination error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/identity-consolidation", dependencies=[Depends(verify_cron_key)])
async def trigger_identity_consolidation():
    """Aciona a consolidação de crenças do agente (antigo scheduler de 6h)"""
    logger.info("⚙️ CRON: Acionando Consolidação de Identidade")
    try:
        from agent_identity_consolidation_job import run_agent_identity_consolidation
        await run_agent_identity_consolidation()
        return {"status": "success", "message": "Identity consolidation completed"}
    except Exception as e:
        logger.error(f"❌ CRON Identity Consolidation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/identity-bridge", dependencies=[Depends(verify_cron_key)])
async def trigger_identity_bridge():
    """Aciona a sincronização entre Identidade e Ruminação (antigo scheduler de 6h)"""
    logger.info("⚙️ CRON: Acionando Bridge Identidade-Ruminação")
    try:
        from identity_rumination_bridge import run_identity_rumination_sync
        await run_identity_rumination_sync()
        return {"status": "success", "message": "Identity-Rumination bridge completed"}
    except Exception as e:
        logger.error(f"❌ CRON Identity Bridge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory-metrics", dependencies=[Depends(verify_cron_key)])
async def trigger_memory_metrics():
    """Aciona a consolidação de memórias de longo prazo (antigo job mensal)"""
    logger.info("⚙️ CRON: Acionando Consolidação de Memórias a Longo Prazo")
    try:
        from jung_memory_consolidation import run_consolidation_job
        from telegram_bot import bot_state
        await asyncio.to_thread(run_consolidation_job, bot_state.db)
        return {"status": "success", "message": "Memory metrics consolidated"}
    except Exception as e:
        logger.error(f"❌ CRON Memory Metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/proactive-messages", dependencies=[Depends(verify_cron_key)])
async def trigger_proactive_messages(request: Request):
    """Aciona a verificação e envio de mensagens proativas (antigo scheduler de 30min)"""
    _proactive_enabled = os.getenv("PROACTIVE_ENABLED", "false").lower() == "true"
    if not _proactive_enabled:
        return {"status": "skipped", "message": "Proactive mode disabled in ENV variables"}

    logger.info("⚙️ CRON: Acionando Verificação de Mensagens Proativas")
    try:
        from telegram_bot import bot_state
        telegram_app = getattr(request.app.state, "telegram_app", None)
        
        if not telegram_app:
            raise ValueError("telegram_app não está disponível em request.app.state")

        # Reproduzindo a lógica do antigo proactive_message_scheduler
        users = bot_state.db.get_all_users()
        sent_count = 0

        for user in users:
            try:
                user_id = user.get('user_id')
                user_name = user.get('user_name', 'Usuário')
                platform_id = user.get('platform_id')

                if not user_id or not platform_id:
                    continue

                message = bot_state.proactive.check_and_generate_advanced_message(
                    user_id=user_id,
                    user_name=user_name
                )

                if message:
                    telegram_id = int(platform_id)
                    await telegram_app.bot.send_message(
                        chat_id=telegram_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    logger.info(f"✅ [CRON PROATIVO] Mensagem enviada para {user_name} ({telegram_id})")
                    sent_count += 1
                    await asyncio.sleep(1) # delay para rate limit

            except Exception as loop_e:
                logger.error(f"❌ Error processing proactive for {user_id}: {loop_e}")
                continue
                
        return {"status": "success", "message": f"Processed proactives. Sent: {sent_count}"}
        
    except Exception as e:
        logger.error(f"❌ CRON Proactive Messages error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
