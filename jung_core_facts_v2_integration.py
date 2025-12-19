"""
jung_core_facts_v2_integration.py - Integração do Sistema de Fatos V2
======================================================================

Código para integrar no jung_core.py para substituir o sistema antigo
de extração de fatos por regex pelo novo sistema com LLM.

INSTRUÇÕES DE INTEGRAÇÃO:
1. Importar LLMFactExtractor no início do jung_core.py
2. Substituir método extract_and_save_facts()
3. Substituir método _save_or_update_fact()
4. Atualizar build_rich_context() para usar user_facts_v2

Autor: Sistema Jung
Data: 2025-12-19
"""

# ===================================================================
# ADICIONAR NO INÍCIO DO jung_core.py (depois dos imports existentes)
# ===================================================================

"""
from llm_fact_extractor import LLMFactExtractor, ExtractedFact
"""


# ===================================================================
# ADICIONAR NO __init__ da classe HybridDatabaseManager
# ===================================================================

"""
# Inicializar extrator de fatos com LLM
try:
    self.fact_extractor = LLMFactExtractor(
        llm_client=self.xai_client,  # Usar Grok por padrão (mais barato)
        model="grok-beta"
    )
    logger.info("✅ LLM Fact Extractor inicializado")
except Exception as e:
    logger.warning(f"⚠️ Erro ao inicializar LLM Fact Extractor: {e}")
    logger.warning("   Usando extração regex como fallback")
    self.fact_extractor = None
"""


# ===================================================================
# SUBSTITUIR MÉTODO extract_and_save_facts
# ===================================================================

def extract_and_save_facts_v2(self, user_id: str, user_input: str,
                              conversation_id: int) -> List[Dict]:
    """
    Extrai fatos estruturados usando LLM + fallback regex

    VERSÃO 2: Usa LLMFactExtractor + tabela user_facts_v2
    """

    extracted_facts = []

    # Tentar extração com LLM
    if hasattr(self, 'fact_extractor') and self.fact_extractor:
        try:
            logger.info("🤖 Extraindo fatos com LLM...")
            facts = self.fact_extractor.extract_facts(user_input, user_id)

            # Salvar cada fato extraído
            for fact in facts:
                self._save_fact_v2(
                    user_id=user_id,
                    category=fact.category,
                    fact_type=fact.fact_type,
                    attribute=fact.attribute,
                    value=fact.value,
                    confidence=fact.confidence,
                    extraction_method='llm',
                    context=fact.context,
                    conversation_id=conversation_id
                )

                extracted_facts.append({
                    'category': fact.category,
                    'type': fact.fact_type,
                    'attribute': fact.attribute,
                    'value': fact.value,
                    'confidence': fact.confidence
                })

            if extracted_facts:
                logger.info(f"✅ Extraídos {len(extracted_facts)} fatos com LLM")

        except Exception as e:
            logger.error(f"❌ Erro na extração com LLM: {e}")
            # Continuar para fallback

    # Se LLM não extraiu nada ou falhou, usar regex fallback
    if not extracted_facts:
        logger.info("🔄 Usando extração regex como fallback...")
        # Chamar método regex antigo (se quiser manter como backup)
        # extracted_facts = self._extract_facts_regex_fallback(user_id, user_input, conversation_id)

    return extracted_facts


# ===================================================================
# NOVO MÉTODO: _save_fact_v2
# ===================================================================

def _save_fact_v2(self, user_id: str, category: str, fact_type: str,
                 attribute: str, value: str, confidence: float = 1.0,
                 extraction_method: str = 'llm', context: str = None,
                 conversation_id: int = None):
    """
    Salva ou atualiza fato na tabela user_facts_v2

    FEATURES:
    - Suporta múltiplas pessoas da mesma categoria
    - Versionamento adequado
    - Metadados de confiança e método
    """

    logger.info(f"📝 [FACTS V2] Salvando: {category}.{fact_type}.{attribute} = {value}")

    with self._lock:
        cursor = self.conn.cursor()

        # Verificar se fato já existe
        cursor.execute("""
            SELECT id, fact_value, version
            FROM user_facts_v2
            WHERE user_id = ?
              AND fact_category = ?
              AND fact_type = ?
              AND fact_attribute = ?
              AND is_current = 1
        """, (user_id, category, fact_type, attribute))

        existing = cursor.fetchone()

        if existing:
            existing_id = existing[0]
            existing_value = existing[1]
            existing_version = existing[2]

            # Se valor mudou, criar nova versão
            if existing_value != value:
                logger.info(f"   ✏️  Atualizando: '{existing_value}' → '{value}'")

                # Marcar versão antiga como não-atual
                cursor.execute("""
                    UPDATE user_facts_v2
                    SET is_current = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (existing_id,))

                # Criar nova versão
                cursor.execute("""
                    INSERT INTO user_facts_v2
                    (user_id, fact_category, fact_type, fact_attribute, fact_value,
                     confidence, extraction_method, context, source_conversation_id,
                     version, is_current)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    user_id, category, fact_type, attribute, value,
                    confidence, extraction_method, context, conversation_id,
                    existing_version + 1
                ))

                new_id = cursor.lastrowid

                # Marcar que a versão antiga foi substituída
                cursor.execute("""
                    UPDATE user_facts_v2
                    SET replaced_by = ?
                    WHERE id = ?
                """, (new_id, existing_id))

                logger.info(f"   ✅ Nova versão criada (v{existing_version + 1})")
            else:
                logger.info(f"   ℹ️  Fato já existe com mesmo valor")
        else:
            # Criar fato novo
            logger.info(f"   ✨ Criando novo fato")
            cursor.execute("""
                INSERT INTO user_facts_v2
                (user_id, fact_category, fact_type, fact_attribute, fact_value,
                 confidence, extraction_method, context, source_conversation_id,
                 version, is_current)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
            """, (
                user_id, category, fact_type, attribute, value,
                confidence, extraction_method, context, conversation_id
            ))

            logger.info(f"   ✅ Fato salvo com sucesso")

        self.conn.commit()


# ===================================================================
# ATUALIZAR build_rich_context PARA USAR user_facts_v2
# ===================================================================

def build_rich_context_v2(self, user_id: str, current_input: str,
                         k_memories: int = 5,
                         chat_history: List[Dict] = None) -> str:
    """
    VERSÃO V2: Usa user_facts_v2 para contexto mais rico

    Mudanças:
    - Busca em user_facts_v2
    - Agrupa fatos por tipo (ex: todos os filhos juntos)
    - Mostra atributos complementares (nome + idade + profissão)
    """

    logger.info(f"🏁 [DEBUG] ========== INÍCIO build_rich_context_v2 ==========")
    logger.info(f"🏁 [DEBUG] user_id='{user_id}'")

    user = self.get_user(user_id)
    name = user['user_name'] if user else "Usuário"

    context_parts = []

    # ===== 1. CABEÇALHO =====
    context_parts.append(f"=== CONTEXTO SOBRE {name.upper()} ===\n")

    # ===== 2. HISTÓRICO DA CONVERSA ATUAL =====
    if chat_history and len(chat_history) > 0:
        context_parts.append("💬 HISTÓRICO DA CONVERSA ATUAL:")

        recent = chat_history[-6:] if len(chat_history) > 6 else chat_history

        for msg in recent:
            role = "👤 Usuário" if msg["role"] == "user" else "🤖 Assistente"
            content = msg["content"][:150] + "..." if len(msg["content"]) > 150 else msg["content"]
            context_parts.append(f"{role}: {content}")

        context_parts.append("")

    # ===== 3. FATOS ESTRUTURADOS V2 =====
    cursor = self.conn.cursor()

    logger.info(f"📚 [DEBUG] Recuperando fatos v2 para user_id='{user_id}'")

    # Verificar se tabela existe
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='user_facts_v2'
    """)

    if cursor.fetchone():
        # Usar tabela V2
        cursor.execute("""
            SELECT fact_category, fact_type, fact_attribute, fact_value, confidence
            FROM user_facts_v2
            WHERE user_id = ? AND is_current = 1
            ORDER BY fact_category, fact_type, fact_attribute
        """, (user_id,))

        facts = cursor.fetchall()

        logger.info(f"   Fatos encontrados: {len(facts)}")

        if facts:
            context_parts.append("📋 FATOS CONHECIDOS:")

            # Agrupar por categoria e tipo
            facts_hierarchy = {}
            for fact in facts:
                category = fact[0]
                fact_type = fact[1]
                attribute = fact[2]
                value = fact[3]
                conf = fact[4]

                if category not in facts_hierarchy:
                    facts_hierarchy[category] = {}

                if fact_type not in facts_hierarchy[category]:
                    facts_hierarchy[category][fact_type] = []

                facts_hierarchy[category][fact_type].append({
                    'attribute': attribute,
                    'value': value,
                    'confidence': conf
                })

            # Formatar para exibição
            for category, types in facts_hierarchy.items():
                context_parts.append(f"\n{category}:")

                for fact_type, attributes in types.items():
                    # Consolidar atributos do mesmo tipo
                    attr_text = ", ".join([
                        f"{a['attribute']}: {a['value']}"
                        for a in attributes
                    ])
                    context_parts.append(f"  - {fact_type}: {attr_text}")

            context_parts.append("")
    else:
        # Fallback para tabela antiga
        logger.warning("   ⚠️ user_facts_v2 não existe, usando user_facts antiga")
        cursor.execute("""
            SELECT fact_category, fact_key, fact_value
            FROM user_facts
            WHERE user_id = ? AND is_current = 1
            ORDER BY fact_category, fact_key
        """, (user_id,))

        facts = cursor.fetchall()

        if facts:
            context_parts.append("📋 FATOS CONHECIDOS:")

            facts_by_category = {}
            for fact in facts:
                category = fact[0]
                if category not in facts_by_category:
                    facts_by_category[category] = []
                facts_by_category[category].append(f"{fact[1]}: {fact[2]}")

            for category, items in facts_by_category.items():
                context_parts.append(f"\n{category}:")
                context_parts.append("\n".join(f"  - {item}" for item in items))

            context_parts.append("")

    # ===== 4. PADRÕES DETECTADOS =====
    cursor.execute("""
        SELECT pattern_name, pattern_description, confidence_score
        FROM user_patterns
        WHERE user_id = ? AND confidence_score > 0.6
        ORDER BY confidence_score DESC
        LIMIT 5
    """, (user_id,))

    patterns = cursor.fetchall()

    if patterns:
        context_parts.append("🔍 PADRÕES COMPORTAMENTAIS:")
        for pattern in patterns:
            context_parts.append(
                f"  - {pattern[0]} ({pattern[2]:.0%}): {pattern[1]}"
            )
        context_parts.append("")

    # ===== 5. MEMÓRIAS SEMÂNTICAS =====
    relevant_memories = self.semantic_search(user_id, current_input, k_memories, chat_history)

    if relevant_memories:
        context_parts.append("🧠 MEMÓRIAS SEMÂNTICAS RELEVANTES:")

        for i, memory in enumerate(relevant_memories, 1):
            timestamp = memory['timestamp'][:10] if memory['timestamp'] else 'N/A'
            score = memory['similarity_score']
            context_parts.append(
                f"\n{i}. [{timestamp}] Similaridade: {score:.2f}"
            )
            context_parts.append(f"   Usuário: {memory['user_input'][:150]}...")

        context_parts.append("")

    # ===== 6. INSTRUÇÕES =====
    context_parts.append("🎯 COMO USAR ESTE CONTEXTO:")
    context_parts.append("  1. FATOS são informações confirmadas sobre o usuário")
    context_parts.append("  2. Use nomes próprios quando disponíveis")
    context_parts.append("  3. PADRÕES mostram comportamentos recorrentes")
    context_parts.append("  4. MEMÓRIAS fornecem contexto histórico")

    logger.info(f"🏁 [DEBUG] ========== FIM build_rich_context_v2 ==========")

    return "\n".join(context_parts)


# ===================================================================
# EXEMPLO DE USO
# ===================================================================

"""
# No método save_conversation, substituir a linha:

self.extract_and_save_facts(user_id, user_input, conversation_id)

# Por:

self.extract_and_save_facts_v2(user_id, user_input, conversation_id)

# E no método process_message, substituir:

semantic_context = self.db.build_rich_context(...)

# Por:

semantic_context = self.db.build_rich_context_v2(...)
"""
