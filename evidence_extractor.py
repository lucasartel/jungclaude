"""
evidence_extractor.py - Sistema de Extração de Evidências para Análises Psicométricas
======================================================================================

Extrai citações literais das conversas que embasam cada dimensão do Big Five.
Implementa abordagem híbrida: análise rápida + evidências on-demand.

Autor: Sistema Jung
Data: 2025-12-02
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Evidence:
    """Representa uma evidência que embasa um traço psicométrico"""
    conversation_id: int
    quote: str
    context_before: Optional[str]
    context_after: Optional[str]
    dimension: str  # 'openness', 'conscientiousness', etc.
    trait_indicator: str  # 'creativity', 'organization', etc.
    direction: str  # 'positive', 'negative', 'neutral'
    relevance_score: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    explanation: str
    conversation_timestamp: datetime
    is_ambiguous: bool = False


class EvidenceExtractor:
    """Extrai evidências das conversas para cada dimensão do Big Five"""

    # Mapa de dimensões para trait indicators
    DIMENSION_TRAITS = {
        'openness': ['creativity', 'curiosity', 'imagination', 'routine_preference', 'tradition'],
        'conscientiousness': ['organization', 'planning', 'discipline', 'spontaneity', 'flexibility'],
        'extraversion': ['sociability', 'energy', 'talkativeness', 'reserved', 'introspection'],
        'agreeableness': ['empathy', 'cooperation', 'trust', 'competitiveness', 'directness'],
        'neuroticism': ['anxiety', 'emotional_stability', 'sensitivity', 'calmness', 'resilience']
    }

    def __init__(self, db_manager, llm_provider):
        """
        Args:
            db_manager: Instância do DatabaseManager (jung_core)
            llm_provider: Provider de LLM (Claude)
        """
        self.db = db_manager
        self.llm = llm_provider

    def extract_evidence_for_user(
        self,
        user_id: str,
        psychometric_version: int,
        conversations: List[Dict],
        big_five_scores: Dict
    ) -> Dict[str, List[Evidence]]:
        """
        Extrai evidências para todas as dimensões do Big Five

        Args:
            user_id: ID do usuário
            psychometric_version: Versão da análise psicométrica
            conversations: Lista de conversas do usuário
            big_five_scores: Scores do Big Five já calculados

        Returns:
            Dict com dimensões como chaves e listas de Evidence como valores
        """
        logger.info(f"🔍 Extraindo evidências para {user_id} (v{psychometric_version})")

        all_evidence = {}

        for dimension in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
            logger.info(f"  Extraindo evidências para {dimension}...")

            evidence_list = self._extract_dimension_evidence(
                dimension=dimension,
                conversations=conversations,
                expected_score=big_five_scores.get(dimension, {}).get('score', 50)
            )

            all_evidence[dimension] = evidence_list

            logger.info(f"    ✓ {len(evidence_list)} evidências encontradas")

        return all_evidence

    def _extract_dimension_evidence(
        self,
        dimension: str,
        conversations: List[Dict],
        expected_score: int
    ) -> List[Evidence]:
        """
        Extrai evidências para uma dimensão específica

        Args:
            dimension: Nome da dimensão ('openness', etc.)
            conversations: Lista de conversas
            expected_score: Score esperado (0-100) para contexto

        Returns:
            Lista de objetos Evidence
        """

        # Formatar conversas com IDs para rastreabilidade
        conversations_formatted = self._format_conversations_with_ids(conversations)

        # Criar prompt para Claude
        prompt = self._create_evidence_extraction_prompt(
            dimension=dimension,
            conversations_formatted=conversations_formatted,
            expected_score=expected_score
        )

        try:
            # Chamar Claude para extrair evidências
            response = self.llm.get_response(prompt, temperature=0.3, max_tokens=2000)

            # Parse JSON robusto
            evidence_data = self._parse_json_response(response)

            # Converter para objetos Evidence
            evidence_list = []
            for item in evidence_data.get('evidence', []):
                try:
                    conv_id = item['conversation_id']
                    conv = next((c for c in conversations if c['id'] == conv_id), None)

                    if not conv:
                        logger.warning(f"Conversa ID {conv_id} não encontrada, pulando evidência")
                        continue

                    evidence = Evidence(
                        conversation_id=conv_id,
                        quote=item['quote'],
                        context_before=item.get('context_before'),
                        context_after=item.get('context_after'),
                        dimension=dimension,
                        trait_indicator=item.get('trait_indicator', 'general'),
                        direction=item.get('direction', 'positive'),
                        relevance_score=item.get('relevance', 0.5),
                        confidence=item.get('confidence', 0.5),
                        explanation=item.get('explanation', ''),
                        conversation_timestamp=datetime.fromisoformat(conv['timestamp']),
                        is_ambiguous=item.get('is_ambiguous', False)
                    )

                    evidence_list.append(evidence)

                except Exception as e:
                    logger.error(f"Erro ao processar evidência: {e}")
                    continue

            return evidence_list

        except Exception as e:
            logger.error(f"Erro ao extrair evidências para {dimension}: {e}")
            return []

    def _format_conversations_with_ids(self, conversations: List[Dict]) -> str:
        """Formata conversas incluindo IDs para rastreabilidade"""
        formatted = []

        for conv in conversations:
            formatted.append(f"""[ID: {conv['id']}]
Timestamp: {conv['timestamp']}
Usuário: {conv['user_input']}
Jung: {conv['ai_response'][:150]}...
---""")

        return "\n\n".join(formatted)

    def _create_evidence_extraction_prompt(
        self,
        dimension: str,
        conversations_formatted: str,
        expected_score: int
    ) -> str:
        """Cria prompt para extração de evidências"""

        dimension_info = {
            'openness': {
                'name': 'Abertura à Experiência (Openness)',
                'high': 'criativo, curioso, busca novidades, imaginativo',
                'low': 'prático, tradicional, prefere rotina, convencional',
                'traits': ['criatividade', 'curiosidade', 'imaginação', 'preferência por rotina']
            },
            'conscientiousness': {
                'name': 'Conscienciosidade (Conscientiousness)',
                'high': 'organizado, planejado, disciplinado, responsável',
                'low': 'espontâneo, flexível, improvisador, menos estruturado',
                'traits': ['organização', 'planejamento', 'disciplina', 'espontaneidade']
            },
            'extraversion': {
                'name': 'Extroversão (Extraversion)',
                'high': 'social, energético, falante, busca estimulação',
                'low': 'reservado, independente, introspectivo, prefere solidão',
                'traits': ['sociabilidade', 'energia', 'comunicação', 'introspecção']
            },
            'agreeableness': {
                'name': 'Amabilidade (Agreeableness)',
                'high': 'empático, cooperativo, altruísta, confiante',
                'low': 'analítico, competitivo, direto, cético',
                'traits': ['empatia', 'cooperação', 'confiança', 'competitividade']
            },
            'neuroticism': {
                'name': 'Neuroticismo (Neuroticism)',
                'high': 'ansioso, emocionalmente reativo, sensível, preocupado',
                'low': 'calmo, estável, resiliente, equilibrado',
                'traits': ['ansiedade', 'estabilidade emocional', 'sensibilidade', 'resiliência']
            }
        }

        info = dimension_info[dimension]

        prompt = f"""Você é um psicólogo especializado em análise de personalidade Big Five.

TAREFA: Extrair CITAÇÕES LITERAIS das conversas que são evidências de **{info['name']}**.

CONTEXTO:
- Esta dimensão teve score de {expected_score}/100 na análise anterior
- Score alto ({expected_score} > 60): {info['high']}
- Score baixo ({expected_score} < 40): {info['low']}
- Traits relevantes: {', '.join(info['traits'])}

CONVERSAS:
{conversations_formatted}

INSTRUÇÕES:
1. Para cada conversa, identifique citações do USUÁRIO que são evidências claras desta dimensão
2. Apenas citações EXPLÍCITAS e DIRETAS - não inferências vagas
3. Para cada evidência, indique:
   - conversation_id: ID da conversa
   - quote: Citação literal do usuário
   - context_before: Mensagem anterior (se relevante para contexto)
   - context_after: Mensagem posterior (se relevante para contexto)
   - trait_indicator: Qual trait específico ({', '.join(info['traits'])})
   - direction: "positive" (aumenta score) ou "negative" (diminui score)
   - relevance: 0.0-1.0 (quão relevante é essa evidência)
   - confidence: 0.0-1.0 (quão confiante você está)
   - is_ambiguous: true/false (se a evidência é ambígua)
   - explanation: Por que isso é evidência (1 frase)

CRITÉRIOS DE QUALIDADE:
- Priorize evidências FORTES (relevance > 0.7)
- Ignore menções superficiais ou contextos irrelevantes
- Se o usuário contradiz a si mesmo, marque como ambígua

FORMATO DE RESPOSTA (JSON válido):
{{
    "dimension": "{dimension}",
    "evidence": [
        {{
            "conversation_id": 123,
            "quote": "citação literal aqui",
            "context_before": "contexto anterior (opcional)",
            "context_after": "contexto posterior (opcional)",
            "trait_indicator": "creativity",
            "direction": "positive",
            "relevance": 0.85,
            "confidence": 0.90,
            "is_ambiguous": false,
            "explanation": "Usuário demonstra busca ativa por experiências criativas"
        }}
    ]
}}

IMPORTANTE: Retorne APENAS o JSON válido, sem markdown ou texto adicional."""

        return prompt

    def _parse_json_response(self, response: str) -> Dict:
        """Parse robusto de resposta JSON do LLM"""
        import re

        response = response.strip()

        # Remover markdown code blocks
        if response.startswith("```"):
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                response = match.group(1).strip()

        # Tentar remover texto antes do JSON
        if not response.startswith('{') and not response.startswith('['):
            json_start = min(
                response.find('{') if response.find('{') != -1 else len(response),
                response.find('[') if response.find('[') != -1 else len(response)
            )
            if json_start < len(response):
                response = response[json_start:]

        return json.loads(response)

    def save_evidence_to_db(
        self,
        user_id: str,
        psychometric_version: int,
        all_evidence: Dict[str, List[Evidence]]
    ) -> int:
        """
        Salva evidências no banco de dados

        Args:
            user_id: ID do usuário
            psychometric_version: Versão da análise
            all_evidence: Dict com evidências por dimensão

        Returns:
            Número total de evidências salvas
        """
        cursor = self.db.conn.cursor()
        total_saved = 0

        for dimension, evidence_list in all_evidence.items():
            for evidence in evidence_list:
                cursor.execute("""
                    INSERT INTO psychometric_evidence (
                        user_id,
                        psychometric_version,
                        conversation_id,
                        dimension,
                        trait_indicator,
                        quote,
                        context_before,
                        context_after,
                        relevance_score,
                        direction,
                        weight,
                        conversation_timestamp,
                        confidence,
                        is_ambiguous,
                        extraction_method,
                        explanation
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    psychometric_version,
                    evidence.conversation_id,
                    evidence.dimension,
                    evidence.trait_indicator,
                    evidence.quote,
                    evidence.context_before,
                    evidence.context_after,
                    evidence.relevance_score,
                    evidence.direction,
                    1.0,  # weight padrão
                    evidence.conversation_timestamp.isoformat(),
                    evidence.confidence,
                    1 if evidence.is_ambiguous else 0,
                    'claude_sonnet_4.5',
                    evidence.explanation
                ))

                total_saved += 1

        self.db.conn.commit()

        # Atualizar flag na tabela user_psychometrics
        cursor.execute("""
            UPDATE user_psychometrics
            SET evidence_extracted = 1,
                evidence_extraction_date = CURRENT_TIMESTAMP
            WHERE user_id = ? AND version = ?
        """, (user_id, psychometric_version))

        self.db.conn.commit()

        logger.info(f"✅ {total_saved} evidências salvas para {user_id}")

        return total_saved

    def get_evidence_for_dimension(
        self,
        user_id: str,
        dimension: str,
        psychometric_version: Optional[int] = None
    ) -> List[Dict]:
        """
        Busca evidências de uma dimensão específica

        Args:
            user_id: ID do usuário
            dimension: Nome da dimensão
            psychometric_version: Versão específica (None = mais recente)

        Returns:
            Lista de evidências em formato dict
        """
        cursor = self.db.conn.cursor()

        if psychometric_version is None:
            # Buscar versão mais recente
            cursor.execute("""
                SELECT MAX(version) FROM user_psychometrics WHERE user_id = ?
            """, (user_id,))
            result = cursor.fetchone()
            psychometric_version = result[0] if result and result[0] else 1

        cursor.execute("""
            SELECT
                id,
                conversation_id,
                quote,
                context_before,
                context_after,
                trait_indicator,
                direction,
                relevance_score,
                confidence,
                is_ambiguous,
                explanation,
                conversation_timestamp,
                extracted_at
            FROM psychometric_evidence
            WHERE user_id = ?
              AND dimension = ?
              AND psychometric_version = ?
            ORDER BY relevance_score DESC, confidence DESC
        """, (user_id, dimension, psychometric_version))

        evidence_list = []
        for row in cursor.fetchall():
            evidence_list.append({
                'id': row[0],
                'conversation_id': row[1],
                'quote': row[2],
                'context_before': row[3],
                'context_after': row[4],
                'trait_indicator': row[5],
                'direction': row[6],
                'relevance_score': row[7],
                'confidence': row[8],
                'is_ambiguous': bool(row[9]),
                'explanation': row[10],
                'conversation_timestamp': row[11],
                'extracted_at': row[12]
            })

        return evidence_list
