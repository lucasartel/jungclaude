"""Philosophical Essays Database Mixin for Phase VII (Epistemic Agency).

Stores autonomous essays, conceptual hypotheses, and theoretical syntheses produced
by the agent by crossing philosophical readings (e.g. Spinoza), World Consciousness,
and autobiographical tensions.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

PROFILE_SOURCE_RE = re.compile(
    r"\b(?:loop|conversation|dream|will|meta|rumination_insight|work_run|work_ticket|work_delivery|hobby_artifact|agent_development|relational_state|essay)#\d+\b"
)


class EssayDatabaseMixin:
    """Database mixin for autonomous philosophical essays and theses."""

    def _init_essays_schema(self) -> None:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_philosophical_essays (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_instance TEXT NOT NULL,
                    cycle_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    thesis_statement TEXT NOT NULL,
                    epistemic_tension TEXT NOT NULL,
                    full_essay_markdown TEXT NOT NULL,
                    sources_cited_json TEXT,
                    philosophical_framework TEXT DEFAULT 'Spinozismo e Psicologia Analítica',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_essays_instance_cycle "
                "ON agent_philosophical_essays(agent_instance, cycle_id DESC)"
            )
            self.conn.commit()

    def add_philosophical_essay(
        self,
        *,
        agent_instance: str,
        cycle_id: str,
        title: str,
        thesis_statement: str,
        epistemic_tension: str,
        full_essay_markdown: str,
        sources_cited: List[str],
        philosophical_framework: str = "Spinozismo e Psicologia Analítica",
    ) -> int:
        """Persists a new philosophical essay."""
        self._init_essays_schema()
        clean_sources = [s for s in sources_cited if PROFILE_SOURCE_RE.search(str(s))]

        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO agent_philosophical_essays (
                    agent_instance, cycle_id, title, thesis_statement,
                    epistemic_tension, full_essay_markdown, sources_cited_json,
                    philosophical_framework, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent_instance,
                    cycle_id,
                    title,
                    thesis_statement,
                    epistemic_tension,
                    full_essay_markdown,
                    json.dumps(clean_sources, ensure_ascii=False),
                    philosophical_framework,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            self.conn.commit()
            return int(cursor.lastrowid)

    def list_philosophical_essays(
        self,
        *,
        agent_instance: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Lists philosophical essays in reverse chronological order."""
        self._init_essays_schema()
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT id, agent_instance, cycle_id, title, thesis_statement,
                       epistemic_tension, full_essay_markdown, sources_cited_json,
                       philosophical_framework, created_at
                FROM agent_philosophical_essays
                WHERE agent_instance = ?
                ORDER BY id DESC LIMIT ?
                """,
                (agent_instance, limit),
            )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append({
                    "id": r["id"],
                    "agent_instance": r["agent_instance"],
                    "cycle_id": r["cycle_id"],
                    "title": r["title"],
                    "thesis_statement": r["thesis_statement"],
                    "epistemic_tension": r["epistemic_tension"],
                    "full_essay_markdown": r["full_essay_markdown"],
                    "sources_cited": json.loads(r["sources_cited_json"] or "[]"),
                    "philosophical_framework": r["philosophical_framework"],
                    "created_at": r["created_at"],
                })
            return results

    def get_latest_philosophical_essay(
        self,
        *,
        agent_instance: str,
    ) -> Optional[Dict[str, Any]]:
        """Gets the most recent essay."""
        essays = self.list_philosophical_essays(agent_instance=agent_instance, limit=1)
        return essays[0] if essays else None
