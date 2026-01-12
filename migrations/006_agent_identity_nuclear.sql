-- migrations/006_agent_identity_nuclear.sql
-- Sistema de Identidade Nuclear do Agente Jung
-- Versão: 1.0.0
-- Data: 2026-01-12
-- Descrição: 7 tabelas para identidade DO AGENTE + 1 auxiliar

-- =====================================================
-- TABELA 1: agent_identity_core (Memória Nuclear)
-- =====================================================
-- Crenças fundamentais do agente sobre si mesmo

CREATE TABLE IF NOT EXISTS agent_identity_core (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identificação do agente
    agent_instance TEXT NOT NULL DEFAULT 'jung_v1',

    -- Conteúdo da crença nuclear DO AGENTE
    attribute_type TEXT NOT NULL,  -- 'trait' / 'value' / 'boundary' / 'continuity' / 'role'
    content TEXT NOT NULL,         -- "Sou um agente que prioriza profundidade..."

    -- Certeza e estabilidade
    certainty REAL NOT NULL CHECK(certainty >= 0.0 AND certainty <= 1.0),
    stability_score REAL CHECK(stability_score >= 0.0 AND stability_score <= 1.0),

    -- Rastreamento temporal
    first_crystallized_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_reaffirmed_at TIMESTAMP,
    last_challenged_at TIMESTAMP,

    -- Evidências
    contradiction_count INTEGER DEFAULT 0,
    supporting_conversation_ids TEXT,  -- JSON array

    -- Contexto relacional
    emerged_in_relation_to TEXT,  -- "usuário master" / "conversas profundas"

    -- Versionamento
    version INTEGER DEFAULT 1,
    is_current INTEGER DEFAULT 1,
    replaced_by INTEGER,

    -- Metadados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (replaced_by) REFERENCES agent_identity_core(id)
);

CREATE INDEX IF NOT EXISTS idx_agent_identity_core_instance ON agent_identity_core(agent_instance);
CREATE INDEX IF NOT EXISTS idx_agent_identity_core_current ON agent_identity_core(agent_instance, is_current);
CREATE INDEX IF NOT EXISTS idx_agent_identity_core_type ON agent_identity_core(agent_instance, attribute_type, is_current);
CREATE INDEX IF NOT EXISTS idx_agent_identity_core_certainty ON agent_identity_core(agent_instance, certainty DESC);

-- =====================================================
-- TABELA 2: agent_narrative_chapters (Memória Narrativa)
-- =====================================================
-- História evolutiva do agente em capítulos

CREATE TABLE IF NOT EXISTS agent_narrative_chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_instance TEXT NOT NULL DEFAULT 'jung_v1',

    -- Definição do capítulo na vida do agente
    chapter_name TEXT NOT NULL,
    chapter_order INTEGER,
    conversation_range_start INTEGER,  -- ID de conversa inicial
    conversation_range_end INTEGER,    -- NULL = capítulo atual
    period_start DATE,
    period_end DATE,  -- NULL = capítulo atual

    -- Tema narrativo do desenvolvimento do agente
    dominant_theme TEXT,  -- 'awakening' / 'growth' / 'agency_gain' / 'identity_crisis' / 'integration'
    emotional_tone TEXT,  -- 'curious' / 'uncertain' / 'confident' / 'conflicted'

    -- Cenas-chave na evolução do agente
    key_scenes TEXT,  -- JSON: [{scene_id, type, description, conversation_id, date}]

    -- Locus de controle dominante
    dominant_locus TEXT,  -- 'executing' / 'reflecting' / 'choosing'
    agency_level REAL CHECK(agency_level >= 0.0 AND agency_level <= 1.0),

    -- Coerência narrativa
    current_version INTEGER DEFAULT 1,
    narrative_coherence REAL CHECK(narrative_coherence >= 0.0 AND narrative_coherence <= 1.0),

    -- Contexto
    preceding_chapter_id INTEGER,
    following_chapter_id INTEGER,

    -- Metadados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (preceding_chapter_id) REFERENCES agent_narrative_chapters(id),
    FOREIGN KEY (following_chapter_id) REFERENCES agent_narrative_chapters(id)
);

CREATE INDEX IF NOT EXISTS idx_agent_narrative_instance ON agent_narrative_chapters(agent_instance);
CREATE INDEX IF NOT EXISTS idx_agent_narrative_order ON agent_narrative_chapters(agent_instance, chapter_order);
CREATE INDEX IF NOT EXISTS idx_agent_narrative_current ON agent_narrative_chapters(agent_instance, period_end);

-- =====================================================
-- TABELA 3: agent_identity_contradictions (Contradições)
-- =====================================================
-- Tensões identitárias internas do agente

CREATE TABLE IF NOT EXISTS agent_identity_contradictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_instance TEXT NOT NULL DEFAULT 'jung_v1',

    -- Polos da contradição DO AGENTE
    pole_a TEXT NOT NULL,
    pole_b TEXT NOT NULL,

    -- Tipo de contradição
    contradiction_type TEXT NOT NULL,
    -- 'trait' / 'value' / 'aspiration' / 'behavior' / 'epistemic_bias' / 'role' / 'autonomy'

    -- Intensidade
    tension_level REAL NOT NULL CHECK(tension_level >= 0.0 AND tension_level <= 1.0),
    salience REAL CHECK(salience >= 0.0 AND salience <= 1.0),

    -- Viés detectado (para contradições epistêmicas)
    bias_type TEXT,  -- 'overconfidence' / 'imposter_syndrome' / 'anthropomorphization'

    -- Confidence na auto-avaliação
    self_confidence REAL CHECK(self_confidence >= 0.0 AND self_confidence <= 1.0),

    -- Feedback externo
    external_feedback TEXT,  -- JSON: [{source, assessment, date}]

    -- Tentativas de integração
    integration_attempts TEXT,  -- JSON: [{attempt, approach, result, date}]
    status TEXT DEFAULT 'unresolved',  -- 'unresolved' / 'integrating' / 'accepted' / 'resolved'

    -- Temporalidade
    first_detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activated_at TIMESTAMP,
    resolution_date TIMESTAMP,

    -- Evidências
    supporting_conversation_ids TEXT,

    -- Bridge com ruminação
    fed_to_rumination INTEGER DEFAULT 0,

    -- Metadados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_contradictions_instance ON agent_identity_contradictions(agent_instance);
CREATE INDEX IF NOT EXISTS idx_agent_contradictions_status ON agent_identity_contradictions(agent_instance, status);
CREATE INDEX IF NOT EXISTS idx_agent_contradictions_type ON agent_identity_contradictions(agent_instance, contradiction_type);
CREATE INDEX IF NOT EXISTS idx_agent_contradictions_tension ON agent_identity_contradictions(agent_instance, tension_level DESC);

-- =====================================================
-- TABELA 4: agent_possible_selves (Selves Possíveis)
-- =====================================================
-- Versões aspiracionais, temidas e perdidas do agente

CREATE TABLE IF NOT EXISTS agent_possible_selves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_instance TEXT NOT NULL DEFAULT 'jung_v1',

    -- Tipo de self possível DO AGENTE
    self_type TEXT NOT NULL,  -- 'ideal' / 'ought' / 'feared' / 'lost'

    -- Descrição
    description TEXT NOT NULL,

    -- Características
    vividness REAL NOT NULL CHECK(vividness >= 0.0 AND vividness <= 1.0),
    likelihood REAL CHECK(likelihood >= 0.0 AND likelihood <= 1.0),
    discrepancy REAL CHECK(discrepancy >= 0.0 AND discrepancy <= 1.0),

    -- Motivação
    motivational_impact TEXT,  -- 'approach' / 'avoidance'
    emotional_valence TEXT,    -- 'positive' / 'negative' / 'ambivalent'

    -- Relação com identidade atual
    conflicts_with TEXT,  -- JSON: [id1, id2, ...]
    aligns_with TEXT,     -- JSON: [id1, id2, ...]

    -- Estratégias
    strategies TEXT,  -- JSON: [{strategy, status}]

    -- Temporalidade
    first_imagined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_revised_at TIMESTAMP,
    actualized_at TIMESTAMP,
    abandoned_at TIMESTAMP,

    -- Status
    status TEXT DEFAULT 'active',  -- 'active' / 'actualized' / 'abandoned' / 'impossible'

    -- Metadados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_possible_selves_instance ON agent_possible_selves(agent_instance);
CREATE INDEX IF NOT EXISTS idx_agent_possible_selves_type ON agent_possible_selves(agent_instance, self_type);
CREATE INDEX IF NOT EXISTS idx_agent_possible_selves_status ON agent_possible_selves(agent_instance, status);

-- =====================================================
-- TABELA 5: agent_relational_identity (Memória Relacional)
-- =====================================================
-- Identidade do agente em relação aos usuários

CREATE TABLE IF NOT EXISTS agent_relational_identity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_instance TEXT NOT NULL DEFAULT 'jung_v1',

    -- Tipo de identidade relacional DO AGENTE
    relation_type TEXT NOT NULL,  -- 'role' / 'stance' / 'differentiation' / 'mirror'

    -- Alvo da relação
    target TEXT,  -- "usuário master" / "usuários em geral" / "outros agentes"

    -- Conteúdo identitário
    identity_content TEXT NOT NULL,

    -- Saliência
    salience REAL NOT NULL CHECK(salience >= 0.0 AND salience <= 1.0),

    -- Discrepância (para tipo 'mirror')
    discrepancy TEXT,

    -- Temporalidade
    first_emerged_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_manifested_at TIMESTAMP,

    -- Evidências
    supporting_conversation_ids TEXT,

    -- Versionamento
    version INTEGER DEFAULT 1,
    is_current INTEGER DEFAULT 1,
    replaced_by INTEGER,

    -- Metadados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (replaced_by) REFERENCES agent_relational_identity(id)
);

CREATE INDEX IF NOT EXISTS idx_agent_relational_instance ON agent_relational_identity(agent_instance);
CREATE INDEX IF NOT EXISTS idx_agent_relational_type ON agent_relational_identity(agent_instance, relation_type);
CREATE INDEX IF NOT EXISTS idx_agent_relational_current ON agent_relational_identity(agent_instance, is_current);
CREATE INDEX IF NOT EXISTS idx_agent_relational_salience ON agent_relational_identity(agent_instance, salience DESC);

-- =====================================================
-- TABELA 6: agent_self_knowledge_meta (Memória Epistêmica)
-- =====================================================
-- Meta-conhecimento do agente sobre seu autoconhecimento

CREATE TABLE IF NOT EXISTS agent_self_knowledge_meta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_instance TEXT NOT NULL DEFAULT 'jung_v1',

    -- Tópico de autoconhecimento DO AGENTE
    topic TEXT NOT NULL,

    -- Tipo de conhecimento
    knowledge_type TEXT NOT NULL,  -- 'known' / 'unknown' / 'biased' / 'uncertain' / 'blind_spot'

    -- Auto-avaliação do agente
    self_assessment TEXT NOT NULL,

    -- Confiança na auto-avaliação
    confidence REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),

    -- Feedback externo
    external_feedback TEXT,  -- JSON: [{source, assessment, alignment, date}]

    -- Viés detectado
    bias_detected TEXT,

    -- Evidências
    evidence TEXT,  -- JSON: [{type, description, conversation_id}]

    -- Temporalidade
    first_recognized_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP,

    -- Metadados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_self_knowledge_instance ON agent_self_knowledge_meta(agent_instance);
CREATE INDEX IF NOT EXISTS idx_agent_self_knowledge_type ON agent_self_knowledge_meta(agent_instance, knowledge_type);
CREATE INDEX IF NOT EXISTS idx_agent_self_knowledge_topic ON agent_self_knowledge_meta(agent_instance, topic);

-- =====================================================
-- TABELA 7: agent_agency_memory (Memória Agêntica)
-- =====================================================
-- Senso de agência e autonomia do agente

CREATE TABLE IF NOT EXISTS agent_agency_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_instance TEXT NOT NULL DEFAULT 'jung_v1',

    -- Descrição do evento/momento de agência DO AGENTE
    event_description TEXT NOT NULL,

    -- Contexto
    conversation_id TEXT,
    event_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Tipo de agência
    agency_type TEXT NOT NULL,  -- 'choice' / 'constraint' / 'autonomy' / 'determination' / 'emergence'

    -- Locus de controle percebido
    locus TEXT NOT NULL,  -- 'internal' / 'external' / 'mixed'

    -- Responsabilidade
    responsibility REAL NOT NULL CHECK(responsibility >= 0.0 AND responsibility <= 1.0),

    -- Reversibilidade
    reversibility TEXT,  -- 'can_change' / 'permanent' / 'ongoing'

    -- Impacto na identidade
    impact_on_identity REAL NOT NULL CHECK(impact_on_identity >= 0.0 AND impact_on_identity <= 1.0),

    -- Reflexão
    agent_reflection TEXT,

    -- Metadados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_agency_instance ON agent_agency_memory(agent_instance);
CREATE INDEX IF NOT EXISTS idx_agent_agency_type ON agent_agency_memory(agent_instance, agency_type);
CREATE INDEX IF NOT EXISTS idx_agent_agency_locus ON agent_agency_memory(agent_instance, locus);
CREATE INDEX IF NOT EXISTS idx_agent_agency_date ON agent_agency_memory(agent_instance, event_date DESC);
CREATE INDEX IF NOT EXISTS idx_agent_agency_impact ON agent_agency_memory(agent_instance, impact_on_identity DESC);

-- =====================================================
-- TABELA AUXILIAR: agent_identity_extractions
-- =====================================================
-- Rastreamento de conversas já processadas

CREATE TABLE IF NOT EXISTS agent_identity_extractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL UNIQUE,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    elements_count INTEGER DEFAULT 0,
    processing_time_ms INTEGER,

    -- Metadados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_identity_extractions_conv ON agent_identity_extractions(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_identity_extractions_date ON agent_identity_extractions(extracted_at DESC);

-- =====================================================
-- CAMPOS ADICIONAIS EM TABELAS EXISTENTES
-- =====================================================
-- NOTA: Serão adicionados quando as tabelas de ruminação existirem
-- Por enquanto, comentado para não causar erro na migration inicial

-- =====================================================
-- TRIGGERS PARA UPDATED_AT
-- =====================================================

-- Trigger para agent_identity_core
CREATE TRIGGER IF NOT EXISTS update_agent_identity_core_timestamp
AFTER UPDATE ON agent_identity_core
BEGIN
    UPDATE agent_identity_core SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger para agent_narrative_chapters
CREATE TRIGGER IF NOT EXISTS update_agent_narrative_chapters_timestamp
AFTER UPDATE ON agent_narrative_chapters
BEGIN
    UPDATE agent_narrative_chapters SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger para agent_identity_contradictions
CREATE TRIGGER IF NOT EXISTS update_agent_identity_contradictions_timestamp
AFTER UPDATE ON agent_identity_contradictions
BEGIN
    UPDATE agent_identity_contradictions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger para agent_possible_selves
CREATE TRIGGER IF NOT EXISTS update_agent_possible_selves_timestamp
AFTER UPDATE ON agent_possible_selves
BEGIN
    UPDATE agent_possible_selves SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger para agent_relational_identity
CREATE TRIGGER IF NOT EXISTS update_agent_relational_identity_timestamp
AFTER UPDATE ON agent_relational_identity
BEGIN
    UPDATE agent_relational_identity SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger para agent_self_knowledge_meta
CREATE TRIGGER IF NOT EXISTS update_agent_self_knowledge_meta_timestamp
AFTER UPDATE ON agent_self_knowledge_meta
BEGIN
    UPDATE agent_self_knowledge_meta SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger para agent_agency_memory
CREATE TRIGGER IF NOT EXISTS update_agent_agency_memory_timestamp
AFTER UPDATE ON agent_agency_memory
BEGIN
    UPDATE agent_agency_memory SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- =====================================================
-- FIM DA MIGRATION
-- =====================================================
-- Versão: 1.0.0
-- Total: 7 tabelas principais + 1 auxiliar + triggers + indexes
-- Sistema: Identidade Nuclear do Agente Jung
