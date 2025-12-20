# 🔍 Análise de Keywords e Solução para Extração de Fatos

**Data:** 2025-12-20
**Problema:** Sistema não está extraindo fatos novos (insônia, hobbies, viagens) porque o fallback regex não tem padrões para eles.

---

## 📊 1. DIAGNÓSTICO ATUAL

### Onde os Keywords Estão (2 locais)

#### A. `jung_core.py` - Método `extract_and_save_facts()` (linhas 1700-1773)
**Usado:** Apenas quando `extract_and_save_facts_v2` NÃO existe.

**Padrões atuais:**
- **TRABALHO:** profissao, empresa
- **PERSONALIDADE:** introvertido, extrovertido, ansioso, calmo, perfeccionista
- **RELACIONAMENTO:** apenas menções genéricas (minha esposa, meu pai)

**Problema:** ❌ Não tem padrões para saúde mental, hobbies, eventos, valores, crenças

#### B. `llm_fact_extractor.py` - Método `_extract_with_regex()` (linhas 316-415)
**Usado:** Como fallback quando LLM falha no parsing de JSON.

**Padrões atuais:**
- **RELACIONAMENTO:** nomes de familiares
- **TRABALHO:** profissao, empresa
- **PERSONALIDADE:** introvertido, extrovertido, ansioso, calmo

**Problema:** ❌ Não tem padrões para as novas subcategorias expandidas

---

## 🎯 2. CATEGORIAS EXPANDIDAS (O QUE PRECISAMOS COBRIR)

### RELACIONAMENTO (vida pessoal completa)

#### Pessoas (✅ JÁ FUNCIONA)
```
minha esposa Ana
meu filho João de 12 anos
```

#### Personalidade (⚠️ PARCIAL)
```
sou introvertido              → traço=introvertido ✅
família é tudo para mim       → valor=familia ❌ FALTA
acredito em terapia           → crenca=terapia ❌ FALTA
me acho incompetente          → autoimagem=incompetente ❌ FALTA
```

#### Saúde Mental/Física (❌ NÃO FUNCIONA)
```
tenho insônia há 3 meses      → saude_mental_insonia.duracao=3 meses
sofro de ansiedade            → saude_mental_ansiedade.tipo=geral
tenho diabetes                → saude_fisica_diabetes.tipo=tipo 2
```

#### Hobbies (❌ NÃO FUNCIONA)
```
adoro ler ficção científica   → hobbie_leitura.genero=ficção científica
gosto de correr               → hobbie_exercicio.tipo=corrida
toco violão                   → hobbie_musica.instrumento=violão
```

#### Eventos/Rotinas (❌ NÃO FUNCIONA)
```
vou viajar para Paris em janeiro  → evento_viagem.destino=Paris, data=janeiro
faço aniversário dia 15 de março  → evento_aniversario.data=15/03
acordo às 6h todo dia             → rotina_matinal.horario=6h
```

### TRABALHO (vida profissional completa)

#### Profissão/Empresa (✅ JÁ FUNCIONA)
```
trabalho como designer na Google
sou desenvolvedor
```

#### Satisfação/Objetivos (❌ NÃO FUNCIONA)
```
gosto mas é estressante       → satisfacao=estressante
quero virar senior logo       → objetivo=senior
trabalho é minha prioridade   → valor=prioridade alta
```

#### Desafios/Dinâmica (❌ NÃO FUNCIONA)
```
tenho muito retrabalho        → desafio=retrabalho
chefe é microgerente          → dinamica_chefe=microgerenciamento
equipe é desorganizada        → dinamica_equipe=desorganizada
```

---

## 🛠️ 3. SOLUÇÃO: EXPANDIR REGEX FALLBACK

### Estratégia

1. **Prioridade 1:** Expandir `_extract_with_regex()` em `llm_fact_extractor.py` (é o fallback ativo)
2. **Prioridade 2:** Atualizar `extract_and_save_facts()` em `jung_core.py` (compatibilidade)

### Novos Padrões Regex Necessários

#### Para RELACIONAMENTO:

```python
# VALORES PESSOAIS
valores_patterns = {
    'familia': ['família é tudo', 'família em primeiro', 'priorizo família'],
    'saude': ['saúde é importante', 'cuido da saúde', 'priorizo saúde'],
    'relacionamentos': ['amigos são importantes', 'valorizo amizades'],
    'crescimento': ['busco crescer', 'desenvolvimento pessoal'],
}

# CRENÇAS
crencas_patterns = {
    'terapia': ['acredito em terapia', 'faço terapia', 'terapia ajuda'],
    'espiritualidade': ['acredito em Deus', 'sou religioso', 'tenho fé'],
    'autoajuda': ['acredito em desenvolvimento', 'faço meditação'],
}

# SAÚDE MENTAL
saude_mental_patterns = [
    (r'tenho (insônia|ansiedade|depressão|síndrome do pânico)', 'tipo'),
    (r'(insônia|ansiedade|depressão) há (\d+) (?:meses|anos|semanas)', 'duracao'),
    (r'sofro (?:de|com) (ansiedade|depressão|insônia)', 'tipo'),
    (r'faço tratamento para (ansiedade|depressão)', 'tratamento'),
]

# SAÚDE FÍSICA
saude_fisica_patterns = [
    (r'tenho (diabetes|hipertensão|asma|enxaqueca)', 'condicao'),
    (r'sou (diabético|hipertenso|asmático)', 'condicao'),
]

# HOBBIES - LEITURA
hobbie_leitura_patterns = [
    (r'adoro ler (ficção científica|romance|autoajuda|biografia)', 'genero'),
    (r'gosto de ler ([^.,!?]+)', 'genero'),
    (r'(Isaac Asimov|Stephen King|[A-Z][a-z]+ [A-Z][a-z]+) é meu (?:autor )?favorito', 'autor_favorito'),
    (r'leio (?:antes de dormir|todo dia|aos finais de semana)', 'frequencia'),
]

# HOBBIES - EXERCÍCIO
hobbie_exercicio_patterns = [
    (r'gosto de (correr|nadar|pedalar|fazer yoga|musculação)', 'tipo'),
    (r'pratico (corrida|natação|ciclismo|yoga)', 'tipo'),
    (r'corro (\d+ (?:vezes|x) por semana)', 'frequencia'),
]

# HOBBIES - MÚSICA
hobbie_musica_patterns = [
    (r'toco (violão|guitarra|piano|bateria)', 'instrumento'),
    (r'gosto de (rock|jazz|clássica|sertanejo)', 'genero'),
]

# EVENTOS - VIAGEM
evento_viagem_patterns = [
    (r'vou viajar para ([A-Z][a-záéíóúâêôãõç]+) em (janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)', 'destino_data'),
    (r'viagem para ([A-Z][a-záéíóúâêôãõç]+)', 'destino'),
    (r'primeira vez n[ao] ([A-Z][a-záéíóúâêôãõç]+)', 'planejamento'),
]

# ROTINAS
rotina_patterns = [
    (r'acordo às? (\d{1,2}h?\d{0,2})', 'matinal_horario'),
    (r'durmo às? (\d{1,2}h?\d{0,2})', 'noturna_horario'),
    (r'(?:leio|medito|corro) (?:antes de dormir|todo dia|de manhã)', 'habito'),
]
```

#### Para TRABALHO:

```python
# SATISFAÇÃO
satisfacao_patterns = {
    'positiva': ['adoro meu trabalho', 'gosto do trabalho', 'satisfeito'],
    'neutra': ['trabalho é ok', 'não amo mas não odeio'],
    'negativa': ['odeio meu trabalho', 'estressante', 'cansativo', 'frustrante'],
}

# OBJETIVOS
objetivo_patterns = [
    (r'quero (?:virar|ser|me tornar) (senior|pleno|gerente|diretor)', 'cargo'),
    (r'objetivo é (mudar de área|crescer|liderar)', 'tipo'),
    (r'sonho em trabalhar n[ao] ([^.,!?]+)', 'empresa_sonho'),
]

# DESAFIOS
desafio_trabalho_patterns = {
    'retrabalho': ['muito retrabalho', 'refaço coisas'],
    'pressao': ['muita pressão', 'prazos apertados', 'cobrança'],
    'sobrecarga': ['muito trabalho', 'sobrecarregado', 'horas extras'],
    'desorganizacao': ['falta organização', 'equipe desorganizada'],
}

# DINÂMICA COM CHEFE
dinamica_chefe_patterns = {
    'microgerenciamento': ['chefe é microgerente', 'controla tudo', 'não dá autonomia'],
    'ausente': ['chefe sumido', 'falta direção', 'não dá feedback'],
    'apoiador': ['chefe me apoia', 'bom líder', 'me ajuda'],
}

# DINÂMICA COM EQUIPE
dinamica_equipe_patterns = {
    'colaborativa': ['equipe unida', 'trabalhamos bem juntos'],
    'conflituosa': ['muita briga', 'discussões', 'clima ruim'],
    'desorganizada': ['equipe desorganizada', 'falta alinhamento'],
}
```

---

## 💻 4. IMPLEMENTAÇÃO - CÓDIGO COMPLETO

### Arquivo: `llm_fact_extractor.py`

**Substituir método `_extract_with_regex()` (linhas 316-415):**

```python
def _extract_with_regex(self, user_input: str) -> List[ExtractedFact]:
    """
    Fallback: Extração usando regex (método expandido para 2 categorias completas)
    """
    logger.info("   🔄 Usando fallback regex...")

    facts = []
    input_lower = user_input.lower()

    # =====================================
    # RELACIONAMENTO - VIDA PESSOAL
    # =====================================

    # 1. PESSOAS (nomes de familiares)
    relationship_with_name = [
        (r'minh[ao] (esposa|marido|namorad[ao]|companheiro|companheira) (?:se chama|é|:)?\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)', 'relationship'),
        (r'(?:tenho|meu|minha) (filho|filha) (?:se chama|é|:)?\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)', 'relationship'),
        (r'(?:meu|minha) (pai|mãe|irmão|irmã|avô|avó) (?:se chama|é|:)?\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)', 'relationship'),
    ]

    for pattern, category in relationship_with_name:
        matches = re.finditer(pattern, user_input, re.IGNORECASE)
        for match in matches:
            relationship_type = match.group(1).lower()
            name = match.group(2)
            facts.append(ExtractedFact(
                category="RELACIONAMENTO",
                fact_type=relationship_type,
                attribute="nome",
                value=name,
                confidence=0.9,
                context=match.group(0)
            ))

    # 2. VALORES PESSOAIS
    valores_patterns = {
        'familia': ['família é tudo', 'família em primeiro', 'priorizo família', 'família é importante'],
        'saude': ['saúde é importante', 'cuido da saúde', 'priorizo saúde'],
        'amizade': ['amigos são importantes', 'valorizo amizades', 'amizade é essencial'],
    }

    for valor, patterns in valores_patterns.items():
        if any(p in input_lower for p in patterns):
            facts.append(ExtractedFact(
                category="RELACIONAMENTO",
                fact_type="valor",
                attribute=valor,
                value="sim",
                confidence=0.8,
                context=user_input[:100]
            ))

    # 3. CRENÇAS
    crencas_patterns = {
        'terapia': ['acredito em terapia', 'faço terapia', 'terapia ajuda', 'acompanhamento psicológico'],
        'espiritualidade': ['acredito em Deus', 'sou religioso', 'tenho fé', 'sou católico', 'sou evangélico'],
        'meditacao': ['faço meditação', 'medito', 'mindfulness'],
    }

    for crenca, patterns in crencas_patterns.items():
        if any(p in input_lower for p in patterns):
            facts.append(ExtractedFact(
                category="RELACIONAMENTO",
                fact_type="crenca",
                attribute=crenca,
                value="pratica" if "faço" in input_lower or "pratico" in input_lower else "acredita",
                confidence=0.8,
                context=user_input[:100]
            ))

    # 4. SAÚDE MENTAL
    saude_mental_patterns = [
        (r'tenho (insônia|ansiedade|depressão|síndrome do pânico|burnout)', 'tipo'),
        (r'sofro (?:de|com) (ansiedade|depressão|insônia|estresse crônico)', 'tipo'),
        (r'(insônia|ansiedade|depressão) há (\d+) (?:meses|anos|semanas|dias)', 'duracao'),
    ]

    for pattern, attr_type in saude_mental_patterns:
        matches = re.finditer(pattern, input_lower)
        for match in matches:
            if attr_type == 'tipo':
                condicao = match.group(1)
                facts.append(ExtractedFact(
                    category="RELACIONAMENTO",
                    fact_type=f"saude_mental_{condicao}",
                    attribute="tipo",
                    value=condicao,
                    confidence=0.85,
                    context=match.group(0)
                ))
            elif attr_type == 'duracao':
                condicao = match.group(1)
                tempo = match.group(2)
                facts.append(ExtractedFact(
                    category="RELACIONAMENTO",
                    fact_type=f"saude_mental_{condicao}",
                    attribute="duracao",
                    value=f"{tempo} (período mencionado)",
                    confidence=0.85,
                    context=match.group(0)
                ))

    # 5. SAÚDE FÍSICA
    saude_fisica_patterns = [
        (r'tenho (diabetes|hipertensão|asma|enxaqueca|colesterol alto)', 'condicao'),
        (r'sou (diabético|hipertenso|asmático)', 'condicao'),
    ]

    for pattern, attr_type in saude_fisica_patterns:
        match = re.search(pattern, input_lower)
        if match:
            condicao = match.group(1)
            facts.append(ExtractedFact(
                category="RELACIONAMENTO",
                fact_type=f"saude_fisica_{condicao}",
                attribute="tipo",
                value=condicao,
                confidence=0.85,
                context=match.group(0)
            ))

    # 6. HOBBIES - LEITURA
    hobbie_leitura_patterns = [
        (r'adoro ler (ficção científica|romance|autoajuda|biografia|fantasia|poesia)', 'genero'),
        (r'gosto de ler (ficção científica|romance|autoajuda|biografia|fantasia)', 'genero'),
        (r'(Isaac Asimov|Stephen King|Machado de Assis|[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+ [A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+) é meu (?:autor )?favorito', 'autor'),
    ]

    for pattern, attr_type in hobbie_leitura_patterns:
        match = re.search(pattern, input_lower if attr_type == 'genero' else user_input)
        if match:
            value = match.group(1)
            facts.append(ExtractedFact(
                category="RELACIONAMENTO",
                fact_type="hobbie_leitura",
                attribute=attr_type,
                value=value,
                confidence=0.8,
                context=match.group(0)
            ))

    # Frequência de leitura
    if any(p in input_lower for p in ['leio antes de dormir', 'leio todo dia', 'leio aos finais de semana']):
        freq = "antes de dormir" if "antes de dormir" in input_lower else \
               "diariamente" if "todo dia" in input_lower else \
               "fins de semana"
        facts.append(ExtractedFact(
            category="RELACIONAMENTO",
            fact_type="hobbie_leitura",
            attribute="frequencia",
            value=freq,
            confidence=0.75,
            context=user_input[:100]
        ))

    # 7. HOBBIES - EXERCÍCIO
    hobbie_exercicio_patterns = [
        (r'gosto de (correr|nadar|pedalar|fazer yoga|musculação|caminhar)', 'tipo'),
        (r'pratico (corrida|natação|ciclismo|yoga|musculação|caminhada)', 'tipo'),
    ]

    for pattern, attr_type in hobbie_exercicio_patterns:
        match = re.search(pattern, input_lower)
        if match:
            tipo = match.group(1)
            facts.append(ExtractedFact(
                category="RELACIONAMENTO",
                fact_type="hobbie_exercicio",
                attribute="tipo",
                value=tipo,
                confidence=0.8,
                context=match.group(0)
            ))

    # 8. HOBBIES - MÚSICA
    hobbie_musica_patterns = [
        (r'toco (violão|guitarra|piano|bateria|flauta|saxofone)', 'instrumento'),
        (r'gosto de (?:música |som )?(?:de )?(rock|jazz|clássica|sertanejo|mpb|pop)', 'genero'),
    ]

    for pattern, attr_type in hobbie_musica_patterns:
        match = re.search(pattern, input_lower)
        if match:
            value = match.group(1)
            facts.append(ExtractedFact(
                category="RELACIONAMENTO",
                fact_type="hobbie_musica",
                attribute=attr_type,
                value=value,
                confidence=0.8,
                context=match.group(0)
            ))

    # 9. EVENTOS - VIAGEM
    evento_viagem_patterns = [
        (r'vou viajar para ([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+) em (janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)', 'destino_e_data'),
        (r'viagem para ([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)', 'destino'),
    ]

    for pattern, attr_type in evento_viagem_patterns:
        match = re.search(pattern, user_input)  # Usar user_input para pegar maiúsculas
        if match:
            if attr_type == 'destino_e_data':
                destino = match.group(1)
                mes = match.group(2)
                facts.append(ExtractedFact(
                    category="RELACIONAMENTO",
                    fact_type="evento_viagem",
                    attribute="destino",
                    value=destino,
                    confidence=0.85,
                    context=match.group(0)
                ))
                facts.append(ExtractedFact(
                    category="RELACIONAMENTO",
                    fact_type="evento_viagem",
                    attribute="data",
                    value=mes,
                    confidence=0.85,
                    context=match.group(0)
                ))
            else:
                destino = match.group(1)
                facts.append(ExtractedFact(
                    category="RELACIONAMENTO",
                    fact_type="evento_viagem",
                    attribute="destino",
                    value=destino,
                    confidence=0.8,
                    context=match.group(0)
                ))

    # Planejamento de viagem
    if 'primeira vez' in input_lower:
        facts.append(ExtractedFact(
            category="RELACIONAMENTO",
            fact_type="evento_viagem",
            attribute="planejamento",
            value="primeira vez",
            confidence=0.75,
            context=user_input[:100]
        ))

    # Sentimento sobre viagem
    sentimentos_viagem = {
        'ansioso': ['ansioso', 'nervoso'],
        'empolgado': ['empolgado', 'animado', 'feliz'],
    }
    for sentimento, keywords in sentimentos_viagem.items():
        if any(k in input_lower for k in keywords):
            facts.append(ExtractedFact(
                category="RELACIONAMENTO",
                fact_type="evento_viagem",
                attribute="sentimento",
                value=sentimento,
                confidence=0.7,
                context=user_input[:100]
            ))

    # 10. PERSONALIDADE (traços básicos)
    personality_patterns = {
        'introvertido': ['sou introvertido', 'prefiro ficar sozinho', 'evito eventos sociais'],
        'extrovertido': ['sou extrovertido', 'gosto de pessoas', 'adoro festas'],
        'ansioso': ['sou ansioso', 'fico ansioso com tudo'],
        'calmo': ['sou calmo', 'sou tranquilo', 'pessoa zen'],
    }

    for trait, patterns in personality_patterns.items():
        if any(p in input_lower for p in patterns):
            facts.append(ExtractedFact(
                category="RELACIONAMENTO",
                fact_type="personalidade",
                attribute="traço",
                value=trait,
                confidence=0.75,
                context=user_input[:100]
            ))

    # =====================================
    # TRABALHO - VIDA PROFISSIONAL
    # =====================================

    # 1. PROFISSÃO E EMPRESA (já funcionava)
    work_patterns = [
        (r'trabalho como ([^.,!?]+?)(?:\.|,|no|na|em)', 'profissao'),
        (r'sou (engenheiro|médico|professor|advogado|desenvolvedor|designer|gerente|analista|arquiteto)', 'profissao'),
        (r'trabalho n[ao] ([^.,!?]+?)(?:\.|,|como)', 'empresa'),
    ]

    for pattern, attr in work_patterns:
        match = re.search(pattern, input_lower)
        if match:
            value = match.group(1).strip()
            facts.append(ExtractedFact(
                category="TRABALHO",
                fact_type=attr,
                attribute="valor",
                value=value,
                confidence=0.8,
                context=match.group(0)
            ))

    # 2. SATISFAÇÃO
    satisfacao_patterns = {
        'positiva': ['adoro meu trabalho', 'gosto do trabalho', 'satisfeito com trabalho', 'amo meu trabalho'],
        'neutra': ['trabalho é ok', 'não amo mas não odeio', 'trabalho normal'],
        'negativa': ['odeio meu trabalho', 'muito estressante', 'cansativo', 'frustrante', 'trabalho ruim'],
    }

    for nivel, patterns in satisfacao_patterns.items():
        if any(p in input_lower for p in patterns):
            facts.append(ExtractedFact(
                category="TRABALHO",
                fact_type="satisfacao",
                attribute="nivel",
                value=nivel,
                confidence=0.75,
                context=user_input[:100]
            ))
            break  # Pegar apenas a primeira

    # 3. OBJETIVOS PROFISSIONAIS
    objetivo_patterns = [
        (r'quero (?:virar|ser|me tornar) (senior|pleno|júnior|gerente|diretor|tech lead)', 'cargo'),
        (r'objetivo é (mudar de área|crescer|liderar equipe|empreender)', 'tipo'),
        (r'sonho em trabalhar n[ao] ([^.,!?]+)', 'empresa_sonho'),
    ]

    for pattern, attr_type in objetivo_patterns:
        match = re.search(pattern, input_lower)
        if match:
            value = match.group(1)
            facts.append(ExtractedFact(
                category="TRABALHO",
                fact_type="objetivo",
                attribute=attr_type,
                value=value,
                confidence=0.8,
                context=match.group(0)
            ))

    # 4. DESAFIOS NO TRABALHO
    desafio_patterns = {
        'retrabalho': ['muito retrabalho', 'refaço coisas', 'sempre mudando'],
        'pressao': ['muita pressão', 'prazos apertados', 'muita cobrança'],
        'sobrecarga': ['muito trabalho', 'sobrecarregado', 'horas extras', 'trabalho demais'],
        'desorganizacao': ['falta organização', 'equipe desorganizada', 'caos'],
    }

    for desafio, patterns in desafio_patterns.items():
        if any(p in input_lower for p in patterns):
            facts.append(ExtractedFact(
                category="TRABALHO",
                fact_type="desafio",
                attribute="tipo",
                value=desafio,
                confidence=0.75,
                context=user_input[:100]
            ))

    # 5. TEMPO NA EMPRESA/CARGO
    tempo_patterns = [
        (r'(?:trabalho|estou) (?:há|ha|a) (\d+) (?:anos|meses)', 'tempo'),
        (r'(?:há|ha|a) (\d+) (?:anos|meses) n[ao]', 'tempo'),
    ]

    for pattern, attr_type in tempo_patterns:
        match = re.search(pattern, input_lower)
        if match:
            tempo = match.group(1)
            facts.append(ExtractedFact(
                category="TRABALHO",
                fact_type="tempo",
                attribute="duracao",
                value=f"{tempo} (período mencionado)",
                confidence=0.8,
                context=match.group(0)
            ))

    # =====================================
    # RETORNO
    # =====================================

    if facts:
        logger.info(f"   ✅ Regex extraiu {len(facts)} fatos")
        for fact in facts:
            logger.debug(f"      {fact.category}.{fact.fact_type}.{fact.attribute} = {fact.value}")
    else:
        logger.info(f"   ℹ️ Nenhum fato extraído via regex")

    return facts
```

---

## 🧪 5. TESTES NECESSÁRIOS

Após implementação, testar via Telegram ou endpoint:

```
1. Insônia: "Tenho insônia há 3 meses"
   Esperado: RELACIONAMENTO.saude_mental_insonia.tipo=insônia
             RELACIONAMENTO.saude_mental_insonia.duracao=3 (período mencionado)

2. Leitura: "Adoro ler ficção científica antes de dormir"
   Esperado: RELACIONAMENTO.hobbie_leitura.genero=ficção científica
             RELACIONAMENTO.hobbie_leitura.frequencia=antes de dormir

3. Viagem: "Vou viajar para Paris em janeiro"
   Esperado: RELACIONAMENTO.evento_viagem.destino=Paris
             RELACIONAMENTO.evento_viagem.data=janeiro

4. Valores: "Família é tudo para mim"
   Esperado: RELACIONAMENTO.valor.familia=sim

5. Satisfação: "Gosto mas é muito estressante"
   Esperado: TRABALHO.satisfacao.nivel=negativa

6. Objetivo: "Quero virar senior logo"
   Esperado: TRABALHO.objetivo.cargo=senior
```

---

## ✅ 6. CHECKLIST DE IMPLEMENTAÇÃO

- [ ] Substituir método `_extract_with_regex()` em `llm_fact_extractor.py`
- [ ] Commit e push para Railway
- [ ] Aguardar deploy (2-3 min)
- [ ] Testar mensagem: "Tenho insônia há 3 meses"
- [ ] Verificar logs: `✅ Regex extraiu X fatos`
- [ ] Verificar endpoint: `GET /admin/facts-v2/list`
- [ ] Testar mensagem: "Adoro ler ficção científica"
- [ ] Testar mensagem: "Vou viajar para Paris em janeiro"
- [ ] Confirmar fatos salvos no banco

---

## 🎯 7. RESULTADO ESPERADO

### Antes (Estado atual):
```
Mensagem: "Tenho insônia há 3 meses"
Log: ❌ Erro no LLM: '\n  "fatos"', usando fallback regex
Log: ℹ️ Nenhum fato extraído
```

### Depois (Com nova implementação):
```
Mensagem: "Tenho insônia há 3 meses"
Log: 🔄 Usando fallback regex...
Log: ✅ Regex extraiu 2 fatos
     RELACIONAMENTO.saude_mental_insonia.tipo = insônia
     RELACIONAMENTO.saude_mental_insonia.duracao = 3 (período mencionado)
Log: 📝 [FACTS V2] Salvando: RELACIONAMENTO.saude_mental_insonia.tipo = insônia
Log: ✅ Fato salvo com sucesso
```

---

**Próximo passo:** Implementar o código acima e fazer push para Railway.
