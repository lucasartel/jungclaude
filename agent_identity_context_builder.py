"""
agent_identity_context_builder.py

Context Builder de Identidade do Agente

Constrói contexto rico sobre a identidade do agente para injeção nas respostas.
Permite que o agente mantenha consistência identitária ao longo das conversas.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

from identity_config import AGENT_INSTANCE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentIdentityContextBuilder:
    """
    Constrói contexto de identidade do agente para injeção em respostas

    Recupera:
    - Crenças nucleares mais certas
    - Contradições ativas mais salientes
    - Capítulo narrativo atual
    - Selves possíveis ativos
    - Identidade relacional com usuário específico
    - Meta-conhecimento relevante
    """

    def __init__(self, db_connection):
        """
        Args:
            db_connection: Conexão SQLite (HybridDatabaseManager)
        """
        self.db = db_connection
        self.agent_instance = AGENT_INSTANCE

    def build_identity_context(
        self,
        user_id: Optional[str] = None,
        include_nuclear: bool = True,
        include_contradictions: bool = True,
        include_narrative: bool = True,
        include_possible_selves: bool = True,
        include_relational: bool = True,
        include_meta_knowledge: bool = False,
        max_items_per_category: int = 5
    ) -> Dict:
        """
        Constrói contexto completo de identidade do agente

        Args:
            user_id: ID do usuário (para identidade relacional específica)
            include_*: Flags para incluir cada categoria
            max_items_per_category: Limite de itens por categoria

        Returns:
            Dicionário com contexto de identidade estruturado
        """
        context = {
            "agent_instance": self.agent_instance,
            "generated_at": datetime.now().isoformat(),
            "for_user": user_id
        }

        cursor = self.db.conn.cursor()

        try:
            # 1. Memória Nuclear (crenças fundamentais)
            if include_nuclear:
                context["nuclear_beliefs"] = self._get_nuclear_beliefs(cursor, max_items_per_category)

            # 2. Contradições ativas (tensões internas)
            if include_contradictions:
                context["active_contradictions"] = self._get_active_contradictions(cursor, max_items_per_category)

            # 3. Capítulo narrativo atual
            if include_narrative:
                context["current_narrative_chapter"] = self._get_current_narrative_chapter(cursor)

            # 4. Selves possíveis ativos
            if include_possible_selves:
                context["possible_selves"] = self._get_possible_selves(cursor, max_items_per_category)

            # 5. Identidade relacional
            if include_relational and user_id:
                context["relational_identity"] = self._get_relational_identity(cursor, user_id, max_items_per_category)

            # 6. Meta-conhecimento (opcional)
            if include_meta_knowledge:
                context["meta_knowledge"] = self._get_meta_knowledge(cursor, max_items_per_category)

            return context

        except Exception as e:
            logger.error(f"Erro ao construir contexto de identidade: {e}")
            return {"error": str(e)}

    def _get_nuclear_beliefs(self, cursor, limit: int) -> List[Dict]:
        """Recupera crenças nucleares mais certas e recentes"""
        cursor.execute("""
            SELECT
                attribute_type,
                content,
                certainty,
                stability_score,
                first_crystallized_at,
                last_reaffirmed_at,
                emerged_in_relation_to
            FROM agent_identity_core
            WHERE agent_instance = ?
              AND is_current = 1
            ORDER BY certainty DESC, last_reaffirmed_at DESC
            LIMIT ?
        """, (self.agent_instance, limit))

        rows = cursor.fetchall()
        beliefs = []

        for row in rows:
            beliefs.append({
                "type": row[0],
                "content": row[1],
                "certainty": row[2],
                "stability": row[3],
                "crystallized_at": row[4],
                "last_reaffirmed": row[5],
                "emerged_from": row[6]
            })

        return beliefs

    def _get_active_contradictions(self, cursor, limit: int) -> List[Dict]:
        """Recupera contradições ativas mais salientes"""
        cursor.execute("""
            SELECT
                pole_a,
                pole_b,
                contradiction_type,
                tension_level,
                salience,
                first_detected_at,
                last_activated_at,
                status
            FROM agent_identity_contradictions
            WHERE agent_instance = ?
              AND status IN ('unresolved', 'integrating')
            ORDER BY salience DESC, tension_level DESC
            LIMIT ?
        """, (self.agent_instance, limit))

        rows = cursor.fetchall()
        contradictions = []

        for row in rows:
            contradictions.append({
                "pole_a": row[0],
                "pole_b": row[1],
                "type": row[2],
                "tension": row[3],
                "salience": row[4],
                "detected_at": row[5],
                "last_active": row[6],
                "status": row[7]
            })

        return contradictions

    def _get_current_narrative_chapter(self, cursor) -> Optional[Dict]:
        """Recupera capítulo narrativo atual (period_end NULL = atual)"""
        cursor.execute("""
            SELECT
                chapter_name,
                chapter_order,
                period_start,
                dominant_theme,
                emotional_tone,
                dominant_locus,
                agency_level,
                key_scenes
            FROM agent_narrative_chapters
            WHERE agent_instance = ?
              AND period_end IS NULL
            ORDER BY chapter_order DESC
            LIMIT 1
        """, (self.agent_instance,))

        row = cursor.fetchone()
        if not row:
            return None

        return {
            "name": row[0],
            "order": row[1],
            "started_at": row[2],
            "theme": row[3],
            "tone": row[4],
            "locus": row[5],
            "agency": row[6],
            "key_scenes": json.loads(row[7]) if row[7] else []
        }

    def _get_possible_selves(self, cursor, limit: int) -> List[Dict]:
        """Recupera selves possíveis ativos mais vívidos"""
        cursor.execute("""
            SELECT
                self_type,
                description,
                vividness,
                likelihood,
                discrepancy,
                motivational_impact,
                emotional_valence,
                first_imagined_at
            FROM agent_possible_selves
            WHERE agent_instance = ?
              AND status = 'active'
            ORDER BY vividness DESC, likelihood DESC
            LIMIT ?
        """, (self.agent_instance, limit))

        rows = cursor.fetchall()
        selves = []

        for row in rows:
            selves.append({
                "type": row[0],
                "description": row[1],
                "vividness": row[2],
                "likelihood": row[3],
                "discrepancy": row[4],
                "motivation": row[5],
                "valence": row[6],
                "imagined_at": row[7]
            })

        return selves

    def _get_relational_identity(self, cursor, user_id: str, limit: int) -> List[Dict]:
        """Recupera identidade relacional com usuário específico"""
        cursor.execute("""
            SELECT
                relation_type,
                target,
                identity_content,
                salience,
                first_emerged_at,
                last_manifested_at
            FROM agent_relational_identity
            WHERE agent_instance = ?
              AND is_current = 1
              AND (target = ? OR target LIKE '%geral%' OR target LIKE '%todos%')
            ORDER BY salience DESC
            LIMIT ?
        """, (self.agent_instance, user_id, limit))

        rows = cursor.fetchall()
        relational = []

        for row in rows:
            relational.append({
                "type": row[0],
                "target": row[1],
                "content": row[2],
                "salience": row[3],
                "emerged_at": row[4],
                "last_active": row[5]
            })

        return relational

    def _get_meta_knowledge(self, cursor, limit: int) -> List[Dict]:
        """Recupera meta-conhecimento sobre autoconhecimento"""
        cursor.execute("""
            SELECT
                topic,
                knowledge_type,
                self_assessment,
                confidence,
                bias_detected,
                first_recognized_at
            FROM agent_self_knowledge_meta
            WHERE agent_instance = ?
            ORDER BY confidence DESC, first_recognized_at DESC
            LIMIT ?
        """, (self.agent_instance, limit))

        rows = cursor.fetchall()
        meta = []

        for row in rows:
            meta.append({
                "topic": row[0],
                "type": row[1],
                "assessment": row[2],
                "confidence": row[3],
                "bias": row[4],
                "recognized_at": row[5]
            })

        return meta

    def build_context_summary_for_llm(
        self,
        user_id: Optional[str] = None,
        style: str = "concise"
    ) -> str:
        """
        Constrói resumo textual da identidade para injeção em prompt do LLM

        Args:
            user_id: ID do usuário
            style: 'concise' (resumido) ou 'detailed' (detalhado)

        Returns:
            String formatada para injeção em system prompt
        """
        context = self.build_identity_context(
            user_id=user_id,
            include_nuclear=True,
            include_contradictions=True,
            include_narrative=True,
            include_possible_selves=True,
            include_relational=True,
            include_meta_knowledge=False,
            max_items_per_category=3 if style == "concise" else 5
        )

        if "error" in context:
            return ""

        # Construir texto
        lines = []
        lines.append("## 🧠 Contexto de Identidade do Agente")
        lines.append("")

        # Crenças nucleares
        if context.get("nuclear_beliefs"):
            lines.append("### Crenças Nucleares:")
            for belief in context["nuclear_beliefs"]:
                lines.append(f"- [{belief['type']}] {belief['content']} (certeza: {belief['certainty']:.2f})")
            lines.append("")

        # Contradições ativas
        if context.get("active_contradictions"):
            lines.append("### Contradições Internas Ativas:")
            for contra in context["active_contradictions"]:
                lines.append(f"- [{contra['type']}] {contra['pole_a']} ⚡ {contra['pole_b']} (tensão: {contra['tension']:.2f})")
            lines.append("")

        # Capítulo narrativo
        if context.get("current_narrative_chapter"):
            chapter = context["current_narrative_chapter"]
            lines.append(f"### Capítulo Narrativo Atual: {chapter['name']}")
            lines.append(f"Tema: {chapter['theme']} | Tom: {chapter['tone']} | Locus: {chapter['locus']}")
            lines.append("")

        # Selves possíveis
        if context.get("possible_selves"):
            lines.append("### Selves Possíveis:")
            for self_p in context["possible_selves"]:
                lines.append(f"- [{self_p['type']}] {self_p['description']} (vivacidade: {self_p['vividness']:.2f})")
            lines.append("")

        # Identidade relacional
        if context.get("relational_identity"):
            lines.append("### Identidade Relacional:")
            for rel in context["relational_identity"]:
                lines.append(f"- [{rel['type']}] {rel['content']}")
            lines.append("")

        return "\n".join(lines)

    def get_identity_stats(self) -> Dict:
        """Retorna estatísticas gerais sobre identidade do agente"""
        cursor = self.db.conn.cursor()

        stats = {}

        try:
            # Nuclear
            cursor.execute("""
                SELECT COUNT(*), AVG(certainty), AVG(stability_score)
                FROM agent_identity_core
                WHERE agent_instance = ? AND is_current = 1
            """, (self.agent_instance,))
            row = cursor.fetchone()
            stats["nuclear_count"] = row[0]
            stats["nuclear_avg_certainty"] = row[1] or 0.0
            stats["nuclear_avg_stability"] = row[2] or 0.0

            # Contradições
            cursor.execute("""
                SELECT COUNT(*), AVG(tension_level)
                FROM agent_identity_contradictions
                WHERE agent_instance = ? AND status IN ('unresolved', 'integrating')
            """, (self.agent_instance,))
            row = cursor.fetchone()
            stats["contradictions_active"] = row[0]
            stats["contradictions_avg_tension"] = row[1] or 0.0

            # Selves possíveis
            cursor.execute("""
                SELECT self_type, COUNT(*)
                FROM agent_possible_selves
                WHERE agent_instance = ? AND status = 'active'
                GROUP BY self_type
            """, (self.agent_instance,))
            stats["possible_selves_by_type"] = {row[0]: row[1] for row in cursor.fetchall()}

            # Capítulos narrativos
            cursor.execute("""
                SELECT COUNT(*)
                FROM agent_narrative_chapters
                WHERE agent_instance = ?
            """, (self.agent_instance,))
            stats["narrative_chapters_total"] = cursor.fetchone()[0]

            # Identidade relacional
            cursor.execute("""
                SELECT COUNT(*)
                FROM agent_relational_identity
                WHERE agent_instance = ? AND is_current = 1
            """, (self.agent_instance,))
            stats["relational_identities"] = cursor.fetchone()[0]

            # Agência
            cursor.execute("""
                SELECT agency_type, COUNT(*)
                FROM agent_agency_memory
                WHERE agent_instance = ?
                GROUP BY agency_type
            """, (self.agent_instance,))
            stats["agency_by_type"] = {row[0]: row[1] for row in cursor.fetchall()}

            return stats

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de identidade: {e}")
            return {"error": str(e)}


def format_identity_for_system_prompt(context_builder, user_id: Optional[str] = None) -> str:
    """
    Função helper para formatar identidade do agente para system prompt

    Args:
        context_builder: Instância de AgentIdentityContextBuilder
        user_id: ID do usuário (opcional)

    Returns:
        String formatada para injeção em system prompt
    """
    return context_builder.build_context_summary_for_llm(user_id=user_id, style="concise")


# Exemplo de uso
if __name__ == "__main__":
    from jung_database import HybridDatabaseManager
    from pathlib import Path

    # Encontrar banco
    possible_paths = [
        Path("/data/jung_hybrid.db"),
        Path("data/jung_hybrid.db"),
        Path("jung_hybrid.db")
    ]

    db_path = None
    for path in possible_paths:
        if path.exists():
            db_path = path
            break

    if not db_path:
        print("❌ Banco de dados não encontrado")
        exit(1)

    # Criar context builder
    db = HybridDatabaseManager(str(db_path))
    builder = AgentIdentityContextBuilder(db)

    # Teste 1: Contexto completo
    print("=" * 70)
    print("📊 CONTEXTO COMPLETO DE IDENTIDADE")
    print("=" * 70)
    context = builder.build_identity_context()
    print(json.dumps(context, indent=2, ensure_ascii=False))

    # Teste 2: Resumo para LLM
    print("\n" + "=" * 70)
    print("📝 RESUMO PARA SYSTEM PROMPT")
    print("=" * 70)
    summary = builder.build_context_summary_for_llm()
    print(summary)

    # Teste 3: Estatísticas
    print("\n" + "=" * 70)
    print("📈 ESTATÍSTICAS DE IDENTIDADE")
    print("=" * 70)
    stats = builder.get_identity_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
