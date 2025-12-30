-- ========================================
-- MIGRAÇÃO MULTI-TENANT JUNGAGENT ADMIN
-- ========================================
-- Data: 2025-12-29
-- Descrição: Adiciona suporte a múltiplas organizações
-- Versão: 1.0
-- ========================================

-- ATENÇÃO: Execute este script APENAS após fazer backup do banco!

-- ========================================
-- 1. CRIAR NOVAS TABELAS
-- ========================================

-- Organizações (empresas clientes)
CREATE TABLE IF NOT EXISTS organizations (
    org_id TEXT PRIMARY KEY,              -- UUID gerado
    org_name TEXT NOT NULL,               -- "Acme Corp"
    org_slug TEXT UNIQUE NOT NULL,        -- "acme-corp" (URL-friendly)
    industry TEXT,                         -- "Tecnologia", "Saúde"
    size TEXT,                             -- "small", "medium", "large"
    subscription_tier TEXT DEFAULT 'basic', -- "basic", "pro", "enterprise"
    subscription_status TEXT DEFAULT 'active', -- "active", "trial", "suspended"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    contact_email TEXT,
    contact_phone TEXT,
    logo_url TEXT,                         -- URL do logo da empresa
    metadata TEXT                          -- JSON com configs específicas
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_org_slug ON organizations(org_slug);

-- Usuários admin (master + org admins)
CREATE TABLE IF NOT EXISTS admin_users (
    admin_id TEXT PRIMARY KEY,             -- UUID gerado
    email TEXT UNIQUE NOT NULL,            -- Login (ex: admin@empresa.com)
    password_hash TEXT NOT NULL,           -- bcrypt hash
    full_name TEXT NOT NULL,               -- Nome completo
    role TEXT NOT NULL CHECK(role IN ('master', 'org_admin')),
    org_id TEXT,                           -- NULL para master, preenchido para org_admin
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    permissions TEXT,                      -- JSON com permissões granulares (futuro)
    FOREIGN KEY (org_id) REFERENCES organizations(org_id)
);

CREATE INDEX IF NOT EXISTS idx_admin_email ON admin_users(email);
CREATE INDEX IF NOT EXISTS idx_admin_org ON admin_users(org_id);

-- Mapeamento usuários ↔ organizações
CREATE TABLE IF NOT EXISTS user_organization_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,                 -- FK para users.user_id (tabela existente)
    org_id TEXT NOT NULL,                  -- FK para organizations.org_id
    role TEXT,                             -- "employee", "manager", etc.
    department TEXT,                       -- "Engenharia", "Vendas"
    hire_date DATE,
    status TEXT DEFAULT 'active',          -- "active", "inactive", "terminated"
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by TEXT,                         -- admin_id que adicionou
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (org_id) REFERENCES organizations(org_id),
    UNIQUE(user_id, org_id)                -- Um user pode estar em múltiplas orgs
);

CREATE INDEX IF NOT EXISTS idx_uom_user ON user_organization_mapping(user_id);
CREATE INDEX IF NOT EXISTS idx_uom_org ON user_organization_mapping(org_id);
CREATE INDEX IF NOT EXISTS idx_uom_status ON user_organization_mapping(status);

-- Sessões de admin
CREATE TABLE IF NOT EXISTS admin_sessions (
    session_id TEXT PRIMARY KEY,           -- Token UUID
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

-- Logs de auditoria
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id TEXT NOT NULL,
    org_id TEXT,                           -- Qual org estava sendo acessada
    action TEXT NOT NULL,                  -- 'view_user', 'generate_report', etc.
    resource_type TEXT,                    -- 'user', 'psychometrics', 'report'
    resource_id TEXT,                      -- user_id, report_id, etc.
    ip_address TEXT,
    user_agent TEXT,
    details TEXT,                          -- JSON com dados adicionais
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admin_users(admin_id),
    FOREIGN KEY (org_id) REFERENCES organizations(org_id)
);

CREATE INDEX IF NOT EXISTS idx_audit_admin ON audit_log(admin_id);
CREATE INDEX IF NOT EXISTS idx_audit_org ON audit_log(org_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);

-- ========================================
-- 2. SEED DE DADOS INICIAIS
-- ========================================

-- Criar organização "Default" para migrar dados existentes
INSERT OR IGNORE INTO organizations (
    org_id,
    org_name,
    org_slug,
    industry,
    size,
    subscription_tier,
    subscription_status,
    contact_email
)
VALUES (
    'default-org',
    'Sistema Default',
    'default',
    'Sistema',
    'large',
    'enterprise',
    'active',
    'admin@jungagent.com'
);

-- ATENÇÃO: O usuário master será criado pelo script Python de migração
-- para permitir definir email e senha customizados

-- ========================================
-- 3. MIGRAR DADOS EXISTENTES
-- ========================================

-- Associar todos os usuários existentes à organização "Default"
-- Isso garante que nenhum dado é perdido na migração
INSERT OR IGNORE INTO user_organization_mapping (
    user_id,
    org_id,
    status,
    added_by,
    added_at
)
SELECT
    user_id,
    'default-org',
    'active',
    'system-migration',
    CURRENT_TIMESTAMP
FROM users
WHERE platform = 'telegram';

-- ========================================
-- 4. VERIFICAÇÕES DE INTEGRIDADE
-- ========================================

-- As verificações são feitas pelo script Python
-- Este arquivo SQL apenas cria a estrutura

-- ========================================
-- FIM DA MIGRAÇÃO
-- ========================================

-- Para verificar manualmente após execução:
-- SELECT COUNT(*) FROM organizations;  -- Deve ser >= 1
-- SELECT COUNT(*) FROM admin_users WHERE role = 'master';  -- Deve ser >= 1
-- SELECT COUNT(*) FROM user_organization_mapping;  -- Deve ser = número de users
