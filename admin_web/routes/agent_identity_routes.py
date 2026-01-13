"""
Rotas de Identidade Nuclear do Agente - Restrito Master Admin

Dashboard e APIs para visualização da identidade evolutiva do agente Jung.

Autor: Sistema de Identidade Nuclear
Data: 2026-01-12
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from typing import Dict
import logging
import json

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
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 Jung - Identidade Nuclear do Agente</h1>

        <button class="refresh-btn" onclick="loadAllData()">🔄 Atualizar Dados</button>

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
