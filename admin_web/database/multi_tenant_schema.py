"""
Schema Multi-Tenant para JungAgent Admin

Este módulo define o schema de banco de dados para suporte a múltiplas organizações,
permitindo que empresas clientes acessem apenas os dados de seus colaboradores.

Tabelas:
    - organizations: Empresas clientes
    - admin_users: Usuários administrativos (master + org admins)
    - user_organization_mapping: Vínculo colaboradores ↔ empresas
    - admin_sessions: Gestão de sessões
    - audit_log: Logs de auditoria

Autor: Sistema Multi-Tenant JungAgent
Data: 2025-12-29
"""

import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MultiTenantSchema:
    """
    Gerenciador de schema multi-tenant
    """

    # SQL para criar todas as tabelas multi-tenant
    SCHEMA_SQL = """
    -- ========================================
    -- TABELAS MULTI-TENANT
    -- ========================================

    -- 1. ORGANIZATIONS - Empresas Clientes
    CREATE TABLE IF NOT EXISTS organizations (
        org_id TEXT PRIMARY KEY,
        org_name TEXT NOT NULL,
        org_slug TEXT UNIQUE NOT NULL,
        industry TEXT,
        size TEXT,
        subscription_tier TEXT DEFAULT 'basic',
        subscription_status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        contact_email TEXT,
        contact_phone TEXT,
        logo_url TEXT,
        metadata TEXT
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_org_slug ON organizations(org_slug);

    -- 2. ADMIN_USERS - Usuários Admin (Master + Org Admins)
    CREATE TABLE IF NOT EXISTS admin_users (
        admin_id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('master', 'org_admin')),
        org_id TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        permissions TEXT,
        FOREIGN KEY (org_id) REFERENCES organizations(org_id)
    );

    CREATE INDEX IF NOT EXISTS idx_admin_email ON admin_users(email);
    CREATE INDEX IF NOT EXISTS idx_admin_org ON admin_users(org_id);

    -- 3. USER_ORGANIZATION_MAPPING - Vínculo Colaboradores ↔ Empresas
    CREATE TABLE IF NOT EXISTS user_organization_mapping (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        org_id TEXT NOT NULL,
        role TEXT,
        department TEXT,
        hire_date DATE,
        status TEXT DEFAULT 'active',
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        added_by TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (org_id) REFERENCES organizations(org_id),
        UNIQUE(user_id, org_id)
    );

    CREATE INDEX IF NOT EXISTS idx_uom_user ON user_organization_mapping(user_id);
    CREATE INDEX IF NOT EXISTS idx_uom_org ON user_organization_mapping(org_id);
    CREATE INDEX IF NOT EXISTS idx_uom_status ON user_organization_mapping(status);

    -- 4. ADMIN_SESSIONS - Gestão de Sessões
    CREATE TABLE IF NOT EXISTS admin_sessions (
        session_id TEXT PRIMARY KEY,
        admin_id TEXT NOT NULL,
        ip_address TEXT,
        user_agent TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        FOREIGN KEY (admin_id) REFERENCES admin_users(admin_id)
    );

    CREATE INDEX IF NOT EXISTS idx_session_admin ON admin_sessions(admin_id);
    CREATE INDEX IF NOT EXISTS idx_session_expires ON admin_sessions(expires_at);

    -- 5. AUDIT_LOG - Logs de Auditoria
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id TEXT NOT NULL,
        org_id TEXT,
        action TEXT NOT NULL,
        resource_type TEXT,
        resource_id TEXT,
        ip_address TEXT,
        user_agent TEXT,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (admin_id) REFERENCES admin_users(admin_id),
        FOREIGN KEY (org_id) REFERENCES organizations(org_id)
    );

    CREATE INDEX IF NOT EXISTS idx_audit_admin ON audit_log(admin_id);
    CREATE INDEX IF NOT EXISTS idx_audit_org ON audit_log(org_id);
    CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
    """

    @staticmethod
    def create_tables(conn: sqlite3.Connection) -> bool:
        """
        Cria todas as tabelas multi-tenant no banco de dados.

        Args:
            conn: Conexão SQLite

        Returns:
            True se sucesso, False se erro
        """
        try:
            cursor = conn.cursor()

            # Executar schema SQL
            cursor.executescript(MultiTenantSchema.SCHEMA_SQL)

            conn.commit()
            logger.info("✅ Tabelas multi-tenant criadas com sucesso")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao criar tabelas multi-tenant: {e}")
            conn.rollback()
            return False

    @staticmethod
    def verify_tables(conn: sqlite3.Connection) -> dict:
        """
        Verifica se todas as tabelas multi-tenant existem.

        Args:
            conn: Conexão SQLite

        Returns:
            Dict com status de cada tabela
        """
        cursor = conn.cursor()

        tables = [
            'organizations',
            'admin_users',
            'user_organization_mapping',
            'admin_sessions',
            'audit_log'
        ]

        status = {}

        for table in tables:
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """, (table,))

            exists = cursor.fetchone() is not None
            status[table] = exists

        return status

    @staticmethod
    def get_table_counts(conn: sqlite3.Connection) -> dict:
        """
        Retorna contagem de registros em cada tabela.

        Args:
            conn: Conexão SQLite

        Returns:
            Dict com contagens
        """
        cursor = conn.cursor()

        counts = {}

        tables = [
            'organizations',
            'admin_users',
            'user_organization_mapping',
            'admin_sessions',
            'audit_log'
        ]

        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cursor.fetchone()[0]
            except:
                counts[table] = 0

        return counts


def init_multi_tenant_schema(db_path: str) -> bool:
    """
    Inicializa schema multi-tenant em um banco de dados.

    Args:
        db_path: Caminho para o arquivo .db

    Returns:
        True se sucesso
    """
    try:
        conn = sqlite3.connect(db_path)

        # Criar tabelas
        success = MultiTenantSchema.create_tables(conn)

        if success:
            # Verificar
            status = MultiTenantSchema.verify_tables(conn)
            all_exist = all(status.values())

            if all_exist:
                logger.info("✅ Schema multi-tenant inicializado com sucesso")
                logger.info(f"   Tabelas criadas: {list(status.keys())}")

                # Mostrar contagens
                counts = MultiTenantSchema.get_table_counts(conn)
                logger.info(f"   Contagens: {counts}")

                return True
            else:
                missing = [t for t, exists in status.items() if not exists]
                logger.error(f"❌ Tabelas faltando: {missing}")
                return False

        return False

    except Exception as e:
        logger.error(f"❌ Erro ao inicializar schema: {e}")
        return False

    finally:
        conn.close()


if __name__ == '__main__':
    # Teste do schema
    import tempfile
    import os

    # Criar banco temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        test_db = f.name

    print(f"🧪 Testando schema em: {test_db}")

    success = init_multi_tenant_schema(test_db)

    if success:
        print("✅ Teste do schema passou!")

        # Verificar tabelas
        conn = sqlite3.connect(test_db)
        status = MultiTenantSchema.verify_tables(conn)

        print("\n📊 Status das tabelas:")
        for table, exists in status.items():
            print(f"   {'✅' if exists else '❌'} {table}")

        conn.close()
    else:
        print("❌ Teste do schema falhou!")

    # Limpar
    os.unlink(test_db)
