# 📊 Jung Claude - Painel Administrativo

Documentação completa do painel administrativo web para monitoramento e análise de usuários do Jung Claude Bot.

---

## 📑 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Autenticação](#autenticação)
4. [Páginas e Funcionalidades](#páginas-e-funcionalidades)
5. [Análises Psicométricas (RH)](#análises-psicométricas-rh)
6. [Guia de Uso](#guia-de-uso)
7. [API Endpoints](#api-endpoints)
8. [Tecnologias](#tecnologias)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O painel administrativo do Jung Claude é uma interface web completa para:

- **Monitorar** todos os usuários do bot Telegram
- **Analisar** padrões comportamentais e psicológicos
- **Gerar** relatórios MBTI e psicométricos avançados
- **Acompanhar** o desenvolvimento psicológico de cada usuário
- **Visualizar** conflitos arquetípicos e milestones
- **Fornecer** insights para RH e gestão de pessoas

### Acesso

**URL:** `https://seu-app.railway.app/admin`

**Credenciais padrão:**
- Usuário: `admin`
- Senha: `admin`

> ⚠️ **Produção:** Configure variáveis de ambiente `ADMIN_USER` e `ADMIN_PASSWORD`

---

## 🏗️ Arquitetura

### Stack Tecnológico

```
FastAPI (Backend API)
├── Jinja2 (Template Engine)
├── TailwindCSS (UI Framework)
├── HTMX (Interatividade assíncrona)
├── Chart.js (Visualizações de dados)
└── Jung Core (Engine psicológico)
```

### Estrutura de Arquivos

```
admin_web/
├── routes.py                 # Rotas FastAPI e lógica de negócio
├── templates/
│   ├── base.html            # Template base com navbar e imports
│   ├── dashboard.html       # Dashboard principal com estatísticas
│   ├── users.html           # Lista de todos os usuários
│   ├── sync_check.html      # Diagnóstico SQLite vs ChromaDB
│   ├── user_analysis.html   # Análise MBTI individual
│   ├── user_development.html # Desenvolvimento do agente
│   └── user_psychometrics.html # Análises psicométricas completas
└── static/                  # (Futuro: CSS/JS customizados)
```

### Integração com Backend

O admin web se comunica diretamente com o `jung_core.py` através do `DatabaseManager`:

```python
# routes.py
from jung_core import DatabaseManager, JungianEngine, Config

db = DatabaseManager()  # Singleton
engine = JungianEngine(db)
```

---

## 🔐 Autenticação

### HTTP Basic Authentication

Todas as rotas (exceto `/admin/test`) exigem autenticação:

```python
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = os.getenv("ADMIN_USER", "admin")
    correct_password = os.getenv("ADMIN_PASSWORD", "admin")
    # ... validação
```

### Configuração de Produção

No Railway, configure as variáveis de ambiente:

```bash
ADMIN_USER=seu_usuario_seguro
ADMIN_PASSWORD=sua_senha_forte_123
```

---

## 📄 Páginas e Funcionalidades

### 1. Dashboard (`/admin`)

**Objetivo:** Visão geral do sistema

**Métricas exibidas:**
- Total de usuários (Telegram)
- Total de interações
- Total de conflitos registrados
- Top 5 usuários mais recentes

**Funcionalidades:**
- Modo diagnóstico (quando `jung_core` não carrega)
- Status de dependências Python
- Links rápidos para usuários

**Screenshot conceitual:**
```
┌──────────────────────────────────────┐
│ 🧠 Jung Claude - Dashboard          │
├──────────────────────────────────────┤
│ 📊 Estatísticas Gerais               │
│  👥 125 usuários                     │
│  💬 3.847 interações                 │
│  ⚡ 1.234 conflitos                  │
├──────────────────────────────────────┤
│ 📋 Usuários Recentes                 │
│  [Lista dos 5 mais recentes]         │
└──────────────────────────────────────┘
```

---

### 2. Lista de Usuários (`/admin/users`)

**Objetivo:** Visualizar e filtrar todos os usuários

**Informações por usuário:**
- Nome e ID
- Total de mensagens
- Última atividade
- Botão "🔍 Ver Detalhes"

**Funcionalidades:**
- Ordenação por nome/mensagens/atividade
- Filtro por mínimo de mensagens
- Navegação para análises individuais

**Cards de usuário:**
```
┌─────────────────────────────────────────┐
│ 👤 Lucas Silva                          │
│ 🆔 abc123...                            │
│ 💬 47 mensagens  ⏰ Há 2 horas         │
│ ⭐ Persona (12x) • Sombra (8x)         │
│                      [🔍 Ver Detalhes] │
└─────────────────────────────────────────┘
```

---

### 3. Análise MBTI (`/admin/user/{user_id}/analysis`)

**Objetivo:** Análise de tipo psicológico MBTI usando Grok AI

**Seções:**

#### 3.1. Informações do Usuário
- Nome, ID, total de conversas e conflitos

#### 3.2. Análise MBTI com Grok
**Botão:** "🧠 Analisar MBTI"

**Processo:**
1. Coleta últimas 30 conversas do usuário
2. Envia para Grok AI (`grok-4-fast-reasoning`)
3. Retorna JSON com análise completa

**Resultado inclui:**
- **Tipo MBTI:** Ex: INFP, ENTJ, etc.
- **Confiança:** 0-100%
- **4 Dimensões:**
  - E/I (Extroversão/Introversão)
  - S/N (Sensação/Intuição)
  - T/F (Pensamento/Sentimento)
  - J/P (Julgamento/Percepção)
- **Funções Cognitivas:**
  - Dominante (ex: Ni - Intuição Introvertida)
  - Auxiliar (ex: Fe - Sentimento Extrovertido)
- **Potenciais e Desafios**
- **Recomendações práticas**

**Requisitos mínimos:**
- 5 conversas mínimas
- `XAI_API_KEY` configurada

---

### 4. Desenvolvimento do Agente (`/admin/user/{user_id}/development`)

**Objetivo:** Acompanhar evolução psicológica do usuário

**Seções:**

#### 4.1. Padrões Comportamentais
Lista padrões detectados automaticamente:
- Nome do padrão (ex: `tema_relacionamentos`)
- Tipo (tema recorrente, mecanismo de defesa, etc.)
- Frequência de ocorrências
- Confiança (0-100%)
- Data de primeira detecção

#### 4.2. Milestones de Desenvolvimento
Marcos importantes da jornada:
- Tipo de milestone
- Descrição
- Estado "antes" e "depois"
- Data de conquista

**Exemplos de milestones:**
- Primeira integração de arquétipos
- Resolução de conflito recorrente
- Mudança significativa de padrão
- Evolução de autoconsciência

#### 4.3. Conflitos Arquetípicos Recentes
Últimos 10 conflitos internos:
- Par de arquétipos em conflito
- Tipo de conflito
- Nível de tensão (0-10)
- Descrição do conflito
- Data

**Visualização:**
```
Persona ⚔️ Sombra
Tipo: Autossabotagem
Tensão: 7.5/10
"Conflito entre apresentação social e
 necessidades emocionais reprimidas"
```

---

### 5. Análises Psicométricas (`/admin/user/{user_id}/psychometrics`) ⭐ **NOVO**

**Objetivo:** Relatório completo para RH com 4 testes psicométricos

> 💼 **Uso corporativo:** Ideal para departamentos de RH avaliarem colaboradores

**Requisitos:**
- Mínimo de **20 conversas** para análise confiável
- `XAI_API_KEY` configurada (Grok AI)

**Geração:**
- **On-demand:** Primeira visita gera análise (15-20 segundos)
- **Cache:** Visitas subsequentes carregam do banco instantaneamente
- **Versionamento:** Cada regeneração cria nova versão (v1, v2, v3...)

---

#### 5.1. Big Five (OCEAN) 🌟

**O que é:** Os 5 traços fundamentais de personalidade

**Traços analisados:**

1. **Openness (Abertura)** - Score 0-100
   - Criatividade, curiosidade, abertura para experiências
   - Níveis: Muito Baixo / Baixo / Médio / Alto / Muito Alto

2. **Conscientiousness (Conscienciosidade)** - Score 0-100
   - Organização, disciplina, responsabilidade
   - Indicador de confiabilidade e planejamento

3. **Extraversion (Extroversão)** - Score 0-100
   - Sociabilidade, assertividade, energia social
   - Preferência por interações sociais vs solidão

4. **Agreeableness (Amabilidade)** - Score 0-100
   - Cooperação, empatia, consideração pelos outros
   - Capacidade de trabalho em equipe

5. **Neuroticism (Neuroticismo)** - Score 0-100
   - Instabilidade emocional, ansiedade, reatividade
   - Baixo score = Estabilidade emocional

**Visualização:**
- **Gráfico Radar:** Visualização dos 5 traços em pentágono
- **Cards detalhados:** Cada traço com descrição e nível
- **Interpretação integrada:** Análise holística do perfil

**Confiança da análise:** 0-100% (baseado em dados disponíveis)

**Uso em RH:**
- Identificar fit cultural
- Alocar papéis adequados (criativo vs operacional)
- Prever dinâmica de equipes
- Planejar desenvolvimento individual

---

#### 5.2. Inteligência Emocional (EQ) 💙

**O que é:** Capacidade de perceber, usar, compreender e gerenciar emoções

**Método de cálculo:**
- ❌ **Não usa Grok AI** (usa dados existentes do sistema)
- ✅ Calcula a partir de: autoconsciência, conflitos, tensão_level, menções sociais

**4 Componentes:**

1. **Autoconsciência (Self-Awareness)** - Score 0-100
   - Fonte: `agent_development.self_awareness_score`
   - Capacidade de reconhecer próprias emoções
   - Base para todas as outras habilidades emocionais

2. **Autogestão (Self-Management)** - Score 0-100
   - Cálculo: Desvio padrão de `tension_level` (menor = melhor)
   - Controle de impulsos e reações emocionais
   - Adaptabilidade a situações estressantes

3. **Consciência Social (Social Awareness)** - Score 0-100
   - Cálculo: Frequência de palavras sociais nas conversas
   - Keywords: 'outros', 'equipe', 'família', 'amigos', 'colegas', 'pessoas'
   - Empatia e percepção das emoções alheias

4. **Gestão de Relacionamentos (Relationship Management)** - Score 0-100
   - Cálculo: Evolução de conflitos arquetípicos ao longo do tempo
   - Capacidade de influenciar, inspirar e desenvolver outros
   - Habilidade de resolver conflitos construtivamente

**Score Geral (EQ Overall):** Média dos 4 componentes

**Potencial de Liderança:**
- Calculado a partir do EQ geral e perfil de conflitos
- Categorias: Alto / Médio / Em Desenvolvimento / Baixo
- Recomendações específicas para desenvolver liderança

**Uso em RH:**
- Identificar potencial de liderança
- Avaliar adequação para cargos de gestão
- Planejar treinamentos de soft skills
- Prever sucesso em trabalho colaborativo

---

#### 5.3. Estilos de Aprendizagem (VARK) 📚

**O que é:** Preferências individuais para absorver conhecimento

**Método:** Análise via Grok AI das palavras e padrões de comunicação

**4 Estilos (scores 0-100, somam ~100):**

1. **Visual (V)** 👁️
   - Palavras-chave: "vejo", "imagem", "parece", "visualizo", "mostra"
   - Aprende melhor com: Diagramas, gráficos, mapas mentais, vídeos
   - **Treinamento ideal:** Infográficos, slides visuais, demonstrações

2. **Auditivo (A)** 🎧
   - Palavras-chave: "ouço", "soa", "ritmo", "escuto", "fala"
   - Aprende melhor com: Podcasts, palestras, discussões, áudio
   - **Treinamento ideal:** Workshops, webinars, sessões de debate

3. **Leitura/Escrita (R)** 📖
   - Indicadores: Mensagens longas, listas, citações, referências
   - Aprende melhor com: Textos, artigos, manuais, relatórios
   - **Treinamento ideal:** E-learning textual, livros, documentação

4. **Cinestésico (K)** ✋
   - Palavras-chave: "sinto", "toque", "movimento", "prática", "experiência"
   - Aprende melhor com: Hands-on, simulações, role-play
   - **Treinamento ideal:** Laboratórios, projetos práticos, mentoria

**Visualização:**
- **Gráfico de Barras:** Comparação dos 4 estilos
- **Barras de progresso:** Indicadores visuais com percentuais
- **Estilo Dominante:** Destaque do estilo com maior score

**Recomendação de Treinamento:**
Texto gerado pelo Grok explicando o melhor formato de capacitação:
> "Usuário com perfil dominantemente Visual (65%) + Cinestésico (25%).
> Recomenda-se treinamentos com demonstrações visuais seguidas de
> prática hands-on. Evitar cursos puramente teóricos/textuais."

**Uso em RH:**
- Personalizar programas de onboarding
- Escolher formato de treinamentos corporativos
- Otimizar transferência de conhecimento
- Aumentar engajamento em capacitações

---

#### 5.4. Valores Pessoais (Schwartz) 🎯

**O que é:** Teoria de Schwartz identifica 10 valores universais que motivam comportamentos

**Método:**
- **Híbrido:**
  1. Primeiro busca em `user_facts` (valores já identificados)
  2. Se < 3 valores, usa Grok AI para inferir das conversas

**10 Valores Universais (scores 0-100):**

1. **Autodireção (Self-Direction)** 🎯
   - Independência de pensamento e ação
   - Criatividade, exploração, autonomia
   - Perfil: Empreendedores, criadores, inovadores

2. **Estimulação (Stimulation)** ⚡
   - Necessidade de novidade, desafios, excitação
   - Variedade, ousadia, vida emocionante
   - Perfil: Aventureiros, early adopters, agentes de mudança

3. **Hedonismo (Hedonism)** 😊
   - Prazer e gratificação sensorial
   - Aproveitar a vida, satisfação pessoal
   - Perfil: Work-life balance, qualidade de vida

4. **Realização (Achievement)** 🏆
   - Sucesso pessoal através de competência
   - Ambição, influência, reconhecimento
   - Perfil: High performers, competitivos, orientados a metas

5. **Poder (Power)** 👑
   - Status social, prestígio, controle sobre recursos
   - Autoridade, dominância, riqueza
   - Perfil: Líderes hierárquicos, executivos seniores

6. **Segurança (Security)** 🛡️
   - Proteção, estabilidade, ordem social
   - Previsibilidade, evitar riscos
   - Perfil: Conservadores, risk-averse, leais

7. **Conformidade (Conformity)** 📏
   - Restrição de ações que violam normas sociais
   - Obediência, autodisciplina, respeito
   - Perfil: Seguidores de regras, tradicionalistas

8. **Tradição (Tradition)** 🏛️
   - Respeito por costumes culturais/religiosos
   - Humildade, devoção, aceitação
   - Perfil: Conservadores culturais, religiosos

9. **Benevolência (Benevolence)** ❤️
   - Bem-estar de pessoas próximas
   - Ajudar, cuidar, lealdade, amizade
   - Perfil: Cuidadores, mentores, pessoas de equipe

10. **Universalismo (Universalism)** 🌍
    - Compreensão, tolerância, justiça social
    - Proteção ambiental, igualdade, paz
    - Perfil: Ativistas, humanitários, idealistas

**Visualização:**
- **Grid de 10 Cards:** Cada valor com emoji, nome e score
- **Top 3 Valores:** Destaque dos valores dominantes
- **Cores e ícones:** Identificação visual rápida

**Análises Derivadas:**

**🏢 Fit Cultural:**
Texto explicando compatibilidade com diferentes tipos de empresa:
> "Top valores: Autodireção + Universalismo + Estimulação.
> Alto fit com: Startups, ONGs, empresas inovadoras, culturas horizontais.
> Baixo fit com: Corporações hierárquicas, ambientes burocráticos rígidos."

**⚠️ Risco de Retenção:**
Predição de risco de turnover baseado em valores:
> "Médio risco. Valores de Estimulação + Autodireção indicam necessidade
> de projetos variados e autonomia. Empresas que oferecerem rotina
> repetitiva podem perder este talento."

**Uso em RH:**
- **Recrutamento:** Avaliar fit cultural antes de contratar
- **Retenção:** Identificar riscos de turnover precocemente
- **Alocação:** Colocar pessoas em times/projetos alinhados com valores
- **Gestão de conflitos:** Entender choques de valores entre colegas
- **Engajamento:** Criar benefícios e políticas alinhadas aos valores

---

#### 5.5. Resumo Executivo 📊

**Síntese de todas as análises em formato executivo:**

```json
{
  "profile": "Big Five: O85, C72, E45, A68, N35",
  "strengths": "Alta abertura para inovação, consciencioso, emocionalmente estável",
  "development_areas": "EQ Liderança: Médio - desenvolver gestão de relacionamentos",
  "organizational_fit": "Ideal para: Inovação, P&D, gestão de projetos criativos",
  "recommendations": "Estilo de aprendizagem: Visual + Cinestésico - usar workshops práticos"
}
```

**Formato de exibição:**
- Card destacado no topo da página
- Cores diferenciadas (gradiente roxo/índigo)
- Bullets com informações-chave
- Linguagem acessível para não-psicólogos

---

#### 5.6. Funcionalidades Técnicas

**Botão "🔄 Regenerar Análises":**
- Força nova análise mesmo se já existe cache
- Cria nova versão (incrementa v1 → v2)
- Útil quando usuário teve muitas novas conversas
- Usa HTMX para atualização assíncrona

**Versionamento:**
- Cada análise salva é uma versão (v1, v2, v3...)
- Mantém histórico de evolução ao longo do tempo
- Campo `version` na tabela `user_psychometrics`
- Possibilita comparação temporal (futuro)

**Cache Inteligente:**
```python
# Primeira visita
GET /admin/user/123/psychometrics
→ Não encontra análise
→ Gera via Grok AI (15-20s)
→ Salva no banco
→ Exibe resultado

# Visitas subsequentes
GET /admin/user/123/psychometrics
→ Encontra análise existente
→ Carrega do banco (<100ms)
→ Exibe resultado instantaneamente
```

**Estado de Erro (<20 conversas):**
```
┌─────────────────────────────────────┐
│ ❌ Dados Insuficientes              │
│                                     │
│ Este usuário possui apenas 12       │
│ conversas. São necessárias pelo     │
│ menos 20 conversas para gerar       │
│ análises psicométricas confiáveis.  │
│                                     │
│ Total de conversas: 12              │
│ Mínimo necessário: 20               │
└─────────────────────────────────────┘
```

---

### 6. Diagnóstico de Sincronização (`/admin/sync-check`)

**Objetivo:** Verificar integridade entre SQLite e ChromaDB

**Métricas:**
- Total de registros no SQLite (metadados)
- Total de vetores no ChromaDB
- Descasamento (se diferença > 5)
- Status de conexão do ChromaDB

**Botão:** "🔍 Diagnosticar"

**Uso:** Troubleshooting quando há inconsistências de dados

---

## 📡 API Endpoints

### Endpoints de Página (HTML)

| Rota | Método | Auth | Descrição |
|------|--------|------|-----------|
| `/admin` | GET | ✅ | Dashboard principal |
| `/admin/users` | GET | ✅ | Lista de usuários |
| `/admin/sync-check` | GET | ✅ | Diagnóstico de sync |
| `/admin/user/{id}/analysis` | GET | ✅ | Análise MBTI |
| `/admin/user/{id}/development` | GET | ✅ | Desenvolvimento |
| `/admin/user/{id}/psychometrics` | GET | ✅ | Análises psicométricas |

### Endpoints de API (JSON/HTMX)

| Rota | Método | Auth | Descrição |
|------|--------|------|-----------|
| `/admin/test` | GET | ❌ | Health check (sem auth) |
| `/admin/api/sync-status` | GET | ✅ | Status do sistema (HTMX) |
| `/admin/api/diagnose` | GET | ✅ | Rodar diagnóstico completo |
| `/admin/api/user/{id}/analyze-mbti` | POST | ✅ | Gerar análise MBTI |
| `/admin/api/user/{id}/regenerate-psychometrics` | POST | ✅ | Regenerar psicometria |

### Exemplos de Requisição

**Gerar análise MBTI:**
```bash
curl -X POST \
  -u admin:admin \
  https://seu-app.railway.app/admin/api/user/abc123/analyze-mbti
```

**Resposta de sucesso:**
```json
{
  "type_indicator": "INFP",
  "confidence": 87,
  "dimensions": {
    "E_I": {
      "score": 45,
      "interpretation": "Leve preferência por Introversão",
      "key_indicators": ["Reflexão interna", "Energia ao estar só"]
    },
    "S_N": {...},
    "T_F": {...},
    "J_P": {...}
  },
  "dominant_function": "Fi (Sentimento Introvertido)",
  "auxiliary_function": "Ne (Intuição Extrovertida)",
  "summary": "Idealista autêntico, guiado por valores pessoais profundos...",
  "potentials": ["Empatia profunda", "Criatividade", "Autenticidade"],
  "challenges": ["Perfeccionismo", "Evitar conflitos", "Decisões práticas"],
  "recommendations": ["Desenvolver Te", "Prática de assertividade"]
}
```

---

## 🛠️ Tecnologias

### Backend

- **FastAPI 0.100+**
  - Framework web assíncrono
  - Validação automática (Pydantic)
  - Documentação OpenAPI automática

- **Jinja2**
  - Template engine server-side
  - Herança de templates (`{% extends %}`)
  - Filtros e funções customizadas

- **SQLite3**
  - Banco de dados relacional
  - Armazena metadados, usuários, conversas, conflitos, análises

- **ChromaDB** (Opcional)
  - Vector database para embeddings
  - Busca semântica de conversas

### Frontend

- **TailwindCSS 3.x**
  - Framework CSS utility-first
  - Responsivo por padrão
  - Customizável via CDN

- **HTMX 1.9**
  - Requisições AJAX sem JavaScript
  - Atualização parcial de DOM
  - Polling e eventos customizados

- **Chart.js 4.x**
  - Gráficos interativos
  - Radar charts (Big Five)
  - Bar charts (VARK)
  - Responsivo e acessível

- **Google Fonts (Inter)**
  - Tipografia moderna e legível

### Integrações

- **Grok AI (X.AI)**
  - Modelo: `grok-4-fast-reasoning`
  - Análises MBTI, Big Five, VARK, Schwartz
  - Requer: `XAI_API_KEY`

- **Telegram Bot API**
  - Fonte de dados dos usuários
  - Integração via `telegram_bot.py`

---

## 📖 Guia de Uso

### Para Administradores

#### 1. Acessar o Painel

1. Navegue para `https://seu-app.railway.app/admin`
2. Insira credenciais (admin/admin ou customizadas)
3. Visualize dashboard com estatísticas gerais

#### 2. Analisar um Usuário

1. Clique em "Usuários" na navbar
2. Encontre o usuário desejado (use filtros se necessário)
3. Clique em "🔍 Ver Detalhes"
4. Escolha o tipo de análise:
   - **Análise MBTI:** Tipo psicológico e funções cognitivas
   - **Desenvolvimento:** Padrões, milestones, conflitos
   - **Psicometria:** Relatório completo para RH

#### 3. Gerar Análise MBTI

1. Na página de análise do usuário
2. Clique em "🧠 Analisar MBTI"
3. Aguarde 10-15 segundos
4. Visualize resultado com tipo, confiança e recomendações

#### 4. Gerar Relatório Psicométrico

1. Certifique-se que usuário tem 20+ conversas
2. Acesse "🧪 Ver Análises Psicométricas Completas"
3. Primeira visita: Aguarde 15-20 segundos (geração)
4. Explore 4 seções: Big Five, EQ, VARK, Schwartz
5. Visualize gráficos e métricas
6. Use botão "🔄 Regenerar" se usuário evoluiu

#### 5. Exportar Dados (Futuro)

> 🚧 **Em desenvolvimento:** Exportação para PDF, Excel, JSON

Temporariamente, use screenshot ou copie texto.

---

### Para Desenvolvedores

#### Adicionar Nova Rota

```python
# admin_web/routes.py

@router.get("/nova-funcionalidade", response_class=HTMLResponse)
async def nova_funcionalidade(
    request: Request,
    username: str = Depends(verify_credentials)
):
    """Sua nova funcionalidade"""
    db = get_db()

    # Sua lógica aqui
    dados = db.alguma_query()

    return templates.TemplateResponse("novo_template.html", {
        "request": request,
        "dados": dados
    })
```

#### Criar Novo Template

```html
<!-- admin_web/templates/novo_template.html -->
{% extends "base.html" %}

{% block content %}
<div class="space-y-6">
    <h1 class="text-3xl font-bold">Título</h1>

    <!-- Seu conteúdo aqui -->
    <div class="bg-white shadow rounded-lg p-6">
        {{ dados }}
    </div>
</div>
{% endblock %}
```

#### Adicionar Gráfico Chart.js

```html
<!-- No template -->
<canvas id="meuGrafico" width="400" height="300"></canvas>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('meuGrafico');
    new Chart(ctx, {
        type: 'bar', // ou 'line', 'radar', 'pie'
        data: {
            labels: ['Label 1', 'Label 2'],
            datasets: [{
                label: 'Meus Dados',
                data: [{{ valor1 }}, {{ valor2 }}],
                backgroundColor: 'rgba(99, 102, 241, 0.5)'
            }]
        },
        options: {
            responsive: true,
            // ... opções
        }
    });
});
</script>
```

#### Adicionar Método de Análise

```python
# jung_core.py (DatabaseManager)

def minha_nova_analise(self, user_id: str) -> Dict:
    """Nova análise customizada"""

    # 1. Buscar dados
    conversations = self.get_user_conversations(user_id, limit=50)

    # 2. Processar
    resultado = processar_dados(conversations)

    # 3. Opcional: Usar Grok AI
    if self.xai_client:
        prompt = f"Analise: {resultado}"
        resposta = send_to_xai(prompt)

    # 4. Retornar estrutura padronizada
    return {
        "score": 85,
        "category": "Alto",
        "details": "Descrição...",
        "recommendations": ["Recomendação 1", "Recomendação 2"]
    }
```

---

## 🐛 Troubleshooting

### Problema: "jung_core não pôde ser carregado"

**Sintomas:**
- Dashboard mostra modo diagnóstico
- Erro no log: `❌ Erro ao importar jung_core`

**Causas possíveis:**
1. Dependências faltando (`openai`, `chromadb`, `langchain`)
2. Erro de sintaxe em `jung_core.py`
3. Falta de variáveis de ambiente

**Solução:**
```bash
# 1. Verificar dependências
pip install -r requirements.txt

# 2. Testar import direto
python -c "from jung_core import DatabaseManager"

# 3. Ver erro detalhado
python main.py
```

---

### Problema: "Dados insuficientes" ao gerar psicometria

**Sintomas:**
- Mensagem: "Este usuário possui apenas X conversas"
- Mínimo necessário: 20

**Solução:**
- Usuário precisa interagir mais com o bot
- Ou ajuste o parâmetro `min_conversations` no código:

```python
# routes.py (linha ~447)
big_five = db.analyze_big_five(user_id, min_conversations=10)  # Reduzir para 10
```

> ⚠️ **Atenção:** Reduzir muito compromete qualidade da análise

---

### Problema: "XAI_API_KEY não configurada"

**Sintomas:**
- Análises MBTI, Big Five, VARK, Schwartz falham
- Erro: "Configure a variável XAI_API_KEY"

**Solução:**
```bash
# No Railway, adicione variável de ambiente:
XAI_API_KEY=xai-sua-chave-aqui

# Localmente, adicione no .env:
echo "XAI_API_KEY=xai-sua-chave" >> .env
```

**Obter chave:**
1. Acesse https://x.ai/
2. Crie conta e acesse API keys
3. Gere nova chave
4. Configure no ambiente

---

### Problema: Gráficos não aparecem

**Sintomas:**
- Espaço em branco onde deveria ter gráfico
- Console do browser: "Chart is not defined"

**Solução:**
1. Verifique se Chart.js está no `base.html`:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

2. Verifique se IDs dos canvas batem:
```html
<!-- Template -->
<canvas id="bigFiveRadarChart"></canvas>

<!-- JavaScript -->
const ctx = document.getElementById('bigFiveRadarChart'); // ✅ Mesmo ID
```

3. Verifique console do browser (F12) para erros JS

---

### Problema: "401 Unauthorized" ao acessar admin

**Sintomas:**
- Popup de autenticação não aceita credenciais
- Erro HTTP 401

**Solução:**
1. Verifique variáveis de ambiente:
```bash
# Railway
ADMIN_USER=admin
ADMIN_PASSWORD=admin
```

2. Limpe cache do navegador (credenciais HTTP Basic ficam em cache)

3. Use navegador anônimo/privado para testar

---

### Problema: Análise demora muito (>30s)

**Sintomas:**
- Timeout ao gerar análises
- Grok AI não responde

**Causas:**
1. Muitas conversas sendo enviadas (token limit)
2. Grok API lenta/congestionada
3. Timeout de rede

**Solução:**
```python
# jung_core.py - Reduzir conversas enviadas
conversations = self.get_user_conversations(user_id, limit=20)  # Era 30-50
```

Ou aumentar timeout:
```python
# jung_core.py - send_to_xai()
response = client.chat.completions.create(
    model="grok-4-fast-reasoning",
    messages=[...],
    timeout=60  # Aumentar para 60s
)
```

---

### Problema: ChromaDB desconectado

**Sintomas:**
- Diagnóstico mostra "Desconectado"
- Erro: "Collection not found"

**Solução:**
1. Verifique se ChromaDB está instalado:
```bash
pip install chromadb
```

2. Verifique path do ChromaDB:
```python
# jung_core.py (Config)
CHROMA_PERSIST_DIR = "./chroma_db"  # Certifique-se que existe
```

3. ChromaDB é opcional - sistema funciona só com SQLite

---

## 🔒 Segurança

### Recomendações de Produção

1. **Mude credenciais padrão**
```bash
ADMIN_USER=seu_usuario_forte
ADMIN_PASSWORD=SenhaForte123!@#
```

2. **Use HTTPS** (Railway fornece automaticamente)

3. **Limite IPs** (se necessário):
```python
# routes.py
ALLOWED_IPS = ["192.168.1.100", "10.0.0.50"]

@router.get("/admin")
async def dashboard(request: Request):
    client_ip = request.client.host
    if client_ip not in ALLOWED_IPS:
        raise HTTPException(403, "IP não autorizado")
```

4. **Rate limiting** (evitar brute force):
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/admin")
@limiter.limit("10/minute")  # Max 10 requisições/minuto
async def dashboard(request: Request):
    ...
```

5. **Logs de auditoria**:
```python
import logging

@router.get("/admin/user/{user_id}/psychometrics")
async def psychometrics(user_id: str, username: str = Depends(verify_credentials)):
    logging.info(f"Admin '{username}' acessou psicometria de '{user_id}'")
    # ... resto do código
```

---

## 📈 Performance

### Otimizações Implementadas

1. **Cache de análises:** Primeira geração é lenta (15-20s), demais são instantâneas
2. **Limit de queries:** `get_user_conversations(limit=30)` evita carregar milhares
3. **Lazy loading:** Templates carregam dados apenas quando necessário
4. **Singleton DatabaseManager:** Reutiliza conexão SQLite

### Métricas Esperadas

| Operação | Tempo Médio | Observação |
|----------|-------------|------------|
| Dashboard load | <500ms | Sem jung_core: <100ms |
| Lista de usuários | 200-500ms | Depende de total de usuários |
| Análise MBTI (primeira) | 10-15s | Chamada Grok AI |
| Psicometria (primeira) | 15-25s | 4 chamadas Grok AI |
| Psicometria (cache) | <200ms | Leitura do SQLite |
| Regenerar psicometria | 15-25s | Nova versão criada |

---

## 🚀 Roadmap Futuro

### Fase 2 - Relatórios Corporativos

- [ ] Exportar análises para PDF
- [ ] Gráficos comparativos de equipes
- [ ] Dashboard de RH com métricas agregadas
- [ ] Alertas de risco de turnover
- [ ] Recomendações de alocação em projetos

### Fase 3 - Integrações

- [ ] API REST completa (JSON)
- [ ] Webhook para sistemas de RH (BambooHR, Gupy, etc.)
- [ ] SSO (Single Sign-On) via OAuth2
- [ ] Integração com Slack para notificações

### Fase 4 - Analytics Avançado

- [ ] Machine Learning para predição de comportamento
- [ ] Análise de compatibilidade entre duplas/equipes
- [ ] Tracking de evolução temporal (comparar v1 vs v5)
- [ ] Benchmarking entre departamentos/empresas

### Fase 5 - Customização

- [ ] White-label (logo e cores customizáveis)
- [ ] Modelos de relatórios personalizados
- [ ] Questionários complementares
- [ ] Integração com assessment centers

---

## 📞 Suporte

### Documentação Adicional

- **Jung Core:** Ver [jung_core.py](../jung_core.py) docstrings
- **Bot Telegram:** Ver [telegram_bot.py](../telegram_bot.py)
- **Main App:** Ver [main.py](../main.py)

### Logs

**Ver logs em tempo real (Railway):**
```bash
railway logs --tail
```

**Logs locais:**
```bash
# Linux/Mac
tail -f jung_claude.log

# Windows (PowerShell)
Get-Content jung_claude.log -Wait
```

### Comunidade

- **Issues:** [GitHub Issues](https://github.com/lucasartel/jungclaude/issues)
- **Discussões:** [GitHub Discussions](https://github.com/lucasartel/jungclaude/discussions)

---

## 📄 Licença

Este painel administrativo faz parte do projeto Jung Claude.

**Desenvolvido por:** Sistema Jung Claude
**Versão:** 1.0 (com Análises Psicométricas)
**Última atualização:** 2025-01-25

---

## 🎯 Conclusão

O painel administrativo do Jung Claude é uma ferramenta completa para:

✅ **Monitorar** interações do bot em tempo real
✅ **Analisar** perfis psicológicos (MBTI + 4 psicométricos)
✅ **Gerar** insights para RH e gestão de pessoas
✅ **Acompanhar** desenvolvimento psicológico individual
✅ **Visualizar** dados de forma clara e acionável

Com a adição das **Análises Psicométricas (Big Five, EQ, VARK, Schwartz)**, o Jung Claude agora oferece valor direto para departamentos de RH corporativos, permitindo:

- Avaliações objetivas de colaboradores
- Decisões de contratação baseadas em dados
- Planejamento de desenvolvimento individual
- Prevenção de turnover
- Otimização de alocação de talentos

**O futuro do RH é baseado em dados psicológicos profundos. Jung Claude entrega isso hoje.** 🚀
