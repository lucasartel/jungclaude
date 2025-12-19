#!/usr/bin/env python3
"""
migrate_facts_v2.py - Migração para Sistema de Fatos V2
========================================================

Cria nova estrutura de tabela user_facts_v2 que suporta:
- Múltiplas pessoas da mesma categoria
- Nomes próprios e atributos complementares
- Versionamento adequado

Autor: Sistema Jung
Data: 2025-12-19
"""

import sqlite3
import logging
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_to_v2(db_path: str = None):
    """
    Migração completa para user_facts_v2

    Args:
        db_path: Caminho do banco (None = usar padrão Railway/local)
    """

    # Determinar caminho do banco
    if db_path is None:
        data_dir = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./data")
        db_path = os.path.join(data_dir, "jung_hybrid.db")

    logger.info(f"{'='*60}")
    logger.info(f"MIGRAÇÃO PARA USER_FACTS_V2")
    logger.info(f"{'='*60}")
    logger.info(f"Database: {db_path}")

    if not os.path.exists(db_path):
        logger.error(f"❌ Database não encontrado: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # =============================================
        # 1. VERIFICAR SE JÁ EXISTE
        # =============================================
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='user_facts_v2'
        """)

        if cursor.fetchone():
            logger.warning("⚠️ Tabela user_facts_v2 já existe!")
            response = input("Deseja recriá-la? Isso apagará dados existentes (s/N): ")
            if response.lower() != 's':
                logger.info("❌ Migração cancelada")
                return False

            logger.info("🗑️ Removendo tabela antiga...")
            cursor.execute("DROP TABLE user_facts_v2")
            conn.commit()

        # =============================================
        # 2. CRIAR NOVA TABELA
        # =============================================
        logger.info("📋 Criando tabela user_facts_v2...")

        cursor.execute("""
            CREATE TABLE user_facts_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- Identificação
                user_id TEXT NOT NULL,

                -- Estrutura hierárquica
                fact_category TEXT NOT NULL,      -- RELACIONAMENTO, TRABALHO, etc.
                fact_type TEXT NOT NULL,          -- esposa, filho, profissao, etc.
                fact_attribute TEXT NOT NULL,     -- nome, idade, profissao, etc.
                fact_value TEXT NOT NULL,         -- O valor em si

                -- Metadados
                confidence REAL DEFAULT 1.0,      -- Confiança na extração (0.0-1.0)
                extraction_method TEXT DEFAULT 'llm',  -- llm, regex, manual
                context TEXT,                     -- Trecho da conversa que gerou

                -- Rastreabilidade
                source_conversation_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Versionamento
                is_current BOOLEAN DEFAULT 1,
                version INTEGER DEFAULT 1,
                replaced_by INTEGER,              -- ID do fato que substituiu este

                -- Constraints
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (source_conversation_id) REFERENCES conversations(id),
                FOREIGN KEY (replaced_by) REFERENCES user_facts_v2(id)
            )
        """)

        logger.info("   ✅ Tabela criada")

        # =============================================
        # 3. CRIAR ÍNDICES
        # =============================================
        logger.info("📊 Criando índices...")

        indices = [
            ("idx_facts_v2_user", "user_id"),
            ("idx_facts_v2_current", "user_id, is_current"),
            ("idx_facts_v2_category", "user_id, fact_category, is_current"),
            ("idx_facts_v2_type", "user_id, fact_type, is_current"),
            ("idx_facts_v2_lookup", "user_id, fact_category, fact_type, fact_attribute, is_current"),
        ]

        for idx_name, columns in indices:
            cursor.execute(f"""
                CREATE INDEX {idx_name}
                ON user_facts_v2({columns})
            """)
            logger.info(f"   ✅ Índice: {idx_name}")

        # =============================================
        # 4. CRIAR UNIQUE CONSTRAINT
        # =============================================
        logger.info("🔒 Criando constraint de unicidade...")

        cursor.execute("""
            CREATE UNIQUE INDEX idx_facts_v2_unique
            ON user_facts_v2(user_id, fact_category, fact_type, fact_attribute, is_current)
            WHERE is_current = 1
        """)

        logger.info("   ✅ Constraint criado")

        # =============================================
        # 5. MIGRAR DADOS DA TABELA ANTIGA (SE EXISTIR)
        # =============================================
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='user_facts'
        """)

        if cursor.fetchone():
            logger.info("🔄 Migrando dados de user_facts para user_facts_v2...")

            # Buscar fatos atuais
            cursor.execute("""
                SELECT user_id, fact_category, fact_key, fact_value,
                       source_conversation_id, created_at, version, is_current
                FROM user_facts
                WHERE is_current = 1
            """)

            old_facts = cursor.fetchall()
            migrated_count = 0

            for old_fact in old_facts:
                # Tentar mapear para novo formato
                # fact_key pode ser: 'profissao', 'traço', 'pessoa'
                # Precisamos inferir fact_type e fact_attribute

                category = old_fact['fact_category']
                old_key = old_fact['fact_key']
                value = old_fact['fact_value']

                # Mapeamento simples
                if category == 'TRABALHO':
                    fact_type = old_key  # profissao, empresa
                    attribute = 'valor'
                elif category == 'PERSONALIDADE':
                    fact_type = 'traço'
                    attribute = old_key  # tipo
                elif category == 'RELACIONAMENTO':
                    # old_key = 'pessoa', value = 'minha esposa', 'meu pai', etc.
                    fact_type = value.replace('minha ', '').replace('meu ', '').replace('minhas ', '').replace('meus ', '')
                    attribute = 'mencao'  # Apenas menção, sem nome
                else:
                    fact_type = old_key
                    attribute = 'valor'

                try:
                    cursor.execute("""
                        INSERT INTO user_facts_v2
                        (user_id, fact_category, fact_type, fact_attribute, fact_value,
                         confidence, extraction_method, source_conversation_id,
                         created_at, is_current, version)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        old_fact['user_id'],
                        category,
                        fact_type,
                        attribute,
                        value,
                        0.8,  # Confiança média para dados antigos
                        'regex_legacy',
                        old_fact['source_conversation_id'],
                        old_fact['created_at'],
                        1,  # is_current
                        old_fact['version']
                    ))

                    migrated_count += 1

                except sqlite3.IntegrityError as e:
                    logger.warning(f"   ⚠️ Fato duplicado ignorado: {old_fact['fact_key']} - {e}")

            conn.commit()
            logger.info(f"   ✅ {migrated_count} fatos migrados de user_facts")

        # =============================================
        # 6. CRIAR VIEW DE COMPATIBILIDADE
        # =============================================
        logger.info("🔍 Criando view de compatibilidade...")

        cursor.execute("""
            CREATE VIEW user_facts_current AS
            SELECT
                user_id,
                fact_category,
                fact_type,
                fact_attribute,
                fact_value,
                confidence,
                extraction_method,
                created_at,
                updated_at,
                source_conversation_id
            FROM user_facts_v2
            WHERE is_current = 1
            ORDER BY fact_category, fact_type, fact_attribute
        """)

        logger.info("   ✅ View criada")

        # =============================================
        # 7. ESTATÍSTICAS
        # =============================================
        cursor.execute("SELECT COUNT(*) as count FROM user_facts_v2 WHERE is_current = 1")
        total_facts = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(DISTINCT user_id) as count FROM user_facts_v2")
        total_users = cursor.fetchone()['count']

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO")
        logger.info(f"{'='*60}")
        logger.info(f"Total de fatos: {total_facts}")
        logger.info(f"Usuários com fatos: {total_users}")
        logger.info(f"\nPróximos passos:")
        logger.info(f"1. Atualizar jung_core.py para usar user_facts_v2")
        logger.info(f"2. Integrar LLMFactExtractor")
        logger.info(f"3. Testar com conversas reais")

        conn.commit()
        return True

    except Exception as e:
        logger.error(f"❌ Erro na migração: {e}")
        import traceback
        logger.error(traceback.format_exc())
        conn.rollback()
        return False

    finally:
        conn.close()


def show_facts_structure(db_path: str = None):
    """Mostra estrutura de fatos existentes"""

    if db_path is None:
        data_dir = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./data")
        db_path = os.path.join(data_dir, "jung_hybrid.db")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    logger.info(f"\n{'='*60}")
    logger.info(f"ESTRUTURA DE FATOS ATUAL")
    logger.info(f"{'='*60}")

    # Verificar qual tabela existe
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE 'user_facts%'
        ORDER BY name
    """)

    tables = cursor.fetchall()

    for table in tables:
        table_name = table['name']
        logger.info(f"\n📊 Tabela: {table_name}")

        # Schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        logger.info("   Colunas:")
        for col in columns:
            logger.info(f"   - {col['name']}: {col['type']}")

        # Sample data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
        samples = cursor.fetchall()

        if samples:
            logger.info(f"\n   Exemplos de dados ({len(samples)} primeiros):")
            for i, sample in enumerate(samples, 1):
                logger.info(f"\n   {i}. {dict(sample)}")

    conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "show":
        show_facts_structure()
    else:
        success = migrate_to_v2()
        sys.exit(0 if success else 1)
