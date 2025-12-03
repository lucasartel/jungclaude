#!/usr/bin/env python3
"""
profile_gap_analyzer.py - Analisador de Gaps em Perfis Psicométricos
====================================================================

Identifica lacunas na análise psicométrica para guiar perguntas estratégicas
do sistema proativo.

Autor: Sistema Jung
Data: 2025-12-03
Versão: 1.0.0
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class ProfileGapAnalyzer:
    """
    Analisa lacunas (gaps) em perfis psicométricos para guiar
    o sistema proativo de perfilamento conversacional.
    """

    # Thresholds
    MIN_CONVERSATIONS_PER_DIMENSION = 3
    MIN_CONFIDENCE_SCORE = 70  # 0-100
    MIN_CONTEXT_VARIETY = 2  # Número mínimo de contextos diferentes

    # Contextos de vida importantes
    LIFE_CONTEXTS = [
        "trabalho",
        "carreira",
        "relacionamentos",
        "família",
        "amigos",
        "hobbies",
        "lazer",
        "valores",
        "ética",
        "passado",
        "infância",
        "futuro",
        "sonhos",
        "desafios",
        "conflitos"
    ]

    # Palavras-chave por dimensão Big Five
    DIMENSION_KEYWORDS = {
        "openness": [
            "criatividade", "curiosidade", "imaginação", "arte", "música",
            "novo", "mudança", "experiência", "aprender", "explorar",
            "abstrato", "filosófico", "cultural", "viagem", "diferente"
        ],
        "conscientiousness": [
            "organização", "planejamento", "disciplina", "responsabilidade",
            "prazo", "compromisso", "objetivo", "meta", "projeto", "tarefa",
            "estrutura", "método", "sistema", "ordem", "controle"
        ],
        "extraversion": [
            "pessoas", "social", "festa", "amigos", "grupo", "conversa",
            "energia", "ativo", "falar", "compartilhar", "interação",
            "público", "evento", "network", "conexão"
        ],
        "agreeableness": [
            "ajudar", "cooperar", "empatia", "gentil", "compreensão",
            "conflito", "harmonia", "acordo", "perdoar", "apoiar",
            "generoso", "confiança", "colaborar", "cuidar", "bondade"
        ],
        "neuroticism": [
            "ansiedade", "preocupação", "estresse", "medo", "nervoso",
            "calma", "estável", "emocional", "pressão", "tensão",
            "sensível", "resiliente", "lidar", "reagir", "sentir"
        ]
    }

    def __init__(self, db):
        """
        Args:
            db: DatabaseManager instance
        """
        self.db = db

    def analyze_gaps(self, user_id: str) -> Dict:
        """
        Analisa gaps completos no perfil do usuário

        Args:
            user_id: ID do usuário

        Returns:
            {
                "overall_completeness": float,  # 0-1
                "dimension_completeness": {
                    "openness": float,
                    "conscientiousness": float,
                    ...
                },
                "missing_contexts": List[str],
                "low_confidence_dimensions": List[str],
                "priority_questions": List[Dict],
                "recommendations": List[str]
            }
        """

        logger.info(f"🔍 [GAP ANALYZER] Analisando gaps para usuário {user_id[:8]}...")

        # Buscar dados
        psychometrics = self.db.get_psychometrics(user_id)
        conversations = self.db.get_user_conversations(user_id, limit=100)

        if not psychometrics:
            logger.warning(f"⚠️  Sem análise psicométrica para {user_id}")
            return self._empty_result("no_analysis")

        if len(conversations) < 5:
            logger.warning(f"⚠️  Conversas insuficientes ({len(conversations)}/5)")
            return self._empty_result("insufficient_conversations")

        # Calcular completude por dimensão
        dimension_completeness = {}
        for dimension in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            completeness = self._calculate_dimension_completeness(
                dimension=dimension,
                conversations=conversations,
                psychometrics=psychometrics
            )
            dimension_completeness[dimension] = completeness

        # Completude geral
        overall_completeness = sum(dimension_completeness.values()) / 5

        # Identificar dimensões com baixa confiança
        low_confidence_dimensions = self._identify_low_confidence_dimensions(
            psychometrics=psychometrics
        )

        # Identificar contextos faltantes
        missing_contexts = self._identify_missing_contexts(
            conversations=conversations
        )

        # Gerar perguntas prioritárias
        priority_questions = self._generate_priority_questions(
            dimension_completeness=dimension_completeness,
            low_confidence_dimensions=low_confidence_dimensions,
            missing_contexts=missing_contexts
        )

        # Recomendações
        recommendations = self._generate_recommendations(
            overall_completeness=overall_completeness,
            dimension_completeness=dimension_completeness,
            missing_contexts=missing_contexts
        )

        result = {
            "overall_completeness": round(overall_completeness, 2),
            "dimension_completeness": {k: round(v, 2) for k, v in dimension_completeness.items()},
            "missing_contexts": missing_contexts[:5],  # Top 5
            "low_confidence_dimensions": low_confidence_dimensions,
            "priority_questions": priority_questions[:3],  # Top 3
            "recommendations": recommendations,
            "metadata": {
                "num_conversations": len(conversations),
                "analysis_version": psychometrics.get('version', 1),
                "analyzed_at": datetime.now().isoformat()
            }
        }

        logger.info(f"✅ Completude geral: {overall_completeness:.1%}")
        logger.info(f"   Dimensões com gap: {[d for d, c in dimension_completeness.items() if c < 0.7]}")
        logger.info(f"   Contextos faltantes: {missing_contexts[:3]}")

        return result

    def _calculate_dimension_completeness(
        self,
        dimension: str,
        conversations: List[Dict],
        psychometrics: Dict
    ) -> float:
        """
        Calcula completude de uma dimensão Big Five

        Fatores considerados:
        1. Número de conversas relacionadas (40%)
        2. Confiança do score (30%)
        3. Variedade de contextos (30%)

        Returns:
            float: 0-1
        """

        # Fator 1: Conversas relacionadas
        related_conversations = self._count_related_conversations(
            dimension=dimension,
            conversations=conversations
        )

        conv_score = min(related_conversations / self.MIN_CONVERSATIONS_PER_DIMENSION, 1.0)

        # Fator 2: Confiança do score
        confidence = psychometrics.get('big_five_confidence', 50) / 100
        confidence_score = confidence

        # Fator 3: Variedade de contextos
        contexts_covered = self._count_contexts_covered(
            dimension=dimension,
            conversations=conversations
        )

        context_score = min(contexts_covered / self.MIN_CONTEXT_VARIETY, 1.0)

        # Média ponderada
        completeness = (
            conv_score * 0.4 +
            confidence_score * 0.3 +
            context_score * 0.3
        )

        logger.debug(f"   {dimension}: {completeness:.2f} (convs={conv_score:.2f}, conf={confidence_score:.2f}, ctx={context_score:.2f})")

        return completeness

    def _count_related_conversations(
        self,
        dimension: str,
        conversations: List[Dict]
    ) -> int:
        """
        Conta conversas relacionadas a uma dimensão

        Busca por palavras-chave da dimensão nas conversas
        """

        keywords = self.DIMENSION_KEYWORDS.get(dimension, [])
        count = 0

        for conv in conversations:
            user_input = conv.get('user_input', '').lower()

            # Verificar se contém alguma palavra-chave
            if any(keyword in user_input for keyword in keywords):
                count += 1

        return count

    def _count_contexts_covered(
        self,
        dimension: str,
        conversations: List[Dict]
    ) -> int:
        """
        Conta quantos contextos de vida diferentes foram abordados
        """

        contexts_found = set()

        for conv in conversations:
            user_input = conv.get('user_input', '').lower()

            for context in self.LIFE_CONTEXTS:
                if context in user_input:
                    contexts_found.add(context)

        return len(contexts_found)

    def _identify_low_confidence_dimensions(
        self,
        psychometrics: Dict
    ) -> List[str]:
        """
        Identifica dimensões com confiança abaixo do threshold
        """

        low_confidence = []
        overall_confidence = psychometrics.get('big_five_confidence', 50)

        if overall_confidence < self.MIN_CONFIDENCE_SCORE:
            # Se confiança geral é baixa, todas as dimensões são suspeitas
            low_confidence = [
                "openness",
                "conscientiousness",
                "extraversion",
                "agreeableness",
                "neuroticism"
            ]

        return low_confidence

    def _identify_missing_contexts(
        self,
        conversations: List[Dict]
    ) -> List[str]:
        """
        Identifica contextos de vida não abordados nas conversas
        """

        contexts_covered = set()

        for conv in conversations:
            user_input = conv.get('user_input', '').lower()

            for context in self.LIFE_CONTEXTS:
                if context in user_input:
                    contexts_covered.add(context)

        missing = [ctx for ctx in self.LIFE_CONTEXTS if ctx not in contexts_covered]

        return missing

    def _generate_priority_questions(
        self,
        dimension_completeness: Dict,
        low_confidence_dimensions: List[str],
        missing_contexts: List[str]
    ) -> List[Dict]:
        """
        Gera lista de perguntas prioritárias ordenadas por importância

        Returns:
            [
                {
                    "dimension": "conscientiousness",
                    "priority": 0.9,
                    "reason": "Baixa completude (0.3)",
                    "suggested_context": "trabalho"
                },
                ...
            ]
        """

        priority_questions = []

        # Priorizar dimensões incompletas
        for dimension, completeness in dimension_completeness.items():
            if completeness < 0.7:
                priority = 1.0 - completeness  # Quanto menor completude, maior prioridade

                # Tentar sugerir contexto faltante
                suggested_context = missing_contexts[0] if missing_contexts else "geral"

                priority_questions.append({
                    "dimension": dimension,
                    "priority": round(priority, 2),
                    "reason": f"Baixa completude ({completeness:.1%})",
                    "suggested_context": suggested_context
                })

        # Priorizar dimensões de baixa confiança
        for dimension in low_confidence_dimensions:
            # Evitar duplicatas
            if not any(q['dimension'] == dimension for q in priority_questions):
                priority_questions.append({
                    "dimension": dimension,
                    "priority": 0.75,
                    "reason": "Baixa confiança geral",
                    "suggested_context": missing_contexts[0] if missing_contexts else "geral"
                })

        # Ordenar por prioridade (maior primeiro)
        priority_questions.sort(key=lambda x: x['priority'], reverse=True)

        return priority_questions

    def _generate_recommendations(
        self,
        overall_completeness: float,
        dimension_completeness: Dict,
        missing_contexts: List[str]
    ) -> List[str]:
        """
        Gera recomendações acionáveis
        """

        recommendations = []

        # Recomendação geral
        if overall_completeness < 0.5:
            recommendations.append(
                f"Perfil está {overall_completeness:.0%} completo. "
                "Recomenda-se fazer perguntas estratégicas para enriquecer análise."
            )
        elif overall_completeness < 0.7:
            recommendations.append(
                f"Perfil está {overall_completeness:.0%} completo. "
                "Algumas dimensões precisam de mais dados."
            )
        else:
            recommendations.append(
                f"Perfil está {overall_completeness:.0%} completo. "
                "Manutenção periódica recomendada."
            )

        # Dimensões específicas
        incomplete_dims = [d for d, c in dimension_completeness.items() if c < 0.6]
        if incomplete_dims:
            recommendations.append(
                f"Focar em: {', '.join(incomplete_dims)}"
            )

        # Contextos faltantes
        if missing_contexts:
            recommendations.append(
                f"Explorar contextos: {', '.join(missing_contexts[:3])}"
            )

        return recommendations

    def _empty_result(self, reason: str) -> Dict:
        """
        Retorna resultado vazio quando análise não é possível
        """

        return {
            "overall_completeness": 0.0,
            "dimension_completeness": {
                "openness": 0.0,
                "conscientiousness": 0.0,
                "extraversion": 0.0,
                "agreeableness": 0.0,
                "neuroticism": 0.0
            },
            "missing_contexts": self.LIFE_CONTEXTS,
            "low_confidence_dimensions": [],
            "priority_questions": [],
            "recommendations": [f"Análise impossível: {reason}"],
            "metadata": {
                "num_conversations": 0,
                "analysis_version": 0,
                "analyzed_at": datetime.now().isoformat(),
                "error": reason
            }
        }

    def get_next_strategic_dimension(self, user_id: str) -> Optional[str]:
        """
        Retorna a próxima dimensão que deve receber pergunta estratégica

        Método rápido para integração com sistema proativo

        Returns:
            str: "openness", "conscientiousness", etc.
            None: Se perfil está completo
        """

        gaps = self.analyze_gaps(user_id)

        if gaps["priority_questions"]:
            return gaps["priority_questions"][0]["dimension"]

        return None
