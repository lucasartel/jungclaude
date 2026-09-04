"""Arbitration between a completed WILL expression and a loop phase."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional


SATISFIABLE_PHASES = frozenset({"world", "work", "hobby"})
CAPABILITY_PHASE = {
    "saber_world_refresh": "world",
    "expressar_visual_artifact": "hobby",
}


def _dump(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=False, default=str)


def _load(value: Any) -> Dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def _row(row: Any) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    data = dict(row)
    data["evidence"] = _load(data.pop("evidence_json", None))
    return data


class WillPhaseArbitrationDatabaseMixin:
    """Additive schema for one-use phase satisfaction receipts."""

    def _init_will_phase_arbitration_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS will_phase_satisfactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_instance TEXT NOT NULL,
                relation_id TEXT,
                scope_kind TEXT NOT NULL DEFAULT 'global',
                cycle_id TEXT NOT NULL,
                phase TEXT NOT NULL,
                expression_id INTEGER NOT NULL UNIQUE,
                will_name TEXT NOT NULL,
                capability_key TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'available',
                quality REAL NOT NULL DEFAULT 1.0,
                source_ref TEXT NOT NULL,
                result_code TEXT NOT NULL,
                evidence_json TEXT NOT NULL DEFAULT '{}',
                valid_until DATETIME,
                consumed_by_phase_pulse_id INTEGER,
                consumed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        columns = {row[1] for row in self.conn.execute("PRAGMA table_info(will_phase_satisfactions)").fetchall()}
        for column, definition in (
            ("relation_id", "TEXT"),
            ("scope_kind", "TEXT NOT NULL DEFAULT 'global'"),
        ):
            if column not in columns:
                self.conn.execute(f"ALTER TABLE will_phase_satisfactions ADD COLUMN {column} {definition}")
        self.conn.execute(
            "UPDATE will_phase_satisfactions SET scope_kind = 'global' WHERE scope_kind IS NULL OR scope_kind = ''"
        )
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_will_phase_satisfactions_lookup
            ON will_phase_satisfactions(agent_instance, scope_kind, relation_id, cycle_id, phase, status, consumed_at)
            """
        )
        self.conn.commit()


class WillPhaseArbitration:
    """Turns a confirmed expression into at most one phase receipt."""

    def __init__(self, db_manager: Any):
        self.db = db_manager
        initializer = getattr(db_manager, "_init_will_phase_arbitration_schema", None)
        if callable(initializer):
            initializer()
        else:
            WillPhaseArbitrationDatabaseMixin._init_will_phase_arbitration_schema(db_manager)

    @staticmethod
    def _now() -> datetime:
        return datetime.utcnow()

    def record_expression_completion(
        self,
        expression: Dict[str, Any],
        *,
        validity_hours: float = 24.0,
    ) -> Optional[Dict[str, Any]]:
        if not expression or expression.get("status") != "completed":
            return None
        capability_key = str(expression.get("capability_key") or "")
        phase = CAPABILITY_PHASE.get(capability_key)
        if phase not in SATISFIABLE_PHASES:
            return None

        now = self._now()
        valid_until = now + timedelta(hours=max(0.0, float(validity_hours)))
        evidence = {
            "expression_id": expression.get("id"),
            "agent_instance": expression.get("agent_instance"),
            "relation_id": expression.get("relation_id"),
            "scope_kind": expression.get("scope_kind"),
            "delivery_confirmed": True,
        }
        self.db.conn.execute(
            """
            INSERT OR IGNORE INTO will_phase_satisfactions (
                agent_instance, relation_id, scope_kind, cycle_id, phase, expression_id, will_name,
                capability_key, quality, source_ref, result_code, evidence_json,
                valid_until, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expression.get("agent_instance") or "jung_v1",
                expression.get("relation_id"),
                expression.get("scope_kind") or "global",
                expression.get("cycle_id") or "",
                phase,
                int(expression["id"]),
                expression.get("will_name") or "",
                capability_key,
                1.0,
                f"will_expression#{expression['id']}",
                "delivery_confirmed",
                _dump(evidence),
                valid_until.isoformat(),
                now.isoformat(),
                now.isoformat(),
            ),
        )
        self.db.conn.commit()
        cursor = self.db.conn.execute(
            "SELECT * FROM will_phase_satisfactions WHERE expression_id = ?",
            (int(expression["id"]),),
        )
        return _row(cursor.fetchone())

    def claim_for_phase(
        self,
        *,
        agent_instance: str,
        cycle_id: str,
        phase: str,
        phase_pulse_id: int,
    ) -> Optional[Dict[str, Any]]:
        if phase not in SATISFIABLE_PHASES or not phase_pulse_id:
            return None
        now = self._now().isoformat()
        cursor = self.db.conn.execute(
            """
            SELECT id
            FROM will_phase_satisfactions
            WHERE agent_instance = ?
              AND cycle_id = ?
              AND phase = ?
              AND status = 'available'
              AND consumed_at IS NULL
              AND (valid_until IS NULL OR valid_until > ?)
            ORDER BY created_at ASC, id ASC
            LIMIT 1
            """,
            (agent_instance, cycle_id, phase, now),
        )
        candidate = cursor.fetchone()
        if not candidate:
            return None
        cursor.execute(
            """
            UPDATE will_phase_satisfactions
            SET status = 'consumed', consumed_by_phase_pulse_id = ?, consumed_at = ?, updated_at = ?
            WHERE id = ? AND status = 'available' AND consumed_at IS NULL
            """,
            (int(phase_pulse_id), now, now, candidate["id"]),
        )
        if cursor.rowcount != 1:
            self.db.conn.rollback()
            return None
        self.db.conn.commit()
        cursor.execute("SELECT * FROM will_phase_satisfactions WHERE id = ?", (candidate["id"],))
        return _row(cursor.fetchone())
