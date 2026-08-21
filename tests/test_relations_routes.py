"""Tests for the Relations admin cockpit boundary."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

for module_name in list(sys.modules):
    if module_name == "fastapi" or module_name.startswith("fastapi."):
        del sys.modules[module_name]
    if module_name == "jinja2" or module_name.startswith("jinja2."):
        del sys.modules[module_name]
    if module_name == "pydantic" or module_name.startswith("pydantic."):
        del sys.modules[module_name]

import pytest
from fastapi import HTTPException
from jinja2 import Environment, FileSystemLoader

from admin_web.routes import relations_routes


class FakeDB:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            CREATE TABLE users (user_id TEXT PRIMARY KEY, user_name TEXT, first_name TEXT, platform TEXT);
            CREATE TABLE organizations (org_id TEXT PRIMARY KEY, org_name TEXT);
            CREATE TABLE user_organization_mapping (user_id TEXT, org_id TEXT, status TEXT);
        """)
        self.conn.execute("INSERT INTO users VALUES ('user-a', 'Alice', 'Alice', 'telegram')")
        self.conn.execute("INSERT INTO users VALUES ('user-b', 'Bob', 'Bob', 'telegram')")
        self.conn.execute("INSERT INTO organizations VALUES ('org-a', 'Acme')")
        self.conn.execute("INSERT INTO user_organization_mapping VALUES ('user-a', 'org-a', 'active')")
        self.conn.commit()

    def get_user(self, user_id):
        row = self.conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    def count_conversations(self, user_id, relation_id=None):
        return 2 if relation_id else 0


def test_org_scope_isolated_for_org_admin_and_global_for_master():
    assert relations_routes._org_scope({"role": "org_admin", "org_id": "org-a"}) == "org-a"
    assert relations_routes._org_scope({"role": "master"}) is None
    db = FakeDB()
    assert relations_routes._validate_target(db, {"role": "org_admin", "org_id": "org-a"}, "user-a", "org-a") == "org-a"
    with pytest.raises(HTTPException) as exc_info:
        relations_routes._validate_target(db, {"role": "org_admin", "org_id": "org-a"}, "user-b", "org-a")
    assert exc_info.value.status_code == 403


def test_relation_rows_expose_metadata_but_not_conversation_content():
    rows = relations_routes._relation_rows(FakeDB(), [{
        "relation_id": "rel-a", "agent_instance": "jung_v1", "org_id": "org-a",
        "participant_user_id": "user-a", "relation_type": "participant",
        "role": "employee", "status": "active", "consent_status": "granted",
        "scope": {"memory": "private"}, "last_interaction_at": "2026-08-21T10:00:00",
    }])
    assert rows[0]["participant_name"] == "Alice"
    assert rows[0]["conversation_count"] == 2
    assert "user_input" not in rows[0]
    assert "ai_response" not in rows[0]


def test_relations_template_renders_empty_state_and_scope():
    template_dir = Path(__file__).resolve().parents[1] / "admin_web" / "templates"
    template = Environment(loader=FileSystemLoader(template_dir)).get_template("relations.html")
    rendered = template.render(
        request=SimpleNamespace(url=SimpleNamespace(path="/admin/relations"), state=SimpleNamespace(admin={"role": "org_admin", "org_id": "org-a"})), admin={"role": "org_admin", "org_id": "org-a"},
        active_nav="relations", agent_instance="jung_v1", relations=[],
        organizations=[], participant_options=[], total_relations=0,
        active_relations=0, granted_relations=0, message=None,
    )
    assert "No relations registered" in rendered
    assert "No conversation text is loaded here." in rendered
