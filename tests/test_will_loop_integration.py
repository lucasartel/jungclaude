"""Offline post-commit recovery through real WM domain operations and SQLite."""
from __future__ import annotations

import copy
import json
import sqlite3
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from types import SimpleNamespace

import pytest

from engines.will_loop_integration import integrate, recover
from engines.will_phase_arbitration import WillPhaseArbitration
from engines.will_recovery import utc_time
from scripts.remote_db_probe import query_phase_satisfaction
from test_will_phase_arbitration import CYCLE, claim, completed, context, pulse, save_callback


@pytest.fixture
def pending(context):
    completed(context)
    p = pulse(context)
    receipt = claim(context, p)
    result_id, _ = WillPhaseArbitration(context.db).commit_for_phase(
        receipt["id"], phase_pulse_id=p["id"], save_result=save_callback(context, p, receipt),
    )
    memory = context.db.working_memory_transaction(context.db.conn)
    memory._init_working_memory_schema()
    context.db.conn.commit()
    context.receipt_id = receipt["id"]
    context.result_id = result_id
    context.pulse_id = p["id"]
    return context


def counts(ctx):
    return [ctx.db.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in (
        "working_memory_items", "working_memory_broadcasts", "consciousness_loop_events",
    )]


def stored(ctx):
    return dict(ctx.db.conn.execute("SELECT * FROM will_phase_satisfactions WHERE id = ?", (ctx.receipt_id,)).fetchone())


def test_integrates_once_with_scoped_source_and_audit(pending):
    result = integrate(pending.manager, pending.receipt_id)
    assert counts(pending) == [1, 1, 1]
    assert stored(pending)["integration_at"]
    item = pending.db.conn.execute("SELECT * FROM working_memory_items").fetchone()
    assert json.loads(item["source_refs_json"]) == [f"loop#{pending.result_id}"]
    assert item["agent_instance"] == pending.manager.agent_instance
    assert result["raw_result"]["working_memory_broadcast"]["to_phase"] == "work"
    assert result["metrics"]["will_loop_event_id"]
    replay = integrate(pending.manager, pending.receipt_id)
    assert replay == result
    assert counts(pending) == [1, 1, 1]


@pytest.mark.parametrize("table,operation", [
    ("working_memory_items", "INSERT"), ("working_memory_broadcasts", "INSERT"),
    ("consciousness_loop_events", "INSERT"), ("consciousness_loop_phase_results", "UPDATE"),
    ("will_phase_satisfactions", "UPDATE"),
])
def test_failure_at_any_write_rolls_back_all_effects(pending, table, operation):
    pending.db.conn.execute(f"""CREATE TRIGGER reject_integration BEFORE {operation} ON {table}
        BEGIN SELECT RAISE(ABORT, 'private-error-sentinel'); END""")
    pending.db.conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        integrate(pending.manager, pending.receipt_id)
    assert counts(pending) == [0, 0, 0]
    assert stored(pending)["integration_at"] is None
    assert stored(pending)["status"] == "consumed"
    assert pending.db.conn.execute("SELECT COUNT(*) FROM consciousness_loop_phase_results").fetchone()[0] == 1
    pending.db.conn.execute("DROP TRIGGER reject_integration")
    pending.db.conn.commit()
    integrate(pending.manager, pending.receipt_id)
    assert counts(pending) == [1, 1, 1]


def test_focus_eviction_is_also_rolled_back(pending):
    memory = pending.db.working_memory_transaction(pending.db.conn)
    for index in range(5):
        memory.create_working_memory_item(agent_instance=pending.manager.agent_instance, phase="world",
            title=f"existing {index}", summary="existing focus", source_refs=[f"loop#{900 + index}"],
            item_type="focus", priority=0.8)
    pending.db.conn.commit()
    pending.db.conn.execute("""CREATE TRIGGER reject_broadcast BEFORE INSERT ON working_memory_broadcasts
        BEGIN SELECT RAISE(ABORT, 'rollback'); END""")
    pending.db.conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        integrate(pending.manager, pending.receipt_id)
    assert pending.db.conn.execute("SELECT COUNT(*) FROM working_memory_items WHERE status='active'").fetchone()[0] == 5
    assert counts(pending) == [5, 0, 0]


def test_restart_recovers_without_reexecuting_phase(pending, tmp_path, monkeypatch):
    path = tmp_path / "loop.db"
    with sqlite3.connect(path) as target:
        pending.db.conn.backup(target)
    pending.db.conn.close()
    pending.db.conn = sqlite3.connect(path)
    pending.db.conn.row_factory = sqlite3.Row
    monkeypatch.setattr(pending.manager, "_run_world_phase", lambda _: pytest.fail("no provider replay"))
    assert recover(pending.manager) == {"recovered": 1, "deferred": 0}
    assert recover(pending.manager) == {"recovered": 0, "deferred": 0}
    assert counts(pending) == [1, 1, 1]


def test_scheduler_recovers_before_selecting_current_phase(pending, monkeypatch):
    def stop_after_recovery():
        raise RuntimeError("stop-before-normal-cycle")

    monkeypatch.setattr(pending.manager, "_phase_window_for", stop_after_recovery)
    with pytest.raises(RuntimeError, match="stop-before-normal-cycle"):
        pending.manager.sync_loop()
    assert counts(pending) == [1, 1, 1]


@pytest.mark.parametrize("field,value", [
    ("agent_instance", "other"), ("user_id", "other"), ("scope_kind", "relation"),
    ("relation_id", "private-relation"), ("status", "reserved"), ("evidence_version", 0),
])
def test_invalid_receipt_scope_or_state_cannot_touch_wm(pending, field, value):
    pending.db.conn.execute(f"UPDATE will_phase_satisfactions SET {field} = ?", (value,))
    pending.db.conn.commit()
    with pytest.raises(ValueError):
        integrate(pending.manager, pending.receipt_id)
    assert counts(pending) == [0, 0, 0]


def test_wrong_pulse_cannot_be_integrated(pending):
    pending.db.conn.execute("UPDATE consciousness_phase_pulses SET phase_result_id = 999")
    pending.db.conn.commit()
    with pytest.raises(ValueError, match="pulse_mismatch"):
        integrate(pending.manager, pending.receipt_id)
    assert counts(pending) == [0, 0, 0]


def test_corrupt_result_binding_cannot_be_integrated(pending):
    pending.db.conn.execute("UPDATE consciousness_loop_phase_results SET metrics_json = '{}'")
    pending.db.conn.commit()
    with pytest.raises(ValueError, match="committed_result_missing"):
        integrate(pending.manager, pending.receipt_id)
    assert counts(pending) == [0, 0, 0]


@pytest.mark.parametrize("hours", [-25, 1])
def test_stale_or_future_result_does_not_revive_focus(pending, hours):
    timestamp = utc_time(pending.manager._now()) + timedelta(hours=hours)
    pending.db.conn.execute("UPDATE consciousness_loop_phase_results SET completed_at = ?", (timestamp.isoformat(),))
    pending.db.conn.commit()
    assert recover(pending.manager)["deferred"] == 1
    assert counts(pending) == [0, 0, 0]
    assert stored(pending)["integration_error"] == "will_loop_stale_result_requires_review"


def test_legacy_consumption_is_not_blindly_replayed(pending):
    pending.db.conn.execute("UPDATE will_phase_satisfactions SET integration_version = 0")
    pending.db.conn.commit()
    assert recover(pending.manager)["deferred"] == 1
    assert stored(pending)["integration_error"] == "will_loop_legacy_effects_require_review"
    assert counts(pending) == [0, 0, 0]


def test_partial_existing_observation_is_not_duplicated(pending):
    memory = pending.db.working_memory_transaction(pending.db.conn)
    memory.create_working_memory_item(agent_instance=pending.manager.agent_instance, phase="world",
        title="legacy", summary="legacy", source_refs=[f"loop#{pending.result_id}"])
    pending.db.conn.commit()
    assert recover(pending.manager)["deferred"] == 1
    assert counts(pending) == [1, 0, 0]


def test_backoff_is_bounded_and_probe_contains_no_payload(pending, monkeypatch):
    pending.db.conn.execute("""CREATE TRIGGER reject_broadcast BEFORE INSERT ON working_memory_broadcasts
        BEGIN SELECT RAISE(ABORT, 'private-error-sentinel'); END""")
    pending.db.conn.commit()
    now = utc_time(pending.manager._now())
    for attempt in range(1, 6):
        monkeypatch.setattr(pending.manager, "_now", lambda: now)
        assert recover(pending.manager)["deferred"] == 1
        row = stored(pending)
        assert row["integration_attempts"] == attempt
        assert recover(pending.manager)["deferred"] == 0
        assert utc_time(row["integration_next_at"]) == now + timedelta(minutes=5 * 2 ** (attempt - 1))
        now = utc_time(row["integration_next_at"]) + timedelta(seconds=1)
    assert recover(pending.manager)["deferred"] == 0
    payload = query_phase_satisfaction(pending.db.conn.cursor(), Namespace(
        user_id=pending.manager.admin_user_id, agent_instance=pending.manager.agent_instance,
        scope_kind="global", relation_id=None, limit=5))
    assert payload["rows"][0]["integration_attempts"] == 5
    assert "private-error-sentinel" not in str(payload)
    assert "output_summary" not in str(payload)


def test_concurrent_integrations_commit_once(pending, tmp_path):
    path = tmp_path / "concurrent.db"
    with sqlite3.connect(path) as target:
        pending.db.conn.backup(target)

    def worker():
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        try:
            manager = copy.copy(pending.manager)
            manager.db = SimpleNamespace(conn=conn, working_memory_transaction=pending.db.working_memory_transaction)
            return integrate(manager, pending.receipt_id)
        finally:
            conn.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: worker(), range(2)))
    assert results[0] == results[1]
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM working_memory_items").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM working_memory_broadcasts").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM consciousness_loop_events").fetchone()[0] == 1
