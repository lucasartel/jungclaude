"""Database mixin for Phase IV.3 double-loop metacognition evaluations."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_COOLDOWN_HOURS = 24


class MetaCognitionDatabaseMixin:
    """Database mixin for persisting and querying double-loop metacognition evaluations."""

    def _init_meta_cognition_schema(self) -> None:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_meta_cognition_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_instance TEXT NOT NULL,
                    cycle_id TEXT NOT NULL,
                    evaluation_type TEXT DEFAULT 'double_loop',
                    resonance_score REAL DEFAULT 0.0,
                    coherence_score REAL DEFAULT 0.0,
                    biases_detected_json TEXT,
                    heuristic_adjustments_json TEXT,
                    recommendations_json TEXT,
                    summary TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_meta_cognition_instance_created "
                "ON agent_meta_cognition_evaluations(agent_instance, created_at)"
            )
            self.conn.commit()

    def save_meta_cognition_evaluation(
        self,
        *,
        agent_instance: str,
        cycle_id: str,
        evaluation_type: str = "double_loop",
        resonance_score: float = 0.0,
        coherence_score: float = 0.0,
        biases_detected: Optional[List[Dict[str, Any]]] = None,
        heuristic_adjustments: Optional[List[Dict[str, Any]]] = None,
        recommendations: Optional[List[str]] = None,
        summary: str = "",
    ) -> int:
        """Persists a new double-loop metacognition evaluation record."""
        self._init_meta_cognition_schema()
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO agent_meta_cognition_evaluations (
                    agent_instance, cycle_id, evaluation_type,
                    resonance_score, coherence_score,
                    biases_detected_json, heuristic_adjustments_json,
                    recommendations_json, summary, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent_instance,
                    cycle_id,
                    evaluation_type,
                    resonance_score,
                    coherence_score,
                    json.dumps(biases_detected or []),
                    json.dumps(heuristic_adjustments or []),
                    json.dumps(recommendations or []),
                    summary,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            self.conn.commit()
            eval_id = cursor.lastrowid
            logger.info(
                "✅ [META-COGNITION DB] Evaluation saved id=%s instance=%s cycle=%s type=%s",
                eval_id,
                agent_instance,
                cycle_id,
                evaluation_type,
            )
            return eval_id

    def get_latest_meta_cognition_evaluation(
        self,
        *,
        agent_instance: str,
        evaluation_type: Optional[str] = "double_loop",
    ) -> Optional[Dict[str, Any]]:
        """Returns the most recent metacognition evaluation record for the instance."""
        self._init_meta_cognition_schema()
        with self._lock:
            cursor = self.conn.cursor()
            if evaluation_type:
                cursor.execute(
                    """
                    SELECT * FROM agent_meta_cognition_evaluations
                    WHERE agent_instance = ? AND evaluation_type = ?
                    ORDER BY id DESC LIMIT 1
                    """,
                    (agent_instance, evaluation_type),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM agent_meta_cognition_evaluations
                    WHERE agent_instance = ?
                    ORDER BY id DESC LIMIT 1
                    """,
                    (agent_instance,),
                )
            row = cursor.fetchone()
            if not row:
                return None
            return self._parse_evaluation_row(row)

    def is_meta_cognition_cooldown_active(
        self,
        *,
        agent_instance: str,
        cooldown_hours: int = DEFAULT_COOLDOWN_HOURS,
    ) -> bool:
        """Returns True if a double-loop evaluation ran within the cooldown window."""
        latest = self.get_latest_meta_cognition_evaluation(
            agent_instance=agent_instance,
            evaluation_type="double_loop",
        )
        if not latest:
            return False
        created_at_str = latest.get("created_at")
        if not created_at_str:
            return False
        try:
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            elapsed = (now - created_at).total_seconds()
            return elapsed < (cooldown_hours * 3600)
        except Exception as exc:
            logger.warning("meta_cognition: error parsing cooldown timestamp: %s", exc)
            return False

    def _parse_evaluation_row(self, row: Any) -> Dict[str, Any]:
        d = dict(row)
        for key in ("biases_detected_json", "heuristic_adjustments_json", "recommendations_json"):
            raw = d.get(key)
            target = key.replace("_json", "")
            try:
                d[target] = json.loads(raw) if raw else []
            except Exception:
                d[target] = []
        return d
