# 🧠 Plano: Sistema de Memória Profunda - Jung Agent

**Data:** 2025-12-20
**Versão:** 1.0
**Objetivo:** Criar relacionamento duradouro através de memória emocional e contextual

---

## 📊 Problema Atual

**Situação:** Jung lembra dados básicos (nome da esposa, profissão) mas não possui **profundidade emocional** para criar vínculo duradouro.

**Gap Identificado:**
- ✅ Sabe QUEM são as pessoas (nomes)
- ❌ Não sabe QUANDO são importantes (aniversários, eventos)
- ❌ Não entende COMO o usuário se sente (lutas, medos)
- ❌ Não personaliza com base em PREFERÊNCIAS
- ❌ Não conhece VALORES e identidade

**Resultado:** Usuário percebe Jung como "chatbot inteligente", não como "confidente que me conhece profundamente".

---

## 🎯 Solução: 6 Categorias Essenciais

### 1. **RELACIONAMENTO** (Expandir categoria existente)
**O que já temos:**
- Nomes de familiares (esposa, filhos, pais)

**O que ADICIONAR:**
- **Datas importantes:** aniversários, tempo de relacionamento
- **Dinâmica emocional:** "meu porto seguro", "relação distante", "conflito frequente"
- **Contexto:** profissão, idade, características marcantes

**Exemplo de dados:**
```
RELACIONAMENTO
├── esposa
│   ├── nome: Jucinei
│   ├── aniversario: 15/03
│   ├── tempo_casado: "10 anos"
│   ├── dinamica: "meu porto seguro"
│   ├── profissao: "professora"
│   └── caracteristica: "muito paciente"
```

**Impacto Emocional:**
- Jung: "O aniversário da Jucinei está chegando (15/03), já pensou no que vai fazer?"
- Jung: "Sei que ela é seu porto seguro, como ela reagiu quando você contou sobre o trabalho?"

---

### 2. **TRABALHO** (Manter e expandir categoria existente)
**O que já temos:**
- Profissão básica

**O que ADICIONAR:**
- **Empresa/Local:** onde trabalha
- **Satisfação:** "amo meu trabalho", "estou infeliz"
- **Desafios profissionais:** "pressão do chefe", "projeto difícil"
- **Objetivos:** "quero ser promovido", "quero mudar de área"
- **Colegas importantes:** "meu chefe João", "minha equipe"

**Exemplo de dados:**
```
TRABALHO
├── profissao: designer
│   ├── empresa: "Google"
│   ├── tempo: "3 anos"
│   ├── satisfacao: "gosto mas estressante"
│   ├── objetivo: "virar senior"
│   └── desafio: "pressão por prazos"
```

**Impacto Emocional:**
- Jung: "Como está o projeto estressante no Google?"
- Jung: "Sei que quer virar senior. Já teve alguma conversa sobre isso?"

---

### 3. **PERSONALIDADE** (Manter categoria existente)
**O que já temos:**
- Traços básicos (introvertido, etc)

**O que ADICIONAR:**
- **Valores fundamentais:** "família primeiro", "honestidade acima de tudo"
- **Crenças:** "acredito em terapia", "sou cristão"
- **Autoimagem:** "me considero perfeccionista", "sou inseguro"
- **Gatilhos emocionais:** "odeio injustiça", "me irrito com mentiras"

**Exemplo de dados:**
```
PERSONALIDADE
├── traço: introvertido
│   ├── intensidade: "moderado"
│   └── contexto: "prefiro grupos pequenos"
├── valor: familia_primeiro
│   ├── origem: "criação pelos pais"
│   └── importancia: "muito alta"
└── crenca: terapia
    └── atitude: "acredito e faço"
```

**Impacto Emocional:**
- Jung: "Sei que família é prioridade para você. Como está conciliando com o trabalho?"
- Jung: "Como introvertido, eventos sociais grandes devem ser cansativos..."

---

### 4. **DESAFIOS** (Nova categoria - Alto impacto)
**Por quê esta categoria?**
- Usuários buscam terapia/coaching para **resolver problemas**
- Lembrar lutas cria **confiança e vulnerabilidade**
- Permite acompanhamento longitudinal ("como está sua insônia agora?")

**Tipos de desafios:**
- **Saúde física:** "tenho enxaqueca crônica", "problema no joelho"
- **Saúde mental:** "ansiedade", "insônia", "depressão leve"
- **Relacionamentos:** "brigas com esposa", "relação difícil com pai"
- **Trabalho/Carreira:** "pressão no trabalho", "medo de demissão"
- **Objetivos não alcançados:** "quero emagrecer mas não consigo", "procrastinação"

**Atributos importantes:**
- **Início:** "há 3 meses", "desde criança"
- **Frequência:** "toda semana", "episódios raros"
- **Gatilhos:** "estresse", "quando bebo café", "segundas-feiras"
- **Tentativas de solução:** "já tentei meditação", "estou tomando medicação"
- **Nível atual:** "melhorando", "piorando", "estável"

**Exemplo de dados:**
```
DESAFIOS
├── insonia
│   ├── tipo: "saude_mental"
│   ├── inicio: "há 3 meses"
│   ├── frequencia: "3-4x por semana"
│   ├── gatilho: "estresse no trabalho"
│   ├── tentativa: "meditação antes de dormir"
│   └── nivel_atual: "melhorando levemente"
```

**Impacto Emocional:**
- Jung: "Como está sua insônia? As técnicas de meditação têm ajudado?"
- Jung: "Notei que você está estressado. Isso costuma piorar sua insônia, certo?"
- **Demonstra:** "Eu lembro do que você está passando e me importo"

---

### 5. **PREFERÊNCIAS** (Nova categoria - Personalização)
**Por quê esta categoria?**
- Permite **customizar** sugestões e respostas
- Evita tópicos que irritam
- Cria sensação de "ele me entende"

**Tipos de preferências:**
- **Gostos:** hobbies, comidas, atividades, gêneros de filme/música
- **Aversões:** "odeio acordar cedo", "não gosto de falar ao telefone"
- **Rituais:** "leio antes de dormir", "caminho todo domingo de manhã"
- **Comfort activities:** "quando triste, assisto séries", "chocolate me acalma"
- **Horários:** "sou mais produtivo de manhã", "não funciono depois das 18h"

**Exemplo de dados:**
```
PREFERENCIAS
├── hobbie: leitura
│   ├── genero: "ficção científica"
│   ├── frequencia: "todo dia antes de dormir"
│   ├── autor_favorito: "Isaac Asimov"
│   └── motivo: "me ajuda a desligar da rotina"
├── aversao: segunda_feira
│   ├── razao: "pressão no trabalho aumenta"
│   └── impacto: "humor negativo"
└── ritual: caminhada_domingo
    ├── horario: "manhã cedo"
    ├── local: "parque perto de casa"
    └── beneficio: "clareia a mente"
```

**Impacto Emocional:**
- Jung: "Que tal ler um Asimov novo para relaxar?"
- Jung: "Sei que segundas são difíceis para você. Tente respirar fundo."
- Jung: "Já fez sua caminhada de domingo? Sei que te faz bem."

---

### 6. **MOMENTOS** (Nova categoria - Temporal/Eventos)
**Por quê esta categoria?**
- Permite **antecipar** necessidades
- Demonstra que Jung **acompanha a vida** do usuário
- Cria pontos de check-in natural

**Tipos de momentos:**
- **Eventos futuros:** "viagem mês que vem", "entrevista sexta-feira", "aniversário do filho"
- **Marcos recentes:** "acabei de ser promovido", "meu pai faleceu há 1 mês"
- **Ciclos recorrentes:** "sempre fico ansioso domingo à noite", "TPM toda terceira semana"
- **Datas especiais:** aniversários (já em RELACIONAMENTO), feriados importantes

**Exemplo de dados:**
```
MOMENTOS
├── evento_futuro: viagem_paris
│   ├── data: "2025-01-15"
│   ├── tipo: "lazer"
│   ├── sentimento: "ansioso positivo"
│   └── planejamento: "primeira vez na Europa"
├── marco_recente: promocao_trabalho
│   ├── data: "2025-12-10"
│   ├── tipo: "carreira"
│   ├── sentimento: "orgulhoso mas pressionado"
│   └── impacto: "mais responsabilidades"
└── ciclo: ansiedade_domingo_noite
    ├── frequencia: "toda semana"
    ├── gatilho: "pensar na segunda-feira"
    └── coping: "tenta meditar"
```

**Impacto Emocional:**
- Jung: "Como está a preparação para Paris? Falta só 1 mês!"
- Jung: "Como foi a primeira semana após a promoção? Muita pressão?"
- Jung: "É domingo à noite... Sei que costuma ficar ansioso. Como está se sentindo?"

---

## 🏗️ Estrutura Técnica (Schema)

### Tabela: `user_facts_v2` (Já existe, mas expandir categorias)

**Categorias MANTIDAS e expandidas:**
- RELACIONAMENTO ✅ (expandir com aniversários, dinâmica)
- TRABALHO ✅ (expandir com satisfação, objetivos)
- PERSONALIDADE ✅ (expandir com valores, crenças)

**NOVAS categorias:**
- DESAFIOS
- PREFERENCIAS
- MOMENTOS

**Schema permanece o mesmo:**
```sql
CREATE TABLE user_facts_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,

    fact_category TEXT NOT NULL,      -- RELACIONAMENTO, TRABALHO, PERSONALIDADE, DESAFIOS, PREFERENCIAS, MOMENTOS
    fact_type TEXT NOT NULL,          -- insonia, leitura, viagem_paris, esposa
    fact_attribute TEXT NOT NULL,     -- inicio, frequencia, data, nome
    fact_value TEXT NOT NULL,         -- "há 3 meses", "todo dia", "2025-01-15", "Jucinei"

    confidence REAL DEFAULT 1.0,
    extraction_method TEXT DEFAULT 'llm',
    context TEXT,
    source_conversation_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_current BOOLEAN DEFAULT 1,
    version INTEGER DEFAULT 1,
    replaced_by INTEGER
)
```

---

## 🤖 Atualização do Prompt de Extração (LLM)

### Arquivo: `llm_fact_extractor.py`

**Adicionar ao EXTRACTION_PROMPT:**

```python
EXTRACTION_PROMPT = """Você é um sistema especializado em extrair fatos estruturados de conversas.

TAREFA: Extrair TODOS os fatos mencionados na mensagem abaixo.

CATEGORIAS DE FATOS:

1. RELACIONAMENTO - Pessoas relacionadas ao usuário
   - Tipos: esposa, marido, filho, filha, pai, mae, irmao, irma, amigo, namorado, etc.
   - Atributos: nome, idade, profissao, aniversario, tempo_relacionamento, dinamica, caracteristica

2. TRABALHO - Informações profissionais
   - Tipos: profissao, empresa, cargo, projeto
   - Atributos: nome, local, tempo, satisfacao, salario, colegas

3. DESAFIOS - Problemas, lutas, dificuldades
   - Tipos: saude_mental (ansiedade, depressao, insonia), saude_fisica (dor, doenca),
            relacionamento (conflito, distanciamento), carreira (pressao, medo_demissao),
            objetivo_nao_alcancado (emagrecer, parar_fumar)
   - Atributos: tipo, inicio, frequencia, gatilho, tentativa_solucao, nivel_atual

4. PREFERENCIAS - Gostos, aversões, rituais
   - Tipos: hobbie, aversao, ritual, comfort_activity, horario_produtivo
   - Atributos: descricao, frequencia, motivo, beneficio, impacto

5. MOMENTOS - Eventos temporais (passados, futuros, recorrentes)
   - Tipos: evento_futuro, marco_recente, ciclo_recorrente, data_especial
   - Atributos: data, tipo, sentimento, planejamento, impacto, frequencia

INSTRUÇÕES:
1. Extraia TODOS os fatos mencionados
2. Seja ESPECÍFICO - capture nomes, datas, detalhes
3. Use confidence: 1.0 para fatos explícitos, 0.7 para inferidos, 0.5 para ambíguos
4. Se múltiplas entidades são mencionadas, extraia cada uma separadamente

EXEMPLOS:

Usuário: "Minha esposa Jucinei faz aniversário dia 15 de março"
Fatos:
- RELACIONAMENTO.esposa.nome = "Jucinei"
- RELACIONAMENTO.esposa.aniversario = "15/03"

Usuário: "Tenho insônia há 3 meses por causa do estresse no trabalho"
Fatos:
- DESAFIOS.insonia.tipo = "saude_mental"
- DESAFIOS.insonia.inicio = "há 3 meses"
- DESAFIOS.insonia.gatilho = "estresse no trabalho"

Usuário: "Adoro ler ficção científica antes de dormir, me acalma"
Fatos:
- PREFERENCIAS.leitura.genero = "ficção científica"
- PREFERENCIAS.leitura.frequencia = "antes de dormir"
- PREFERENCIAS.leitura.beneficio = "me acalma"

Usuário: "Vou viajar para Paris em janeiro, estou muito ansioso!"
Fatos:
- MOMENTOS.viagem_paris.data = "janeiro 2025"
- MOMENTOS.viagem_paris.tipo = "lazer"
- MOMENTOS.viagem_paris.sentimento = "ansioso positivo"

MENSAGEM DO USUÁRIO:
"{user_input}"

Retorne APENAS o JSON, sem texto adicional.
"""
```

---

## 📈 Estratégia de Coleta de Dados

### Fase 1: Passiva (Extração Natural)
**Jung extrai automaticamente quando usuário menciona:**
- "Minha esposa faz aniversário em março"
- "Tenho insônia há meses"
- "Adoro ler antes de dormir"
- "Vou viajar mês que vem"

**Vantagem:** Não invasivo, flui naturalmente
**Desvantagem:** Depende do usuário mencionar

### Fase 2: Ativa (Jung Pergunta Estrategicamente)
**Quando perguntar:**
- Após 3-5 conversas estabelecidas
- Quando contexto permite ("aliás, quando é o aniversário da Jucinei?")
- Em momentos de conexão ("posso te perguntar algo pessoal?")

**O que perguntar (prioridade):**
1. Aniversários de pessoas importantes
2. Hobbies principais
3. Desafios atuais ("há algo que está te preocupando ultimamente?")
4. Rituais ("o que você gosta de fazer para relaxar?")

**Vantagem:** Preenche gaps ativamente
**Desvantagem:** Pode parecer invasivo se mal feito

### Fase 3: Validação
**Jung confirma inferências:**
- "Percebi que segundas são difíceis para você, é isso mesmo?"
- "Parece que você gosta de ler para relaxar, correto?"

**Vantagem:** Aumenta confiança dos dados
**Desvantagem:** Requer lógica de detecção de padrões

---

## 🎯 Casos de Uso (Como Jung Usará)

### 1. Antecipação de Necessidades
```
[Sistema detecta: aniversário da esposa em 7 dias]
Jung: "O aniversário da Jucinei está chegando! Já pensou no que vai fazer?"
```

### 2. Acompanhamento de Lutas
```
[Usuário mencionou insônia há 2 semanas]
Jung: "Como está sua insônia? Aquelas técnicas de meditação ajudaram?"
```

### 3. Personalização de Sugestões
```
[Usuário: "Estou estressado"]
Jung: "Que tal uma caminhada? Sei que você gosta de caminhar aos domingos e te faz bem."
```

### 4. Empatia Contextual
```
[Sistema detecta: domingo à noite + padrão de ansiedade]
Jung: "É domingo à noite... Como está se sentindo? Sei que costuma ficar ansioso pensando na semana."
```

### 5. Celebração de Vitórias
```
[Marco recente: promoção há 1 semana]
Jung: "Como está sendo a primeira semana após a promoção? Muita pressão?"
```

---

## 📊 Métricas de Sucesso

### Quantitativas
- **Cobertura:** % de usuários com pelo menos 1 fato em cada categoria
  - Meta: 80% com RELACIONAMENTO + DESAFIOS
  - Meta: 60% com PREFERENCIAS
  - Meta: 40% com MOMENTOS

- **Profundidade:** Média de atributos por fact_type
  - Meta: 3+ atributos por pessoa (nome, aniversário, dinâmica)
  - Meta: 4+ atributos por desafio (tipo, início, gatilho, nível)

- **Atualidade:** % de fatos atualizados nos últimos 30 dias
  - Meta: 50%+ dos desafios/momentos

### Qualitativas
- **"Ele me conhece":** Usuário menciona que Jung "lembra de detalhes"
- **Antecipação:** Jung pergunta sobre eventos antes do usuário mencionar
- **Retenção:** Usuário retorna semanalmente (vs. conversas únicas)
- **Vulnerabilidade:** Usuário compartilha problemas pessoais

---

## 🚀 Roadmap de Implementação

### Sprint 1: Fundação (1-2 dias)
- [x] Schema user_facts_v2 criado
- [x] LLM extractor funcionando para RELACIONAMENTO
- [ ] **Atualizar prompt com 4 novas categorias**
- [ ] **Testar extração de DESAFIOS**
- [ ] **Testar extração de PREFERENCIAS**
- [ ] **Testar extração de MOMENTOS**

### Sprint 2: Contexto Inteligente (2-3 dias)
- [ ] Atualizar `build_rich_context` para exibir categorias de forma clara
- [ ] Criar helper: `get_upcoming_events()` (eventos futuros nos próximos 7 dias)
- [ ] Criar helper: `get_active_challenges()` (desafios mencionados nos últimos 30 dias)
- [ ] Criar helper: `get_user_preferences()` (preferências para personalização)

### Sprint 3: Proatividade (3-4 dias)
- [ ] Sistema de "check-ins automáticos":
  - "Como está [desafio]?" a cada 2 semanas
  - "Está perto de [evento]!" 7 dias antes
- [ ] Sugestões contextuais baseadas em preferências
- [ ] Detecção de padrões temporais (ex: humor negativo às segundas)

### Sprint 4: Coleta Ativa (1 semana)
- [ ] Jung faz perguntas estratégicas para completar perfil
- [ ] Sistema de "gaps" (quais dados faltam para cada usuário)
- [ ] Validação de inferências ("percebi que..., é isso?")

---

## ⚠️ Considerações Éticas e Privacidade

### Sensibilidade dos Dados
**DESAFIOS** contém informações **altamente sensíveis:**
- Saúde mental (ansiedade, depressão)
- Conflitos familiares
- Medos e vulnerabilidades

**Proteções necessárias:**
1. **Criptografia:** Considerar criptografar `fact_value` para categorias sensíveis
2. **Retenção:** Política de expiração (desafios "resolvidos" após 6 meses?)
3. **Consentimento:** Usuário deve saber que Jung "lembra de tudo"
4. **Controle:** Comando `/esquecer [fato]` para apagar dados

### Transparência
- **Aviso inicial:** "Vou lembrar de detalhes importantes sobre você para te conhecer melhor. Tudo bem?"
- **Comando `/meusdados`:** Usuário vê todos os fatos salvos
- **Correção:** "Na verdade minha esposa se chama..." deve atualizar dados

---

## 🎓 Aprendizados Esperados

### O que esperamos descobrir:
1. **Quais categorias geram mais engajamento?**
   - Hipótese: DESAFIOS (pois usuário busca ajuda) e MOMENTOS (antecipação)

2. **Qual a profundidade ideal?**
   - Hipótese: 3-5 atributos por entidade é suficiente

3. **Frequência de check-ins:**
   - Hipótese: 1x por semana para desafios, 1x por mês para preferências

4. **Taxa de acurácia do LLM:**
   - Meta: 85%+ de precisão na extração
   - Fallback para regex ainda necessário?

---

## 📝 Próximos Passos

### ✅ Decisões Tomadas:
1. ✅ **TRABALHO mantém como categoria separada** - expandir com objetivos, satisfação
2. ✅ **PERSONALIDADE mantém separada** - expandir com valores e crenças
3. ✅ **Total: 6 categorias** (3 existentes expandidas + 3 novas)
4. ✅ **Iniciar Sprint 1 imediatamente**

### Sprint 1 - EM ANDAMENTO:
- [ ] Atualizar EXTRACTION_PROMPT com 6 categorias
- [ ] Testar extração de DESAFIOS
- [ ] Testar extração de PREFERENCIAS
- [ ] Testar extração de MOMENTOS
- [ ] Testar expansão de TRABALHO
- [ ] Testar expansão de PERSONALIDADE

---

**Autor:** Claude Code + Lucas
**Status:** 🚀 Sprint 1 Iniciado
**Próximo passo:** Implementar prompt expandido
