# 📋 Instruções Pós-Deploy - Sistema de Fatos V2

**Status:** Deploy em andamento no Railway
**Data:** 2025-12-19

---

## 🚀 Passo 1: Aguardar Deploy (2-3 minutos)

Verifique se o deploy foi concluído:
1. Acesse: https://railway.app/project/[seu-projeto]/deployments
2. Aguarde status: **✅ Success**
3. Verifique logs para: `✅ Rotas do admin web carregadas`

---

## 🔧 Passo 2: Executar Migração

### Opção A: Via Endpoint (Recomendado)

**1. Verificar status atual:**
```
GET https://jungproject-production.up.railway.app/admin/facts-v2/status
```

Resposta esperada:
```json
{
  "user_facts_v2_exists": false,
  "status": "not_migrated",
  "action": "Execute POST /admin/migrate/facts-v2"
}
```

**2. Executar migração:**
```bash
curl -X POST https://jungproject-production.up.railway.app/admin/migrate/facts-v2
```

Ou via browser/Postman:
```
POST https://jungproject-production.up.railway.app/admin/migrate/facts-v2
```

Resposta de sucesso:
```json
{
  "status": "success",
  "message": "Migração para user_facts_v2 concluída com sucesso",
  "next_steps": [
    "1. Verificar logs do Railway",
    "2. Integrar código no jung_core.py",
    "3. Testar com mensagem: 'Minha esposa se chama [nome]'",
    "4. Remover este endpoint depois dos testes"
  ]
}
```

**3. Verificar logs do Railway:**
- Procurar por: `✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO`
- Ver quantos fatos foram migrados

---

## 🔨 Passo 3: Integrar Código no jung_core.py

**IMPORTANTE:** Esta etapa precisa ser feita manualmente editando o arquivo.

### 3.1 Adicionar Import (linha ~34)

Adicionar após `from openai import OpenAI`:

```python
# Extrator de fatos com LLM
try:
    from llm_fact_extractor import LLMFactExtractor
    LLM_FACT_EXTRACTOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ LLMFactExtractor não disponível: {e}")
    LLM_FACT_EXTRACTOR_AVAILABLE = False
```

### 3.2 Inicializar Extrator (classe HybridDatabaseManager.__init__)

Adicionar após inicialização do ChromaDB (por volta da linha 750):

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

### 3.3 Copiar Novos Métodos

Abrir arquivo: `jung_core_facts_v2_integration.py`

**Copiar para jung_core.py:**

1. **Método `extract_and_save_facts_v2`** (substituir o antigo ou adicionar novo)
   - Localização sugerida: Linha ~1572 (depois do método antigo)

2. **Método `_save_fact_v2`**
   - Localização sugerida: Linha ~1647 (depois de `_save_or_update_fact`)

### 3.4 Atualizar Chamada

Localização: Linha ~1171 (dentro de `save_conversation`)

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

### 3.5 Commit e Push

```bash
git add jung_core.py
git commit -m "feat: Integrar LLM Fact Extractor V2 no jung_core

- Adiciona import de LLMFactExtractor
- Inicializa extrator com Grok
- Usa extract_and_save_facts_v2
- Mantém fallback para método antigo"
git push
```

---

## 🧪 Passo 4: Testar o Sistema

### Teste 1: Extração de Nome da Esposa

**Via Telegram, envie:**
```
Minha esposa se chama Ana Maria
```

**Aguarde resposta do Jung**

**Verificar nos logs do Railway:**
```
🤖 [LLM EXTRACTOR] Extraindo fatos de: Minha esposa se chama Ana Maria
✅ LLM extraiu 1 fatos
📝 [FACTS V2] Salvando: RELACIONAMENTO.esposa.nome = Ana Maria
✅ Fato salvo com sucesso
```

**Verificar via endpoint:**
```
GET https://jungproject-production.up.railway.app/admin/facts-v2/status
```

Deve mostrar:
```json
{
  "by_category": {
    "RELACIONAMENTO": 1
  }
}
```

### Teste 2: Múltiplos Filhos

**Via Telegram:**
```
Tenho dois filhos: João de 12 anos e Maria de 8 anos
```

**Logs esperados:**
```
🤖 [LLM EXTRACTOR] Extraindo fatos
✅ LLM extraiu 4 fatos
📝 [FACTS V2] Salvando: RELACIONAMENTO.filho.nome_1 = João
📝 [FACTS V2] Salvando: RELACIONAMENTO.filho.idade_1 = 12 anos
📝 [FACTS V2] Salvando: RELACIONAMENTO.filho.nome_2 = Maria
📝 [FACTS V2] Salvando: RELACIONAMENTO.filho.idade_2 = 8 anos
```

### Teste 3: Memória Funciona

**30 minutos depois, envie:**
```
Como está minha família?
```

**Jung DEVE responder algo como:**
```
Fico feliz que você queira conversar sobre sua família!

Como estão Ana Maria e as crianças? João com 12 anos
deve estar em uma fase interessante...
```

**Se NÃO mencionar os nomes:** ❌ Contexto não está usando facts_v2
- Verificar se `build_rich_context` foi atualizado

---

## 🐛 Troubleshooting Rápido

### Problema: "Module llm_fact_extractor not found"

**Causa:** Deploy não incluiu o arquivo

**Solução:**
```bash
git status  # Verificar se está commitado
git push    # Forçar push
```

### Problema: "LLM não está extraindo fatos"

**Verificar:**
1. XAI_API_KEY está configurada?
   ```
   railway variables
   ```

2. Grok está respondendo?
   - Logs: `🤖 [LLM EXTRACTOR]`

**Solução temporária:**
Comentar inicialização do fact_extractor:
```python
# self.fact_extractor = LLMFactExtractor(...)
self.fact_extractor = None  # Usar regex fallback
```

### Problema: "Tabela user_facts_v2 não existe"

**Solução:**
```
POST https://jungproject-production.up.railway.app/admin/migrate/facts-v2
```

---

## ✅ Checklist Final

Depois de tudo funcionando:

- [ ] Migração executada com sucesso
- [ ] LLM extrai nomes próprios corretamente
- [ ] Jung usa nomes nas respostas
- [ ] Múltiplas pessoas coexistem
- [ ] Sem erros nos logs
- [ ] **REMOVER** endpoints de migração (main.py)

---

## 📊 Monitoramento Contínuo

### Verificar Diariamente (primeiros 3 dias)

1. **Quantidade de fatos extraídos:**
   ```
   GET /admin/facts-v2/status
   ```

2. **Logs de erro:**
   - Procurar: `❌ Erro no LLM`
   - Procurar: `❌ PROBLEMA`

3. **Feedback dos usuários:**
   - Jung está usando nomes?
   - Usuários reclamam de memória?

### Métricas de Sucesso

**Após 7 dias:**
- [ ] 80%+ dos fatos extraídos via LLM (não regex)
- [ ] 0 reclamações de memória
- [ ] Confiança média > 0.8
- [ ] Custo API Grok < $2/semana

---

## 🎉 Próximos Passos (Após Estabilização)

1. **Adicionar mais categorias:**
   - HOBBIES, EDUCACAO, SAUDE

2. **Comando `/memoria`:**
   - Usuário vê seus fatos salvos
   - Pode corrigir informações

3. **Auto-perguntas:**
   - Jung pergunta para completar perfil
   - "Qual a idade dos seus filhos?"

4. **Analytics:**
   - Dashboard de fatos mais comuns
   - Evolução de completude de perfis

---

**Boa sorte com o deploy! 🚀**

Em caso de problemas, consulte: `ANALISE_GAPS_MEMORIA.md` e `DEPLOY_FACTS_V2.md`
