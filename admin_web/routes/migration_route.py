"""
Rota TEMPORÁRIA para executar migração via web

⚠️ IMPORTANTE: REMOVA ESTA ROTA APÓS A MIGRAÇÃO!

Esta rota permite executar a migração multi-tenant diretamente
pelo navegador, sem precisar de Railway CLI.

Uso:
    1. Acesse: https://seu-app.railway.app/admin/run-migration
    2. Preencha o formulário com email e senha do master
    3. Clique em "Executar Migração"
    4. Aguarde (pode levar alguns segundos)
    5. REMOVA esta rota do código após sucesso!

Autor: Sistema Multi-Tenant JungAgent
Data: 2025-12-29
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
import os
import sys
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from migrations.run_migration_web import run_web_migration

router = APIRouter(prefix="/admin", tags=["migration"])


@router.get("/run-migration", response_class=HTMLResponse)
async def migration_form(request: Request):
    """
    Formulário para executar migração.

    ⚠️ Esta rota deve ser REMOVIDA após a migração!
    """
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Executar Migração Multi-Tenant</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                padding: 20px;
            }

            .container {
                background: white;
                padding: 40px;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                width: 100%;
                max-width: 600px;
            }

            h1 {
                color: #333;
                margin-bottom: 10px;
                font-size: 1.8em;
            }

            .warning {
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }

            .warning h3 {
                color: #856404;
                margin-bottom: 10px;
            }

            .warning ul {
                color: #856404;
                margin-left: 20px;
            }

            .form-group {
                margin-bottom: 20px;
            }

            label {
                display: block;
                margin-bottom: 8px;
                color: #444;
                font-weight: 500;
            }

            input {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 1em;
                transition: all 0.3s;
            }

            input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }

            .btn {
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 1.05em;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
            }

            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
            }

            .info {
                background: #e3f2fd;
                border-left: 4px solid #2196f3;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
                color: #1565c0;
            }

            .loading {
                display: none;
                text-align: center;
                margin-top: 20px;
            }

            .loading.active {
                display: block;
            }

            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Migração Multi-Tenant</h1>
            <p style="color: #666; margin-bottom: 20px;">Sistema de Organizações e Autenticação</p>

            <div class="warning">
                <h3>⚠️ ATENÇÃO - Leia antes de continuar:</h3>
                <ul>
                    <li>Esta migração cria as tabelas multi-tenant no banco de dados</li>
                    <li>Um backup automático será criado antes de qualquer alteração</li>
                    <li>Se algo der errado, o backup será restaurado automaticamente</li>
                    <li>Escolha uma senha forte (mínimo 8 caracteres)</li>
                    <li><strong>IMPORTANTE</strong>: Anote a senha em local seguro!</li>
                </ul>
            </div>

            <form method="POST" action="/admin/run-migration" id="migrationForm">
                <div class="form-group">
                    <label for="master_email">Email do Usuário Master</label>
                    <input
                        type="email"
                        id="master_email"
                        name="master_email"
                        required
                        placeholder="seu@email.com"
                        autofocus
                    >
                    <small style="color: #666;">Este será seu login para acessar o sistema</small>
                </div>

                <div class="form-group">
                    <label for="master_password">Senha do Usuário Master</label>
                    <input
                        type="password"
                        id="master_password"
                        name="master_password"
                        required
                        minlength="8"
                        placeholder="Mínimo 8 caracteres"
                    >
                    <small style="color: #666;">Escolha uma senha forte e anote!</small>
                </div>

                <div class="form-group">
                    <label for="master_name">Nome Completo (Opcional)</label>
                    <input
                        type="text"
                        id="master_name"
                        name="master_name"
                        placeholder="Seu Nome"
                        value="Master Admin"
                    >
                </div>

                <div class="info">
                    <strong>O que esta migração faz:</strong>
                    <ol style="margin-left: 20px; margin-top: 10px;">
                        <li>Cria 5 novas tabelas (organizations, admin_users, etc.)</li>
                        <li>Cria organização "Default"</li>
                        <li>Migra todos os usuários existentes para a org Default</li>
                        <li>Cria seu usuário Master com a senha que você definir</li>
                        <li>Valida que tudo funcionou corretamente</li>
                    </ol>
                </div>

                <button type="submit" class="btn" id="submitBtn">
                    Executar Migração
                </button>

                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p style="color: #667eea; margin-top: 15px; font-weight: 500;">
                        Executando migração...<br>
                        <small>Isso pode levar até 30 segundos. Não feche esta página!</small>
                    </p>
                </div>
            </form>
        </div>

        <script>
            document.getElementById('migrationForm').addEventListener('submit', function() {
                // Mostrar loading
                document.getElementById('loading').classList.add('active');
                document.getElementById('submitBtn').disabled = true;
                document.getElementById('submitBtn').textContent = 'Executando...';
            });
        </script>
    </body>
    </html>
    """


@router.post("/run-migration", response_class=HTMLResponse)
async def run_migration(
    master_email: str = Form(...),
    master_password: str = Form(...),
    master_name: str = Form("Master Admin")
):
    """
    Executa migração multi-tenant.

    ⚠️ Esta rota deve ser REMOVIDA após a migração!

    Args:
        master_email: Email do usuário master
        master_password: Senha do usuário master
        master_name: Nome completo do master
    """
    # Caminho do banco de dados
    # No Railway, o banco fica em /app/jung_memory.db
    # Localmente, pode estar na raiz do projeto
    db_path = os.getenv("DATABASE_PATH", "/app/jung_memory.db")

    # Se não existir, tentar path local
    if not os.path.exists(db_path):
        db_path = os.path.join(os.getcwd(), "jung_memory.db")

    # Executar migração
    html_output = run_web_migration(
        db_path=db_path,
        master_email=master_email,
        master_password=master_password,
        master_name=master_name
    )

    return html_output


# ============================================
# INSTRUÇÕES DE USO
# ============================================

"""
PASSO A PASSO:

1. Adicione esta rota em main.py:

    from admin_web.routes.migration_route import router as migration_router
    app.include_router(migration_router)

2. Faça deploy no Railway

3. Acesse no navegador:
    https://seu-app.railway.app/admin/run-migration

4. Preencha o formulário:
    - Email: seu email real
    - Senha: escolha uma senha forte (mínimo 8 caracteres)
    - Nome: seu nome (opcional)

5. Clique em "Executar Migração"

6. Aguarde (pode levar 10-30 segundos)

7. Se der sucesso, você verá uma página com logs verdes

8. IMPORTANTE: Após a migração, REMOVA esta rota de main.py:
    # app.include_router(migration_router)  # <- COMENTAR OU DELETAR

9. Faça novo deploy sem a rota de migração

10. Acesse /admin/login e faça login com o email/senha que você criou

PRONTO! Sistema multi-tenant funcionando! 🎉
"""
