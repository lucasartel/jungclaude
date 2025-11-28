"""
migrate_add_consent.py - Adiciona colunas de consentimento LGPD
=================================================================

Adiciona à tabela 'users':
- consent_given (INTEGER): 0=não, 1=sim
- consent_timestamp (DATETIME): momento do consentimento

Versão: 1.0
Data: 2025-11-28
"""

import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

# Caminho do banco
DATA_DIR = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./data")
DB_PATH = os.path.join(DATA_DIR, "jung_hybrid.db")

def migrate():
    """Executa a migração"""

    print(f"Conectando ao banco: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verificar se as colunas já existem
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'consent_given' in columns and 'consent_timestamp' in columns:
        print("OK: Colunas de consentimento ja existem. Nada a fazer.")
        conn.close()
        return

    print("Adicionando colunas de consentimento...")

    try:
        # Adicionar consent_given
        if 'consent_given' not in columns:
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN consent_given INTEGER DEFAULT 0
            """)
            print("  [OK] Coluna 'consent_given' adicionada")

        # Adicionar consent_timestamp
        if 'consent_timestamp' not in columns:
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN consent_timestamp DATETIME
            """)
            print("  [OK] Coluna 'consent_timestamp' adicionada")

        # Marcar usuários existentes como tendo consentido (grandfathering)
        cursor.execute("""
            UPDATE users
            SET consent_given = 1,
                consent_timestamp = registration_date
            WHERE consent_given = 0
        """)

        updated = cursor.rowcount
        print(f"  [OK] {updated} usuarios existentes marcados como tendo consentido (grandfathering)")

        conn.commit()
        print("SUCESSO: Migracao concluida!")

    except Exception as e:
        conn.rollback()
        print(f"ERRO na migracao: {e}")
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
