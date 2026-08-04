"""Tests for admin_communicate handlers (Corte 3.1).

Covers:
- pose_strategic_question handler sends Telegram message
- proactive_check_in handler sends Telegram message
- follow_up_theme handler sends Telegram message
- _send_telegram_message handles missing token gracefully
- _send_telegram_message handles missing chat_id gracefully
- dispatch_proposal routes admin_communicate proposals correctly
- Telegram send failure marks proposal as failed
"""
from __future__ import annotations

import importlib.util
import os
import sqlite3
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        del sys.modules[name]
        raise
    return module


_PROPOSALS_MODULE = _load_module(
    "core.db.action_proposals", REPO_ROOT / "core" / "db" / "action_proposals.py"
)
ActionProposalDatabaseMixin = _PROPOSALS_MODULE.ActionProposalDatabaseMixin


class _DispatchDB(ActionProposalDatabaseMixin):
    def __init__(self, conn):
        self.conn = conn
        self._lock = threading.RLock()
        self.agent_instance = "test_jung_v0"
        self._init_action_proposals_schema()


def _make_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return _DispatchDB(conn)


def _load_runner():
    if "instance_config" not in sys.modules:
        ic = type(sys)("instance_config")
        ic.AGENT_INSTANCE = "test_jung_v0"
        ic.ADMIN_USER_ID = "test_admin"
        sys.modules["instance_config"] = ic
    return _load_module(
        "controlled_action_test", REPO_ROOT / "engines" / "controlled_action.py"
    )


class TestAdminCommunicateHandlers:
    def _make_runner(self, db, monkeypatch, *, send_succeeds=True):
        runner_module = _load_runner()
        runner = runner_module.ControlledActionRunner(db, agent_instance="test_jung_v0")

        # Mock Telegram send
        sent_messages = []

        def fake_send(text):
            sent_messages.append(text)
            return send_succeeds

        monkeypatch.setattr(runner, "_send_telegram_message", fake_send)
        return runner, sent_messages

    def _create_proposal(self, db, action_type, gate_level="admin_communicate"):
        return db.create_action_proposal(
            agent_instance="test_jung_v0",
            cycle_id="c1",
            user_id="test_admin",
            action_type=action_type,
            gate_level=gate_level,
            source_refs=["will#1"],
            payload={"agent_stance": "companionable", "silence_delta_hours": 48},
        )

    def test_pose_strategic_question_sends_message(self, monkeypatch):
        db = _make_db()
        pid = self._create_proposal(db, "pose_strategic_question")
        runner, sent = self._make_runner(db, monkeypatch)
        result = runner.dispatch_proposal(proposal_id=pid, user_id="test_admin")
        assert result["status"] == "executed"
        assert result["message_sent"] is True
        assert len(sent) == 1
        assert "Lucas" in sent[0]

    def test_proactive_check_in_sends_message(self, monkeypatch):
        db = _make_db()
        pid = self._create_proposal(db, "proactive_check_in")
        runner, sent = self._make_runner(db, monkeypatch)
        result = runner.dispatch_proposal(proposal_id=pid, user_id="test_admin")
        assert result["status"] == "executed"
        assert len(sent) == 1
        assert "dias" in sent[0] or "presença" in sent[0]

    def test_follow_up_theme_sends_message(self, monkeypatch):
        db = _make_db()
        pid = self._create_proposal(db, "follow_up_theme")
        runner, sent = self._make_runner(db, monkeypatch)
        result = runner.dispatch_proposal(proposal_id=pid, user_id="test_admin")
        assert result["status"] == "executed"
        assert len(sent) == 1
        assert "tema" in sent[0]

    def test_telegram_failure_marks_proposal_failed(self, monkeypatch):
        db = _make_db()
        pid = self._create_proposal(db, "proactive_check_in")
        runner, sent = self._make_runner(db, monkeypatch, send_succeeds=False)
        result = runner.dispatch_proposal(proposal_id=pid, user_id="test_admin")
        assert result["status"] == "failed"
        assert "telegram_send_failed" in result.get("error", "")

    def test_missing_token_returns_false(self):
        runner_module = _load_runner()
        db = _make_db()
        runner = runner_module.ControlledActionRunner(db, agent_instance="test_jung_v0")
        # Ensure no token
        old_token = os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        try:
            assert runner._send_telegram_message("test") is False
        finally:
            if old_token:
                os.environ["TELEGRAM_BOT_TOKEN"] = old_token

    def test_pending_handlers_still_skipped(self, monkeypatch):
        db = _make_db()
        pid = db.create_action_proposal(
            agent_instance="test_jung_v0",
            cycle_id="c1",
            user_id="test_admin",
            action_type="synthesize_cross_source",
            gate_level="internal_only",
            source_refs=["will#1"],
        )
        runner, _ = self._make_runner(db, monkeypatch)
        result = runner.dispatch_proposal(proposal_id=pid, user_id="test_admin")
        assert result["status"] == "skipped"
        assert "handler_pending" in result["skipped_reason"]
