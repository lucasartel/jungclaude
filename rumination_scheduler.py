"""
Scheduler do Sistema de Ruminação
Executa jobs periódicos de digestão e entrega a cada 12 horas
"""

import schedule
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
            dream.generate_dream(user_id)
        except Exception as e:
            logger.error(f"⚠️ Erro no Motor Onírico: {e}")

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

    except Exception as e:
        logger.error(f"❌ Erro no job de ruminação: {e}", exc_info=True)


# Agendar job
schedule.every(DIGEST_INTERVAL_HOURS).hours.do(run_rumination_job)

# Executar imediatamente na primeira vez
run_rumination_job()

logger.info(f"\n🕐 Scheduler configurado: job a cada {DIGEST_INTERVAL_HOURS}h")
logger.info("   Próxima execução agendada")
logger.info("   Pressione Ctrl+C para parar\n")


if __name__ == "__main__":
    """Loop principal do scheduler"""
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar a cada minuto
    except KeyboardInterrupt:
        logger.info("\n🛑 Scheduler interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal no scheduler: {e}", exc_info=True)
