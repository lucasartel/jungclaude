"""Evidence projection for WILL work that can replace a circadian pulse.

The v1 adapter deliberately supports full world snapshots only. An image or
a delivery acknowledgement alone cannot demonstrate equivalence to hobby.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from urllib.parse import urlparse

WORLD_FIELDS = (
    "cache_timestamp", "dominant_tensions", "atmosphere", "continuity_note",
    "stale_areas", "consensus_map", "divergence_map", "work_seeds", "hobby_seeds",
    "attention_profile", "will_bias_summary", "knowledge_gap",
    "knowledge_source_decision", "knowledge_resolution_summary", "knowledge_findings",
    "knowledge_seed", "knowledge_journal_entry", "epistemic_object",
    "epistemic_receipts", "epistemic_longitudinal_summary", "dynamic_queries",
)
SCOPE_FIELDS = ("agent_instance", "relation_id", "scope_kind", "user_id", "cycle_id")


def utc_time(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _http_url(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False


def world_evidence(snapshot, expected_areas):
    """Project the actual executor output; no new model call or paid work."""
    if not isinstance(snapshot, dict):
        return {}
    panels = snapshot.get("area_panels") or {}
    panels = panels if isinstance(panels, dict) else {}
    sources = {}
    for signal in snapshot.get("signals") or []:
        if not isinstance(signal, dict):
            continue
        area = signal.get("area_key")
        url = signal.get("source_url") or ""
        if area in expected_areas and _http_url(url):
            sources.setdefault(area, []).append(url)
    return {
        "version": 1, "kind": "world_snapshot", "captured_at": snapshot.get("cache_timestamp"),
        "expected_areas": sorted(expected_areas),
        "loaded_areas": sorted(key for key, panel in panels.items()
                               if isinstance(panel, dict)
                               and isinstance(panel.get("signal_count"), (int, float))
                               and panel["signal_count"] > 0),
        "source_urls": {key: list(dict.fromkeys(urls))[:5] for key, urls in sources.items()},
        "confidence": snapshot.get("confidence_overall"),
        "world_state": {key: snapshot.get(key) for key in WORLD_FIELDS},
    }


def validate_evidence(evidence, capability_key, now):
    if not isinstance(evidence, dict) or capability_key != "saber_world_refresh" or evidence.get("version") != 1:
        return None
    if evidence.get("kind") != "world_snapshot":
        return None
    captured = utc_time(evidence.get("captured_at"))
    current = utc_time(now)
    if not captured or not current or captured > current or (current - captured).total_seconds() >= 86400:
        return None
    expected = evidence.get("expected_areas")
    loaded = evidence.get("loaded_areas")
    sources = evidence.get("source_urls")
    world = evidence.get("world_state")
    if (not isinstance(expected, list) or not expected or not all(isinstance(x, str) and x for x in expected)
            or not isinstance(loaded, list) or not all(isinstance(x, str) for x in loaded)
            or set(expected) != set(loaded) or len(expected) != len(set(expected))
            or len(loaded) != len(set(loaded))
            or not isinstance(sources, dict) or not isinstance(world, dict)):
        return None
    if world.get("stale_areas") != [] or utc_time(world.get("cache_timestamp")) != captured:
        return None
    for area in expected:
        urls = sources.get(area)
        if not isinstance(urls, list) or not urls:
            return None
        for url in urls:
            if not _http_url(url):
                return None
    if isinstance(evidence.get("confidence"), bool):
        return None
    try:
        quality = float(evidence.get("confidence"))
    except (ValueError, TypeError):
        return None
    # Reuse World's medium-lucidity boundary, but never treat it as semantic truth.
    if not math.isfinite(quality) or not 0.54 <= quality <= 1:
        return None
    tensions = world.get("dominant_tensions")
    if not isinstance(tensions, list) or not tensions or not all(isinstance(x, str) for x in tensions):
        return None
    for key in ("work_seeds", "hobby_seeds"):
        if not isinstance(world.get(key), list) or not all(isinstance(x, str) for x in world[key]):
            return None
    summary = "World atualizado: " + ", ".join(tensions[:2]) + "."
    return {
        "phase": "world", "quality": quality, "captured_at": captured,
        "output_summary": summary,
        "world_state": world,
        "metrics": {
            "world_areas_loaded": len(expected), "stale_area_count": 0,
            "confidence_overall": quality,
            "work_seed_count": len(world.get("work_seeds") or []),
            "hobby_seed_count": len(world.get("hobby_seeds") or []),
        },
    }
