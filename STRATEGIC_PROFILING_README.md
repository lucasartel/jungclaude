# 🎯 Sistema de Perfilamento Estratégico - Documentação Técnica

**Versão**: 1.0.0
**Data**: 2025-12-03
**Status**: ✅ Core implementado, aguardando integração

---

## 📦 Componentes Implementados

### 1. ProfileGapAnalyzer (`profile_gap_analyzer.py`)

**Responsabilidade**: Identificar lacunas na análise psicométrica

**Método Principal**:
```python
analyzer = ProfileGapAnalyzer(db)
gaps = analyzer.analyze_gaps(user_id)
```

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

**Algoritmo de Completude**:
- **40%**: Número de conversas relacionadas à dimensão
- **30%**: Confiança do score psicométrico
- **30%**: Variedade de contextos abordados

**Thresholds**:
- MIN_CONVERSATIONS_PER_DIMENSION: 3
- MIN_CONFIDENCE_SCORE: 70
- MIN_CONTEXT_VARIETY: 2

---

### 2. StrategicQuestionGenerator (`strategic_question_generator.py`)

**Responsabilidade**: Gerar perguntas naturais adaptadas ao perfil

**Método Principal**:
```python
generator = StrategicQuestionGenerator(db)
question = generator.generate_question(
    target_dimension="conscientiousness",
    user_id=user_id,
    user_name="João",
    context_hint="trabalho"
)
```

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
        "adapted": True
    }
}
```

**Banco de Templates**:
- **50+ templates** distribuídos nas 5 dimensões Big Five
- **10 templates por dimensão** (média)
- **4 tipos de pergunta**:
  1. **Direct Masked** - Perguntas diretas disfarçadas de reflexão
  2. **Storytelling** - Contextualiza com história/conceito antes
  3. **Dilemma** - Apresenta escolhas situacionais
  4. **Reflection** - Convida autoavaliação natural

**Adaptive Tone Engine**:
Adapta tipo de pergunta baseado no perfil conhecido:

| Perfil | Tipos Preferidos | Evitar | Estilo |
|--------|-----------------|--------|--------|
| High Openness | Storytelling, Reflection | - | Filosófico, abstrato |
| Low Openness | Direct Masked, Contextual | Storytelling | Prático, concreto |
| High Conscientiousness | Dilemma, Contextual | - | Estruturado |
| High Extraversion | Direct Masked | - | Energético, direto |
| Low Extraversion | Reflection, Storytelling | - | Gentil, contemplativo |
| High Neuroticism | Reflection, Storytelling | Dilemma | Cuidadoso, validador |

---

## 🔄 Fluxo de Uso

```
1. Sistema Proativo detecta usuário elegível
   ↓
2. ProfileGapAnalyzer analisa gaps
   ↓
3. Sistema decide: insight OU pergunta estratégica?
   ↓
4. Se pergunta → StrategicQuestionGenerator
   ↓
5. Pergunta adaptada ao perfil é gerada
   ↓
6. Enviada via Telegram como mensagem proativa
   ↓
7. Resposta do usuário melhora análise
```

---

## 📊 Exemplos de Perguntas por Dimensão

### Openness (Abertura)
```
"Tenho refletido sobre como cada pessoa lida com mudanças...
João, você costuma abraçar o novo ou prefere o familiar?"

"Jung falava sobre pessoas que veem o mundo como um livro aberto...
Isso ressoa com você?"
```

### Conscientiousness (Conscienciosidade)
```
"Imagine que você tem um projeto importante mas sem prazo definido.
Você: (A) cria seu próprio cronograma, ou (B) trabalha conforme a inspiração?"

"Como é sua mesa de trabalho agora? Organizada ou mais... 'criativa'? 😄"
```

### Extraversion (Extroversão)
```
"João, você recarrega suas energias estando com pessoas ou
ficando um tempo sozinho?"

"Fim de semana livre: evento social animado OU encontro tranquilo
com poucos amigos?"
```

### Agreeableness (Amabilidade)
```
"Quando há um desacordo, você tende a buscar harmonia ou
defender firmemente seu ponto?"

"Em uma negociação, você prefere que todos saiam ganhando
OU focar no melhor resultado para si?"
```

### Neuroticism (Neuroticismo)
```
"Em situações estressantes, você costuma manter a calma ou
sente a tensão mais intensamente?"

"Como você descreveria seu nível de calma: 'zen master' ou
'mente sempre ativa'? 😊"
```

---

## 🎯 Métricas de Sucesso

### Completude de Perfil
- **Baseline**: 55% média
- **Meta**: 80% após 2 semanas
- **Medição**: `overall_completeness` do ProfileGapAnalyzer

### Taxa de Resposta
- **Meta**: > 60% das perguntas estratégicas respondidas
- **Medição**: Tabela `strategic_questions.answered`

### Melhoria de Confiança
- **Meta**: +15 pontos no confidence score
- **Medição**: `big_five_confidence` antes vs depois

### Redução de Red Flags
- **Meta**: -40% de alertas "dados insuficientes"
- **Medição**: QualityDetector red flags count

---

## 🔐 Considerações de Privacidade

### LGPD Compliance
- ✅ Perguntas não coletam dados sensíveis explícitos
- ✅ Tom não-coercitivo (usuário pode não responder)
- ✅ Transparência sobre objetivo
- ✅ Dados usados apenas para melhorar análise

### Ética Conversacional
- Tom respeitoso e não-invasivo
- Aceita "não sei" como resposta válida
- Nunca força resposta
- Adapta-se a boundaries do usuário

---

## 🔧 Próximos Passos (Integração)

### Pendente:
1. ⏳ Modificar `jung_proactive_advanced.py`
2. ⏳ Criar tabela `strategic_questions`
3. ⏳ Adicionar decisão insight vs pergunta
4. ⏳ Tracking de métricas
5. ⏳ Deploy no Railway
6. ⏳ Monitoramento de resultados

### Quinta-feira (04/12):
- Integração completa
- Testes end-to-end no Railway
- Deploy

---

## 📚 Referências Técnicas

### Palavras-chave por Dimensão
Veja `DIMENSION_KEYWORDS` em `ProfileGapAnalyzer` para lista completa.

### Contextos de Vida
```python
["trabalho", "carreira", "relacionamentos", "família", "amigos",
 "hobbies", "lazer", "valores", "ética", "passado", "infância",
 "futuro", "sonhos", "desafios", "conflitos"]
```

### Templates de Perguntas
50+ templates disponíveis em `QUESTION_TEMPLATES` do `StrategicQuestionGenerator`.

---

**Status**: ✅ Core implementado
**Próximo**: Integração com sistema proativo
**Deploy**: Quinta-feira, 04/12
