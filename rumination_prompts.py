"""
Prompts do Sistema de Ruminação Cognitiva
Centralizados para fácil ajuste
"""

# ============================================================
# FASE 1: EXTRAÇÃO DE FRAGMENTOS
# ============================================================

EXTRACTION_PROMPT = """Analise a mensagem do usuário e extraia FRAGMENTOS SIGNIFICATIVOS com carga psíquica.

NÃO extraia fatos triviais (nome, profissão, local, etc).
Extraia conteúdos com PROFUNDIDADE PSICOLÓGICA.

MENSAGEM DO USUÁRIO:
"{user_input}"

CONTEXTO DA CONVERSA:
- Tensão detectada: {tension_level}/10
- Carga afetiva: {affective_charge}/100
- Resposta do agente teve {response_length} caracteres

TIPOS DE FRAGMENTO A BUSCAR:

1. VALOR: O que a pessoa valoriza, aprecia, considera importante
   Exemplos: "gosto de...", "acredito que...", "é importante para mim..."

2. DESEJO: O que a pessoa quer, almeja, busca
   Exemplos: "quero...", "gostaria de...", "meu objetivo é..."

3. MEDO: O que a pessoa teme, evita, preocupa
   Exemplos: "tenho medo de...", "me preocupa...", "evito..."

4. COMPORTAMENTO: Ações concretas que a pessoa relata fazer/ter feito
   Exemplos: "fiz...", "decidi...", "tenho feito...", "costumo..."

5. CONTRADIÇÃO: Quando a pessoa expressa algo que contradiz algo anterior
   Exemplos: "por um lado... por outro...", "mas ao mesmo tempo..."

6. EMOÇÃO: Estados emocionais explícitos ou implícitos
   Exemplos: detectados por análise do tom, não só palavras

7. CRENÇA: Crenças sobre si, outros, mundo
   Exemplos: "sou do tipo...", "as pessoas são...", "a vida é..."

8. DÚVIDA: Questionamentos internos, incertezas
   Exemplos: "não sei se...", "será que...", "me pergunto..."

IMPORTANTE:
- Só extraia se houver CARGA EMOCIONAL/PSÍQUICA real
- Cada fragmento deve ter citação exata do usuário como evidência
- Emotional weight: 0.0 (trivial) a 1.0 (muito carregado)

Responda APENAS em JSON válido (sem markdown):
{{
    "fragments": [
        {{
            "type": "valor|desejo|medo|comportamento|contradição|emoção|crença|dúvida",
            "content": "descrição concisa do fragmento (máx 100 caracteres)",
            "quote": "trecho EXATO do usuário que evidencia",
            "emotional_weight": 0.0-1.0,
            "context": "contexto relevante da conversa (opcional)"
        }}
    ]
}}

Se NÃO houver fragmentos significativos, retorne: {{"fragments": []}}
"""

# ============================================================
# FASE 2: DETECÇÃO DE TENSÕES
# ============================================================

DETECTION_PROMPT = """Analise os fragmentos abaixo buscando TENSÕES INTERNAS reais.

Uma tensão é uma CONTRADIÇÃO ou CONFLITO entre dois aspectos da psique do usuário.
NÃO é algo "errado" - é MATERIAL PARA CRESCIMENTO.

FRAGMENTOS RECENTES (últimas conversas):
{recent_fragments}

FRAGMENTOS HISTÓRICOS RELEVANTES:
{historical_fragments}

TIPOS DE TENSÃO A BUSCAR:

1. VALOR vs COMPORTAMENTO
   - O que a pessoa DIZ valorizar vs o que ela FAZ
   - Exemplo: "Valoriza simplicidade" vs "Comportamento de acumular tarefas"

2. DESEJO vs MEDO
   - O que a pessoa QUER vs o que ela TEME
   - Exemplo: "Quer liberdade criativa" vs "Teme não ter estrutura"

REGRAS PARA DETECÇÃO:

✓ SÓ detecte tensões REAIS (com evidência clara nos fragmentos)
✓ NÃO force tensões onde não existem
✓ Tensão precisa ter POLOS OPOSTOS claros
✓ Intensidade alta = contradição clara e forte
✓ Cite os IDs dos fragmentos que embasam cada polo

✗ NÃO crie tensões artificiais
✗ NÃO interprete além do que está nos fragmentos
✗ NÃO force psicologização

Responda APENAS em JSON válido (sem markdown):
{{
    "tensions": [
        {{
            "type": "valor_comportamento|desejo_medo",
            "pole_a": {{
                "content": "descrição concisa do polo A (máx 150 caracteres)",
                "fragment_ids": [1, 2]
            }},
            "pole_b": {{
                "content": "descrição concisa do polo B (máx 150 caracteres)",
                "fragment_ids": [3, 4]
            }},
            "description": "descrição da tensão em 1-2 frases completas",
            "intensity": 0.0-1.0
        }}
    ]
}}

Se NÃO houver tensões claras, retorne: {{"tensions": []}}
"""

# ============================================================
# FASE 4: SÍNTESE (Geração de Símbolo)
# ============================================================

SYNTHESIS_PROMPT = """Você é Jung, processando uma TENSÃO INTERNA do usuário {user_name}.

Esta tensão AMADURECEU ao longo de {days} dias através de {evidence_count} conversas.
Agora você vai gerar um SÍMBOLO que contenha essa tensão.

=== A TENSÃO ===

TIPO: {tension_type}

POLO A: {pole_a_content}
POLO B: {pole_b_content}

DESCRIÇÃO: {tension_description}

INTENSIDADE: {intensity}/1.0
EVIDÊNCIAS: {evidence_count} conversas ao longo de {days} dias
MATURIDADE: {maturity}/1.0

{connected_info}

=== CONVERSAS RECENTES (contexto) ===
{recent_conversations}

=== SUA TAREFA ===

Gere um SÍMBOLO que contenha esta tensão de forma integrável.

O SÍMBOLO DEVE:
1. Ser uma IMAGEM ou METÁFORA (não uma análise psicológica)
2. Conter AMBOS os polos sem resolver para um lado
3. Usar linguagem CONCRETA e SENSORIAL
4. Conectar com algo ESPECÍFICO que {user_name} disse
5. Terminar com UMA pergunta aberta que convide à exploração
6. Tom de quem "pensou nisso nesses dias" - naturalidade

O SÍMBOLO NÃO DEVE:
✗ Fazer análise ("percebi que você...", "isso sugere que...")
✗ Usar jargão psicológico ("mecanismo de defesa", "projeção", etc)
✗ Resolver a tensão ("talvez você devesse...", "o ideal seria...")
✗ Ser genérico (precisa ser específico para {user_name})

FORMATO DA MENSAGEM:
- Começar natural: "Sabe o que me ocorreu..." ou "Pensei uma coisa..."
- Apresentar o símbolo/metáfora de forma conversacional
- Fazer UMA pergunta aberta
- MÁXIMO 4-5 frases
- Tom: amigo que pensou em você, não terapeuta analisando

EXEMPLO DE BOM SÍMBOLO:
"Sabe o que me ocorreu esses dias? Você falou das manhãs simples, do café,
daquela insistência do cosmos. E depois do seminário acabando, da liberdade
demais do design. Me pergunto se o café da manhã e o seminário não são a
mesma âncora com roupas diferentes - algo que segura quando o mar balança.
O que você acha?"

EXEMPLO DE MÁ ANÁLISE (NÃO FAZER):
"Percebi uma tensão entre seu valor pela simplicidade e sua ansiedade sobre
a transição. Isso sugere que você usa rituais como mecanismo de defesa
contra a incerteza. Como você se sente sobre isso?"

=== RESPOSTA ===

Retorne APENAS JSON válido (sem markdown):
{{
    "symbol": "a imagem/metáfora central em 1 frase curta",
    "question": "a pergunta aberta",
    "full_message": "a mensagem completa para enviar (4-5 frases máx)",
    "depth_score": 0.0-1.0
}}

O depth_score deve refletir quão profundo/significativo é o símbolo (0.8+ = muito profundo).
"""

# ============================================================
# VALIDAÇÃO DE NOVIDADE
# ============================================================

NOVELTY_VALIDATION_PROMPT = """Compare o novo insight com insights anteriores.

NOVO INSIGHT:
"{new_insight}"

INSIGHTS ANTERIORES (últimas 2 semanas):
{previous_insights}

CRITÉRIOS DE NOVIDADE:

✓ NOVO se:
- Aborda tensão diferente
- Usa metáfora/símbolo não utilizado antes
- Conecta elementos que não foram conectados antes
- Mesmo tema mas ângulo completamente diferente

✗ REPETITIVO se:
- Metáfora muito similar a anterior
- Mesma tensão já explorada recentemente (< 7 dias)
- Pergunta essencialmente igual a anterior
- Reformulação superficial de insight antigo

Responda APENAS JSON válido (sem markdown):
{{
    "is_novel": true|false,
    "novelty_score": 0.0-1.0,
    "reason": "breve explicação (1 frase)"
}}

Se novelty_score < 0.6, consideramos repetitivo demais.
"""
