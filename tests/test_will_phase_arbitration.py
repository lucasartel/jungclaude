"""Evidence, scope, reservation and atomic loop completion for WILL."""
from __future__ import annotations

import copy
import json
import sqlite3
from argparse import Namespace
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from conftest import _create_loop_schema
from consciousness_loop import ConsciousnessLoopManager, PHASE_BY_KEY
from engines.will_delivery_receipt import bind_event
from engines.will_phase_arbitration import WillPhaseArbitration
from engines.will_phase_evidence import validate_evidence, world_evidence
from scripts.remote_db_probe import query_phase_satisfaction
from test_will_relation_scope import ScopedWillDB, TEST_INSTANCE
from will_pressure import WillPressureEngine

USER = "phase-admin"
CYCLE = "2026-09-05"
AREAS = ["politica", "ciencia"]


def snapshot():
    return {
        "cache_timestamp": (datetime.utcnow() - timedelta(minutes=1)).isoformat(),
        "confidence_overall": 0.73, "stale_areas": [],
        "area_panels": {key: {"signal_count": 1} for key in AREAS},
        "signals": [{"area_key": key, "source_url": f"https://example.org/{key}"} for key in AREAS],
        "dominant_tensions": ["cooperacao e conflito"], "atmosphere": "incerteza",
        "work_seeds": ["investigar cooperacao"], "hobby_seeds": ["perspectivas"],
        "knowledge_findings": "resultado cognitivo real, nao apenas uma notificacao",
    }


@pytest.fixture
def context():
    db = ScopedWillDB()
    _create_loop_schema(db.conn)
    pressure = WillPressureEngine(db, threshold=51)
    pressure._refractory_hours = lambda: 6
    manager = ConsciousnessLoopManager(db)
    manager.agent_instance = TEST_INSTANCE
    manager.admin_user_id = USER
    yield SimpleNamespace(db=db, pressure=pressure, manager=manager)
    db.conn.close()


def completed(context, *, evidence=True):
    engine = context.pressure._expression_engine()
    state = context.pressure._get_or_create_state(USER, CYCLE)
    context.pressure._update_state(state["id"], saber_pressure=80)
    result = {"success": True, "pending_delivery": {"platform_id": 42, "cycle_id": CYCLE, "text": "area investigada"}}
    if evidence:
        result["phase_evidence"] = world_evidence(snapshot(), AREAS)
    prepared = engine.prepare(user_id=USER, cycle_id=CYCLE, will_name="saber",
                              prepare_capability=lambda _: result)
    event_id = context.pressure._register_event(
        USER, CYCLE, {"saber": 80, "relacionar": 0, "expressar": 0},
        "test", "saber", "test", "saber_release", "prepared", "triggered",
    )
    bind_event(context.db, prepared["expression"]["id"], event_id)
    context.pressure.finalize_pending_delivery(
        event_id, USER, CYCLE, "saber", True, "confirmed",
        expression_id=prepared["expression"]["id"],
        delivery_evidence={"transport": "telegram", "chat_id": 42, "message_ids": [123]},
    )
    return engine._fetch(prepared["expression"]["id"])


def pulse(context, index=1, phase="world"):
    conn = context.db.conn
    cursor = conn.execute("""
        INSERT INTO consciousness_phase_pulses
        (agent_instance, cycle_id, phase, pulse_index, pulse_count, scheduled_at, status)
        VALUES (?, ?, ?, ?, 3, ?, 'running')
    """, (TEST_INSTANCE, CYCLE, phase, index, datetime.utcnow().isoformat()))
    conn.commit()
    return dict(conn.execute("SELECT * FROM consciousness_phase_pulses WHERE id = ?", (cursor.lastrowid,)).fetchone())


def claim(context, p, **changes):
    args = dict(agent_instance=TEST_INSTANCE, user_id=USER, cycle_id=CYCLE, phase=p["phase"], phase_pulse_id=p["id"])
    args.update(changes)
    return WillPhaseArbitration(context.db).claim_for_phase(**args)


def save_callback(context, p, receipt):
    def save(conn):
        result = context.manager._build_placeholder_result(CYCLE, PHASE_BY_KEY[p["phase"]], "test", "automatic")
        result["status"] = "satisfied_by_will"
        result["output_summary"] = receipt["result"]["output_summary"]
        result["metrics"].update({"pulse_id": p["id"], "will_phase_satisfaction_id": receipt["id"]})
        context.manager._finalize_phase_result_timing(result)
        return context.manager._save_phase_result(result, connection=conn, commit=False)
    return save


def test_notification_without_work_evidence_never_satisfies(context):
    expression = completed(context, evidence=False)
    assert WillPhaseArbitration(context.db).record_expression_completion(expression) is None
    assert claim(context, pulse(context)) is None


def test_fabricated_completed_dictionary_is_not_evidence(context):
    context.pressure._expression_engine()
    assert WillPhaseArbitration(context.db).record_expression_completion({"id": 999, "status": "completed"}) is None


def test_quality_is_measured_and_reservation_is_not_consumption(context):
    completed(context)
    p = pulse(context)
    receipt = claim(context, p)
    assert receipt["quality"] == 0.73
    assert receipt["status"] == "reserved"
    assert receipt["consumed_at"] is None
    assert receipt["result"]["world_state"]["knowledge_findings"] == snapshot()["knowledge_findings"]
    assert claim(context, p)["id"] == receipt["id"]
    assert claim(context, pulse(context, index=2)) is None


@pytest.mark.parametrize("change", [
    {"agent_instance": "other"}, {"cycle_id": "other"}, {"phase": "hobby"},
    {"phase_pulse_id": 999}, {"user_id": "other"}, {"user_id": None},
    {"execution_mode": "manual"}, {"execution_mode": "dry_run"},
])
def test_wrong_pulse_owner_or_mode_cannot_claim(context, change):
    completed(context)
    assert claim(context, pulse(context), **change) is None


@pytest.mark.parametrize("phase", ["dream", "identity", "rumination_intro", "rumination_extro", "will", "work"])
def test_protected_or_unmapped_phases_execute_normally(context, phase):
    completed(context)
    assert claim(context, pulse(context, phase=phase)) is None


def test_private_relation_cannot_be_promoted_to_global(context):
    expression = completed(context)
    for table in ("will_expressions", "agent_will_pulse_events", "agent_will_pressure_state"):
        context.db.conn.execute(f"UPDATE {table} SET scope_kind='relation', relation_id='private-a'")
    context.db.conn.commit()
    # Even a caller presenting the old global dictionary cannot restore eligibility.
    assert WillPhaseArbitration(context.db).record_expression_completion(expression) is None
    assert claim(context, pulse(context)) is None


@pytest.mark.parametrize("mutation", [
    lambda e: e.update(confidence=float("nan")),
    lambda e: e.update(confidence=0.1),
    lambda e: e.update(confidence=True),
    lambda e: e.update(source_urls={"politica": ["https://["], "ciencia": ["https://example.org"]}),
    lambda e: e.update(loaded_areas=["politica"]),
    lambda e: e.update(source_urls={}),
    lambda e: e["world_state"].update(stale_areas=["ciencia"]),
    lambda e: e["world_state"].update(work_seeds="invalid"),
    lambda e: e.update(captured_at="invalid"),
    lambda e: e.update(captured_at=(datetime.utcnow() + timedelta(days=1)).isoformat()),
])
def test_incomplete_or_invalid_work_is_not_equivalent(mutation):
    evidence = world_evidence(snapshot(), AREAS)
    mutation(evidence)
    assert validate_evidence(evidence, "saber_world_refresh", datetime.utcnow()) is None


def test_hobby_needs_its_own_equivalence_adapter():
    assert validate_evidence(world_evidence(snapshot(), AREAS), "expressar_visual_artifact", datetime.utcnow()) is None


def test_malformed_evidence_is_ineligible_not_an_exception():
    assert validate_evidence(["not", "a", "snapshot"], "saber_world_refresh", datetime.utcnow()) is None


@pytest.mark.parametrize("change", ["delete_work", "change_work", "delete_delivery", "expire"])
def test_source_evidence_is_revalidated_at_claim(context, change):
    completed(context)
    conn = context.db.conn
    if change == "delete_work":
        conn.execute("DELETE FROM will_expression_receipts WHERE status='capability_completed'")
    elif change == "change_work":
        conn.execute("UPDATE will_expression_receipts SET evidence_json='{}' WHERE status='capability_completed'")
    elif change == "delete_delivery":
        conn.execute("DELETE FROM will_expression_receipts WHERE status='completed'")
    else:
        conn.execute("UPDATE will_phase_satisfactions SET valid_until='2000-01-01'")
    conn.commit()
    assert claim(context, pulse(context)) is None
    assert conn.execute("SELECT status FROM will_phase_satisfactions").fetchone()[0] == "invalidated"


def test_commit_is_atomic_and_replay_safe(context):
    completed(context)
    p = pulse(context)
    receipt = claim(context, p)
    arb = WillPhaseArbitration(context.db)
    result_id, created = arb.commit_for_phase(receipt["id"], phase_pulse_id=p["id"], save_result=save_callback(context, p, receipt))
    assert created
    repeated_id, created = arb.commit_for_phase(receipt["id"], phase_pulse_id=p["id"],
                                               save_result=lambda _: pytest.fail("must not save twice"))
    assert not created and repeated_id == result_id
    assert context.db.conn.execute("SELECT COUNT(*) FROM consciousness_loop_phase_results").fetchone()[0] == 1
    assert context.db.conn.execute("SELECT status FROM will_phase_satisfactions").fetchone()[0] == "consumed"
    assert context.db.conn.execute("SELECT phase_result_id FROM consciousness_phase_pulses").fetchone()[0] == result_id


def test_failed_save_rolls_back_and_reopens_reserved_work_after_restart(context, tmp_path):
    completed(context)
    p = pulse(context)
    receipt = claim(context, p)
    target = sqlite3.connect(tmp_path / "restart.db")
    context.db.conn.backup(target)
    target.close()
    context.db.conn.close()
    context.db.conn = sqlite3.connect(tmp_path / "restart.db")
    context.db.conn.row_factory = sqlite3.Row
    arb = WillPhaseArbitration(context.db)

    def failing(conn):
        save_callback(context, p, receipt)(conn)
        raise RuntimeError("crash before consumption")
    with pytest.raises(RuntimeError, match="crash"):
        arb.commit_for_phase(receipt["id"], phase_pulse_id=p["id"], save_result=failing)
    assert context.db.conn.execute("SELECT COUNT(*) FROM consciousness_loop_phase_results").fetchone()[0] == 0
    assert context.db.conn.execute("SELECT status FROM will_phase_satisfactions").fetchone()[0] == "reserved"
    context.db.conn.close()
    context.db.conn = sqlite3.connect(tmp_path / "restart.db")
    context.db.conn.row_factory = sqlite3.Row
    recovered = claim(context, p)
    assert recovered["id"] == receipt["id"]
    WillPhaseArbitration(context.db).commit_for_phase(receipt["id"], phase_pulse_id=p["id"],
                                                     save_result=save_callback(context, p, recovered))


def test_result_cannot_be_committed_to_another_pulse(context):
    completed(context)
    p = pulse(context)
    receipt = claim(context, p)
    with pytest.raises(ValueError, match="reservation_mismatch"):
        WillPhaseArbitration(context.db).commit_for_phase(receipt["id"], phase_pulse_id=p["id"] + 1,
                                                         save_result=lambda _: pytest.fail("wrong pulse"))
    assert context.db.conn.execute("SELECT COUNT(*) FROM consciousness_loop_phase_results").fetchone()[0] == 0


def test_real_loop_preserves_world_content_inbox_and_broadcast(context, monkeypatch):
    completed(context)
    p = pulse(context)
    reads, broadcasts = [], []
    manager = context.manager
    monkeypatch.setattr(manager, "_run_world_phase", lambda _: pytest.fail("must reuse completed work"))
    monkeypatch.setattr(manager, "_read_working_memory_inbox", lambda *args: reads.append(args))
    monkeypatch.setattr(manager, "_observe_phase_for_working_memory", lambda *args: None)
    monkeypatch.setattr(manager, "_broadcast_working_memory_to_next_phase", lambda phase, result: broadcasts.append(copy.deepcopy(result)))
    result = manager.execute_phase("world", CYCLE, pulse=p)
    assert result["status"] == "satisfied_by_will"
    assert result["metrics"]["phase_placeholder"] == 0
    assert result["metrics"]["artifacts_created_count"] == 1
    assert result["raw_result"]["world_state"]["knowledge_findings"] == snapshot()["knowledge_findings"]
    assert len(reads) == 1 and len(broadcasts) == 1
    assert result["artifacts_created"][0]["artifact_table"] == "will_expression_receipts"
    replay = manager.execute_phase("world", CYCLE, pulse=p)
    assert replay["output_summary"] == result["output_summary"]
    assert len(reads) == 1 and len(broadcasts) == 1
    assert context.db.conn.execute("SELECT COUNT(*) FROM consciousness_loop_phase_results").fetchone()[0] == 1


def test_real_loop_runs_normally_when_evidence_is_absent(context, monkeypatch):
    completed(context, evidence=False)
    p = pulse(context)
    calls = []
    def run(result):
        calls.append(True)
        result["status"] = "success"
        result["output_summary"] = "normal world work"
        return result
    monkeypatch.setattr(context.manager, "_run_world_phase", run)
    monkeypatch.setattr(context.manager, "_read_working_memory_inbox", lambda *args: None)
    monkeypatch.setattr(context.manager, "_observe_phase_for_working_memory", lambda *args: None)
    monkeypatch.setattr(context.manager, "_broadcast_working_memory_to_next_phase", lambda *args: None)
    assert context.manager.execute_phase("world", CYCLE, pulse=p)["status"] == "success"
    assert calls == [True]


def test_probe_reports_reservation_without_exposing_world_content(context):
    completed(context)
    p = pulse(context)
    claim(context, p)
    payload = query_phase_satisfaction(context.db.conn.cursor(), Namespace(
        user_id=USER, agent_instance=TEST_INSTANCE, relation_id=None, scope_kind="global", limit=5,
    ))
    row = payload["rows"][0]
    assert row["status"] == "reserved" and row["reserved_by_phase_pulse_id"] == p["id"]
    assert row["consumed_at"] is None
    assert "knowledge_findings" not in str(payload)
    assert "evidence_json" not in row


def test_one_pulse_reserves_only_one_of_multiple_equivalent_results(context):
    first = completed(context)
    context.db.conn.execute("UPDATE will_expressions SET idempotency_key = idempotency_key || ':previous' WHERE id = ?", (first["id"],))
    context.db.conn.commit()
    completed(context)
    p = pulse(context)
    receipt = claim(context, p)
    assert claim(context, p)["id"] == receipt["id"]
    assert claim(context, pulse(context, index=2))["id"] != receipt["id"]


def test_scheduler_recovers_only_abandoned_reservations(context):
    from datetime import timezone
    completed(context)
    p = pulse(context)
    claim(context, p)
    arb = WillPhaseArbitration(context.db)
    assert arb.recover_reservations(agent_instance=TEST_INSTANCE, cycle_id=CYCLE, phase="world") == 0
    old = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
    context.db.conn.execute("UPDATE will_phase_satisfactions SET reserved_at = ?", (old,))
    context.db.conn.execute("UPDATE consciousness_phase_pulses SET updated_at = ?, scheduled_at = ?", (old, old))
    context.db.conn.commit()
    due = context.manager._get_due_phase_pulse(cycle_id=CYCLE, phase=PHASE_BY_KEY["world"])
    assert due["id"] == p["id"] and due["status"] == "failed"
    assert due["last_error"] == "will_phase_reservation_interrupted"
    assert context.db.conn.execute("SELECT status FROM will_phase_satisfactions").fetchone()[0] == "reserved"


def test_a_future_pulse_does_not_consume_current_work(context):
    completed(context)
    p = pulse(context)
    context.db.conn.execute("UPDATE consciousness_phase_pulses SET scheduled_at = ?",
                            ((datetime.utcnow() + timedelta(days=1)).isoformat(),))
    context.db.conn.commit()
    assert claim(context, p) is None


def test_migration_invalidates_legacy_unverified_receipts(context):
    completed(context)
    context.db.conn.execute("UPDATE will_phase_satisfactions SET evidence_version = 0")
    context.db.conn.commit()
    WillPhaseArbitration(context.db)
    row = context.db.conn.execute("SELECT status, result_code FROM will_phase_satisfactions").fetchone()
    assert tuple(row) == ("invalidated", "legacy_evidence_unverified")
    assert context.db.conn.execute("SELECT COUNT(*) FROM will_phase_satisfactions").fetchone()[0] == 1
    assert claim(context, pulse(context)) is None


def test_concurrent_commits_create_one_result(context, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    completed(context)
    p = pulse(context)
    receipt = claim(context, p)
    result = context.manager._build_placeholder_result(CYCLE, PHASE_BY_KEY["world"], "test", "automatic")
    result["status"] = "satisfied_by_will"
    result["metrics"].update({"pulse_id": p["id"], "will_phase_satisfaction_id": receipt["id"]})
    path = tmp_path / "concurrent.db"
    target = sqlite3.connect(path)
    context.db.conn.backup(target)
    target.close()

    def worker(_):
        conn = sqlite3.connect(path, timeout=30)
        try:
            arb = WillPhaseArbitration(SimpleNamespace(conn=conn))
            return arb.commit_for_phase(
                receipt["id"], phase_pulse_id=p["id"],
                save_result=lambda connection: context.manager._save_phase_result(
                    copy.deepcopy(result), connection=connection, commit=False),
            )
        finally:
            conn.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, range(2)))
    assert results[0][0] == results[1][0]
    assert sorted(created for _, created in results) == [False, True]
