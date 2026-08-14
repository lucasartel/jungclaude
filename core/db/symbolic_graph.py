"""Symbolic Knowledge Graph (SKG) database mixin for Phase V.

Provides structured persistence for symbolic nodes and relational triples
(subject -> predicate -> object) with strict evidence anchors (PROFILE_SOURCE_RE)
and causal path traversal via recursive SQL queries.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

PROFILE_SOURCE_RE = re.compile(
    r"\b(?:loop|conversation|dream|will|meta|rumination_insight|work_run|work_ticket|work_delivery|hobby_artifact|agent_development)#\d+\b"
)


class SymbolicGraphDatabaseMixin:
    """Database mixin for Symbolic Knowledge Graph nodes, triples, and causal queries."""

    def _init_symbolic_graph_schema(self) -> None:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS symbolic_nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_instance TEXT NOT NULL,
                    entity_name TEXT NOT NULL,
                    entity_type TEXT DEFAULT 'concept',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(agent_instance, entity_name)
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_symbolic_nodes_name "
                "ON symbolic_nodes(agent_instance, entity_name)"
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS symbolic_triples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_instance TEXT NOT NULL,
                    subject_id INTEGER NOT NULL,
                    predicate TEXT NOT NULL,
                    object_id INTEGER NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    source_ref TEXT NOT NULL,
                    status TEXT DEFAULT 'candidate',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subject_id) REFERENCES symbolic_nodes(id),
                    FOREIGN KEY (object_id) REFERENCES symbolic_nodes(id),
                    UNIQUE(agent_instance, subject_id, predicate, object_id, source_ref)
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_symbolic_triples_subj "
                "ON symbolic_triples(agent_instance, subject_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_symbolic_triples_pred "
                "ON symbolic_triples(agent_instance, predicate)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_symbolic_triples_obj "
                "ON symbolic_triples(agent_instance, object_id)"
            )
            self.conn.commit()

    def get_or_create_symbolic_node(
        self,
        *,
        agent_instance: str,
        entity_name: str,
        entity_type: str = "concept",
    ) -> int:
        """Gets or inserts a symbolic node by name, returning its node ID."""
        self._init_symbolic_graph_schema()
        clean_name = " ".join((entity_name or "").strip().split())
        clean_type = (entity_type or "concept").strip().lower()
        if not clean_name:
            raise ValueError("empty_entity_name")

        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id FROM symbolic_nodes WHERE agent_instance = ? AND entity_name = ?",
                (agent_instance, clean_name),
            )
            row = cursor.fetchone()
            if row:
                return int(row[0])

            cursor.execute(
                """
                INSERT INTO symbolic_nodes (agent_instance, entity_name, entity_type, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (agent_instance, clean_name, clean_type, datetime.now(timezone.utc).isoformat()),
            )
            self.conn.commit()
            return int(cursor.lastrowid)

    def add_symbolic_triple(
        self,
        *,
        agent_instance: str,
        subject_name: str,
        predicate: str,
        object_name: str,
        source_ref: str,
        confidence: float = 1.0,
        status: str = "candidate",
        subject_type: str = "concept",
        object_type: str = "concept",
    ) -> int:
        """Inserts a verified or candidate triple anchored to valid evidence."""
        self._init_symbolic_graph_schema()
        clean_ref = (source_ref or "").strip()
        if not clean_ref or not PROFILE_SOURCE_RE.search(clean_ref):
            raise ValueError(f"invalid_source_ref:{source_ref} (must match PROFILE_SOURCE_RE pattern)")

        clean_pred = "_".join((predicate or "").strip().lower().split())
        if not clean_pred:
            raise ValueError("empty_predicate")

        confidence = max(0.0, min(1.0, float(confidence)))
        subj_id = self.get_or_create_symbolic_node(
            agent_instance=agent_instance,
            entity_name=subject_name,
            entity_type=subject_type,
        )
        obj_id = self.get_or_create_symbolic_node(
            agent_instance=agent_instance,
            entity_name=object_name,
            entity_type=object_type,
        )

        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO symbolic_triples (
                    agent_instance, subject_id, predicate, object_id,
                    confidence, source_ref, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(agent_instance, subject_id, predicate, object_id, source_ref)
                DO UPDATE SET confidence = excluded.confidence, status = excluded.status
                """,
                (
                    agent_instance,
                    subj_id,
                    clean_pred,
                    obj_id,
                    confidence,
                    clean_ref,
                    status,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            self.conn.commit()
            triple_id = cursor.lastrowid
            logger.debug(
                "Symbolic triple saved id=%s (%s -[%s]-> %s) source=%s",
                triple_id,
                subject_name,
                clean_pred,
                object_name,
                clean_ref,
            )
            return int(triple_id)

    def list_symbolic_triples(
        self,
        *,
        agent_instance: str,
        limit: int = 100,
        status: Optional[str] = None,
        subject_name: Optional[str] = None,
        predicate: Optional[str] = None,
        object_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Lists symbolic triples with resolved node names."""
        self._init_symbolic_graph_schema()
        with self._lock:
            cursor = self.conn.cursor()
            query = """
                SELECT
                    t.id,
                    t.agent_instance,
                    ns.entity_name AS subject,
                    ns.entity_type AS subject_type,
                    t.predicate,
                    no.entity_name AS object,
                    no.entity_type AS object_type,
                    t.confidence,
                    t.source_ref,
                    t.status,
                    t.created_at
                FROM symbolic_triples t
                JOIN symbolic_nodes ns ON t.subject_id = ns.id
                JOIN symbolic_nodes no ON t.object_id = no.id
                WHERE t.agent_instance = ?
            """
            params: List[Any] = [agent_instance]

            if status:
                query += " AND t.status = ?"
                params.append(status)
            if subject_name:
                query += " AND ns.entity_name = ?"
                params.append(subject_name)
            if predicate:
                query += " AND t.predicate = ?"
                params.append(predicate)
            if object_name:
                query += " AND no.entity_name = ?"
                params.append(object_name)

            query += " ORDER BY t.id DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def query_causal_neighborhood(
        self,
        *,
        agent_instance: str,
        start_node_name: str,
        max_depth: int = 2,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Traverses causal and associative paths starting from a node using recursive SQL."""
        self._init_symbolic_graph_schema()
        with self._lock:
            cursor = self.conn.cursor()
            query = """
                WITH RECURSIVE graph_path(subject_id, predicate, object_id, confidence, source_ref, depth, path_str) AS (
                    SELECT
                        t.subject_id,
                        t.predicate,
                        t.object_id,
                        t.confidence,
                        t.source_ref,
                        1 AS depth,
                        CAST(t.subject_id AS TEXT) || '->' || CAST(t.object_id AS TEXT)
                    FROM symbolic_triples t
                    JOIN symbolic_nodes n ON t.subject_id = n.id
                    WHERE t.agent_instance = ? AND n.entity_name = ? AND t.status != 'rejected'

                    UNION ALL

                    SELECT
                        t.subject_id,
                        t.predicate,
                        t.object_id,
                        t.confidence * gp.confidence,
                        t.source_ref,
                        gp.depth + 1,
                        gp.path_str || '->' || CAST(t.object_id AS TEXT)
                    FROM symbolic_triples t
                    JOIN graph_path gp ON t.subject_id = gp.object_id
                    WHERE t.agent_instance = ?
                      AND gp.depth < ?
                      AND gp.path_str NOT LIKE '%' || CAST(t.object_id AS TEXT) || '%'
                      AND t.status != 'rejected'
                )
                SELECT
                    gp.depth,
                    ns.entity_name AS subject,
                    gp.predicate,
                    no.entity_name AS object,
                    gp.confidence,
                    gp.source_ref,
                    gp.path_str
                FROM graph_path gp
                JOIN symbolic_nodes ns ON gp.subject_id = ns.id
                JOIN symbolic_nodes no ON gp.object_id = no.id
                ORDER BY gp.depth ASC, gp.confidence DESC
                LIMIT ?
            """
            cursor.execute(query, (agent_instance, start_node_name, agent_instance, max_depth, limit))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_symbolic_graph_stats(self, *, agent_instance: str) -> Dict[str, Any]:
        """Returns statistics on nodes, triples, predicates, and evidence coverage."""
        self._init_symbolic_graph_schema()
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM symbolic_nodes WHERE agent_instance = ?",
                (agent_instance,),
            )
            node_count = int(cursor.fetchone()[0])

            cursor.execute(
                """
                SELECT status, COUNT(*) as count
                FROM symbolic_triples
                WHERE agent_instance = ?
                GROUP BY status
                """,
                (agent_instance,),
            )
            status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

            cursor.execute(
                """
                SELECT predicate, COUNT(*) as count
                FROM symbolic_triples
                WHERE agent_instance = ?
                GROUP BY predicate
                ORDER BY count DESC LIMIT 10
                """,
                (agent_instance,),
            )
            top_predicates = [{row["predicate"]: row["count"]} for row in cursor.fetchall()]

            return {
                "total_nodes": node_count,
                "total_triples": sum(status_counts.values()),
                "status_breakdown": status_counts,
                "top_predicates": top_predicates,
            }
