# 🎯 Plano de Melhorias - Jung Bot

## Status: 🔄 EM PROGRESSO

---

## 1. ✅ CRÍTICO: Isolar agent_development por Usuário

### 📋 Problema
A tabela `agent_development` é **GLOBAL** (único registro com id=1) compartilhada entre TODOS os usuários.

**Impacto:** O "estado evolutivo do agente" (autoconsciência, profundidade, autonomia) é o mesmo para todos os usuários, violando o princípio core do projeto: **cada usuário constrói seu agente único a partir da relação**.

### 🎯 Solução

#### Fase 1: Migração do Schema (BREAKING CHANGE)

**Arquivo:** `jung_core.py` - método `_create_tables()`

**Alterações:**
1. Remover constraint `CHECK (id = 1)` (que força único registro)
2. Adicionar coluna `user_id TEXT NOT NULL`
3. Adicionar `FOREIGN KEY (user_id) REFERENCES users(user_id)`
4. Criar índice único: `CREATE UNIQUE INDEX idx_agent_dev_user ON agent_development(user_id)`

**SQL de Migração:**
```sql
-- 1. Criar nova tabela com schema correto
CREATE TABLE agent_development_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    phase INTEGER DEFAULT 1,
    total_interactions INTEGER DEFAULT 0,
    self_awareness_score REAL DEFAULT 0.0,
    moral_complexity_score REAL DEFAULT 0.0,
    emotional_depth_score REAL DEFAULT 0.0,
    autonomy_score REAL DEFAULT 0.0,
    depth_level REAL DEFAULT 0.0,
    autonomy_level REAL DEFAULT 0.0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 2. Criar índice único
CREATE UNIQUE INDEX idx_agent_dev_user ON agent_development_new(user_id);

-- 3. Migrar dados existentes (copiar registro global para cada usuário)
INSERT INTO agent_development_new (user_id, phase, total_interactions, self_awareness_score,
                                    moral_complexity_score, emotional_depth_score, autonomy_score,
                                    depth_level, autonomy_level, last_updated)
SELECT u.user_id,
       COALESCE(ad.phase, 1),
       COALESCE(ad.total_interactions, 0),
       COALESCE(ad.self_awareness_score, 0.0),
       COALESCE(ad.moral_complexity_score, 0.0),
       COALESCE(ad.emotional_depth_score, 0.0),
       COALESCE(ad.autonomy_score, 0.0),
       COALESCE(ad.depth_level, 0.0),
       COALESCE(ad.autonomy_level, 0.0),
       COALESCE(ad.last_updated, CURRENT_TIMESTAMP)
FROM users u
LEFT JOIN agent_development ad ON ad.id = 1;

-- 4. Dropar tabela antiga e renomear
DROP TABLE agent_development;
ALTER TABLE agent_development_new RENAME TO agent_development;
```

#### Fase 2: Atualizar Queries

**Buscar todas as referências:**
```bash
grep -n "agent_development" jung_core.py
```

**Queries que precisam de filtro `WHERE user_id = ?`:**

1. **get_agent_state()** - linha ~750
2. **update_agent_development()** - linha ~800
3. **_calculate_agent_scores()** - linha ~850
4. Qualquer SELECT/UPDATE/INSERT na tabela

**Exemplo de correção:**
```python
# ANTES (global)
cursor.execute("""
    SELECT * FROM agent_development WHERE id = 1
""")

# DEPOIS (por usuário)
cursor.execute("""
    SELECT * FROM agent_development WHERE user_id = ?
""", (user_id,))
```

#### Fase 3: Criar/Inicializar Estado por Usuário

Adicionar método `_ensure_agent_state(user_id)`:

```python
def _ensure_agent_state(self, user_id: str):
    """Garante que usuário tem registro de agent_development"""
    cursor = self.conn.cursor()

    cursor.execute("""
        SELECT id FROM agent_development WHERE user_id = ?
    """, (user_id,))

    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO agent_development (user_id)
            VALUES (?)
        """, (user_id,))
        self.conn.commit()
        logger.info(f"✅ Agent state inicializado para user_id={user_id}")
```

Chamar este método em `process_message()` antes de qualquer operação.

#### Fase 4: Testes

**Script de teste:**
```python
def test_agent_isolation():
    db = HybridDatabaseManager()

    # Criar dois usuários
    db.save_user("user1", "Alice", "telegram")
    db.save_user("user2", "Bob", "telegram")

    # Atualizar desenvolvimento de Alice
    db.update_agent_development("user1", self_awareness_score=0.8)

    # Atualizar desenvolvimento de Bob
    db.update_agent_development("user2", self_awareness_score=0.3)

    # Verificar isolamento
    state_alice = db.get_agent_state("user1")
    state_bob = db.get_agent_state("user2")

    assert state_alice['self_awareness_score'] == 0.8
    assert state_bob['self_awareness_score'] == 0.3

    print("✅ Isolamento de agent_development funcionando!")
```

### ⚠️ Riscos
- **Breaking change**: Banco existente precisa de migração
- **Dados do Railway**: Criar backup antes de migrar

### 📦 Arquivos Afetados
- `jung_core.py` (schema + queries)
- Possivelmente `telegram_bot.py` (se usar agent_state)

---

## 2. 🔍 Investigar Proatividade Não Funcionando

### 📋 Problema
Sistema de mensagens proativas implementado mas não está enviando mensagens.

### 🔍 Investigação

#### Passo 1: Verificar Logs no Railway

Procurar por:
```
✅ Scheduler de mensagens proativas ativado!
🔍 [PROATIVO] Verificando usuários elegíveis...
✅ [PROATIVO] Mensagem enviada para...
```

Se não aparecer → Scheduler não está rodando.

#### Passo 2: Verificar main.py

**Linha 74:**
```python
proactive_task = asyncio.create_task(proactive_message_scheduler(telegram_app))
```

**Problema possível:** Task pode estar sendo cancelada ou não iniciada.

#### Passo 3: Verificar Condições de Envio

**Arquivo:** `jung_proactive.py`

Método `check_and_generate_advanced_message()` tem várias condições:

1. ✅ **Cooldown de 6h:** Usuário não pode ter recebido mensagem proativa há menos de 6h
2. ✅ **Inatividade de 3h:** Usuário precisa estar inativo há 3h
3. ✅ **Mínimo de conversas:** Pode ter requisito mínimo de conversas

**Teste Manual:**
```python
# Adicionar log temporário
logger.info(f"[PROATIVO DEBUG] user_id={user_id}")
logger.info(f"  - Última msg proativa: {last_proactive}")
logger.info(f"  - Última interação: {last_interaction}")
logger.info(f"  - Cooldown ok? {cooldown_ok}")
logger.info(f"  - Inativo? {is_inactive}")
```

#### Passo 4: Verificar Banco de Dados

**Tabela:** `proactive_messages`

Verificar se há registros sendo salvos:
```sql
SELECT * FROM proactive_messages ORDER BY sent_at DESC LIMIT 10;
```

Se vazio → Mensagens nunca foram geradas.

### 🎯 Possíveis Soluções

1. **Reduzir cooldown temporariamente** (de 6h para 30min) para testar
2. **Reduzir inatividade** (de 3h para 5min) para testar
3. **Adicionar logs detalhados** em cada etapa do check
4. **Verificar se AsyncIO loop está rodando** (Railway pode ter issue)

### 📦 Arquivos Afetados
- `main.py` (scheduler)
- `jung_proactive.py` (lógica de proatividade)
- `telegram_bot.py` (integração)

---

## 3. 🗑️ Remover Comandos Antigos do Bot Telegram

### 📋 Problema
Comandos antigos ainda aparecem no menu do Telegram para os usuários.

### 🔍 Investigação

#### Passo 1: Listar Comandos Atuais Registrados

**Arquivo:** `telegram_bot.py`

Buscar por `add_handler`:
```bash
grep -n "add_handler" telegram_bot.py
```

**Comandos atualmente registrados:**
- `/start`
- `/help`
- `/stats`
- `/mbti`
- `/desenvolvimento`
- `/reset`

#### Passo 2: Verificar Comandos Públicos (BotFather)

Comandos que aparecem no Telegram são definidos via **BotFather** ou via API.

**Checar comandos via API:**
```python
from telegram import Bot

bot = Bot(token="SEU_TOKEN")
commands = await bot.get_my_commands()
for cmd in commands:
    print(f"/{cmd.command} - {cmd.description}")
```

#### Passo 3: Limpar Comandos Antigos

**Opção 1: Via BotFather (Manual)**
1. Abrir [@BotFather](https://t.me/botfather)
2. `/mybots`
3. Selecionar seu bot
4. `Edit Bot` → `Edit Commands`
5. Enviar lista atualizada:

```
start - Iniciar conversa com Jung
help - Ver comandos disponíveis
stats - Ver estatísticas do agente
mbti - Ver análise MBTI
desenvolvimento - Ver estado de desenvolvimento
reset - Resetar conversa
```

**Opção 2: Via Código (Automático)**

Adicionar em `main.py` no startup:

```python
async def setup_bot_commands(app):
    """Configura comandos do bot no Telegram"""
    commands = [
        ("start", "Iniciar conversa com Jung"),
        ("help", "Ver comandos disponíveis"),
        ("stats", "Ver estatísticas do agente"),
        ("mbti", "Ver análise MBTI"),
        ("desenvolvimento", "Ver estado de desenvolvimento"),
        ("reset", "Resetar conversa"),
    ]

    await app.bot.set_my_commands(commands)
    logger.info(f"✅ {len(commands)} comandos configurados no Telegram")

# Chamar no lifespan após bot.start()
await setup_bot_commands(telegram_app)
```

### 🎯 Solução Recomendada
Implementar **Opção 2** (via código) para garantir que comandos sempre estejam sincronizados.

### 📦 Arquivos Afetados
- `main.py` (adicionar setup de comandos)

---

## 4. 🔄 Sistema de Alternância Fácil entre Grok e Claude

### 📋 Objetivo
Permitir alternar facilmente entre Grok (atual) e Claude Sonnet 3.5 (mais barato e melhor em seguir instruções complexas) via variável de ambiente.

### 🎯 Solução: LLM Provider Abstraction

#### Fase 1: Criar Classe Abstrata de Provider

**Novo arquivo:** `llm_provider.py`

```python
from abc import ABC, abstractmethod
from typing import List, Dict
import os
from openai import OpenAI
from anthropic import Anthropic

class LLMProvider(ABC):
    """Interface abstrata para provedores de LLM"""

    @abstractmethod
    def chat_completion(self, messages: List[Dict], temperature: float = 0.7,
                       max_tokens: int = 1500) -> str:
        """Gera resposta do LLM"""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Retorna nome do modelo"""
        pass

    @abstractmethod
    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        """Retorna custo por 1k tokens (input/output)"""
        pass


class GrokProvider(LLMProvider):
    """Provedor Grok (xAI)"""

    def __init__(self, model: str = "grok-beta"):
        self.client = OpenAI(
            api_key=os.getenv("XAI_API_KEY"),
            base_url="https://api.x.ai/v1"
        )
        self.model = model

    def chat_completion(self, messages: List[Dict], temperature: float = 0.7,
                       max_tokens: int = 1500) -> str:
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return completion.choices[0].message.content

    def get_model_name(self) -> str:
        return f"Grok ({self.model})"

    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        # Grok Beta: $5/M tokens input, $15/M tokens output
        return {"input": 0.005, "output": 0.015}


class ClaudeProvider(LLMProvider):
    """Provedor Claude (Anthropic)"""

    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model

    def chat_completion(self, messages: List[Dict], temperature: float = 0.7,
                       max_tokens: int = 1500) -> str:
        # Converter formato OpenAI para Anthropic
        system_msg = None
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_msg,
            messages=anthropic_messages
        )

        return response.content[0].text

    def get_model_name(self) -> str:
        return f"Claude ({self.model})"

    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        # Claude 3.5 Sonnet: $3/M tokens input, $15/M tokens output
        return {"input": 0.003, "output": 0.015}


class LLMFactory:
    """Factory para criar provider correto"""

    @staticmethod
    def create_provider(provider_name: str = None) -> LLMProvider:
        """
        Cria provider baseado em variável de ambiente ou parâmetro

        Args:
            provider_name: "grok", "claude", ou None (usa env LLM_PROVIDER)
        """
        if provider_name is None:
            provider_name = os.getenv("LLM_PROVIDER", "grok").lower()

        providers = {
            "grok": GrokProvider,
            "claude": ClaudeProvider,
        }

        if provider_name not in providers:
            raise ValueError(f"Provider '{provider_name}' não suportado. Use: {list(providers.keys())}")

        provider_class = providers[provider_name]
        provider = provider_class()

        print(f"✅ LLM Provider: {provider.get_model_name()}")
        print(f"   Custo: ${provider.get_cost_per_1k_tokens()['input']}/1k input, "
              f"${provider.get_cost_per_1k_tokens()['output']}/1k output")

        return provider
```

#### Fase 2: Integrar em jung_core.py

**Substituir:**
```python
# ANTES
self.xai_client = OpenAI(...)
self.openai_client = OpenAI(...)

# DEPOIS
from llm_provider import LLMFactory
self.llm_provider = LLMFactory.create_provider()
```

**Atualizar métodos que chamam LLM:**
```python
# ANTES
if model.startswith("grok"):
    completion = self.xai_client.chat.completions.create(...)
else:
    completion = self.openai_client.chat.completions.create(...)

# DEPOIS
response = self.llm_provider.chat_completion(
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,
    max_tokens=1500
)
```

#### Fase 3: Configuração no .env

Adicionar variável:
```bash
# LLM Provider (grok ou claude)
LLM_PROVIDER=grok

# API Keys
XAI_API_KEY=xai-...
ANTHROPIC_API_KEY=sk-ant-...
```

#### Fase 4: Adicionar Claude SDK

**requirements.txt:**
```
anthropic==0.39.0
```

**Instalar:**
```bash
pip install anthropic
```

### 🎯 Como Usar

**Alternar para Claude:**
1. Adicionar `ANTHROPIC_API_KEY` no `.env` do Railway
2. Mudar `LLM_PROVIDER=claude`
3. Redeploy

**Alternar para Grok:**
1. Mudar `LLM_PROVIDER=grok`
2. Redeploy

### 💰 Comparação de Custos

| Modelo | Input ($/1M tokens) | Output ($/1M tokens) | Melhor Para |
|--------|---------------------|----------------------|-------------|
| **Grok Beta** | $5 | $15 | Raciocínio rápido, low-latency |
| **Claude 3.5 Sonnet** | $3 | $15 | Instruções complexas, profundidade psicológica |

**Economia com Claude:** ~40% mais barato no input, mesmo preço no output.

### 📦 Arquivos Afetados
- `llm_provider.py` (NOVO)
- `jung_core.py` (integração)
- `requirements.txt` (adicionar anthropic)
- `.env` (adicionar ANTHROPIC_API_KEY e LLM_PROVIDER)

---

## 🎯 Ordem de Implementação Recomendada

1. **PRIMEIRO:** Isolar agent_development (CRÍTICO - core do projeto)
2. **SEGUNDO:** Sistema Grok/Claude (habilita testes com Claude)
3. **TERCEIRO:** Remover comandos antigos (quick win)
4. **QUARTO:** Investigar proatividade (pode precisar de debug longo)

---

## 📊 Checklist de Progresso

- [ ] 1.1 - Criar SQL de migração de agent_development
- [ ] 1.2 - Atualizar schema em _create_tables()
- [ ] 1.3 - Atualizar todas as queries (get_agent_state, update_agent_development)
- [ ] 1.4 - Adicionar _ensure_agent_state()
- [ ] 1.5 - Testar isolamento em dev
- [ ] 1.6 - Backup do Railway
- [ ] 1.7 - Deploy e migração no Railway
- [ ] 1.8 - Teste final de isolamento

- [ ] 2.1 - Verificar logs de proatividade no Railway
- [ ] 2.2 - Adicionar logs detalhados de debug
- [ ] 2.3 - Verificar condições de cooldown/inatividade
- [ ] 2.4 - Testar com cooldown reduzido
- [ ] 2.5 - Fix e redeploy

- [ ] 3.1 - Listar comandos atuais via API
- [ ] 3.2 - Criar setup_bot_commands() em main.py
- [ ] 3.3 - Deploy e verificar comandos no Telegram

- [ ] 4.1 - Criar llm_provider.py com abstração
- [ ] 4.2 - Implementar GrokProvider
- [ ] 4.3 - Implementar ClaudeProvider
- [ ] 4.4 - Criar LLMFactory
- [ ] 4.5 - Integrar em jung_core.py
- [ ] 4.6 - Adicionar anthropic no requirements.txt
- [ ] 4.7 - Testar localmente com Claude
- [ ] 4.8 - Deploy com Grok (default)
- [ ] 4.9 - Teste A/B: alternar para Claude e comparar

---

## 📝 Notas

- **Backup antes de tudo:** Criar backup do banco Railway antes da migração
- **Testes locais primeiro:** Testar todas as mudanças localmente antes de deploy
- **Deploy incremental:** Fazer um deploy por vez, testar, depois próximo
- **Monitorar custos:** Após migrar para Claude, monitorar custos no dashboard Anthropic

---

**Última atualização:** 2025-11-26
**Status:** Aguardando aprovação para início da implementação
