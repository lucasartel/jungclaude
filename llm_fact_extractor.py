"""
llm_fact_extractor.py - Extrator de Fatos com LLM
==================================================

Sistema inteligente de extração de fatos usando LLM (Grok/Claude)
para capturar informações estruturadas das conversas.

Autor: Sistema Jung
Data: 2025-12-19
"""

import json
import logging
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ExtractedFact:
    """Representa um fato extraído da conversa"""
    category: str       # RELACIONAMENTO, TRABALHO, PERSONALIDADE, etc.
    fact_type: str      # esposa, filho, pai, profissao, hobby, etc.
    attribute: str      # nome, idade, profissao, etc.
    value: str          # O valor do atributo
    confidence: float   # 0.0 a 1.0
    context: str        # Trecho da conversa que gerou o fato


class LLMFactExtractor:
    """
    Extrator inteligente de fatos usando LLM

    Features:
    - Extrai nomes próprios de pessoas
    - Detecta múltiplas pessoas na mesma frase
    - Captura atributos complementares (idade, profissão, etc.)
    - Fallback para regex em caso de falha do LLM
    """

    # Prompt otimizado para extração de fatos
    EXTRACTION_PROMPT = """Você é um sistema especializado em extrair fatos estruturados de conversas.

TAREFA: Extrair TODOS os fatos mencionados na mensagem abaixo.

CATEGORIAS DE FATOS:
1. RELACIONAMENTO - Pessoas relacionadas ao usuário
   - Tipos: esposa, marido, filho, filha, pai, mae, irmao, irma, avô, avó, primo, amigo, namorado, namorada, etc.
   - Atributos: nome, idade, profissao, local_trabalho, personalidade, etc.

2. TRABALHO - Informações profissionais
   - Tipos: profissao, empresa, cargo, area, projeto
   - Atributos: nome, local, tempo, satisfacao, etc.

3. PERSONALIDADE - Traços de personalidade
   - Tipos: traço, preferencia, habito, valor
   - Atributos: descricao, intensidade, contexto

4. SAUDE - Informações de saúde
   - Tipos: condicao, tratamento, historico
   - Atributos: descricao, status, medicacao

5. EDUCACAO - Formação e aprendizado
   - Tipos: formacao, curso, instituicao, habilidade
   - Atributos: nome, nivel, status, area

6. HOBBIES - Atividades e interesses
   - Tipos: hobby, interesse, esporte, arte
   - Atributos: nome, frequencia, nivel

INSTRUÇÕES:
1. Extraia TODOS os fatos mencionados
2. Seja ESPECÍFICO - capture nomes próprios quando mencionados
3. Para pessoas, sempre tente extrair: nome, idade (se mencionado), profissão (se mencionado)
4. Se múltiplas pessoas são mencionadas, extraia cada uma separadamente
5. Use confidence: 1.0 para fatos explícitos, 0.7 para inferidos, 0.5 para ambíguos

FORMATO DE SAÍDA (JSON):
{
  "fatos": [
    {
      "category": "RELACIONAMENTO",
      "fact_type": "esposa",
      "attribute": "nome",
      "value": "Ana",
      "confidence": 1.0,
      "context": "Minha esposa se chama Ana"
    }
  ]
}

MENSAGEM DO USUÁRIO:
"{user_input}"

Retorne APENAS o JSON, sem texto adicional."""

    def __init__(self, llm_client, model: str = "grok-beta"):
        """
        Args:
            llm_client: Cliente LLM (OpenAI/XAI)
            model: Modelo a usar (grok-beta, gpt-4o-mini, etc.)
        """
        self.llm = llm_client
        self.model = model

    def extract_facts(self, user_input: str, user_id: str = None) -> List[ExtractedFact]:
        """
        Extrai fatos da mensagem do usuário usando LLM

        Args:
            user_input: Mensagem do usuário
            user_id: ID do usuário (para logging)

        Returns:
            Lista de ExtractedFact
        """
        logger.info(f"🤖 [LLM EXTRACTOR] Extraindo fatos de: {user_input[:100]}...")

        try:
            # Tentar extração com LLM
            facts = self._extract_with_llm(user_input)

            if facts:
                logger.info(f"   ✅ LLM extraiu {len(facts)} fatos")
                return facts
            else:
                logger.warning(f"   ⚠️ LLM não extraiu fatos, tentando fallback...")
                return self._extract_with_regex(user_input)

        except Exception as e:
            logger.error(f"   ❌ Erro no LLM: {e}, usando fallback regex")
            return self._extract_with_regex(user_input)

    def _extract_with_llm(self, user_input: str) -> List[ExtractedFact]:
        """Extração usando LLM"""

        prompt = self.EXTRACTION_PROMPT.format(user_input=user_input)

        try:
            # Chamar LLM
            if self.model.startswith("grok"):
                # XAI / Grok
                response = self.llm.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,  # Baixa temperatura para extração precisa
                    max_tokens=2000
                )
            else:
                # OpenAI
                response = self.llm.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=2000
                )

            response_text = response.choices[0].message.content.strip()

            # Parsear JSON - Melhorado para lidar com diferentes formatos
            # Remover markdown code blocks se presentes
            cleaned_text = re.sub(r'^```json?\s*', '', response_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r'\s*```\s*$', '', cleaned_text)

            # Tentar encontrar JSON válido na resposta
            # Caso 1: JSON direto
            try:
                data = json.loads(cleaned_text)
            except json.JSONDecodeError:
                # Caso 2: Extrair apenas o bloco JSON {...}
                json_match = re.search(r'\{[\s\S]*\}', cleaned_text)
                if json_match:
                    try:
                        data = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        # Caso 3: Tentar encontrar array de fatos diretamente
                        array_match = re.search(r'"fatos"\s*:\s*\[[\s\S]*\]', cleaned_text)
                        if array_match:
                            # Reconstruir JSON válido
                            data = json.loads('{' + array_match.group(0) + '}')
                        else:
                            raise
                else:
                    raise

            # Converter para ExtractedFact
            facts = []
            for fact_dict in data.get("fatos", []):
                try:
                    fact = ExtractedFact(
                        category=fact_dict.get("category", "OUTROS").upper(),
                        fact_type=fact_dict.get("fact_type", "").lower(),
                        attribute=fact_dict.get("attribute", "").lower(),
                        value=fact_dict.get("value", ""),
                        confidence=float(fact_dict.get("confidence", 0.8)),
                        context=fact_dict.get("context", user_input[:100])
                    )

                    # Validar que tem conteúdo
                    if fact.fact_type and fact.value:
                        facts.append(fact)
                        logger.debug(f"      Fato: {fact.category}.{fact.fact_type}.{fact.attribute} = {fact.value}")

                except (ValueError, KeyError) as e:
                    logger.warning(f"      ⚠️ Fato inválido ignorado: {fact_dict} - {e}")
                    continue

            return facts

        except json.JSONDecodeError as e:
            logger.error(f"      ❌ Erro ao parsear JSON do LLM: {e}")
            logger.error(f"      Resposta completa recebida:")
            logger.error(f"      {response_text}")
            logger.error(f"      Cleaned text tentado:")
            logger.error(f"      {cleaned_text[:500]}")
            return []
        except Exception as e:
            logger.error(f"      ❌ Erro no LLM: {type(e).__name__} - {e}")
            if 'response_text' in locals():
                logger.error(f"      Resposta do LLM: {response_text[:300]}")
            return []

    def _extract_with_regex(self, user_input: str) -> List[ExtractedFact]:
        """
        Fallback: Extração usando regex (método antigo melhorado)
        """
        logger.info("   🔄 Usando fallback regex...")

        facts = []
        input_lower = user_input.lower()

        # ===== RELACIONAMENTOS =====
        # Padrão: "minha esposa se chama Ana"
        relationship_with_name = [
            (r'minh[ao] (esposa|marido|namorad[ao]|companheiro|companheira) (?:se chama|é|:)?\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)', 'relationship'),
            (r'(?:tenho|meu|minha) (filho|filha) (?:se chama|é|:)?\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)', 'relationship'),
            (r'(?:meu|minha) (pai|mãe|irmão|irmã) (?:se chama|é|:)?\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)', 'relationship'),
        ]

        for pattern, category in relationship_with_name:
            matches = re.finditer(pattern, user_input, re.IGNORECASE)
            for match in matches:
                relationship_type = match.group(1).lower()
                name = match.group(2)

                facts.append(ExtractedFact(
                    category="RELACIONAMENTO",
                    fact_type=relationship_type,
                    attribute="nome",
                    value=name,
                    confidence=0.9,
                    context=match.group(0)
                ))

        # Padrão: "tenho 2 filhos" ou "tenho dois filhos: João e Maria"
        children_pattern = r'tenho (?:(\d+)|dois|duas|três|tr[eê]s|quatro) filhos?(?:\s*:\s*([^.!?]+))?'
        match = re.search(children_pattern, input_lower)
        if match:
            children_names = []
            if match.group(2):  # Lista de nomes
                # Extrair nomes próprios
                names_text = match.group(2)
                # Padrão de nomes próprios (começa com maiúscula)
                names = re.findall(r'\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)\b', names_text)
                children_names = names

            if children_names:
                for i, name in enumerate(children_names, 1):
                    facts.append(ExtractedFact(
                        category="RELACIONAMENTO",
                        fact_type="filho",
                        attribute=f"nome_{i}",
                        value=name,
                        confidence=0.85,
                        context=match.group(0)
                    ))

        # ===== TRABALHO =====
        work_patterns = [
            (r'trabalho como ([^.,!?]+?)(?:\.|,|no|na|em)', 'profissao'),
            (r'sou (engenheiro|médico|professor|advogado|desenvolvedor|designer|gerente|analista)', 'profissao'),
            (r'trabalho n[ao] ([^.,!?]+?)(?:\.|,|como)', 'empresa'),
        ]

        for pattern, attr in work_patterns:
            match = re.search(pattern, input_lower)
            if match:
                value = match.group(1).strip()
                facts.append(ExtractedFact(
                    category="TRABALHO",
                    fact_type=attr,
                    attribute="valor",
                    value=value,
                    confidence=0.8,
                    context=match.group(0)
                ))

        # ===== PERSONALIDADE =====
        personality_patterns = {
            'introvertido': ['sou introvertido', 'prefiro ficar sozinho'],
            'extrovertido': ['sou extrovertido', 'gosto de pessoas'],
            'ansioso': ['tenho ansiedade', 'sou ansioso'],
            'calmo': ['sou calmo', 'sou tranquilo'],
        }

        for trait, patterns in personality_patterns.items():
            if any(p in input_lower for p in patterns):
                facts.append(ExtractedFact(
                    category="PERSONALIDADE",
                    fact_type="traço",
                    attribute="tipo",
                    value=trait,
                    confidence=0.75,
                    context=user_input[:100]
                ))

        if facts:
            logger.info(f"   ✅ Regex extraiu {len(facts)} fatos")
        else:
            logger.info(f"   ℹ️ Nenhum fato extraído")

        return facts


def test_extractor():
    """Teste rápido do extrator"""
    from openai import OpenAI
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Inicializar cliente (usar Grok para teste)
    client = OpenAI(
        api_key=os.getenv("XAI_API_KEY"),
        base_url="https://api.x.ai/v1"
    )

    extractor = LLMFactExtractor(client, model="grok-beta")

    # Mensagens de teste
    test_messages = [
        "Minha esposa se chama Ana e ela é médica",
        "Tenho dois filhos: João de 10 anos e Maria de 8 anos",
        "Trabalho como desenvolvedor na Google há 3 anos",
        "Sou introvertido e gosto de ler livros de ficção científica",
        "Meu pai é aposentado e minha mãe é professora"
    ]

    print("="*60)
    print("TESTE DO LLM FACT EXTRACTOR")
    print("="*60)

    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Input: {message}")
        facts = extractor.extract_facts(message)

        if facts:
            print(f"   Fatos extraídos: {len(facts)}")
            for fact in facts:
                print(f"   - {fact.category}.{fact.fact_type}.{fact.attribute}: {fact.value} (conf: {fact.confidence:.2f})")
        else:
            print("   Nenhum fato extraído")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_extractor()
