"""Tests for Phase V Stage B Symbolic Knowledge Graph Prompt Context Injection."""
from __future__ import annotations

import sys
import types

openai_stub = types.ModuleType("openai")
openai_stub.OpenAI = object
if not hasattr(sys.modules.get("openai"), "OpenAI"):
    sys.modules["openai"] = openai_stub

import sqlite3
import pytest

from core.config import Config
from core.database import HybridDatabaseManager
from engines.symbolic_context import SymbolicGraphContextBuilder


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_symbolic_context.db"
    db = HybridDatabaseManager.__new__(HybridDatabaseManager)
    db.conn = sqlite3.connect(str(db_file), check_same_thread=False)
    db.conn.row_factory = sqlite3.Row
    import threading
    db._lock = threading.Lock()
    db.agent_instance = "test_jung"
    db._init_sqlite_schema()
    return db


def test_symbolic_context_builder_with_triples(test_db):
    test_db.add_symbolic_triple(
        agent_instance="test_jung",
        subject_name="Lucas",
        predicate="atua_em",
        object_name="pastor",
        source_ref="conversation#1001",
        confidence=1.0,
    )
    test_db.add_symbolic_triple(
        agent_instance="test_jung",
        subject_name="pastor",
        predicate="tenciona_com",
        object_name="sensibilidade_vs_adequacao",
        source_ref="conversation#1002",
        confidence=0.9,
    )

    builder = SymbolicGraphContextBuilder(test_db, agent_instance="test_jung", max_hops=2, max_triples=10)
    res = builder.build_causal_context(user_id=Config.ADMIN_USER_ID, message_text="como está minha vida pastoral?")

    assert res["status"] == "available"
    assert res["triple_count"] >= 2
    assert "GRAFO SIMBÓLICO" in res["context_block"]
    assert "Lucas -[atua_em]-> pastor" in res["context_block"]
    assert "conversation#1001" in res["context_block"]


def test_symbolic_context_empty(test_db):
    builder = SymbolicGraphContextBuilder(test_db, agent_instance="test_jung")
    res = builder.build_causal_context(user_id=Config.ADMIN_USER_ID, message_text="qualquer coisa")
    assert res["status"] == "empty"
    assert res["context_block"] == ""


def test_symbolic_context_flag_controls(test_db, monkeypatch):
    test_db.add_symbolic_triple(
        agent_instance="test_jung",
        subject_name="Lucas",
        predicate="valoriza",
        object_name="autonomia",
        source_ref="conversation#500",
        confidence=0.95,
    )

    from core.engine import JungianEngine

    engine = JungianEngine.__new__(JungianEngine)
    engine.db = test_db
    engine._get_admin_user_id = lambda: Config.ADMIN_USER_ID

    # Test disabled flag
    monkeypatch.setattr(Config, "SYMBOLIC_GRAPH_PROMPT_CONTEXT_ENABLED", False)
    monkeypatch.setattr(Config, "SYMBOLIC_GRAPH_PROMPT_CONTEXT_ADMIN_ONLY", True)
    assert engine._build_symbolic_graph_prompt_context(Config.ADMIN_USER_ID) == ""

    # Test enabled for admin
    monkeypatch.setattr(Config, "SYMBOLIC_GRAPH_PROMPT_CONTEXT_ENABLED", True)
    monkeypatch.setattr(Config, "SYMBOLIC_GRAPH_PROMPT_CONTEXT_ADMIN_ONLY", True)
    ctx = engine._build_symbolic_graph_prompt_context(Config.ADMIN_USER_ID)
    assert "GRAFO SIMBÓLICO" in ctx
    assert "Lucas -[valoriza]-> autonomia" in ctx

    # Test admin-only flag blocks regular users
    assert engine._build_symbolic_graph_prompt_context("other_user_id_123") == ""


def test_find_seed_nodes_extraction(test_db):
    cursor = test_db.conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO symbolic_nodes (agent_instance, entity_name) VALUES (?, ?)",
        ("test_jung", "Python"),
    )
    test_db.conn.commit()

    builder = SymbolicGraphContextBuilder(test_db, agent_instance="test_jung")

    # Message with entity
    seeds = builder.find_seed_nodes("user_test_123", "I love writing Python code.")
    assert "Python" in seeds
    assert "Lucas" not in seeds

    # Message without entity
    empty_seeds = builder.find_seed_nodes("user_test_123", "I love writing code.")
    assert empty_seeds == []
