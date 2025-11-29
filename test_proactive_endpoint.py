"""
Endpoint de teste para proatividade - adicionar ao admin_web/routes.py
Ou criar rota temporária em main.py
"""

from fastapi import APIRouter
from telegram_bot import bot_state
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/test/proactive")
async def test_proactive():
    """Testa sistema proativo manualmente"""

    results = []

    try:
        # Buscar usuários
        users = bot_state.db.get_all_users()

        results.append({
            "step": "get_users",
            "status": "success",
            "total_users": len(users)
        })

        for user in users:
            user_id = user.get('user_id')
            user_name = user.get('user_name', 'Usuário')
            platform_id = user.get('platform_id')

            user_result = {
                "user_name": user_name,
                "user_id": user_id[:8] if user_id else None,
                "platform_id": platform_id,
                "last_seen": user.get('last_seen'),
                "total_messages": user.get('total_messages', 0)
            }

            if not user_id or not platform_id:
                user_result["error"] = "Missing user_id or platform_id"
                results.append(user_result)
                continue

            # Tentar gerar mensagem
            try:
                message = bot_state.proactive.check_and_generate_advanced_message(
                    user_id=user_id,
                    user_name=user_name
                )

                if message:
                    user_result["eligible"] = True
                    user_result["message_preview"] = message[:100] + "..."
                else:
                    user_result["eligible"] = False
                    user_result["reason"] = "See logs for eligibility check"

            except Exception as e:
                user_result["error"] = str(e)
                logger.error(f"Error generating proactive for {user_name}: {e}", exc_info=True)

            results.append(user_result)

        return {
            "status": "success",
            "results": results
        }

    except Exception as e:
        logger.error(f"Error in test_proactive: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }
