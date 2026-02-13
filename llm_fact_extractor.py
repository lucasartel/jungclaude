"""
llm_fact_extractor.py - Extrator de Fatos com LLM
==================================================

Sistema inteligente de extração de fatos usando Claude Sonnet 4.5
para capturar informações estruturadas das conversas.

Modelo único: claude-sonnet-4-5-20250929

Autor: Sistema Jung
Data: 2025-01-22
"""

import json
import logging
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Import do detector de correções
try:
    from correction_detector import CorrectionDetector, CorrectionIntent
    CORRECTION_DETECTOR_AVAILABLE = True
except ImportError:
    CORRECTION_DETECTOR_AVAILABLE = False
    CorrectionDetector = None
    CorrectionIntent = None


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

    # Prompt otimizado para extração de fatos - Sistema de Memória Profunda V2
    EXTRACTION_PROMPT = """Você é um sistema especializado em extrair fatos estruturados de conversas para criar memória emocional profunda.

TAREFA: Extrair TODOS os fatos mencionados na mensagem abaixo.

CATEGORIAS DE FATOS (APENAS 2):

1. RELACIONAMENTO - TODA a vida pessoal do usuário
   Tipos principais:
   - Pessoas: esposa, marido, filho, filha, pai, mae, irmao, irma, amigo, namorado, etc.
   - Personalidade: traço, valor, crenca, autoimagem, gatilho_emocional
   - Desafios pessoais: saude_mental, saude_fisica, objetivo_pessoal
   - Preferências pessoais: hobbie, leitura, musica, comida, ritual, aversao
   - Eventos pessoais: viagem, aniversario, marco_importante, rotina

   Atributos: nome, idade, profissao, aniversario, dinamica, tipo, inicio, frequencia, gatilho,
              tentativa_solucao, genero, autor_favorito, beneficio, data, sentimento, planejamento

   Exemplos:
   - esposa.nome="Ana"
   - esposa.aniversario="15/03"
   - personalidade_traço.tipo="introvertido"
   - saude_mental_insonia.inicio="há 3 meses"
   - saude_mental_insonia.gatilho="estresse no trabalho"
   - hobbie_leitura.genero="ficção científica"
   - hobbie_leitura.frequencia="antes de dormir"
   - evento_viagem.destino="Paris"
   - evento_viagem.data="janeiro 2025"

2. TRABALHO - TODA a vida profissional do usuário
   Tipos principais:
   - Profissão: profissao, empresa, cargo, projeto
   - Relações: colega, chefe, equipe
   - Situação: satisfacao, objetivo, desafio, responsabilidade
   - Desenvolvimento: objetivo_carreira, curso, certificacao

   Atributos: nome, local, tempo, satisfacao, objetivo, desafio, salario, responsabilidade,
              nivel, meta, prazo

   Exemplos:
   - profissao.nome="designer"
   - profissao.empresa="Google"
   - profissao.tempo="3 anos"
   - satisfacao.nivel="gosto mas estressante"
   - objetivo.meta="virar senior"
   - desafio.tipo="pressão por prazos"

INSTRUÇÕES CRÍTICAS:
1. Use APENAS as categorias RELACIONAMENTO ou TRABALHO
2. Para vida pessoal (saúde, hobbies, família, eventos): use RELACIONAMENTO
3. Para vida profissional (carreira, empresa, colegas): use TRABALHO
4. Seja ESPECÍFICO - capture nomes próprios, datas, números
5. Extraia TODOS os detalhes mencionados
6. Use confidence: 1.0 para fatos explícitos, 0.8 para inferidos claros, 0.6 para ambíguos

EXEMPLOS DE EXTRAÇÃO:

Entrada: "Minha esposa Jucinei faz aniversário dia 15 de março, ela é professora"
Saída:
{
  "fatos": [
    {"category": "RELACIONAMENTO", "fact_type": "esposa", "attribute": "nome", "value": "Jucinei", "confidence": 1.0, "context": "Minha esposa Jucinei"},
    {"category": "RELACIONAMENTO", "fact_type": "esposa", "attribute": "aniversario", "value": "15/03", "confidence": 1.0, "context": "faz aniversário dia 15 de março"},
    {"category": "RELACIONAMENTO", "fact_type": "esposa", "attribute": "profissao", "value": "professora", "confidence": 1.0, "context": "ela é professora"}
  ]
}

Entrada: "Tenho insônia há 3 meses por causa do estresse no trabalho, já tentei meditação"
Saída:
{
  "fatos": [
    {"category": "RELACIONAMENTO", "fact_type": "saude_mental_insonia", "attribute": "inicio", "value": "há 3 meses", "confidence": 1.0, "context": "há 3 meses"},
    {"category": "RELACIONAMENTO", "fact_type": "saude_mental_insonia", "attribute": "gatilho", "value": "estresse no trabalho", "confidence": 0.8, "context": "por causa do estresse no trabalho"},
    {"category": "RELACIONAMENTO", "fact_type": "saude_mental_insonia", "attribute": "tentativa_solucao", "value": "meditação", "confidence": 1.0, "context": "já tentei meditação"}
  ]
}

Entrada: "Adoro ler ficção científica antes de dormir, Isaac Asimov é meu favorito, me ajuda a relaxar"
Saída:
{
  "fatos": [
    {"category": "RELACIONAMENTO", "fact_type": "hobbie_leitura", "attribute": "genero", "value": "ficção científica", "confidence": 1.0, "context": "ler ficção científica"},
    {"category": "RELACIONAMENTO", "fact_type": "hobbie_leitura", "attribute": "frequencia", "value": "antes de dormir", "confidence": 1.0, "context": "antes de dormir"},
    {"category": "RELACIONAMENTO", "fact_type": "hobbie_leitura", "attribute": "autor_favorito", "value": "Isaac Asimov", "confidence": 1.0, "context": "Isaac Asimov é meu favorito"},
    {"category": "RELACIONAMENTO", "fact_type": "hobbie_leitura", "attribute": "beneficio", "value": "me ajuda a relaxar", "confidence": 1.0, "context": "me ajuda a relaxar"}
  ]
}

Entrada: "Vou viajar para Paris em janeiro, primeira vez na Europa, estou muito ansioso!"
Saída:
{
  "fatos": [
    {"category": "RELACIONAMENTO", "fact_type": "evento_viagem", "attribute": "destino", "value": "Paris", "confidence": 1.0, "context": "viajar para Paris"},
    {"category": "RELACIONAMENTO", "fact_type": "evento_viagem", "attribute": "data", "value": "janeiro 2025", "confidence": 1.0, "context": "em janeiro"},
    {"category": "RELACIONAMENTO", "fact_type": "evento_viagem", "attribute": "planejamento", "value": "primeira vez na Europa", "confidence": 1.0, "context": "primeira vez na Europa"},
    {"category": "RELACIONAMENTO", "fact_type": "evento_viagem", "attribute": "sentimento", "value": "ansioso positivo", "confidence": 0.9, "context": "estou muito ansioso!"}
  ]
}

Entrada: "Trabalho como designer na Google há 3 anos, gosto mas é muito estressante, quero virar senior"
Saída:
{
  "fatos": [
    {"category": "TRABALHO", "fact_type": "profissao", "attribute": "nome", "value": "designer", "confidence": 1.0, "context": "Trabalho como designer"},
    {"category": "TRABALHO", "fact_type": "profissao", "attribute": "empresa", "value": "Google", "confidence": 1.0, "context": "na Google"},
    {"category": "TRABALHO", "fact_type": "profissao", "attribute": "tempo", "value": "3 anos", "confidence": 1.0, "context": "há 3 anos"},
    {"category": "TRABALHO", "fact_type": "satisfacao", "attribute": "nivel", "value": "gosto mas estressante", "confidence": 1.0, "context": "gosto mas é muito estressante"},
    {"category": "TRABALHO", "fact_type": "objetivo", "attribute": "meta", "value": "virar senior", "confidence": 1.0, "context": "quero virar senior"}
  ]
}

Entrada: "Sou introvertido, família é tudo para mim, acredito muito em terapia"
Saída:
{
  "fatos": [
    {"category": "RELACIONAMENTO", "fact_type": "personalidade_traço", "attribute": "tipo", "value": "introvertido", "confidence": 1.0, "context": "Sou introvertido"},
    {"category": "RELACIONAMENTO", "fact_type": "personalidade_valor", "attribute": "tipo", "value": "familia_primeiro", "confidence": 0.9, "context": "família é tudo para mim"},
    {"category": "RELACIONAMENTO", "fact_type": "personalidade_crenca", "attribute": "tipo", "value": "terapia", "confidence": 1.0, "context": "acredito muito em terapia"},
    {"category": "RELACIONAMENTO", "fact_type": "personalidade_crenca", "attribute": "atitude", "value": "acredito muito", "confidence": 1.0, "context": "acredito muito"}
  ]
}

MENSAGEM DO USUÁRIO:
"{user_input}"

Retorne APENAS o JSON no formato especificado, sem texto adicional."""

    def __init__(self, llm_client, model: str = "claude-sonnet-4-5-20250929"):
        """
        Args:
            llm_client: Cliente Anthropic
            model: Modelo Claude a usar (padrão: claude-sonnet-4-5-20250929)
        """
        self.llm = llm_client
        self.model = model

        # Inicializar detector de correções
        if CORRECTION_DETECTOR_AVAILABLE:
            self.correction_detector = CorrectionDetector(
                llm_client=llm_client,
                model=model
            )
            logger.info("✅ CorrectionDetector integrado ao LLMFactExtractor")
        else:
            self.correction_detector = None
            logger.warning("⚠️ CorrectionDetector não disponível")

    def extract_facts(self, user_input: str, user_id: str = None,
                      existing_facts: List[Dict] = None) -> Tuple[List[ExtractedFact], List["CorrectionIntent"]]:
        """
        Extrai fatos da mensagem do usuário usando LLM.
        Detecta correções ANTES de extrair fatos novos.

        Args:
            user_input: Mensagem do usuário
            user_id: ID do usuário (para logging)
            existing_facts: Fatos atuais do usuário (melhora detecção de correções)

        Returns:
            Tupla (fatos_novos, correções_detectadas)
        """
        logger.info(f"🤖 [LLM EXTRACTOR] Analisando: {user_input[:100]}...")

        # ETAPA 1: Detectar correções primeiro
        corrections = []
        if self.correction_detector:
            corrections = self.correction_detector.detect(user_input, existing_facts or [])
            if corrections:
                logger.info(f"   🔧 {len(corrections)} correção(ões) detectada(s) - pulando extração normal")
                # Não extrai como fato novo para evitar duplicidade
                return [], corrections

        # ETAPA 2: Extração normal de fatos novos
        try:
            facts = self._extract_with_llm(user_input)

            if facts:
                logger.info(f"   ✅ LLM extraiu {len(facts)} fatos")
                return facts, []
            else:
                logger.warning(f"   ⚠️ LLM não extraiu fatos, tentando fallback...")
                return self._extract_with_regex(user_input), []

        except Exception as e:
            logger.error(f"   ❌ Erro no LLM: {e}, usando fallback regex")
            return self._extract_with_regex(user_input), []

    def _extract_with_llm(self, user_input: str) -> List[ExtractedFact]:
        """Extração usando LLM"""

        prompt = self.EXTRACTION_PROMPT.format(user_input=user_input)

        try:
            # Chamar Claude (único provider)
            response = self.llm.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = response.content[0].text.strip()

            # Parsear JSON - Melhorado para lidar com diferentes formatos
            # Remover markdown code blocks se presentes
            cleaned_text = re.sub(r'^```json?\s*', '', response_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r'\s*```\s*$', '', cleaned_text)
            cleaned_text = cleaned_text.strip()

            # Tentar encontrar JSON válido na resposta
            # Caso 1: JSON direto
            try:
                data = json.loads(cleaned_text)
            except json.JSONDecodeError:
                # Caso 2: Extrair apenas o bloco JSON {...} mais externo
                # Use regex não-greedy para pegar apenas o JSON completo
                json_match = re.search(r'\{[^{}]*"fatos"[^{}]*:\s*\[[^\]]*\][^{}]*\}', cleaned_text, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(0))
                    except json.JSONDecodeError as e:
                        logger.error(f"      ❌ Erro ao parsear JSON extraído: {e}")
                        logger.error(f"      JSON tentado: {json_match.group(0)[:500]}")
                        raise
                else:
                    # Se não encontrou JSON com "fatos", pode ser resposta vazia ou sem formato
                    logger.warning(f"      ⚠️ Não encontrei JSON válido na resposta do LLM")
                    logger.warning(f"      Resposta (primeiros 500 chars): {cleaned_text[:500]}")
                    # Retornar estrutura vazia em vez de falhar
                    data = {"fatos": []}

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
        except KeyError as e:
            # Caso o JSON seja válido mas não tenha a chave "fatos"
            logger.warning(f"      ⚠️ JSON válido mas sem chave 'fatos': {e}")
            if 'response_text' in locals():
                logger.info(f"      Resposta do Claude: {response_text[:500]}")
            return []
        except Exception as e:
            logger.error(f"      ❌ Erro inesperado no LLM: {type(e).__name__} - {e}")
            if 'response_text' in locals():
                logger.error(f"      Resposta do LLM: {response_text[:500]}")
            # Log do traceback completo para debug
            import traceback
            logger.error(f"      Traceback: {traceback.format_exc()}")
            return []

    def _extract_with_regex(self, user_input: str) -> List[ExtractedFact]:
        """
        Fallback: Extração usando regex (método expandido para 2 categorias completas)
        Cobre RELACIONAMENTO (vida pessoal) e TRABALHO (vida profissional)
        """
        logger.info("   🔄 Usando fallback regex expandido...")

        facts = []
        input_lower = user_input.lower()

        # =====================================
        # RELACIONAMENTO - VIDA PESSOAL
        # =====================================

        # 1. PESSOAS (nomes de familiares)
        relationship_with_name = [
            (r'minh[ao] (esposa|marido|namorad[ao]|companheiro|companheira) (?:se chama|é|:)?\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)', 'relationship'),
            (r'(?:tenho|meu|minha) (filho|filha) (?:se chama|é|:)?\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)', 'relationship'),
            (r'(?:meu|minha) (pai|mãe|irmão|irmã|avô|avó) (?:se chama|é|:)?\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)', 'relationship'),
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

        # 2. VALORES PESSOAIS
        valores_patterns = {
            'familia': ['família é tudo', 'família em primeiro', 'priorizo família', 'família é importante'],
            'saude': ['saúde é importante', 'cuido da saúde', 'priorizo saúde'],
            'amizade': ['amigos são importantes', 'valorizo amizades', 'amizade é essencial'],
        }

        for valor, patterns in valores_patterns.items():
            if any(p in input_lower for p in patterns):
                facts.append(ExtractedFact(
                    category="RELACIONAMENTO",
                    fact_type="valor",
                    attribute=valor,
                    value="sim",
                    confidence=0.8,
                    context=user_input[:100]
                ))

        # 3. CRENÇAS
        crencas_patterns = {
            'terapia': ['acredito em terapia', 'faço terapia', 'terapia ajuda', 'acompanhamento psicológico'],
            'espiritualidade': ['acredito em Deus', 'sou religioso', 'tenho fé', 'sou católico', 'sou evangélico'],
            'meditacao': ['faço meditação', 'medito', 'mindfulness'],
        }

        for crenca, patterns in crencas_patterns.items():
            if any(p in input_lower for p in patterns):
                facts.append(ExtractedFact(
                    category="RELACIONAMENTO",
                    fact_type="crenca",
                    attribute=crenca,
                    value="pratica" if "faço" in input_lower or "pratico" in input_lower else "acredita",
                    confidence=0.8,
                    context=user_input[:100]
                ))

        # 4. SAÚDE MENTAL
        saude_mental_patterns = [
            (r'tenho (insônia|ansiedade|depressão|síndrome do pânico|burnout)', 'tipo'),
            (r'sofro (?:de|com) (ansiedade|depressão|insônia|estresse crônico)', 'tipo'),
            (r'(insônia|ansiedade|depressão) há (\d+) (?:meses|anos|semanas|dias)', 'duracao'),
        ]

        for pattern, attr_type in saude_mental_patterns:
            matches = re.finditer(pattern, input_lower)
            for match in matches:
                if attr_type == 'tipo':
                    condicao = match.group(1)
                    facts.append(ExtractedFact(
                        category="RELACIONAMENTO",
                        fact_type=f"saude_mental_{condicao}",
                        attribute="tipo",
                        value=condicao,
                        confidence=0.85,
                        context=match.group(0)
                    ))
                elif attr_type == 'duracao':
                    condicao = match.group(1)
                    tempo = match.group(2)
                    facts.append(ExtractedFact(
                        category="RELACIONAMENTO",
                        fact_type=f"saude_mental_{condicao}",
                        attribute="duracao",
                        value=f"{tempo} (período mencionado)",
                        confidence=0.85,
                        context=match.group(0)
                    ))

        # 5. SAÚDE FÍSICA
        saude_fisica_patterns = [
            (r'tenho (diabetes|hipertensão|asma|enxaqueca|colesterol alto)', 'condicao'),
            (r'sou (diabético|hipertenso|asmático)', 'condicao'),
        ]

        for pattern, attr_type in saude_fisica_patterns:
            match = re.search(pattern, input_lower)
            if match:
                condicao = match.group(1)
                facts.append(ExtractedFact(
                    category="RELACIONAMENTO",
                    fact_type=f"saude_fisica_{condicao}",
                    attribute="tipo",
                    value=condicao,
                    confidence=0.85,
                    context=match.group(0)
                ))

        # 6. HOBBIES - LEITURA
        hobbie_leitura_patterns = [
            (r'adoro ler (ficção científica|romance|autoajuda|biografia|fantasia|poesia)', 'genero'),
            (r'gosto de ler (ficção científica|romance|autoajuda|biografia|fantasia)', 'genero'),
            (r'(Isaac Asimov|Stephen King|Machado de Assis|[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+ [A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+) é meu (?:autor )?favorito', 'autor'),
        ]

        for pattern, attr_type in hobbie_leitura_patterns:
            match = re.search(pattern, input_lower if attr_type == 'genero' else user_input)
            if match:
                value = match.group(1)
                facts.append(ExtractedFact(
                    category="RELACIONAMENTO",
                    fact_type="hobbie_leitura",
                    attribute=attr_type,
                    value=value,
                    confidence=0.8,
                    context=match.group(0)
                ))

        # Frequência de leitura
        if any(p in input_lower for p in ['leio antes de dormir', 'leio todo dia', 'leio aos finais de semana']):
            freq = "antes de dormir" if "antes de dormir" in input_lower else \
                   "diariamente" if "todo dia" in input_lower else \
                   "fins de semana"
            facts.append(ExtractedFact(
                category="RELACIONAMENTO",
                fact_type="hobbie_leitura",
                attribute="frequencia",
                value=freq,
                confidence=0.75,
                context=user_input[:100]
            ))

        # 7. HOBBIES - EXERCÍCIO
        hobbie_exercicio_patterns = [
            (r'gosto de (correr|nadar|pedalar|fazer yoga|musculação|caminhar)', 'tipo'),
            (r'pratico (corrida|natação|ciclismo|yoga|musculação|caminhada)', 'tipo'),
        ]

        for pattern, attr_type in hobbie_exercicio_patterns:
            match = re.search(pattern, input_lower)
            if match:
                tipo = match.group(1)
                facts.append(ExtractedFact(
                    category="RELACIONAMENTO",
                    fact_type="hobbie_exercicio",
                    attribute="tipo",
                    value=tipo,
                    confidence=0.8,
                    context=match.group(0)
                ))

        # 8. HOBBIES - MÚSICA
        hobbie_musica_patterns = [
            (r'toco (violão|guitarra|piano|bateria|flauta|saxofone)', 'instrumento'),
            (r'gosto de (?:música |som )?(?:de )?(rock|jazz|clássica|sertanejo|mpb|pop)', 'genero'),
        ]

        for pattern, attr_type in hobbie_musica_patterns:
            match = re.search(pattern, input_lower)
            if match:
                value = match.group(1)
                facts.append(ExtractedFact(
                    category="RELACIONAMENTO",
                    fact_type="hobbie_musica",
                    attribute=attr_type,
                    value=value,
                    confidence=0.8,
                    context=match.group(0)
                ))

        # 9. EVENTOS - VIAGEM
        evento_viagem_patterns = [
            (r'vou viajar para ([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+) em (janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)', 'destino_e_data'),
            (r'viagem para ([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)', 'destino'),
        ]

        for pattern, attr_type in evento_viagem_patterns:
            match = re.search(pattern, user_input)  # Usar user_input para pegar maiúsculas
            if match:
                if attr_type == 'destino_e_data':
                    destino = match.group(1)
                    mes = match.group(2)
                    facts.append(ExtractedFact(
                        category="RELACIONAMENTO",
                        fact_type="evento_viagem",
                        attribute="destino",
                        value=destino,
                        confidence=0.85,
                        context=match.group(0)
                    ))
                    facts.append(ExtractedFact(
                        category="RELACIONAMENTO",
                        fact_type="evento_viagem",
                        attribute="data",
                        value=mes,
                        confidence=0.85,
                        context=match.group(0)
                    ))
                else:
                    destino = match.group(1)
                    facts.append(ExtractedFact(
                        category="RELACIONAMENTO",
                        fact_type="evento_viagem",
                        attribute="destino",
                        value=destino,
                        confidence=0.8,
                        context=match.group(0)
                    ))

        # Planejamento de viagem
        if 'primeira vez' in input_lower:
            facts.append(ExtractedFact(
                category="RELACIONAMENTO",
                fact_type="evento_viagem",
                attribute="planejamento",
                value="primeira vez",
                confidence=0.75,
                context=user_input[:100]
            ))

        # Sentimento sobre viagem
        sentimentos_viagem = {
            'ansioso': ['ansioso', 'nervoso'],
            'empolgado': ['empolgado', 'animado', 'feliz'],
        }
        for sentimento, keywords in sentimentos_viagem.items():
            if any(k in input_lower for k in keywords):
                facts.append(ExtractedFact(
                    category="RELACIONAMENTO",
                    fact_type="evento_viagem",
                    attribute="sentimento",
                    value=sentimento,
                    confidence=0.7,
                    context=user_input[:100]
                ))

        # 10. PERSONALIDADE (traços básicos)
        personality_patterns = {
            'introvertido': ['sou introvertido', 'prefiro ficar sozinho', 'evito eventos sociais'],
            'extrovertido': ['sou extrovertido', 'gosto de pessoas', 'adoro festas'],
            'ansioso': ['sou ansioso', 'fico ansioso com tudo'],
            'calmo': ['sou calmo', 'sou tranquilo', 'pessoa zen'],
        }

        for trait, patterns in personality_patterns.items():
            if any(p in input_lower for p in patterns):
                facts.append(ExtractedFact(
                    category="RELACIONAMENTO",
                    fact_type="personalidade",
                    attribute="traço",
                    value=trait,
                    confidence=0.75,
                    context=user_input[:100]
                ))

        # =====================================
        # TRABALHO - VIDA PROFISSIONAL
        # =====================================

        # 1. PROFISSÃO E EMPRESA (já funcionava)
        work_patterns = [
            (r'trabalho como ([^.,!?]+?)(?:\.|,|no|na|em)', 'profissao'),
            (r'sou (engenheiro|médico|professor|advogado|desenvolvedor|designer|gerente|analista|arquiteto)', 'profissao'),
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

        # 2. SATISFAÇÃO
        satisfacao_patterns = {
            'positiva': ['adoro meu trabalho', 'gosto do trabalho', 'satisfeito com trabalho', 'amo meu trabalho'],
            'neutra': ['trabalho é ok', 'não amo mas não odeio', 'trabalho normal'],
            'negativa': ['odeio meu trabalho', 'muito estressante', 'cansativo', 'frustrante', 'trabalho ruim'],
        }

        for nivel, patterns in satisfacao_patterns.items():
            if any(p in input_lower for p in patterns):
                facts.append(ExtractedFact(
                    category="TRABALHO",
                    fact_type="satisfacao",
                    attribute="nivel",
                    value=nivel,
                    confidence=0.75,
                    context=user_input[:100]
                ))
                break  # Pegar apenas a primeira

        # 3. OBJETIVOS PROFISSIONAIS
        objetivo_patterns = [
            (r'quero (?:virar|ser|me tornar) (senior|pleno|júnior|gerente|diretor|tech lead)', 'cargo'),
            (r'objetivo é (mudar de área|crescer|liderar equipe|empreender)', 'tipo'),
            (r'sonho em trabalhar n[ao] ([^.,!?]+)', 'empresa_sonho'),
        ]

        for pattern, attr_type in objetivo_patterns:
            match = re.search(pattern, input_lower)
            if match:
                value = match.group(1)
                facts.append(ExtractedFact(
                    category="TRABALHO",
                    fact_type="objetivo",
                    attribute=attr_type,
                    value=value,
                    confidence=0.8,
                    context=match.group(0)
                ))

        # 4. DESAFIOS NO TRABALHO
        desafio_patterns = {
            'retrabalho': ['muito retrabalho', 'refaço coisas', 'sempre mudando'],
            'pressao': ['muita pressão', 'prazos apertados', 'muita cobrança'],
            'sobrecarga': ['muito trabalho', 'sobrecarregado', 'horas extras', 'trabalho demais'],
            'desorganizacao': ['falta organização', 'equipe desorganizada', 'caos'],
        }

        for desafio, patterns in desafio_patterns.items():
            if any(p in input_lower for p in patterns):
                facts.append(ExtractedFact(
                    category="TRABALHO",
                    fact_type="desafio",
                    attribute="tipo",
                    value=desafio,
                    confidence=0.75,
                    context=user_input[:100]
                ))

        # 5. TEMPO NA EMPRESA/CARGO
        tempo_patterns = [
            (r'(?:trabalho|estou) (?:há|ha|a) (\d+) (?:anos|meses)', 'tempo'),
            (r'(?:há|ha|a) (\d+) (?:anos|meses) n[ao]', 'tempo'),
        ]

        for pattern, attr_type in tempo_patterns:
            match = re.search(pattern, input_lower)
            if match:
                tempo = match.group(1)
                facts.append(ExtractedFact(
                    category="TRABALHO",
                    fact_type="tempo",
                    attribute="duracao",
                    value=f"{tempo} (período mencionado)",
                    confidence=0.8,
                    context=match.group(0)
                ))

        # =====================================
        # RETORNO
        # =====================================

        if facts:
            logger.info(f"   ✅ Regex extraiu {len(facts)} fatos")
            for fact in facts:
                logger.debug(f"      {fact.category}.{fact.fact_type}.{fact.attribute} = {fact.value}")
        else:
            logger.info(f"   ℹ️ Nenhum fato extraído via regex")

        return facts


def test_extractor():
    """Teste rápido do extrator"""
    import anthropic
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Inicializar cliente Claude
    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    extractor = LLMFactExtractor(client, model="claude-sonnet-4-5-20250929")

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
