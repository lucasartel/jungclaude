# 📚 Documentação Completa - Sistema Proativo Jung v5.0

**Última Atualização**: 2025-12-03
**Versão**: 5.0 (Sistema de Perfilamento Estratégico)
**Status**: ✅ Produção no Railway

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Componentes Principais](#componentes-principais)
4. [Fluxo de Execução](#fluxo-de-execução)
5. [Sistema de Perfilamento Estratégico](#sistema-de-perfilamento-estratégico)
6. [Configurações](#configurações)
7. [Database Schema](#database-schema)
8. [API e Integrações](#api-e-integrações)
9. [Monitoramento e Logs](#monitoramento-e-logs)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

### O que é o Sistema Proativo?

O Sistema Proativo Jung é um mecanismo inteligente que **inicia conversas** com usuários de forma autônoma, enviando mensagens relevantes baseadas em:

1. **Insights Arquetípicos** (v1.0-4.2): Reflexões sobre tópicos das conversas anteriores
2. **Perguntas Estratégicas** (v5.0): Questionário conversacional adaptativo para enriquecer análise psicométrica

### Objetivos

- **B2C**: Manter engajamento natural com insights personalizados
- **B2B/RH**: Coletar dados psicométricos de forma conversacional e não-intrusiva
- **Qualidade**: Melhorar completude das análises de 55% → 80%

### Características Principais

✅ **Dual-Mode**: Alterna entre insights e perguntas estratégicas
✅ **Adaptativo**: Tom e conteúdo ajustam-se ao perfil do usuário
✅ **Respeitoso**: Sistema de cooldown e detecção de atividade
✅ **Inteligente**: Usa LLM + conhecimento multi-domínio
✅ **Anti-repetição**: Tracking de mensagens anteriores

---

## 🏗️ Arquitetura

### Componentes do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    SCHEDULER (APScheduler)                   │
│                  Executa a cada 30 minutos                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              JUNG PROACTIVE ADVANCED ENGINE                  │
│                 (jung_proactive_advanced.py)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌──────────────────┐          ┌──────────────────┐
│  MODO INSIGHT    │          │  MODO PERGUNTA   │
│   (v1.0-4.2)     │          │  ESTRATÉGICA     │
│                  │          │    (v5.0)        │
│ • Pares          │          │ • Gap Analyzer   │
│   Arquetípicos   │          │ • Question Gen   │
│ • Conhecimento   │          │ • Adaptive Tone  │
│   Autônomo       │          │                  │
└──────────────────┘          └──────────────────┘
        │                             │
        └──────────────┬──────────────┘
                       ▼
              ┌─────────────────┐
              │  TELEGRAM BOT   │
              │  Envia Mensagem │
              └─────────────────┘
```

### Tecnologias

- **Backend**: Python 3.11
- **Framework**: FastAPI + python-telegram-bot
- **Database**: SQLite (híbrido com ChromaDB)
- **LLM**: Claude 3.5 Sonnet (via Anthropic API)
- **Scheduler**: APScheduler
- **Deploy**: Railway (produção)

---

## 🔧 Componentes Principais

### 1. `main.py` - Orquestrador

**Responsabilidade**: Inicializa scheduler e coordena verificações periódicas

```python
def proactive_scheduler():
    """Executa a cada 30 minutos"""
    scheduler = BackgroundScheduler(timezone=utc)
    scheduler.add_job(
        func=check_users_for_proactive_messages,
        trigger="interval",
        minutes=30,
        id='proactive_messages'
    )
    scheduler.start()
```

**Configurações**:
- ⏰ Intervalo: 30 minutos
- 🕒 Timezone: UTC
- 🔄 Persistência: Sim (sobrevive a restarts)

### 2. `jung_proactive_advanced.py` - Motor Principal

**Responsabilidade**: Lógica de decisão e geração de mensagens

#### Classe: `AdvancedProactiveEngine`

##### Método: `check_and_generate_advanced_message(user_id, user_name)`

**Fluxo de Decisão**:

```python
# 1. Verificar elegibilidade
if not is_eligible(user_id):
    return None

# 2. NOVO (v5.0): Decidir tipo de mensagem
message_type = _decide_message_type(user_id)

if message_type == "strategic_question":
    # 3a. Gerar pergunta estratégica
    return _generate_strategic_question(user_id, user_name)
else:
    # 3b. Gerar insight arquetípico (modo original)
    return _generate_insight_message(user_id, user_name)
```

#### Método: `_decide_message_type(user_id)` ⭐ NOVO v5.0

**Regras de Decisão**:

```python
def _decide_message_type(self, user_id: str) -> str:
    """
    Decide entre insight vs pergunta estratégica

    Lógica:
    1. Se não tem análise psicométrica → insight
    2. Se últimas 2 proativas foram perguntas → insight (variedade)
    3. Se completude < 70% → strategic_question (80% chance)
    4. Se completude >= 70% → insight
    """

    # Analisar gaps no perfil
    analyzer = ProfileGapAnalyzer(self.db)
    gaps = analyzer.analyze_gaps(user_id)
    completeness = gaps["overall_completeness"]

    # Verificar histórico recente
    last_2_types = get_last_2_message_types(user_id)

    if all(t == "strategic_question" for t in last_2_types):
        return "insight"  # Variedade

    if completeness < 0.7:
        return "strategic_question" if random.random() < 0.8 else "insight"

    return "insight"
```

**Parâmetros**:
- `COMPLETENESS_THRESHOLD`: 0.70 (70%)
- `QUESTION_PROBABILITY`: 0.80 (80% se incompleto)
- `VARIETY_CHECK`: Últimas 2 mensagens

#### Critérios de Elegibilidade

```python
# Thresholds
MIN_CONVERSATIONS = 3        # Mínimo de conversas para participar
INACTIVITY_HOURS = 6         # Horas de inatividade necessárias
COOLDOWN_HOURS = 12          # Tempo entre mensagens proativas

# Verificações
✓ Usuário tem >= 3 conversas
✓ Última atividade > 6h atrás
✓ Última proativa > 12h atrás (ou nunca recebeu)
✓ Não está em cooldown forçado
```

### 3. `profile_gap_analyzer.py` ⭐ NOVO v5.0

**Responsabilidade**: Analisar lacunas na análise psicométrica

#### Classe: `ProfileGapAnalyzer`

##### Método: `analyze_gaps(user_id)`

**Output**:
```python
{
    "overall_completeness": 0.65,  # 0-1
    "dimension_completeness": {
        "openness": 0.80,
        "conscientiousness": 0.42,  # Gap detectado!
        "extraversion": 0.75,
        "agreeableness": 0.70,
        "neuroticism": 0.55
    },
    "missing_contexts": ["trabalho", "família", "valores"],
    "low_confidence_dimensions": ["conscientiousness"],
    "priority_questions": [
        {
            "dimension": "conscientiousness",
            "priority": 0.58,
            "reason": "Baixa completude (42%)",
            "suggested_context": "trabalho"
        }
    ],
    "recommendations": [
        "Perfil está 65% completo. Algumas dimensões precisam de mais dados.",
        "Focar em: conscientiousness",
        "Explorar contextos: trabalho, família, valores"
    ]
}
```

##### Algoritmo de Completude

```python
def _calculate_dimension_completeness(dimension, conversations, psychometrics):
    """
    Calcula completude de uma dimensão Big Five

    Fatores:
    1. Conversas relacionadas (40%)
    2. Confiança do score (30%)
    3. Variedade de contextos (30%)
    """

    # Fator 1: Conversas com keywords da dimensão
    related_convs = count_conversations_with_keywords(dimension)
    conv_score = min(related_convs / MIN_CONVERSATIONS_PER_DIMENSION, 1.0)

    # Fator 2: Confiança atual do score
    confidence = psychometrics['big_five_confidence'] / 100
    confidence_score = confidence

    # Fator 3: Contextos abordados
    contexts = count_contexts_covered(dimension, conversations)
    context_score = min(contexts / MIN_CONTEXT_VARIETY, 1.0)

    # Média ponderada
    return conv_score * 0.4 + confidence_score * 0.3 + context_score * 0.3
```

**Thresholds**:
```python
MIN_CONVERSATIONS_PER_DIMENSION = 3
MIN_CONFIDENCE_SCORE = 70  # 0-100
MIN_CONTEXT_VARIETY = 2    # Diferentes contextos de vida
```

**Keywords por Dimensão**:
```python
DIMENSION_KEYWORDS = {
    "openness": [
        "criatividade", "curiosidade", "imaginação", "arte", "música",
        "novo", "mudança", "experiência", "aprender", "explorar"
    ],
    "conscientiousness": [
        "organização", "planejamento", "disciplina", "responsabilidade",
        "prazo", "compromisso", "objetivo", "meta", "projeto"
    ],
    # ... (ver código completo)
}
```

**Contextos de Vida**:
```python
LIFE_CONTEXTS = [
    "trabalho", "carreira", "relacionamentos", "família", "amigos",
    "hobbies", "lazer", "valores", "ética", "passado", "infância",
    "futuro", "sonhos", "desafios", "conflitos"
]
```

### 4. `strategic_question_generator.py` ⭐ NOVO v5.0

**Responsabilidade**: Gerar perguntas naturais adaptadas ao perfil

#### Classe: `StrategicQuestionGenerator`

##### Banco de Templates (50+)

**Tipos de Pergunta**:
1. **Direct Masked**: Perguntas diretas disfarçadas de reflexão
2. **Storytelling**: Contextualiza com história/conceito antes
3. **Dilemma**: Apresenta escolhas situacionais
4. **Reflection**: Convida autoavaliação natural

**Exemplo - Openness**:
```python
{
    "type": "direct_masked",
    "template": "Tenho refletido sobre como cada pessoa lida com mudanças... {name}, você costuma abraçar o novo ou prefere o familiar?",
    "reveals": ["abertura a experiências", "tolerância ao risco"],
    "tone": "reflexivo",
    "context_hints": ["mudança", "novo"]
}
```

**Exemplo - Conscientiousness**:
```python
{
    "type": "dilemma",
    "template": "Imagine que você tem um projeto importante mas sem prazo definido. Como você aborda isso? (A) cria cronograma próprio, ou (B) trabalha conforme inspiração?",
    "reveals": ["autodisciplina", "organização"],
    "tone": "prático",
    "context_hints": ["trabalho", "projeto"]
}
```

##### Adaptive Tone Engine

**Regras de Adaptação**:

```python
TONE_ADAPTATION_RULES = {
    "high_openness": {
        "preferred_types": ["storytelling", "reflection", "dilemma"],
        "style": "Use linguagem filosófica e abstrata",
        "example": "Jung falava sobre pessoas que veem o mundo como um livro aberto..."
    },
    "low_openness": {
        "preferred_types": ["direct_masked", "contextual"],
        "avoid_types": ["storytelling"],
        "style": "Use linguagem prática e concreta",
        "example": "No dia a dia, você prefere ter tudo planejado ou deixar espaço para improviso?"
    },
    "high_conscientiousness": {
        "preferred_types": ["dilemma", "contextual"],
        "style": "Perguntas estruturadas e práticas"
    },
    "high_extraversion": {
        "preferred_types": ["direct_masked"],
        "style": "Tom energético e direto"
    },
    "low_extraversion": {
        "preferred_types": ["reflection", "storytelling"],
        "style": "Tom gentil e contemplativo"
    },
    "high_neuroticism": {
        "preferred_types": ["reflection", "storytelling"],
        "avoid_types": ["dilemma"],
        "style": "Tom cuidadoso e validador"
    }
}
```

##### Método: `generate_question(target_dimension, user_id, user_name, context_hint)`

**Output**:
```python
{
    "question": "No trabalho, você prefere ter tudo planejado com antecedência ou deixar espaço para improviso?",
    "dimension": "conscientiousness",
    "type": "contextual",
    "reveals": ["planejamento profissional", "flexibilidade"],
    "tone": "profissional",
    "metadata": {
        "context": "trabalho",
        "adapted": True,
        "user_profile_considered": True
    }
}
```

---

## 🔄 Fluxo de Execução

### Ciclo Completo (30 minutos)

```
┌──────────────────────────────────────────────────────────┐
│ 1. SCHEDULER TRIGGER (a cada 30 min)                     │
└───────────────────┬──────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────┐
│ 2. BUSCAR TODOS USUÁRIOS                                 │
│    SELECT * FROM users WHERE platform='telegram'         │
└───────────────────┬──────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────┐
│ 3. PARA CADA USUÁRIO: VERIFICAR ELEGIBILIDADE            │
│                                                           │
│    ✓ Tem >= 3 conversas?                                 │
│    ✓ Última atividade > 6h?                              │
│    ✓ Última proativa > 12h?                              │
└───────────────────┬──────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼ SIM                   ▼ NÃO
┌────────────────┐      ┌───────────────┐
│ 4. ELIGIBLE    │      │ 4. SKIP       │
│ Continuar      │      │ Próximo user  │
└───────┬────────┘      └───────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│ 5. DECIDIR TIPO DE MENSAGEM (v5.0)                       │
│                                                           │
│    • Analisar completude do perfil                       │
│    • Verificar últimas 2 mensagens                       │
│    • Aplicar regras de decisão                           │
└───────────────────┬──────────────────────────────────────┘
                    │
        ┌───────────┴────────────┐
        │                        │
        ▼ strategic_question     ▼ insight
┌────────────────────┐   ┌────────────────────┐
│ 6a. GERAR PERGUNTA │   │ 6b. GERAR INSIGHT  │
│                    │   │                    │
│ • Gap Analyzer     │   │ • Pares            │
│ • Question Gen     │   │   Arquetípicos     │
│ • Adaptive Tone    │   │ • Conhecimento     │
│                    │   │   Autônomo         │
└─────────┬──────────┘   └─────────┬──────────┘
          │                        │
          └────────────┬───────────┘
                       ▼
┌──────────────────────────────────────────────────────────┐
│ 7. SALVAR NO BANCO                                       │
│                                                           │
│    • proactive_approaches (sempre)                       │
│    • strategic_questions (se pergunta)                   │
│    • conversations (como memória)                        │
└───────────────────┬──────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────┐
│ 8. ENVIAR VIA TELEGRAM                                   │
│                                                           │
│    bot.send_message(chat_id, text)                       │
└───────────────────┬──────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────┐
│ 9. LOGGING & METRICS                                     │
│                                                           │
│    ✅ Mensagem enviada com sucesso                       │
│    📊 Atualizar cooldown_until                           │
│    📈 Incrementar contadores                             │
└──────────────────────────────────────────────────────────┘
```

---

## 💎 Sistema de Perfilamento Estratégico (v5.0)

### Visão Geral

Sistema híbrido que combina:
- **Insights** (v1-4): Mantém engajamento e relacionamento
- **Perguntas** (v5): Coleta dados para análise psicométrica

### Quando Usar Cada Modo?

| Condição | Tipo | Probabilidade | Razão |
|----------|------|---------------|-------|
| Completude < 70% | Pergunta | 80% | Precisa coletar dados |
| Completude >= 70% | Insight | 100% | Perfil já completo |
| Últimas 2 = perguntas | Insight | 100% | Variedade |
| Sem análise psicométrica | Insight | 100% | Fallback seguro |

### Exemplo de Decisão

**Usuário A** (João):
- Completude: 45%
- Últimas 2 mensagens: insight, insight
- **Decisão**: 80% chance de **pergunta estratégica**

**Pergunta gerada**:
```
"João, tenho refletido sobre como cada pessoa lida com
prazos e organização no trabalho...

Você costuma:
(A) planejar tudo com antecedência, ou
(B) trabalhar de forma mais flexível, conforme as coisas surgem?

Não há resposta certa, só quero entender melhor seu estilo! 😊"
```

**Dimensão alvo**: `conscientiousness` (score atual: 42%)

### Métricas de Sucesso

| Métrica | Baseline | Meta | Atual |
|---------|----------|------|-------|
| Completude média | 55% | 80% | *A medir* |
| Taxa de resposta | N/A | >60% | *A medir* |
| Confiança score | 60 | 75 | *A medir* |
| Red flags | 100% | 60% | *A medir* |

---

## ⚙️ Configurações

### Variáveis de Ambiente

```bash
# Telegram
TELEGRAM_TOKEN=<seu_token>

# Anthropic (LLM)
ANTHROPIC_API_KEY=<sua_chave>

# OpenAI (Embeddings)
OPENAI_API_KEY=<sua_chave>

# Admin (opcional)
ADMIN_USERS=admin:$2b$12$hashedpassword
```

### Parâmetros do Sistema

```python
# Scheduler
SCHEDULER_INTERVAL_MINUTES = 30

# Elegibilidade
MIN_CONVERSATIONS = 3
INACTIVITY_HOURS = 6
COOLDOWN_HOURS = 12

# Perfilamento Estratégico
COMPLETENESS_THRESHOLD = 0.70
QUESTION_PROBABILITY = 0.80
VARIETY_CHECK_SIZE = 2

# Gap Analyzer
MIN_CONVERSATIONS_PER_DIMENSION = 3
MIN_CONFIDENCE_SCORE = 70
MIN_CONTEXT_VARIETY = 2
```

### Configuração no Railway

1. **Variáveis de Ambiente**: Configuradas no dashboard
2. **Deploy Automático**: Push para `main` → deploy
3. **Logs**: Acessíveis via dashboard
4. **Database**: Volume persistente em `/data`

---

## 🗄️ Database Schema

### Tabela: `proactive_approaches`

```sql
CREATE TABLE IF NOT EXISTS proactive_approaches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,

    -- Arquétipos usados
    archetype_primary TEXT NOT NULL,
    archetype_secondary TEXT NOT NULL,

    -- Conteúdo
    knowledge_domain TEXT NOT NULL,
    topic_extracted TEXT,
    autonomous_insight TEXT,

    -- Metadados
    complexity_score REAL DEFAULT 0.5,
    facts_used TEXT,  -- JSON array
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- v5.0: Tipo de mensagem (adicionado via UPDATE)
    message_type TEXT DEFAULT 'insight',  -- 'insight' ou 'strategic_question'

    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_proactive_approaches_user
ON proactive_approaches(user_id, timestamp DESC);
```

### Tabela: `strategic_questions` ⭐ NOVO v5.0

```sql
CREATE TABLE IF NOT EXISTS strategic_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,

    -- Pergunta
    question_text TEXT NOT NULL,
    target_dimension TEXT NOT NULL,
    question_type TEXT,

    -- Gap info
    gap_type TEXT,
    gap_priority REAL,
    reveals TEXT,  -- JSON array

    -- Timestamps
    asked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    answered BOOLEAN DEFAULT 0,
    answer_timestamp DATETIME,

    -- Qualidade
    answer_quality_score REAL,
    improved_analysis BOOLEAN DEFAULT 0,

    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_strategic_questions_user
ON strategic_questions(user_id, asked_at DESC);
```

### Queries Comuns

**Buscar mensagens proativas de um usuário**:
```sql
SELECT
    autonomous_insight,
    timestamp,
    archetype_primary,
    archetype_secondary,
    topic_extracted,
    message_type
FROM proactive_approaches
WHERE user_id = ?
ORDER BY timestamp DESC
LIMIT 10;
```

**Verificar cooldown**:
```sql
SELECT timestamp
FROM proactive_approaches
WHERE user_id = ?
ORDER BY timestamp DESC
LIMIT 1;

-- Se (NOW - timestamp) < 12h → em cooldown
```

**Buscar perguntas não respondidas**:
```sql
SELECT
    question_text,
    target_dimension,
    asked_at
FROM strategic_questions
WHERE user_id = ? AND answered = 0
ORDER BY asked_at DESC;
```

---

## 🔌 API e Integrações

### Telegram Bot

**Envio de Mensagem Proativa**:
```python
async def send_proactive_message(chat_id, message_text):
    await application.bot.send_message(
        chat_id=chat_id,
        text=message_text,
        parse_mode='Markdown'
    )
```

### Admin Web

**Endpoint**: `/admin/user/{user_id}/agent-data`

**Dados Exibidos**:
```python
{
    "summary": {
        "total_conversations": 156,
        "reactive_count": 145,
        "proactive_count": 11,
        "first_interaction": "2024-11-15 10:23",
        "last_activity": "2025-12-02 21:15",
        "proactive_status": "⏸️ Cooldown (3.1h restantes)",
        "response_rate": 93
    },
    "reactive_messages": [...],  # Últimas 10
    "proactive_messages": [...]  # Últimas 10
}
```

### LLM (Claude)

**Geração de Insights**:
```python
prompt = f"""
Você é um assistente junguiano avançado.

Par arquetípico: {archetype_pair}
Tópicos recentes: {topics}
Conhecimento: {knowledge_domain}

Gere um insight profundo e personalizado para {user_name}.
"""

response = anthropic_client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=500,
    messages=[{"role": "user", "content": prompt}]
)
```

---

## 📊 Monitoramento e Logs

### Logs do Sistema

**Formato**:
```
2025-12-03 14:10:52 - INFO - 🔍 [PROATIVO] Verificando usuários elegíveis...
2025-12-03 14:10:52 - INFO -    📊 Total de usuários: 4
2025-12-03 14:10:52 - INFO - 🧠 [PROATIVO] GERAÇÃO AVANÇADA para João (abc123...)
2025-12-03 14:10:52 - INFO -    📊 Total de conversas: 156 (mínimo: 3)
2025-12-03 14:10:52 - INFO -    ⏰ Última atividade: 17.3h atrás (mínimo: 6h)
2025-12-03 14:10:52 - INFO -    🔄 Última proativa: 8.9h atrás (cooldown: 12h)
2025-12-03 14:10:52 - INFO -    🎯 Tipo de mensagem: strategic_question
2025-12-03 14:10:52 - INFO -    🔍 [GAP ANALYZER] Completude: 65%
2025-12-03 14:10:52 - INFO -    📝 [QUESTION GEN] Dimensão: conscientiousness
2025-12-03 14:10:53 - INFO - ✅ Mensagem proativa enviada!
```

### Métricas no Railway

**Dashboard**:
- CPU Usage
- Memory Usage
- Request Count
- Error Rate
- Deploy History

**Logs em Tempo Real**:
```bash
# Via Railway CLI
railway logs --tail

# Filtrar por erro
railway logs | grep ERROR
```

### Health Checks

**Endpoint**: `/admin/api/sync-status`

**Response**:
```json
{
    "status": "ok",
    "database": "connected",
    "last_check": "2025-12-03T14:10:52Z"
}
```

---

## 🔧 Troubleshooting

### Problema: Mensagens não estão sendo enviadas

**Diagnóstico**:
```python
# 1. Verificar scheduler
logger.info("Scheduler está rodando?")

# 2. Verificar elegibilidade
engine = AdvancedProactiveEngine(db)
for user in users:
    eligible = engine.check_and_generate_advanced_message(user.user_id, user.first_name)
    logger.info(f"User {user.user_id}: {eligible}")

# 3. Verificar cooldowns
SELECT user_id, MAX(timestamp) as last_proactive
FROM proactive_approaches
GROUP BY user_id;
```

**Soluções**:
- ✅ Verificar se `SCHEDULER_INTERVAL_MINUTES` está configurado
- ✅ Verificar se usuários atendem critérios de elegibilidade
- ✅ Verificar logs de erro no Railway

### Problema: Perguntas estratégicas não são geradas

**Diagnóstico**:
```python
# Verificar completude do perfil
analyzer = ProfileGapAnalyzer(db)
gaps = analyzer.analyze_gaps(user_id)
print(f"Completeness: {gaps['overall_completeness']}")

# Se >= 0.70 → sempre insight
# Se < 0.70 → 80% chance de pergunta
```

**Soluções**:
- ✅ Verificar se análise psicométrica existe
- ✅ Verificar regra de variedade (últimas 2 mensagens)
- ✅ Ajustar `COMPLETENESS_THRESHOLD` se necessário

### Problema: Tabela `strategic_questions` não existe

**Solução**:
```python
# A tabela é criada automaticamente na primeira pergunta
# Se necessário, criar manualmente:

cursor.execute("""
    CREATE TABLE IF NOT EXISTS strategic_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        question_text TEXT NOT NULL,
        target_dimension TEXT NOT NULL,
        question_type TEXT,
        gap_type TEXT,
        gap_priority REAL,
        reveals TEXT,
        asked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        answered BOOLEAN DEFAULT 0,
        answer_timestamp DATETIME,
        answer_quality_score REAL,
        improved_analysis BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
""")
```

### Problema: Erro "no such column"

**Diagnóstico**:
```sql
-- Verificar schema das tabelas
PRAGMA table_info(proactive_approaches);
PRAGMA table_info(conversations);
PRAGMA table_info(strategic_questions);
```

**Colunas corretas**:
- `conversations`: `ai_response` (não `bot_response`)
- `proactive_approaches`: `autonomous_insight` (não `message`)
- `proactive_approaches`: `timestamp` (não `sent_at`)

---

## 📚 Referências

### Arquivos Principais

1. **[main.py](main.py)** - Inicialização e scheduler
2. **[jung_proactive_advanced.py](jung_proactive_advanced.py)** - Motor proativo
3. **[profile_gap_analyzer.py](profile_gap_analyzer.py)** - Análise de gaps
4. **[strategic_question_generator.py](strategic_question_generator.py)** - Geração de perguntas
5. **[admin_web/routes.py](admin_web/routes.py)** - Admin web (dados do agente)

### Documentação Relacionada

- [STRATEGIC_PROFILING_README.md](STRATEGIC_PROFILING_README.md) - Sistema de perfilamento
- [PLANO_PROATIVIDADE_PERFILAMENTO.md](PLANO_PROATIVIDADE_PERFILAMENTO.md) - Plano técnico
- [ROADMAP.md](ROADMAP.md) - Roadmap do projeto

### Commits Relevantes

- `92d83cd` - Core do sistema de perfilamento estratégico
- `7ce3829` - Integração com sistema proativo
- `061b5a9` - Reformulação do admin "Dados do Agente"
- `16e7950` - Fix: cursor row_factory
- `d9c8e7a` - Fix: schema correto proactive_approaches
- `2cc17a4` - Fix: ai_response vs bot_response
- `7455dba` - Fix: remover JOIN com strategic_questions

---

## 🎯 Próximos Passos

### Melhorias Planejadas

1. **Tracking de Respostas**:
   - Detectar quando usuário responde a pergunta estratégica
   - Marcar `answered = 1` na tabela
   - Calcular `answer_quality_score`

2. **Analytics Dashboard**:
   - Taxa de resposta por tipo de pergunta
   - Melhoria de completude ao longo do tempo
   - Correlação entre tipo de pergunta e engajamento

3. **A/B Testing**:
   - Testar diferentes tons de pergunta
   - Testar frequência (30min vs 1h)
   - Testar momento do dia (manhã vs noite)

4. **Adaptive Frequency**:
   - Aumentar frequência se usuário responde rápido
   - Diminuir se usuário ignora mensagens

---

**Versão**: 5.0
**Última Atualização**: 2025-12-03
**Autores**: Sistema Jung + Claude Code
**Status**: ✅ Produção no Railway
