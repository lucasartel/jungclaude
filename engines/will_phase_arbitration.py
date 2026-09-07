"""Evidence-based, reserved then committed WILL/phase arbitration."""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from engines.will_delivery_receipt import atomic, delivery_connection
from engines.will_phase_evidence import SCOPE_FIELDS, utc_time, validate_evidence

SATISFIABLE_PHASES = frozenset({"world", "hobby"})
CAPABILITY_PHASE = {"saber_world_refresh": "world", "expressar_visual_artifact": "hobby"}


def _dump(value):
    return json.dumps(value or {}, ensure_ascii=False, sort_keys=True)


def _load(value):
    try:
        parsed = json.loads(value or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except (ValueError, TypeError):
        return {}


def _row(row):
    if row is None:
        return None
    data = dict(row)
    data["evidence"] = _load(data.pop("evidence_json", None))
    return data


class WillPhaseArbitrationDatabaseMixin:
    def _init_will_phase_arbitration_schema(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS will_phase_satisfactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, agent_instance TEXT NOT NULL,
                relation_id TEXT, scope_kind TEXT NOT NULL DEFAULT 'global',
                cycle_id TEXT NOT NULL, phase TEXT NOT NULL,
                expression_id INTEGER NOT NULL UNIQUE, will_name TEXT NOT NULL,
                capability_key TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'available',
                quality REAL NOT NULL DEFAULT 0, source_ref TEXT NOT NULL,
                result_code TEXT NOT NULL, evidence_json TEXT NOT NULL DEFAULT '{}',
                valid_until DATETIME, consumed_by_phase_pulse_id INTEGER, consumed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        columns = {row[1] for row in self.conn.execute("PRAGMA table_info(will_phase_satisfactions)")}
        for name, definition in (
            ("relation_id", "TEXT"), ("scope_kind", "TEXT NOT NULL DEFAULT 'global'"),
            ("evidence_version", "INTEGER NOT NULL DEFAULT 0"),
            ("reserved_by_phase_pulse_id", "INTEGER"), ("reserved_at", "TEXT"),
            ("phase_result_id", "INTEGER"),
            ("user_id", "TEXT"),
            ("integration_version", "INTEGER NOT NULL DEFAULT 0"),
            ("integration_at", "TEXT"), ("integration_attempts", "INTEGER NOT NULL DEFAULT 0"),
            ("integration_next_at", "TEXT"), ("integration_error", "TEXT"),
        ):
            if name not in columns:
                self.conn.execute(f"ALTER TABLE will_phase_satisfactions ADD COLUMN {name} {definition}")
        self.conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_will_phase_active_reservation_v1
            ON will_phase_satisfactions(reserved_by_phase_pulse_id)
            WHERE evidence_version = 1 AND reserved_by_phase_pulse_id IS NOT NULL
              AND status IN ('reserved', 'consumed')
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_will_phase_satisfactions_lookup
            ON will_phase_satisfactions(agent_instance, scope_kind, relation_id, cycle_id, phase, status)
        """)
        self.conn.execute("""
            UPDATE will_phase_satisfactions SET status = 'invalidated',
                result_code = 'legacy_evidence_unverified'
            WHERE evidence_version = 0 AND status = 'available'
        """)
        self.conn.commit()


class WillPhaseArbitration:
    def __init__(self, db_manager):
        self.db = db_manager
        initializer = getattr(db_manager, "_init_will_phase_arbitration_schema", None)
        if callable(initializer):
            initializer()
        else:
            WillPhaseArbitrationDatabaseMixin._init_will_phase_arbitration_schema(db_manager)

    @staticmethod
    def _now():
        return datetime.utcnow()

    def _validated_expression(self, conn, expression_id):
        row = conn.execute("SELECT * FROM will_expressions WHERE id = ?", (expression_id,)).fetchone()
        if row is None:
            return None
        expression = dict(row)
        if (expression["status"] != "completed" or not expression.get("pressure_effect_at")
                or expression.get("scope_kind") != "global" or expression.get("relation_id") is not None):
            return None
        event = conn.execute("SELECT * FROM agent_will_pulse_events WHERE id = ?",
                             (expression.get("delivery_event_id"),)).fetchone()
        if (event is None or event["status"] != "completed"
                or any(dict(event).get(key) != expression[key] for key in SCOPE_FIELDS)
                or event["winning_will"] != expression["will_name"]):
            return None
        receipt = conn.execute("""
            SELECT * FROM will_expression_receipts
            WHERE expression_id = ? AND status = 'completed' AND result_code = 'delivery_confirmed'
            ORDER BY id DESC LIMIT 1
        """, (expression_id,)).fetchone()
        if receipt is None:
            return None
        confirmation = _load(receipt["evidence_json"])
        payload = _load(expression.get("prepared_payload_json"))
        ids = confirmation.get("message_ids")
        if (confirmation.get("transport") != "telegram" or not isinstance(ids, list) or not ids
                or any(not isinstance(value, (str, int)) or isinstance(value, bool) or not str(value) for value in ids)
                or confirmation.get("chat_id") is None
                or str(confirmation["chat_id"]) != str(payload.get("platform_id"))):
            return None
        proof = conn.execute("""
            SELECT * FROM will_expression_receipts
            WHERE expression_id = ? AND status = 'capability_completed' AND result_code = 'phase_evidence_v1'
            ORDER BY id DESC LIMIT 1
        """, (expression_id,)).fetchone()
        if proof is None:
            return None
        evidence = _load(proof["evidence_json"])
        if evidence.get("scope") != {key: expression[key] for key in SCOPE_FIELDS}:
            return None
        result = validate_evidence(evidence.get("result") or {}, expression["capability_key"], self._now())
        if result is None:
            return None
        if (CAPABILITY_PHASE.get(expression["capability_key"]) != result["phase"]
                or expression["will_name"] != "saber"):
            return None
        return expression, proof, result

    def record_expression_completion(self, expression: Dict[str, Any], *, validity_hours=24.0):
        if not expression or not isinstance(expression.get("id"), int):
            return None
        if not math.isfinite(float(validity_hours)) or validity_hours <= 0:
            return None
        with delivery_connection(self.db) as conn, atomic(conn):
            validated = self._validated_expression(conn, expression["id"])
            if validated is None:
                return None
            stored, proof, result = validated
            expires = result["captured_at"] + timedelta(hours=min(24.0, validity_hours))
            if expires <= utc_time(self._now()):
                return None
            evidence = {"source_receipt_id": proof["id"],
                        "source_digest": hashlib.sha256(proof["evidence_json"].encode()).hexdigest()}
            conn.execute("""
                INSERT OR IGNORE INTO will_phase_satisfactions (
                    agent_instance, relation_id, scope_kind, cycle_id, phase, expression_id,
                    will_name, capability_key, quality, source_ref, result_code,
                    evidence_json, valid_until, evidence_version, user_id
                ) VALUES (?, NULL, 'global', ?, ?, ?, ?, ?, ?, ?, 'equivalent_world_snapshot', ?, ?, 1, ?)
            """, (stored["agent_instance"], stored["cycle_id"], result["phase"], stored["id"],
                  stored["will_name"], stored["capability_key"], result["quality"],
                  f"will_expression_receipt#{proof['id']}", _dump(evidence), expires.isoformat(), stored["user_id"]))
            return _row(conn.execute("SELECT * FROM will_phase_satisfactions WHERE expression_id = ?",
                                     (stored["id"],)).fetchone())

    def _eligible(self, conn, receipt):
        expiry = utc_time(receipt.get("valid_until"))
        if (receipt.get("evidence_version") != 1 or not expiry or expiry <= utc_time(self._now())
                or receipt.get("scope_kind") != "global" or receipt.get("relation_id") is not None):
            return None
        validated = self._validated_expression(conn, receipt["expression_id"])
        if not validated:
            return None
        expression, proof, result = validated
        evidence = receipt["evidence"]
        if (evidence.get("source_receipt_id") != proof["id"]
                or evidence.get("source_digest") != hashlib.sha256(proof["evidence_json"].encode()).hexdigest()
                or receipt["quality"] != result["quality"]
                or any(receipt[key] != expression[key] for key in ("agent_instance", "user_id", "cycle_id", "will_name", "capability_key"))
                or receipt["phase"] != result["phase"]):
            return None
        return result

    def claim_for_phase(self, *, agent_instance, cycle_id, phase, phase_pulse_id, user_id=None, execution_mode="automatic"):
        if execution_mode != "automatic" or phase not in SATISFIABLE_PHASES or not phase_pulse_id or not user_id:
            return None
        with delivery_connection(self.db) as conn, atomic(conn):
            pulse = conn.execute("SELECT * FROM consciousness_phase_pulses WHERE id = ?", (phase_pulse_id,)).fetchone()
            if (pulse is None or pulse["agent_instance"] != agent_instance or pulse["cycle_id"] != cycle_id
                    or pulse["phase"] != phase or pulse["status"] != "running"):
                return None
            scheduled = utc_time(pulse["scheduled_at"])
            if not scheduled or scheduled > utc_time(self._now()):
                return None
            rows = conn.execute("""
                SELECT * FROM will_phase_satisfactions
                WHERE agent_instance = ? AND cycle_id = ? AND phase = ? AND user_id = ?
                  AND evidence_version = 1 AND scope_kind = 'global' AND relation_id IS NULL
                  AND ((status = 'available' AND reserved_by_phase_pulse_id IS NULL)
                       OR (reserved_by_phase_pulse_id = ? AND status IN ('reserved', 'consumed')))
                ORDER BY (reserved_by_phase_pulse_id IS NOT NULL) DESC, id
            """, (agent_instance, cycle_id, phase, user_id, phase_pulse_id)).fetchall()
            for row in rows:
                receipt = _row(row)
                if receipt["status"] == "consumed":
                    stored = self._stored_result(conn, receipt)
                    conn.execute(
                        "UPDATE consciousness_phase_pulses SET status = 'completed', phase_result_id = ? WHERE id = ?",
                        (receipt["phase_result_id"], phase_pulse_id),
                    )
                    return {**receipt, "already_committed": True, "stored_result": stored}
                result = self._eligible(conn, receipt)
                if not result:
                    conn.execute("""
                        UPDATE will_phase_satisfactions SET status = 'invalidated', result_code = 'evidence_invalid_or_expired'
                        WHERE id = ?
                    """, (receipt["id"],))
                    continue
                if pulse["phase_result_id"] is not None:
                    return None
                conn.execute("""
                    UPDATE will_phase_satisfactions SET status = 'reserved',
                        reserved_by_phase_pulse_id = ?, reserved_at = COALESCE(reserved_at, ?), updated_at = ?
                    WHERE id = ?
                """, (phase_pulse_id, self._now().isoformat(), self._now().isoformat(), receipt["id"]))
                claimed = _row(conn.execute("SELECT * FROM will_phase_satisfactions WHERE id = ?", (receipt["id"],)).fetchone())
                claimed["result"] = result
                return claimed
            return None

    def recover_reservations(self, *, agent_instance, cycle_id, phase, lease_seconds=300):
        """Requeue interrupted reservations through the existing bounded retry policy."""
        now = utc_time(self._now())
        repaired = 0
        with delivery_connection(self.db) as conn, atomic(conn):
            rows = conn.execute("""
                SELECT p.id, p.updated_at, s.reserved_at FROM consciousness_phase_pulses p
                JOIN will_phase_satisfactions s ON s.reserved_by_phase_pulse_id = p.id
                WHERE p.agent_instance = ? AND p.cycle_id = ? AND p.phase = ?
                  AND s.agent_instance = p.agent_instance AND s.cycle_id = p.cycle_id AND s.phase = p.phase
                  AND s.status = 'reserved' AND s.evidence_version = 1
                  AND p.status = 'running' AND p.phase_result_id IS NULL
            """, (agent_instance, cycle_id, phase)).fetchall()
            for row in rows:
                timestamps = [utc_time(row["updated_at"]), utc_time(row["reserved_at"])]
                if any(value is None for value in timestamps) or (now - max(timestamps)).total_seconds() < lease_seconds:
                    continue
                conn.execute("""
                    UPDATE consciousness_phase_pulses SET status = 'failed',
                        executed_at = ?, updated_at = ?, last_error = 'will_phase_reservation_interrupted'
                    WHERE id = ? AND status = 'running' AND phase_result_id IS NULL
                """, (max(timestamps).isoformat(), now.isoformat(), row["id"]))
                repaired += 1
        return repaired

    @staticmethod
    def _stored_result(conn, receipt):
        row = conn.execute("SELECT * FROM consciousness_loop_phase_results WHERE id = ?",
                           (receipt["phase_result_id"],)).fetchone()
        if (row is None or row["status"] != "satisfied_by_will"
                or any(row[key] != receipt[key] for key in ("agent_instance", "cycle_id", "phase"))
                or _load(row["metrics_json"]).get("will_phase_satisfaction_id") != receipt["id"]
                or _load(row["metrics_json"]).get("pulse_id") != receipt["reserved_by_phase_pulse_id"]):
            raise ValueError("will_phase_committed_result_missing")
        result = dict(row)
        for field in ("artifacts_created", "warnings", "errors", "metrics", "raw_result"):
            result[field] = json.loads(result.pop(field + "_json"))
        result["execution_mode"] = "automatic"
        return result

    def commit_for_phase(self, receipt_id, *, phase_pulse_id, save_result):
        """Commit the phase result, pulse and receipt together, or none of them."""
        with delivery_connection(self.db) as conn, atomic(conn):
            receipt = _row(conn.execute("SELECT * FROM will_phase_satisfactions WHERE id = ?", (receipt_id,)).fetchone())
            if not receipt or receipt.get("reserved_by_phase_pulse_id") != phase_pulse_id:
                raise ValueError("will_phase_reservation_mismatch")
            pulse = conn.execute("SELECT * FROM consciousness_phase_pulses WHERE id = ?", (phase_pulse_id,)).fetchone()
            if (pulse is None or any(pulse[key] != receipt[key] for key in ("agent_instance", "cycle_id", "phase"))):
                raise ValueError("will_phase_pulse_mismatch")
            if receipt["status"] == "consumed" and receipt["phase_result_id"]:
                self._stored_result(conn, receipt)
                conn.execute("UPDATE consciousness_phase_pulses SET status = 'completed' WHERE id = ?", (phase_pulse_id,))
                return receipt["phase_result_id"], False
            if (receipt["status"] != "reserved" or pulse["status"] != "running"
                    or pulse["phase_result_id"] is not None or not self._eligible(conn, receipt)):
                raise ValueError("will_phase_evidence_no_longer_eligible")
            result_id = save_result(conn)
            row = conn.execute("SELECT * FROM consciousness_loop_phase_results WHERE id = ?", (result_id,)).fetchone()
            if (row is None or row["status"] != "satisfied_by_will"
                    or any(row[key] != receipt[key] for key in ("agent_instance", "cycle_id", "phase"))
                    or _load(row["metrics_json"]).get("pulse_id") != phase_pulse_id
                    or _load(row["metrics_json"]).get("will_phase_satisfaction_id") != receipt_id):
                raise ValueError("will_phase_result_mismatch")
            conn.execute("""
                UPDATE will_phase_satisfactions SET status = 'consumed', consumed_by_phase_pulse_id = ?,
                    consumed_at = ?, phase_result_id = ?, updated_at = ?, integration_version = 1 WHERE id = ?
            """, (phase_pulse_id, self._now().isoformat(), result_id, self._now().isoformat(), receipt_id))
            conn.execute("""
                UPDATE consciousness_phase_pulses SET status = 'completed', phase_result_id = ?,
                    executed_at = ?, updated_at = ?, last_error = NULL WHERE id = ?
            """, (result_id, row["completed_at"], self._now().isoformat(), phase_pulse_id))
            return result_id, True
