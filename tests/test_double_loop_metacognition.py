from __future__ import annotations

import sys
import types

openai_stub = types.ModuleType("openai")
openai_stub.OpenAI = object
if not hasattr(sys.modules.get("openai"), "OpenAI"):
    sys.modules["openai"] = openai_stub

import json
import sqlite3
import pytest
from datetime import datetime, timedelta, timezone

from core.database import HybridDatabaseManager
from engines.meta_cognition import DoubleLoopMetaCognitionEngine


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_meta_cognition.db"
    db = HybridDatabaseManager.__new__(HybridDatabaseManager)
    db.conn = sqlite3.connect(str(db_file), check_same_thread=False)
    db.conn.row_factory = sqlite3.Row
    db._lock = HybridDatabaseManager._lock_cls() if hasattr(HybridDatabaseManager, "_lock_cls") else pytest.importorskip("threading").Lock()
    db.agent_instance = "test_jung"
    db._init_sqlite_schema()
    return db


def test_meta_cognition_schema_and_save(test_db):
    eval_id = test_db.save_meta_cognition_evaluation(
        agent_instance="test_jung",
        cycle_id="2026-08-13",
        resonance_score=0.85,
        coherence_score=0.92,
        biases_detected=[{"bias_type": "high_tension_accumulation", "severity": "medium"}],
        heuristic_adjustments=[{"parameter": "rumination_synthesis_bias", "adjustment_delta": 0.05}],
        recommendations=["Clear tension backlog."],
        summary="Test double-loop evaluation summary.",
    )
    assert eval_id > 0

    latest = test_db.get_latest_meta_cognition_evaluation(agent_instance="test_jung")
    assert latest is not None
    assert latest["cycle_id"] == "2026-08-13"
    assert latest["resonance_score"] == 0.85
    assert len(latest["biases_detected"]) == 1
    assert latest["biases_detected"][0]["bias_type"] == "high_tension_accumulation"
    assert len(latest["heuristic_adjustments"]) == 1
    assert latest["heuristic_adjustments"][0]["adjustment_delta"] == 0.05


def test_meta_cognition_cooldown(test_db):
    engine = DoubleLoopMetaCognitionEngine(test_db, agent_instance="test_jung")

    res1 = engine.run_double_loop_evaluation(
        user_id="u_test",
        cycle_id="2026-08-13",
        force=False,
    )
    assert res1["status"] == "success"
    assert res1["eval_id"] > 0

    assert test_db.is_meta_cognition_cooldown_active(agent_instance="test_jung", cooldown_hours=24) is True

    res2 = engine.run_double_loop_evaluation(
        user_id="u_test",
        cycle_id="2026-08-13",
        force=False,
    )
    assert res2["status"] == "skipped"
    assert res2["reason"] == "cooldown_active"

    res_forced = engine.run_double_loop_evaluation(
        user_id="u_test",
        cycle_id="2026-08-13",
        force=True,
    )
    assert res_forced["status"] == "success"


def test_heuristic_adjustment_bounds(test_db):
    engine = DoubleLoopMetaCognitionEngine(test_db, agent_instance="test_jung")
    res = engine.run_double_loop_evaluation(
        user_id="u_test",
        cycle_id="2026-08-13",
        force=True,
    )
    for adj in res.get("heuristic_adjustments", []):
        delta = abs(adj.get("adjustment_delta", 0.0))
        assert delta <= 0.05
