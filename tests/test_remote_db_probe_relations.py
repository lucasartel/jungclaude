from argparse import Namespace
import sqlite3

from scripts.remote_db_probe import query_relations


def test_relations_probe_reports_scope_and_consent_counts() -> None:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE agent_relations (
            relation_id TEXT PRIMARY KEY,
            agent_instance TEXT,
            org_id TEXT,
            participant_user_id TEXT,
            relation_type TEXT,
            role TEXT,
            status TEXT,
            consent_status TEXT,
            consented_at TEXT,
            revoked_at TEXT,
            scope_json TEXT,
            cadence_baseline_hours REAL,
            last_interaction_at TEXT,
            metadata_json TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    conn.execute(
        """
        INSERT INTO agent_relations (
            relation_id, agent_instance, org_id, participant_user_id,
            relation_type, role, status, consent_status, scope_json,
            metadata_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "rel-1", "jung_a", "org_a", "user_a", "participant", "employee",
            "active", "granted", '{"memory":"private"}', '{}', "now", "now",
        ),
    )
    conn.commit()

    payload = query_relations(
        conn.cursor(), Namespace(agent_instance="jung_a", user_id=None, limit=5)
    )

    assert payload["available"] is True
    assert payload["total"] == 1
    assert payload["status_counts"] == [{"key": "active", "count": 1}]
    assert payload["consent_counts"] == [{"key": "granted", "count": 1}]
    assert payload["rows"][0]["scope"] == {"memory": "private"}
