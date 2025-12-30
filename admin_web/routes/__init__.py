"""
Rotas do Admin Web - Multi-Tenant System

Módulos:
    - auth_routes: Login/Logout
    - dashboard_routes: Master e Org Admin Dashboards

IMPORTANTE: Este __init__.py resolve conflito entre:
    - admin_web/routes.py (arquivo antigo com rotas legadas)
    - admin_web/routes/ (pasta nova com rotas multi-tenant)

Para manter compatibilidade, re-exportamos o router do arquivo antigo.
"""

# Re-exportar router do arquivo legado para manter compatibilidade com main.py
# main.py faz: from admin_web.routes import router as admin_router
# Isso agora pega o router de admin_web/routes.py (o arquivo, não a pasta)
import sys
import os

# Adicionar diretório pai ao path temporariamente
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Importar router do arquivo routes.py (irmão desta pasta)
try:
    # Hack: importar o módulo routes.py que está em admin_web/
    import importlib.util
    routes_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'routes.py')
    spec = importlib.util.spec_from_file_location("admin_web_routes_legacy", routes_file)
    legacy_routes = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy_routes)

    # Re-exportar o router
    router = legacy_routes.router

except Exception as e:
    import logging
    logging.error(f"❌ Erro ao importar routes.py legado: {e}")
    # Criar router vazio como fallback
    from fastapi import APIRouter
    router = APIRouter()
