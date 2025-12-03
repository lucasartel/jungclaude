# 🎯 Plano: Sistema Proativo de Perfilamento Conversacional

**Data:** 2025-12-03 (Quarta-feira)
**Objetivo:** Transformar mensagens proativas em perguntas estratégicas para enriquecer análise psicométrica

---

## 📊 Situação Atual

### Sistema Proativo Existente (v4.2.0)
- ✅ Gera insights baseados em tópicos das conversas
- ✅ Usa pares arquetípicos rotativos
- ✅ Conhecimento autônomo multi-domínio
- ✅ Anti-repetição via banco de dados
- ⚠️ **Problema**: Foco em insights, não em coleta de dados

### Sistema de Qualidade (v1.0)
- ✅ Detecta dados insuficientes (< 10 conversas)
- ✅ Identifica baixo engajamento (mensagens curtas)
- ✅ Alerta sobre análises incompletas
- ⚠️ **Gap**: Não ajuda ativamente a coletar dados melhores

---

## 🎯 Visão do Sistema Novo

### Sistema Proativo de Perfilamento (v5.0)

**Conceito**: Questionário conversacional adaptativo que:
1. Identifica gaps na análise psicométrica
2. Gera perguntas naturais para preencher gaps
3. Adapta o tom ao perfil já conhecido do usuário
4. Mantém naturalidade da conversa
5. Melhora progressivamente a qualidade dos dados

---

## 🏗️ Arquitetura do Sistema

### Componente 1: Profile Gap Analyzer
**Responsabilidade**: Identificar o que falta na análise

**Input**:
- Dados psicométricos atuais
- Conversas existentes
- Red flags do QualityDetector

**Output**:
```python
{
    "incomplete_dimensions": ["openness", "neuroticism"],
    "missing_contexts": ["trabalho", "relacionamentos"],
    "low_confidence_areas": ["valores pessoais"],
    "suggested_topics": [
        {
            "dimension": "openness",
            "topic": "criatividade",
            "priority": 0.9
        }
    ]
}
```

### Componente 2: Strategic Question Generator
**Responsabilidade**: Gerar perguntas naturais baseadas em gaps

**Estratégias**:
1. **Perguntas Diretas Disfarçadas**
   - "Tenho refletido sobre algo... Como você costuma reagir quando..."
   - Natural, mas estratégica

2. **Storytelling com Pergunta**
   - "Jung uma vez disse... Isso te faz pensar em algo?"
   - Contextualiza antes de perguntar

3. **Dilemmas Situacionais**
   - "Imagine que você precisa escolher entre..."
   - Revela valores e traços

4. **Reflexões Provocativas**
   - "Percebi que não falamos sobre... O que você pensa disso?"
   - Abre novo terreno

### Componente 3: Adaptive Tone Engine
**Responsabilidade**: Adaptar tom ao perfil conhecido

**Regras**:
- **High Openness** → Perguntas abstratas, filosóficas
- **High Conscientiousness** → Perguntas estruturadas, práticas
- **High Extraversion** → Tom energético, social
- **High Agreeableness** → Perguntas empáticas, colaborativas
- **High Neuroticism** → Tom cuidadoso, sem pressão

---

## 🛠️ Implementação Técnica

### Fase 1: Profile Gap Analyzer (2h)

**Arquivo**: `profile_gap_analyzer.py`

```python
class ProfileGapAnalyzer:
    """Identifica gaps na análise psicométrica"""

    def analyze_gaps(self, user_id: str) -> Dict:
        """
        Analisa o que falta para análise completa

        Returns:
            {
                "overall_completeness": 0.65,  # 0-1
                "dimension_completeness": {
                    "openness": 0.8,
                    "conscientiousness": 0.4,  # LOW!
                    ...
                },
                "missing_contexts": ["trabalho", "família"],
                "priority_questions": [...]
            }
        """

    def _calculate_dimension_completeness(self, dimension, conversations):
        """
        Calcula completude de uma dimensão baseado em:
        - Número de conversas relacionadas
        - Variedade de contextos abordados
        - Confiança atual do score
        """

    def _identify_missing_contexts(self, conversations):
        """
        Identifica contextos de vida não abordados:
        - Trabalho/carreira
        - Relacionamentos
        - Família
        - Hobbies/lazer
        - Valores/ética
        - Passado/infância
        """
```

### Fase 2: Strategic Question Generator (3h)

**Arquivo**: `strategic_question_generator.py`

```python
class StrategicQuestionGenerator:
    """Gera perguntas estratégicas para perfilamento"""

    # Templates por dimensão Big Five
    QUESTION_TEMPLATES = {
        "openness": [
            {
                "type": "direct_masked",
                "template": "Tenho refletido sobre como cada pessoa lida com mudanças... {user_name}, você costuma abraçar o novo ou prefere o familiar?",
                "reveals": ["abertura a experiências", "tolerância ao risco"]
            },
            {
                "type": "storytelling",
                "template": "Jung falava sobre pessoas que veem o mundo como um livro aberto, cheio de possibilidades... Isso ressoa com você?",
                "reveals": ["curiosidade intelectual", "imaginação"]
            }
        ],
        "conscientiousness": [
            {
                "type": "dilemma",
                "template": "Imagine que você tem um projeto importante mas sem prazo definido. Como você aborda isso?",
                "reveals": ["autodisciplina", "organização"]
            }
        ],
        # ... outros
    }

    def generate_question(
        self,
        target_dimension: str,
        current_profile: Dict,
        user_name: str
    ) -> str:
        """
        Gera pergunta adaptada ao perfil atual
        """

    def _select_best_template(self, dimension, profile):
        """
        Escolhe template mais adequado baseado no perfil
        """

    def _inject_context_from_past(self, template, conversations):
        """
        Adiciona referências sutis a conversas anteriores
        Ex: "Lembro que você mencionou gostar de [X]..."
        """
```

### Fase 3: Integração com Sistema Proativo (2h)

**Modificar**: `jung_proactive_advanced.py`

```python
def check_and_generate_advanced_message(self, user_id, user_name):
    """Método principal - MODIFICADO"""

    # ... código de elegibilidade existente ...

    # NOVO: Decidir entre insight vs pergunta estratégica
    decision = self._decide_message_type(user_id)

    if decision == "strategic_question":
        # Usar novo sistema de perguntas
        gap_analyzer = ProfileGapAnalyzer(self.db)
        gaps = gap_analyzer.analyze_gaps(user_id)

        question_gen = StrategicQuestionGenerator(self.db)
        message = question_gen.generate_question(
            target_dimension=gaps["priority_questions"][0]["dimension"],
            current_profile=self.db.get_psychometrics(user_id),
            user_name=user_name
        )

        # Salvar com marcador especial
        self._save_strategic_question(user_id, message, gaps)

        return message

    else:
        # Sistema existente (insights)
        return self._generate_insight_message(...)

def _decide_message_type(self, user_id) -> str:
    """
    Decide se envia pergunta estratégica ou insight

    Regra:
    - Se completude < 70% → strategic_question (80% chance)
    - Se completude >= 70% → insight (modo atual)
    - Se últimas 2 foram perguntas → insight (variedade)
    """
```

### Fase 4: Tracking e Analytics (1h)

**Adicionar**: Tabela `strategic_questions`

```sql
CREATE TABLE strategic_questions (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    question_text TEXT NOT NULL,
    target_dimension TEXT NOT NULL,
    gap_type TEXT,  -- "insufficient_data", "low_confidence", etc.
    asked_at DATETIME,
    answered BOOLEAN DEFAULT 0,
    answer_quality_score REAL,  -- Avaliado automaticamente
    improved_analysis BOOLEAN,  -- Se melhorou após resposta
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**Métricas a Rastrear**:
- Taxa de resposta às perguntas estratégicas
- Melhoria de completude após perguntas
- Tempo médio até resposta
- Correlação entre tipo de pergunta e qualidade da resposta

---

## 📋 Cronograma de Implementação

### Quarta-feira, 03/12 (Hoje)

**Manhã** (3-4h):
1. ✅ Criar `profile_gap_analyzer.py` (2h)
2. ✅ Testes unitários do analyzer (30min)
3. ✅ Documentação (30min)

**Tarde** (3-4h):
4. ✅ Criar `strategic_question_generator.py` (2h)
5. ✅ Criar banco de perguntas templates (1h)
6. ✅ Testes com perfis reais (30min)

### Quinta-feira, 04/12

**Manhã** (3h):
7. ✅ Modificar `jung_proactive_advanced.py` (2h)
8. ✅ Criar tabela `strategic_questions` (30min)
9. ✅ Migração no Railway (30min)

**Tarde** (3h):
10. ✅ Testes end-to-end (1h)
11. ✅ Ajustes e refinamentos (1h)
12. ✅ Deploy e monitoramento (1h)

### Sexta-feira, 05/12

**Manhã** (2h):
13. ✅ Analytics dashboard (visualizar perguntas e respostas)
14. ✅ Documentação final

**Tarde** (2h):
15. ✅ Apresentação para stakeholders
16. ✅ Ajustes baseados em feedback

---

## 🎯 Métricas de Sucesso

### KPIs Primários
1. **Completude de Perfil**:
   - Antes: 55% média
   - Meta: 80% média após 2 semanas

2. **Taxa de Resposta**:
   - Meta: > 60% das perguntas estratégicas são respondidas

3. **Melhoria de Confiança**:
   - Meta: +15 pontos no confidence score após 5 perguntas

### KPIs Secundários
4. **Redução de Red Flags**:
   - Meta: -40% de alertas "dados insuficientes"

5. **Engajamento**:
   - Meta: +20% no comprimento médio das respostas

6. **Satisfação NPS**:
   - Meta: > 8.0 de satisfação com perguntas

---

## 🔐 Considerações de Privacidade

### LGPD Compliance
- ✅ Perguntas não coletam dados sensíveis explícitos
- ✅ Usuário pode recusar responder (tom não-coercitivo)
- ✅ Dados usados apenas para melhorar análise
- ✅ Transparência: "Isso me ajuda a te conhecer melhor"

### Ética Conversacional
- ❌ NUNCA forçar resposta
- ❌ NUNCA fazer perguntas intrusivas
- ✅ SEMPRE respeitar boundaries
- ✅ Adaptar se usuário demonstra desconforto

---

## 🚀 Benefícios Esperados

### Para o Usuário (B2C)
1. **Experiência mais rica**: Conversas mais profundas e personalizadas
2. **Autoconhecimento**: Perguntas provocam reflexão
3. **Natural**: Não parece questionário, parece conversa real

### Para o RH (B2B)
1. **Dados melhores**: Análises mais completas e confiáveis
2. **Menos gaps**: Redução de alertas de qualidade
3. **Mais contexto**: Entende o candidato em múltiplas dimensões

### Para o Negócio
1. **Diferencial competitivo**: Questionário conversacional único
2. **Maior precisão**: Análises mais acuradas = mais valor
3. **Escalabilidade**: Sistema automatizado de coleta

---

## 📚 Referências

### Psicometria Conversacional
- **Adaptive Testing Theory**: Perguntas adaptam-se às respostas anteriores
- **Item Response Theory (IRT)**: Cada pergunta revela informação diferencial
- **Conversational AI Ethics**: Frameworks de IA conversacional ética

### Exemplos de Mercado
- **Crystal Knows**: Usa LinkedIn + perguntas estratégicas
- **16Personalities**: Questionário tradicional (queremos superar isso)
- **Replika**: Conversacional mas sem foco em perfilamento

---

## ⚠️ Riscos e Mitigações

### Risco 1: Perguntas Parecerem Mecânicas
**Mitigação**:
- Usar storytelling
- Adaptar tom ao perfil
- Rotacionar templates

### Risco 2: Usuário Perceber Manipulação
**Mitigação**:
- Transparência: "Estou curioso sobre..."
- Nunca forçar resposta
- Aceitar "não sei" como válido

### Risco 3: Perguntas Não Melhorarem Análise
**Mitigação**:
- Tracking rigoroso de métricas
- A/B testing de diferentes abordagens
- Iterar baseado em dados

---

## 🎬 Próximos Passos Imediatos

1. ✅ **Aprovação do plano** (você!)
2. ⏳ **Criar `profile_gap_analyzer.py`** (primeira implementação)
3. ⏳ **Atualizar ROADMAP.md** com novo cronograma
4. ⏳ **Começar implementação**

---

**Status**: ⏳ AGUARDANDO APROVAÇÃO
**Estimativa Total**: 15-18 horas de desenvolvimento
**Prazo Sugerido**: 3 dias (Quarta a Sexta)
