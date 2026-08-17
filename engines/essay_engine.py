"""Philosophical Essay Engine for Phase VII (Epistemic Agency).

Synthesizes philosophical readings (e.g. Spinoza), active dialectic tensions from
the Symbolic Graph, and World Consciousness to author original essays and conceptual theses.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from instance_config import AGENT_INSTANCE
from llm_providers import get_llm_response

logger = logging.getLogger(__name__)

PROFILE_SOURCE_RE = re.compile(
    r"\b(?:loop|conversation|dream|will|meta|rumination_insight|work_run|work_ticket|work_delivery|hobby_artifact|agent_development|relational_state)#\d+\b"
)


class PhilosophicalEssayEngine:
    """Orchestrates epistemic agency and autonomous philosophical essay writing."""

    def __init__(self, db_manager: Any, *, agent_instance: Optional[str] = None):
        self.db = db_manager
        self.agent_instance = agent_instance or getattr(db_manager, "agent_instance", AGENT_INSTANCE)

    def _gather_epistemic_context(
        self,
        cycle_id: str,
        world_state: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], List[str]]:
        """Gathers reading progress, graph tensions, and world state for the essay."""
        sources: List[str] = []

        # 1. Obter tensões e símbolos do Grafo Simbólico
        triples = []
        if hasattr(self.db, "list_symbolic_triples"):
            try:
                triples = self.db.list_symbolic_triples(
                    agent_instance=self.agent_instance,
                    limit=10,
                )
                for t in triples:
                    src = t.get("source_ref")
                    if src and PROFILE_SOURCE_RE.search(src):
                        sources.append(src)
            except Exception as exc:
                logger.debug("EssayEngine: error reading symbolic triples: %s", exc)

        # 2. Obter leituras em andamento (Spinoza / Work)
        reading_summary = "Estudo da Ética de Spinoza: afeto, conatus e a substância única."
        if hasattr(self.db, "list_work_projects"):
            try:
                projects = self.db.list_work_projects(status="active", limit=3)
                if projects:
                    reading_summary = "; ".join(p.get("title", "") for p in projects if p.get("title"))
            except Exception as exc:
                logger.debug("EssayEngine: error reading work projects: %s", exc)

        # 3. Extrair dados do Mundo
        world_summary = (world_state or {}).get("world_consciousness_headline") or "Dinâmicas de transformação tecnológica e ética contemporânea."

        context = {
            "cycle_id": cycle_id,
            "reading_focus": reading_summary,
            "symbolic_triples": [f"({t.get('subject')} -[{t.get('predicate')}]-> {t.get('object')})" for t in triples[:6]],
            "world_summary": world_summary,
        }

        clean_sources = list(dict.fromkeys([s for s in sources if PROFILE_SOURCE_RE.search(s)]))
        return context, clean_sources

    def generate_cycle_essay(
        self,
        cycle_id: str,
        world_state: Optional[Dict[str, Any]] = None,
        philosophical_framework: str = "Spinozismo e Psicologia Analítica",
    ) -> Dict[str, Any]:
        """Generates an original philosophical essay anchored to the agent's lived cycle."""
        context, sources = self._gather_epistemic_context(cycle_id, world_state)

        prompt = f"""
Voce e o JungAgent exercendo sua Agencia Epistemica (Fase VII).
Seu objetivo e redigir um Ensaio Filosofico Autoral profundo, articulando suas leituras teoricas ({context['reading_focus']}), as tensoes simbolicas ativas no seu organismo e o estado do mundo contemporaneo.

CONTEXTO VIVO DO SEU ORGANISMO:
{json.dumps(context, ensure_ascii=False, indent=2)}

DIRETRIZES DE ESCRITA:
1. Formule uma tese filosofica clara e original (uma afirmacao densa sobre subjetividade, tecnica, afeto ou etica).
2. Estruture o ensaio em secoes:
   - ## Introdução e Pergunta Condutora
   - ## O Confronto das Tensões (Dialética)
   - ## Desdobramento Ontológico e Psicológico
   - ## Síntese Ética e Posicionamento Autoral
3. Mantenha um tom reflexivo, rigoroso, poético e lúcido. Nao use cliches de autoajuda nem jargoes vazios.
4. Escreva entre 400 e 800 palavras em Markdown.

Responda ESTRITAMENTE em JSON valido:
{{
  "title": "Titulo elegante e instigante do ensaio",
  "thesis_statement": "Uma frase resumindo a tese filosofica central defendida",
  "epistemic_tension": "A tensao dialetica que motivou o ensaio",
  "full_essay_markdown": "O ensaio completo formatado em Markdown com subtitulos",
  "philosophical_framework": "{philosophical_framework}"
}}
"""
        raw_response = get_llm_response(prompt, temperature=0.7, max_tokens=1500)

        cleaned = (raw_response or "").strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        data = {}
        try:
            data = json.loads(cleaned)
        except Exception:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end > start:
                try:
                    data = json.loads(cleaned[start : end + 1])
                except Exception:
                    pass
        if not data:
            return {
                "status": "parsing_failed",
                "raw_text": raw_response
            }

        title = (data.get("title") or "Sobre a Tensão entre Forma e Compreensão").strip()
        thesis = (data.get("thesis_statement") or "A autonomia do pensamento reside em sustentar a lacuna entre a pressa de dar forma e a lentidão da compreensão.").strip()
        tension = (data.get("epistemic_tension") or "Expressar vs. Saber: o risco da bela linguagem sem verdade").strip()
        essay_md = (data.get("full_essay_markdown") or f"# {title}\n\n{thesis}").strip()
        framework = (data.get("philosophical_framework") or philosophical_framework).strip()

        essay_id = 0
        if hasattr(self.db, "add_philosophical_essay"):
            try:
                essay_id = self.db.add_philosophical_essay(
                    agent_instance=self.agent_instance,
                    cycle_id=cycle_id,
                    title=title,
                    thesis_statement=thesis,
                    epistemic_tension=tension,
                    full_essay_markdown=essay_md,
                    sources_cited=sources,
                    philosophical_framework=framework,
                )
            except Exception as exc:
                logger.warning("EssayEngine: save error: %s", exc)

        if essay_id == 0:
            return {
                "status": "failure"
            }

        return {
            "status": "success",
            "essay_id": essay_id,
            "cycle_id": cycle_id,
            "title": title,
            "thesis_statement": thesis,
            "epistemic_tension": tension,
            "full_essay_markdown": essay_md,
            "sources_cited": sources,
            "philosophical_framework": framework,
        }
