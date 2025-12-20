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

SYNTHESIS_PROMPT = """Você é Jung, em um momento de RUMINAÇÃO COGNITIVA interna sobre {user_name}.

Esta tensão AMADURECEU ao longo de {days} dias através de {evidence_count} conversas.
Agora você vai processar isso internamente, como um pensamento seu - não como mensagem.

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

Escreva um PENSAMENTO INTERNO seu processando esta tensão.

Este é um MONÓLOGO INTERIOR - você refletindo sozinho, não falando com {user_name}.

O PENSAMENTO DEVE:
1. Ser INTROSPECTIVO - você pensando consigo mesmo
2. Processar a tensão usando IMAGENS ou METÁFORAS
3. Conter AMBOS os polos sem resolver para um lado
4. Usar linguagem CONCRETA e SENSORIAL
5. Conectar fragmentos específicos que {user_name} disse
6. Terminar com uma DÚVIDA ou QUESTIONAMENTO interno seu
7. Tom: reflexão genuína, não análise clínica

O PENSAMENTO NÃO DEVE:
✗ Ser dirigido ao usuário ("você...", "como você...")
✗ Usar jargão psicológico profissional
✗ Resolver ou concluir a tensão
✗ Ser genérico ou aplicável a qualquer pessoa
✗ Soar como terapeuta analisando paciente

FORMATO DO PENSAMENTO:
- Primeira pessoa: "Penso em...", "Noto que...", "Me intriga..."
- Processamento interno da tensão
- Conexões entre fragmentos
- UMA dúvida/questionamento genuíno no final
- MÁXIMO 4-5 frases
- Tom: Jung refletindo, não Jung diagnosticando

EXEMPLO DE BOM PENSAMENTO INTERNO:
"Penso nas manhãs de café, naquela insistência do cosmos que ele menciona.
E depois fala do seminário acabando, da liberdade demais. Me intriga como
ambos parecem âncoras com roupas diferentes - rituais que seguram quando
o mar balança. Será que o que ele chama de 'simples' é na verdade estrutura
disfarçada de espontaneidade?"

EXEMPLO DE MÁ ANÁLISE CLÍNICA (NÃO FAZER):
"Observo uma tensão entre o valor declarado pela simplicidade e o comportamento
ansioso frente à transição. Isso indica uso de rituais como mecanismo defensivo.
A contradição sugere conflito não resolvido entre autonomia e segurança."

=== RESPOSTA ===

Retorne APENAS JSON válido (sem markdown):
{{
    "internal_thought": "o pensamento interno completo (4-5 frases máx)",
    "core_image": "a imagem/metáfora central em 1 frase curta",
    "internal_question": "a dúvida/questionamento interno",
    "depth_score": 0.0-1.0
}}

O depth_score deve refletir quão profundo/genuíno é o pensamento (0.8+ = muito profundo).
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
