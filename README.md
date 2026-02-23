# 🧠 Jung Claude (JungProject)

## 📖 Sobre o Projeto

Este projeto nasceu da ideia de aplicar conceitos da psicologia analítica para simular uma psiquê humana com o uso de Inteligência Artificial e LLMs (Large Language Models). 

---

## ✨ Conceito Central

Em vez de ser um simples "chatbot de perguntas e respostas", este projeto desenvolve uma inteligência artificial que simula uma "psique" interna, baseando-se em modelos psicológicos e linguísticos complexos. 

A proposta é construir uma IA que incorpora:
1. **A Estrutura da Psique de Carl Jung**: Consciência, Inconsciente Pessoal, Inconsciente Coletivo e dinâmicas arquetípicas.
2. **A Tensão Dialógica de Mikhail Bakhtin**: Múltiplas "vozes" internas (polifonia) dialogam e debatem, impulsionando a construção gradual de conhecimento, identidade e empatia.

O sistema atua como um conjunto de **lentes interpretativas**. Quando o usuário interage, a arquitetura psíquica não atua como um simples filtro de conhecimento, mas como um motor de reflexão que permite à identidade emergente ter profundidade e memória contínua.

Link para o Artigo completo (Fundamentação Teórica): [Docs Google](https://docs.google.com/document/d/1s265ZOO2ZLsoTd-bPjJr0JbQZnqz5BvFAyBAhjsVyu0/edit?usp=sharing)

---

## 🚀 Principais Recursos e Arquitetura

O sistema evoluiu para uma plataforma robusta e multifacetada, contendo os seguintes módulos principais:

### 1. Motor Junguiano (`JungianEngine` & Core)
O coração da aplicação. Emula funções psíquicas (Persona, Sombra, Anima) e processa mensagens avaliando o tom emocional, detectando fragmentos comportamentais e gerando respostas a partir da dinâmica dessas instâncias internas ativas.

### 2. Memória Contínua (Banco de Dados Híbrido)
A IA não tem amnésia. O sistema mescla dados estruturados relacionais (**SQLite**) com buscas semânticas vetoriais ultra-rápidas (**ChromaDB** / **Mem0** com *OpenAI Embeddings*). Fatos curtos são extraídos por LLMs no background e consolidados em traços e padrões de longo prazo.

### 3. Ruminação e Evolução de Identidade
Enquanto o usuário não está conversando, a IA possui seu próprio "inconsciente" trabalhando em background. Jobs de **Ruminação** revisitam conversas recentes, processam tensões não resolvidas, amadurecem pensamentos e geram "insights". Isso alimenta o desenvolvimento da própria identidade do agente (que evolui em fases, de 1 a 5).

### 4. Sistema Proativo (Push Notifications)
Se o usuário ficar inativo, o sistema analisa o contexto da última conversa, a fase evolutiva da IA e gera mensagens espontâneas (Just-in-Time) no Telegram. A IA toma a iniciativa de reengajar de forma natural e empática, baseada em reflexões não literais.

### 5. Validação Psicométrica (MBTI, Big Five, etc.)
Com o acúmulo de interações, o motor é capaz de aplicar análises baseadas em psicometria, traçando perfis de MBTI, Big Five (OCEAN), inteligência emocional e estilos de aprendizagem do usuário, entregues mediante comandos específicos.

### 6. Dashboard Administrativo Multi-Tenant (FastAPI)
Gestores podem monitorar o "estado mental" da IA e a base de usuários em tempo real através de uma interface web (Dashboard Admin) construída em **FastAPI**, com gráficos de retenção, tensões ativas da IA e visualização das ruminações dos usuários.

### 7. Interface do Usuário (Telegram Bot)
A linha de frente do sistema é um bot no Telegram, suportando comandos diretos como `/start`, `/mbti` (geração psicológica), `/stats` (estatísticas) e `/desenvolvimento` (status do amadurecimento do agente).

---

## 🛠️ Tecnologias Envolvidas
* **Linguagem**: Python (Assíncrono com `asyncio`)
* **Frameworks Web & Bots**: `python-telegram-bot` e `FastAPI` (Dashboard web administrativo)
* **Bancos de Dados**: SQLite (Relacional), ChromaDB / Qdrant via Mem0 (Vetorial)
* **LLMs e IA**: Anthropic Claude 3.5 (Sonnet/Haiku), OpenAI Embeddings, Integrações via OpenRouter.
* **Agendamento**: `schedule` para rotinas diárias e de background.

---

## 📧 Contato

**Lucas Pedro**
* **Email:** `lucas.arte@gmail.com`
* **LinkedIn:** [Lucas Pedro - 37graus](https://www.linkedin.com/in/lucas-pedro-37graus/)
