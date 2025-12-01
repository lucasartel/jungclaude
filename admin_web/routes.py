from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import os
from typing import Dict, List, Optional
import logging
from datetime import datetime

# Importar autenticação segura
from admin_web.auth import verify_credentials

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
# A autenticação agora é gerenciada por admin_web/auth.py
# A função verify_credentials foi importada acima e usa bcrypt para senhas hashadas

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
            model="grok-4-fast-reasoning",
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

@router.get("/user/{user_id}/psychometrics", response_class=HTMLResponse)
async def user_psychometrics_page(request: Request, user_id: str, username: str = Depends(verify_credentials)):
    """Página de análises psicométricas completas (Big Five, EQ, VARK, Schwartz)"""
    db = get_db()

    # Buscar usuário
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Verificar se análise já existe (cache)
    psychometrics_data = db.get_psychometrics(user_id)

    # Se não existe ou está desatualizada, gerar nova
    if not psychometrics_data:
        logger.info(f"🧪 Gerando análises psicométricas para {user_id}...")

        try:
            # Gerar todas as 4 análises
            big_five = db.analyze_big_five(user_id, min_conversations=20)
            eq = db.analyze_emotional_intelligence(user_id)
            vark = db.analyze_learning_style(user_id, min_conversations=20)
            values = db.analyze_personal_values(user_id, min_conversations=20)

            # Verificar se houve erros
            errors = []
            if "error" in big_five:
                errors.append(f"Big Five: {big_five['error']}")
            if "error" in eq:
                errors.append(f"EQ: {eq['error']}")
            if "error" in vark:
                errors.append(f"VARK: {vark['error']}")
            if "error" in values:
                errors.append(f"Values: {values['error']}")

            if errors:
                # Renderizar página com erro
                return templates.TemplateResponse("user_psychometrics.html", {
                    "request": request,
                    "user": user,
                    "user_id": user_id,
                    "error": " | ".join(errors),
                    "conversations_count": db.count_conversations(user_id)
                })

            # Salvar no banco
            db.save_psychometrics(user_id, big_five, eq, vark, values)

            # Buscar dados salvos
            psychometrics_data = db.get_psychometrics(user_id)

        except Exception as e:
            logger.error(f"❌ Erro ao gerar psicometria: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Erro ao gerar análise: {str(e)}")

    # Parse JSON fields
    import json as json_lib

    schwartz_values = {}
    if psychometrics_data.get('schwartz_values'):
        try:
            schwartz_values = json_lib.loads(psychometrics_data['schwartz_values'])
        except:
            schwartz_values = {}

    eq_details = {}
    if psychometrics_data.get('eq_details'):
        try:
            eq_details = json_lib.loads(psychometrics_data['eq_details'])
        except:
            eq_details = {}

    # Stats
    total_conversations = db.count_conversations(user_id)

    # Renderizar template
    return templates.TemplateResponse("user_psychometrics.html", {
        "request": request,
        "user": user,
        "user_id": user_id,
        "psychometrics": psychometrics_data,
        "schwartz_values": schwartz_values,
        "eq_details": eq_details,
        "total_conversations": total_conversations
    })

@router.post("/api/user/{user_id}/regenerate-psychometrics")
async def regenerate_psychometrics(user_id: str, username: str = Depends(verify_credentials)):
    """Força regeneração das análises psicométricas (cria nova versão)"""
    db = get_db()

    try:
        logger.info(f"🔄 Regenerando análises psicométricas para {user_id}...")

        # Gerar todas as 4 análises
        big_five = db.analyze_big_five(user_id, min_conversations=20)
        eq = db.analyze_emotional_intelligence(user_id)
        vark = db.analyze_learning_style(user_id, min_conversations=20)
        values = db.analyze_personal_values(user_id, min_conversations=20)

        # Verificar erros
        if "error" in big_five or "error" in eq or "error" in vark or "error" in values:
            error_msg = big_five.get("error") or eq.get("error") or vark.get("error") or values.get("error")
            return JSONResponse({"error": error_msg}, status_code=400)

        # Salvar (vai criar nova versão)
        db.save_psychometrics(user_id, big_five, eq, vark, values)

        return JSONResponse({"success": True, "message": "Análises regeneradas com sucesso!"})

    except Exception as e:
        logger.error(f"❌ Erro ao regenerar psicometria: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/user/{user_id}/psychometrics/download-pdf")
async def download_psychometrics_pdf(user_id: str, username: str = Depends(verify_credentials)):
    """
    Download de relatório psicométrico em PDF

    Gera PDF profissional com todas as 4 análises:
    - Big Five (OCEAN)
    - Inteligência Emocional (EQ)
    - VARK (Estilos de Aprendizagem)
    - Valores de Schwartz
    """
    from fastapi.responses import StreamingResponse
    from pdf_generator import generate_psychometric_pdf
    import json as json_lib

    db = get_db()

    try:
        # Buscar usuário
        user = db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # Buscar análises psicométricas
        psychometrics_data = db.get_psychometrics(user_id)

        if not psychometrics_data:
            raise HTTPException(
                status_code=404,
                detail="Análises psicométricas não encontradas. Gere as análises primeiro."
            )

        # Extrair dados de cada análise
        big_five = json_lib.loads(psychometrics_data.get('big_five_data', '{}'))
        eq_data = {
            'eq_score': psychometrics_data.get('eq_score'),
            'eq_level': psychometrics_data.get('eq_level'),
            'eq_details': json_lib.loads(psychometrics_data.get('eq_details', '{}'))
        }
        vark_data = json_lib.loads(psychometrics_data.get('vark_data', '{}'))
        schwartz_data = json_lib.loads(psychometrics_data.get('schwartz_values', '{}'))

        # Contar conversas
        total_conversations = db.count_conversations(user_id)

        # Gerar PDF
        pdf_buffer = generate_psychometric_pdf(
            user_name=user['user_name'],
            total_conversations=total_conversations,
            big_five=big_five,
            eq=eq_data,
            vark=vark_data,
            values=schwartz_data
        )

        # Preparar resposta
        filename = f"relatorio_psicometrico_{user['user_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"

        # Garantir que o buffer está no início
        pdf_buffer.seek(0)

        return StreamingResponse(
            iter([pdf_buffer.read()]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao gerar PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")

# ============================================================================
# 🔍 DIAGNÓSTICO DE VAZAMENTO DE MEMÓRIA
# ============================================================================

@router.get("/api/diagnose-facts")
async def diagnose_facts(username: str = Depends(verify_credentials)):
    """
    API para diagnosticar vazamento de memória entre usuários.
    Retorna todos os fatos de todos os usuários para análise.
    """
    try:
        db = get_db()
        cursor = db.conn.cursor()

        # 1. Listar todos os usuários
        cursor.execute("SELECT user_id, user_name, platform FROM users ORDER BY user_name")
        users = cursor.fetchall()

        users_list = []
        for user in users:
            users_list.append({
                "user_id": user['user_id'],
                "user_name": user['user_name'],
                "platform": user['platform']
            })

        # 2. Fatos por usuário
        facts_by_user = {}
        for user in users:
            user_id = user['user_id']

            cursor.execute("""
                SELECT fact_category, fact_key, fact_value, is_current, version,
                       source_conversation_id
                FROM user_facts
                WHERE user_id = ?
                ORDER BY fact_category, fact_key, version DESC
            """, (user_id,))

            facts = cursor.fetchall()

            facts_by_user[user_id] = {
                "user_name": user['user_name'],
                "facts": []
            }

            for fact in facts:
                facts_by_user[user_id]["facts"].append({
                    "category": fact['fact_category'],
                    "key": fact['fact_key'],
                    "value": fact['fact_value'],
                    "is_current": bool(fact['is_current']),
                    "version": fact['version'],
                    "source_conversation_id": fact['source_conversation_id']
                })

        # 3. Verificar integridade
        cursor.execute("""
            SELECT COUNT(*) as count FROM user_facts WHERE user_id IS NULL OR user_id = ''
        """)
        null_facts_count = cursor.fetchone()['count']

        # 4. Buscar duplicatas
        cursor.execute("""
            SELECT fact_category, fact_key, fact_value, COUNT(DISTINCT user_id) as user_count,
                   GROUP_CONCAT(DISTINCT user_id) as user_ids
            FROM user_facts
            WHERE is_current = 1
            GROUP BY fact_category, fact_key, fact_value
            HAVING user_count > 1
        """)

        duplicates = cursor.fetchall()
        duplicates_list = []
        for dup in duplicates:
            duplicates_list.append({
                "category": dup['fact_category'],
                "key": dup['fact_key'],
                "value": dup['fact_value'],
                "user_count": dup['user_count'],
                "user_ids": dup['user_ids'].split(',') if dup['user_ids'] else []
            })

        return JSONResponse({
            "success": True,
            "users": users_list,
            "facts_by_user": facts_by_user,
            "integrity": {
                "null_facts_count": null_facts_count,
                "has_null_facts": null_facts_count > 0
            },
            "duplicates": duplicates_list,
            "has_leaks": len(duplicates_list) > 0
        })

    except Exception as e:
        logger.error(f"❌ Erro ao diagnosticar fatos: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/api/diagnose-chromadb")
async def diagnose_chromadb(username: str = Depends(verify_credentials)):
    """
    API para diagnosticar vazamento de memória no ChromaDB.
    Retorna todas as conversas salvas no ChromaDB com seus metadados.
    """
    try:
        db = get_db()

        # Verificar se ChromaDB está habilitado
        if not db.chroma_enabled:
            return JSONResponse({
                "success": False,
                "error": "ChromaDB está desabilitado",
                "chroma_enabled": False
            })

        # Buscar TODOS os documentos do ChromaDB (sem filtro)
        # Isso vai revelar se há documentos com user_id errado
        try:
            # Get the collection directly
            collection = db.vectorstore._collection

            # Get all documents
            all_docs = collection.get(
                include=["metadatas", "documents"]
            )

            # Organizar por usuário
            docs_by_user = {}
            total_docs = len(all_docs['ids'])

            for i in range(total_docs):
                doc_id = all_docs['ids'][i]
                metadata = all_docs['metadatas'][i]
                document = all_docs['documents'][i]

                user_id = metadata.get('user_id', 'N/A')
                user_name = metadata.get('user_name', 'N/A')

                if user_id not in docs_by_user:
                    docs_by_user[user_id] = {
                        "user_name": user_name,
                        "document_count": 0,
                        "documents": []
                    }

                docs_by_user[user_id]["document_count"] += 1
                docs_by_user[user_id]["documents"].append({
                    "doc_id": doc_id,
                    "user_input": metadata.get('user_input', ''),
                    "ai_response": metadata.get('ai_response', ''),
                    "conversation_id": metadata.get('conversation_id', 'N/A'),
                    "timestamp": metadata.get('timestamp', 'N/A'),
                    "preview": document[:200] if document else ""
                })

            # Buscar usuários cadastrados
            cursor = db.conn.cursor()
            cursor.execute("SELECT user_id, user_name FROM users")
            registered_users = {row['user_id']: row['user_name'] for row in cursor.fetchall()}

            # Verificar integridade
            orphan_docs = []
            for user_id in docs_by_user.keys():
                if user_id not in registered_users and user_id != 'N/A':
                    orphan_docs.append({
                        "user_id": user_id,
                        "document_count": docs_by_user[user_id]["document_count"]
                    })

            return JSONResponse({
                "success": True,
                "chroma_enabled": True,
                "total_documents": total_docs,
                "registered_users": list(registered_users.keys()),
                "users_with_documents": list(docs_by_user.keys()),
                "docs_by_user": docs_by_user,
                "orphan_docs": orphan_docs,
                "has_orphans": len(orphan_docs) > 0
            })

        except Exception as e:
            logger.error(f"❌ Erro ao acessar ChromaDB: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return JSONResponse({"error": f"Erro ao acessar ChromaDB: {str(e)}"}, status_code=500)

    except Exception as e:
        logger.error(f"❌ Erro ao diagnosticar ChromaDB: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/api/conversation/{conversation_id}")
async def get_conversation_detail(conversation_id: int, username: str = Depends(verify_credentials)):
    """
    Retorna detalhes completos de uma conversa específica.
    """
    try:
        db = get_db()
        cursor = db.conn.cursor()

        cursor.execute("""
            SELECT c.id, c.user_id, c.user_input, c.ai_response, c.timestamp,
                   u.user_name, u.platform
            FROM conversations c
            LEFT JOIN users u ON c.user_id = u.user_id
            WHERE c.id = ?
        """, (conversation_id,))

        conv = cursor.fetchone()

        if not conv:
            return JSONResponse({"error": "Conversa não encontrada"}, status_code=404)

        return JSONResponse({
            "success": True,
            "conversation": {
                "id": conv['id'],
                "user_id": conv['user_id'],
                "user_name": conv['user_name'],
                "platform": conv['platform'],
                "timestamp": conv['timestamp'],
                "user_input": conv['user_input'],
                "ai_response": conv['ai_response']
            }
        })

    except Exception as e:
        logger.error(f"❌ Erro ao buscar conversa: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({"error": str(e)}, status_code=500)
