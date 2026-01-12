"""
apply_agent_identity_migration.py

Script para aplicar migration do Sistema de Identidade Nuclear do Agente
"""

import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def apply_migration():
    """
    Aplica migration 006_agent_identity_nuclear.sql
    """
    logger.info("=" * 70)
    logger.info("🚀 Aplicando Migration: Sistema de Identidade Nuclear do Agente")
    logger.info("=" * 70)

    # Conectar ao banco
    db_path = Path("data/jung_hybrid.db")
    if not db_path.exists():
        logger.error(f"❌ Banco de dados não encontrado: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Ler migration
    migration_path = Path("migrations/006_agent_identity_nuclear.sql")
    if not migration_path.exists():
        logger.error(f"❌ Migration não encontrada: {migration_path}")
        return False

    with open(migration_path, 'r', encoding='utf-8') as f:
        migration_sql = f.read()

    # Executar migration
    try:
        logger.info("\n📝 Executando SQL migration...")
        cursor.executescript(migration_sql)
        conn.commit()
        logger.info("✅ Migration executada com sucesso!")

        # Verificar tabelas criadas
        logger.info("\n🔍 Verificando tabelas criadas...")

        tables_to_check = [
            "agent_identity_core",
            "agent_narrative_chapters",
            "agent_identity_contradictions",
            "agent_possible_selves",
            "agent_relational_identity",
            "agent_self_knowledge_meta",
            "agent_agency_memory",
            "agent_identity_extractions"
        ]

        all_tables_exist = True
        for table in tables_to_check:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            result = cursor.fetchone()
            if result:
                # Contar registros
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"   ✅ {table} (registros: {count})")
            else:
                logger.error(f"   ❌ {table} NÃO ENCONTRADA")
                all_tables_exist = False

        # Verificar índices
        logger.info("\n📊 Verificando índices...")
        cursor.execute("""
            SELECT name, tbl_name
            FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_agent_%'
            ORDER BY tbl_name, name
        """)
        indexes = cursor.fetchall()
        logger.info(f"   Total de índices criados: {len(indexes)}")
        for idx_name, tbl_name in indexes[:5]:  # Mostrar primeiros 5
            logger.info(f"   ✅ {idx_name} em {tbl_name}")
        if len(indexes) > 5:
            logger.info(f"   ... e mais {len(indexes) - 5} índices")

        # Verificar triggers
        logger.info("\n⚙️ Verificando triggers...")
        cursor.execute("""
            SELECT name, tbl_name
            FROM sqlite_master
            WHERE type='trigger' AND name LIKE 'update_agent_%'
        """)
        triggers = cursor.fetchall()
        logger.info(f"   Total de triggers criados: {len(triggers)}")
        for trigger_name, tbl_name in triggers:
            logger.info(f"   ✅ {trigger_name} em {tbl_name}")

        # Verificar campos adicionados em tabelas de ruminação
        logger.info("\n🔗 Verificando bridge com Ruminação...")

        tables_with_bridge = [
            ("rumination_tensions", "exported_to_identity_id"),
            ("rumination_insights", "exported_to_identity_id"),
            ("rumination_fragments", "exported_to_identity_id")
        ]

        for table, column in tables_with_bridge:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            if column in columns:
                logger.info(f"   ✅ {table}.{column} adicionado")
            else:
                logger.warning(f"   ⚠️ {table}.{column} NÃO encontrado")

        if all_tables_exist:
            logger.info("\n" + "=" * 70)
            logger.info("🎉 MIGRATION COMPLETA COM SUCESSO!")
            logger.info("=" * 70)
            logger.info("\n📋 Próximos passos:")
            logger.info("1. Implementar agent_identity_extractor.py")
            logger.info("2. Criar agent_identity_consolidation_job.py")
            logger.info("3. Implementar identity_rumination_bridge.py")
            logger.info("4. Integrar context building em jung_core.py")
            logger.info("5. Criar dashboard admin")
            return True
        else:
            logger.error("\n❌ MIGRATION INCOMPLETA - algumas tabelas não foram criadas")
            return False

    except sqlite3.Error as e:
        logger.error(f"❌ Erro ao executar migration: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    success = apply_migration()
    exit(0 if success else 1)
