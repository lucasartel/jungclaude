#!/usr/bin/env python3
"""
migrate_add_evidence_table.py - Migration para Sistema de Evidências 2.0
=========================================================================

Cria a tabela psychometric_evidence para armazenar citações literais
que embasam cada score psicométrico.

Autor: Sistema Jung
Data: 2025-12-02
"""

import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

# Caminho do banco
DATA_DIR = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./data")
DB_PATH = os.path.join(DATA_DIR, "jung_hybrid.db")


def migrate():
    """Executa a migração para adicionar tabela de evidências"""

    print("=" * 70)
    print("MIGRATION: Sistema de Evidências 2.0")
    print("=" * 70)
    print(f"\nConectando ao banco: {DB_PATH}\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Verificar se tabela já existe
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='psychometric_evidence'
        """)

        if cursor.fetchone():
            print("[OK] Tabela 'psychometric_evidence' ja existe. Nada a fazer.")
            conn.close()
            return

        print("Criando tabela 'psychometric_evidence'...")

        # Criar tabela de evidências
        cursor.execute("""
            CREATE TABLE psychometric_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- Relacionamentos
                user_id TEXT NOT NULL,
                psychometric_version INTEGER NOT NULL,
                conversation_id INTEGER NOT NULL,

                -- Tipo de evidência
                dimension TEXT NOT NULL,
                trait_indicator TEXT,

                -- A evidência em si
                quote TEXT NOT NULL,
                context_before TEXT,
                context_after TEXT,

                -- Scoring
                relevance_score REAL DEFAULT 0.5,
                direction TEXT CHECK(direction IN ('positive', 'negative', 'neutral')),
                weight REAL DEFAULT 1.0,

                -- Metadados
                conversation_timestamp DATETIME,
                extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Qualidade
                confidence REAL DEFAULT 0.5,
                is_ambiguous BOOLEAN DEFAULT 0,
                extraction_method TEXT DEFAULT 'claude',

                -- Explicação
                explanation TEXT,

                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)

        print("  [OK] Tabela criada com sucesso")

        # Criar índices para performance
        print("\nCriando indices de performance...")

        cursor.execute("""
            CREATE INDEX idx_evidence_user_dimension
            ON psychometric_evidence(user_id, dimension)
        """)
        print("  [OK] Indice: idx_evidence_user_dimension")

        cursor.execute("""
            CREATE INDEX idx_evidence_conversation
            ON psychometric_evidence(conversation_id)
        """)
        print("  [OK] Indice: idx_evidence_conversation")

        cursor.execute("""
            CREATE INDEX idx_evidence_version
            ON psychometric_evidence(psychometric_version)
        """)
        print("  [OK] Indice: idx_evidence_version")

        cursor.execute("""
            CREATE INDEX idx_evidence_direction
            ON psychometric_evidence(direction)
        """)
        print("  [OK] Indice: idx_evidence_direction")

        # Adicionar colunas à tabela user_psychometrics para rastreabilidade
        print("\nAtualizando tabela 'user_psychometrics'...")

        # Verificar quais colunas já existem
        cursor.execute("PRAGMA table_info(user_psychometrics)")
        existing_columns = {col[1] for col in cursor.fetchall()}

        columns_to_add = {
            'conversations_used': 'TEXT',  # JSON array de IDs das conversas usadas
            'evidence_extracted': 'BOOLEAN DEFAULT 0',  # Flag se evidências foram extraídas
            'evidence_extraction_date': 'DATETIME',
            'red_flags': 'TEXT',  # JSON array de red flags detectados
        }

        for column_name, column_type in columns_to_add.items():
            if column_name not in existing_columns:
                cursor.execute(f"""
                    ALTER TABLE user_psychometrics
                    ADD COLUMN {column_name} {column_type}
                """)
                print(f"  [OK] Coluna '{column_name}' adicionada")
            else:
                print(f"  [SKIP] Coluna '{column_name}' ja existe")

        # Commit
        conn.commit()

        print("\n" + "=" * 70)
        print("MIGRACAO CONCLUIDA COM SUCESSO!")
        print("=" * 70)
        print("\nSistema de Evidencias 2.0 esta pronto para uso.")
        print("\nProximos passos:")
        print("1. Executar analises psicometricas normalmente")
        print("2. Evidencias serao extraidas on-demand quando visualizadas")
        print("3. Cache automatico para visualizacoes futuras")
        print()

    except Exception as e:
        conn.rollback()
        print("\n" + "=" * 70)
        print("ERRO NA MIGRACAO")
        print("=" * 70)
        print(f"\n{e}\n")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
