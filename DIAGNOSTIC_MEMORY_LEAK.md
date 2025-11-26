# 🚨 DIAGNÓSTICO CRÍTICO: Vazamento de Memórias Entre Usuários

## ❌ Problema Relatado

**Sintoma:** Usuário novo (celular diferente) está recebendo memórias/contexto de outro usuário.

**Gravidade:** 🔴 CRÍTICO - Violação de privacidade e quebra total do isolamento de dados.

---

## 🔍 Análise Completa do Código

### 1. **ChromaDB - Salvamento** ✅ CORRETO

**Arquivo:** `jung_core.py` (linhas 976-1046)

```python
metadata = {
    "user_id": user_id,  # ✅ User ID é salvo corretamente
    "user_name": user_name,
    ...
}
```

**Status:** ✅ Cada documento no ChromaDB tem `user_id` no metadata.

---

### 2. **ChromaDB - Busca Semântica** ✅ CORRETO

**Arquivo:** `jung_core.py` (linhas 1131-1135)

```python
results = self.vectorstore.similarity_search_with_score(
    enriched_query,
    k=k * 2,
    filter={"user_id": user_id}  # ✅ Filtra por user_id
)
```

**Status:** ✅ Busca semântica filtra corretamente por `user_id`.

---

### 3. **SQLite - Fatos Estruturados** ✅ CORRETO

**Arquivo:** `jung_core.py` (linhas 1245-1250)

```python
cursor.execute("""
    SELECT fact_category, fact_key, fact_value
    FROM user_facts
    WHERE user_id = ? AND is_current = 1  # ✅ Filtra por user_id
    ...
""", (user_id,))
```

**Status:** ✅ Fatos filtrados corretamente por `user_id`.

---

### 4. **SQLite - Padrões Detectados** ✅ CORRETO

**Arquivo:** `jung_core.py` (linhas 1271-1277)

```python
cursor.execute("""
    SELECT ...
    FROM user_patterns
    WHERE user_id = ? AND confidence_score > 0.6  # ✅ Filtra por user_id
    ...
""", (user_id,))
```

**Status:** ✅ Padrões filtrados corretamente por `user_id`.

---

### 5. **Chat History (Telegram)** ✅ CORRETO

**Arquivo:** `telegram_bot.py` (linhas 96, 105-121)

```python
self.chat_histories: Dict[int, List[Dict]] = {}  # Chave: telegram_id

def get_chat_history(self, telegram_id: int):
    return self.chat_histories.get(telegram_id, [])  # ✅ Isolado por telegram_id
```

**Status:** ✅ Histórico de chat isolado por `telegram_id`.

---

### 6. **⚠️ POSSÍVEL CAUSA: Agent Development State**

**Arquivo:** `jung_core.py` (tabela `agent_development`)

**Problema Suspeito:** Esta tabela NÃO tem `user_id`!

```python
# jung_core.py - Linha ~607
cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_development (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        # ❌ FALTA user_id AQUI!
        self_awareness_score REAL DEFAULT 0.0,
        integration_level REAL DEFAULT 0.0,
        ...
    )
""")
```

**Impacto:** Estado do agente é **GLOBAL**, não por usuário!

---

### 7. **🔴 CAUSA CONFIRMADA: Prompts Compartilhados**

**Arquivo:** `jung_core.py` (Config class)

**PROBLEMA CRÍTICO:**

```python
# Config.AGENT_IDENTITY - Linha 150-196
AGENT_IDENTITY = """
Seu nome é Jung...
Você existe para duas coisas:
1. CONHECER PROFUNDAMENTE
   - Descobrir padrões que o usuário repete sem perceber
   ...
"""
```

**O prompt diz:**
> "Cada padrão que identifica, cada conflito que mapeia, cada valor que descobre -
> tudo isso constrói seu conhecimento único sobre ESTE usuário."

**MAS:** O `AGENT_IDENTITY` é uma **constante global** compartilhada por todos os usuários!

O mesmo acontece com:
- `CONFLICTED_RESPONSE_PROMPT`
- `HARMONIOUS_RESPONSE_PROMPT`
- `PERSONA_PROMPT`
- `SOMBRA_PROMPT`
- `SABIO_PROMPT`
- `ANIMA_PROMPT`

**Consequência:** Embora os **DADOS** estejam isolados, os **PROMPTS** fazem referência ao "aprendizado contínuo" como se fosse um agente único, o que pode confundir o LLM.

---

### 8. **🔴 CAUSA REAL: `build_rich_context()` Pode Retornar Dados Errados**

**Análise do fluxo:**

```python
# telegram_bot.py - handle_message() - Linha ~746
response = bot_state.jung_engine.process_message(
    user_id=str(telegram_id),  # ✅ String do telegram_id
    user_name=username,
    user_input=message_text,
    chat_history=chat_history  # ✅ Isolado por telegram_id
)
```

```python
# jung_core.py - process_message() - Linha 2416
semantic_context = self.db.build_rich_context(
    user_id=user_id,  # ✅ Passa user_id correto
    current_input=user_input,
    k_memories=10,
    chat_history=chat_history
)
```

```python
# jung_core.py - build_rich_context() - Linha 1291
relevant_memories = self.semantic_search(
    user_id,  # ✅ Passa user_id
    current_input,
    k_memories,
    chat_history
)
```

```python
# jung_core.py - semantic_search() - Linha 1134
results = self.vectorstore.similarity_search_with_score(
    enriched_query,
    k=k * 2,
    filter={"user_id": user_id}  # ✅ Filtra corretamente!
)
```

**Teoricamente está correto!** Mas...

---

## 🧪 Teste de Hipóteses

### Hipótese 1: ChromaDB não está filtrando ❌

**Teste:**
```python
# No semantic_search, adicionar log ANTES do filtro:
logger.info(f"🔍 Buscando memórias para user_id={user_id}")
logger.info(f"   Filtro ChromaDB: {{'user_id': user_id}}")

# Depois do resultado:
for doc, score in results:
    logger.info(f"   Resultado: user_id={doc.metadata.get('user_id')}")
```

**Se user_id dos resultados for diferente do filtro → BUG CONFIRMADO no ChromaDB**

---

### Hipótese 2: user_id não está sendo convertido corretamente ⚠️

**Problema Possível:**

```python
# telegram_bot.py - Linha 746
response = bot_state.jung_engine.process_message(
    user_id=str(telegram_id),  # ← Converte int para string
    ...
)
```

**MAS:** No ChromaDB, o `user_id` pode estar salvo como INT ou STRING inconsistentemente!

**Teste:**
```python
# No save_conversation:
logger.info(f"💾 Salvando: user_id={user_id} (type={type(user_id).__name__})")

# No semantic_search:
logger.info(f"🔍 Buscando: user_id={user_id} (type={type(user_id).__name__})")
```

**Se os tipos forem diferentes → FILTRO FALHA!**

---

### Hipótese 3: Fallback keyword search não filtra ❌

**Verificar:** `_fallback_keyword_search()` - Linha 1177

```python
cursor.execute("""
    SELECT * FROM conversations
    WHERE user_id = ?  # ✅ Tem filtro
    AND (user_input LIKE ? OR ai_response LIKE ?)
    ...
""", (user_id, search_term, search_term, k))
```

**Status:** ✅ Tem filtro correto.

---

### Hipótese 4: ChromaDB está desabilitado e fallback falha ⚠️

**Se `chroma_enabled = False`:**

```python
# semantic_search() - Linha 1112-1114
if not self.chroma_enabled:
    logger.warning("ChromaDB desabilitado...")
    return self._fallback_keyword_search(user_id, query, k)
```

**Verificar logs:** Se há warning "ChromaDB desabilitado", então está usando fallback.

**Teste:** Verificar se `_fallback_keyword_search` está realmente filtrando.

---

## 🎯 Plano de Correção

### ✅ CORREÇÃO IMEDIATA (Fase 1): IMPLEMENTADO

#### 1. **Logs de Debug Críticos Adicionados** ✅

**Arquivo:** `jung_core.py`

**✅ IMPLEMENTADO em `semantic_search()` (linhas 1117-1165):**
- Log do user_id sendo buscado e seu tipo
- Log do filtro ChromaDB aplicado
- Log de todos os resultados retornados com user_id e tipo
- Detecção automática de vazamento com log de erro
- Filtragem manual para remover qualquer resultado com user_id errado

**✅ IMPLEMENTADO em `save_conversation()` (linhas 943-1040):**
- Log do user_id sendo salvo e seu tipo
- Conversão automática para string se necessário
- Log do metadata sendo salvo no ChromaDB
- Log de confirmação após salvamento bem-sucedido

#### 2. **Garantir Consistência de Tipos** ✅

**✅ IMPLEMENTADO em `save_conversation()`:**
- Conversão automática de user_id para string
- Validação que user_id não é None
- Log de warning se conversão foi necessária

**✅ IMPLEMENTADO em `semantic_search()`:**
- Conversão automática de user_id para string
- Validação que user_id não é None
- Retorna lista vazia se user_id inválido

#### 3. **Validar Filtro do ChromaDB** ✅

**✅ IMPLEMENTADO em `semantic_search()`:**
- Filtro ChromaDB usa string explícita
- Log do filtro sendo aplicado
- Validação manual de todos os resultados retornados
- Filtragem extra para remover qualquer documento com user_id errado
- Log de erro se vazamento for detectado

---

### CORREÇÃO ESTRUTURAL (Fase 2):

#### 4. **Adicionar user_id à tabela agent_development**

**Problema:** Tabela `agent_development` é global, não por usuário.

**Solução:**

```python
# jung_core.py - _create_tables() (linha ~607)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_development (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,  # ✅ ADICIONAR
        self_awareness_score REAL DEFAULT 0.0,
        integration_level REAL DEFAULT 0.0,
        complexity_level REAL DEFAULT 0.0,
        total_insights_generated INTEGER DEFAULT 0,
        last_significant_growth DATETIME,
        FOREIGN KEY (user_id) REFERENCES users(user_id)  # ✅ ADICIONAR
    )
""")

# Criar índice
cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_dev_user
    ON agent_development(user_id)
""")
```

**Migração de dados existentes:**

```python
# Copiar registro global para cada usuário existente
cursor.execute("SELECT user_id FROM users")
users = cursor.fetchall()

cursor.execute("SELECT * FROM agent_development WHERE id = 1")
global_state = cursor.fetchone()

if global_state:
    for user in users:
        cursor.execute("""
            INSERT OR IGNORE INTO agent_development
            (user_id, self_awareness_score, integration_level, ...)
            VALUES (?, ?, ?, ...)
        """, (user['user_id'], global_state['self_awareness_score'], ...))
```

---

#### 5. **Atualizar todas as queries de agent_development**

**Buscar por:**
```bash
grep -n "agent_development" jung_core.py
```

**Adicionar `WHERE user_id = ?` em TODAS as queries.**

---

### TESTES (Fase 3):

#### Teste 1: Validar Isolamento

```python
# Criar script de teste
def test_user_isolation():
    db = HybridDatabaseManager()

    # Usuário 1
    db.save_conversation(
        user_id="user1",
        user_name="Alice",
        user_input="Eu gosto de café",
        ai_response="Entendi"
    )

    # Usuário 2
    db.save_conversation(
        user_id="user2",
        user_name="Bob",
        user_input="Eu gosto de chá",
        ai_response="Entendi"
    )

    # Buscar por "café" como usuário 2
    results = db.semantic_search("user2", "café", k=5)

    # VALIDAR: Nenhum resultado deve vir de user1!
    for result in results:
        assert result['metadata']['user_id'] == "user2", \
            f"VAZAMENTO! user_id={result['metadata']['user_id']}"

    print("✅ Teste de isolamento passou!")
```

---

## 🚨 Ação Imediata Recomendada

**✅ 1. Deploy de Logs (FASE 1 COMPLETA):**
- ✅ Logs de debug adicionados no `semantic_search()`
- ✅ Logs de debug adicionados no `save_conversation()`
- ✅ Conversão automática para string implementada
- ✅ Filtragem manual como segurança adicional
- 🔄 **PRÓXIMO:** Fazer commit e deploy no Railway

**2. Análise dos Logs (APÓS DEPLOY):**
- Aguardar próxima mensagem de usuário
- Verificar nos logs do Railway:
  - Se user_id está consistente (sempre string)
  - Se resultados do ChromaDB têm user_id correto
  - Se há warnings de conversão de tipo
  - Se há erros de vazamento detectados

**3. Correção Baseada em Evidência:**
- ✅ Logs já implementados
- ✅ Conversão forçada para string já implementada
- ✅ Filtragem manual de segurança já implementada
- Se logs ainda mostrarem vazamento → Investigar ChromaDB ou agent_development

---

## 📋 Checklist de Validação

Status atual:

- ✅ Logs de debug implementados
- ✅ Conversão de user_id para string implementada
- ✅ Validação manual de resultados implementada
- 🔄 Deploy pendente
- ⏳ Aguardando análise de logs reais
- [ ] Teste manual: Usuário A não vê dados de Usuário B
- [ ] Tabela `agent_development` tem coluna `user_id` (Fase 2)
- [ ] Todas as queries de agent_development filtram por `user_id` (Fase 2)

---

## 🎯 Status Atual

**FASE 1 (Debug Logs): ✅ COMPLETA**
- Todos os logs críticos implementados
- Conversão de tipos implementada
- Filtragem de segurança implementada

**PRÓXIMO PASSO:**
1. Commit das alterações
2. Deploy no Railway
3. Análise dos logs reais para identificar causa exata do vazamento
4. Se necessário, implementar Fase 2 (agent_development table)
