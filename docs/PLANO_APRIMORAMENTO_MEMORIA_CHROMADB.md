# Plano de Aprimoramento da Memória Semântica ChromaDB - JungAgent

**Data de Criação:** 2026-01-02
**Versão:** 1.0
**Status:** Planejamento Aprovado

---

## 📋 Sumário Executivo

Este documento detalha o plano completo de aprimoramento da consistência e eficácia da memória semântica do agente Jung, focando na otimização do sistema ChromaDB + SQLite híbrido.

**Objetivo Central:** Garantir que o agente Jung não perca memória contextual como um LLM comum, melhorando a organização, busca e utilização da memória semântica armazenada no ChromaDB.

**Escopo:**
- ✅ SQLite está bem resolvido (dados estruturados, fatos, padrões)
- 🎯 **FOCO:** ChromaDB (memória semântica, busca vetorial, retrieval)

---

## 🔍 Análise da Arquitetura Atual

### Componentes do Sistema

#### **1. SQLite - Dados Estruturados** ✅ BEM RESOLVIDO
**Localização:** `jung_core.py:595-899`

**Tabelas Principais:**
- `users` - Cadastro de usuários
- `conversations` - Metadados de conversas (IDs, timestamps, métricas)
- `user_facts_v2` - Fatos extraídos com LLM (hierárquico: categoria → tipo → atributo)
- `user_patterns` - Padrões comportamentais detectados
- `archetype_conflicts` - Conflitos arquetípicos registrados
- `agent_development` - Evolução do agente por usuário

**Extração de Fatos:**
- Sistema LLM-based com fallback regex (`llm_fact_extractor.py`)
- Categorias: RELACIONAMENTO (vida pessoal) e TRABALHO (vida profissional)
- Confiança por fato (0.0 a 1.0)

#### **2. ChromaDB - Memória Semântica** ⚠️ REQUER APRIMORAMENTO
**Localização:** `jung_core.py:480-502, 1140-1216, 1369-1472`

**Armazenamento Atual:**
```python
# Documento completo salvo no ChromaDB
doc_content = """
Usuário: {user_name}
Input: {user_input}
Resposta: {ai_response}

=== VOZES INTERNAS ===
{archetype_analyses}

=== CONFLITOS DETECTADOS ===
{detected_conflicts}
"""

# Metadata atual
metadata = {
    "user_id": user_id,
    "user_name": user_name,
    "session_id": session_id,
    "timestamp": datetime.now().isoformat(),
    "conversation_id": conversation_id,
    "tension_level": tension_level,
    "affective_charge": affective_charge,
    "existential_depth": existential_depth,
    "intensity_level": intensity_level,
    "complexity": complexity,
    "keywords": ",".join(keywords),
    "has_conflicts": bool(detected_conflicts)
}
```

**Busca Semântica Atual** (`jung_core.py:1369-1472`):
```python
def semantic_search(user_id, query, k=5, chat_history=None):
    # Enriquece query com últimas 3 mensagens do chat_history
    enriched_query = query + " " + chat_history_snippet

    # Busca vetorial com filtro de user_id
    results = vectorstore.similarity_search_with_score(
        enriched_query,
        k=k * 2,  # Busca mais para filtrar manualmente
        filter={"user_id": user_id}
    )

    # Filtra manualmente para evitar vazamento entre usuários
    # Converte distância em similaridade
    # Retorna top k memórias
```

**Construção de Contexto** (`jung_core.py:1505-1618`):
```python
def build_rich_context(user_id, current_input, k_memories=5, chat_history=None):
    # Combina:
    # 1. Histórico da conversa atual (últimas 6 mensagens)
    # 2. Fatos estruturados do SQLite
    # 3. Memórias semânticas do ChromaDB (k=5)
    # 4. Padrões detectados
```

### Problemas Identificados

#### **Problema 1: Busca Vetorial Simples**
- Apenas similaridade cosine, sem ponderação por recência, emoção ou contexto relacional
- k=5 fixo pode ser insuficiente para conversas complexas
- Não captura nuances temporais (memórias antigas vs recentes)

#### **Problema 2: Query Enrichment Limitado**
- Enriquece apenas com últimas 3 mensagens do usuário
- Não utiliza fatos estruturados para enriquecer a busca
- Não detecta tópicos ou pessoas mencionadas

#### **Problema 3: Sem Consolidação de Memória**
- Memórias individuais acumulam sem resumos ou agrupamentos
- Redundâncias não são tratadas
- Sem "memória episódica" de longo prazo

#### **Problema 4: Metadata Pobre**
- Falta estratificação temporal (dia, semana, mês)
- Não rastreia menções a pessoas específicas
- Não categoriza por tópicos (trabalho, família, saúde)

#### **Problema 5: Fatos e Memórias Desconectados**
- SQLite (fatos estruturados) e ChromaDB (memória semântica) não conversam
- Não há cross-referencing entre sistemas

---

## 🎯 Plano de Aprimoramento - 6 Fases

---

## **FASE 1: Metadata Enriquecido e Organização Temporal** 🏷️

### Objetivo
Adicionar campos temporais, emocionais e relacionais ao metadata do ChromaDB para permitir filtragem e reranking inteligente.

### Implementação

#### **1.1 Expandir Metadata na Função `save_conversation()`**
**Arquivo:** `jung_core.py:1100-1264`

**Metadata Atual → Metadata Enriquecido:**
```python
# ANTES (linha ~1160)
metadata = {
    "user_id": user_id,
    "user_name": user_name,
    "session_id": session_id or "",
    "timestamp": datetime.now().isoformat(),
    "conversation_id": conversation_id,
    "tension_level": tension_level,
    "affective_charge": affective_charge,
    "existential_depth": existential_depth,
    "intensity_level": intensity_level,
    "complexity": complexity,
    "keywords": ",".join(keywords) if keywords else "",
    "has_conflicts": len(detected_conflicts) > 0 if detected_conflicts else False
}

# DEPOIS (NOVO)
now = datetime.now()
metadata = {
    # Existentes (manter)
    "user_id": user_id,
    "user_name": user_name,
    "session_id": session_id or "",
    "timestamp": now.isoformat(),
    "conversation_id": conversation_id,
    "tension_level": tension_level,
    "affective_charge": affective_charge,
    "existential_depth": existential_depth,
    "intensity_level": intensity_level,
    "complexity": complexity,
    "keywords": ",".join(keywords) if keywords else "",
    "has_conflicts": len(detected_conflicts) > 0 if detected_conflicts else False,

    # NOVOS - Temporal Estratificado
    "day_bucket": now.strftime("%Y-%m-%d"),        # Ex: "2026-01-02"
    "week_bucket": now.strftime("%Y-W%W"),         # Ex: "2026-W01"
    "month_bucket": now.strftime("%Y-%m"),         # Ex: "2026-01"
    "recency_tier": self._calculate_recency_tier(now),  # "recent" | "medium" | "old"

    # NOVOS - Emocional/Temático
    "emotional_intensity": round(affective_charge + tension_level, 2),  # Score combinado
    "dominant_archetype": self._get_dominant_archetype(archetype_analyses) if archetype_analyses else "",

    # NOVOS - Relacional
    "mentions_people": ",".join(self._extract_people_from_conversation(conversation_id)),
    "topics": ",".join(self._extract_topics_from_keywords(keywords)),
}
```

#### **1.2 Implementar Funções Auxiliares**
**Adicionar em `HybridDatabaseManager` (jung_core.py):**

```python
def _calculate_recency_tier(self, timestamp: datetime) -> str:
    """
    Calcula tier de recência da conversa

    Args:
        timestamp: Timestamp da conversa

    Returns:
        "recent" (≤30 dias) | "medium" (31-90 dias) | "old" (>90 dias)
    """
    days_ago = (datetime.now() - timestamp).days

    if days_ago <= 30:
        return "recent"
    elif days_ago <= 90:
        return "medium"
    else:
        return "old"

def _get_dominant_archetype(self, archetype_analyses: Dict) -> str:
    """
    Retorna arquétipo com maior intensidade

    Args:
        archetype_analyses: Dict com análises arquetípicas

    Returns:
        Nome do arquétipo dominante ou ""
    """
    if not archetype_analyses:
        return ""

    dominant = max(
        archetype_analyses.items(),
        key=lambda x: x[1].intensity if hasattr(x[1], 'intensity') else 0
    )

    return dominant[0] if dominant else ""

def _extract_people_from_conversation(self, conversation_id: int) -> List[str]:
    """
    Extrai nomes de pessoas mencionadas nos fatos desta conversa

    Args:
        conversation_id: ID da conversa

    Returns:
        Lista de nomes próprios
    """
    cursor = self.conn.cursor()

    # Verificar se user_facts_v2 existe
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='user_facts_v2'
    """)
    use_v2 = cursor.fetchone() is not None

    if use_v2:
        cursor.execute("""
            SELECT fact_value
            FROM user_facts_v2
            WHERE source_conversation_id = ?
            AND fact_attribute = 'nome'
            AND is_current = 1
        """, (conversation_id,))
    else:
        cursor.execute("""
            SELECT fact_value
            FROM user_facts
            WHERE source_conversation_id = ?
            AND fact_key = 'nome'
            AND is_current = 1
        """, (conversation_id,))

    names = [row[0] for row in cursor.fetchall() if row[0]]
    return names

def _extract_topics_from_keywords(self, keywords: List[str]) -> List[str]:
    """
    Classifica keywords em tópicos amplos

    Args:
        keywords: Lista de keywords da conversa

    Returns:
        Lista de tópicos detectados
    """
    if not keywords:
        return []

    # Mapeamento de keywords para tópicos
    topic_mapping = {
        "trabalho": ["trabalho", "emprego", "empresa", "carreira", "chefe", "colega", "projeto"],
        "familia": ["esposa", "marido", "filho", "filha", "pai", "mae", "familia", "casa"],
        "saude": ["saude", "medico", "doença", "ansiedade", "depressao", "insonia", "terapia"],
        "relacionamento": ["amigo", "amizade", "namoro", "relacionamento", "amor"],
        "lazer": ["viagem", "hobby", "leitura", "esporte", "musica"],
        "dinheiro": ["dinheiro", "financeiro", "salario", "conta", "divida"],
    }

    topics = set()
    keywords_lower = [k.lower() for k in keywords]

    for topic, topic_keywords in topic_mapping.items():
        if any(kw in " ".join(keywords_lower) for kw in topic_keywords):
            topics.add(topic)

    return list(topics)
```

#### **1.3 Implementar Decay Temporal**
**Adicionar em `HybridDatabaseManager`:**

```python
def calculate_temporal_boost(self, memory_timestamp: str, mode: str = "balanced") -> float:
    """
    Calcula boost temporal para reranking de memórias

    Args:
        memory_timestamp: Timestamp ISO da memória
        mode: Modo de decay ("recent_focused" | "balanced" | "archeological")

    Returns:
        Float multiplicador (0.5 a 1.5)
    """
    try:
        mem_time = datetime.fromisoformat(memory_timestamp)
    except:
        return 1.0  # Fallback se timestamp inválido

    days_ago = (datetime.now() - mem_time).days

    if mode == "recent_focused":
        # Valoriza últimos 7 dias, penaliza antigas
        if days_ago <= 7:
            return 1.5
        elif days_ago <= 30:
            return 1.2
        elif days_ago <= 90:
            return 1.0
        else:
            return 0.7

    elif mode == "balanced":
        # Equilíbrio entre recente e histórico
        if days_ago <= 30:
            return 1.2
        elif days_ago <= 90:
            return 1.0
        else:
            return 0.9

    elif mode == "archeological":
        # Valoriza padrões de longo prazo
        if days_ago <= 30:
            return 1.0
        elif days_ago <= 90:
            return 1.1
        else:
            return 1.3  # Boost para memórias antigas

    return 1.0  # Default
```

### Checklist de Implementação Fase 1

- [ ] Adicionar novos campos ao metadata em `save_conversation()`
- [ ] Implementar `_calculate_recency_tier()`
- [ ] Implementar `_get_dominant_archetype()`
- [ ] Implementar `_extract_people_from_conversation()`
- [ ] Implementar `_extract_topics_from_keywords()`
- [ ] Implementar `calculate_temporal_boost()`
- [ ] Testar com 10 conversas e validar metadata no ChromaDB
- [ ] Documentar novos campos no README

---

## **FASE 2: Query Enrichment Avançado** 🔍

### Objetivo
Enriquecer a query de busca semântica com contexto estruturado (fatos, pessoas, tópicos) para melhorar relevância dos resultados.

### Implementação

#### **2.1 Multi-Stage Query Enhancement**
**Modificar `semantic_search()` em jung_core.py:1369-1472:**

**ANTES:**
```python
# Query enriquecida com histórico recente (se disponível)
enriched_query = query

if chat_history and len(chat_history) > 0:
    recent_context = " ".join([
        msg["content"][:100]
        for msg in chat_history[-3:]
        if msg["role"] == "user"
    ])
    enriched_query = f"{recent_context} {query}"
```

**DEPOIS:**
```python
# Query enriquecida multi-stage
enriched_query = self._build_enriched_query(
    user_id=user_id,
    user_input=query,
    chat_history=chat_history
)
```

**Adicionar nova função:**
```python
def _build_enriched_query(self, user_id: str, user_input: str, chat_history: List[Dict] = None) -> str:
    """
    Constrói query enriquecida com múltiplas fontes

    Args:
        user_id: ID do usuário
        user_input: Input do usuário
        chat_history: Histórico da conversa atual

    Returns:
        Query enriquecida
    """
    query_parts = [user_input]  # Base

    # CAMADA 1: Contexto conversacional recente (expandir de 3 para 5)
    if chat_history and len(chat_history) > 0:
        recent = " ".join([
            msg["content"][:100]
            for msg in chat_history[-5:]  # Era -3, agora -5
            if msg["role"] == "user"
        ])
        query_parts.append(recent)

    # CAMADA 2: Fatos relevantes do usuário (NOVO)
    # Buscar nomes de pessoas mencionadas no input
    mentioned_names = self._extract_names_from_text(user_input)

    if mentioned_names:
        # Buscar fatos sobre essas pessoas
        cursor = self.conn.cursor()

        # Usar user_facts_v2 se disponível
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='user_facts_v2'
        """)
        use_v2 = cursor.fetchone() is not None

        relevant_facts = []
        for name in mentioned_names:
            if use_v2:
                cursor.execute("""
                    SELECT fact_type, fact_attribute, fact_value
                    FROM user_facts_v2
                    WHERE user_id = ? AND fact_value LIKE ? AND is_current = 1
                    LIMIT 3
                """, (user_id, f"%{name}%"))
            else:
                cursor.execute("""
                    SELECT fact_key, fact_value
                    FROM user_facts
                    WHERE user_id = ? AND fact_value LIKE ? AND is_current = 1
                    LIMIT 3
                """, (user_id, f"%{name}%"))

            relevant_facts.extend([
                f"{row[0]}: {row[1]}" if use_v2 else f"{row[0]}: {row[1]}"
                for row in cursor.fetchall()
            ])

        if relevant_facts:
            query_parts.append(" ".join(relevant_facts[:5]))

    # CAMADA 3: Tópicos implícitos (NOVO)
    topics = self._detect_topics_in_text(user_input)
    if topics:
        query_parts.append(" ".join(topics))

    return " ".join(query_parts)

def _extract_names_from_text(self, text: str) -> List[str]:
    """
    Extrai nomes próprios do texto (heurística simples)

    Args:
        text: Texto para análise

    Returns:
        Lista de possíveis nomes próprios
    """
    import re

    # Padrão: Palavras capitalizadas que não são início de frase
    # Ex: "Minha esposa Ana" -> captura "Ana"
    pattern = r'\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)\b'

    # Filtrar palavras comuns que não são nomes
    stopwords = {'O', 'A', 'Os', 'As', 'Um', 'Uma', 'De', 'Da', 'Do', 'Em', 'No', 'Na'}

    matches = re.findall(pattern, text)
    names = [m for m in matches if m not in stopwords]

    return list(set(names))  # Remover duplicatas

def _detect_topics_in_text(self, text: str) -> List[str]:
    """
    Detecta tópicos mencionados no texto

    Args:
        text: Texto para análise

    Returns:
        Lista de tópicos detectados
    """
    text_lower = text.lower()

    topic_keywords = {
        "trabalho": ["trabalho", "emprego", "empresa", "chefe", "colega", "reunião"],
        "família": ["esposa", "marido", "filho", "filha", "pai", "mãe", "família"],
        "saúde": ["saúde", "doença", "médico", "ansiedade", "depressão", "terapia"],
        "relacionamento": ["amigo", "namoro", "amor", "relacionamento"],
    }

    detected = []
    for topic, keywords in topic_keywords.items():
        if any(kw in text_lower for kw in keywords):
            detected.append(topic)

    return detected
```

#### **2.2 Hypothetical Document Embeddings (HyDE) - Opcional**
**Para queries muito curtas/ambíguas:**

```python
def _generate_hypothetical_response(self, user_input: str, chat_history: List[Dict]) -> str:
    """
    Gera resposta hipotética para melhorar busca semântica
    Técnica HyDE (Hypothetical Document Embeddings)

    Args:
        user_input: Input curto/ambíguo do usuário
        chat_history: Histórico recente

    Returns:
        Query enriquecida com resposta hipotética
    """
    # Só usar HyDE se input for muito curto
    if len(user_input.split()) >= 5:
        return user_input

    # Formatar histórico recente
    history_text = "\n".join([
        f"{'Usuário' if msg['role'] == 'user' else 'Jung'}: {msg['content'][:100]}"
        for msg in chat_history[-3:]
    ])

    prompt = f"""Histórico recente:
{history_text}

Usuário perguntou: "{user_input}"

Gere UMA resposta hipotética breve (2-3 frases) que Jung daria.
Essa resposta será usada para buscar memórias relevantes."""

    try:
        if self.anthropic_client:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            hypothetical = response.content[0].text.strip()
        else:
            # Fallback: retornar input original
            return user_input

        # Combinar input + resposta hipotética
        return f"{user_input} {hypothetical}"

    except Exception as e:
        logger.warning(f"Erro ao gerar resposta hipotética: {e}")
        return user_input
```

**Integrar no `semantic_search()` (opcional):**
```python
# Usar HyDE se query for muito curta
if len(query.split()) < 5 and chat_history:
    enriched_query = self._generate_hypothetical_response(query, chat_history)
else:
    enriched_query = self._build_enriched_query(user_id, query, chat_history)
```

### Checklist de Implementação Fase 2

- [ ] Implementar `_build_enriched_query()`
- [ ] Implementar `_extract_names_from_text()`
- [ ] Implementar `_detect_topics_in_text()`
- [ ] Integrar no `semantic_search()`
- [ ] (Opcional) Implementar `_generate_hypothetical_response()` para HyDE
- [ ] Testar com queries curtas ("e ela?") e longas ("como está minha esposa Ana?")
- [ ] Validar que nomes e tópicos são corretamente detectados

---

## **FASE 3: Busca Multi-Stage e Reranking Inteligente** 🎯

### Objetivo
Implementar busca em dois estágios (broad → narrow) com reranking inteligente baseado em múltiplos fatores (temporal, emocional, relacional, temático).

### Implementação

#### **3.1 Refatorar `semantic_search()` para Two-Stage Retrieval**
**Modificar jung_core.py:1369-1472:**

**ESTRUTURA ATUAL:**
```python
def semantic_search(user_id, query, k=5, chat_history=None):
    # Busca única com k fixo
    results = vectorstore.similarity_search_with_score(query, k=k*2, filter={"user_id": user_id})
    # Processamento básico
    return memories[:k]
```

**NOVA ESTRUTURA:**
```python
def semantic_search(self, user_id: str, query: str, k: int = None,
                   chat_history: List[Dict] = None) -> List[Dict]:
    """
    Busca semântica com two-stage retrieval e reranking inteligente

    STAGE 1: Broad retrieval (k=20)
    STAGE 2: Intelligent reranking com múltiplos fatores

    Args:
        user_id: ID do usuário
        query: Texto da consulta
        k: Número de resultados (None = adaptativo)
        chat_history: Histórico da conversa atual

    Returns:
        Lista de memórias rerankeadas
    """

    if not self.chroma_enabled:
        logger.warning("ChromaDB desabilitado. Retornando conversas recentes do SQLite.")
        return self._fallback_keyword_search(user_id, query, k or 5)

    try:
        # Calcular k adaptativo se não fornecido
        if k is None:
            k = self._calculate_adaptive_k(query, chat_history, user_id)

        logger.info(f"🔍 Busca semântica two-stage para user_id='{user_id}' (k={k})")

        # Enriquecer query
        enriched_query = self._build_enriched_query(user_id, query, chat_history)

        # STAGE 1: BROAD RETRIEVAL
        broad_k = max(k * 3, 15)  # Buscar pelo menos 3x mais
        logger.info(f"   STAGE 1: Broad retrieval (k={broad_k})")

        results = self.vectorstore.similarity_search_with_score(
            enriched_query,
            k=broad_k,
            filter={"user_id": str(user_id)}
        )

        logger.info(f"   Resultados retornados: {len(results)}")

        # STAGE 2: INTELLIGENT RERANKING
        logger.info(f"   STAGE 2: Reranking inteligente")
        reranked = self._rerank_memories(
            results=results,
            user_id=user_id,
            query=query,
            chat_history=chat_history
        )

        # Retornar top k
        top_memories = reranked[:k]

        logger.info(f"✅ Top {len(top_memories)} memórias após reranking:")
        for i, mem in enumerate(top_memories[:3], 1):
            logger.info(f"   {i}. [score={mem['final_score']:.3f}] {mem['user_input'][:50]}...")

        return top_memories

    except Exception as e:
        logger.error(f"❌ Erro na busca semântica: {e}")
        return self._fallback_keyword_search(user_id, query, k or 5)
```

#### **3.2 Implementar Adaptive k**
```python
def _calculate_adaptive_k(self, query: str, chat_history: List[Dict], user_id: str) -> int:
    """
    Calcula k adaptativo baseado em complexidade do contexto

    Args:
        query: Query do usuário
        chat_history: Histórico da conversa
        user_id: ID do usuário

    Returns:
        k dinâmico entre 3 e 12
    """
    base_k = 5

    # Fator 1: Comprimento do histórico
    if chat_history and len(chat_history) > 10:
        base_k += 2  # Conversas longas precisam de mais contexto

    # Fator 2: Complexidade da query
    query_words = len(query.split())
    if query_words > 20:
        base_k += 2
    elif query_words < 5:
        base_k -= 1  # Queries curtas precisam de menos

    # Fator 3: Múltiplas pessoas mencionadas
    mentioned_names = self._extract_names_from_text(query)
    if len(mentioned_names) > 1:
        base_k += len(mentioned_names)

    # Fator 4: Histórico total do usuário
    total_conversations = self.count_conversations(user_id)
    if total_conversations < 20:
        base_k = min(base_k, 3)  # Limitar para usuários novos

    # Limitar entre 3 e 12
    return max(3, min(base_k, 12))
```

#### **3.3 Implementar Reranking Inteligente**
```python
def _rerank_memories(self, results: List[tuple], user_id: str, query: str,
                    chat_history: List[Dict] = None) -> List[Dict]:
    """
    Reranking inteligente com múltiplos fatores

    Args:
        results: Lista de (Document, score) do ChromaDB
        user_id: ID do usuário
        query: Query original
        chat_history: Histórico da conversa

    Returns:
        Lista de memórias rerankeadas com scores combinados
    """
    reranked = []

    # Extrair informações da query para boosting
    query_names = set(self._extract_names_from_text(query))
    query_topics = set(self._detect_topics_in_text(query))

    for doc, base_score in results:
        metadata = doc.metadata

        # Validação extra: filtrar manualmente user_id errado
        doc_user_id = str(metadata.get('user_id', ''))
        if doc_user_id != str(user_id):
            logger.error(f"🚨 Removendo doc com user_id='{doc_user_id}' (esperado='{user_id}')")
            continue

        # === CÁLCULO DE BOOSTS ===

        # 1. BOOST TEMPORAL
        temporal_boost = self.calculate_temporal_boost(
            metadata.get('timestamp', ''),
            mode="balanced"
        )

        # 2. BOOST EMOCIONAL
        emotional_intensity = metadata.get('emotional_intensity', 0.0)
        emotional_boost = 1.0
        if emotional_intensity > 1.5:
            emotional_boost = 1.3  # Priorizar momentos emocionalmente intensos
        elif emotional_intensity > 2.5:
            emotional_boost = 1.5  # Muito intenso

        # 3. BOOST DE TÓPICO
        memory_topics = set(metadata.get('topics', '').split(',')) if metadata.get('topics') else set()
        topic_boost = 1.0
        if query_topics & memory_topics:  # Interseção
            topic_boost = 1.2

        # 4. BOOST DE PESSOA MENCIONADA (mais forte)
        memory_people = set(metadata.get('mentions_people', '').split(',')) if metadata.get('mentions_people') else set()
        person_boost = 1.0
        if query_names & memory_people:  # Interseção
            person_boost = 1.5  # FORTE boost se mesma pessoa mencionada

        # 5. BOOST DE PROFUNDIDADE EXISTENCIAL
        depth = metadata.get('existential_depth', 0.0)
        depth_boost = 1.0
        if depth > 0.7:
            depth_boost = 1.1  # Leve boost para conversas profundas

        # 6. BOOST DE CONFLITO ARQUETÍPICO
        conflict_boost = 1.0
        if metadata.get('has_conflicts', False):
            conflict_boost = 1.1  # Leve boost para momentos de conflito interno

        # === SCORE FINAL COMBINADO ===
        final_score = (
            base_score *
            temporal_boost *
            emotional_boost *
            topic_boost *
            person_boost *
            depth_boost *
            conflict_boost
        )

        # Extrair conteúdo do documento
        user_input_match = re.search(r"Input:\s*(.+?)(?:\n|Resposta:|$)", doc.page_content, re.DOTALL)
        user_input_text = user_input_match.group(1).strip() if user_input_match else ""

        response_match = re.search(r"Resposta:\s*(.+?)(?:\n|===|$)", doc.page_content, re.DOTALL)
        response_text = response_match.group(1).strip() if response_match else ""

        reranked.append({
            'conversation_id': metadata.get('conversation_id'),
            'user_input': user_input_text,
            'ai_response': response_text,
            'timestamp': metadata.get('timestamp', ''),
            'base_score': base_score,
            'final_score': final_score,
            'boosts': {
                'temporal': round(temporal_boost, 2),
                'emotional': round(emotional_boost, 2),
                'topic': round(topic_boost, 2),
                'person': round(person_boost, 2),
                'depth': round(depth_boost, 2),
                'conflict': round(conflict_boost, 2),
            },
            'metadata': metadata,
            'full_document': doc.page_content,
        })

    # Ordenar por final_score (decrescente)
    reranked.sort(key=lambda x: x['final_score'], reverse=True)

    # Log dos top 3 com detalhes de boosts
    for i, mem in enumerate(reranked[:3], 1):
        logger.info(f"   Memória {i}: base={mem['base_score']:.3f}, final={mem['final_score']:.3f}")
        logger.info(f"      Boosts: {mem['boosts']}")

    return reranked
```

### Checklist de Implementação Fase 3

- [ ] Refatorar `semantic_search()` para two-stage
- [ ] Implementar `_calculate_adaptive_k()`
- [ ] Implementar `_rerank_memories()`
- [ ] Validar que boosts estão sendo aplicados corretamente (logs)
- [ ] Testar com queries que mencionam pessoas ("como está Ana?")
- [ ] Testar com queries sobre tópicos ("problemas no trabalho")
- [ ] Comparar resultados antes/depois do reranking

---

## **FASE 4: Consolidação e Memória de Longo Prazo** 🧠

### Objetivo
Implementar sistema de consolidação de memórias para reduzir redundância e criar "memória episódica" de longo prazo.

### Implementação

#### **4.1 Memory Summarization (Background Job)**

**Criar novo arquivo:** `jung_memory_consolidation.py`

```python
"""
jung_memory_consolidation.py - Sistema de Consolidação de Memórias

Responsável por:
- Agrupar memórias similares por período
- Gerar resumos temáticos com LLM
- Criar documentos "consolidated" no ChromaDB
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
import json

logger = logging.getLogger(__name__)


class MemoryConsolidator:
    """
    Consolida memórias similares em resumos temáticos
    """

    def __init__(self, db_manager):
        """
        Args:
            db_manager: HybridDatabaseManager instance
        """
        self.db = db_manager

    def consolidate_user_memories(self, user_id: str, lookback_days: int = 90):
        """
        Consolida memórias de um usuário nos últimos N dias

        Args:
            user_id: ID do usuário
            lookback_days: Período de lookback (default: 90 dias)
        """
        logger.info(f"📦 Iniciando consolidação de memórias para user_id={user_id} (lookback={lookback_days} dias)")

        # 1. Buscar todas as memórias do período
        start_date = datetime.now() - timedelta(days=lookback_days)

        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, user_input, ai_response, timestamp, keywords,
                   tension_level, affective_charge, existential_depth
            FROM conversations
            WHERE user_id = ?
            AND timestamp >= ?
            ORDER BY timestamp ASC
        """, (user_id, start_date.isoformat()))

        memories = [dict(row) for row in cursor.fetchall()]

        if len(memories) < 5:
            logger.info(f"   Menos de 5 memórias encontradas ({len(memories)}), consolidação não necessária")
            return

        logger.info(f"   Encontradas {len(memories)} memórias para consolidar")

        # 2. Agrupar por tópico usando keywords
        clusters = self._cluster_by_topic(memories)

        logger.info(f"   Identificados {len(clusters)} clusters temáticos")

        # 3. Para cada cluster grande (≥5 memórias), gerar resumo
        for topic, cluster_memories in clusters.items():
            if len(cluster_memories) >= 5:
                logger.info(f"   Consolidando cluster '{topic}' ({len(cluster_memories)} memórias)")
                self._create_consolidated_memory(
                    user_id=user_id,
                    topic=topic,
                    memories=cluster_memories,
                    lookback_days=lookback_days
                )

    def _cluster_by_topic(self, memories: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Agrupa memórias por tópico baseado em keywords

        Args:
            memories: Lista de memórias

        Returns:
            Dict {topic: [memórias]}
        """
        clusters = {}

        for memory in memories:
            keywords = memory.get('keywords', '').split(',')

            # Detectar tópico principal
            topic = self._identify_main_topic(keywords)

            if topic not in clusters:
                clusters[topic] = []

            clusters[topic].append(memory)

        return clusters

    def _identify_main_topic(self, keywords: List[str]) -> str:
        """
        Identifica tópico principal baseado em keywords

        Args:
            keywords: Lista de keywords

        Returns:
            Nome do tópico
        """
        if not keywords or not keywords[0]:
            return "geral"

        keywords_lower = [k.lower().strip() for k in keywords if k]

        topic_mapping = {
            "trabalho": ["trabalho", "emprego", "empresa", "carreira", "chefe", "colega"],
            "família": ["esposa", "marido", "filho", "filha", "pai", "mae", "familia"],
            "saúde": ["saude", "doença", "ansiedade", "depressao", "insonia", "terapia"],
            "relacionamento": ["amigo", "namoro", "amor", "relacionamento"],
            "lazer": ["viagem", "hobby", "leitura"],
        }

        for topic, topic_keywords in topic_mapping.items():
            if any(kw in " ".join(keywords_lower) for kw in topic_keywords):
                return topic

        return "geral"

    def _create_consolidated_memory(self, user_id: str, topic: str,
                                    memories: List[Dict], lookback_days: int):
        """
        Cria memória consolidada e salva no ChromaDB

        Args:
            user_id: ID do usuário
            topic: Tópico do cluster
            memories: Memórias do cluster
            lookback_days: Período de lookback
        """
        # Gerar resumo com LLM
        summary = self._generate_summary_with_llm(topic, memories)

        # IDs das conversas originais
        source_ids = [mem['id'] for mem in memories]

        # Calcular métricas agregadas
        avg_tension = sum(m.get('tension_level', 0) for m in memories) / len(memories)
        avg_affective = sum(m.get('affective_charge', 0) for m in memories) / len(memories)
        avg_depth = sum(m.get('existential_depth', 0) for m in memories) / len(memories)

        # Período da consolidação
        timestamps = [datetime.fromisoformat(m['timestamp']) for m in memories]
        period_start = min(timestamps).strftime("%Y-%m-%d")
        period_end = max(timestamps).strftime("%Y-%m-%d")

        # Construir documento consolidado
        doc_content = f"""
=== MEMÓRIA CONSOLIDADA ===
TÓPICO: {topic.upper()}
PERÍODO: {period_start} a {period_end} ({len(memories)} conversas)

{summary}

MÉTRICAS DO PERÍODO:
- Tensão média: {avg_tension:.2f}
- Carga afetiva média: {avg_affective:.2f}
- Profundidade média: {avg_depth:.2f}
"""

        # Metadata
        metadata = {
            "user_id": user_id,
            "type": "consolidated",
            "topic": topic,
            "period_start": period_start,
            "period_end": period_end,
            "count": len(memories),
            "source_ids": json.dumps(source_ids),
            "avg_tension": round(avg_tension, 2),
            "avg_affective": round(avg_affective, 2),
            "avg_depth": round(avg_depth, 2),
            "timestamp": datetime.now().isoformat(),
            "recency_tier": "consolidated",  # Tier especial
        }

        # Salvar no ChromaDB
        chroma_id = f"consolidated_{user_id}_{topic}_{period_end}"

        from langchain.schema import Document
        doc = Document(page_content=doc_content, metadata=metadata)

        try:
            # Tentar adicionar
            self.db.vectorstore.add_documents([doc], ids=[chroma_id])
            logger.info(f"✅ Memória consolidada criada: {chroma_id}")
        except Exception as e:
            # Se já existe, substituir
            if "already exists" in str(e).lower():
                logger.info(f"   Substituindo memória consolidada existente: {chroma_id}")
                self.db.vectorstore.delete([chroma_id])
                self.db.vectorstore.add_documents([doc], ids=[chroma_id])
            else:
                logger.error(f"❌ Erro ao criar memória consolidada: {e}")

    def _generate_summary_with_llm(self, topic: str, memories: List[Dict]) -> str:
        """
        Gera resumo temático das memórias usando LLM

        Args:
            topic: Tópico do cluster
            memories: Lista de memórias

        Returns:
            Resumo gerado
        """
        # Construir prompt com as memórias
        memories_text = "\n\n".join([
            f"[{mem['timestamp'][:10]}] Usuário: {mem['user_input'][:200]}\nJung: {mem['ai_response'][:200]}"
            for mem in memories[:10]  # Limitar a 10 para não estourar tokens
        ])

        prompt = f"""Você é um sistema de consolidação de memórias do Jung.

Analise as {len(memories)} conversas abaixo sobre o tema "{topic}" e gere um RESUMO CONSOLIDADO estruturado:

CONVERSAS:
{memories_text}

Gere um resumo seguindo este formato:

FATOS CONSOLIDADOS:
- [Liste 3-5 fatos principais mencionados repetidamente]

PADRÕES EMOCIONAIS:
- [Descreva padrões emocionais recorrentes, gatilhos, sentimentos]

EVOLUÇÃO:
- [Descreva como o tema evoluiu ao longo do período, se houve mudanças]

Seja conciso mas informativo. Máximo 200 palavras."""

        try:
            if self.db.anthropic_client:
                response = self.db.anthropic_client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                summary = response.content[0].text.strip()
            elif self.db.xai_client:
                response = self.db.xai_client.chat.completions.create(
                    model="grok-beta",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500
                )
                summary = response.choices[0].message.content.strip()
            else:
                # Fallback: resumo manual básico
                summary = f"Consolidação de {len(memories)} conversas sobre {topic}."

            return summary

        except Exception as e:
            logger.error(f"Erro ao gerar resumo com LLM: {e}")
            return f"Consolidação de {len(memories)} conversas sobre {topic}."


def run_consolidation_job(db_manager):
    """
    Job para rodar consolidação em todos os usuários

    Args:
        db_manager: HybridDatabaseManager instance
    """
    logger.info("🔄 Iniciando job de consolidação de memórias")

    consolidator = MemoryConsolidator(db_manager)

    # Buscar todos os usuários
    cursor = db_manager.conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM conversations")
    user_ids = [row[0] for row in cursor.fetchall()]

    logger.info(f"   Consolidando memórias para {len(user_ids)} usuários")

    for user_id in user_ids:
        try:
            consolidator.consolidate_user_memories(user_id, lookback_days=90)
        except Exception as e:
            logger.error(f"Erro ao consolidar memórias de {user_id}: {e}")

    logger.info("✅ Job de consolidação concluído")
```

#### **4.2 Agendar Background Job**

**Adicionar em `telegram_bot.py` ou criar `jobs.py`:**

```python
from apscheduler.schedulers.background import BackgroundScheduler
from jung_memory_consolidation import run_consolidation_job

# Inicializar scheduler
scheduler = BackgroundScheduler()

# Agendar consolidação mensal (todo dia 1 às 03:00)
scheduler.add_job(
    func=lambda: run_consolidation_job(db_manager),
    trigger='cron',
    day=1,
    hour=3,
    minute=0
)

scheduler.start()
logger.info("✅ Scheduler de consolidação iniciado (mensal)")
```

#### **4.3 Fact-Conversation Linking**

**Modificar `save_conversation()` para linkar fatos:**

```python
# Após salvar fatos (linha ~1245 em jung_core.py)
# Adicionar linking ao metadata

# Buscar fatos extraídos desta conversa
cursor.execute("""
    SELECT id FROM user_facts_v2
    WHERE source_conversation_id = ? AND is_current = 1
""", (conversation_id,))
fact_ids = [row[0] for row in cursor.fetchall()]

# Adicionar ao metadata antes de salvar no ChromaDB
metadata["extracted_fact_ids"] = ",".join(map(str, fact_ids))
```

### Checklist de Implementação Fase 4

- [ ] Criar `jung_memory_consolidation.py`
- [ ] Implementar `MemoryConsolidator` class
- [ ] Implementar `_cluster_by_topic()`
- [ ] Implementar `_generate_summary_with_llm()`
- [ ] Implementar `_create_consolidated_memory()`
- [ ] Adicionar job mensal no scheduler
- [ ] Testar consolidação manual com um usuário
- [ ] Validar que memórias consolidadas aparecem nas buscas
- [ ] Adicionar fact-conversation linking no metadata

---

## **FASE 5: Context Building Otimizado** 📝

### Objetivo
Melhorar a função `build_rich_context()` para construir contexto hierárquico e estratificado, com compressão inteligente.

### Implementação

#### **5.1 Refatorar `build_rich_context()`**
**Modificar jung_core.py:1505-1618:**

```python
def build_rich_context(self, user_id: str, current_input: str,
                      k_memories: int = None,
                      chat_history: List[Dict] = None) -> str:
    """
    Constrói contexto HIERÁRQUICO e ESTRATIFICADO

    Combina:
    - Histórico imediato (sempre incluir)
    - Fatos relevantes ao input (busca inteligente)
    - Memórias semânticas (reranked, agrupadas por recência)
    - Padrões detectados (se relevantes)
    - Memórias consolidadas (se existirem)

    Args:
        user_id: ID do usuário
        current_input: Input atual do usuário
        k_memories: Número de memórias (None = adaptativo)
        chat_history: Histórico da conversa atual

    Returns:
        Contexto formatado e hierárquico
    """
    logger.info(f"🏗️ Construindo contexto hierárquico para user_id={user_id}")

    user = self.get_user(user_id)
    name = user['user_name'] if user else "Usuário"

    context_parts = []

    # ===== LAYER 1: HISTÓRICO IMEDIATO =====
    context_parts.append("=== CONVERSA ATUAL ===\n")

    if chat_history and len(chat_history) > 0:
        recent = chat_history[-6:] if len(chat_history) > 6 else chat_history

        for msg in recent:
            role = "👤 Usuário" if msg["role"] == "user" else "🤖 Jung"
            content = msg["content"][:150] + "..." if len(msg["content"]) > 150 else msg["content"]
            context_parts.append(f"{role}: {content}")

    context_parts.append("")

    # ===== LAYER 2: FATOS RELEVANTES =====
    relevant_facts = self._search_relevant_facts(user_id, current_input)

    if relevant_facts:
        context_parts.append("=== FATOS RELEVANTES ===\n")
        context_parts.append(self._format_facts_hierarchically(relevant_facts))
        context_parts.append("")

    # ===== LAYER 3: MEMÓRIAS SEMÂNTICAS =====
    memories = self.semantic_search(user_id, current_input, k=k_memories, chat_history=chat_history)

    if memories:
        context_parts.append("=== MEMÓRIAS RELACIONADAS ===\n")

        # Separar por tipo e recência
        consolidated = [m for m in memories if m.get('metadata', {}).get('type') == 'consolidated']
        regular = [m for m in memories if m.get('metadata', {}).get('type') != 'consolidated']

        # Agrupar regulares por recência
        recent = [m for m in regular if m.get('metadata', {}).get('recency_tier') == 'recent']
        older = [m for m in regular if m.get('metadata', {}).get('recency_tier') != 'recent']

        # Memórias consolidadas primeiro (se existirem)
        if consolidated:
            context_parts.append("📦 Padrões de Longo Prazo (Consolidado):")
            for mem in consolidated[:1]:  # Apenas 1 consolidada
                context_parts.append(f"- {mem['full_document'][:300]}...")
            context_parts.append("")

        # Memórias recentes
        if recent:
            context_parts.append("🕐 Recente (últimos 30 dias):")
            for i, mem in enumerate(recent[:3], 1):
                timestamp = mem.get('timestamp', '')[:10]
                context_parts.append(f"{i}. [{timestamp}] {mem['user_input'][:100]}...")
            context_parts.append("")

        # Memórias antigas (se relevantes)
        if older:
            context_parts.append("📚 Histórico:")
            for i, mem in enumerate(older[:2], 1):
                timestamp = mem.get('timestamp', '')[:10]
                context_parts.append(f"{i}. [{timestamp}] {mem['user_input'][:100]}...")
            context_parts.append("")

    # ===== LAYER 4: PADRÕES DETECTADOS =====
    patterns = self._get_relevant_patterns(user_id, current_input)

    if patterns:
        context_parts.append("=== PADRÕES OBSERVADOS ===\n")
        for pattern in patterns[:2]:
            context_parts.append(f"- {pattern['pattern_name']}: {pattern['pattern_description']}")
        context_parts.append("")

    # Juntar tudo
    full_context = "\n".join(context_parts)

    # Comprimir se necessário
    full_context = self._compress_context_if_needed(full_context, max_tokens=2000)

    logger.info(f"✅ Contexto construído: {len(full_context)} caracteres")

    return full_context

def _search_relevant_facts(self, user_id: str, query: str) -> List[Dict]:
    """
    Busca fatos relevantes ao input atual

    Args:
        user_id: ID do usuário
        query: Input do usuário

    Returns:
        Lista de fatos relevantes
    """
    # Extrair nomes e tópicos da query
    mentioned_names = self._extract_names_from_text(query)
    mentioned_topics = self._detect_topics_in_text(query)

    cursor = self.conn.cursor()

    # Verificar estrutura V2
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='user_facts_v2'
    """)
    use_v2 = cursor.fetchone() is not None

    relevant_facts = []

    # Buscar fatos sobre pessoas mencionadas
    if mentioned_names:
        for name in mentioned_names:
            if use_v2:
                cursor.execute("""
                    SELECT fact_category, fact_type, fact_attribute, fact_value, confidence
                    FROM user_facts_v2
                    WHERE user_id = ? AND fact_value LIKE ? AND is_current = 1
                    LIMIT 5
                """, (user_id, f"%{name}%"))
            else:
                cursor.execute("""
                    SELECT fact_category, fact_key, fact_value
                    FROM user_facts
                    WHERE user_id = ? AND fact_value LIKE ? AND is_current = 1
                    LIMIT 5
                """, (user_id, f"%{name}%"))

            relevant_facts.extend([dict(row) for row in cursor.fetchall()])

    # Buscar fatos sobre tópicos mencionados
    if mentioned_topics:
        for topic in mentioned_topics:
            category_map = {
                "trabalho": "TRABALHO",
                "família": "RELACIONAMENTO",
                "saúde": "RELACIONAMENTO",
            }
            category = category_map.get(topic, "RELACIONAMENTO")

            if use_v2:
                cursor.execute("""
                    SELECT fact_category, fact_type, fact_attribute, fact_value, confidence
                    FROM user_facts_v2
                    WHERE user_id = ? AND fact_category = ? AND is_current = 1
                    LIMIT 5
                """, (user_id, category))
            else:
                cursor.execute("""
                    SELECT fact_category, fact_key, fact_value
                    FROM user_facts
                    WHERE user_id = ? AND fact_category = ? AND is_current = 1
                    LIMIT 5
                """, (user_id, category))

            relevant_facts.extend([dict(row) for row in cursor.fetchall()])

    return relevant_facts

def _format_facts_hierarchically(self, facts: List[Dict]) -> str:
    """
    Formata fatos de forma hierárquica

    Args:
        facts: Lista de fatos

    Returns:
        String formatada
    """
    if not facts:
        return ""

    # Agrupar por categoria
    by_category = {}
    for fact in facts:
        category = fact.get('fact_category', 'OUTROS')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(fact)

    lines = []
    for category, cat_facts in by_category.items():
        lines.append(f"{category}:")
        for fact in cat_facts[:5]:  # Limitar a 5 por categoria
            if 'fact_type' in fact:  # V2
                lines.append(f"  - {fact['fact_type']}.{fact['fact_attribute']}: {fact['fact_value']}")
            else:  # V1
                lines.append(f"  - {fact['fact_key']}: {fact['fact_value']}")

    return "\n".join(lines)

def _get_relevant_patterns(self, user_id: str, query: str) -> List[Dict]:
    """
    Busca padrões relevantes ao input

    Args:
        user_id: ID do usuário
        query: Input do usuário

    Returns:
        Lista de padrões relevantes
    """
    cursor = self.conn.cursor()

    # Buscar padrões que ocorrem frequentemente
    cursor.execute("""
        SELECT pattern_type, pattern_name, pattern_description, frequency_count
        FROM user_patterns
        WHERE user_id = ?
        ORDER BY frequency_count DESC, confidence_score DESC
        LIMIT 5
    """, (user_id,))

    patterns = [dict(row) for row in cursor.fetchall()]

    # Filtrar por relevância à query (simples: keywords)
    query_lower = query.lower()
    relevant = [
        p for p in patterns
        if any(word in query_lower for word in p['pattern_name'].lower().split())
    ]

    return relevant if relevant else patterns[:2]

def _compress_context_if_needed(self, context: str, max_tokens: int = 2000) -> str:
    """
    Comprime contexto se exceder limite de tokens

    Args:
        context: Contexto completo
        max_tokens: Limite de tokens

    Returns:
        Contexto original ou comprimido
    """
    # Estimativa: 1 token ≈ 4 caracteres
    estimated_tokens = len(context) // 4

    if estimated_tokens <= max_tokens:
        return context

    logger.warning(f"⚠️ Contexto muito longo ({estimated_tokens} tokens), comprimindo...")

    # Estratégia de compressão: manter apenas essencial
    # 1. Sempre manter histórico atual (primeiras linhas)
    # 2. Resumir fatos (manter apenas 3 por categoria)
    # 3. Reduzir memórias (manter apenas 2 recentes + 1 antiga)

    # Por simplicidade, truncar e logar warning
    # (Implementação completa com LLM seria mais sofisticada)
    max_chars = max_tokens * 4
    truncated = context[:max_chars] + "\n\n[... contexto truncado para otimização ...]"

    logger.warning(f"   Contexto truncado para {max_chars} caracteres")

    return truncated
```

### Checklist de Implementação Fase 5

- [ ] Refatorar `build_rich_context()` para hierárquico
- [ ] Implementar `_search_relevant_facts()`
- [ ] Implementar `_format_facts_hierarchically()`
- [ ] Implementar `_get_relevant_patterns()`
- [ ] Implementar `_compress_context_if_needed()`
- [ ] Testar com usuário que tem muitas memórias (>100)
- [ ] Validar que contexto está organizado e legível
- [ ] Verificar que memórias consolidadas aparecem no contexto

---

## **FASE 6: Monitoramento e Feedback Loop** 📊

### Objetivo
Implementar métricas para monitorar qualidade do sistema de memória e identificar problemas.

### Implementação

#### **6.1 Memory Quality Metrics**

**Criar novo arquivo:** `jung_memory_metrics.py`

```python
"""
jung_memory_metrics.py - Métricas de Qualidade da Memória

Monitora:
- Cobertura de memórias
- Gaps temporais
- Taxas de retrieval
- Qualidade de consolidação
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List

logger = logging.getLogger(__name__)


class MemoryQualityMetrics:
    """
    Calcula e monitora métricas de qualidade do sistema de memória
    """

    def __init__(self, db_manager):
        """
        Args:
            db_manager: HybridDatabaseManager instance
        """
        self.db = db_manager

    def calculate_coverage(self, user_id: str) -> float:
        """
        Calcula % de conversas que têm memórias recuperáveis no ChromaDB

        Args:
            user_id: ID do usuário

        Returns:
            Float entre 0 e 1
        """
        cursor = self.db.conn.cursor()

        # Total de conversas no SQLite
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM conversations
            WHERE user_id = ?
        """, (user_id,))
        total = cursor.fetchone()['total']

        if total == 0:
            return 0.0

        # Conversas com chroma_id (salvas no ChromaDB)
        cursor.execute("""
            SELECT COUNT(*) as with_chroma
            FROM conversations
            WHERE user_id = ? AND chroma_id IS NOT NULL
        """, (user_id,))
        with_chroma = cursor.fetchone()['with_chroma']

        coverage = with_chroma / total

        logger.info(f"📊 Cobertura ChromaDB para {user_id}: {coverage:.1%} ({with_chroma}/{total})")

        return coverage

    def detect_memory_gaps(self, user_id: str, gap_threshold_days: int = 7) -> List[Dict]:
        """
        Identifica períodos sem memórias (gaps)

        Args:
            user_id: ID do usuário
            gap_threshold_days: Mínimo de dias para considerar gap

        Returns:
            Lista de gaps detectados
        """
        cursor = self.db.conn.cursor()

        cursor.execute("""
            SELECT timestamp
            FROM conversations
            WHERE user_id = ?
            ORDER BY timestamp ASC
        """, (user_id,))

        timestamps = [datetime.fromisoformat(row['timestamp']) for row in cursor.fetchall()]

        if len(timestamps) < 2:
            return []

        gaps = []
        for i in range(len(timestamps) - 1):
            time_diff = timestamps[i + 1] - timestamps[i]

            if time_diff.days >= gap_threshold_days:
                gaps.append({
                    'start': timestamps[i].strftime("%Y-%m-%d"),
                    'end': timestamps[i + 1].strftime("%Y-%m-%d"),
                    'duration_days': time_diff.days
                })

        if gaps:
            logger.warning(f"⚠️ {len(gaps)} gaps de memória detectados para {user_id}")
            for gap in gaps:
                logger.warning(f"   Gap: {gap['start']} → {gap['end']} ({gap['duration_days']} dias)")

        return gaps

    def calculate_retrieval_stats(self, user_id: str, last_n_conversations: int = 20) -> Dict:
        """
        Calcula estatísticas de retrieval (quantas memórias recuperadas por busca)

        Args:
            user_id: ID do usuário
            last_n_conversations: Últimas N conversas para análise

        Returns:
            Dict com estatísticas
        """
        # Esta métrica requer tracking de quantas memórias foram recuperadas
        # Por simplicidade, retornar estrutura vazia (implementar tracking posterior)

        return {
            "avg_memories_retrieved": 0,
            "min_memories": 0,
            "max_memories": 0,
        }

    def generate_user_report(self, user_id: str) -> str:
        """
        Gera relatório completo de métricas para um usuário

        Args:
            user_id: ID do usuário

        Returns:
            Relatório formatado
        """
        logger.info(f"📊 Gerando relatório de métricas para {user_id}")

        # Métricas
        coverage = self.calculate_coverage(user_id)
        gaps = self.detect_memory_gaps(user_id)

        # Total de conversas
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total,
                   MIN(timestamp) as first,
                   MAX(timestamp) as last
            FROM conversations
            WHERE user_id = ?
        """, (user_id,))
        stats = dict(cursor.fetchone())

        # Consolidações existentes
        cursor.execute("""
            SELECT COUNT(*) as consolidated
            FROM conversations
            WHERE user_id = ? AND chroma_id LIKE 'consolidated_%'
        """, (user_id,))
        consolidated_count = cursor.fetchone()['consolidated']

        # Montar relatório
        report = f"""
========================================
RELATÓRIO DE MÉTRICAS DE MEMÓRIA
========================================
Usuário: {user_id}

ESTATÍSTICAS GERAIS:
- Total de conversas: {stats['total']}
- Primeira conversa: {stats['first'][:10] if stats['first'] else 'N/A'}
- Última conversa: {stats['last'][:10] if stats['last'] else 'N/A'}

COBERTURA CHROMADB:
- Cobertura: {coverage:.1%}
- Memórias consolidadas: {consolidated_count}

GAPS TEMPORAIS:
- Gaps detectados (≥7 dias): {len(gaps)}
"""

        if gaps:
            report += "\nDETALHES DOS GAPS:\n"
            for i, gap in enumerate(gaps[:5], 1):
                report += f"{i}. {gap['start']} → {gap['end']} ({gap['duration_days']} dias)\n"

        report += "\n========================================\n"

        return report


def generate_system_metrics(db_manager) -> str:
    """
    Gera métricas globais do sistema

    Args:
        db_manager: HybridDatabaseManager instance

    Returns:
        Relatório do sistema
    """
    logger.info("📊 Gerando métricas globais do sistema")

    cursor = db_manager.conn.cursor()

    # Total de usuários
    cursor.execute("SELECT COUNT(DISTINCT user_id) as total FROM conversations")
    total_users = cursor.fetchone()['total']

    # Total de conversas
    cursor.execute("SELECT COUNT(*) as total FROM conversations")
    total_conversations = cursor.fetchone()['total']

    # Conversas no ChromaDB
    cursor.execute("SELECT COUNT(*) as total FROM conversations WHERE chroma_id IS NOT NULL")
    chroma_conversations = cursor.fetchone()['total']

    # Memórias consolidadas
    cursor.execute("SELECT COUNT(*) as total FROM conversations WHERE chroma_id LIKE 'consolidated_%'")
    consolidated = cursor.fetchone()['total']

    # Cobertura média
    avg_coverage = chroma_conversations / total_conversations if total_conversations > 0 else 0

    report = f"""
========================================
MÉTRICAS GLOBAIS DO SISTEMA
========================================
Data: {datetime.now().strftime("%Y-%m-%d %H:%M")}

ESTATÍSTICAS:
- Total de usuários: {total_users}
- Total de conversas: {total_conversations}
- Conversas no ChromaDB: {chroma_conversations}
- Memórias consolidadas: {consolidated}

COBERTURA:
- Cobertura média: {avg_coverage:.1%}

========================================
"""

    return report
```

#### **6.2 Endpoint de Diagnóstico**

**Adicionar em `admin_web/routes.py` ou arquivo equivalente:**

```python
@router.get("/admin/memory-metrics/{user_id}")
async def memory_metrics(user_id: str, admin: Dict = Depends(require_auth)):
    """
    Retorna métricas de memória para um usuário
    """
    from jung_memory_metrics import MemoryQualityMetrics

    metrics = MemoryQualityMetrics(db_manager)
    report = metrics.generate_user_report(user_id)

    return {"report": report}

@router.get("/admin/system-metrics")
async def system_metrics(admin: Dict = Depends(require_master)):
    """
    Retorna métricas globais do sistema (apenas Master)
    """
    from jung_memory_metrics import generate_system_metrics

    report = generate_system_metrics(db_manager)

    return {"report": report}
```

### Checklist de Implementação Fase 6

- [ ] Criar `jung_memory_metrics.py`
- [ ] Implementar `MemoryQualityMetrics` class
- [ ] Implementar `calculate_coverage()`
- [ ] Implementar `detect_memory_gaps()`
- [ ] Implementar `generate_user_report()`
- [ ] Implementar `generate_system_metrics()`
- [ ] Adicionar endpoints de diagnóstico no admin
- [ ] Testar com 3-5 usuários diferentes
- [ ] Criar dashboard visual (opcional, futura iteração)

---

## 📅 Roadmap de Implementação Sugerido

### **Sprint 1 (Semana 1-2): Fase 1 - Metadata Enriquecido**
**Objetivo:** Adicionar campos temporais, emocionais e temáticos ao metadata

**Tarefas:**
1. Modificar `save_conversation()` para adicionar novos campos ao metadata
2. Implementar funções auxiliares (`_calculate_recency_tier`, `_get_dominant_archetype`, etc.)
3. Implementar `calculate_temporal_boost()`
4. Testar com 10 conversas e validar metadata no ChromaDB
5. Documentar novos campos

**Entregável:** Metadata enriquecido funcionando em produção

---

### **Sprint 2 (Semana 3): Fase 2 - Query Enrichment**
**Objetivo:** Enriquecer queries com contexto estruturado

**Tarefas:**
1. Implementar `_build_enriched_query()`
2. Implementar `_extract_names_from_text()`
3. Implementar `_detect_topics_in_text()`
4. Integrar no `semantic_search()`
5. (Opcional) Implementar HyDE para queries curtas
6. Testar com queries diversas

**Entregável:** Query enrichment funcionando, melhorando relevância

---

### **Sprint 3 (Semana 4-5): Fase 3 - Busca Multi-Stage**
**Objetivo:** Two-stage retrieval com reranking inteligente

**Tarefas:**
1. Refatorar `semantic_search()` para two-stage
2. Implementar `_calculate_adaptive_k()`
3. Implementar `_rerank_memories()` com 6 boosts
4. Testar e comparar resultados antes/depois
5. Ajustar pesos dos boosts baseado em testes

**Entregável:** Sistema de busca two-stage + reranking em produção

---

### **Sprint 4 (Semana 6): Fase 5 - Context Building**
**Objetivo:** Contexto hierárquico e estratificado

**Tarefas:**
1. Refatorar `build_rich_context()` para hierárquico
2. Implementar `_search_relevant_facts()`
3. Implementar `_format_facts_hierarchically()`
4. Implementar `_get_relevant_patterns()`
5. Implementar `_compress_context_if_needed()`
6. Testar com usuários que têm muitas memórias

**Entregável:** Contexto otimizado e organizado

---

### **Sprint 5 (Semana 7-8): Fase 4 - Consolidação**
**Objetivo:** Background job de consolidação

**Tarefas:**
1. Criar `jung_memory_consolidation.py`
2. Implementar `MemoryConsolidator` class
3. Implementar clustering e summarization
4. Adicionar job mensal no scheduler
5. Testar consolidação manual
6. Adicionar fact-conversation linking

**Entregável:** Sistema de consolidação rodando mensalmente

---

### **Sprint 6 (Semana 9): Fase 6 - Métricas**
**Objetivo:** Dashboard de monitoramento

**Tarefas:**
1. Criar `jung_memory_metrics.py`
2. Implementar métricas de cobertura, gaps, etc.
3. Adicionar endpoints de diagnóstico no admin
4. Testar com múltiplos usuários
5. (Opcional) Criar dashboard visual

**Entregável:** Sistema de métricas e diagnóstico funcionando

---

## 🎯 Benefícios Esperados

### **1. Consistência de Memória**
- ✅ Agente não perde contexto mesmo após semanas/meses sem interação
- ✅ Memórias relevantes são sempre recuperadas, independente de quando ocorreram
- ✅ Consolidação reduz redundância e cria "memória episódica"

### **2. Relevância Aumentada**
- ✅ Retrieval captura não apenas similaridade vetorial, mas:
  - Contexto temporal (recente vs histórico)
  - Intensidade emocional
  - Menções a pessoas específicas
  - Tópicos relevantes
- ✅ k adaptativo evita sobrecarga ou falta de contexto

### **3. Escalabilidade**
- ✅ Sistema funciona eficientemente com 10 ou 10.000 conversas
- ✅ Consolidação previne crescimento exponencial de memórias redundantes

### **4. Experiência do Usuário**
- ✅ Sensação de "Jung realmente me conhece e lembra de tudo"
- ✅ Respostas mais contextualizadas e personalizadas
- ✅ Continuidade em conversas mesmo após longos períodos

### **5. Observabilidade**
- ✅ Métricas permitem identificar problemas de memória
- ✅ Gaps temporais são detectados e podem ser investigados
- ✅ Cobertura de ChromaDB é monitorada

---

## 📚 Referências Técnicas

### Arquivos Principais a Modificar

1. **jung_core.py**
   - Linhas 1100-1264: `save_conversation()` - Adicionar metadata enriquecido
   - Linhas 1369-1472: `semantic_search()` - Two-stage retrieval
   - Linhas 1505-1618: `build_rich_context()` - Contexto hierárquico

2. **Novos Arquivos a Criar**
   - `jung_memory_consolidation.py` - Sistema de consolidação
   - `jung_memory_metrics.py` - Métricas de qualidade

3. **Arquivos de Configuração**
   - `telegram_bot.py` ou `jobs.py` - Scheduler de consolidação

### Dependências

**Existentes:**
- ChromaDB + LangChain
- OpenAI Embeddings (`text-embedding-3-small`)
- SQLite
- Anthropic Claude API

**Novas (instalar se necessário):**
- `apscheduler` - Para background jobs de consolidação

### Comandos de Instalação

```bash
pip install apscheduler
```

---

## ⚠️ Considerações de Implementação

### **1. Backward Compatibility**
- Metadata antigo (sem novos campos) deve continuar funcionando
- Adicionar verificações de existência antes de acessar novos campos

### **2. Performance**
- Two-stage retrieval aumenta carga: monitorar tempos de resposta
- Consolidação deve rodar em horários de baixo uso (03:00)
- Compression de contexto só quando necessário

### **3. Testes**
- Testar com usuários reais (variados: novos, antigos, ativos, inativos)
- Comparar qualidade de respostas antes/depois de cada fase
- Validar que não há vazamento de memórias entre usuários

### **4. Rollback Plan**
- Manter código antigo comentado durante transição
- Criar flag de feature toggle para desabilitar novos recursos se necessário
- Backup do banco ChromaDB antes de grandes mudanças

---

## ✅ Critérios de Sucesso

### **Fase 1 (Metadata)**
- [ ] Metadata enriquecido salvo em 100% das novas conversas
- [ ] Campos temporais corretamente populados
- [ ] Nenhum erro ao buscar memórias antigas (sem novos campos)

### **Fase 2 (Query Enrichment)**
- [ ] Queries enriquecidas incluem nomes e tópicos detectados
- [ ] Relevância de resultados melhora (validação manual com 10 queries)

### **Fase 3 (Two-Stage)**
- [ ] Reranking altera ordem de resultados em ≥50% das buscas
- [ ] k adaptativo varia entre 3 e 12 conforme esperado
- [ ] Boosts aplicados corretamente (logs confirmam)

### **Fase 4 (Consolidação)**
- [ ] Job mensal roda sem erros
- [ ] Memórias consolidadas são criadas para clusters ≥5 conversas
- [ ] Resumos com LLM são coerentes e informativos

### **Fase 5 (Context Building)**
- [ ] Contexto hierárquico é legível e organizado
- [ ] Memórias consolidadas aparecem quando relevantes
- [ ] Compression só ativa quando contexto > 2000 tokens

### **Fase 6 (Métricas)**
- [ ] Relatórios de usuário gerados sem erros
- [ ] Gaps temporais corretamente detectados
- [ ] Cobertura ChromaDB > 95% para usuários ativos

---

## 📝 Notas Finais

Este plano foi desenhado para ser implementado de forma **incremental e modular**, permitindo testar e ajustar cada fase antes de prosseguir.

**Prioridades:**
1. **Essencial:** Fases 1, 2, 3 (Metadata + Query + Two-Stage)
2. **Importante:** Fase 5 (Context Building)
3. **Desejável:** Fases 4, 6 (Consolidação + Métricas)

**Estimativa de Esforço Total:** 8-10 semanas de desenvolvimento

**Data de Criação:** 2026-01-02
**Última Atualização:** 2026-01-02
**Versão:** 1.0
