"""
Configurações do Sistema de Ruminação Cognitiva
Baseado em SISTEMA_RUMINACAO_v1.md
"""

# ============================================================
# CONFIGURAÇÃO DE USUÁRIO ADMIN
# ============================================================
ADMIN_USER_ID = "367f9e509e396d51"  # Único usuário com ruminação ativa

# ============================================================
# FASE 1: INGESTÃO
# ============================================================
MIN_EMOTIONAL_WEIGHT = 0.3  # Fragmentos abaixo disso são ignorados
MAX_FRAGMENTS_PER_CONVERSATION = 5  # Evitar extração excessiva
MIN_TENSION_LEVEL = 0.5  # Mínimo de tension_level para processar conversa (tensão moderada+)

# ============================================================
# FASE 2: DETECÇÃO DE TENSÕES
# ============================================================
MIN_INTENSITY_FOR_TENSION = 0.4  # Tensões fracas são ignoradas
MAX_OPEN_TENSIONS_PER_USER = 10  # Evitar acúmulo excessivo

# Tipos de tensão a detectar (MVP: 2 tipos principais)
TENSION_TYPES = {
    "valor_comportamento": {
        "description": "O que a pessoa DIZ valorizar vs o que FAZ",
        "pole_a_types": ["valor", "crença"],
        "pole_b_types": ["comportamento"],
        "weight": 1.0
    },
    "desejo_medo": {
        "description": "O que a pessoa QUER vs o que TEME",
        "pole_a_types": ["desejo"],
        "pole_b_types": ["medo"],
        "weight": 1.0
    }
}

# ============================================================
# FASE 3: DIGESTÃO
# ============================================================
DIGEST_INTERVAL_HOURS = 12  # Frequência do job de digestão
DAYS_TO_ARCHIVE = 14  # Dias sem evidência para arquivar tensão
MIN_EVIDENCE_RECENCY_DAYS = 7  # Evidências mais antigas que isso pesam menos

# ============================================================
# FASE 4: SÍNTESE
# ============================================================
MIN_MATURITY_FOR_SYNTHESIS = 0.55  # Threshold de maturidade (55% - reduzido de 75%)
MIN_EVIDENCE_FOR_SYNTHESIS = 2  # Mínimo de evidências (reduzido de 3)
MIN_DAYS_FOR_SYNTHESIS = 1  # Mínimo de dias de maturação (reduzido de 2)
MAX_DAYS_FOR_SYNTHESIS = 14  # Máximo - depois disso força síntese ou arquiva (reduzido de 21)

# Pesos para cálculo de maturidade
MATURITY_WEIGHTS = {
    "time": 0.15,       # Tempo desde detecção (reduzido de 0.25)
    "evidence": 0.25,   # Quantidade de evidências
    "revisit": 0.15,    # Número de revisitas
    "connection": 0.15, # Conexões com outras tensões
    "intensity": 0.30   # Força da contradição (aumentado de 0.20)
}

# ============================================================
# FASE 5: ENTREGA
# ============================================================
INACTIVITY_THRESHOLD_HOURS = 12  # Horas de inatividade para enviar (reduzido de 24)
COOLDOWN_HOURS = 24  # Horas entre entregas (1 dia - reduzido de 48)
MIN_MATURATION_DAYS = 1  # Mínimo de dias de maturação do insight (reduzido de 2)

# ============================================================
# LIMITES GERAIS
# ============================================================
MAX_INSIGHTS_PER_WEEK = 3  # Máximo de insights por semana (aumentado de 2)
MIN_CONVERSATIONS_FOR_RUMINATION = 3  # Conversas mínimas para começar (reduzido de 5)

# ============================================================
# LOGGING
# ============================================================
ENABLE_DETAILED_LOGGING = True  # Logs detalhados para debug
LOG_ALL_PHASES = True  # Logar todas as fases no banco
