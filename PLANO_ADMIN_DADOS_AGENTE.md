# 🖥️ Plano: Reformulação da Página "Dados do Agente" no Admin

**Data:** 2025-12-04 (Quinta-feira)
**Objetivo:** Transformar a página "Desenvolvimento" em "Dados do Agente" com relatório resumido e histórico de mensagens reativas vs proativas

---

## 📊 Situação Atual

### Página Existente: `/admin/user/{user_id}/development`
**Conteúdo atual:**
- ✅ Header com info do usuário e total de conversas
- ✅ Padrões Comportamentais (tabela `user_patterns`)
- ✅ Milestones de Desenvolvimento (tabela `user_milestones`)
- ✅ Conflitos Arquetípicos Recentes (tabela `archetype_conflicts`)

**Botão na lista de usuários:**
- 🔹 Texto atual: "Desenvolvimento"
- 🔹 Cor: roxo (`text-purple-600`)
- 🔹 Localização: [users.html:53-55](c:\Users\conta\OneDrive\jungproject\admin_web\templates\users.html#L53-L55)

---

## 🎯 Visão do Novo Design

### Nova Página: "Dados do Agente"

**Estrutura:**

```
┌─────────────────────────────────────────────────────────┐
│  🤖 Dados do Agente - [Nome do Usuário]                 │
│  ← Voltar | 🧠 Ver Análise | 🧪 Ver Psicometria         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  📊 RELATÓRIO RESUMIDO DO AGENTE                         │
│  ┌───────────────┬───────────────┬───────────────┐      │
│  │ 📈 Total Conv │ 💬 Reativas   │ 🤖 Proativas  │      │
│  │     156       │     145       │      11       │      │
│  └───────────────┴───────────────┴───────────────┘      │
│                                                          │
│  ┌───────────────────────────────────────────────┐      │
│  │ 📅 Primeira Interação: 2024-11-15 10:23      │      │
│  │ ⏰ Última Atividade: 2025-12-02 21:15        │      │
│  │ 🎯 Status Proativo: ⏸️  Cooldown (3h rest)   │      │
│  │ 📊 Taxa de Resposta: 87% (145/156)           │      │
│  └───────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  💬 HISTÓRICO DE MENSAGENS DO AGENTE                     │
│                                                          │
│  ┌─────────────────────┬─────────────────────┐         │
│  │  💬 REATIVAS (10)   │  🤖 PROATIVAS (10)  │         │
│  │                     │                     │         │
│  │ [Card 1]            │ [Card 1]            │         │
│  │ User: "Como..."     │ 📅 2025-12-02 15:30 │         │
│  │ Bot: "Olá..."       │ 🎯 Tipo: insight    │         │
│  │ 📅 2025-12-03 11:45 │ Arquetípico         │         │
│  │                     │                     │         │
│  │ [Card 2]            │ [Card 2]            │         │
│  │ User: "Tenho..."    │ 📅 2025-12-01 09:15 │         │
│  │ Bot: "Entendo..."   │ 🎯 Tipo: pergunta   │         │
│  │ 📅 2025-12-03 10:22 │ estratégica         │         │
│  │                     │ Dimensão: openness  │         │
│  │ ...                 │ ...                 │         │
│  └─────────────────────┴─────────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

---

## 🏗️ Arquitetura da Solução

### 1. Modificações no Frontend

#### 1.1. Arquivo: `users.html` (Linha 53-55)
**Mudança:**
```html
<!-- ANTES -->
<a href="/admin/user/{{ user.user_id }}/development" class="text-purple-600 hover:text-purple-900">
    Desenvolvimento
</a>

<!-- DEPOIS -->
<a href="/admin/user/{{ user.user_id }}/agent-data" class="text-purple-600 hover:text-purple-900">
    Dados do Agente
</a>
```

#### 1.2. Arquivo: `user_development.html` → Renomear para `user_agent_data.html`
**Nova estrutura:**

```html
{% extends "base.html" %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-3xl font-bold text-gray-900">🤖 Dados do Agente</h1>
            <p class="mt-1 text-sm text-gray-500">Histórico e estatísticas de {{ user.user_name }}</p>
        </div>
        <div class="flex space-x-3">
            <a href="/admin/user/{{ user_id }}/psychometrics">🧪 Ver Psicometria</a>
            <a href="/admin/user/{{ user_id }}/analysis">🧠 Ver Análise</a>
            <a href="/admin/users">← Voltar</a>
        </div>
    </div>

    <!-- Relatório Resumido -->
    <div class="bg-gradient-to-r from-purple-500 to-indigo-600 shadow rounded-lg p-6 text-white">
        <h2 class="text-xl font-semibold mb-4">📊 Relatório Resumido do Agente</h2>

        <!-- Métricas Principais (3 colunas) -->
        <div class="grid grid-cols-3 gap-4 mb-6">
            <div class="bg-white bg-opacity-20 rounded-lg p-4 text-center">
                <div class="text-3xl font-bold">{{ summary.total_conversations }}</div>
                <div class="text-sm opacity-90">📈 Total de Conversas</div>
            </div>
            <div class="bg-white bg-opacity-20 rounded-lg p-4 text-center">
                <div class="text-3xl font-bold">{{ summary.reactive_count }}</div>
                <div class="text-sm opacity-90">💬 Mensagens Reativas</div>
            </div>
            <div class="bg-white bg-opacity-20 rounded-lg p-4 text-center">
                <div class="text-3xl font-bold">{{ summary.proactive_count }}</div>
                <div class="text-sm opacity-90">🤖 Mensagens Proativas</div>
            </div>
        </div>

        <!-- Informações Adicionais (2 colunas) -->
        <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
                <div class="opacity-75">📅 Primeira Interação</div>
                <div class="font-semibold">{{ summary.first_interaction }}</div>
            </div>
            <div>
                <div class="opacity-75">⏰ Última Atividade</div>
                <div class="font-semibold">{{ summary.last_activity }}</div>
            </div>
            <div>
                <div class="opacity-75">🎯 Status Proativo</div>
                <div class="font-semibold">{{ summary.proactive_status }}</div>
            </div>
            <div>
                <div class="opacity-75">📊 Taxa de Resposta</div>
                <div class="font-semibold">{{ summary.response_rate }}%</div>
            </div>
        </div>
    </div>

    <!-- Histórico de Mensagens (2 colunas) -->
    <div class="bg-white shadow rounded-lg p-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-4">💬 Histórico de Mensagens do Agente</h2>

        <div class="grid grid-cols-2 gap-6">
            <!-- Coluna 1: Reativas -->
            <div>
                <h3 class="text-lg font-medium text-gray-900 mb-3 flex items-center">
                    <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold">
                        💬 REATIVAS ({{ reactive_messages|length }})
                    </span>
                </h3>
                <div class="space-y-3">
                    {% for msg in reactive_messages %}
                    <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div class="text-xs text-gray-500 mb-2">📅 {{ msg.timestamp }}</div>

                        <!-- User input -->
                        <div class="mb-2">
                            <div class="text-xs font-semibold text-gray-700 mb-1">👤 Usuário:</div>
                            <div class="text-sm text-gray-900 bg-gray-50 p-2 rounded">
                                {{ msg.user_input[:100] }}{% if msg.user_input|length > 100 %}...{% endif %}
                            </div>
                        </div>

                        <!-- Bot response -->
                        <div>
                            <div class="text-xs font-semibold text-gray-700 mb-1">🤖 Bot:</div>
                            <div class="text-sm text-gray-700 bg-blue-50 p-2 rounded">
                                {{ msg.bot_response[:100] }}{% if msg.bot_response|length > 100 %}...{% endif %}
                            </div>
                        </div>

                        <!-- Metadata -->
                        {% if msg.keywords %}
                        <div class="mt-2 flex flex-wrap gap-1">
                            {% for keyword in msg.keywords[:3] %}
                            <span class="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded">
                                {{ keyword }}
                            </span>
                            {% endfor %}
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Coluna 2: Proativas -->
            <div>
                <h3 class="text-lg font-medium text-gray-900 mb-3 flex items-center">
                    <span class="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-semibold">
                        🤖 PROATIVAS ({{ proactive_messages|length }})
                    </span>
                </h3>
                <div class="space-y-3">
                    {% for msg in proactive_messages %}
                    <div class="border border-purple-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div class="text-xs text-gray-500 mb-2">📅 {{ msg.timestamp }}</div>

                        <!-- Message content -->
                        <div class="mb-2">
                            <div class="text-sm text-gray-900 bg-purple-50 p-3 rounded">
                                {{ msg.message }}
                            </div>
                        </div>

                        <!-- Metadata -->
                        <div class="mt-2 space-y-1">
                            <div class="flex items-center text-xs text-gray-600">
                                <span class="font-semibold mr-1">🎯 Tipo:</span>
                                <span class="bg-purple-100 text-purple-800 px-2 py-0.5 rounded">
                                    {{ msg.message_type or 'insight' }}
                                </span>
                            </div>

                            {% if msg.message_type == 'strategic_question' %}
                            <div class="flex items-center text-xs text-gray-600">
                                <span class="font-semibold mr-1">📊 Dimensão:</span>
                                <span class="bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded">
                                    {{ msg.target_dimension }}
                                </span>
                            </div>
                            {% endif %}

                            {% if msg.archetype_pair %}
                            <div class="flex items-center text-xs text-gray-600">
                                <span class="font-semibold mr-1">🎭 Arquétipos:</span>
                                <span class="text-gray-700">{{ msg.archetype_pair }}</span>
                            </div>
                            {% endif %}

                            {% if msg.topic %}
                            <div class="flex items-center text-xs text-gray-600">
                                <span class="font-semibold mr-1">💡 Tópico:</span>
                                <span class="text-gray-700">{{ msg.topic }}</span>
                            </div>
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- Mensagem quando não há dados -->
        {% if not reactive_messages and not proactive_messages %}
        <div class="text-center text-gray-500 py-8">
            <p>Nenhuma mensagem registrada ainda</p>
        </div>
        {% endif %}
    </div>
</div>
{% endblock %}
```

---

### 2. Modificações no Backend

#### 2.1. Arquivo: `routes.py`
**Mudanças necessárias:**

1. **Renomear rota:**
   - Mudar de `/user/{user_id}/development` para `/user/{user_id}/agent-data`

2. **Criar nova função `user_agent_data_page()`:**

```python
@router.get("/user/{user_id}/agent-data", response_class=HTMLResponse)
async def user_agent_data_page(request: Request, user_id: str, username: str = Depends(verify_credentials)):
    """
    Página de Dados do Agente

    Mostra:
    - Relatório resumido (total conversas, reativas, proativas, status)
    - 10 últimas mensagens reativas (conversação normal)
    - 10 últimas mensagens proativas (sistema proativo)
    """
    db = get_db()

    # Buscar usuário
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    cursor = db.conn.cursor()

    # ============================================================
    # 1. RELATÓRIO RESUMIDO
    # ============================================================

    # Total de conversas
    cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id = ?", (user_id,))
    total_conversations = cursor.fetchone()[0]

    # Conversas reativas (todas exceto plataforma 'proactive')
    cursor.execute("""
        SELECT COUNT(*) FROM conversations
        WHERE user_id = ? AND platform != 'proactive'
    """, (user_id,))
    reactive_count = cursor.fetchone()[0]

    # Mensagens proativas (tabela proactive_approaches)
    cursor.execute("""
        SELECT COUNT(*) FROM proactive_approaches
        WHERE user_id = ? AND sent = 1
    """, (user_id,))
    proactive_count = cursor.fetchone()[0]

    # Primeira interação
    cursor.execute("""
        SELECT MIN(timestamp) FROM conversations WHERE user_id = ?
    """, (user_id,))
    first_interaction = cursor.fetchone()[0] or "N/A"

    # Última atividade
    cursor.execute("""
        SELECT MAX(timestamp) FROM conversations WHERE user_id = ?
    """, (user_id,))
    last_activity = cursor.fetchone()[0] or "N/A"

    # Status proativo (última proativa + cooldown)
    cursor.execute("""
        SELECT sent_at, cooldown_until FROM proactive_approaches
        WHERE user_id = ? AND sent = 1
        ORDER BY sent_at DESC
        LIMIT 1
    """, (user_id,))
    last_proactive = cursor.fetchone()

    if last_proactive:
        from datetime import datetime
        now = datetime.now()
        cooldown_until = datetime.fromisoformat(last_proactive['cooldown_until']) if last_proactive['cooldown_until'] else now

        if cooldown_until > now:
            hours_left = (cooldown_until - now).total_seconds() / 3600
            proactive_status = f"⏸️  Cooldown ({hours_left:.1f}h restantes)"
        else:
            proactive_status = "✅ Ativo (pode receber mensagem)"
    else:
        proactive_status = "🆕 Nunca recebeu mensagem proativa"

    # Taxa de resposta (aproximada - conversas reativas / total)
    response_rate = int((reactive_count / total_conversations * 100)) if total_conversations > 0 else 0

    summary = {
        "total_conversations": total_conversations,
        "reactive_count": reactive_count,
        "proactive_count": proactive_count,
        "first_interaction": first_interaction[:16] if first_interaction != "N/A" else "N/A",
        "last_activity": last_activity[:16] if last_activity != "N/A" else "N/A",
        "proactive_status": proactive_status,
        "response_rate": response_rate
    }

    # ============================================================
    # 2. MENSAGENS REATIVAS (últimas 10)
    # ============================================================
    cursor.execute("""
        SELECT
            user_input,
            bot_response,
            timestamp,
            keywords
        FROM conversations
        WHERE user_id = ? AND platform != 'proactive'
        ORDER BY timestamp DESC
        LIMIT 10
    """, (user_id,))

    reactive_messages = []
    for row in cursor.fetchall():
        reactive_messages.append({
            "user_input": row['user_input'],
            "bot_response": row['bot_response'],
            "timestamp": row['timestamp'][:16] if row['timestamp'] else "N/A",
            "keywords": row['keywords'].split(',') if row['keywords'] else []
        })

    # ============================================================
    # 3. MENSAGENS PROATIVAS (últimas 10)
    # ============================================================
    cursor.execute("""
        SELECT
            pa.message,
            pa.sent_at,
            pa.message_type,
            pa.archetype_pair,
            pa.topic,
            sq.target_dimension
        FROM proactive_approaches pa
        LEFT JOIN strategic_questions sq
            ON pa.user_id = sq.user_id
            AND datetime(pa.sent_at) = datetime(sq.asked_at)
        WHERE pa.user_id = ? AND pa.sent = 1
        ORDER BY pa.sent_at DESC
        LIMIT 10
    """, (user_id,))

    proactive_messages = []
    for row in cursor.fetchall():
        proactive_messages.append({
            "message": row['message'],
            "timestamp": row['sent_at'][:16] if row['sent_at'] else "N/A",
            "message_type": row['message_type'] or 'insight',
            "archetype_pair": row['archetype_pair'],
            "topic": row['topic'],
            "target_dimension": row['target_dimension']
        })

    return templates.TemplateResponse("user_agent_data.html", {
        "request": request,
        "user": user,
        "user_id": user_id,
        "summary": summary,
        "reactive_messages": reactive_messages,
        "proactive_messages": proactive_messages
    })
```

---

## 📋 Checklist de Implementação

### Quinta-feira, 04/12 (Amanhã)

**Manhã** (2-3h):
1. ⏳ Renomear template: `user_development.html` → `user_agent_data.html`
2. ⏳ Reescrever template com novo design (seções: resumo + 2 colunas)
3. ⏳ Modificar `routes.py`:
   - Renomear rota `/development` → `/agent-data`
   - Implementar `user_agent_data_page()` com queries SQL
4. ⏳ Modificar botão em `users.html`: "Desenvolvimento" → "Dados do Agente"

**Tarde** (1-2h):
5. ⏳ Testes locais (se possível) ou direto no Railway
6. ⏳ Ajustes de layout e responsividade
7. ⏳ Verificar que tabela `strategic_questions` está sendo linkada corretamente
8. ⏳ Commit e deploy no Railway

---

## 🎨 Design System

### Cores:
- **Reativas**: Azul (`bg-blue-50`, `text-blue-800`)
- **Proativas**: Roxo (`bg-purple-50`, `text-purple-800`)
- **Resumo**: Gradiente roxo-indigo (`from-purple-500 to-indigo-600`)

### Ícones:
- 💬 Reativas
- 🤖 Proativas
- 📊 Relatório
- 📅 Data
- 🎯 Tipo
- 📈 Total
- ⏰ Última atividade
- 🎭 Arquétipos

---

## 🔍 Queries SQL Necessárias

### 1. Total de conversas reativas:
```sql
SELECT COUNT(*) FROM conversations
WHERE user_id = ? AND platform != 'proactive'
```

### 2. Total de mensagens proativas enviadas:
```sql
SELECT COUNT(*) FROM proactive_approaches
WHERE user_id = ? AND sent = 1
```

### 3. Últimas 10 mensagens reativas:
```sql
SELECT user_input, bot_response, timestamp, keywords
FROM conversations
WHERE user_id = ? AND platform != 'proactive'
ORDER BY timestamp DESC
LIMIT 10
```

### 4. Últimas 10 mensagens proativas (com join para strategic_questions):
```sql
SELECT
    pa.message,
    pa.sent_at,
    pa.message_type,
    pa.archetype_pair,
    pa.topic,
    sq.target_dimension
FROM proactive_approaches pa
LEFT JOIN strategic_questions sq
    ON pa.user_id = sq.user_id
    AND datetime(pa.sent_at) = datetime(sq.asked_at)
WHERE pa.user_id = ? AND pa.sent = 1
ORDER BY pa.sent_at DESC
LIMIT 10
```

### 5. Status proativo (cooldown):
```sql
SELECT sent_at, cooldown_until
FROM proactive_approaches
WHERE user_id = ? AND sent = 1
ORDER BY sent_at DESC
LIMIT 1
```

---

## 📊 Dados Exibidos

### Relatório Resumido:
- ✅ Total de conversas
- ✅ Mensagens reativas
- ✅ Mensagens proativas
- ✅ Primeira interação
- ✅ Última atividade
- ✅ Status proativo (cooldown)
- ✅ Taxa de resposta

### Coluna Reativas (10 últimas):
- ✅ Input do usuário (truncado 100 chars)
- ✅ Resposta do bot (truncado 100 chars)
- ✅ Timestamp
- ✅ Keywords (até 3)

### Coluna Proativas (10 últimas):
- ✅ Mensagem completa
- ✅ Timestamp
- ✅ Tipo (insight vs strategic_question)
- ✅ Dimensão alvo (se pergunta estratégica)
- ✅ Par arquetípico (se insight)
- ✅ Tópico

---

## ⚠️ Considerações Importantes

### Compatibilidade:
- ✅ Tabela `strategic_questions` pode não existir ainda → LEFT JOIN
- ✅ Campo `message_type` em `proactive_approaches` pode ser NULL → fallback para "insight"

### Performance:
- ✅ Queries limitadas a 10 mensagens cada (rápido)
- ✅ Índices já existem em `user_id` e `timestamp`

### UX:
- ✅ Layout responsivo (grid 2 colunas)
- ✅ Scroll independente por coluna se necessário
- ✅ Truncamento de texto longo (100 chars)
- ✅ Hover effects para melhor interatividade

---

## 🚀 Deploy

**Processo:**
1. Commit das mudanças:
   - `user_agent_data.html` (novo)
   - `routes.py` (modificado)
   - `users.html` (modificado)
2. Push para GitHub
3. Railway faz deploy automático
4. Verificar logs
5. Testar no admin web

---

## 📝 Notas Finais

**Diferenças da página antiga:**
- ❌ Remove: Padrões comportamentais, milestones, conflitos arquetípicos
- ✅ Adiciona: Relatório resumido, histórico de mensagens reativas/proativas

**Por quê?**
- Foco em **dados operacionais** do agente (o que ele falou/recebeu)
- Menos foco em **análises psicológicas** (que já estão em outras páginas)
- **Transparência** sobre comportamento do sistema proativo

**Páginas mantidas:**
- `/admin/user/{user_id}/analysis` - Análise MBTI/Jungiana
- `/admin/user/{user_id}/psychometrics` - Análise psicométrica Big Five

---

**Status**: ⏳ AGUARDANDO APROVAÇÃO
**Estimativa**: 3-5 horas de desenvolvimento
**Prazo**: Quinta-feira, 04/12
