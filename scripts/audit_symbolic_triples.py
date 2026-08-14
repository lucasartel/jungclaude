"""Audit script for Phase V Symbolic Knowledge Graph 100-Triple Quality Gate.

Audits candidate triples extracted from database evidence against strict criteria:
- Valid evidence handle matching PROFILE_SOURCE_RE
- Well-formed subject, predicate, and object
- Valid confidence bounds
- Target precision >= 80% to pass the gate
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import types
from pathlib import Path
from typing import Any, Dict, List, Tuple

openai_stub = types.ModuleType("openai")
openai_stub.OpenAI = object
if not hasattr(sys.modules.get("openai"), "OpenAI"):
    sys.modules["openai"] = openai_stub

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PROFILE_SOURCE_RE = re.compile(
    r"\b(?:loop|conversation|dream|will|meta|rumination_insight|work_run|work_ticket|work_delivery|hobby_artifact|agent_development)#\d+\b"
)

TARGET_AUDIT_COUNT = 100
PASSING_PRECISION_THRESHOLD = 0.80


def audit_triple(triple: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Evaluates whether a single triple meets quality criteria."""
    issues = []
    subject = str(triple.get("subject") or "").strip()
    predicate = str(triple.get("predicate") or "").strip()
    obj = str(triple.get("object") or "").strip()
    source_ref = str(triple.get("source_ref") or "").strip()
    confidence = triple.get("confidence", 0.0)

    if not subject or len(subject) < 2:
        issues.append("invalid_or_empty_subject")
    if not predicate or len(predicate) < 2:
        issues.append("invalid_or_empty_predicate")
    if not obj or len(obj) < 2:
        issues.append("invalid_or_empty_object")

    if not source_ref or not PROFILE_SOURCE_RE.search(source_ref):
        issues.append("missing_or_invalid_evidence_anchor")

    try:
        c_val = float(confidence)
        if not (0.0 <= c_val <= 1.0):
            issues.append("confidence_out_of_bounds")
    except Exception:
        issues.append("non_numeric_confidence")

    is_valid = len(issues) == 0
    return is_valid, issues


def run_audit(db_path: str, user_id: str, limit: int = TARGET_AUDIT_COUNT) -> Dict[str, Any]:
    """Runs the 100-triple quality gate audit against the database."""
    if not os.path.exists(db_path):
        return {"error": f"database_not_found: {db_path}", "passed": False}

    conn = sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    # Duck-type or import HybridDatabaseManager
    from core.database import HybridDatabaseManager
    from engines.symbolic_graph import SymbolicGraphExtractor

    db = HybridDatabaseManager.__new__(HybridDatabaseManager)
    db.conn = conn
    db.agent_instance = "jung_v1"
    import threading
    db._lock = threading.Lock()

    extractor = SymbolicGraphExtractor(db, agent_instance="jung_v1")
    fact_triples = extractor.extract_from_user_facts(user_id, limit=limit // 2)
    contra_triples = extractor.extract_from_identity_contradictions(limit=limit // 2)
    insight_triples = extractor.extract_from_rumination_insights(user_id, limit=limit // 2)

    all_triples = (fact_triples + contra_triples + insight_triples)[:limit]

    valid_count = 0
    audit_records = []

    for t in all_triples:
        is_valid, issues = audit_triple(t)
        if is_valid:
            valid_count += 1
        audit_records.append(
            {
                "triple": f"({t.get('subject')} -[{t.get('predicate')}]-> {t.get('object')})",
                "source_ref": t.get("source_ref"),
                "confidence": t.get("confidence"),
                "is_valid": is_valid,
                "issues": issues,
            }
        )

    total = len(all_triples)
    precision = (valid_count / total) if total > 0 else 0.0
    passed = total >= 1 and precision >= PASSING_PRECISION_THRESHOLD

    return {
        "total_audited": total,
        "valid_count": valid_count,
        "invalid_count": total - valid_count,
        "precision": round(precision, 4),
        "threshold": PASSING_PRECISION_THRESHOLD,
        "passed": passed,
        "audit_sample": audit_records[:10],
    }


def main():
    parser = argparse.ArgumentParser(description="Audit Phase V Symbolic Graph Triples.")
    parser.add_argument("--db-path", default="railway_jung_hybrid_live.db")
    parser.add_argument("--user-id", default="367f9e509e396d51")
    parser.add_argument("--limit", type=int, default=TARGET_AUDIT_COUNT)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    result = run_audit(args.db_path, args.user_id, limit=args.limit)
    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
