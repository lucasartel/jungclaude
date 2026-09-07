"""Recover the local WM and audit effects of a phase satisfied by WILL."""
from __future__ import annotations

import logging
from datetime import timedelta
from engines.working_memory import WorkingMemoryEngine
from engines.will_delivery_receipt import atomic, delivery_connection
from engines.will_phase_arbitration import WillPhaseArbitration
from engines.will_recovery import utc_time

logger = logging.getLogger(__name__)


def integrate(manager, receipt_id):
    """WM observation, broadcast, audit, payload and completion marker commit together."""
    from consciousness_loop import PHASE_BY_KEY

    with delivery_connection(manager.db) as conn, atomic(conn):
        row = conn.execute("SELECT * FROM will_phase_satisfactions WHERE id = ?", (receipt_id,)).fetchone()
        if row is None:
            raise ValueError("will_loop_receipt_missing")
        receipt = dict(row)
        if (receipt["agent_instance"] != manager.agent_instance or receipt["user_id"] != manager.admin_user_id
                or receipt["scope_kind"] != "global" or receipt["relation_id"] is not None
                or receipt["status"] != "consumed" or receipt["evidence_version"] != 1):
            raise ValueError("will_loop_receipt_scope_or_state_mismatch")
        result = WillPhaseArbitration._stored_result(conn, receipt)
        pulse = conn.execute("SELECT * FROM consciousness_phase_pulses WHERE id = ?",
                             (receipt["consumed_by_phase_pulse_id"],)).fetchone()
        if (pulse is None or pulse["status"] != "completed" or pulse["phase_result_id"] != result["id"]
                or any(pulse[key] != receipt[key] for key in ("agent_instance", "cycle_id", "phase"))):
            raise ValueError("will_loop_pulse_mismatch")
        if receipt["integration_at"]:
            return result
        if receipt["integration_version"] != 1:
            raise ValueError("will_loop_legacy_effects_require_review")
        now = utc_time(manager._now())
        completed = utc_time(result["completed_at"])
        if completed is None or completed > now or now - completed > timedelta(hours=24):
            raise ValueError("will_loop_stale_result_requires_review")
        phase = PHASE_BY_KEY[result["phase"]]
        memory_db = manager.db.working_memory_transaction(conn)
        memory_db._init_working_memory_schema()
        previous = conn.execute("""SELECT id FROM working_memory_items WHERE agent_instance = ?
            AND EXISTS (SELECT 1 FROM json_each(CASE WHEN json_valid(source_refs_json)
                THEN source_refs_json ELSE '[]' END) WHERE value = ?) LIMIT 1""",
            (manager.agent_instance, f"loop#{result['id']}")).fetchone()
        audit = conn.execute("SELECT id FROM consciousness_loop_events WHERE phase_result_id = ?",
                             (result["id"],)).fetchone()
        if previous or audit:
            raise ValueError("will_loop_partial_effects_require_review")
        memory = WorkingMemoryEngine(memory_db, agent_instance=manager.agent_instance)
        item_id = memory.observe_phase_result(
            phase_result_id=result["id"], cycle_id=result["cycle_id"], phase=phase.key,
            status=result["status"], output_summary=result["output_summary"],
            trigger_source=result["trigger_source"], warnings=result["warnings"],
            errors=result["errors"], metrics=result["metrics"],
        )
        if item_id is None:
            raise ValueError("will_loop_observation_missing")
        item = memory_db.get_working_memory_item(item_id)
        result["metrics"].update(working_memory_item_id=item_id, working_memory_item_type=item["item_type"])
        if item["item_type"] == "candidate":
            result["metrics"]["working_memory_candidate_id"] = item_id
        result["raw_result"]["working_memory_observation"] = {
            "item_id": item_id, "item_type": item["item_type"], "source_ref": f"loop#{result['id']}",
        }
        broadcast = memory.broadcast_payload(cycle_id=result["cycle_id"], from_phase=phase.key,
                                             to_phase=manager._next_phase_key(phase))
        result["metrics"].update(working_memory_broadcast_id=broadcast["id"],
            working_memory_broadcast_focus_count=broadcast["focus_count"],
            working_memory_broadcast_fringe_count=broadcast["fringe_count"])
        result["raw_result"]["working_memory_broadcast"] = broadcast
        event_id = manager._insert_event(
            cycle_id=result["cycle_id"], phase=phase.key, status="completed", trigger_name=phase.trigger_name,
            trigger_source=result["trigger_source"], execution_mode="automatic",
            input_summary=result["input_summary"], output_summary=result["output_summary"],
            duration_seconds=result["duration_ms"] / 1000.0, phase_result_id=result["id"],
            warnings=result["warnings"], errors=result["errors"], metrics=result["metrics"],
            connection=conn, commit=False,
        )
        result["metrics"]["will_loop_event_id"] = event_id
        manager._update_phase_result_payloads(result["id"], result, connection=conn, commit=False)
        conn.execute("""UPDATE will_phase_satisfactions SET integration_at = ?, integration_next_at = NULL,
            integration_error = NULL WHERE id = ?""", (now.isoformat(), receipt_id))
    logger.info("[WILL LOOP INTEGRATION] receipt_id=%s phase_result_id=%s committed", receipt_id, result["id"])
    return result


def recover(manager):
    """Bounded retries for the post-commit queue, independent of the current phase."""
    now = utc_time(manager._now())
    with delivery_connection(manager.db) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(will_phase_satisfactions)")}
        if "integration_at" not in columns:
            return {"recovered": 0, "deferred": 0}
        rows = conn.execute("""SELECT id FROM will_phase_satisfactions
            WHERE agent_instance = ? AND user_id = ? AND scope_kind = 'global' AND relation_id IS NULL
            AND status = 'consumed' AND integration_at IS NULL AND integration_attempts < 5
            AND (integration_next_at IS NULL OR julianday(integration_next_at) <= julianday(?))
            ORDER BY id LIMIT 25""", (manager.agent_instance, manager.admin_user_id, now.isoformat())).fetchall()
    counts = {"recovered": 0, "deferred": 0}
    for row in rows:
        with delivery_connection(manager.db) as conn, atomic(conn):
            claimed = conn.execute("""UPDATE will_phase_satisfactions
                SET integration_attempts = integration_attempts + 1, integration_next_at = ?
                WHERE id = ? AND integration_at IS NULL AND integration_attempts < 5
                AND (integration_next_at IS NULL OR julianday(integration_next_at) <= julianday(?))""",
                ((now + timedelta(minutes=5)).isoformat(), row["id"], now.isoformat()))
            if claimed.rowcount != 1:
                continue
            attempt = conn.execute("SELECT integration_attempts FROM will_phase_satisfactions WHERE id = ?",
                                   (row["id"],)).fetchone()[0]
        try:
            integrate(manager, row["id"])
            counts["recovered"] += 1
        except Exception as exc:
            error = str(exc) if isinstance(exc, ValueError) and str(exc).startswith("will_loop_") else type(exc).__name__
            logger.warning("[WILL LOOP RECOVERY] receipt_id=%s error=%s", row["id"], error)
            with delivery_connection(manager.db) as conn, atomic(conn):
                conn.execute("""UPDATE will_phase_satisfactions SET integration_error = ?, integration_next_at = ?
                    WHERE id = ? AND integration_at IS NULL""",
                    (error, (now + timedelta(minutes=5 * 2 ** (attempt - 1))).isoformat(), row["id"]))
            counts["deferred"] += 1
    return counts
