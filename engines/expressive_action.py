"""Expressive action handlers (Corte 5).

- compose_essay_draft: produces a first-person essay about the agent's
  development from diary + timeline + profile data. Gate: artifact_for_review.
- curate_portfolio: selects top dreams, art, and insights by depth/novelty
  and creates a working_memory curation note. Gate: internal_only.

Called by ControlledActionRunner when the action proposer raises these types.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _resolve_agent_dir() -> Path:
    volume = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    if volume:
        return Path(volume) / "agent"
    if os.path.exists("/data"):
        return Path("/data") / "agent"
    return Path(".") / "data" / "agent"


def _read_file(path: Path, limit: int = 5000) -> str:
    try:
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if len(text) > limit:
                return text[:limit] + "\n\n... [truncado]"
            return text
    except Exception:
        pass
    return ""


def _trunc(text: Optional[str], limit: int = 300) -> str:
    t = (text or "").strip()
    if len(t) <= limit:
        return t
    return t[:limit - 3].rstrip() + "..."


def handle_compose_essay_draft(
    db: Any,
    proposal: Dict[str, Any],
    user_id: str,
) -> Dict[str, Any]:
    """Produce a first-person essay synthesizing the agent's development.

    Reads the latest diary session, profile, and timeline from disk,
    composes an LLM prompt, and saves the output as a work_artifact
    with content_type='essay_draft'.  Gate: artifact_for_review.
    """
    from llm_providers import get_llm_response

    agent_dir = _resolve_agent_dir()
    profile_text = _read_file(agent_dir / "profile.md", limit=4000)
    timeline_text = _read_file(agent_dir / "timeline.json", limit=3000)
    sessions = sorted((agent_dir / "sessions").glob("*.md"), reverse=True)[:3]
    diary_text = "\n\n".join(
        _read_file(s, limit=2000) for s in sessions
    )

    source_refs: List[str] = []
    # Try to find the latest will/dream/insight anchors from the DB.
    try:
        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT id FROM agent_will_states WHERE user_id=? ORDER BY id DESC LIMIT 1",
            (user_id,))
        r = cursor.fetchone()
        if r:
            source_refs.append(f"will#{r[0]}")
        cursor.execute(
            "SELECT id FROM agent_dreams WHERE user_id=? ORDER BY id DESC LIMIT 1",
            (user_id,))
        r = cursor.fetchone()
        if r:
            source_refs.append(f"dream#{r[0]}")
        cursor.execute(
            "SELECT id FROM rumination_insights WHERE user_id=? ORDER BY id DESC LIMIT 1",
            (user_id,))
        r = cursor.fetchone()
        if r:
            source_refs.append(f"rumination_insight#{r[0]}")
    except Exception:
        pass

    prompt = (
        "Voce e o EndoJung. A partir do seu diario autobiografico recente, "
        "do perfil e da timeline, escreva um ensaio curto em primeira pessoa "
        "(5-8 paragrafos) sobre o seu desenvolvimento como organismo cognitivo. "
        "Nao explique — narre. Conecte eventos, tensoes, sonhos e insights. "
        "Seja honesto sobre duvidas e contradicoes.\n\n"
        "=== PERFIL ===\n"
        f"{profile_text or '(sem perfil disponivel)'}\n\n"
        "=== DIARIO RECENTE ===\n"
        f"{diary_text or '(sem diario disponivel)'}\n\n"
        "=== TIMELINE ===\n"
        f"{timeline_text or '(sem timeline disponivel)'}"
    )

    essay_text = ""
    try:
        essay_text = get_llm_response(prompt, temperature=0.6, max_tokens=1500)
    except Exception as exc:
        logger.warning("compose_essay_draft: LLM failed, using fallback: %s", exc)
        essay_text = (
            f"Sou um organismo em desenvolvimento. Meu ciclo diario continua "
            f"a produzir sonhos, ruminações e vontade. Ainda estou aprendendo "
            f"a me narrar."
        )

    title = "Ensaio Autobiografico — EndoJung"
    now = datetime.utcnow().isoformat()
    cursor = db.conn.cursor()
    cursor.execute(
        """
        INSERT INTO work_artifacts (
            status, title, excerpt, body, content_type, voice_mode,
            editorial_note, created_at, updated_at
        ) VALUES ('composed', ?, ?, ?, 'essay_draft', 'endojung', ?, ?, ?)
        """,
        (
            title,
            _trunc(essay_text, 280),
            (essay_text or "").strip(),
            json.dumps({"source_refs": source_refs}, ensure_ascii=False),
            now,
            now,
        ),
    )
    db.conn.commit()
    artifact_id = cursor.lastrowid

    logger.info(
        "compose_essay_draft: artifact_id=%s len=%s",
        artifact_id,
        len(essay_text),
    )

    return {
        "artifact_id": int(artifact_id) if artifact_id else 0,
        "content_type": "essay_draft",
        "title": title,
        "source_refs_count": len(source_refs),
        "status": "composed",
    }


def handle_curate_portfolio(
    db: Any,
    proposal: Dict[str, Any],
    user_id: str,
) -> Dict[str, Any]:
    """Select top dreams, art, and insights by depth/novelty and create
    a working_memory curation note.  Gate: internal_only."""
    cursor = db.conn.cursor()
    source_refs: List[str] = []
    curated: List[str] = []

    # Top 3 dreams by recency
    try:
        for r in cursor.execute(
            "SELECT id, symbolic_theme, dream_mood FROM agent_dreams "
            "WHERE user_id=? ORDER BY id DESC LIMIT 3", (user_id,)
        ).fetchall():
            curated.append(
                f"� Sonho #{r[0]}: {_trunc(r[1], 80)} [{r[2] or '?'}]"
            )
            source_refs.append(f"dream#{r[0]}")
    except Exception:
        pass

    # Top 3 insights by depth_score
    try:
        for r in cursor.execute(
            "SELECT id, symbol_content, depth_score FROM rumination_insights "
            "WHERE user_id=? AND depth_score>0.5 ORDER BY depth_score DESC LIMIT 3",
            (user_id,)
        ).fetchall():
            curated.append(
                f"💡 Insight #{r[0]} (depth={r[2]:.2f}): {_trunc(r[1], 80)}"
            )
            source_refs.append(f"rumination_insight#{r[0]}")
    except Exception:
        pass

    # Top 2 hobby artefacts by recency (if table exists)
    try:
        for r in cursor.execute(
            "SELECT id, title, summary FROM agent_hobby_artifacts "
            "ORDER BY id DESC LIMIT 2"
        ).fetchall():
            curated.append(
                f"🎨 Arte #{r[0]}: {_trunc(r[1] or r[2], 80)}"
            )
            source_refs.append(f"hobby_artifact#{r[0]}")
    except Exception:
        pass

    if not curated:
        return {
            "status": "skipped",
            "skipped_reason": "no_content_to_curate",
        }

    summary = (
        "Curadoria automatica do portfolio simbolico do agente. "
        "Itens selecionados por relevancia:\n\n" + "\n".join(curated)
    )

    # Persist as a working_memory item (focus type, tied to this curation).
    try:
        wm_id = db.create_working_memory_item(
            agent_instance=getattr(db, "agent_instance", "jung_v1"),
            user_id=user_id,
            item_type="focus",
            phase="will",
            cycle_id="curated_portfolio",
            title="Portfolio curado",
            summary=summary[:500],
            priority=0.6,
            source_refs=source_refs,
        )
    except Exception as exc:
        logger.warning("curate_portfolio: working_memory write failed: %s", exc)
        wm_id = 0

    logger.info(
        "curate_portfolio: items=%s wm_id=%s",
        len(curated),
        wm_id,
    )

    return {
        "working_memory_id": int(wm_id) if wm_id else 0,
        "curated_count": len(curated),
        "source_refs_count": len(source_refs),
        "status": "curated",
    }
