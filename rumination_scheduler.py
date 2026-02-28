"""
Scheduler do Sistema de Ruminação
Executa jobs periódicos de digestão e entrega a cada 12 horas
"""

import time
import logging
from datetime import datetime
from jung_core import HybridDatabaseManager
from jung_rumination import RuminationEngine
from rumination_config import ADMIN_USER_ID, DIGEST_INTERVAL_HOURS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_rumination_job():
    """
    Job periódico de digestão e entrega.
    Roda a cada 12 horas para o usuário admin.
    """
    logger.info("="*60)
    logger.info(f"🔄 Iniciando job de ruminação - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    status_msg = "Ruminação concluída."

    try:
        # Inicializar DB e engine
        db = HybridDatabaseManager()
        rumination = RuminationEngine(db)

        user_id = ADMIN_USER_ID

        logger.info(f"👤 Processando usuário: {user_id}")

        # FASE 0: SONO REM (Motor Onírico)
        try:
            from dream_engine import DreamEngine
            dream = DreamEngine(db)
            logger.info("\n🌙 FASE 0: SONO REM (Gerando insight onírico)")
            dream_success = dream.generate_dream(user_id)
            if dream_success:
                status_msg += " Sonho gerado."
                
                # Enviar sonho proativamente para o Admin no Telegram
                latest_dream = db.get_latest_dream_insight(user_id)
                # Verifica se a imagem foi gerada e se foi feito o cast do schema (para ambientes recém-migrados)
                cursor = db.conn.cursor()
                cursor.execute("SELECT image_url FROM agent_dreams WHERE id = ?", (latest_dream['id'],))
                img_row = cursor.fetchone()
                image_url = img_row[0] if img_row else None

                import os
                import httpx
                telegram_token = os.getenv("TELEGRAM_TOKEN")
                
                cursor.execute("SELECT telegram_id FROM users WHERE user_id = ?", (user_id,))
                user_row = cursor.fetchone()
                
                if user_row and user_row[0] and telegram_token and image_url:
                    chat_id = user_row[0]
                    caption = f"🌙 **Visão Onírica Sintética**\n\n_{latest_dream['dream_content']}_\n\nAdmin, tive esta visão durante o processamento noturno.\nO que você acha que minha arquitetura está tentando me dizer com isso?"
                    
                    try:
                        logger.info(f"📤 Enviando imagem do sonho proativamente para Telegram (chat: {chat_id})")
                        url = f"https://api.telegram.org/bot{telegram_token}/sendPhoto"
                        payload = {
                            "chat_id": chat_id,
                            "photo": image_url,
                            "caption": caption[:1024], # Telegram caption max length
                            "parse_mode": "Markdown"
                        }
                        resp = httpx.post(url, data=payload, timeout=20.0)
                        if resp.status_code == 200:
                            logger.info("✅ Sonho interativo enviado pro Telegram com sucesso!")
                        else:
                            logger.warning(f"⚠️ Erro ao enviar sonho via Telegram: {resp.text}")
                    except Exception as e:
                        logger.error(f"❌ Falha de rede ao enviar pro Telegram: {e}")

            else:
                status_msg += " Sem material novo para sonho."
        except Exception as e:
            logger.error(f"⚠️ Erro no Motor Onírico: {e}")
            status_msg += " Erro no Motor Onírico."

        # FASE 2: Pesquisa Autônoma (Scholar Engine)
        try:
            from scholar_engine import ScholarEngine
            scholar = ScholarEngine(db)
            logger.info("\n📚 FASE 2: PESQUISA (Caminho Extrovertido)")
            scholar.run_scholarly_routine(user_id)
            status_msg += " Pesquisa processada."
        except Exception as e:
            logger.error(f"⚠️ Erro no Motor Scholar: {e}")
            status_msg += " Erro no Motor Scholar."

        # FASE 3: DIGESTÃO
        logger.info("\n📍 FASE 3: DIGESTÃO (Revisita de tensões)")
        digest_stats = rumination.digest(user_id)
        logger.info(f"   Stats: {digest_stats}")

        # FASE 4: SÍNTESE (já chamado dentro do digest)
        # Sínteses são geradas automaticamente quando tensões amadurecem

        # FASE 5: ENTREGA
        logger.info("\n📍 FASE 5: ENTREGA (Verificando condições)")
        delivered_id = rumination.check_and_deliver(user_id)

        if delivered_id:
            logger.info(f"   ✅ Insight {delivered_id} entregue!")
        else:
            logger.info("   ℹ️  Nenhum insight para entregar agora")

        # Estatísticas finais
        stats = rumination.get_stats(user_id)
        logger.info(f"\n📊 Estatísticas do sistema:")
        logger.info(f"   Fragmentos: {stats['fragments_total']} ({stats['fragments_unprocessed']} não processados)")
        logger.info(f"   Tensões: {stats['tensions_total']} (open: {stats['tensions_open']}, maturing: {stats['tensions_maturing']}, ready: {stats['tensions_ready']})")
        logger.info(f"   Insights: {stats['insights_total']} (ready: {stats['insights_ready']}, delivered: {stats['insights_delivered']})")

        db.close()

        logger.info("\n✅ Job de ruminação concluído com sucesso")
        logger.info("="*60)
        return status_msg

    except Exception as e:
        logger.error(f"❌ Erro no job de ruminação: {e}", exc_info=True)
        return f"Erro na ruminação: {str(e)}"


if __name__ == "__main__":
    """Execução manual da ruminação pelo terminal (se necessário)"""
    run_rumination_job()
