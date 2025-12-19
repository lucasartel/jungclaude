# 🔍 Análise de Gaps no Sistema de Memória Semântica

**Data:** 2025-12-19
**Status:** 🔴 CRÍTICO - Sistema tem falhas graves na extração de fatos

---

## 📋 Resumo Executivo

O sistema de memória do JungAgent apresenta **gaps críticos** que impedem o agente de lembrar informações básicas sobre o usuário, como nomes de familiares. Foram identificados 3 problemas principais:

### 🔴 Problema Principal
**O agente não se lembra do nome da esposa e filhos do usuário, mesmo após informado.**

---

## 🔬 Análise Técnica Detalhada

### 1. Fluxo Atual de Memória

#### 1.1 Extração de Fatos (`extract_and_save_facts`)
**Localização:** `jung_core.py:1572-1645`

O sistema usa **regex patterns** simples para detectar fatos:

```python
# Relacionamentos detectados
relationship_patterns = [
    'meu namorado', 'minha namorada', 'meu marido', 'minha esposa',
    'meu pai', 'minha mãe', 'meu irmão', 'minha irmã'
]

for pattern in relationship_patterns:
    if pattern in input_lower:
        self._save_or_update_fact(
            user_id, 'RELACIONAMENTO', 'pessoa', pattern, conversation_id
        )
```

#### 1.2 Problemas Identificados

##### ❌ PROBLEMA 1: Extração Incompleta de Nomes Próprios

**Teste realizado:**
- Input: `"Minha esposa se chama Maria"`
- **Extraído:** `pessoa: minha esposa` ✅
- **NÃO extraído:** `nome_esposa: Maria` ❌

**Teste realizado:**
- Input: `"Tenho dois filhos: João e Pedro"`
- **Extraído:** NADA ❌
- **Esperado:** `filhos: ['João', 'Pedro']` ou `filho_1: João`, `filho_2: Pedro`

##### ❌ PROBLEMA 2: Chave Única Sobrescrita

A tabela `user_facts` usa `(user_id, fact_category, fact_key)` como chave composta.

**Problema:** Múltiplas pessoas da mesma categoria sobrescrevem umas às outras.

**Exemplo do teste:**
```
✏️ Atualizando fato existente: 'minha esposa' → 'meu pai'
✏️ Atualizando fato existente: 'meu pai' → 'minha mãe'
```

**Resultado final:**
```sql
RELACIONAMENTO:
  pessoa: minha esposa (v1) ✗ ANTIGO
  pessoa: meu pai (v2) ✗ ANTIGO
  pessoa: minha mãe (v3) ✓ ATUAL  <-- Apenas este fica "atual"
```

**O que deveria acontecer:**
Todas as pessoas deveriam coexistir:
- `pessoa_esposa: Maria`
- `pessoa_pai: [sem nome]`
- `pessoa_mae: [sem nome]`
- `filho_1: João`
- `filho_2: Pedro`

##### ❌ PROBLEMA 3: Patterns Insuficientes

**Patterns atuais são muito limitados:**

Relacionamentos **detectados**:
- ✅ "minha esposa", "meu marido"
- ✅ "meu pai", "minha mãe"

Relacionamentos **NÃO detectados**:
- ❌ "meus filhos"
- ❌ "meu filho se chama..."
- ❌ "minha filha..."
- ❌ "meu irmão João"
- ❌ "minha avó"
- ❌ "meu melhor amigo"
- ❌ "meu chefe"
- ❌ "meu colega de trabalho"

---

### 2. Fluxo de Recuperação de Memória

#### 2.1 Build Rich Context (`build_rich_context`)
**Localização:** `jung_core.py:1431-1566`

O contexto é construído corretamente e **inclui fatos salvos**:

```python
# Query SQL que recupera fatos
cursor.execute("""
    SELECT fact_category, fact_key, fact_value
    FROM user_facts
    WHERE user_id = ? AND is_current = 1
    ORDER BY fact_category, fact_key
""", (user_id,))
```

**Contexto gerado** (exemplo do teste):
```
📋 FATOS CONHECIDOS:

PERSONALIDADE:
  - traço: introvertido

RELACIONAMENTO:
  - pessoa: minha mãe  <-- Apenas a última pessoa!

TRABALHO:
  - profissao: desenvolvedor
```

✅ **A recuperação funciona**
❌ **Mas os fatos salvos estão incompletos**

---

## 🎯 Impacto nos Usuários

### Cenário Real (Seu Caso)
**Conversa:**
- Você: "Minha esposa se chama Ana"
- Você: "Tenho dois filhos: Lucas e Maria"

**30 minutos depois:**
- Você: "Como está minha família?"
- Jung: "Desculpe, não tenho informações sobre sua família" ❌

**O que o Jung deveria responder:**
- Jung: "Que bom te ver de novo! Como estão Ana, Lucas e Maria?" ✅

### Frequência Esperada do Problema
- 🔴 **Alta:** Qualquer conversa sobre família, amigos ou relacionamentos
- 🔴 **Crítica:** Informações mencionadas uma única vez são perdidas
- 🔴 **Permanente:** Não se resolve com mais conversas

---

## 💡 Soluções Propostas

### Solução 1: Extração com LLM (Recomendada)
**Ao invés de regex, usar Claude/GPT para extrair fatos estruturados**

**Prompt exemplo:**
```
Extraia TODOS os fatos estruturados desta mensagem do usuário.
Retorne em JSON no formato:

{
  "fatos": [
    {
      "categoria": "RELACIONAMENTO",
      "tipo": "esposa",
      "nome": "Ana",
      "contexto": "menciona esposa pela primeira vez"
    },
    {
      "categoria": "RELACIONAMENTO",
      "tipo": "filho",
      "nome": "Lucas",
      "idade_aproximada": "criança/adolescente/adulto"
    }
  ]
}

Mensagem: "Minha esposa Ana e meus filhos Lucas e Maria foram ao parque"
```

**Vantagens:**
- ✅ Captura nomes próprios
- ✅ Entende contexto ("esposa Ana" → nome=Ana, tipo=esposa)
- ✅ Detecta múltiplas pessoas na mesma frase
- ✅ Flexível para novos tipos de relacionamento

**Desvantagens:**
- ⚠️ Custo de API (mas pode usar modelo barato como grok-beta)
- ⚠️ Latência adicional

### Solução 2: Regex Melhorado + Parser NER
**Usar Named Entity Recognition para nomes próprios**

```python
import spacy
nlp = spacy.load("pt_core_news_sm")

def extract_names_and_relationships(text):
    doc = nlp(text)

    # Detectar relacionamentos
    relationships = re.findall(r'minh[ao] (\w+)', text.lower())

    # Detectar nomes próprios
    names = [ent.text for ent in doc.ents if ent.label_ == "PER"]

    # Combinar contexto
    facts = []
    for rel in relationships:
        if names:
            facts.append({
                'tipo': rel,
                'nome': names.pop(0) if names else None
            })

    return facts
```

**Exemplo:**
- Input: "Minha esposa Ana e meu filho Pedro"
- Output: `[{tipo: 'esposa', nome: 'Ana'}, {tipo: 'filho', nome: 'Pedro'}]`

**Vantagens:**
- ✅ Mais rápido que LLM
- ✅ Sem custo de API
- ✅ Captura nomes próprios

**Desvantagens:**
- ⚠️ Menos flexível
- ⚠️ Pode errar em casos complexos

### Solução 3: Schema de Fatos Melhorado
**Mudar estrutura da tabela `user_facts`**

**Problema atual:**
```sql
CREATE TABLE user_facts (
    user_id TEXT,
    fact_category TEXT,
    fact_key TEXT,      -- ❌ "pessoa" para TODOS
    fact_value TEXT,    -- ❌ "minha esposa" (sem nome)
    UNIQUE(user_id, fact_category, fact_key)  -- ❌ Sobrescreve
)
```

**Solução proposta:**
```sql
CREATE TABLE user_facts (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    fact_category TEXT NOT NULL,
    fact_type TEXT,           -- ✅ 'esposa', 'filho', 'pai'
    fact_key TEXT,            -- ✅ 'nome', 'idade', 'profissao'
    fact_value TEXT NOT NULL,
    metadata JSON,            -- ✅ Dados extras
    is_current BOOLEAN DEFAULT 1,
    version INTEGER DEFAULT 1,
    source_conversation_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)

CREATE UNIQUE INDEX idx_facts_unique
ON user_facts(user_id, fact_category, fact_type, fact_key, is_current)
WHERE is_current = 1;
```

**Exemplos:**
```sql
-- Esposa
(user_id, category='RELACIONAMENTO', type='esposa', key='nome', value='Ana')
(user_id, category='RELACIONAMENTO', type='esposa', key='profissao', value='médica')

-- Filho 1
(user_id, category='RELACIONAMENTO', type='filho', key='nome_1', value='Lucas')
(user_id, category='RELACIONAMENTO', type='filho', key='idade_1', value='10 anos')

-- Filho 2
(user_id, category='RELACIONAMENTO', type='filho', key='nome_2', value='Maria')
```

**Vantagens:**
- ✅ Múltiplas pessoas coexistem
- ✅ Informações complementares (nome + idade + profissão)
- ✅ Escalável para qualquer tipo de fato

---

## 🚀 Plano de Implementação

### Fase 1: Fix Crítico (1-2 horas)
1. ✅ Adicionar extração com LLM para nomes próprios
2. ✅ Modificar schema de `user_facts` para suportar múltiplas pessoas
3. ✅ Criar migração de dados

### Fase 2: Melhorias (2-3 horas)
1. ✅ Adicionar 50+ patterns de relacionamento
2. ✅ Implementar NER com spaCy como fallback
3. ✅ Testar com conversas reais do Railway

### Fase 3: Validação (1 hora)
1. ✅ Testar recuperação de memória com dados reais
2. ✅ Verificar se contexto inclui todos os fatos
3. ✅ Deploy no Railway

---

## 📊 Evidências do Problema

### Logs do Teste Local

```
TESTE 1: Minha esposa se chama Maria
✅ Extraídos 1 fatos
  - RELACIONAMENTO.pessoa: minha esposa  ❌ SEM NOME

TESTE 2: Tenho dois filhos: João e Pedro
❌ Fatos extraídos: 0  ❌ NADA DETECTADO

TESTE 5: Meu pai é médico e minha mãe é professora
✏️ Atualizando fato existente: 'minha esposa' → 'meu pai'
✏️ Atualizando fato existente: 'meu pai' → 'minha mãe'
❌ SOBRESCREVEU TODOS
```

### Contexto Gerado

```
📋 FATOS CONHECIDOS:

RELACIONAMENTO:
  - pessoa: minha mãe  ❌ Apenas 1 de 4 pessoas mencionadas!
```

---

## ✅ Checklist de Implementação

### Imediato (Hoje)
- [ ] Implementar extração com LLM (usar Grok para custo baixo)
- [ ] Criar nova tabela `user_facts_v2` com schema melhorado
- [ ] Script de migração de dados
- [ ] Testes com dados reais do Railway

### Curto Prazo (Esta Semana)
- [ ] Adicionar NER com spaCy
- [ ] Expandir patterns para 50+ tipos de relacionamento
- [ ] Dashboard admin para visualizar fatos extraídos
- [ ] Comando `/memoria` para usuário ver seus fatos

### Médio Prazo (Próxima Semana)
- [ ] Sistema de "confirmação de fatos" com usuário
- [ ] Auto-correção quando usuário corrige informação
- [ ] Timeline de evolução de fatos (ex: "filho nasceu", "mudou de emprego")

---

## 🎓 Lições Aprendidas

1. **Regex não é suficiente** para extração de fatos complexos
2. **Nomes próprios são críticos** para memória pessoal
3. **Schema rígido limita** tipos de informação que podemos guardar
4. **Testes automatizados** detectam problemas antes dos usuários
5. **Versionamento de fatos** é bom, mas precisa de chaves melhores

---

## 📞 Próximos Passos

**Pergunta para o usuário:**
> Qual solução você prefere implementar primeiro?
> 1. Extração com LLM (mais completa, pequeno custo de API)
> 2. Regex + NER (mais rápida, sem custo)
> 3. Ambas (LLM como principal, regex como fallback)

**Minha recomendação:** **Opção 3** - LLM principal + regex fallback
- Melhor de ambos os mundos
- Se LLM falhar ou estiver lento, regex cobre o básico
- Custo controlado (usar grok-beta que é barato)

---

**Autor:** Claude Code
**Versão:** 1.0
**Data:** 2025-12-19
