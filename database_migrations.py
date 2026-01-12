"""
database_migrations.py

Sistema de Migrations Automático
Aplica migrations pendentes no startup do servidor
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationManager:
    """Gerencia aplicação automática de migrations"""

    def __init__(self, db_path: str = "data/jung_hybrid.db"):
        self.db_path = Path(db_path)
        self.migrations_dir = Path("migrations")

    def ensure_migrations_table(self, cursor):
        """Cria tabela de controle de migrations se não existir"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                migration_file TEXT NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success INTEGER DEFAULT 1
            )
        """)

    def get_applied_migrations(self, cursor):
        """Retorna lista de migrations já aplicadas"""
        cursor.execute("SELECT migration_file FROM schema_migrations WHERE success = 1")
        return {row[0] for row in cursor.fetchall()}

    def get_pending_migrations(self):
        """Retorna lista de migrations pendentes"""
        if not self.migrations_dir.exists():
            return []

        all_migrations = sorted(self.migrations_dir.glob("*.sql"))
        return [m for m in all_migrations if m.name.endswith(".sql")]

    def apply_migration(self, cursor, migration_file: Path):
        """Aplica uma migration específica"""
        logger.info(f"📝 Aplicando migration: {migration_file.name}")

        try:
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()

            # Executar migration
            cursor.executescript(migration_sql)

            # Registrar como aplicada
            cursor.execute(
                "INSERT INTO schema_migrations (migration_file) VALUES (?)",
                (migration_file.name,)
            )

            logger.info(f"✅ Migration aplicada: {migration_file.name}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao aplicar migration {migration_file.name}: {e}")
            # Registrar falha
            cursor.execute(
                "INSERT INTO schema_migrations (migration_file, success) VALUES (?, 0)",
                (migration_file.name,)
            )
            return False

    def run_pending_migrations(self):
        """Aplica todas as migrations pendentes"""
        if not self.db_path.exists():
            logger.error(f"❌ Banco de dados não encontrado: {self.db_path}")
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Criar tabela de controle
            self.ensure_migrations_table(cursor)
            conn.commit()

            # Obter migrations
            applied = self.get_applied_migrations(cursor)
            pending = [m for m in self.get_pending_migrations() if m.name not in applied]

            if not pending:
                logger.info("✅ Nenhuma migration pendente")
                return True

            logger.info(f"📦 {len(pending)} migration(s) pendente(s)")

            # Aplicar migrations pendentes
            success_count = 0
            for migration in pending:
                if self.apply_migration(cursor, migration):
                    conn.commit()
                    success_count += 1
                else:
                    conn.rollback()
                    logger.error(f"❌ Parando aplicação de migrations devido a erro")
                    break

            logger.info(f"✅ {success_count}/{len(pending)} migration(s) aplicada(s) com sucesso")
            return success_count == len(pending)

        except Exception as e:
            logger.error(f"❌ Erro geral no sistema de migrations: {e}")
            conn.rollback()
            return False

        finally:
            conn.close()


def run_migrations_on_startup():
    """
    Função chamada no startup do servidor
    """
    logger.info("=" * 70)
    logger.info("🔧 Verificando migrations pendentes...")
    logger.info("=" * 70)

    manager = MigrationManager()
    success = manager.run_pending_migrations()

    if success:
        logger.info("=" * 70)
        logger.info("✅ Sistema de migrations OK - servidor pronto")
        logger.info("=" * 70)
    else:
        logger.error("=" * 70)
        logger.error("❌ ERRO: Migrations falharam - verifique logs acima")
        logger.error("=" * 70)

    return success


if __name__ == "__main__":
    # Executar migrations manualmente
    success = run_migrations_on_startup()
    exit(0 if success else 1)
