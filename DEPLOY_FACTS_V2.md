# 🚀 Deploy do Sistema de Fatos V2 no Railway

**Data:** 2025-12-19
**Versão:** 2.0 - Sistema de Memória com LLM

---

## 📋 Checklist de Deploy

### Pré-requisitos
- [ ] Código commitado no Git
- [ ] XAI_API_KEY configurada (para Grok)
- [ ] Backup do banco de dados atual

### Fase 1: Upload dos Novos Arquivos
- [ ] `llm_fact_extractor.py`
- [ ] `migrate_facts_v2.py`
- [ ] `jung_core_facts_v2_integration.py` (referência)

### Fase 2: Executar Migração
- [ ] Rodar script de migração no Railway
- [ ] Verificar criação de `user_facts_v2`
- [ ] Confirmar migração de dados antigos

### Fase 3: Atualizar jung_core.py
- [ ] Integrar código do arquivo de integração
- [ ] Testar localmente (opcional)
- [ ] Deploy no Railway

### Fase 4: Validação
- [ ] Testar extração com mensagens novas
- [ ] Verificar contexto gerado
- [ ] Confirmar nomes próprios salvos

---

## 🔧 Passo a Passo Detalhado

### 1. Commit e Push

```bash
git add llm_fact_extractor.py migrate_facts_v2.py jung_core_facts_v2_integration.py DEPLOY_FACTS_V2.md
git commit -m "feat: Sistema de Fatos V2 com extração LLM

- Extrator inteligente com Grok/Claude
- Novo schema user_facts_v2 (suporta múltiplas pessoas)
- Captura nomes próprios automaticamente
- Migração de dados da versão antiga
- Fallback para regex em caso de falha

BREAKING CHANGE: Nova estrutura de tabela user_facts_v2"

git push
```

### 2. Executar Migração no Railway

**Opção A: Via Railway CLI**
```bash
railway run python migrate_facts_v2.py
```

**Opção B: Criar endpoint temporário**
Adicionar em `main.py`:

```python
@app.post("/admin/migrate/facts-v2")
async def migrate_facts_v2_endpoint():
    """
    ENDPOINT TEMPORÁRIO: Migrar para user_facts_v2

    Acesse: POST https://seu-railway-url/admin/migrate/facts-v2
    """
    try:
        from migrate_facts_v2 import migrate_to_v2

        success = migrate_to_v2()

        if success:
            return {
                "status": "success",
                "message": "Migração para user_facts_v2 concluída",
                "next_steps": [
                    "Verificar logs do Railway",
                    "Testar com mensagem nova",
                    "Remover este endpoint"
                ]
            }
        else:
            return {
                "status": "error",
                "message": "Migração falhou, ver logs"
            }

    except Exception as e:
        logger.error(f"Erro na migração: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
```

### 3. Integrar no jung_core.py

#### 3.1 Adicionar Import
**Localização:** Linha ~34 (após `from openai import OpenAI`)

```python
# Extrator de fatos com LLM
try:
    from llm_fact_extractor import LLMFactExtractor
    LLM_FACT_EXTRACTOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ LLMFactExtractor não disponível: {e}")
    LLM_FACT_EXTRACTOR_AVAILABLE = False
```

#### 3.2 Inicializar no __init__
**Localização:** Classe `HybridDatabaseManager.__init__()` (linha ~750)

Adicionar após inicialização do ChromaDB:

```python
# Inicializar extrator de fatos com LLM
if LLM_FACT_EXTRACTOR_AVAILABLE:
    try:
        self.fact_extractor = LLMFactExtractor(
            llm_client=self.xai_client,  # Usar Grok (mais barato)
            model="grok-beta"
        )
        logger.info("✅ LLM Fact Extractor inicializado (Grok)")
    except Exception as e:
        logger.warning(f"⚠️ Erro ao inicializar LLM Fact Extractor: {e}")
        self.fact_extractor = None
else:
    self.fact_extractor = None
```

#### 3.3 Substituir extract_and_save_facts
**Localização:** Linha ~1572

**ANTES:**
```python
def extract_and_save_facts(self, user_id: str, user_input: str,
                          conversation_id: int) -> List[Dict]:
    """
    Extrai fatos estruturados do input do usuário
    ...
    """
```

**DEPOIS:**
Copiar código completo de `jung_core_facts_v2_integration.py`:
- Método `extract_and_save_facts_v2()`
- Método `_save_fact_v2()`

#### 3.4 Atualizar Chamadas

**Localização:** Linha ~1171 (dentro de `save_conversation`)

**ANTES:**
```python
self.extract_and_save_facts(user_id, user_input, conversation_id)
```

**DEPOIS:**
```python
# Usar extração V2 se disponível
if hasattr(self, 'extract_and_save_facts_v2'):
    self.extract_and_save_facts_v2(user_id, user_input, conversation_id)
else:
    # Fallback para versão antiga
    self.extract_and_save_facts(user_id, user_input, conversation_id)
```

#### 3.5 Atualizar build_rich_context (Opcional mas Recomendado)

**Localização:** Linha ~1431

Adicionar verificação no início do método:

```python
def build_rich_context(self, user_id: str, current_input: str,
                      k_memories: int = 5,
                      chat_history: List[Dict] = None) -> str:
    """..."""

    # Verificar se deve usar V2
    cursor = self.conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='user_facts_v2'
    """)

    use_v2 = cursor.fetchone() is not None

    # ... resto do código
```

Depois substituir a query de fatos (linha ~1477):

**ANTES:**
```python
cursor.execute("""
    SELECT fact_category, fact_key, fact_value
    FROM user_facts
    WHERE user_id = ? AND is_current = 1
    ORDER BY fact_category, fact_key
""", (user_id,))
```

**DEPOIS:**
```python
if use_v2:
    cursor.execute("""
        SELECT fact_category, fact_type, fact_attribute, fact_value
        FROM user_facts_v2
        WHERE user_id = ? AND is_current = 1
        ORDER BY fact_category, fact_type, fact_attribute
    """, (user_id,))

    facts = cursor.fetchall()

    if facts:
        context_parts.append("📋 FATOS CONHECIDOS:")

        # Agrupar por categoria e tipo
        facts_hierarchy = {}
        for fact in facts:
            category = fact[0]
            fact_type = fact[1]
            attribute = fact[2]
            value = fact[3]

            if category not in facts_hierarchy:
                facts_hierarchy[category] = {}

            if fact_type not in facts_hierarchy[category]:
                facts_hierarchy[category][fact_type] = []

            facts_hierarchy[category][fact_type].append(f"{attribute}: {value}")

        # Exibir
        for category, types in facts_hierarchy.items():
            context_parts.append(f"\n{category}:")
            for fact_type, attrs in types.items():
                attrs_text = ", ".join(attrs)
                context_parts.append(f"  - {fact_type}: {attrs_text}")

        context_parts.append("")
else:
    # Código antigo mantido
    cursor.execute("""
        SELECT fact_category, fact_key, fact_value
        FROM user_facts
        WHERE user_id = ? AND is_current = 1
        ORDER BY fact_category, fact_key
    """, (user_id,))

    # ... resto do código antigo
```

---

## 🧪 Testes

### Teste 1: Verificar Migração

**Via Railway CLI:**
```bash
railway run python -c "
from jung_core import DatabaseManager
db = DatabaseManager()
cursor = db.conn.cursor()
cursor.execute('SELECT COUNT(*) FROM user_facts_v2 WHERE is_current = 1')
print(f'Fatos migrados: {cursor.fetchone()[0]}')
"
```

**Via Telegram:**
Enviar mensagem: `/admin facts-count`

### Teste 2: Extração de Nomes

**Telegram - Envie:**
```
Minha esposa se chama Ana Maria
```

**Verificar logs Railway:**
```
🤖 [LLM EXTRACTOR] Extraindo fatos de: Minha esposa se chama Ana Maria
✅ LLM extraiu 1 fatos
📝 [FACTS V2] Salvando: RELACIONAMENTO.esposa.nome = Ana Maria
✅ Fato salvo com sucesso
```

**Verificar banco:**
```bash
railway run python -c "
from jung_core import DatabaseManager
db = DatabaseManager()
cursor = db.conn.cursor()
cursor.execute('''
    SELECT fact_type, fact_attribute, fact_value
    FROM user_facts_v2
    WHERE fact_category = \"RELACIONAMENTO\" AND is_current = 1
''')
for row in cursor.fetchall():
    print(f'{row[0]}.{row[1]} = {row[2]}')
"
```

**Esperado:**
```
esposa.nome = Ana Maria
```

### Teste 3: Múltiplas Pessoas

**Telegram - Envie:**
```
Tenho dois filhos: João de 12 anos e Maria de 8 anos
```

**Verificar:**
```
filho.nome_1 = João
filho.idade_1 = 12 anos
filho.nome_2 = Maria
filho.idade_2 = 8 anos
```

### Teste 4: Contexto com Nomes

**Telegram - Envie:**
```
Como você acha que está minha família?
```

**Resposta esperada do Jung:**
```
Fico feliz que você queira conversar sobre sua família!

Como estão Ana Maria e as crianças? João já completou 12 anos, deve estar...
```

---

## 🐛 Troubleshooting

### Problema: LLM não está extraindo fatos

**Verificar:**
1. XAI_API_KEY está configurada?
   ```bash
   railway variables
   ```

2. Grok está respondendo?
   ```bash
   railway logs --tail
   ```
   Procurar por: `🤖 [LLM EXTRACTOR]`

3. Fallback regex funciona?
   - Se sim, o problema é na chamada do LLM
   - Verificar rate limits da XAI

**Solução temporária:**
Forçar uso de regex:
```python
# No jung_core.py, comentar:
# self.fact_extractor = LLMFactExtractor(...)
self.fact_extractor = None  # Forçar regex fallback
```

### Problema: Tabela user_facts_v2 não existe

**Verificar:**
```bash
railway run python migrate_facts_v2.py show
```

**Se não existir:**
```bash
railway run python migrate_facts_v2.py
```

### Problema: Fatos não aparecem no contexto

**Verificar:**
1. Fatos foram salvos?
   ```sql
   SELECT * FROM user_facts_v2 WHERE is_current = 1 LIMIT 10
   ```

2. `build_rich_context` está usando V2?
   - Procurar logs: `📚 [DEBUG] Recuperando fatos v2`

3. User ID está correto?
   - Verificar que user_id na conversa = user_id nos fatos

---

## 📊 Monitoramento

### Métricas a Acompanhar

1. **Taxa de Extração**
   ```sql
   SELECT
       extraction_method,
       COUNT(*) as total,
       AVG(confidence) as avg_confidence
   FROM user_facts_v2
   WHERE created_at > date('now', '-7 days')
   GROUP BY extraction_method
   ```

2. **Fatos por Categoria**
   ```sql
   SELECT fact_category, COUNT(*) as total
   FROM user_facts_v2
   WHERE is_current = 1
   GROUP BY fact_category
   ORDER BY total DESC
   ```

3. **Usuários com Fatos**
   ```sql
   SELECT COUNT(DISTINCT user_id) as users_with_facts
   FROM user_facts_v2
   WHERE is_current = 1
   ```

### Dashboard (Opcional)

Adicionar em `admin_web/routes.py`:

```python
@router.get("/api/facts-stats")
async def facts_stats(username: str = Depends(verify_credentials)):
    """Estatísticas de fatos extraídos"""
    db = get_db()
    cursor = db.conn.cursor()

    # Stats
    cursor.execute("""
        SELECT
            COUNT(*) as total_facts,
            COUNT(DISTINCT user_id) as users_with_facts,
            AVG(confidence) as avg_confidence
        FROM user_facts_v2
        WHERE is_current = 1
    """)

    stats = cursor.fetchone()

    # Por categoria
    cursor.execute("""
        SELECT fact_category, COUNT(*) as count
        FROM user_facts_v2
        WHERE is_current = 1
        GROUP BY fact_category
        ORDER BY count DESC
    """)

    by_category = [dict(row) for row in cursor.fetchall()]

    return {
        "total_facts": stats[0],
        "users_with_facts": stats[1],
        "avg_confidence": round(stats[2], 2) if stats[2] else 0,
        "by_category": by_category
    }
```

---

## ✅ Critérios de Sucesso

Deploy considerado bem-sucedido quando:

- [ ] Migração executada sem erros
- [ ] LLM extrai nomes próprios corretamente
- [ ] Múltiplas pessoas da mesma categoria coexistem
- [ ] Contexto mostra nomes próprios
- [ ] Jung responde usando nomes nas conversas
- [ ] Sem regressões (funcionalidades antigas funcionam)

---

## 🔄 Rollback (Se Necessário)

Se algo der muito errado:

1. **Reverter código:**
   ```bash
   git revert HEAD
   git push
   ```

2. **Banco continua funcionando** (user_facts antiga não foi apagada)

3. **Remover tabela V2:**
   ```sql
   DROP TABLE IF EXISTS user_facts_v2;
   ```

---

## 📞 Próximos Passos

Após deploy bem-sucedido:

1. **Monitorar por 24-48h**
   - Ver se LLM está extraindo corretamente
   - Conferir custos de API do Grok
   - Verificar tempo de resposta

2. **Ajustes finos:**
   - Melhorar prompt de extração se necessário
   - Adicionar mais categorias de fatos
   - Otimizar confiança e fallbacks

3. **Features futuras:**
   - Comando `/memoria` para usuário ver seus fatos
   - Sistema de correção ("na verdade meu filho se chama...")
   - Auto-perguntas para completar perfil

---

**Autor:** Claude Code
**Versão:** 1.0
**Data:** 2025-12-19
