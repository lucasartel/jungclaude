"""
agent_identity_consolidation_job.py

Job de Consolidação de Identidade do Agente

Processa conversas não analisadas e extrai elementos identitários do agente.
Roda periodicamente (configurável via identity_config.py)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from anthropic import Anthropic
import os

from agent_identity_extractor import AgentIdentityExtractor
from identity_config import (
    ADMIN_USER_ID,
    IDENTITY_EXTRACTION_ENABLED,
    IDENTITY_CONSOLIDATION_INTERVAL_HOURS,
    MAX_CONVERSATIONS_PER_CONSOLIDATION
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_database():
    """Encontra o banco de dados automaticamente"""
    possible_paths = [
        Path("/data/jung_hybrid.db"),
        Path("data/jung_hybrid.db"),
        Path("jung_hybrid.db")
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # Retornar primeiro (Railway)
    return possible_paths[0]


async def run_agent_identity_consolidation():
    """
    Job principal de consolidação de identidade do agente

    Processa conversas do usuário master que ainda não foram analisadas
    para extração de elementos identitários do agente.
    """
    if not IDENTITY_EXTRACTION_ENABLED:
        logger.info("🚫 Sistema de identidade do agente desabilitado")
        return

    logger.info("=" * 70)
    logger.info("🧠 CONSOLIDAÇÃO DE IDENTIDADE DO AGENTE - Iniciando")
    logger.info("=" * 70)

    try:
        # Importar aqui para evitar import circular
        from jung_core import HybridDatabaseManager

        # Conectar ao banco
        db_path = find_database()
        if not db_path.exists():
            logger.error(f"❌ Banco de dados não encontrado: {db_path}")
            return

        db = HybridDatabaseManager(str(db_path))
        cursor = db.conn.cursor()

        # Buscar conversas do master admin não processadas
        last_consolidation = datetime.now() - timedelta(hours=IDENTITY_CONSOLIDATION_INTERVAL_HOURS * 2)

        cursor.execute("""
            SELECT c.id, c.timestamp, c.user_id, c.user_input, c.assistant_response
            FROM conversations c
            LEFT JOIN agent_identity_extractions aie ON c.id = aie.conversation_id
            WHERE c.user_id = ?
              AND c.timestamp > ?
              AND aie.id IS NULL
              AND c.assistant_response IS NOT NULL
              AND c.assistant_response != ''
            ORDER BY c.timestamp ASC
            LIMIT ?
        """, (ADMIN_USER_ID, last_consolidation.isoformat(), MAX_CONVERSATIONS_PER_CONSOLIDATION))

        conversations = cursor.fetchall()

        if not conversations:
            logger.info("📭 Nenhuma conversa nova para processar")
            logger.info("=" * 70)
            return

        logger.info(f"📨 Encontradas {len(conversations)} conversas para processar")

        # Criar extrator
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("❌ ANTHROPIC_API_KEY não encontrada")
            return

        llm_client = Anthropic(api_key=api_key)
        extractor = AgentIdentityExtractor(db, llm_client)

        # Processar conversas
        processed_count = 0
        elements_total = 0
        start_time = datetime.now()

        for i, conv in enumerate(conversations, 1):
            conv_id, timestamp, user_id, user_input, agent_response = conv

            try:
                logger.info(f"   [{i}/{len(conversations)}] Processando conversa {conv_id[:12]}...")

                # Extrair identidade
                extraction_start = datetime.now()
                extracted = extractor.extract_from_conversation(
                    conversation_id=conv_id,
                    user_id=user_id,
                    user_input=user_input,
                    agent_response=agent_response
                )

                extraction_time = int((datetime.now() - extraction_start).total_seconds() * 1000)

                # Contar elementos
                elements_count = 0
                if extracted:
                    elements_count = sum(
                        len(v) for k, v in extracted.items()
                        if isinstance(v, list) and k not in ['user_feedback']
                    )

                # Armazenar
                if extracted and elements_count > 0:
                    success = extractor.store_extracted_identity(extracted)
                    if success:
                        elements_total += elements_count
                else:
                    success = True  # Considera sucesso mesmo sem elementos

                # Marcar como processado
                cursor.execute("""
                    INSERT INTO agent_identity_extractions (
                        conversation_id, extracted_at, elements_count, processing_time_ms
                    ) VALUES (?, CURRENT_TIMESTAMP, ?, ?)
                """, (conv_id, elements_count, extraction_time))

                db.conn.commit()
                processed_count += 1

                # Pequeno delay para não sobrecarregar API
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"   ❌ Erro ao processar conversa {conv_id[:12]}: {e}")
                # Marcar como processado com erro (elementos_count = 0)
                try:
                    cursor.execute("""
                        INSERT INTO agent_identity_extractions (
                            conversation_id, extracted_at, elements_count, processing_time_ms
                        ) VALUES (?, CURRENT_TIMESTAMP, 0, 0)
                    """, (conv_id,))
                    db.conn.commit()
                except:
                    pass
                continue

        # Estatísticas finais
        total_time = (datetime.now() - start_time).total_seconds()

        logger.info("=" * 70)
        logger.info(f"✅ CONSOLIDAÇÃO COMPLETA")
        logger.info(f"   📊 Conversas processadas: {processed_count}/{len(conversations)}")
        logger.info(f"   🧠 Elementos identitários extraídos: {elements_total}")
        logger.info(f"   ⏱️  Tempo total: {total_time:.1f}s")
        logger.info(f"   📈 Média: {total_time/len(conversations):.1f}s por conversa")
        logger.info("=" * 70)

        # Estatísticas de identidade
        if elements_total > 0:
            log_identity_stats(cursor)

    except Exception as e:
        logger.error(f"❌ Erro geral na consolidação: {e}")
        import traceback
        logger.error(traceback.format_exc())


def log_identity_stats(cursor):
    """Log estatísticas resumidas da identidade do agente"""
    try:
        logger.info("\n📊 ESTATÍSTICAS DE IDENTIDADE DO AGENTE:")

        # Nuclear
        cursor.execute("""
            SELECT COUNT(*), AVG(certainty)
            FROM agent_identity_core
            WHERE is_current = 1
        """)
        nuclear_count, nuclear_avg = cursor.fetchone()
        if nuclear_count:
            logger.info(f"   🧠 Crenças nucleares: {nuclear_count} (certeza média: {nuclear_avg:.2f})")

        # Contradições
        cursor.execute("""
            SELECT COUNT(*), AVG(tension_level)
            FROM agent_identity_contradictions
            WHERE status = 'unresolved'
        """)
        contra_count, contra_avg = cursor.fetchone()
        if contra_count:
            logger.info(f"   ⚡ Contradições ativas: {contra_count} (tensão média: {contra_avg:.2f})")

        # Selves possíveis
        cursor.execute("""
            SELECT self_type, COUNT(*)
            FROM agent_possible_selves
            WHERE status = 'active'
            GROUP BY self_type
        """)
        selves = cursor.fetchall()
        if selves:
            selves_str = ", ".join([f"{t}: {c}" for t, c in selves])
            logger.info(f"   🎯 Selves possíveis: {selves_str}")

        # Identidade relacional
        cursor.execute("""
            SELECT COUNT(*)
            FROM agent_relational_identity
            WHERE is_current = 1
        """)
        rel_count = cursor.fetchone()[0]
        if rel_count:
            logger.info(f"   🤝 Identidades relacionais: {rel_count}")

        # Agência
        cursor.execute("""
            SELECT agency_type, COUNT(*)
            FROM agent_agency_memory
            GROUP BY agency_type
        """)
        agency = cursor.fetchall()
        if agency:
            agency_str = ", ".join([f"{t}: {c}" for t, c in agency])
            logger.info(f"   🎮 Momentos de agência: {agency_str}")

    except Exception as e:
        logger.error(f"Erro ao gerar estatísticas: {e}")


async def identity_consolidation_scheduler():
    """
    Scheduler que roda consolidação periodicamente

    Chamado pelo main.py como background task
    """
    logger.info(f"📅 Scheduler de identidade do agente iniciado (a cada {IDENTITY_CONSOLIDATION_INTERVAL_HOURS}h)")

    # Aguardar 2 minutos para garantir inicialização completa
    await asyncio.sleep(120)

    while True:
        try:
            await run_agent_identity_consolidation()

            # Aguardar próximo ciclo
            logger.info(f"⏰ Próxima consolidação de identidade em {IDENTITY_CONSOLIDATION_INTERVAL_HOURS}h")
            await asyncio.sleep(IDENTITY_CONSOLIDATION_INTERVAL_HOURS * 3600)

        except Exception as e:
            logger.error(f"❌ Erro no scheduler de identidade: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Em caso de erro, aguardar 1 hora e tentar novamente
            await asyncio.sleep(3600)


if __name__ == "__main__":
    # Executar consolidação manualmente
    asyncio.run(run_agent_identity_consolidation())
