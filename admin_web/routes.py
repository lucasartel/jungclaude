from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import os
from typing import Dict, List, Optional
import logging

# Importar core do Jung (opcional - pode falhar se dependências não estiverem disponíveis)
JUNG_CORE_ERROR = None
try:
    from jung_core import DatabaseManager, JungianEngine, Config
    JUNG_CORE_AVAILABLE = True
except Exception as e:
    import traceback
    JUNG_CORE_ERROR = traceback.format_exc()
    logging.error(f"❌ Erro ao importar jung_core: {e}")
    logging.error(f"Traceback:\n{JUNG_CORE_ERROR}")
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
            "error_message": "jung_core não pôde ser carregado.",
            "error_traceback": JUNG_CORE_ERROR
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

@router.get("/user/{user_id}/analysis", response_class=HTMLResponse)
async def user_analysis_page(request: Request, user_id: str, username: str = Depends(verify_credentials)):
    """Página de análise MBTI/Jungiana do usuário"""
    db = get_db()

    # Buscar usuário
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Buscar conversas
    conversations = db.get_user_conversations(user_id, limit=50)
    total_conversations = db.count_conversations(user_id)

    # Buscar conflitos
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as count FROM archetype_conflicts WHERE user_id = ?
    """, (user_id,))
    total_conflicts = cursor.fetchone()[0]

    return templates.TemplateResponse("user_analysis.html", {
        "request": request,
        "user": user,
        "user_id": user_id,
        "total_conversations": total_conversations,
        "total_conflicts": total_conflicts,
        "conversations": conversations[:10]  # Últimas 10 para preview
    })

@router.get("/user/{user_id}/development", response_class=HTMLResponse)
async def user_development_page(request: Request, user_id: str, username: str = Depends(verify_credentials)):
    """Página de desenvolvimento do agente do usuário"""
    db = get_db()

    # Buscar usuário
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Buscar milestones
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT * FROM user_milestones
        WHERE user_id = ?
        ORDER BY achieved_at DESC
        LIMIT 20
    """, (user_id,))
    milestones = [dict(row) for row in cursor.fetchall()]

    # Buscar padrões
    cursor.execute("""
        SELECT * FROM user_patterns
        WHERE user_id = ?
        ORDER BY confidence_score DESC, frequency_count DESC
        LIMIT 10
    """, (user_id,))
    patterns = [dict(row) for row in cursor.fetchall()]

    # Buscar conflitos recentes
    conflicts = db.get_user_conflicts(user_id, limit=10)

    # Stats
    total_conversations = db.count_conversations(user_id)

    return templates.TemplateResponse("user_development.html", {
        "request": request,
        "user": user,
        "user_id": user_id,
        "total_conversations": total_conversations,
        "milestones": milestones,
        "patterns": patterns,
        "conflicts": conflicts
    })

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

@router.post("/api/user/{user_id}/analyze-mbti")
async def analyze_user_mbti(request: Request, user_id: str, username: str = Depends(verify_credentials)):
    """Analisa padrão MBTI do usuário usando Grok"""
    import re
    import json
    from openai import OpenAI

    db = get_db()

    # Verificar se XAI_API_KEY está disponível
    xai_api_key = os.getenv("XAI_API_KEY")
    if not xai_api_key:
        return JSONResponse({
            "error": "XAI_API_KEY não configurada",
            "type_indicator": "XXXX",
            "confidence": 0,
            "summary": "Configure a variável XAI_API_KEY para habilitar análise MBTI"
        }, status_code=503)

    # Buscar conversas do usuário
    conversations = db.get_user_conversations(user_id, limit=30)

    if len(conversations) < 5:
        return JSONResponse({
            "error": "Conversas insuficientes",
            "type_indicator": "XXXX",
            "confidence": 0,
            "summary": f"São necessárias pelo menos 5 conversas para análise. Atualmente: {len(conversations)}"
        }, status_code=400)

    # Extrair inputs do usuário
    user_inputs = [conv['user_input'] for conv in conversations if conv.get('user_input')]

    if len(user_inputs) < 5:
        return JSONResponse({
            "error": "Dados insuficientes",
            "type_indicator": "XXXX",
            "confidence": 0,
            "summary": "Dados de conversas insuficientes para análise"
        }, status_code=400)

    # Preparar amostra
    sample_size = min(15, len(user_inputs))
    first_inputs = user_inputs[:sample_size // 2]
    last_inputs = user_inputs[-(sample_size // 2):] if len(user_inputs) > sample_size // 2 else []

    inputs_text = "**Mensagens Iniciais:**\n"
    inputs_text += "\n".join([f"- {inp[:150]}..." for inp in first_inputs])

    if last_inputs:
        inputs_text += "\n\n**Mensagens Recentes:**\n"
        inputs_text += "\n".join([f"- {inp[:150]}..." for inp in last_inputs])

    # Calcular estatísticas
    total_conversations = len(conversations)
    avg_tension = sum(conv.get('tension_level', 0) for conv in conversations) / total_conversations
    avg_affective = sum(conv.get('affective_charge', 0) for conv in conversations) / total_conversations

    # Prompt para Grok
    prompt = f"""
Analise o padrão psicológico deste usuário seguindo princípios junguianos e o modelo MBTI.

**ESTATÍSTICAS:**
- Total de interações: {total_conversations}
- Tensão média: {avg_tension:.2f}/10
- Carga afetiva média: {avg_affective:.1f}/100

**MENSAGENS DO USUÁRIO:**
{inputs_text}

Retorne JSON com esta estrutura EXATA:
{{
    "type_indicator": "XXXX (ex: INFP)",
    "confidence": 0-100,
    "dimensions": {{
        "E_I": {{
            "score": -100 a +100 (negativo=E, positivo=I),
            "interpretation": "Análise com evidências",
            "key_indicators": ["indicador1", "indicador2"]
        }},
        "S_N": {{"score": -100 a +100, "interpretation": "...", "key_indicators": [...]}},
        "T_F": {{"score": -100 a +100, "interpretation": "...", "key_indicators": [...]}},
        "J_P": {{"score": -100 a +100, "interpretation": "...", "key_indicators": [...]}}
    }},
    "dominant_function": "Ex: Ni (Intuição Introvertida)",
    "auxiliary_function": "Ex: Fe",
    "summary": "Resumo analítico em 2-3 frases",
    "potentials": ["potencial1", "potencial2"],
    "challenges": ["desafio1", "desafio2"],
    "recommendations": ["recomendação1", "recomendação2"]
}}
"""

    try:
        # Chamar Grok
        client = OpenAI(
            api_key=xai_api_key,
            base_url="https://api.x.ai/v1"
        )

        response = client.chat.completions.create(
            model="grok-beta",
            messages=[
                {"role": "system", "content": "Você é um analista jungiano especializado em MBTI. Responda APENAS com JSON válido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )

        content = response.choices[0].message.content

        # Extrair JSON
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            analysis = json.loads(json_match.group())
        else:
            analysis = json.loads(content)

        return JSONResponse(analysis)

    except Exception as e:
        logger.error(f"Erro na análise MBTI: {e}")
        return JSONResponse({
            "error": str(e),
            "type_indicator": "XXXX",
            "confidence": 0,
            "summary": f"Erro ao processar análise: {str(e)}"
        }, status_code=500)
