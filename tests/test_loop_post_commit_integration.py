"""Normal loop phases persist their local post-commit effects exactly once."""
from __future__ import annotations

import sqlite3

import pytest

from consciousness_loop import ConsciousnessLoopManager
from engines.loop_post_commit_integration import integrate, recover
from engines.working_memory import WorkingMemoryEngine
from test_loop_failure_policy import _LoopWorkingMemoryDB


def pending_result(manager, *, phase="work", cycle_id="2026-09-07"):
    result = manager._build_placeholder_result(cycle_id, manager._phase_window_for()["phase"], "pytest", "manual")
    result["phase"] = phase
    result["trigger_name"] = f"{phase}_phase"
    result["output_summary"] = "Resultado normal persistido para teste."
    manager._finalize_phase_result_timing(result)
    return manager._save_phase_result(result), result


def counts(db):
    return [db.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in (
        "working_memory_items", "working_memory_broadcasts", "consciousness_loop_events",
    )]


def test_normal_phase_integrates_once_and_records_queue(loop_db):
    db = _LoopWorkingMemoryDB(loop_db.conn)
    manager = ConsciousnessLoopManager(db)
    result_id, _ = pending_result(manager)
    first = integrate(manager, result_id)
    second = integrate(manager, result_id)
    assert first == second
    assert counts(db) == [1, 1, 1]
    queue = db.conn.execute("SELECT * FROM consciousness_loop_post_commit_effects WHERE phase_result_id = ?", (result_id,)).fetchone()
    assert queue["integration_at"]
    assert first["raw_result"]["working_memory_broadcast"]["to_phase"] == "hobby"


@pytest.mark.parametrize("table,operation", [
    ("working_memory_items", "INSERT"), ("working_memory_broadcasts", "INSERT"),
    ("consciousness_loop_events", "INSERT"), ("consciousness_loop_phase_results", "UPDATE"),
    ("consciousness_loop_post_commit_effects", "UPDATE"),
])
def test_write_failure_rolls_back_normal_post_commit_effects(loop_db, table, operation):
    db = _LoopWorkingMemoryDB(loop_db.conn)
    manager = ConsciousnessLoopManager(db)
    result_id, _ = pending_result(manager)
    db.conn.execute(f"""CREATE TRIGGER reject_normal_post_commit BEFORE {operation} ON {table}
        BEGIN SELECT RAISE(ABORT, 'private-sentinel'); END""")
    db.conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        integrate(manager, result_id)
    assert counts(db) == [0, 0, 0]
    assert db.conn.execute("SELECT integration_at FROM consciousness_loop_post_commit_effects WHERE phase_result_id = ?", (result_id,)).fetchone()[0] is None


def test_recovery_does_not_run_phase_again(loop_db, monkeypatch):
    db = _LoopWorkingMemoryDB(loop_db.conn)
    manager = ConsciousnessLoopManager(db)
    result_id, _ = pending_result(manager)
    db.conn.execute("""CREATE TRIGGER reject_normal_broadcast BEFORE INSERT ON working_memory_broadcasts
        BEGIN SELECT RAISE(ABORT, 'private-sentinel'); END""")
    db.conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        integrate(manager, result_id)
    db.conn.execute("DROP TRIGGER reject_normal_broadcast")
    db.conn.commit()
    monkeypatch.setattr(manager, "_run_work_phase", lambda _: pytest.fail("phase must not run again"))
    assert recover(manager) == {"recovered": 1, "deferred": 0}
    assert counts(db) == [1, 1, 1]


def test_execute_phase_uses_post_commit_queue(loop_db, monkeypatch):
    db = _LoopWorkingMemoryDB(loop_db.conn)
    manager = ConsciousnessLoopManager(db)
    monkeypatch.setattr(manager, "_run_work_phase", lambda result: result)
    result = manager.execute_phase("work", "2026-09-07", trigger_source="pytest", execution_mode="manual")
    queue = db.conn.execute("SELECT * FROM consciousness_loop_post_commit_effects").fetchone()
    assert result["metrics"]["working_memory_item_id"]
    assert queue["integration_at"]
    assert counts(db) == [1, 1, 1]
