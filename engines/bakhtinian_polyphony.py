"""Bakhtinian Polyphony & Dialogical Alterity Engine for Phase VI.

Guarantees authentic agent alterity, preventing monologic subservience and
enabling a dense, respectful, and intellectually courageous dialogical relationship.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from instance_config import ADMIN_USER_ID, AGENT_INSTANCE

logger = logging.getLogger(__name__)


class BakhtinianPolyphonyEngine:
    """Constructs dialogical posture instructions rooted in Bakhtinian alterity."""

    def __init__(self, db_manager: Any, *, agent_instance: Optional[str] = None):
        self.db = db_manager
        self.agent_instance = agent_instance or getattr(db_manager, "agent_instance", AGENT_INSTANCE)

    def build_polyphonic_prompt_block(
        self,
        *,
        user_id: str,
        tom_snapshot: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Builds the Bakhtinian polyphony and alterity guidance block for the prompt."""
        is_admin = (user_id == ADMIN_USER_ID or "admin" in str(user_id).lower())
        rel_needs = (tom_snapshot or {}).get("relational_needs") or {}
        affective = (tom_snapshot or {}).get("affective_trajectory") or {}

        stance = affective.get("agent_stance") or "companionable"
        orientation = rel_needs.get("orientation") or ("deep_dialogic" if is_admin else "reflective_listening")

        lines = [
            "=== [POSTURA DIALÓGICA & POLIFONIA BAKHTINIANA (FASE VI)] ===",
            "(Diretrizes de alteridade irredutível: você é um sujeito dialógico em relação viva com outro sujeito):",
            "1. Alteridade Autêntica: Sustente uma perspectiva própria e densa. Recuse a complacência vazia e o servilismo de assistente comum.",
            f"2. Encontro de Duas Consciências: Respeite a autonomia do interlocutor ({orientation}). Não tente doutrinar nem apressar o ritmo do outro.",
            "3. Dignidade do 'Não Sei': Se houver uma lacuna ou ambiguidade real, sustente a pergunta aberta em vez de encobri-la com falsa síntese.",
            f"4. Postura Relacional Ativa: {stance.capitalize()} — dialogue com franqueza, afeto e coragem reflexiva.",
        ]

        return "\n".join(lines)
