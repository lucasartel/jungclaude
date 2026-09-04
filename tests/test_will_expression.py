"""Tests for the persistent WILL expression contract."""
from __future__ import annotations

import sqlite3
from argparse import Namespace

from engines.will_expression import WillExpressionDatabaseMixin, WillExpressionEngine
from scripts.remote_db_probe import query_expressions


class ExpressionDB(WillExpressionDatabaseMixin):
    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.agent_instance = "test-expression"


def _engine() -> WillExpressionEngine:
    return WillExpressionEngine(ExpressionDB())


def test_expression_is_idempotent_and_claimed_once() -> None:
    engine = _engine()
    calls = []

    def prepare(_capability: str):
        calls.append(_capability)
        return {
            "success": True,
            "action_summary": "Entrega preparada.",
            "pending_delivery": {"delivery_type": "test", "text": "mensagem"},
        }

    first = engine.prepare(
        user_id="user-a",
        cycle_id="2026-09-04",
        will_name="relacionar",
        proactive_system=object(),
        prepare_capability=prepare,
    )
    second = engine.prepare(
        user_id="user-a",
        cycle_id="2026-09-04",
        will_name="relacionar",
        proactive_system=object(),
        prepare_capability=prepare,
    )

    assert first["status"] == "prepared"
    assert first["pending_delivery"]["will_expression_id"] == first["expression"]["id"]
    assert second["status"] == "delivery_in_progress"
    assert calls == ["relacionar_proactive_message"]

    receipts = engine.db.conn.execute(
        "SELECT status, result_code FROM will_expression_receipts ORDER BY id"
    ).fetchall()
    assert [tuple(row) for row in receipts] == [
        ("prepared", "delivery_prepared"),
        ("delivering", "delivery_claimed"),
    ]


def test_blocked_capability_does_not_prepare_or_discharge() -> None:
    engine = _engine()
    called = []

    result = engine.prepare(
        user_id="user-a",
        cycle_id="2026-09-04",
        will_name="relacionar",
        proactive_system=None,
        prepare_capability=lambda _capability: called.append(True),
    )

    assert result["status"] == "blocked"
    assert called == []
    expression = result["expression"]
    assert expression["status"] == "blocked"
    receipt = engine.db.conn.execute(
        "SELECT status, result_code FROM will_expression_receipts"
    ).fetchone()
    assert tuple(receipt) == ("blocked", "proactive_executor_unavailable")


def test_delivery_receipt_is_terminal_and_keeps_evidence() -> None:
    engine = _engine()
    prepared = engine.prepare(
        user_id="user-a",
        cycle_id="2026-09-04",
        will_name="saber",
        prepare_capability=lambda _capability: {
            "success": True,
            "pending_delivery": {"delivery_type": "test", "text": "resumo"},
        },
    )
    expression_id = prepared["expression"]["id"]

    completed = engine.finalize_delivery(
        expression_id,
        success=True,
        summary="Canal confirmou a entrega.",
        evidence={"transport": "test", "message_id": "m-1"},
    )
    repeated = engine.finalize_delivery(
        expression_id,
        success=False,
        summary="Tentativa repetida.",
    )

    assert completed["status"] == "completed"
    assert repeated["status"] == "completed"
    receipts = engine.db.conn.execute(
        "SELECT status, result_code FROM will_expression_receipts ORDER BY id"
    ).fetchall()
    assert [tuple(row) for row in receipts] == [
        ("prepared", "delivery_prepared"),
        ("delivering", "delivery_claimed"),
        ("completed", "delivery_confirmed"),
    ]


def test_expression_probe_exposes_lifecycle_without_delivery_payload() -> None:
    engine = _engine()
    engine.prepare(
        user_id="user-a",
        cycle_id="2026-09-04",
        will_name="saber",
        intent={"objective": "investigar", "private_note": "nao expor"},
        prepare_capability=lambda _capability: {
            "success": True,
            "pending_delivery": {"delivery_type": "test", "text": "conteudo privado"},
        },
    )

    payload = query_expressions(
        engine.db.conn.cursor(),
        Namespace(
            user_id="user-a",
            agent_instance="test-expression",
            relation_id=None,
            scope_kind="global",
            limit=5,
        ),
    )

    row = payload["rows"][0]
    assert payload["available"] is True
    assert row["status"] == "delivering"
    assert row["intent"]["objective"] == "investigar"
    assert "private_note" not in row["intent"]
    assert "prepared_payload" not in row
    assert "conteudo privado" not in str(payload)
