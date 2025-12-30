"""
Script de Migração via Web - Railway

Este script permite executar a migração multi-tenant diretamente
através de uma rota web, sem precisar usar Railway CLI.

IMPORTANTE: Esta rota deve ser REMOVIDA após a migração!

Autor: Sistema Multi-Tenant JungAgent
Data: 2025-12-29
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from admin_web.auth.auth_manager import AuthManager
from admin_web.database.multi_tenant_schema import MultiTenantSchema
import bcrypt
import uuid


class WebMigrationRunner:
    """
    Executa migração multi-tenant com output HTML.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.output = []
        self.success = False

    def log(self, message: str, level: str = "info"):
        """Adiciona mensagem ao output"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        icons = {
            "info": "ℹ️",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️"
        }

        icon = icons.get(level, "•")
        self.output.append(f"[{timestamp}] {icon} {message}")

    def backup_database(self) -> str:
        """Cria backup do banco"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.db_path}.backup_{timestamp}"

        try:
            shutil.copy2(self.db_path, backup_path)
            file_size = os.path.getsize(backup_path) / 1024
            self.log(f"Backup criado: {backup_path} ({file_size:.2f} KB)", "success")
            return backup_path
        except Exception as e:
            self.log(f"Erro ao criar backup: {e}", "error")
            raise

    def run_migration(self, master_email: str, master_password: str, master_name: str = "Master Admin") -> bool:
        """
        Executa migração completa.

        Args:
            master_email: Email do usuário master
            master_password: Senha do usuário master
            master_name: Nome completo do master

        Returns:
            True se sucesso
        """
        self.log("=== INICIANDO MIGRAÇÃO MULTI-TENANT ===", "info")

        # 1. Verificar banco
        self.log("Verificando banco de dados...", "info")

        if not os.path.exists(self.db_path):
            self.log(f"Banco não encontrado: {self.db_path}", "error")
            return False

        # 2. Backup
        self.log("Criando backup...", "info")

        try:
            backup_path = self.backup_database()
        except Exception as e:
            self.log(f"Falha ao criar backup: {e}", "error")
            return False

        # 3. Conectar ao banco
        conn = None

        try:
            conn = sqlite3.connect(self.db_path)
            self.log("Conectado ao banco de dados", "success")

            # 4. Criar tabelas multi-tenant
            self.log("Criando tabelas multi-tenant...", "info")

            if not MultiTenantSchema.create_tables(conn):
                raise Exception("Falha ao criar tabelas")

            self.log("Tabelas criadas com sucesso", "success")

            # 5. Criar organização Default
            self.log("Criando organização Default...", "info")

            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO organizations (
                    org_id, org_name, org_slug, industry, size,
                    subscription_tier, subscription_status, contact_email
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'default-org',
                'Sistema Default',
                'default',
                'Sistema',
                'large',
                'enterprise',
                'active',
                master_email
            ))

            conn.commit()
            self.log("Organização Default criada", "success")

            # 6. Migrar usuários existentes
            self.log("Migrando usuários existentes...", "info")

            cursor.execute("""
                INSERT OR IGNORE INTO user_organization_mapping (
                    user_id, org_id, status, added_by, added_at
                )
                SELECT
                    user_id,
                    'default-org',
                    'active',
                    'system-migration',
                    CURRENT_TIMESTAMP
                FROM users
                WHERE platform = 'telegram'
            """)

            migrated_users = cursor.rowcount
            conn.commit()

            self.log(f"{migrated_users} usuários migrados para org Default", "success")

            # 7. Criar usuário master
            self.log("Criando usuário master...", "info")

            # Verificar se já existe
            cursor.execute("SELECT admin_id FROM admin_users WHERE email = ?", (master_email,))

            if cursor.fetchone():
                self.log(f"Usuário master já existe: {master_email}", "warning")
            else:
                # Criar password hash
                password_hash = bcrypt.hashpw(master_password.encode('utf-8'), bcrypt.gensalt())
                admin_id = f"master-admin-{uuid.uuid4().hex[:8]}"

                cursor.execute("""
                    INSERT INTO admin_users (
                        admin_id, email, password_hash, full_name, role, org_id, is_active
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    admin_id,
                    master_email,
                    password_hash.decode('utf-8'),
                    master_name,
                    'master',
                    None,
                    True
                ))

                conn.commit()
                self.log(f"Usuário master criado: {master_email}", "success")

            # 8. Verificar resultado
            self.log("Verificando resultado...", "info")

            cursor.execute("SELECT COUNT(*) FROM organizations")
            org_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM admin_users")
            admin_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM admin_users WHERE role = 'master'")
            master_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM user_organization_mapping")
            mapping_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE platform = 'telegram'")
            total_users = cursor.fetchone()[0]

            self.log("--- ESTATÍSTICAS DA MIGRAÇÃO ---", "info")
            self.log(f"Organizações: {org_count}", "info")
            self.log(f"Admins totais: {admin_count}", "info")
            self.log(f"Masters: {master_count}", "info")
            self.log(f"Usuários migrados: {mapping_count}", "info")
            self.log(f"Usuários totais: {total_users}", "info")

            # Validar
            if master_count < 1:
                raise Exception("Nenhum usuário master criado!")

            if mapping_count != total_users:
                self.log(
                    f"AVISO: Nem todos os usuários foram migrados ({mapping_count}/{total_users})",
                    "warning"
                )

            # 9. Sucesso!
            self.log("=== MIGRAÇÃO CONCLUÍDA COM SUCESSO ===", "success")
            self.log(f"Backup salvo em: {backup_path}", "info")
            self.log(f"Email master: {master_email}", "info")
            self.log("IMPORTANTE: Guarde a senha em local seguro!", "warning")

            self.success = True
            return True

        except Exception as e:
            self.log(f"ERRO NA MIGRAÇÃO: {e}", "error")
            self.log("Tentando restaurar backup...", "warning")

            try:
                if conn:
                    conn.close()

                shutil.copy2(backup_path, self.db_path)
                self.log("Backup restaurado com sucesso", "success")
                self.log("Banco de dados inalterado", "info")

            except Exception as restore_error:
                self.log(f"ERRO CRÍTICO ao restaurar backup: {restore_error}", "error")
                self.log(f"Backup manual disponível em: {backup_path}", "warning")

            return False

        finally:
            if conn:
                conn.close()

    def get_html_output(self) -> str:
        """Retorna output formatado em HTML"""

        status_color = "#4caf50" if self.success else "#f44336"
        status_text = "SUCESSO" if self.success else "ERRO"

        logs_html = "<br>".join([
            f'<div style="font-family: monospace; padding: 4px 0;">{line}</div>'
            for line in self.output
        ])

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Migração Multi-Tenant - {status_text}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 900px;
                    margin: 40px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: {status_color};
                    border-bottom: 3px solid {status_color};
                    padding-bottom: 10px;
                }}
                .logs {{
                    background: #1e1e1e;
                    color: #d4d4d4;
                    padding: 20px;
                    border-radius: 4px;
                    overflow-x: auto;
                    margin: 20px 0;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 24px;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    margin-top: 20px;
                }}
                .btn:hover {{
                    background: #5568d3;
                }}
                .warning {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                    color: #856404;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Migração Multi-Tenant - {status_text}</h1>

                <div class="logs">
                    {logs_html}
                </div>

                {self._get_next_steps_html()}

                <a href="/admin/login" class="btn">Ir para Login</a>
            </div>
        </body>
        </html>
        """

    def _get_next_steps_html(self) -> str:
        """Retorna próximos passos em HTML"""

        if self.success:
            return """
            <div style="background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; color: #155724;">
                <h3 style="margin-top: 0;">✅ Próximos Passos:</h3>
                <ol>
                    <li>Acesse <strong>/admin/login</strong></li>
                    <li>Faça login com o email e senha que você configurou</li>
                    <li><strong>IMPORTANTE</strong>: Remova a rota /admin/run-migration do código!</li>
                </ol>
            </div>
            """
        else:
            return """
            <div class="warning">
                <h3 style="margin-top: 0;">⚠️ Migração Falhou</h3>
                <p>Verifique os logs acima para identificar o erro.</p>
                <p>O banco de dados foi restaurado automaticamente.</p>
                <p>Você pode tentar novamente ou contatar o suporte.</p>
            </div>
            """


def run_web_migration(db_path: str, master_email: str, master_password: str, master_name: str = "Master Admin") -> str:
    """
    Executa migração e retorna HTML com resultado.

    Args:
        db_path: Caminho para o banco SQLite
        master_email: Email do usuário master
        master_password: Senha do usuário master
        master_name: Nome completo do master

    Returns:
        HTML com resultado da migração
    """
    runner = WebMigrationRunner(db_path)
    runner.run_migration(master_email, master_password, master_name)
    return runner.get_html_output()
