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

@router.get("/user/{user_id}/agent-data", response_class=HTMLResponse)
async def user_agent_data_page(request: Request, user_id: str, username: str = Depends(verify_credentials)):
    """
    Página de Dados do Agente

    Mostra:
    - Relatório resumido (total conversas, reativas, proativas, status)
    - 10 últimas mensagens reativas (conversação normal)
    - 10 últimas mensagens proativas (sistema proativo)
    """
    db = get_db()

    # Buscar usuário
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    cursor = db.conn.cursor()
    # Configurar row_factory para acessar colunas por nome
    cursor.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    # ============================================================
    # 1. RELATÓRIO RESUMIDO
    # ============================================================

    # Total de conversas
    cursor.execute("SELECT COUNT(*) as count FROM conversations WHERE user_id = ?", (user_id,))
    total_conversations = cursor.fetchone()['count']

    # Conversas reativas (todas exceto plataforma 'proactive')
    cursor.execute("""
        SELECT COUNT(*) as count FROM conversations
        WHERE user_id = ? AND platform != 'proactive'
    """, (user_id,))
    reactive_count = cursor.fetchone()['count']

    # Mensagens proativas (tabela proactive_approaches)
    cursor.execute("""
        SELECT COUNT(*) as count FROM proactive_approaches
        WHERE user_id = ?
    """, (user_id,))
    proactive_count = cursor.fetchone()['count']

    # Primeira interação
    cursor.execute("""
        SELECT MIN(timestamp) as first_ts FROM conversations WHERE user_id = ?
    """, (user_id,))
    first_interaction = cursor.fetchone()['first_ts'] or "N/A"

    # Última atividade
    cursor.execute("""
        SELECT MAX(timestamp) as last_ts FROM conversations WHERE user_id = ?
    """, (user_id,))
    last_activity = cursor.fetchone()['last_ts'] or "N/A"

    # Status proativo (última proativa + timestamp)
    cursor.execute("""
        SELECT timestamp FROM proactive_approaches
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (user_id,))
    last_proactive = cursor.fetchone()

    if last_proactive:
        from datetime import datetime, timedelta
        now = datetime.now()
        last_timestamp = datetime.fromisoformat(last_proactive.get('timestamp'))
        hours_since = (now - last_timestamp).total_seconds() / 3600

        # Cooldown de 12h (mesmo do sistema proativo)
        cooldown_hours = 12
        if hours_since < cooldown_hours:
            hours_left = cooldown_hours - hours_since
            proactive_status = f"⏸️  Cooldown ({hours_left:.1f}h restantes)"
        else:
            proactive_status = "✅ Ativo (pode receber mensagem)"
    else:
        proactive_status = "🆕 Nunca recebeu mensagem proativa"

    # Taxa de resposta (aproximada - conversas reativas / total)
    response_rate = int((reactive_count / total_conversations * 100)) if total_conversations > 0 else 0

    summary = {
        "total_conversations": total_conversations,
        "reactive_count": reactive_count,
        "proactive_count": proactive_count,
        "first_interaction": first_interaction[:16] if first_interaction != "N/A" else "N/A",
        "last_activity": last_activity[:16] if last_activity != "N/A" else "N/A",
        "proactive_status": proactive_status,
        "response_rate": response_rate
    }

    # ============================================================
    # 2. MENSAGENS REATIVAS (últimas 10)
    # ============================================================
    cursor.execute("""
        SELECT
            user_input,
            ai_response,
            timestamp,
            keywords
        FROM conversations
        WHERE user_id = ? AND platform != 'proactive'
        ORDER BY timestamp DESC
        LIMIT 10
    """, (user_id,))

    reactive_messages = []
    for row in cursor.fetchall():
        reactive_messages.append({
            "user_input": row.get('user_input', '') or "",
            "bot_response": row.get('ai_response', '') or "",
            "timestamp": row.get('timestamp', '')[:16] if row.get('timestamp') else "N/A",
            "keywords": row.get('keywords', '').split(',') if row.get('keywords') else []
        })

    # ============================================================
    # 3. MENSAGENS PROATIVAS (últimas 10)
    # ============================================================
    # Por enquanto, apenas mensagens de insights (sem JOIN com strategic_questions que pode não existir)
    cursor.execute("""
        SELECT
            autonomous_insight,
            timestamp,
            archetype_primary,
            archetype_secondary,
            topic_extracted,
            knowledge_domain
        FROM proactive_approaches
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    """, (user_id,))

    proactive_messages = []
    for row in cursor.fetchall():
        # Montar o par arquetípico
        archetype_pair = f"{row.get('archetype_primary', '')} + {row.get('archetype_secondary', '')}" if row.get('archetype_primary') else None

        # Por enquanto, todas são insights (perguntas estratégicas serão implementadas depois)
        message_type = 'insight'

        proactive_messages.append({
            "message": row.get('autonomous_insight', '') or "",
            "timestamp": row.get('timestamp', '')[:16] if row.get('timestamp') else "N/A",
            "message_type": message_type,
            "archetype_pair": archetype_pair,
            "topic": row.get('topic_extracted'),
            "target_dimension": None  # Será preenchido quando strategic_questions existir
        })

    return templates.TemplateResponse("user_agent_data.html", {
        "request": request,
        "user": user,
        "user_id": user_id,
        "summary": summary,
        "reactive_messages": reactive_messages,
        "proactive_messages": proactive_messages
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

    # Análise de Qualidade
    quality_analysis = None
    try:
        from quality_detector import QualityDetector

        detector = QualityDetector(db)
        conversations = db.get_user_conversations(user_id, limit=100)

        quality_analysis = detector.analyze_quality(
            user_id=user_id,
            psychometrics=psychometrics_data,
            conversations=conversations
        )

        # Salvar análise de qualidade no banco
        version = psychometrics_data.get('version', 1)
        detector.save_quality_analysis(user_id, version, quality_analysis)

        logger.info(f"✓ Análise de qualidade: {quality_analysis['overall_quality']} ({quality_analysis['quality_score']}%)")

    except Exception as e:
        logger.warning(f"⚠ Erro ao gerar análise de qualidade: {e}")
        # Não falha se análise de qualidade der erro
        pass

    # Renderizar template
    return templates.TemplateResponse("user_psychometrics.html", {
        "request": request,
        "user": user,
        "user_id": user_id,
        "psychometrics": psychometrics_data,
        "schwartz_values": schwartz_values,
        "eq_details": eq_details,
        "total_conversations": total_conversations,
        "quality_analysis": quality_analysis
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

# ============================================================================
# 🔍 SISTEMA DE EVIDÊNCIAS (Evidence System 2.0)
# ============================================================================

@router.get("/user/{user_id}/psychometrics/{dimension}/evidence")
async def get_dimension_evidence(
    user_id: str,
    dimension: str,
    username: str = Depends(verify_credentials)
):
    """
    Retorna evidências (citações literais) que embasam um score específico

    Dimensões válidas:
    - openness
    - conscientiousness
    - extraversion
    - agreeableness
    - neuroticism
    """
    try:
        from evidence_extractor import EvidenceExtractor
        from llm_providers import create_llm_provider
        import json as json_lib

        db = get_db()

        # Validar dimensão
        valid_dimensions = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        if dimension not in valid_dimensions:
            raise HTTPException(
                status_code=400,
                detail=f"Dimensão inválida. Use: {', '.join(valid_dimensions)}"
            )

        # Buscar análise psicométrica do usuário
        psychometrics = db.get_psychometrics(user_id)
        if not psychometrics:
            raise HTTPException(
                status_code=404,
                detail="Análise psicométrica não encontrada para este usuário"
            )

        # Criar extrator de evidências
        claude_provider = create_llm_provider("claude")
        extractor = EvidenceExtractor(db, claude_provider)

        # Verificar se evidências já existem
        existing_evidence = extractor.get_evidence_for_dimension(
            user_id=user_id,
            dimension=dimension,
            psychometric_version=psychometrics.get('version')
        )

        # Se evidências não existem, extrair on-demand
        if not existing_evidence:
            logger.info(f"🔍 Evidências não encontradas para {user_id}/{dimension}. Extraindo...")

            # Buscar conversas
            conversations = db.get_user_conversations(user_id, limit=50)

            if len(conversations) < 10:
                return JSONResponse({
                    "dimension": dimension,
                    "score": psychometrics.get(f'{dimension}_score', 0),
                    "level": psychometrics.get(f'{dimension}_level', 'N/A'),
                    "evidence_available": False,
                    "message": f"Dados insuficientes ({len(conversations)} conversas, mínimo 10)"
                })

            # Extrair evidências para esta dimensão
            big_five_scores = {
                dimension: {
                    'score': psychometrics.get(f'{dimension}_score', 50),
                    'level': psychometrics.get(f'{dimension}_level', 'Médio')
                }
            }

            evidence_list = extractor._extract_dimension_evidence(
                dimension=dimension,
                conversations=conversations,
                expected_score=big_five_scores[dimension]['score']
            )

            # Salvar evidências
            if evidence_list:
                all_evidence = {dimension: evidence_list}
                extractor.save_evidence_to_db(
                    user_id=user_id,
                    psychometric_version=psychometrics.get('version', 1),
                    all_evidence=all_evidence
                )

                existing_evidence = extractor.get_evidence_for_dimension(
                    user_id=user_id,
                    dimension=dimension,
                    psychometric_version=psychometrics.get('version')
                )

        # Formatar resposta
        return JSONResponse({
            "dimension": dimension,
            "score": psychometrics.get(f'{dimension}_score', 0),
            "level": psychometrics.get(f'{dimension}_level', 'N/A'),
            "description": psychometrics.get(f'{dimension}_description', ''),
            "evidence_available": len(existing_evidence) > 0,
            "num_evidence": len(existing_evidence),
            "evidence": existing_evidence[:10],  # Top 10 evidências
            "total_evidence": len(existing_evidence),
            "extraction_cached": len(existing_evidence) > 0
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar evidências: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/user/{user_id}/psychometrics/extract-evidence")
async def extract_all_evidence(
    user_id: str,
    username: str = Depends(verify_credentials)
):
    """
    Extrai evidências para todas as dimensões do Big Five
    (Processo pode demorar ~30-60s)
    """
    try:
        from evidence_extractor import EvidenceExtractor
        from llm_providers import create_llm_provider
        import json as json_lib

        db = get_db()

        # Buscar análise psicométrica
        psychometrics = db.get_psychometrics(user_id)
        if not psychometrics:
            raise HTTPException(
                status_code=404,
                detail="Análise psicométrica não encontrada"
            )

        # Buscar conversas
        conversations = db.get_user_conversations(user_id, limit=50)

        if len(conversations) < 10:
            return JSONResponse({
                "success": False,
                "message": f"Dados insuficientes ({len(conversations)} conversas, mínimo 10)"
            })

        # Criar extrator
        claude_provider = create_llm_provider("claude")
        extractor = EvidenceExtractor(db, claude_provider)

        # Preparar scores Big Five
        big_five_scores = {
            'openness': {
                'score': psychometrics.get('openness_score', 50),
                'level': psychometrics.get('openness_level', 'Médio')
            },
            'conscientiousness': {
                'score': psychometrics.get('conscientiousness_score', 50),
                'level': psychometrics.get('conscientiousness_level', 'Médio')
            },
            'extraversion': {
                'score': psychometrics.get('extraversion_score', 50),
                'level': psychometrics.get('extraversion_level', 'Médio')
            },
            'agreeableness': {
                'score': psychometrics.get('agreeableness_score', 50),
                'level': psychometrics.get('agreeableness_level', 'Médio')
            },
            'neuroticism': {
                'score': psychometrics.get('neuroticism_score', 50),
                'level': psychometrics.get('neuroticism_level', 'Médio')
            }
        }

        # Extrair evidências
        logger.info(f"🔍 Extraindo evidências para {user_id}...")
        all_evidence = extractor.extract_evidence_for_user(
            user_id=user_id,
            psychometric_version=psychometrics.get('version', 1),
            conversations=conversations,
            big_five_scores=big_five_scores
        )

        # Salvar no banco
        total_saved = extractor.save_evidence_to_db(
            user_id=user_id,
            psychometric_version=psychometrics.get('version', 1),
            all_evidence=all_evidence
        )

        # Contar evidências por dimensão
        evidence_counts = {
            dimension: len(evidence_list)
            for dimension, evidence_list in all_evidence.items()
        }

        return JSONResponse({
            "success": True,
            "total_evidence_extracted": total_saved,
            "evidence_by_dimension": evidence_counts,
            "message": f"Evidências extraídas com sucesso para {len(all_evidence)} dimensões"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao extrair evidências: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)


# ============================================================
# JUNG LAB - SISTEMA DE RUMINAÇÃO (Admin Dashboard)
# ============================================================

@router.get("/jung-lab", response_class=HTMLResponse)
async def jung_lab_dashboard(
    request: Request,
    username: str = Depends(verify_credentials)
):
    """Dashboard do Sistema de Ruminação Cognitiva (Admin only)"""
    from rumination_config import ADMIN_USER_ID
    from jung_rumination import RuminationEngine
    import os

    db = get_db()
    rumination = RuminationEngine(db)

    # Buscar estatísticas gerais
    stats = rumination.get_stats(ADMIN_USER_ID)

    # Buscar últimos fragmentos
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT id, fragment_type, content, source_quote, emotional_weight,
               datetime(created_at, 'localtime') as created_at
        FROM rumination_fragments
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 10
    """, (ADMIN_USER_ID,))
    fragments = [dict(row) for row in cursor.fetchall()]

    # Buscar tensões ativas
    cursor.execute("""
        SELECT id, tension_type, pole_a_content, pole_b_content,
               tension_description, intensity, maturity_score, status,
               datetime(first_detected_at, 'localtime') as created_at,
               datetime(last_revisited_at, 'localtime') as last_revisit
        FROM rumination_tensions
        WHERE user_id = ? AND status != 'archived'
        ORDER BY maturity_score DESC, first_detected_at DESC
        LIMIT 10
    """, (ADMIN_USER_ID,))
    tensions = [dict(row) for row in cursor.fetchall()]

    # Buscar insights (ready e delivered)
    cursor.execute("""
        SELECT id, symbol_content, question_content, full_message, depth_score, status,
               datetime(crystallized_at, 'localtime') as created_at,
               datetime(delivered_at, 'localtime') as delivered_at
        FROM rumination_insights
        WHERE user_id = ?
        ORDER BY crystallized_at DESC
        LIMIT 10
    """, (ADMIN_USER_ID,))
    insights = [dict(row) for row in cursor.fetchall()]

    # Verificar se scheduler está rodando
    scheduler_running = os.path.exists("rumination_scheduler.pid")
    scheduler_pid = None
    if scheduler_running:
        try:
            with open("rumination_scheduler.pid", "r") as f:
                scheduler_pid = int(f.read().strip())
        except:
            scheduler_running = False

    return templates.TemplateResponse(
        "jung_lab.html",
        {
            "request": request,
            "username": username,
            "stats": stats,
            "fragments": fragments,
            "tensions": tensions,
            "insights": insights,
            "scheduler_running": scheduler_running,
            "scheduler_pid": scheduler_pid
        }
    )


@router.post("/api/jung-lab/digest")
async def run_manual_digest(
    username: str = Depends(verify_credentials)
):
    """Executa digestão manual do sistema de ruminação"""
    from rumination_config import ADMIN_USER_ID
    from jung_rumination import RuminationEngine

    try:
        db = get_db()
        rumination = RuminationEngine(db)

        # Executar digestão
        digest_stats = rumination.digest(ADMIN_USER_ID)

        # Verificar se há insights para entregar
        delivered_id = rumination.check_and_deliver(ADMIN_USER_ID)

        # Obter estatísticas atualizadas
        stats = rumination.get_stats(ADMIN_USER_ID)

        return JSONResponse({
            "success": True,
            "digest_stats": digest_stats,
            "delivered_insight_id": delivered_id,
            "current_stats": stats,
            "message": "Digestão executada com sucesso"
        })

    except Exception as e:
        logger.error(f"❌ Erro na digestão manual: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/api/jung-lab/scheduler/{action}")
async def control_scheduler(
    action: str,
    username: str = Depends(verify_credentials)
):
    """Controla o scheduler de ruminação (start/stop)"""
    import subprocess
    import os
    import signal
    import sys

    pid_file = "rumination_scheduler.pid"

    try:
        if action == "start":
            # Verificar se já está rodando
            if os.path.exists(pid_file):
                return JSONResponse({
                    "success": False,
                    "message": "Scheduler já está rodando"
                }, status_code=400)

            # Iniciar processo em background
            python_exe = sys.executable
            process = subprocess.Popen(
                [python_exe, "rumination_scheduler.py"],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Salvar PID
            with open(pid_file, "w") as f:
                f.write(str(process.pid))

            return JSONResponse({
                "success": True,
                "pid": process.pid,
                "message": "Scheduler iniciado com sucesso"
            })

        elif action == "stop":
            # Verificar se está rodando
            if not os.path.exists(pid_file):
                return JSONResponse({
                    "success": False,
                    "message": "Scheduler não está rodando"
                }, status_code=400)

            # Ler PID e matar processo
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())

            try:
                os.kill(pid, signal.SIGTERM)
                os.remove(pid_file)

                return JSONResponse({
                    "success": True,
                    "message": "Scheduler parado com sucesso"
                })
            except ProcessLookupError:
                # Processo já morreu, apenas remove PID file
                os.remove(pid_file)
                return JSONResponse({
                    "success": True,
                    "message": "Scheduler não estava rodando (PID file removido)"
                })

        else:
            return JSONResponse({
                "success": False,
                "message": f"Ação inválida: {action}"
            }, status_code=400)

    except Exception as e:
        logger.error(f"❌ Erro ao controlar scheduler: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/api/jung-lab/diagnose")
async def diagnose_rumination(
    username: str = Depends(verify_credentials)
):
    """
    Diagnóstico completo do sistema de ruminação
    Verifica conversas, fragmentos, tensões e possíveis problemas
    """
    from rumination_config import ADMIN_USER_ID
    from jung_rumination import RuminationEngine

    try:
        db = get_db()
        cursor = db.conn.cursor()

        diagnosis = {
            "admin_user_id": ADMIN_USER_ID,
            "conversations": {},
            "rumination_tables": {},
            "problems": [],
            "recommendations": []
        }

        # 1. VERIFICAR CONVERSAS
        cursor.execute('SELECT COUNT(*) FROM conversations')
        total_conversations = cursor.fetchone()[0]
        diagnosis["conversations"]["total"] = total_conversations

        cursor.execute('SELECT COUNT(*) FROM conversations WHERE user_id = ?', (ADMIN_USER_ID,))
        admin_conversations = cursor.fetchone()[0]
        diagnosis["conversations"]["admin_total"] = admin_conversations

        if admin_conversations > 0:
            # Conversas por plataforma
            cursor.execute('''
                SELECT platform, COUNT(*) as count
                FROM conversations
                WHERE user_id = ?
                GROUP BY platform
            ''', (ADMIN_USER_ID,))
            diagnosis["conversations"]["by_platform"] = {
                row[0] or "NULL": row[1] for row in cursor.fetchall()
            }

            # Última conversa
            cursor.execute('''
                SELECT timestamp, platform, user_input
                FROM conversations
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (ADMIN_USER_ID,))
            last = cursor.fetchone()
            if last:
                diagnosis["conversations"]["last"] = {
                    "timestamp": last[0],
                    "platform": last[1],
                    "preview": last[2][:100] if last[2] else None
                }

            # Últimas 5 conversas com plataforma (para debug)
            cursor.execute('''
                SELECT timestamp, platform, user_input
                FROM conversations
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 5
            ''', (ADMIN_USER_ID,))
            diagnosis["conversations"]["recent_samples"] = [
                {
                    "timestamp": row[0],
                    "platform": row[1],
                    "preview": row[2][:60] if row[2] else None
                }
                for row in cursor.fetchall()
            ]
        else:
            diagnosis["problems"].append({
                "severity": "CRITICAL",
                "issue": "Não há conversas do admin no banco de dados",
                "details": f"User ID configurado: {ADMIN_USER_ID}"
            })
            diagnosis["recommendations"].append({
                "action": "Verificar se o bot está rodando e recebendo mensagens",
                "steps": [
                    "1. Enviar mensagem de teste no Telegram",
                    "2. Verificar logs do Railway para erros",
                    f"3. Confirmar que seu Telegram ID é: {ADMIN_USER_ID}",
                    "4. Verificar se o bot está salvando conversas corretamente"
                ]
            })

        # 2. VERIFICAR TABELAS DE RUMINAÇÃO
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%rumination%'")
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            diagnosis["problems"].append({
                "severity": "HIGH",
                "issue": "Tabelas de ruminação não existem",
                "details": "As tabelas deveriam ser criadas automaticamente"
            })
            diagnosis["recommendations"].append({
                "action": "Reiniciar o serviço web para criar as tabelas",
                "steps": [
                    "1. Fazer deploy no Railway",
                    "2. Aguardar inicialização completa",
                    "3. Acessar /admin/jung-lab novamente"
                ]
            })
        else:
            diagnosis["rumination_tables"]["found"] = tables

            for table in tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE user_id = ?', (ADMIN_USER_ID,))
                count = cursor.fetchone()[0]
                diagnosis["rumination_tables"][table] = {
                    "count": count
                }

                if count > 0:
                    # Get sample
                    cursor.execute(f'SELECT * FROM {table} WHERE user_id = ? LIMIT 1', (ADMIN_USER_ID,))
                    diagnosis["rumination_tables"][table]["has_data"] = True

            # Verificar problemas específicos
            frag_count = diagnosis["rumination_tables"].get("rumination_fragments", {}).get("count", 0)
            tension_count = diagnosis["rumination_tables"].get("rumination_tensions", {}).get("count", 0)

            if admin_conversations > 0 and frag_count == 0:
                # Verificar se tem conversas telegram
                cursor.execute('''
                    SELECT COUNT(*) FROM conversations
                    WHERE user_id = ? AND platform = 'telegram'
                ''', (ADMIN_USER_ID,))
                telegram_count = cursor.fetchone()[0]

                if telegram_count == 0:
                    diagnosis["problems"].append({
                        "severity": "HIGH",
                        "issue": "Há conversas mas NENHUMA tem platform='telegram'",
                        "details": f"Hook de ruminação só processa platform='telegram'. Conversas: {admin_conversations}, Telegram: {telegram_count}"
                    })
                    diagnosis["recommendations"].append({
                        "action": "FIX: Atualizar conversas antigas para platform='telegram'",
                        "steps": [
                            "1. Executar SQL: UPDATE conversations SET platform='telegram' WHERE user_id='367f9e509e396d51' AND (platform IS NULL OR platform != 'telegram')",
                            "2. Enviar nova mensagem no Telegram",
                            "3. Verificar se agora cria fragmentos"
                        ]
                    })
                else:
                    diagnosis["problems"].append({
                        "severity": "HIGH",
                        "issue": "Há conversas mas não há fragmentos",
                        "details": f"O hook de ruminação pode não estar sendo chamado ou a LLM não está extraindo fragmentos. Telegram: {telegram_count}/{admin_conversations}"
                    })
                    diagnosis["recommendations"].append({
                        "action": "Verificar logs do bot para erros no hook de ruminação",
                        "steps": [
                            "1. Verificar logs Railway para warnings: '⚠️ Erro no hook de ruminação'",
                            "2. Verificar se há mensagem '🧠 Ruminação: Ingestão executada' nos logs",
                            "3. Testar enviar nova mensagem e verificar se cria fragmentos"
                        ]
                    })

            if frag_count > 0 and tension_count == 0:
                diagnosis["problems"].append({
                    "severity": "MEDIUM",
                    "issue": "Há fragmentos mas não há tensões",
                    "details": f"Com {frag_count} fragmentos, deveria haver pelo menos algumas tensões detectadas"
                })
                diagnosis["recommendations"].append({
                    "action": "Verificar detecção de tensões",
                    "steps": [
                        "1. Enviar mais mensagens com temas contraditórios",
                        "2. Verificar logs da LLM durante detecção",
                        f"3. Considerar que pode precisar de mais fragmentos (atual: {frag_count})"
                    ]
                })

        # 3. STATUS GERAL
        if len(diagnosis["problems"]) == 0:
            if admin_conversations > 0:
                diagnosis["status"] = "OK"
                diagnosis["message"] = "Sistema funcionando corretamente"
            else:
                diagnosis["status"] = "NO_DATA"
                diagnosis["message"] = "Sistema pronto mas sem dados para processar"
        else:
            diagnosis["status"] = "ERROR"
            diagnosis["message"] = f"Encontrados {len(diagnosis['problems'])} problemas"

        return JSONResponse(diagnosis)

    except Exception as e:
        logger.error(f"❌ Erro no diagnóstico: {e}", exc_info=True)
        return JSONResponse({
            "status": "ERROR",
            "error": str(e),
            "problems": [{
                "severity": "CRITICAL",
                "issue": "Erro ao executar diagnóstico",
                "details": str(e)
            }]
        }, status_code=500)


@router.post("/api/jung-lab/fix-platform")
async def fix_platform_issue(
    username: str = Depends(verify_credentials)
):
    """
    FIX automático: Atualiza conversas antigas para platform='telegram'
    Resolve o problema de conversas sem platform definido
    """
    from rumination_config import ADMIN_USER_ID

    try:
        db = get_db()
        cursor = db.conn.cursor()

        # Verificar quantas conversas serão atualizadas
        cursor.execute('''
            SELECT COUNT(*) FROM conversations
            WHERE user_id = ?
            AND (platform IS NULL OR platform NOT IN ('telegram', 'proactive', 'proactive_rumination'))
        ''', (ADMIN_USER_ID,))
        count_to_update = cursor.fetchone()[0]

        if count_to_update == 0:
            return JSONResponse({
                "success": True,
                "updated": 0,
                "message": "Nenhuma conversa precisa ser atualizada"
            })

        # Atualizar conversas
        cursor.execute('''
            UPDATE conversations
            SET platform = 'telegram'
            WHERE user_id = ?
            AND (platform IS NULL OR platform NOT IN ('telegram', 'proactive', 'proactive_rumination'))
        ''', (ADMIN_USER_ID,))
        db.conn.commit()

        logger.info(f"✅ Platform fix: {count_to_update} conversas atualizadas para platform='telegram'")

        return JSONResponse({
            "success": True,
            "updated": count_to_update,
            "message": f"✅ {count_to_update} conversas atualizadas. Agora envie uma nova mensagem no Telegram para testar."
        })

    except Exception as e:
        logger.error(f"❌ Erro no fix de platform: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.get("/api/jung-lab/debug-full")
async def debug_rumination_full(
    username: str = Depends(verify_credentials)
):
    """
    Debug completo do sistema de ruminação
    Executa todos os testes para identificar problemas
    """
    from rumination_config import ADMIN_USER_ID, MIN_TENSION_LEVEL
    import inspect

    try:
        db = get_db()
        cursor = db.conn.cursor()

        debug_result = {
            "config": {},
            "tables": {},
            "conversations": {},
            "telegram_conversations": {},
            "fragments": {},
            "hook_code": {},
            "imports": {},
            "problems": [],
            "recommendations": []
        }

        # TESTE 1: Configuração
        debug_result["config"] = {
            "admin_user_id": ADMIN_USER_ID,
            "min_tension_level": MIN_TENSION_LEVEL
        }

        # TESTE 2: Tabelas
        tables = ['rumination_fragments', 'rumination_tensions', 'rumination_insights', 'rumination_log']

        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            exists = cursor.fetchone()

            if exists:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]

                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]

                debug_result["tables"][table] = {
                    "exists": True,
                    "count": count,
                    "columns": columns
                }
            else:
                debug_result["tables"][table] = {"exists": False}
                debug_result["problems"].append(f"Tabela {table} não existe")

        # TESTE 3: Conversas do admin
        cursor.execute('SELECT COUNT(*) FROM conversations WHERE user_id = ?', (ADMIN_USER_ID,))
        total_convs = cursor.fetchone()[0]

        debug_result["conversations"]["total"] = total_convs

        if total_convs > 0:
            cursor.execute('''
                SELECT platform, COUNT(*) as count
                FROM conversations
                WHERE user_id = ?
                GROUP BY platform
            ''', (ADMIN_USER_ID,))

            by_platform = {(row[0] or 'NULL'): row[1] for row in cursor.fetchall()}
            debug_result["conversations"]["by_platform"] = by_platform

            # Últimas 3
            cursor.execute('''
                SELECT id, timestamp, platform, user_input
                FROM conversations
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 3
            ''', (ADMIN_USER_ID,))

            debug_result["conversations"]["recent"] = [
                {
                    "id": row[0],
                    "timestamp": row[1],
                    "platform": row[2] or 'NULL',
                    "preview": row[3][:80] if row[3] else None
                }
                for row in cursor.fetchall()
            ]

        # TESTE 4: Conversas telegram
        cursor.execute('''
            SELECT COUNT(*) FROM conversations
            WHERE user_id = ? AND platform = 'telegram'
        ''', (ADMIN_USER_ID,))
        telegram_count = cursor.fetchone()[0]

        debug_result["telegram_conversations"]["count"] = telegram_count

        if telegram_count > 0:
            cursor.execute('''
                SELECT id, timestamp, user_input
                FROM conversations
                WHERE user_id = ? AND platform = 'telegram'
                ORDER BY timestamp DESC
                LIMIT 3
            ''', (ADMIN_USER_ID,))

            debug_result["telegram_conversations"]["recent"] = [
                {
                    "id": row[0],
                    "timestamp": row[1],
                    "preview": row[2][:80] if row[2] else None
                }
                for row in cursor.fetchall()
            ]

        # TESTE 5: Fragmentos
        cursor.execute('SELECT COUNT(*) FROM rumination_fragments WHERE user_id = ?', (ADMIN_USER_ID,))
        frag_count = cursor.fetchone()[0]

        debug_result["fragments"]["count"] = frag_count

        if frag_count > 0:
            cursor.execute('''
                SELECT id, fragment_type, content, emotional_weight, created_at
                FROM rumination_fragments
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 3
            ''', (ADMIN_USER_ID,))

            debug_result["fragments"]["recent"] = [
                {
                    "id": row[0],
                    "type": row[1],
                    "content": row[2][:80],
                    "weight": row[3],
                    "created_at": row[4]
                }
                for row in cursor.fetchall()
            ]

        # TESTE 6: Hook de ruminação
        try:
            import jung_core

            source = inspect.getsource(jung_core.HybridDatabaseManager.save_conversation)

            has_hook = "Hook ruminação" in source or "Sistema de Ruminação" in source or "HOOK: Sistema de Ruminação" in source

            debug_result["hook_code"]["present"] = has_hook
            debug_result["hook_code"]["lines_count"] = len([l for l in source.split('\n') if 'ruminação' in l.lower() or 'rumination' in l.lower()])

            if not has_hook:
                debug_result["problems"].append("Código do hook NÃO encontrado em save_conversation")

        except Exception as e:
            debug_result["hook_code"]["error"] = str(e)
            debug_result["problems"].append(f"Erro ao verificar hook: {e}")

        # TESTE 7: Imports
        try:
            from rumination_config import ADMIN_USER_ID as test_id
            debug_result["imports"]["rumination_config"] = "OK"
        except Exception as e:
            debug_result["imports"]["rumination_config"] = f"ERRO: {e}"
            debug_result["problems"].append(f"Erro ao importar rumination_config: {e}")

        try:
            from jung_rumination import RuminationEngine
            rumination = RuminationEngine(db)
            debug_result["imports"]["jung_rumination"] = "OK"
            debug_result["imports"]["engine_admin_id"] = rumination.admin_user_id
        except Exception as e:
            debug_result["imports"]["jung_rumination"] = f"ERRO: {e}"
            debug_result["problems"].append(f"Erro ao importar/inicializar RuminationEngine: {e}")

        # ANÁLISE DE PROBLEMAS
        if telegram_count == 0 and total_convs > 0:
            debug_result["problems"].append("CRÍTICO: Há conversas mas nenhuma tem platform='telegram'")
            debug_result["recommendations"].append("Executar fix platform: POST /admin/api/jung-lab/fix-platform")

        if telegram_count > 0 and frag_count == 0:
            debug_result["problems"].append("CRÍTICO: Há conversas telegram mas nenhum fragmento foi criado")
            debug_result["recommendations"].append("Hook não está sendo executado ou LLM não está extraindo fragmentos")
            debug_result["recommendations"].append("Verificar logs do Railway para mensagens: '🔍 Hook ruminação', '🔍 INGEST chamado'")

        if total_convs == 0:
            debug_result["problems"].append("Nenhuma conversa do admin no banco")
            debug_result["recommendations"].append("Enviar mensagem no Telegram e verificar se é salva")

        # Status geral
        if len(debug_result["problems"]) == 0:
            debug_result["status"] = "OK"
            debug_result["message"] = "Sistema aparentemente funcional"
        else:
            debug_result["status"] = "ERROR"
            debug_result["message"] = f"{len(debug_result['problems'])} problema(s) encontrado(s)"

        return JSONResponse(debug_result)

    except Exception as e:
        logger.error(f"❌ Erro no debug completo: {e}", exc_info=True)
        return JSONResponse({
            "status": "ERROR",
            "error": str(e),
            "problems": [f"Erro fatal ao executar debug: {e}"]
        }, status_code=500)
