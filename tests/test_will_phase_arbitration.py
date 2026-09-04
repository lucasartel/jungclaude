"""Tests for one-use WILL satisfaction of circadian phases."""
from __future__ import annotations

import sqlite3
from argparse import Namespace

from engines.will_expression import WillExpressionDatabaseMixin, WillExpressionEngine
from engines.will_phase_arbitration import WillPhaseArbitration, WillPhaseArbitrationDatabaseMixin
from scripts.remote_db_probe import query_phase_satisfaction


class ArbitrationDB(WillExpressionDatabaseMixin, WillPhaseArbitrationDatabaseMixin):
    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.agent_instance = "test-arbitration"


def _completed_expression(db: ArbitrationDB, *, will_name: str = "saber") -> dict:
    expression_engine = WillExpressionEngine(db)
    capability = "saber_world_refresh" if will_name == "saber" else "expressar_visual_artifact"
    prepared = expression_engine.prepare(
        user_id="admin",
        cycle_id="2026-09-04",
        will_name=will_name,
        prepare_capability=lambda _capability: {
            "success": True,
            "pending_delivery": {"delivery_type": "test", "text": "delivery"},
        },
    )
    expression = expression_engine.finalize_delivery(
        prepared["expression"]["id"],
        success=True,
        summary="delivery confirmed",
    )
    assert expression is not None
    assert expression["capability_key"] == capability
    return expression


def test_confirmed_expression_becomes_one_use_phase_receipt() -> None:
    db = ArbitrationDB()
    expression = _completed_expression(db)
    arbitration = WillPhaseArbitration(db)

    receipt = arbitration.record_expression_completion(expression)
    claimed = arbitration.claim_for_phase(
        agent_instance="test-arbitration",
        cycle_id="2026-09-04",
        phase="world",
        phase_pulse_id=17,
    )
    repeated = arbitration.claim_for_phase(
        agent_instance="test-arbitration",
        cycle_id="2026-09-04",
        phase="world",
        phase_pulse_id=18,
    )

    assert receipt["phase"] == "world"
    assert receipt["status"] == "available"
    assert claimed["status"] == "consumed"
    assert claimed["consumed_by_phase_pulse_id"] == 17
    assert repeated is None


def test_protected_phases_cannot_be_satisfied_by_will() -> None:
    db = ArbitrationDB()
    arbitration = WillPhaseArbitration(db)
    expression = {
        "id": 99,
        "agent_instance": "test-arbitration",
        "relation_id": None,
        "scope_kind": "global",
        "cycle_id": "2026-09-04",
        "will_name": "expressar",
        "capability_key": "expressar_visual_artifact",
        "status": "completed",
    }

    receipt = arbitration.record_expression_completion(expression)
    claimed = arbitration.claim_for_phase(
        agent_instance="test-arbitration",
        cycle_id="2026-09-04",
        phase="identity",
        phase_pulse_id=21,
    )

    assert receipt["phase"] == "hobby"
    assert claimed is None
    row = db.conn.execute(
        "SELECT status, relation_id, scope_kind FROM will_phase_satisfactions"
    ).fetchone()
    assert tuple(row) == ("available", None, "global")


def test_failed_expression_does_not_create_phase_satisfaction() -> None:
    db = ArbitrationDB()
    expression_engine = WillExpressionEngine(db)
    result = expression_engine.prepare(
        user_id="admin",
        cycle_id="2026-09-04",
        will_name="saber",
        prepare_capability=lambda _capability: {
            "success": False,
            "action_summary": "world unavailable",
        },
    )

    assert result["status"] == "failed"
    assert WillPhaseArbitration(db).record_expression_completion(result.get("expression")) is None
    assert db.conn.execute("SELECT COUNT(*) FROM will_phase_satisfactions").fetchone()[0] == 0


def test_satisfaction_probe_reports_consumption_metadata_only() -> None:
    db = ArbitrationDB()
    expression = _completed_expression(db)
    arbitration = WillPhaseArbitration(db)
    arbitration.record_expression_completion(expression)
    arbitration.claim_for_phase(
        agent_instance="test-arbitration",
        cycle_id="2026-09-04",
        phase="world",
        phase_pulse_id=31,
    )

    payload = query_phase_satisfaction(
        db.conn.cursor(),
        Namespace(
            user_id="admin",
            agent_instance="test-arbitration",
            relation_id=None,
            scope_kind="global",
            limit=5,
        ),
    )

    row = payload["rows"][0]
    assert row["status"] == "consumed"
    assert row["consumed_by_phase_pulse_id"] == 31
    assert "evidence_json" not in row
