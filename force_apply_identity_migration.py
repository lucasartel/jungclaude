"""
Script para forçar aplicação da migration de identidade do agente

Uso:
    python force_apply_identity_migration.py
"""

import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_database():
    """Encontra o banco de dados"""
    possible_paths = [
        Path("/data/jung_hybrid.db"),  # Railway
        Path("data/jung_hybrid.db"),   # Local
        Path("jung_hybrid.db"),         # Root
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # Se não encontrou, retornar o primeiro (Railway)
    return possible_paths[0]


def check_tables_exist(cursor):
    """Verifica se as tabelas de identidade já existem"""
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE 'agent_%'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    return tables


def apply_identity_migration(db_path: Path):
    """Aplica a migration de identidade do agente"""
    logger.info("=" * 70)
    logger.info("🔧 FORÇANDO APLICAÇÃO DA MIGRATION DE IDENTIDADE")
    logger.info("=" * 70)
    logger.info(f"Banco: {db_path}")

    # Conectar ao banco
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # Verificar tabelas existentes
        existing_tables = check_tables_exist(cursor)
        logger.info(f"📊 Tabelas agent_* existentes: {existing_tables}")

        if len(existing_tables) >= 8:
            logger.info("✅ As 8 tabelas já existem! Migration já foi aplicada.")
            logger.info(f"   Tabelas: {', '.join(existing_tables)}")
            return

        # Ler migration file (usar caminho relativo ao script)
        script_dir = Path(__file__).parent
        migration_file = script_dir / "migrations" / "006_agent_identity_nuclear.sql"

        logger.info(f"📁 Script dir: {script_dir}")
        logger.info(f"📁 Migration file path: {migration_file}")

        if not migration_file.exists():
            logger.error(f"❌ Migration file não encontrado: {migration_file}")
            logger.error(f"   Working directory: {Path.cwd()}")
            # Tentar listar o diretório migrations para debug
            migrations_dir = script_dir / "migrations"
            if migrations_dir.exists():
                logger.error(f"   Arquivos em {migrations_dir}:")
                for f in migrations_dir.iterdir():
                    logger.error(f"     - {f.name}")
            else:
                logger.error(f"   Diretório migrations não existe em {script_dir}")
            return

        logger.info(f"📝 Lendo migration: {migration_file}")
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # Aplicar migration
        logger.info("⚙️ Aplicando migration...")
        logger.info(f"📄 Migration tem {len(migration_sql)} caracteres")

        # Dividir SQL em statements individuais (ignora comentários e linhas vazias)
        statements = []
        current_statement = []

        for line in migration_sql.split('\n'):
            stripped = line.strip()
            # Ignorar comentários e linhas vazias
            if not stripped or stripped.startswith('--'):
                continue

            current_statement.append(line)

            # Detectar fim de statement
            if stripped.endswith(';'):
                statement_text = '\n'.join(current_statement)
                if statement_text.strip():
                    statements.append(statement_text)
                current_statement = []

        logger.info(f"📝 Dividiu migration em {len(statements)} statements")

        # Executar cada statement individualmente
        executed = 0
        failed = 0
        for i, statement in enumerate(statements):
            try:
                cursor.execute(statement)
                executed += 1
                if i < 3:  # Log apenas os 3 primeiros
                    logger.info(f"  ✅ Statement {i+1}: {statement[:80]}...")
            except Exception as stmt_error:
                failed += 1
                logger.error(f"  ❌ Statement {i+1} falhou: {stmt_error}")
                logger.error(f"     SQL: {statement[:200]}...")
                # Continuar executando os outros

        logger.info(f"📊 Executados: {executed} | Falhados: {failed}")

        try:
            conn.commit()
            logger.info("✅ commit() completou sem exceção")
        except Exception as commit_error:
            logger.error(f"❌ Erro em commit(): {commit_error}")
            raise

        # Verificar se foi aplicada
        existing_tables_after = check_tables_exist(cursor)
        logger.info(f"🔍 Verificação pós-migration:")
        logger.info(f"📊 Tabelas agent_* após migration: {existing_tables_after}")

        if len(existing_tables_after) >= 8:
            logger.info("✅ Migration aplicada com sucesso!")
            logger.info(f"   {len(existing_tables_after)} tabelas criadas")

            # Registrar na tabela de migrations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_file TEXT NOT NULL UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success INTEGER DEFAULT 1
                )
            """)

            cursor.execute("""
                INSERT OR IGNORE INTO schema_migrations (migration_file, success)
                VALUES ('006_agent_identity_nuclear.sql', 1)
            """)
            conn.commit()
            logger.info("✅ Migration registrada em schema_migrations")
        else:
            logger.error(f"❌ Migration falhou! Esperava 8 tabelas, encontrou {len(existing_tables_after)}")

    except Exception as e:
        logger.error(f"❌ Erro ao aplicar migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    db_path = find_database()
    logger.info(f"🗄️ Usando banco: {db_path}")

    if not db_path.exists():
        logger.error(f"❌ Banco de dados não encontrado: {db_path}")
        exit(1)

    apply_identity_migration(db_path)

    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ Script concluído")
    logger.info("=" * 70)
