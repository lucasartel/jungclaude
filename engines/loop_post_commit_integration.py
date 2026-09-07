"""Recover local memory and audit effects of normally executed loop phases."""
from __future__ import annotations

import json
import logging
from datetime import timedelta

from engines.working_memory import WorkingMemoryEngine
from engines.will_delivery_receipt import atomic, delivery_connection
from engines.will_recovery import utc_time

logger = logging.getLogger(__name__)
MAX_ATTEMPTS = 5


def ensure_schema(db):
    """Add a durable post-commit queue without enrolling historical results."""
    if not hasattr(db, "conn"):
        return
    cursor = db.conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS consciousness_loop_post_commit_effects (
        phase_result_id INTEGER PRIMARY KEY, agent_instance TEXT NOT NULL, cycle_id TEXT NOT NULL,
        phase TEXT NOT NULL, integration_version INTEGER NOT NULL DEFAULT 1,
        integration_at TEXT, integration_attempts INTEGER NOT NULL DEFAULT 0,
        integration_next_at TEXT, integration_error TEXT,
        FOREIGN KEY (phase_result_id) REFERENCES consciousness_loop_phase_results(id))""")
    cursor.execute("""CREATE INDEX IF NOT EXISTS idx_loop_post_commit_pending
        ON consciousness_loop_post_commit_effects(agent_instance, integration_at, integration_next_at)""")
    db.conn.commit()


def register(connection, *, phase_result_id, agent_instance, cycle_id, phase):
    """Enroll a newly persisted normal result in the same transaction."""
    connection.execute("""INSERT OR IGNORE INTO consciousness_loop_post_commit_effects
        (phase_result_id, agent_instance, cycle_id, phase, integration_version)
        VALUES (?, ?, ?, ?, 1)""", (phase_result_id, agent_instance, cycle_id, phase))


def _result(manager, row):
    result = dict(row)
    result["metrics"] = manager._decode_json_dict(result.pop("metrics_json", None))
    result["warnings"] = manager._decode_json_list(result.pop("warnings_json", None))
    result["errors"] = manager._decode_json_list(result.pop("errors_json", None))
    result["raw_result"] = manager._decode_json_dict(result.pop("raw_result_json", None))
    try:
        result["artifacts_created"] = json.loads(result.pop("artifacts_created_json", "[]") or "[]")
    except (TypeError, ValueError, json.JSONDecodeError):
        result["artifacts_created"] = []
    return result


def _validate(manager, conn, phase_result_id):
    queue = conn.execute("SELECT * FROM consciousness_loop_post_commit_effects WHERE phase_result_id = ?",
                         (phase_result_id,)).fetchone()
    if queue is None:
        raise ValueError("loop_post_commit_record_missing")
    queue = dict(queue)
    result_row = conn.execute("SELECT * FROM consciousness_loop_phase_results WHERE id = ?",
                              (phase_result_id,)).fetchone()
    if result_row is None:
        raise ValueError("loop_post_commit_result_missing")
    result = _result(manager, result_row)
    if (queue["agent_instance"] != manager.agent_instance or result["agent_instance"] != manager.agent_instance
            or queue["cycle_id"] != result["cycle_id"] or queue["phase"] != result["phase"]
            or queue["integration_version"] != 1 or result["status"] == "failed"):
        raise ValueError("loop_post_commit_scope_or_state_mismatch")
    return queue, result


def integrate(manager, phase_result_id):
    """Atomically observe, broadcast, audit and mark one normal result integrated."""
    from consciousness_loop import PHASE_BY_KEY

    with delivery_connection(manager.db) as conn, atomic(conn):
        queue, result = _validate(manager, conn, phase_result_id)
        if queue["integration_at"]:
            return result
        now = utc_time(manager._now())
        completed = utc_time(result["completed_at"])
        if completed is None or completed > now or now - completed > timedelta(hours=24):
            raise ValueError("loop_post_commit_stale_result_requires_review")
        phase = PHASE_BY_KEY.get(result["phase"])
        if phase is None:
            raise ValueError("loop_post_commit_unknown_phase")
        memory_db = manager.db.working_memory_transaction(conn)
        memory_db._init_working_memory_schema()
        source_ref = f"loop#{result['id']}"
        previous = conn.execute("""SELECT id FROM working_memory_items WHERE agent_instance = ?
            AND EXISTS (SELECT 1 FROM json_each(CASE WHEN json_valid(source_refs_json)
                THEN source_refs_json ELSE '[]' END) WHERE value = ?) LIMIT 1""",
            (manager.agent_instance, source_ref)).fetchone()
        audit = conn.execute("SELECT id FROM consciousness_loop_events WHERE phase_result_id = ?",
                             (result["id"],)).fetchone()
        if previous or audit:
            raise ValueError("loop_post_commit_partial_effects_require_review")
        memory = WorkingMemoryEngine(memory_db, agent_instance=manager.agent_instance)
        item_id = memory.observe_phase_result(
            phase_result_id=result["id"], cycle_id=result["cycle_id"], phase=phase.key,
            status=result["status"], output_summary=result["output_summary"],
            trigger_source=result["trigger_source"], warnings=result["warnings"],
            errors=result["errors"], metrics=result["metrics"],
        )
        if item_id is None:
            raise ValueError("loop_post_commit_observation_missing")
        item = memory_db.get_working_memory_item(item_id)
        result["metrics"].update(working_memory_item_id=item_id, working_memory_item_type=item["item_type"])
        if item["item_type"] == "candidate":
            result["metrics"]["working_memory_candidate_id"] = item_id
        result["raw_result"]["working_memory_observation"] = {
            "item_id": item_id, "item_type": item["item_type"], "source_ref": source_ref,
        }
        broadcast = memory.broadcast_payload(cycle_id=result["cycle_id"], from_phase=phase.key,
                                             to_phase=manager._next_phase_key(phase))
        result["metrics"].update(working_memory_broadcast_id=broadcast["id"],
            working_memory_broadcast_focus_count=broadcast["focus_count"],
            working_memory_broadcast_fringe_count=broadcast["fringe_count"])
        result["raw_result"]["working_memory_broadcast"] = broadcast
        event_id = manager._insert_event(
            cycle_id=result["cycle_id"], phase=phase.key, status="completed", trigger_name=phase.trigger_name,
            trigger_source=result["trigger_source"], execution_mode=result["raw_result"].get("execution_mode", "automatic"),
            input_summary=result["input_summary"], output_summary=result["output_summary"],
            duration_seconds=result["duration_ms"] / 1000.0, phase_result_id=result["id"],
            warnings=result["warnings"], errors=result["errors"], metrics=result["metrics"],
            connection=conn, commit=False,
        )
        result["metrics"]["loop_post_commit_event_id"] = event_id
        manager._update_phase_result_payloads(result["id"], result, connection=conn, commit=False)
        conn.execute("""UPDATE consciousness_loop_post_commit_effects SET integration_at = ?,
            integration_next_at = NULL, integration_error = NULL WHERE phase_result_id = ?""",
            (now.isoformat(), phase_result_id))
    logger.info("[LOOP POST-COMMIT] phase_result_id=%s committed", phase_result_id)
    return result


def recover(manager):
    """Retry only local persisted integrations; never rerun a phase or provider."""
    now = utc_time(manager._now())
    with delivery_connection(manager.db) as conn:
        rows = conn.execute("""SELECT phase_result_id FROM consciousness_loop_post_commit_effects
            WHERE agent_instance = ? AND integration_at IS NULL AND integration_attempts < ?
            AND (integration_next_at IS NULL OR julianday(integration_next_at) <= julianday(?))
            ORDER BY phase_result_id LIMIT 25""", (manager.agent_instance, MAX_ATTEMPTS, now.isoformat())).fetchall()
    counts = {"recovered": 0, "deferred": 0}
    for row in rows:
        result_id = row["phase_result_id"]
        with delivery_connection(manager.db) as conn, atomic(conn):
            claimed = conn.execute("""UPDATE consciousness_loop_post_commit_effects
                SET integration_attempts = integration_attempts + 1, integration_next_at = ?
                WHERE phase_result_id = ? AND agent_instance = ? AND integration_at IS NULL
                AND integration_attempts < ? AND (integration_next_at IS NULL OR julianday(integration_next_at) <= julianday(?))""",
                ((now + timedelta(minutes=5)).isoformat(), result_id, manager.agent_instance,
                 MAX_ATTEMPTS, now.isoformat()))
            if claimed.rowcount != 1:
                continue
            attempt = conn.execute("SELECT integration_attempts FROM consciousness_loop_post_commit_effects WHERE phase_result_id = ?",
                                   (result_id,)).fetchone()[0]
        try:
            integrate(manager, result_id)
            counts["recovered"] += 1
        except Exception as exc:
            error = str(exc) if isinstance(exc, ValueError) and str(exc).startswith("loop_post_commit_") else type(exc).__name__
            logger.warning("[LOOP POST-COMMIT] phase_result_id=%s error=%s", result_id, error)
            with delivery_connection(manager.db) as conn, atomic(conn):
                conn.execute("""UPDATE consciousness_loop_post_commit_effects SET integration_error = ?, integration_next_at = ?
                    WHERE phase_result_id = ? AND integration_at IS NULL""",
                    (error, (now + timedelta(minutes=5 * 2 ** (attempt - 1))).isoformat(), result_id))
            counts["deferred"] += 1
    return counts
