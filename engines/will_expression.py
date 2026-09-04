"""Persistent contract between a WILL overflow and a concrete capability."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from engines.will_scope import GLOBAL_SCOPE, scope_context


CAPABILITIES: Dict[str, Dict[str, str]] = {
    "saber_world_refresh": {
        "will_name": "saber",
        "gate_level": "admin_communicate",
        "cost_class": "world_refresh",
    },
    "expressar_visual_artifact": {
        "will_name": "expressar",
        "gate_level": "admin_communicate",
        "cost_class": "paid_image_generation",
    },
    "relacionar_proactive_message": {
        "will_name": "relacionar",
        "gate_level": "admin_communicate",
        "cost_class": "proactive_message",
    },
}
CAPABILITY_BY_WILL = {item["will_name"]: key for key, item in CAPABILITIES.items()}


def _dump(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=False, default=str)


def _load(value: Any, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback


def _row(row: Any) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    result = dict(row)
    result["intent"] = _load(result.pop("intent_json", None), {})
    result["prepared_payload"] = _load(result.pop("prepared_payload_json", None), {})
    return result


class WillExpressionDatabaseMixin:
    """Creates additive audit tables for WILL expressions and receipts."""

    def _init_will_expression_schema(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS will_expressions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_instance TEXT NOT NULL,
                relation_id TEXT,
                scope_kind TEXT NOT NULL DEFAULT 'global',
                user_id TEXT NOT NULL,
                cycle_id TEXT NOT NULL,
                will_name TEXT NOT NULL,
                capability_key TEXT NOT NULL,
                gate_level TEXT NOT NULL,
                cost_class TEXT NOT NULL,
                idempotency_key TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'planned',
                reason TEXT,
                intent_json TEXT NOT NULL DEFAULT '{}',
                prepared_payload_json TEXT NOT NULL DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS will_expression_receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expression_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                result_code TEXT,
                summary TEXT,
                evidence_json TEXT NOT NULL DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (expression_id) REFERENCES will_expressions(id)
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_will_expressions_scope ON will_expressions(agent_instance, scope_kind, relation_id, updated_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_will_expression_receipts_expression ON will_expression_receipts(expression_id, created_at DESC)")
        self.conn.commit()


class WillExpressionEngine:
    """Plans, prepares, and receipts an overflow without discharging pressure."""

    def __init__(self, db_manager: Any):
        self.db = db_manager
        initializer = getattr(db_manager, "_init_will_expression_schema", None)
        if callable(initializer):
            initializer()
        else:
            WillExpressionDatabaseMixin._init_will_expression_schema(db_manager)

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().isoformat()

    def _fetch(self, expression_id: int) -> Optional[Dict[str, Any]]:
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM will_expressions WHERE id = ?", (int(expression_id),))
        return _row(cursor.fetchone())

    def _fetch_key(self, key: str) -> Optional[Dict[str, Any]]:
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM will_expressions WHERE idempotency_key = ?", (key,))
        return _row(cursor.fetchone())

    def _receipt(self, expression_id: int, status: str, code: str, summary: str, evidence: Optional[Dict[str, Any]] = None) -> None:
        self.db.conn.execute(
            "INSERT INTO will_expression_receipts (expression_id, status, result_code, summary, evidence_json) VALUES (?, ?, ?, ?, ?)",
            (int(expression_id), status, code, summary[:500], _dump(evidence)),
        )
        self.db.conn.commit()

    def _set_status(self, expression_id: int, status: str, reason: Optional[str], payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        columns = ["status = ?", "reason = ?", "updated_at = ?"]
        values: list[Any] = [status, reason, self._now()]
        if payload is not None:
            columns.append("prepared_payload_json = ?")
            values.append(_dump(payload))
        values.append(int(expression_id))
        self.db.conn.execute(f"UPDATE will_expressions SET {', '.join(columns)} WHERE id = ?", tuple(values))
        self.db.conn.commit()
        return self._fetch(expression_id) or {}

    @staticmethod
    def _availability(capability_key: str, proactive_system: Any) -> tuple[bool, Optional[str]]:
        if capability_key == "expressar_visual_artifact":
            from instance_config import IMAGE_GENERATION_ENABLED
            if not IMAGE_GENERATION_ENABLED:
                return False, "image_generation_disabled"
        if capability_key == "relacionar_proactive_message" and proactive_system is None:
            return False, "proactive_executor_unavailable"
        return True, None

    @staticmethod
    def _key(scope: Dict[str, Optional[str]], user_id: str, cycle_id: str, will_name: str, capability_key: str) -> str:
        return ":".join((
            str(scope.get("agent_instance") or "jung_v1"),
            str(scope.get("scope_kind") or GLOBAL_SCOPE),
            str(scope.get("relation_id") or "global"),
            str(user_id), str(cycle_id), will_name, capability_key,
        ))

    def _create(self, scope: Dict[str, Optional[str]], user_id: str, cycle_id: str, will_name: str, capability_key: str, key: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        capability = CAPABILITIES[capability_key]
        try:
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                INSERT INTO will_expressions (
                    agent_instance, relation_id, scope_kind, user_id, cycle_id, will_name,
                    capability_key, gate_level, cost_class, idempotency_key, status,
                    intent_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'planned', ?, ?, ?)
                """,
                (scope["agent_instance"], scope.get("relation_id"), scope["scope_kind"], user_id, cycle_id, will_name, capability_key, capability["gate_level"], capability["cost_class"], key, _dump(intent), self._now(), self._now()),
            )
            self.db.conn.commit()
            return self._fetch(cursor.lastrowid) or {}
        except sqlite3.IntegrityError:
            existing = self._fetch_key(key)
            if existing:
                return existing
            raise

    def _prepared(self, expression: Dict[str, Any], reused: bool = False) -> Dict[str, Any]:
        delivery = dict(expression.get("prepared_payload") or {})
        if not delivery:
            return {"status": "failed", "expression": expression, "action_summary": "Expressao preparada sem entrega recuperavel."}
        delivery["will_expression_id"] = expression["id"]
        delivery["will_scope"] = {name: expression.get(name) for name in ("agent_instance", "relation_id", "scope_kind")}
        return {"status": "prepared", "success": True, "expression": expression, "pending_delivery": delivery, "action_summary": expression.get("reason") or "Expressao preparada para entrega.", "reused": reused}

    def _claim_delivery(self, expression: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Claim a prepared expression so a retry cannot duplicate delivery."""
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            UPDATE will_expressions
            SET status = 'delivering', updated_at = ?
            WHERE id = ? AND status = 'prepared'
            """,
            (self._now(), int(expression["id"])),
        )
        if cursor.rowcount != 1:
            return None
        self.db.conn.commit()
        self._receipt(
            expression["id"],
            "delivering",
            "delivery_claimed",
            "Expressao reivindicada para uma unica tentativa de entrega.",
        )
        return self._fetch(expression["id"])

    def prepare(self, *, user_id: str, cycle_id: str, will_name: str, scope: Optional[Dict[str, Optional[str]]] = None, intent: Optional[Dict[str, Any]] = None, proactive_system: Any = None, prepare_capability: Callable[[str], Dict[str, Any]]) -> Dict[str, Any]:
        capability_key = CAPABILITY_BY_WILL.get(will_name)
        if not capability_key:
            return {"status": "blocked", "action_summary": f"Vontade sem capacidade registrada: {will_name}."}
        resolved_scope = scope or scope_context(self.db)
        key = self._key(resolved_scope, user_id, cycle_id, will_name, capability_key)
        expression = self._fetch_key(key)
        if expression:
            if expression.get("status") == "prepared":
                claimed = self._claim_delivery(expression)
                if claimed:
                    return self._prepared(claimed, reused=True)
            if expression.get("status") == "delivering":
                return {
                    "status": "delivery_in_progress",
                    "success": False,
                    "expression": expression,
                    "action_summary": "Expressao ja esta em tentativa de entrega; nenhuma duplicacao sera criada.",
                    "reused": True,
                }
            return {"status": expression.get("status") or "blocked", "expression": expression, "action_summary": expression.get("reason") or "Expressao ja registrada neste ciclo.", "reused": True}

        expression = self._create(resolved_scope, user_id, cycle_id, will_name, capability_key, key, {"will_name": will_name, "capability_key": capability_key, "scope_kind": resolved_scope.get("scope_kind"), **(intent or {})})
        available, reason = self._availability(capability_key, proactive_system)
        if not available:
            expression = self._set_status(expression["id"], "blocked", reason)
            self._receipt(expression["id"], "blocked", reason or "capability_unavailable", "Capacidade indisponivel; nenhuma descarga de pressao foi aplicada.", {"capability_key": capability_key})
            return {"status": "blocked", "expression": expression, "action_summary": reason}

        try:
            prepared = prepare_capability(capability_key) or {}
        except Exception as exc:
            expression = self._set_status(expression["id"], "failed", f"executor_error:{exc}")
            self._receipt(expression["id"], "failed", "executor_error", "A capacidade encontrou um erro inesperado antes da entrega.", {"capability_key": capability_key})
            return {"status": "failed", "expression": expression, "action_summary": expression.get("reason")}
        delivery = prepared.get("pending_delivery")
        if not prepared.get("success") or not delivery:
            reason = prepared.get("action_summary") or "capability_did_not_prepare_delivery"
            expression = self._set_status(expression["id"], "failed", reason)
            self._receipt(expression["id"], "failed", "delivery_not_prepared", "A capacidade nao produziu uma entrega valida; nenhuma descarga foi aplicada.", {"capability_key": capability_key})
            return {"status": "failed", "expression": expression, "action_summary": reason, "payload": prepared.get("payload")}

        expression = self._set_status(expression["id"], "prepared", prepared.get("action_summary") or "Expressao preparada para entrega.", delivery)
        self._receipt(expression["id"], "prepared", "delivery_prepared", "Expressao preparada; aguarda confirmacao do canal.", {"capability_key": capability_key, "gate_level": expression.get("gate_level")})
        claimed = self._claim_delivery(expression)
        if not claimed:
            return {
                "status": "delivery_in_progress",
                "success": False,
                "expression": expression,
                "action_summary": "Expressao nao pode ser reivindicada para entrega.",
            }
        result = self._prepared(claimed)
        result["payload"] = prepared.get("payload")
        return result

    def finalize_delivery(self, expression_id: int, *, success: bool, summary: str, evidence: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        expression = self._fetch(expression_id)
        if not expression:
            return None
        if expression.get("status") in {"completed", "failed", "blocked"}:
            return expression
        status, code = ("completed", "delivery_confirmed") if success else ("failed", "delivery_failed")
        expression = self._set_status(expression_id, status, summary)
        self._receipt(expression_id, status, code, summary, evidence)
        return expression
