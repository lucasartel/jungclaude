"""
migrate_to_mem0.py - Migração única de dados históricos para o mem0

Executa UMA VEZ após o deploy do mem0 estar estável no Railway:

    railway run python migrate_to_mem0.py

O que migra:
1. user_facts_v2 (fatos atuais) → mem0 user memories
2. Últimas 30 dias de conversas → mem0 sessions (extração de fatos automática)

É idempotente: pode rodar múltiplas vezes sem duplicar dados
(mem0 detecta conteúdo semelhante e deduplica).
"""

import os
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def find_database() -> Path:
    """Encontra o banco de dados SQLite automaticamente"""
    for p in [Path("/data/jung_hybrid.db"), Path("data/jung_hybrid.db"), Path("jung_hybrid.db")]:
        if p.exists():
            return p
    raise FileNotFoundError("Banco de dados SQLite não encontrado")


def migrate_user_facts(mem0_adapter, conn: sqlite3.Connection) -> int:
    """
    Migra user_facts_v2 (fatos atuais) para mem0.

    Returns:
        int: Número de fatos migrados
    """
    cursor = conn.cursor()

    # Verificar se tabela existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_facts_v2'")
    if not cursor.fetchone():
        logger.warning("⚠️ Tabela user_facts_v2 não encontrada — pulando migração de fatos")
        return 0

    # Buscar fatos ativos dos últimos 90 dias
    cursor.execute("""
        SELECT user_id, category, fact_type, attribute, fact_value, confidence
        FROM user_facts_v2
        WHERE is_current = 1
          AND created_at > datetime('now', '-90 days')
        ORDER BY user_id, confidence DESC
    """)

    facts = cursor.fetchall()
    if not facts:
        logger.info("ℹ️ Nenhum fato encontrado para migrar")
        return 0

    logger.info(f"📦 Migrando {len(facts)} fatos históricos...")

    migrated = 0
    for row in facts:
        user_id, category, fact_type, attribute, value, confidence = row
        fact_text = f"{fact_type} / {attribute}: {value}"

        try:
            mem0_adapter.mem.add(
                messages=[{"role": "user", "content": fact_text}],
                user_id=str(user_id),
                metadata={"source": "migration", "category": category, "confidence": confidence}
            )
            migrated += 1
        except Exception as e:
            logger.warning(f"   ⚠️ Erro ao migrar fato '{fact_text[:50]}': {e}")

    logger.info(f"✅ {migrated}/{len(facts)} fatos migrados")
    return migrated


def migrate_recent_conversations(mem0_adapter, conn: sqlite3.Connection, days: int = 30) -> int:
    """
    Migra conversas recentes para o mem0 (extração automática de fatos).
    Apenas as últimas N dias para não sobrecarregar o LLM.

    Returns:
        int: Número de conversas migradas
    """
    cursor = conn.cursor()

    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    cursor.execute("""
        SELECT user_id, user_input, ai_response, timestamp
        FROM conversations
        WHERE timestamp > ?
          AND user_input IS NOT NULL
          AND ai_response IS NOT NULL
        ORDER BY user_id, timestamp ASC
    """, (cutoff,))

    conversations = cursor.fetchall()
    if not conversations:
        logger.info("ℹ️ Nenhuma conversa recente encontrada para migrar")
        return 0

    logger.info(f"📦 Migrando {len(conversations)} conversas dos últimos {days} dias...")

    migrated = 0
    for row in conversations:
        user_id, user_input, ai_response, ts = row

        try:
            mem0_adapter.mem.add(
                messages=[
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "content": ai_response},
                ],
                user_id=str(user_id),
                metadata={"source": "migration", "original_timestamp": ts}
            )
            migrated += 1

            if migrated % 50 == 0:
                logger.info(f"   {migrated}/{len(conversations)} conversas migradas...")

        except Exception as e:
            logger.warning(f"   ⚠️ Erro ao migrar conversa: {e}")

    logger.info(f"✅ {migrated}/{len(conversations)} conversas migradas")
    return migrated


def main():
    logger.info("=" * 60)
    logger.info("🚀 MIGRAÇÃO HISTÓRICA: SQLite → mem0")
    logger.info("=" * 60)

    # Verificar DATABASE_URL
    if not os.getenv("DATABASE_URL"):
        logger.error("❌ DATABASE_URL não configurado — configure a variável de ambiente e rode novamente")
        return

    # Inicializar mem0 adapter
    try:
        from mem0_memory_adapter import Mem0MemoryAdapter
        adapter = Mem0MemoryAdapter()
        logger.info("✅ mem0 inicializado")
    except Exception as e:
        logger.error(f"❌ Falha ao inicializar mem0: {e}")
        return

    # Conectar ao SQLite
    try:
        db_path = find_database()
        conn = sqlite3.connect(str(db_path))
        logger.info(f"✅ SQLite conectado: {db_path}")
    except Exception as e:
        logger.error(f"❌ Falha ao conectar SQLite: {e}")
        return

    try:
        # Migrar fatos
        logger.info("\n📋 FASE 1: Migrando fatos do usuário...")
        facts_count = migrate_user_facts(adapter, conn)

        # Migrar conversas recentes
        logger.info("\n💬 FASE 2: Migrando conversas recentes (30 dias)...")
        conv_count = migrate_recent_conversations(adapter, conn, days=30)

        logger.info("\n" + "=" * 60)
        logger.info("✅ MIGRAÇÃO CONCLUÍDA")
        logger.info(f"   Fatos migrados:      {facts_count}")
        logger.info(f"   Conversas migradas:  {conv_count}")
        logger.info("=" * 60)
        logger.info("Próximos passos:")
        logger.info("  1. Testar uma nova conversa e verificar log: '✅ [MEM0] Contexto recuperado'")
        logger.info("  2. Após 24h estável, pode desativar memory_flush.py se desejar")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
