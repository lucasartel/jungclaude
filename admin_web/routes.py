from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import os
from typing import Dict, List, Optional
import logging

# Importar core do Jung (opcional - pode falhar se dependências não estiverem disponíveis)
try:
    from jung_core import DatabaseManager, JungianEngine, Config
    JUNG_CORE_AVAILABLE = True
except Exception as e:
    logging.warning(f"jung_core não disponível: {e}")
    DatabaseManager = None
    JungianEngine = None
    Config = None
    JUNG_CORE_AVAILABLE = False

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="admin_web/templates")
security = HTTPBasic()
logger = logging.getLogger(__name__)

# Inicializar componentes (Singleton pattern simples)
_db_manager = None

def get_db():
    global _db_manager
    if not JUNG_CORE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Database não disponível - jung_core não carregado"
        )
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

# ============================================================================
# AUTENTICAÇÃO
# ============================================================================

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verifica credenciais básicas (admin/admin por padrão ou via ENV)"""
    correct_username = os.getenv("ADMIN_USER", "admin")
    correct_password = os.getenv("ADMIN_PASSWORD", "admin")
    
    is_correct_username = secrets.compare_digest(credentials.username, correct_username)
    is_correct_password = secrets.compare_digest(credentials.password, correct_password)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# ============================================================================
# ROTAS DE PÁGINA (HTML)
# ============================================================================

@router.get("/test")
async def test_route():
    """Rota de teste simples - não requer autenticação"""
    return {
        "status": "ok",
        "message": "Admin routes carregadas com sucesso!",
        "jung_core_available": JUNG_CORE_AVAILABLE
    }

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Depends(verify_credentials)):
    """Dashboard principal - com fallback para quando jung_core não está disponível"""
    
    if not JUNG_CORE_AVAILABLE:
        # Dashboard de diagnóstico quando jung_core não está disponível
        import sys
        import platform
        
        # Tentar importar dependências individualmente para diagnóstico
        deps_status = {}
        for dep in ["openai", "chromadb", "langchain", "langchain_openai", "langchain_chroma"]:
            try:
                __import__(dep)
                deps_status[dep] = "✅ OK"
            except ImportError as e:
                deps_status[dep] = f"❌ {str(e)[:50]}"
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "jung_core_available": False,
            "total_users": 0,
            "total_interactions": 0,
            "total_conflicts": 0,
            "users": [],
            "diagnostic_mode": True,
            "python_version": platform.python_version(),
            "dependencies": deps_status,
            "error_message": "jung_core não pôde ser carregado. Verifique os logs para detalhes."
        })
    
    # Modo normal com jung_core disponível
    db = get_db()
    
    # Estatísticas Gerais
    sqlite_users = db.get_all_users(platform="telegram")
    total_interactions = sum(u.get('total_messages', 0) for u in sqlite_users)
    
    # Conflitos
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM archetype_conflicts")
    total_conflicts = cursor.fetchone()[0]
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "jung_core_available": True,
        "total_users": len(sqlite_users),
        "total_interactions": total_interactions,
        "total_conflicts": total_conflicts,
        "users": sqlite_users[:5],  # Top 5 recentes
        "diagnostic_mode": False
    })

@router.get("/users", response_class=HTMLResponse)
async def users_list(request: Request, username: str = Depends(verify_credentials)):
    """Lista de usuários"""
    db = get_db()
    users = db.get_all_users(platform="telegram")
    return templates.TemplateResponse("users.html", {"request": request, "users": users})

@router.get("/sync-check", response_class=HTMLResponse)
async def sync_check_page(request: Request, username: str = Depends(verify_credentials)):
    """Página de diagnóstico de sincronização"""
    return templates.TemplateResponse("sync_check.html", {"request": request})

# ============================================================================
# ROTAS DE API (HTMX / JSON)
# ============================================================================

@router.get("/api/sync-status")
async def get_sync_status(username: str = Depends(verify_credentials)):
    """Retorna status de sincronização para o header"""
    # Lógica simplificada para o header
    return HTMLResponse(
        '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Sistema Online</span>'
    )

@router.get("/api/diagnose")
async def run_diagnosis(username: str = Depends(verify_credentials)):
    """Roda diagnóstico completo (SQLite vs Chroma)"""
    db = get_db()
    
    # SQLite Stats
    sqlite_users = db.get_all_users(platform="telegram")
    sqlite_count = sum(u.get('total_messages', 0) for u in sqlite_users)
    
    # Chroma Stats
    chroma_count = 0
    chroma_status = "Desconectado"
    
    if db.chroma_enabled:
        try:
            chroma_count = db.vectorstore._collection.count()
            chroma_status = "Conectado"
        except Exception as e:
            chroma_status = f"Erro: {str(e)}"
    
    # Renderizar resultado (fragmento HTML)
    html = f"""
    <div class="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <div class="bg-white overflow-hidden shadow rounded-lg">
            <div class="px-4 py-5 sm:p-6">
                <dt class="text-sm font-medium text-gray-500 truncate">SQLite (Metadados)</dt>
                <dd class="mt-1 text-3xl font-semibold text-gray-900">{sqlite_count}</dd>
            </div>
        </div>
        <div class="bg-white overflow-hidden shadow rounded-lg">
            <div class="px-4 py-5 sm:p-6">
                <dt class="text-sm font-medium text-gray-500 truncate">ChromaDB (Vetores)</dt>
                <dd class="mt-1 text-3xl font-semibold text-gray-900">{chroma_count}</dd>
                <dd class="mt-1 text-sm text-gray-500">{chroma_status}</dd>
            </div>
        </div>
    </div>
    """
    
    if abs(sqlite_count - chroma_count) > 5:
        html += """
        <div class="mt-4 bg-red-50 border-l-4 border-red-400 p-4">
            <div class="flex">
                <div class="flex-shrink-0">⚠️</div>
                <div class="ml-3">
                    <p class="text-sm text-red-700">
                        Descasamento detectado! Diferença de {diff} registros.
                    </p>
                </div>
            </div>
        </div>
        """.format(diff=abs(sqlite_count - chroma_count))
    else:
        html += """
        <div class="mt-4 bg-green-50 border-l-4 border-green-400 p-4">
            <div class="flex">
                <div class="flex-shrink-0">✅</div>
                <div class="ml-3">
                    <p class="text-sm text-green-700">
                        Sincronização saudável.
                    </p>
                </div>
            </div>
        </div>
        """
        
    return HTMLResponse(html)
