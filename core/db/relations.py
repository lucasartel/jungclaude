"""Persistence for scoped relationships between an agent and participants."""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional


RELATION_STATUSES = {"active", "paused", "revoked", "archived"}
CONSENT_STATUSES = {"pending", "granted", "revoked"}


def _json_dumps(value: Mapping[str, Any]) -> str:
    return json.dumps(dict(value), ensure_ascii=False, sort_keys=True)


def _json_loads(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _normalize_choice(value: Optional[str], allowed: set[str], field: str, default: str) -> str:
    normalized = (value or default).strip().lower()
    if normalized not in allowed:
        raise ValueError(f"invalid_{field}:{value}")
    return normalized


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


class RelationsDatabaseMixin:
    """Mixin for the first multi-participant Relations domain.

    A relation is the explicit scope boundary between one agent instance and
    one participant. Existing user and relational-state data remain untouched;
    later cuts can migrate individual subsystems behind this boundary.
    """

    def _init_relations_schema(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_relations (
                relation_id TEXT PRIMARY KEY,
                agent_instance TEXT NOT NULL,
                org_id TEXT,
                participant_user_id TEXT NOT NULL,
                relation_type TEXT NOT NULL DEFAULT 'participant',
                role TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                consent_status TEXT NOT NULL DEFAULT 'pending',
                consented_at DATETIME,
                revoked_at DATETIME,
                scope_json TEXT NOT NULL DEFAULT '{}',
                cadence_baseline_hours REAL,
                last_interaction_at DATETIME,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                UNIQUE(agent_instance, participant_user_id)
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_relations_instance "
            "ON agent_relations(agent_instance, status, updated_at DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_relations_org "
            "ON agent_relations(org_id, agent_instance, status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_relations_participant "
            "ON agent_relations(participant_user_id, agent_instance)"
        )
        self.conn.commit()

    def register_agent_relation(
        self,
        *,
        agent_instance: str,
        participant_user_id: str,
        org_id: Optional[str] = None,
        relation_type: str = "participant",
        role: Optional[str] = None,
        status: str = "active",
        consent_status: str = "pending",
        consented_at: Optional[str] = None,
        revoked_at: Optional[str] = None,
        scope: Optional[Mapping[str, Any]] = None,
        cadence_baseline_hours: Optional[float] = None,
        last_interaction_at: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> str:
        """Create or update the relation for an instance/participant pair."""
        clean_instance = (agent_instance or "").strip()
        clean_participant = (participant_user_id or "").strip()
        if not clean_instance:
            raise ValueError("agent_instance_required")
        if not clean_participant:
            raise ValueError("participant_user_id_required")
        clean_type = (relation_type or "participant").strip().lower()
        if not clean_type:
            raise ValueError("relation_type_required")
        clean_status = _normalize_choice(status, RELATION_STATUSES, "relation_status", "active")
        clean_consent = _normalize_choice(
            consent_status, CONSENT_STATUSES, "consent_status", "pending"
        )
        relation_id = str(uuid.uuid4())
        now = _now_iso()
        clean_consented_at = consented_at or (now if clean_consent == "granted" else None)
        clean_revoked_at = revoked_at or (
            now if clean_consent == "revoked" or clean_status == "revoked" else None
        )

        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO agent_relations (
                    relation_id, agent_instance, org_id, participant_user_id,
                    relation_type, role, status, consent_status, consented_at,
                    revoked_at, scope_json, cadence_baseline_hours,
                    last_interaction_at, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(agent_instance, participant_user_id) DO UPDATE SET
                    org_id = COALESCE(excluded.org_id, agent_relations.org_id),
                    relation_type = excluded.relation_type,
                    role = COALESCE(excluded.role, agent_relations.role),
                    status = excluded.status,
                    consent_status = excluded.consent_status,
                    consented_at = COALESCE(excluded.consented_at, agent_relations.consented_at),
                    revoked_at = excluded.revoked_at,
                    scope_json = excluded.scope_json,
                    cadence_baseline_hours = COALESCE(
                        excluded.cadence_baseline_hours,
                        agent_relations.cadence_baseline_hours
                    ),
                    last_interaction_at = COALESCE(
                        excluded.last_interaction_at,
                        agent_relations.last_interaction_at
                    ),
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    relation_id,
                    clean_instance,
                    (org_id or "").strip() or None,
                    clean_participant,
                    clean_type,
                    (role or "").strip() or None,
                    clean_status,
                    clean_consent,
                    clean_consented_at,
                    clean_revoked_at,
                    _json_dumps(scope or {}),
                    cadence_baseline_hours,
                    last_interaction_at,
                    _json_dumps(metadata or {}),
                    now,
                    now,
                ),
            )
            self.conn.commit()
            cursor.execute(
                """
                SELECT relation_id
                FROM agent_relations
                WHERE agent_instance = ? AND participant_user_id = ?
                """,
                (clean_instance, clean_participant),
            )
            row = cursor.fetchone()
            return str(row[0]) if row else relation_id

    def get_agent_relation(self, relation_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM agent_relations WHERE relation_id = ? LIMIT 1",
            ((relation_id or "").strip(),),
        )
        row = cursor.fetchone()
        return self._agent_relation_row_to_dict(row) if row else None

    def get_agent_relation_for_participant(
        self, *, agent_instance: str, participant_user_id: str
    ) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM agent_relations
            WHERE agent_instance = ? AND participant_user_id = ?
            LIMIT 1
            """,
            (agent_instance, participant_user_id),
        )
        row = cursor.fetchone()
        return self._agent_relation_row_to_dict(row) if row else None

    def list_agent_relations(
        self,
        *,
        agent_instance: str,
        org_id: Optional[str] = None,
        participant_user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        clauses = ["agent_instance = ?"]
        params: List[Any] = [agent_instance]
        if org_id:
            clauses.append("org_id = ?")
            params.append(org_id)
        if participant_user_id:
            clauses.append("participant_user_id = ?")
            params.append(participant_user_id)
        if status:
            clean_status = _normalize_choice(status, RELATION_STATUSES, "relation_status", "active")
            clauses.append("status = ?")
            params.append(clean_status)
        params.append(max(1, min(int(limit), 500)))
        cursor = self.conn.cursor()
        cursor.execute(
            f"""
            SELECT * FROM agent_relations
            WHERE {' AND '.join(clauses)}
            ORDER BY updated_at DESC, relation_id DESC
            LIMIT ?
            """,
            tuple(params),
        )
        return [self._agent_relation_row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def _agent_relation_row_to_dict(row: Any) -> Dict[str, Any]:
        data = dict(row)
        data["scope"] = _json_loads(data.pop("scope_json", None))
        data["metadata"] = _json_loads(data.pop("metadata_json", None))
        return data
