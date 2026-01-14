"""
Rotas de Identidade Nuclear do Agente - Restrito Master Admin

Dashboard e APIs para visualização da identidade evolutiva do agente Jung.

Autor: Sistema de Identidade Nuclear
Data: 2026-01-12
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict
import logging
import json
import time

from admin_web.auth.middleware import require_master

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/agent-identity", tags=["Agent Identity"])


@router.get("/stats")
async def get_agent_identity_stats(
    request: Request,
    admin: Dict = Depends(require_master)
):
    """
    Estatísticas gerais da identidade do agente

    Restrito ao master admin
    """
    try:
        from agent_identity_context_builder import AgentIdentityContextBuilder
        from jung_core import HybridDatabaseManager

        db = HybridDatabaseManager()
        builder = AgentIdentityContextBuilder(db)
        stats = builder.get_identity_stats()

        logger.info(f"📊 Stats de identidade acessadas por master admin: {admin['email']}")

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de identidade: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/context")
async def get_agent_identity_context(
    request: Request,
    admin: Dict = Depends(require_master)
):
    """
    Contexto completo de identidade do agente

    Restrito ao master admin
    """
    try:
        from agent_identity_context_builder import AgentIdentityContextBuilder
        from jung_core import HybridDatabaseManager

        db = HybridDatabaseManager()
        builder = AgentIdentityContextBuilder(db)
        context = builder.build_identity_context(
            user_id=None,
            include_nuclear=True,
            include_contradictions=True,
            include_narrative=True,
            include_possible_selves=True,
            include_relational=True,
            include_meta_knowledge=True,
            max_items_per_category=10
        )

        logger.info(f"🧠 Contexto completo acessado por master admin: {admin['email']}")

        return {
            "success": True,
            "context": context
        }

    except Exception as e:
        logger.error(f"Erro ao obter contexto de identidade: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/nuclear")
async def get_nuclear_beliefs(
    request: Request,
    admin: Dict = Depends(require_master)
):
    """
    Crenças nucleares do agente (top 10 por certeza)

    Restrito ao master admin
    """
    try:
        from jung_core import HybridDatabaseManager
        from identity_config import AGENT_INSTANCE

        db = HybridDatabaseManager()
        cursor = db.conn.cursor()

        cursor.execute("""
            SELECT
                id,
                attribute_type,
                content,
                certainty,
                stability_score,
                first_crystallized_at,
                last_reaffirmed_at,
                contradiction_count,
                emerged_in_relation_to,
                version
            FROM agent_identity_core
            WHERE agent_instance = ? AND is_current = 1
            ORDER BY certainty DESC, stability_score DESC
            LIMIT 10
        """, (AGENT_INSTANCE,))

        rows = cursor.fetchall()
        beliefs = []

        for row in rows:
            beliefs.append({
                "id": row[0],
                "type": row[1],
                "content": row[2],
                "certainty": row[3],
                "stability": row[4],
                "crystallized_at": row[5],
                "last_reaffirmed": row[6],
                "contradiction_count": row[7],
                "emerged_from": row[8],
                "version": row[9]
            })

        logger.info(f"💎 {len(beliefs)} crenças nucleares acessadas por: {admin['email']}")

        return {
            "success": True,
            "beliefs": beliefs,
            "count": len(beliefs)
        }

    except Exception as e:
        logger.error(f"Erro ao obter crenças nucleares: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/contradictions")
async def get_active_contradictions(
    request: Request,
    admin: Dict = Depends(require_master)
):
    """
    Contradições ativas do agente (top 10 por tensão)

    Restrito ao master admin
    """
    try:
        from jung_core import HybridDatabaseManager
        from identity_config import AGENT_INSTANCE

        db = HybridDatabaseManager()
        cursor = db.conn.cursor()

        cursor.execute("""
            SELECT
                id,
                pole_a,
                pole_b,
                contradiction_type,
                tension_level,
                salience,
                status,
                first_detected_at,
                last_activated_at,
                integration_attempts
            FROM agent_identity_contradictions
            WHERE agent_instance = ? AND status IN ('unresolved', 'integrating')
            ORDER BY tension_level DESC, salience DESC
            LIMIT 10
        """, (AGENT_INSTANCE,))

        rows = cursor.fetchall()
        contradictions = []

        for row in rows:
            contradictions.append({
                "id": row[0],
                "pole_a": row[1],
                "pole_b": row[2],
                "type": row[3],
                "tension": row[4],
                "salience": row[5],
                "status": row[6],
                "detected_at": row[7],
                "last_active": row[8],
                "integration_attempts": row[9]
            })

        logger.info(f"⚡ {len(contradictions)} contradições ativas acessadas por: {admin['email']}")

        return {
            "success": True,
            "contradictions": contradictions,
            "count": len(contradictions)
        }

    except Exception as e:
        logger.error(f"Erro ao obter contradições: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/narrative")
async def get_narrative_chapters(
    request: Request,
    admin: Dict = Depends(require_master)
):
    """
    Capítulos narrativos do agente

    Restrito ao master admin
    """
    try:
        from jung_core import HybridDatabaseManager
        from identity_config import AGENT_INSTANCE

        db = HybridDatabaseManager()
        cursor = db.conn.cursor()

        cursor.execute("""
            SELECT
                id,
                chapter_name,
                chapter_order,
                period_start,
                period_end,
                dominant_theme,
                emotional_tone,
                dominant_locus,
                agency_level,
                key_scenes,
                narrative_coherence
            FROM agent_narrative_chapters
            WHERE agent_instance = ?
            ORDER BY chapter_order DESC
        """, (AGENT_INSTANCE,))

        rows = cursor.fetchall()
        chapters = []

        for row in rows:
            chapters.append({
                "id": row[0],
                "name": row[1],
                "order": row[2],
                "start": row[3],
                "end": row[4],
                "theme": row[5],
                "tone": row[6],
                "locus": row[7],
                "agency": row[8],
                "key_scenes": json.loads(row[9]) if row[9] else [],
                "coherence": row[10],
                "is_current": row[4] is None
            })

        logger.info(f"📖 {len(chapters)} capítulos narrativos acessados por: {admin['email']}")

        return {
            "success": True,
            "chapters": chapters,
            "count": len(chapters)
        }

    except Exception as e:
        logger.error(f"Erro ao obter capítulos narrativos: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/consolidate")
async def run_manual_consolidation(
    admin: Dict = Depends(require_master)
):
    """
    Executa consolidação manual do sistema de identidade

    Processa conversas do usuário master que ainda não foram analisadas
    para extração de elementos identitários do agente.

    Requer: Master Admin only
    """
    from identity_config import ADMIN_USER_ID, MAX_CONVERSATIONS_PER_CONSOLIDATION
    from agent_identity_extractor import AgentIdentityExtractor
    from jung_core import HybridDatabaseManager

    try:
        start_time = time.time()

        # Conectar ao banco
        db = HybridDatabaseManager()
        cursor = db.conn.cursor()

        # Buscar conversas do master admin não processadas
        cursor.execute("""
            SELECT c.id, c.user_input, c.ai_response, c.timestamp
            FROM conversations c
            LEFT JOIN agent_identity_extractions e ON c.id = e.conversation_id
            WHERE c.user_id = ?
              AND e.conversation_id IS NULL
            ORDER BY c.timestamp DESC
            LIMIT ?
        """, (ADMIN_USER_ID, MAX_CONVERSATIONS_PER_CONSOLIDATION))

        conversations = cursor.fetchall()

        if not conversations:
            return JSONResponse({
                "success": True,
                "message": "Nenhuma conversa nova para processar",
                "stats": {
                    "conversations_processed": 0,
                    "elements_extracted": 0,
                    "processing_time_seconds": 0
                }
            })

        # Inicializar extrator
        extractor = AgentIdentityExtractor(db)

        # Processar cada conversa
        total_elements = 0
        conversations_processed = 0

        for conv in conversations:
            conv_id, user_input, ai_response, timestamp = conv

            try:
                # Extrair elementos identitários
                extracted = extractor.extract_from_conversation(
                    conversation_id=str(conv_id),
                    user_id=ADMIN_USER_ID,
                    user_input=user_input,
                    agent_response=ai_response
                )

                # Armazenar elementos
                if extractor.store_extracted_identity(extracted):
                    conversations_processed += 1
                    total_elements += sum(len(v) for v in extracted.values() if isinstance(v, list))

                # Delay para rate limiting
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Erro ao processar conversa {conv_id}: {e}")
                continue

        # Calcular estatísticas
        processing_time = time.time() - start_time

        # Obter estatísticas atualizadas
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM agent_identity_core WHERE agent_instance = 'jung_v1' AND is_current = 1) as nuclear_count,
                (SELECT AVG(certainty) FROM agent_identity_core WHERE agent_instance = 'jung_v1' AND is_current = 1) as avg_certainty,
                (SELECT COUNT(*) FROM agent_identity_contradictions WHERE agent_instance = 'jung_v1' AND status IN ('unresolved', 'integrating')) as contradictions_count,
                (SELECT COUNT(*) FROM agent_narrative_chapters WHERE agent_instance = 'jung_v1') as chapters_count,
                (SELECT COUNT(*) FROM agent_possible_selves WHERE agent_instance = 'jung_v1' AND status = 'active') as possible_selves_count,
                (SELECT COUNT(*) FROM agent_agency_memory WHERE agent_instance = 'jung_v1') as agency_moments_count
        """)
        current_stats = cursor.fetchone()

        logger.info(f"✅ Consolidação manual executada por {admin['email']}")
        logger.info(f"   📊 {conversations_processed} conversas processadas")
        logger.info(f"   🧠 {total_elements} elementos extraídos")
        logger.info(f"   ⏱️  {processing_time:.2f}s")

        return JSONResponse({
            "success": True,
            "message": f"Consolidação executada com sucesso! {conversations_processed} conversas processadas.",
            "stats": {
                "conversations_processed": conversations_processed,
                "elements_extracted": total_elements,
                "processing_time_seconds": round(processing_time, 2)
            },
            "current_identity_stats": {
                "nuclear_beliefs": current_stats[0] or 0,
                "avg_certainty": round(current_stats[1] or 0, 2),
                "active_contradictions": current_stats[2] or 0,
                "narrative_chapters": current_stats[3] or 0,
                "possible_selves": current_stats[4] or 0,
                "agency_moments": current_stats[5] or 0
            }
        })

    except Exception as e:
        logger.error(f"❌ Erro na consolidação manual: {e}", exc_info=True)
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


@router.get("/dashboard")
async def agent_identity_dashboard(
    request: Request,
    admin: Dict = Depends(require_master)
):
    """
    Interface HTML do dashboard de identidade do agente

    Restrito ao master admin
    """

    logger.info(f"🎨 Dashboard de identidade acessado por master admin: {admin['email']}")

    html_content = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jung - Identidade Nuclear do Agente</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        .card h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.5em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }

        .stat-box {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            background: #f7f8fc;
            border-radius: 8px;
            margin-bottom: 10px;
        }

        .stat-label {
            font-weight: 600;
            color: #555;
        }

        .stat-value {
            font-size: 1.3em;
            font-weight: bold;
            color: #667eea;
        }

        .belief-item, .contradiction-item, .chapter-item {
            padding: 15px;
            background: #f7f8fc;
            border-left: 4px solid #667eea;
            border-radius: 8px;
            margin-bottom: 12px;
        }

        .belief-content {
            font-size: 1.05em;
            color: #333;
            margin-bottom: 8px;
        }

        .belief-meta {
            display: flex;
            gap: 15px;
            font-size: 0.9em;
            color: #666;
        }

        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }

        .badge-type { background: #e3f2fd; color: #1976d2; }
        .badge-certainty { background: #c8e6c9; color: #388e3c; }
        .badge-tension { background: #ffebee; color: #d32f2f; }
        .badge-theme { background: #fff3e0; color: #f57c00; }

        .contradiction-poles {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }

        .pole {
            flex: 1;
            font-weight: 600;
            color: #333;
        }

        .vs {
            color: #d32f2f;
            font-weight: bold;
            font-size: 1.2em;
        }

        .loading {
            text-align: center;
            color: #666;
            font-style: italic;
        }

        .error {
            color: #d32f2f;
            background: #ffebee;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }

        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            display: block;
            margin: 20px auto;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            transition: all 0.3s;
        }

        .refresh-btn:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
        }

        .empty-state {
            text-align: center;
            padding: 30px;
            color: #999;
            font-style: italic;
        }

        /* Mensagens de Feedback */
        .message-box {
            padding: 15px 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            display: none;
            font-weight: 500;
            animation: slideDown 0.3s ease;
            white-space: pre-wrap;
        }

        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .message-success {
            background: rgba(16, 185, 129, 0.1);
            border: 2px solid #10b981;
            color: #059669;
        }

        .message-error {
            background: rgba(239, 68, 68, 0.1);
            border: 2px solid #ef4444;
            color: #dc2626;
        }

        .message-info {
            background: rgba(59, 130, 246, 0.1);
            border: 2px solid #3b82f6;
            color: #2563eb;
        }

        /* Loading state do botão */
        button.loading {
            opacity: 0.6;
            cursor: not-allowed;
            pointer-events: none;
        }

        button.loading::after {
            content: "...";
            animation: dots 1.5s steps(3, end) infinite;
        }

        @keyframes dots {
            0%, 20% { content: "."; }
            40% { content: ".."; }
            60%, 100% { content: "..."; }
        }

        /* Controles do Dashboard */
        .dashboard-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }

        .dashboard-controls h1 {
            margin: 0;
        }

        .controls-buttons {
            display: flex;
            gap: 10px;
        }

        .btn-consolidate {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            transition: all 0.3s ease;
        }

        .btn-consolidate:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }

        .btn-refresh {
            background: white;
            color: #667eea;
            border: 2px solid #667eea;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn-refresh:hover {
            background: #f7f8fc;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Controles do Dashboard -->
        <div class="dashboard-controls">
            <h1>🧠 Jung - Identidade Nuclear do Agente</h1>
            <div class="controls-buttons">
                <button
                    id="consolidate-btn"
                    class="btn-consolidate"
                    onclick="runConsolidation()"
                >
                    ⚙️ Executar Consolidação Manual
                </button>
                <button
                    class="btn-refresh"
                    onclick="loadAllData()"
                >
                    🔄 Atualizar Dados
                </button>
            </div>
        </div>

        <!-- Mensagens de Feedback -->
        <div id="message" class="message-box"></div>

        <!-- Estatísticas Gerais -->
        <div class="card">
            <h2>📊 Estatísticas Gerais</h2>
            <div id="stats-content" class="loading">Carregando...</div>
        </div>

        <div class="dashboard-grid">
            <!-- Crenças Nucleares -->
            <div class="card">
                <h2>💎 Crenças Nucleares</h2>
                <div id="beliefs-content" class="loading">Carregando...</div>
            </div>

            <!-- Contradições Ativas -->
            <div class="card">
                <h2>⚡ Contradições Ativas</h2>
                <div id="contradictions-content" class="loading">Carregando...</div>
            </div>
        </div>

        <!-- Capítulos Narrativos -->
        <div class="card">
            <h2>📖 Capítulos Narrativos</h2>
            <div id="narrative-content" class="loading">Carregando...</div>
        </div>
    </div>

    <script>
        async function loadStats() {
            try {
                const response = await fetch('/admin/agent-identity/stats');
                const data = await response.json();

                if (!data.success) {
                    document.getElementById('stats-content').innerHTML =
                        `<div class="error">Erro: ${data.error}</div>`;
                    return;
                }

                const stats = data.stats;
                let html = '';

                html += `<div class="stat-box">
                    <span class="stat-label">Crenças Nucleares</span>
                    <span class="stat-value">${stats.nuclear_count || 0}</span>
                </div>`;

                html += `<div class="stat-box">
                    <span class="stat-label">Certeza Média</span>
                    <span class="stat-value">${(stats.nuclear_avg_certainty || 0).toFixed(2)}</span>
                </div>`;

                html += `<div class="stat-box">
                    <span class="stat-label">Contradições Ativas</span>
                    <span class="stat-value">${stats.contradictions_active || 0}</span>
                </div>`;

                html += `<div class="stat-box">
                    <span class="stat-label">Tensão Média</span>
                    <span class="stat-value">${(stats.contradictions_avg_tension || 0).toFixed(2)}</span>
                </div>`;

                html += `<div class="stat-box">
                    <span class="stat-label">Capítulos Narrativos</span>
                    <span class="stat-value">${stats.narrative_chapters_total || 0}</span>
                </div>`;

                html += `<div class="stat-box">
                    <span class="stat-label">Identidades Relacionais</span>
                    <span class="stat-value">${stats.relational_identities || 0}</span>
                </div>`;

                document.getElementById('stats-content').innerHTML = html;

            } catch (error) {
                document.getElementById('stats-content').innerHTML =
                    `<div class="error">Erro ao carregar estatísticas: ${error.message}</div>`;
            }
        }

        async function loadBeliefs() {
            try {
                const response = await fetch('/admin/agent-identity/nuclear');
                const data = await response.json();

                if (!data.success) {
                    document.getElementById('beliefs-content').innerHTML =
                        `<div class="error">Erro: ${data.error}</div>`;
                    return;
                }

                if (data.count === 0) {
                    document.getElementById('beliefs-content').innerHTML =
                        '<div class="empty-state">Nenhuma crença nuclear ainda</div>';
                    return;
                }

                let html = '';
                data.beliefs.forEach(belief => {
                    html += `<div class="belief-item">
                        <div class="belief-content">${belief.content}</div>
                        <div class="belief-meta">
                            <span class="badge badge-type">${belief.type}</span>
                            <span class="badge badge-certainty">Certeza: ${(belief.certainty * 100).toFixed(0)}%</span>
                            <span>Estabilidade: ${(belief.stability * 100).toFixed(0)}%</span>
                        </div>
                    </div>`;
                });

                document.getElementById('beliefs-content').innerHTML = html;

            } catch (error) {
                document.getElementById('beliefs-content').innerHTML =
                    `<div class="error">Erro ao carregar crenças: ${error.message}</div>`;
            }
        }

        async function loadContradictions() {
            try {
                const response = await fetch('/admin/agent-identity/contradictions');
                const data = await response.json();

                if (!data.success) {
                    document.getElementById('contradictions-content').innerHTML =
                        `<div class="error">Erro: ${data.error}</div>`;
                    return;
                }

                if (data.count === 0) {
                    document.getElementById('contradictions-content').innerHTML =
                        '<div class="empty-state">Nenhuma contradição ativa</div>';
                    return;
                }

                let html = '';
                data.contradictions.forEach(c => {
                    html += `<div class="contradiction-item">
                        <div class="contradiction-poles">
                            <div class="pole">${c.pole_a}</div>
                            <div class="vs">⚡</div>
                            <div class="pole">${c.pole_b}</div>
                        </div>
                        <div class="belief-meta">
                            <span class="badge badge-type">${c.type}</span>
                            <span class="badge badge-tension">Tensão: ${(c.tension * 10).toFixed(1)}/10</span>
                            <span>Status: ${c.status}</span>
                        </div>
                    </div>`;
                });

                document.getElementById('contradictions-content').innerHTML = html;

            } catch (error) {
                document.getElementById('contradictions-content').innerHTML =
                    `<div class="error">Erro ao carregar contradições: ${error.message}</div>`;
            }
        }

        async function loadNarrative() {
            try {
                const response = await fetch('/admin/agent-identity/narrative');
                const data = await response.json();

                if (!data.success) {
                    document.getElementById('narrative-content').innerHTML =
                        `<div class="error">Erro: ${data.error}</div>`;
                    return;
                }

                if (data.count === 0) {
                    document.getElementById('narrative-content').innerHTML =
                        '<div class="empty-state">Nenhum capítulo narrativo ainda</div>';
                    return;
                }

                let html = '';
                data.chapters.forEach(ch => {
                    const currentBadge = ch.is_current ? ' <span class="badge badge-certainty">ATUAL</span>' : '';
                    html += `<div class="chapter-item">
                        <div class="belief-content">
                            <strong>${ch.name}</strong>${currentBadge}
                        </div>
                        <div class="belief-meta">
                            <span class="badge badge-theme">${ch.theme || 'N/A'}</span>
                            <span>Tom: ${ch.tone || 'N/A'}</span>
                            <span>Locus: ${ch.locus || 'N/A'}</span>
                            <span>Agência: ${ch.agency ? (ch.agency * 100).toFixed(0) + '%' : 'N/A'}</span>
                        </div>
                    </div>`;
                });

                document.getElementById('narrative-content').innerHTML = html;

            } catch (error) {
                document.getElementById('narrative-content').innerHTML =
                    `<div class="error">Erro ao carregar narrativa: ${error.message}</div>`;
            }
        }

        function loadAllData() {
            loadStats();
            loadBeliefs();
            loadContradictions();
            loadNarrative();
        }

        // Função para mostrar mensagens de feedback
        function showMessage(text, type) {
            const msgBox = document.getElementById('message');
            msgBox.className = 'message-box message-' + type;
            msgBox.textContent = text;
            msgBox.style.display = 'block';

            // Auto-fechar após 5 segundos
            setTimeout(() => {
                msgBox.style.display = 'none';
            }, 5000);
        }

        // Função para executar consolidação manual
        async function runConsolidation() {
            const button = document.getElementById('consolidate-btn');
            const originalText = button.textContent;

            try {
                // Desabilitar botão e mostrar loading
                button.classList.add('loading');
                button.textContent = '⚙️ Consolidando';

                showMessage('🔄 Iniciando consolidação de identidade...', 'info');

                // Fazer requisição POST
                const response = await fetch('/admin/agent-identity/consolidate', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    // Sucesso: mostrar estatísticas
                    const stats = data.stats;
                    const currentStats = data.current_identity_stats;

                    let message = `✅ ${data.message}\n\n`;
                    message += `📊 Conversas processadas: ${stats.conversations_processed}\n`;
                    message += `🧠 Elementos extraídos: ${stats.elements_extracted}\n`;
                    message += `⏱️  Tempo: ${stats.processing_time_seconds}s\n\n`;
                    message += `📈 Estado atual:\n`;
                    message += `   • ${currentStats.nuclear_beliefs} crenças nucleares\n`;
                    message += `   • ${currentStats.active_contradictions} contradições ativas\n`;
                    message += `   • ${currentStats.narrative_chapters} capítulos narrativos`;

                    showMessage(message, 'success');

                    // Recarregar dados após 2 segundos
                    setTimeout(() => {
                        loadAllData();
                    }, 2000);
                } else {
                    // Erro retornado pela API
                    showMessage('❌ Erro: ' + (data.error || 'Desconhecido'), 'error');
                }

            } catch (error) {
                // Erro de rede/conexão
                showMessage('❌ Erro ao executar consolidação: ' + error.message, 'error');
                console.error('Erro na consolidação:', error);

            } finally {
                // Restaurar botão
                button.classList.remove('loading');
                button.textContent = originalText;
            }
        }

        // Carregar dados ao iniciar
        loadAllData();

        // Auto-refresh a cada 30 segundos
        setInterval(loadAllData, 30000);
    </script>
</body>
</html>
    """

    return HTMLResponse(content=html_content)


logger.info("✅ Rotas de identidade do agente inicializadas (Master Admin only)")
