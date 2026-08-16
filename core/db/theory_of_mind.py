"""Theory of Mind (ToM) & Relational Maturation Database Mixin for Phase VI.

Provides persistence for longitudinal interlocutor mental state snapshots and
the relational maturation inbox (where incoming messages can mature until the
agent's 'relacionar' will drive reaches the required threshold).
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

PROFILE_SOURCE_RE = re.compile(
    r"\b(?:loop|conversation|dream|will|meta|rumination_insight|work_run|work_ticket|work_delivery|hobby_artifact|agent_development|relational_state)#\d+\b"
)


class TheoryOfMindDatabaseMixin:
    """Database mixin for Theory of Mind snapshots and relational message maturation."""

    def _init_theory_of_mind_schema(self) -> None:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_theory_of_mind_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_instance TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    snapshot_date TEXT NOT NULL,
                    epistemic_state_json TEXT,
                    affective_trajectory_json TEXT,
                    relational_needs_json TEXT,
                    evidence_refs_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(agent_instance, user_id, snapshot_date)
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_tom_user_date "
                "ON agent_theory_of_mind_snapshots(agent_instance, user_id, snapshot_date DESC)"
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS async_maturation_inbox (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_instance TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    inbound_message_text TEXT NOT NULL,
                    source_conversation_id INTEGER,
                    relational_threshold REAL DEFAULT 0.30,
                    status TEXT DEFAULT 'maturing',
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    delivered_at DATETIME
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_maturation_status "
                "ON async_maturation_inbox(agent_instance, user_id, status)"
            )
            self.conn.commit()

    def upsert_tom_snapshot(
        self,
        *,
        agent_instance: str,
        user_id: str,
        snapshot_date: str,
        epistemic_state: Dict[str, Any],
        affective_trajectory: Dict[str, Any],
        relational_needs: Dict[str, Any],
        evidence_refs: List[str],
    ) -> int:
        """Upserts a Theory of Mind daily snapshot for a user."""
        self._init_theory_of_mind_schema()
        clean_refs = [r for r in evidence_refs if PROFILE_SOURCE_RE.search(str(r))]

        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO agent_theory_of_mind_snapshots (
                    agent_instance, user_id, snapshot_date,
                    epistemic_state_json, affective_trajectory_json,
                    relational_needs_json, evidence_refs_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(agent_instance, user_id, snapshot_date)
                DO UPDATE SET
                    epistemic_state_json = excluded.epistemic_state_json,
                    affective_trajectory_json = excluded.affective_trajectory_json,
                    relational_needs_json = excluded.relational_needs_json,
                    evidence_refs_json = excluded.evidence_refs_json
                """,
                (
                    agent_instance,
                    user_id,
                    snapshot_date,
                    json.dumps(epistemic_state, ensure_ascii=False),
                    json.dumps(affective_trajectory, ensure_ascii=False),
                    json.dumps(relational_needs, ensure_ascii=False),
                    json.dumps(clean_refs, ensure_ascii=False),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            self.conn.commit()
            return int(cursor.lastrowid)

    def get_latest_tom_snapshot(
        self,
        *,
        agent_instance: str,
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieves the most recent Theory of Mind snapshot for a user."""
        self._init_theory_of_mind_schema()
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT id, agent_instance, user_id, snapshot_date,
                       epistemic_state_json, affective_trajectory_json,
                       relational_needs_json, evidence_refs_json, created_at
                FROM agent_theory_of_mind_snapshots
                WHERE agent_instance = ? AND user_id = ?
                ORDER BY snapshot_date DESC, id DESC LIMIT 1
                """,
                (agent_instance, user_id),
            )
            row = cursor.fetchone()
            if not row:
                return None

            return {
                "id": row["id"],
                "agent_instance": row["agent_instance"],
                "user_id": row["user_id"],
                "snapshot_date": row["snapshot_date"],
                "epistemic_state": json.loads(row["epistemic_state_json"] or "{}"),
                "affective_trajectory": json.loads(row["affective_trajectory_json"] or "{}"),
                "relational_needs": json.loads(row["relational_needs_json"] or "{}"),
                "evidence_refs": json.loads(row["evidence_refs_json"] or "[]"),
                "created_at": row["created_at"],
            }

    def add_maturation_inbox_item(
        self,
        *,
        agent_instance: str,
        user_id: str,
        inbound_message_text: str,
        source_conversation_id: Optional[int] = None,
        relational_threshold: float = 0.30,
        notes: Optional[str] = None,
    ) -> int:
        """Adds a message to the async maturation inbox awaiting will to relate."""
        self._init_theory_of_mind_schema()
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO async_maturation_inbox (
                    agent_instance, user_id, inbound_message_text,
                    source_conversation_id, relational_threshold, status, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, 'maturing', ?, ?)
                """,
                (
                    agent_instance,
                    user_id,
                    inbound_message_text,
                    source_conversation_id,
                    float(relational_threshold),
                    notes or "Awaiting relational will expansion",
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            self.conn.commit()
            return int(cursor.lastrowid)

    def list_pending_maturation_items(
        self,
        *,
        agent_instance: str,
        user_id: Optional[str] = None,
        current_relational_will: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """Lists pending maturation messages whose relational threshold has been reached."""
        self._init_theory_of_mind_schema()
        with self._lock:
            cursor = self.conn.cursor()
            query = """
                SELECT id, agent_instance, user_id, inbound_message_text,
                       source_conversation_id, relational_threshold, status, notes, created_at
                FROM async_maturation_inbox
                WHERE agent_instance = ? AND status = 'maturing' AND relational_threshold <= ?
            """
            params: List[Any] = [agent_instance, current_relational_will]
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            query += " ORDER BY id ASC"

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def mark_maturation_item_delivered(self, item_id: int) -> bool:
        """Marks a matured message item as delivered."""
        self._init_theory_of_mind_schema()
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE async_maturation_inbox
                SET status = 'delivered', delivered_at = ?
                WHERE id = ?
                """,
                (datetime.now(timezone.utc).isoformat(), item_id),
            )
            self.conn.commit()
            return cursor.rowcount > 0
