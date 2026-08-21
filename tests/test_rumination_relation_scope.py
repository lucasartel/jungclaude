"""Relation isolation tests for the rumination engine."""
from __future__ import annotations

import json
from datetime import datetime, timedelta

from jung_rumination import RuminationEngine


def _insert_fragment(conn, user_id: str, relation_id: str, content: str, processed: int = 0):
    cursor = conn.execute(
        """
        INSERT INTO rumination_fragments (
            user_id, relation_id, fragment_type, content, source_quote, processed
        ) VALUES (?, ?, 'thought', ?, ?, ?)
        """,
        (user_id, relation_id, content, content, processed),
    )
    return cursor.lastrowid


def _insert_tension(conn, user_id: str, relation_id: str, status: str = "open"):
    old = (datetime.now() - timedelta(days=1)).isoformat()
    cursor = conn.execute(
        """
        INSERT INTO rumination_tensions (
            user_id, relation_id, tension_type, pole_a_content, pole_a_fragment_ids,
            pole_b_content, pole_b_fragment_ids, tension_description, intensity,
            maturity_score, evidence_count, first_detected_at, status
        ) VALUES (?, ?, 'value_behavior', 'autonomy', ?, 'belonging', ?, 'same relation',
                  0.6, 0.2, 2, ?, ?)
        """,
        (user_id, relation_id, json.dumps([]), json.dumps([]), old, status),
    )
    return cursor.lastrowid


def test_stats_do_not_mix_relations(rumination_db):
    engine = RuminationEngine(rumination_db)
    conn = rumination_db.conn
    user_id = "participant"

    _insert_fragment(conn, user_id, "relation-a", "fragment a")
    _insert_fragment(conn, user_id, "relation-b", "fragment b")
    _insert_tension(conn, user_id, "relation-a")
    _insert_tension(conn, user_id, "relation-b", status="maturing")
    conn.execute(
        """
        INSERT INTO rumination_insights (
            user_id, relation_id, full_message, status
        ) VALUES (?, ?, 'insight a', 'ready')
        """,
        (user_id, "relation-a"),
    )
    conn.execute(
        """
        INSERT INTO rumination_insights (
            user_id, relation_id, full_message, status
        ) VALUES (?, ?, 'insight b', 'delivered')
        """,
        (user_id, "relation-b"),
    )
    conn.commit()

    stats_a = engine.get_stats(user_id, relation_id="relation-a")
    stats_b = engine.get_stats(user_id, relation_id="relation-b")

    assert stats_a["fragments_total"] == 1
    assert stats_a["tensions_open"] == 1
    assert stats_a["insights_ready"] == 1
    assert stats_a["insights_delivered"] == 0
    assert stats_b["fragments_total"] == 1
    assert stats_b["tensions_open"] == 0
    assert stats_b["tensions_maturing"] == 1
    assert stats_b["insights_ready"] == 0
    assert stats_b["insights_delivered"] == 1


def test_digest_only_updates_the_selected_relation(rumination_db):
    engine = RuminationEngine(rumination_db)
    conn = rumination_db.conn
    user_id = "participant"
    tension_a = _insert_tension(conn, user_id, "relation-a")
    tension_b = _insert_tension(conn, user_id, "relation-b")
    conn.commit()

    result = engine.digest(user_id, relation_id="relation-a")

    assert result["tensions_processed"] == 1
    status_a = conn.execute(
        "SELECT status FROM rumination_tensions WHERE id = ?", (tension_a,)
    ).fetchone()[0]
    status_b = conn.execute(
        "SELECT status FROM rumination_tensions WHERE id = ?", (tension_b,)
    ).fetchone()[0]
    assert status_a == "maturing"
    assert status_b == "open"


def test_non_admin_without_registered_relation_cannot_ingest(rumination_db):
    engine = RuminationEngine(rumination_db)

    assert engine.ingest(
        {
            "user_id": "unregistered-participant",
            "user_input": "A meaningful thought",
            "ai_response": "A response",
            "conversation_id": 1,
            "tension_level": 0.9,
            "affective_charge": 0.9,
            "existential_depth": 0.9,
        }
    ) == []


def test_non_admin_cannot_use_another_participants_relation(rumination_db):
    rumination_db.get_agent_relation = lambda relation_id: {
        "participant_user_id": "another-participant"
    }
    engine = RuminationEngine(rumination_db)

    assert engine.ingest(
        {
            "user_id": "participant",
            "relation_id": "relation-owned-by-another",
            "user_input": "A meaningful thought",
            "ai_response": "A response",
            "conversation_id": 1,
            "tension_level": 0.9,
            "affective_charge": 0.9,
            "existential_depth": 0.9,
        }
    ) == []
