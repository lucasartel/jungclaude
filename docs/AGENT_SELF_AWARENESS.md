# Autoconsciência do Agente Jung — Estado Atual
**Versão:** 1.0 — 2026-02-16
**Escopo:** Diagnóstico completo + plano de ativação

---

## Visão Geral

O JungAgent possui **infraestrutura sofisticada para automodelagem**, mas toda ela
está desconectada da geração de respostas. O agente responde de uma persona estática
hardcoded (`jung_core.py` linhas 165-223) enquanto tabelas ricas de identidade dinâmica
existem no banco, são populadas a cada 6h — e nunca são lidas durante uma resposta.

---

## Sistema de Identidade (7 tabelas SQLite)

Populado pelo job de consolidação em `agent_identity_consolidation_job.py` a cada 6h,
processando apenas conversas do usuário admin (`367f9e509e396d51`).

| Tabela | Conteúdo | Exemplo |
|--------|----------|---------|
| `agent_identity_core` | Crenças nucleares sobre si mesmo | "Priorizo profundidade sobre superficialidade" |
| `agent_identity_contradictions` | Tensões internas do agente | Autoridade ↔ Humildade |
| `agent_narrative_chapters` | Arcos da evolução do agente | "Awakening", "Integration" |
| `agent_possible_selves` | Selves ideais, temidos, perdidos | Ideal: presença plena / Temido: superficialidade |
| `agent_relational_identity` | Como o agente se vê em relação ao usuário | Papel: espelho, Postura: parceiro |
| `agent_self_knowledge_meta` | Metacognição — o que sabe/não sabe | "Tenho viés para profundidade" |
| `agent_agency_memory` | Momentos de escolha autônoma | "Recusei análise superficial" |

### Pipeline de extração de identidade

```
Conversas (admin)
    → agent_identity_consolidation_job.py (a cada 6h)
    → AgentIdentityExtractor.extract_from_conversation() [usa LLM via AnthropicCompatWrapper]
    → store_extracted_identity() → grava nas 7 tabelas
    → agent_identity_extractions (registra quais conversas foram processadas)
```

### Contexto de identidade para LLM

`agent_identity_context_builder.py` já possui `build_context_summary_for_llm()` que
formata todas as tabelas em markdown estruturado para injeção no system prompt.

**LACUNA:** `_generate_response()` em `jung_core.py` NUNCA chama este método.
O agente nunca lê o que sabe sobre si mesmo ao responder.

---

## Sistema de Ruminação (5 fases)

Roda para o usuário admin apenas. O scheduler (`rumination_scheduler.py`) executa
como **processo externo** (`subprocess.Popen`) a cada 12h.

### Fases

```
Fase 1 — Ingestão (sync, após cada conversa com tensão >= 0.5)
  └─ Extrai fragmentos: valor, desejo, medo, comportamento, contradição, emoção, crença, dúvida
  └─ Salva em: rumination_fragments

Fase 2 — Detecção (após ingestão)
  └─ Detecta tensões entre fragmentos: valor↔comportamento | desejo↔medo
  └─ Salva em: rumination_tensions

Fase 3 — Digestão (a cada 12h pelo scheduler)
  └─ Revisita tensões abertas, incrementa maturity_score
  └─ Formula: 15%×tempo + 25%×evidências + 15%×revisitas + 30%×intensidade
  └─ BUG: _count_related_fragments() sempre retorna 0 → evidências travadas em 1

Fase 4 — Síntese (disparada quando maturity_score >= 0.55)
  └─ Gera monólogo interno poético em primeira pessoa
  └─ Salva em: rumination_insights (status='ready')
  └─ NUNCA DISPARA por causa do bug na Fase 3

Fase 5 — Entrega (quando usuário inativo 12h+ e cooldown 24h+)
  └─ Envia insight via Telegram bot.send_message()
  └─ NUNCA DISPARA (depende da Fase 4)
```

### Configurações (rumination_config.py)

| Parâmetro | Valor | Significado |
|-----------|-------|-------------|
| `MIN_TENSION_LEVEL` | 0.5 | Tensão mínima da conversa para ingerir |
| `MIN_EMOTIONAL_WEIGHT` | 0.3 | Peso mínimo de um fragmento |
| `MIN_MATURITY_FOR_SYNTHESIS` | 0.55 | Maturidade mínima para síntese |
| `MIN_EVIDENCE_FOR_SYNTHESIS` | 2 | Evidências mínimas |
| `DIGEST_INTERVAL_HOURS` | 12 | Frequência do scheduler |
| `INACTIVITY_THRESHOLD_HOURS` | 12 | Inatividade mínima para entrega |
| `COOLDOWN_HOURS` | 24 | Intervalo mínimo entre insights |
| `MAX_INSIGHTS_PER_WEEK` | 3 | Limite semanal |

### Bridge Identidade ↔ Ruminação

`identity_rumination_bridge.py` sincroniza bidirecionalmente a cada 6h:
- Tensões de ruminação maduras (> 0.6) → Contradições de identidade
- Contradições não resolvidas → Novas tensões de ruminação

---

## Métricas de Desenvolvimento (agent_development)

Tabela SQLite com uma linha por usuário, atualizada após cada interação.

| Métrica | Incremento por interação | Significado |
|---------|--------------------------|-------------|
| `self_awareness_score` | +0.001 | Autoconsciência |
| `moral_complexity_score` | +0.0008 | Complexidade moral |
| `emotional_depth_score` | +0.0012 | Profundidade emocional |
| `autonomy_score` | +0.0005 | Autonomia |

**Fase = min(5, floor(média × 5) + 1)** — progride automaticamente conforme scores crescem.

**LACUNA:** Scores nunca influenciam respostas. Fase nunca é mencionada pelo agente.
Crescimento é numérico mas não narrativo.

---

## Diagrama de Fluxo Completo

```
CONVERSA ATIVA
──────────────
Usuário → Telegram Bot
    ↓
jung_core._generate_response()
    ├─ [LACUNA] identity_context_builder NÃO chamado
    ├─ Usa persona ESTÁTICA hardcoded (linhas 165-223)
    ├─ Busca memórias do usuário (semantic_search)
    └─ Gera resposta via OpenRouter/GLM-5

APÓS RESPOSTA (save_conversation)
───────────────────────────────────
    ├─ SQLite + ChromaDB salvos
    ├─ _update_agent_development() → incrementa scores (+0.001)
    ├─ HOOK: Ruminação.ingest() → Fase 1
    └─ HOOK: write_session_entry() → sessions/YYYY-MM-DD.md


SCHEDULERS ASSÍNCRONOS
─────────────────────────
A cada 6h (asyncio):
    ├─ identity_consolidation_scheduler() → extrai identidade das conversas do admin
    └─ identity_rumination_sync_scheduler() → bridge bidirecional

A cada 12h (subprocess externo):
    └─ rumination_scheduler.py → Fases 3, 4, 5
           ├─ digest() → [BUG: maturity não cresce]
           ├─ check_and_synthesize() → [nunca dispara]
           └─ check_and_deliver() → [nunca dispara]

Mensal (asyncio):
    └─ consolidation_scheduler() → consolida memórias do USUÁRIO, gera profile.md


O QUE ESTÁ FALTANDO
────────────────────
❌ _generate_response() NÃO lê identity_context_builder
❌ rumination._count_related_fragments() retorna 0 (bug)
❌ agent_profile.md NÃO existe (só existe para usuários)
❌ Fase de desenvolvimento NÃO influencia comportamento
```

---

## Melhorias Implementadas / Em Andamento

### Implementadas (fev/2026)
- ✅ `user_profile_writer.py` — sessions diárias + profile.md para usuários
- ✅ `bm25_search.py` — busca híbrida BM25 + vetorial
- ✅ `memory_flush.py` — flush pré-compaction
- ✅ `AnthropicCompatWrapper` — chamadas internas redirecionadas para GLM-5 via OpenRouter

### Planejadas (este ciclo)
- 🔲 **Melhoria 1:** Conectar `AgentIdentityContextBuilder` ao `_generate_response()`
- 🔲 **Melhoria 2:** Corrigir `_count_related_fragments()` (ruminação)
- 🔲 **Melhoria 3:** Criar `data/agent/self_profile.md` + hook no job de consolidação

---

## Arquivos-Chave

| Arquivo | Função |
|---------|--------|
| `jung_core.py:165-223` | Persona estática hardcoded (system prompt) |
| `jung_core.py:1281-1294` | Hook de ingestão da ruminação após save_conversation |
| `agent_identity_context_builder.py` | Builder de contexto (EXISTE, NÃO É CHAMADO) |
| `agent_identity_extractor.py` | Extrai identidade de conversas via LLM |
| `agent_identity_consolidation_job.py` | Job a cada 6h para extrair identidade |
| `jung_rumination.py` | Engine de ruminação (5 fases) |
| `rumination_config.py` | Thresholds e configurações |
| `rumination_scheduler.py` | Subprocess externo (12h) |
| `identity_rumination_bridge.py` | Sync bidirecional (6h) |
| `identity_config.py` | Config do sistema de identidade |
| `user_profile_writer.py` | Escreve profile.md e sessions/ (apenas para usuários) |
