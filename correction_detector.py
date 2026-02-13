"""
correction_detector.py - Detector Genérico de Correção de Fatos
================================================================

Detecta quando o usuário está corrigindo informações previamente
armazenadas na memória (nome, profissão, empresa, hobby, etc.).

Funciona em dois estágios:
1. Regex rápido para padrões óbvios de correção
2. LLM para casos complexos e extração de detalhes

Autor: Sistema Jung
Data: 2025-02
"""

import json
import logging
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CorrectionIntent:
    """Representa uma intenção de correção de fato"""
    is_correction: bool         # True se é uma correção
    category: str               # RELACIONAMENTO, TRABALHO
    fact_type: str              # esposa, profissao, empresa, hobby, etc.
    attribute: str              # nome, idade, cargo, tempo, etc.
    old_value: Optional[str]    # Valor anterior (se identificável)
    new_value: str              # Novo valor correto
    confidence: float           # 0.0 a 1.0
    context: str                # Trecho que indica correção


class CorrectionDetector:
    """
    Detector genérico de correção de fatos.

    Detecta quando o usuário está corrigindo qualquer tipo de informação:
    - Nomes de pessoas (esposa, filho, chefe)
    - Profissão
    - Empresa
    - Hobbies
    - Idades
    - Locais
    - Qualquer outro fato estruturado
    """

    # Padrões GENÉRICOS para detectar intenção de correção
    CORRECTION_PATTERNS = [
        # Negação direta + correção
        (r"(?:não|nao),?\s*(?:o |a )?(?:nome|certo|correto|verdade)\s*(?:é|e)\s*(.+)", "negacao_nome"),
        (r"(?:não|nao),?\s*(?:é|e|era|sou|tenho|trabalho|moro)\s+(.+)", "negacao_verbo"),
        (r"(?:não|nao)\s+(?:mais|é)\s*(.+)", "negacao_mais"),

        # Admissão de erro
        (r"(?:errei|me enganei|falei errado|disse errado),?\s*(?:na verdade|o certo|o correto)?\s*(?:é|e)?\s*(.+)", "erro_admitido"),
        (r"(?:corrijo|corrigindo|retificando|retifi co)[:\s]+(.+)", "correcao_explicita"),
        (r"(?:desculpa|desculpe),?\s*(?:o |a )?(?:certo|correto|nome)\s*(?:é|e)\s*(.+)", "desculpa_correcao"),

        # Atualização temporal
        (r"(?:na verdade|na real|agora|atualmente|hoje)\s*(?:é|sou|tenho|trabalho|moro)\s*(.+)", "atualizacao"),
        (r"(?:mudou|mudei|troquei|saí|deixei|larguei)\s*(?:de|da|do|para)?\s*(.+)", "mudanca"),
        (r"(?:não trabalho mais|saí da|deixei a|larguei a)\s*(.+)", "saida"),

        # Substituição explícita
        (r"(?:não é|nao e|não era|nao era)\s*(.+?),?\s*(?:é|e|mas sim|mas)\s*(.+)", "substituicao"),
        (r"(.+?)\s*(?:não|nao),?\s*(?:é|e)\s*(.+)", "inversao"),  # "Maria não, é Marina"

        # Parei de / Comecei a
        (r"(?:parei de|deixei de|não faço mais|não pratico mais)\s*(.+)", "parei"),
        (r"(?:comecei a|passei a|agora faço|agora pratico)\s*(.+)", "comecei"),
    ]

    # Prompt LLM para extração detalhada de correção
    CORRECTION_EXTRACTION_PROMPT = """Você é um sistema especializado em detectar CORREÇÕES de informações.

TAREFA: Analise se o usuário está CORRIGINDO uma informação que ele havia dito antes.

TIPOS DE CORREÇÃO:
1. ERRO DE INFORMAÇÃO: "Não, minha esposa se chama Marina" (nome errado)
2. ATUALIZAÇÃO: "Saí da Google, agora estou na Meta" (mudança de situação)
3. RETIFICAÇÃO: "Errei, sou designer, não programador" (profissão errada)
4. DESATIVAÇÃO: "Parei de jogar futebol" (hobby abandonado)

EXEMPLOS DE CORREÇÃO:
- "Não, minha esposa se chama Marina" → esposa.nome = Marina
- "Errei, trabalho na Google, não na Microsoft" → empresa.nome = Google
- "Na verdade sou designer, não programador" → profissao.nome = designer
- "Não pratico mais futebol, agora é natação" → hobby = natação (futebol inativo)
- "Meu filho tem 10 anos, não 8" → filho.idade = 10
- "Saí da empresa X, agora estou na Y" → empresa.nome = Y
- "Mudei para São Paulo" → moradia.cidade = São Paulo

FATOS ATUAIS DO USUÁRIO (para contexto):
{existing_facts}

MENSAGEM DO USUÁRIO:
"{user_input}"

Se for uma correção, responda em JSON:
{{
    "is_correction": true,
    "corrections": [
        {{
            "category": "RELACIONAMENTO ou TRABALHO",
            "fact_type": "tipo do fato (esposa, profissao, empresa, hobby, etc.)",
            "attribute": "atributo (nome, idade, cargo, cidade, status, etc.)",
            "old_value": "valor anterior se mencionado, ou null",
            "new_value": "valor correto",
            "confidence": 0.0 a 1.0
        }}
    ]
}}

Se NÃO for uma correção (apenas informação nova ou conversa normal):
{{
    "is_correction": false,
    "corrections": []
}}

Responda APENAS o JSON, sem explicações."""

    def __init__(self, llm_client=None, model: str = "claude-sonnet-4-5-20250929"):
        """
        Inicializa o detector de correções.

        Args:
            llm_client: Cliente Anthropic para chamadas LLM
            model: Modelo a usar (padrão: claude-sonnet-4-5-20250929)
        """
        self.llm_client = llm_client
        self.model = model

        # Compilar padrões regex para performance
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), name)
            for pattern, name in self.CORRECTION_PATTERNS
        ]

        logger.info("✅ CorrectionDetector inicializado")

    def detect(self, user_input: str, existing_facts: List[Dict] = None) -> List[CorrectionIntent]:
        """
        Detecta se a mensagem contém correções de fatos.

        Args:
            user_input: Mensagem do usuário
            existing_facts: Lista de fatos atuais do usuário (opcional, melhora precisão)

        Returns:
            Lista de CorrectionIntent (vazia se não houver correções)
        """
        if not user_input or len(user_input.strip()) < 3:
            return []

        # ESTÁGIO 1: Detecção rápida via regex
        has_correction_pattern, pattern_name = self._detect_correction_pattern(user_input)

        if not has_correction_pattern:
            logger.debug(f"Nenhum padrão de correção detectado em: {user_input[:50]}...")
            return []

        logger.info(f"🔍 Padrão de correção detectado: {pattern_name}")

        # ESTÁGIO 2: Extração detalhada via LLM
        if self.llm_client:
            corrections = self._extract_correction_details(user_input, existing_facts)
            if corrections:
                logger.info(f"✅ {len(corrections)} correção(ões) extraída(s)")
                return corrections

        # FALLBACK: Retornar correção genérica baseada no padrão
        return self._create_fallback_correction(user_input, pattern_name, existing_facts)

    def _detect_correction_pattern(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Detecta se o texto contém padrões de correção via regex.

        Returns:
            Tupla (encontrou_padrão, nome_do_padrão)
        """
        for pattern, name in self.compiled_patterns:
            if pattern.search(text):
                return True, name
        return False, None

    def _extract_correction_details(self, user_input: str,
                                    existing_facts: List[Dict] = None) -> List[CorrectionIntent]:
        """
        Usa LLM para extrair detalhes da correção.
        """
        if not self.llm_client:
            return []

        # Formatar fatos existentes para contexto
        facts_context = "Nenhum fato registrado ainda."
        if existing_facts:
            facts_lines = []
            for fact in existing_facts[:20]:  # Limitar a 20 fatos
                facts_lines.append(
                    f"- {fact.get('fact_type', '?')}.{fact.get('attribute', '?')} = {fact.get('fact_value', '?')}"
                )
            facts_context = "\n".join(facts_lines)

        prompt = self.CORRECTION_EXTRACTION_PROMPT.format(
            existing_facts=facts_context,
            user_input=user_input
        )

        try:
            response = self.llm_client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.1,  # Baixa para consistência
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()

            # Extrair JSON da resposta
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if not json_match:
                logger.warning("LLM não retornou JSON válido para correção")
                return []

            result = json.loads(json_match.group())

            if not result.get("is_correction", False):
                return []

            corrections = []
            for corr in result.get("corrections", []):
                corrections.append(CorrectionIntent(
                    is_correction=True,
                    category=corr.get("category", "RELACIONAMENTO"),
                    fact_type=corr.get("fact_type", "desconhecido"),
                    attribute=corr.get("attribute", "valor"),
                    old_value=corr.get("old_value"),
                    new_value=corr.get("new_value", ""),
                    confidence=float(corr.get("confidence", 0.8)),
                    context=user_input[:200]
                ))

            return corrections

        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON de correção: {e}")
            return []
        except Exception as e:
            logger.error(f"Erro ao extrair correção via LLM: {type(e).__name__} - {e}")
            return []

    def _create_fallback_correction(self, user_input: str, pattern_name: str,
                                    existing_facts: List[Dict] = None) -> List[CorrectionIntent]:
        """
        Cria correção genérica quando LLM não está disponível.
        Tenta inferir o tipo de correção baseado no padrão e fatos existentes.
        """
        # Tentar encontrar qual fato está sendo corrigido
        fact_type = "desconhecido"
        attribute = "valor"
        old_value = None

        if existing_facts:
            # Buscar menção a valores existentes no texto
            text_lower = user_input.lower()
            for fact in existing_facts:
                fact_value = str(fact.get('fact_value', '')).lower()
                if fact_value and fact_value in text_lower:
                    fact_type = fact.get('fact_type', 'desconhecido')
                    attribute = fact.get('attribute', 'valor')
                    old_value = fact.get('fact_value')
                    break

        # Extrair possível novo valor usando regex simples
        new_value = self._extract_new_value(user_input)

        if not new_value:
            return []

        return [CorrectionIntent(
            is_correction=True,
            category="RELACIONAMENTO",  # Default
            fact_type=fact_type,
            attribute=attribute,
            old_value=old_value,
            new_value=new_value,
            confidence=0.6,  # Baixa confiança sem LLM
            context=user_input[:200]
        )]

    def _extract_new_value(self, text: str) -> Optional[str]:
        """
        Tenta extrair o novo valor de uma correção usando heurísticas.
        """
        # Padrões para extrair o valor corrigido
        patterns = [
            r"(?:é|e)\s+([A-Z][a-záéíóúãõâêô]+)",  # Nome próprio após "é"
            r"(?:agora|atualmente)\s+(?:é|sou|tenho|trabalho|moro)\s+(?:na |no |em |como )?(.+?)(?:\.|,|$)",
            r"(?:na verdade)\s+(?:é|sou|tenho)\s+(.+?)(?:\.|,|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None


def generate_correction_feedback(correction: CorrectionIntent) -> str:
    """
    Gera mensagem de feedback para o usuário.

    APENAS se a correção for ambígua (confidence < 0.8).
    Correções de alta confiança são silenciosas.

    Args:
        correction: Intenção de correção detectada

    Returns:
        String de feedback ou vazia se não precisar confirmar
    """
    if correction.confidence >= 0.8:
        return ""  # Silencioso - alta confiança

    # Feedback para correções ambíguas
    fact_desc = f"{correction.fact_type}"
    if correction.attribute and correction.attribute != "valor":
        fact_desc = f"{correction.attribute} de {correction.fact_type}"

    return f"Só para confirmar: atualizei que {fact_desc} é '{correction.new_value}', certo?"
