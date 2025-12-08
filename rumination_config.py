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
MIN_TENSION_LEVEL = 1  # Mínimo de tension_level para processar conversa (qualquer conflito)

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
MIN_MATURITY_FOR_SYNTHESIS = 0.75  # Threshold de maturidade (75%)
MIN_EVIDENCE_FOR_SYNTHESIS = 3  # Mínimo de evidências
MIN_DAYS_FOR_SYNTHESIS = 2  # Mínimo de dias de maturação
MAX_DAYS_FOR_SYNTHESIS = 21  # Máximo - depois disso força síntese ou arquiva

# Pesos para cálculo de maturidade
MATURITY_WEIGHTS = {
    "time": 0.25,       # Tempo desde detecção
    "evidence": 0.25,   # Quantidade de evidências
    "revisit": 0.15,    # Número de revisitas
    "connection": 0.15, # Conexões com outras tensões
    "intensity": 0.20   # Força da contradição
}

# ============================================================
# FASE 5: ENTREGA
# ============================================================
INACTIVITY_THRESHOLD_HOURS = 24  # Horas de inatividade para enviar
COOLDOWN_HOURS = 48  # Horas entre entregas (2 dias)
MIN_MATURATION_DAYS = 2  # Mínimo de dias de maturação do insight

# ============================================================
# LIMITES GERAIS
# ============================================================
MAX_INSIGHTS_PER_WEEK = 2  # Máximo de insights por semana
MIN_CONVERSATIONS_FOR_RUMINATION = 5  # Conversas mínimas para começar

# ============================================================
# LOGGING
# ============================================================
ENABLE_DETAILED_LOGGING = True  # Logs detalhados para debug
LOG_ALL_PHASES = True  # Logar todas as fases no banco
