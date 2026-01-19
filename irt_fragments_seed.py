"""
irt_fragments_seed.py

Seed de 150 fragmentos comportamentais para o Sistema TRI.
Baseado em Costa & McCrae (1992) - NEO-PI-R
Estrutura: 5 domínios × 6 facetas × 5 fragmentos = 150 fragmentos

Referência: Costa & McCrae (1992), Appendix B
"""

import json
from typing import List, Dict

# ========================================
# EXTRAVERSION (E) - 30 fragmentos
# ========================================

EXTRAVERSION_FRAGMENTS = [
    # E1: Warmth (Acolhimento) - 5 fragmentos
    {
        "fragment_id": "EXT_E1_001",
        "domain": "Extraversion",
        "facet": "E1: Warmth",
        "facet_code": "E1",
        "description": "Expressa afeto genuíno e caloroso por pessoas próximas",
        "description_en": "Expresses genuine warmth and affection for close ones",
        "detection_pattern": "Detectar quando usuário demonstra carinho, afeto ou preocupação genuína com pessoas",
        "example_phrases": json.dumps(["amo minha família", "adoro meus amigos", "me importo muito com", "tenho carinho por"])
    },
    {
        "fragment_id": "EXT_E1_002",
        "domain": "Extraversion",
        "facet": "E1: Warmth",
        "facet_code": "E1",
        "description": "Demonstra interesse genuíno pelo bem-estar dos outros",
        "description_en": "Shows genuine interest in others' well-being",
        "detection_pattern": "Detectar preocupação com bem-estar alheio",
        "example_phrases": json.dumps(["como ela está?", "espero que ele melhore", "fico preocupado com", "quero ajudar"])
    },
    {
        "fragment_id": "EXT_E1_003",
        "domain": "Extraversion",
        "facet": "E1: Warmth",
        "facet_code": "E1",
        "description": "Faz elogios e expressa apreciação por outros",
        "description_en": "Gives compliments and expresses appreciation",
        "detection_pattern": "Detectar elogios e expressões de apreciação",
        "example_phrases": json.dumps(["ela é incrível", "admiro muito", "gosto do jeito que", "valorizo muito"])
    },
    {
        "fragment_id": "EXT_E1_004",
        "domain": "Extraversion",
        "facet": "E1: Warmth",
        "facet_code": "E1",
        "description": "Busca conexão emocional nas interações",
        "description_en": "Seeks emotional connection in interactions",
        "detection_pattern": "Detectar busca por conexão e intimidade emocional",
        "example_phrases": json.dumps(["queria conversar mais", "sinto falta de", "preciso de pessoas", "gosto de intimidade"])
    },
    {
        "fragment_id": "EXT_E1_005",
        "domain": "Extraversion",
        "facet": "E1: Warmth",
        "facet_code": "E1",
        "description": "Demonstra hospitalidade e generosidade",
        "description_en": "Shows hospitality and generosity",
        "detection_pattern": "Detectar comportamentos hospitaleiros e generosos",
        "example_phrases": json.dumps(["adoro receber em casa", "gosto de presentear", "ofereço ajuda", "compartilho com prazer"])
    },

    # E2: Gregariousness (Sociabilidade) - 5 fragmentos
    {
        "fragment_id": "EXT_E2_001",
        "domain": "Extraversion",
        "facet": "E2: Gregariousness",
        "facet_code": "E2",
        "description": "Prefere estar em grupos a ficar sozinho",
        "description_en": "Prefers being in groups over being alone",
        "detection_pattern": "Detectar preferência por companhia vs solidão",
        "example_phrases": json.dumps(["gosto de estar com pessoas", "não gosto de ficar sozinho", "prefiro em grupo", "me sinto bem acompanhado"])
    },
    {
        "fragment_id": "EXT_E2_002",
        "domain": "Extraversion",
        "facet": "E2: Gregariousness",
        "facet_code": "E2",
        "description": "Busca ativamente eventos sociais e encontros",
        "description_en": "Actively seeks social events and gatherings",
        "detection_pattern": "Detectar busca ativa por socialização",
        "example_phrases": json.dumps(["vou sair com amigos", "marquei encontro", "festa no fim de semana", "vou para o happy hour"])
    },
    {
        "fragment_id": "EXT_E2_003",
        "domain": "Extraversion",
        "facet": "E2: Gregariousness",
        "facet_code": "E2",
        "description": "Tem amplo círculo social e muitos conhecidos",
        "description_en": "Has wide social circle and many acquaintances",
        "detection_pattern": "Detectar menções a amplo círculo social",
        "example_phrases": json.dumps(["tenho muitos amigos", "conheço muita gente", "minha rede de contatos", "meus vários grupos"])
    },
    {
        "fragment_id": "EXT_E2_004",
        "domain": "Extraversion",
        "facet": "E2: Gregariousness",
        "facet_code": "E2",
        "description": "Sente-se energizado por interações sociais",
        "description_en": "Feels energized by social interactions",
        "detection_pattern": "Detectar energia derivada de socialização",
        "example_phrases": json.dumps(["me anima encontrar pessoas", "saio revigorado", "adoro a energia do grupo", "me faz bem socializar"])
    },
    {
        "fragment_id": "EXT_E2_005",
        "domain": "Extraversion",
        "facet": "E2: Gregariousness",
        "facet_code": "E2",
        "description": "Inicia e organiza atividades em grupo",
        "description_en": "Initiates and organizes group activities",
        "detection_pattern": "Detectar iniciativa para organizar grupos",
        "example_phrases": json.dumps(["vou organizar", "chamei a galera", "montei o grupo", "propus a reunião"])
    },

    # E3: Assertiveness (Assertividade) - 5 fragmentos
    {
        "fragment_id": "EXT_E3_001",
        "domain": "Extraversion",
        "facet": "E3: Assertiveness",
        "facet_code": "E3",
        "description": "Expressa opiniões de forma direta e confiante",
        "description_en": "Expresses opinions directly and confidently",
        "detection_pattern": "Detectar expressão direta e confiante de opiniões",
        "example_phrases": json.dumps(["acho que", "na minha opinião", "discordo disso", "defendo que"])
    },
    {
        "fragment_id": "EXT_E3_002",
        "domain": "Extraversion",
        "facet": "E3: Assertiveness",
        "facet_code": "E3",
        "description": "Assume papel de liderança naturalmente",
        "description_en": "Naturally takes leadership roles",
        "detection_pattern": "Detectar comportamentos de liderança",
        "example_phrases": json.dumps(["assumi a liderança", "coordeno a equipe", "tomo a frente", "dirijo o projeto"])
    },
    {
        "fragment_id": "EXT_E3_003",
        "domain": "Extraversion",
        "facet": "E3: Assertiveness",
        "facet_code": "E3",
        "description": "Influencia e persuade outros com facilidade",
        "description_en": "Influences and persuades others easily",
        "detection_pattern": "Detectar habilidade de influência",
        "example_phrases": json.dumps(["convenci ele", "consegui persuadir", "mudei a opinião", "influenciei a decisão"])
    },
    {
        "fragment_id": "EXT_E3_004",
        "domain": "Extraversion",
        "facet": "E3: Assertiveness",
        "facet_code": "E3",
        "description": "Toma decisões rapidamente sem hesitar",
        "description_en": "Makes decisions quickly without hesitation",
        "detection_pattern": "Detectar decisões rápidas e assertivas",
        "example_phrases": json.dumps(["decidi na hora", "não hesitei", "foi uma decisão rápida", "agi imediatamente"])
    },
    {
        "fragment_id": "EXT_E3_005",
        "domain": "Extraversion",
        "facet": "E3: Assertiveness",
        "facet_code": "E3",
        "description": "Defende seus direitos e estabelece limites",
        "description_en": "Stands up for rights and sets boundaries",
        "detection_pattern": "Detectar defesa de direitos e limites",
        "example_phrases": json.dumps(["disse não", "estabeleci limites", "exigi respeito", "não aceitei"])
    },

    # E4: Activity (Atividade) - 5 fragmentos
    {
        "fragment_id": "EXT_E4_001",
        "domain": "Extraversion",
        "facet": "E4: Activity",
        "facet_code": "E4",
        "description": "Mantém ritmo de vida acelerado e ocupado",
        "description_en": "Maintains fast-paced and busy lifestyle",
        "detection_pattern": "Detectar vida agitada e ocupada",
        "example_phrases": json.dumps(["minha agenda está lotada", "não paro", "sempre ocupado", "corro o dia todo"])
    },
    {
        "fragment_id": "EXT_E4_002",
        "domain": "Extraversion",
        "facet": "E4: Activity",
        "facet_code": "E4",
        "description": "Tem alta energia e vigor físico",
        "description_en": "Has high energy and physical vigor",
        "detection_pattern": "Detectar alta energia e disposição",
        "example_phrases": json.dumps(["tenho muita energia", "me sinto disposto", "acordo animado", "não canso fácil"])
    },
    {
        "fragment_id": "EXT_E4_003",
        "domain": "Extraversion",
        "facet": "E4: Activity",
        "facet_code": "E4",
        "description": "Prefere ação a reflexão prolongada",
        "description_en": "Prefers action over prolonged reflection",
        "detection_pattern": "Detectar preferência por ação",
        "example_phrases": json.dumps(["vou fazer logo", "prefiro agir", "não fico pensando muito", "mãos à obra"])
    },
    {
        "fragment_id": "EXT_E4_004",
        "domain": "Extraversion",
        "facet": "E4: Activity",
        "facet_code": "E4",
        "description": "Realiza múltiplas tarefas simultaneamente",
        "description_en": "Performs multiple tasks simultaneously",
        "detection_pattern": "Detectar multitarefa",
        "example_phrases": json.dumps(["faço várias coisas ao mesmo tempo", "trabalho em paralelo", "multitarefa", "vários projetos"])
    },
    {
        "fragment_id": "EXT_E4_005",
        "domain": "Extraversion",
        "facet": "E4: Activity",
        "facet_code": "E4",
        "description": "Sente-se inquieto quando inativo",
        "description_en": "Feels restless when inactive",
        "detection_pattern": "Detectar desconforto com inatividade",
        "example_phrases": json.dumps(["não consigo ficar parado", "me sinto inquieto", "preciso fazer algo", "tédio me incomoda"])
    },

    # E5: Excitement-Seeking (Busca por Excitação) - 5 fragmentos
    {
        "fragment_id": "EXT_E5_001",
        "domain": "Extraversion",
        "facet": "E5: Excitement-Seeking",
        "facet_code": "E5",
        "description": "Busca experiências emocionantes e intensas",
        "description_en": "Seeks exciting and intense experiences",
        "detection_pattern": "Detectar busca por adrenalina e emoção",
        "example_phrases": json.dumps(["amo adrenalina", "experiências intensas", "viver ao máximo", "busco emoção"])
    },
    {
        "fragment_id": "EXT_E5_002",
        "domain": "Extraversion",
        "facet": "E5: Excitement-Seeking",
        "facet_code": "E5",
        "description": "Gosta de correr riscos moderados",
        "description_en": "Enjoys taking moderate risks",
        "detection_pattern": "Detectar comportamentos de risco calculado",
        "example_phrases": json.dumps(["arrisquei", "vale a pena o risco", "saí da zona de conforto", "tentei mesmo assim"])
    },
    {
        "fragment_id": "EXT_E5_003",
        "domain": "Extraversion",
        "facet": "E5: Excitement-Seeking",
        "facet_code": "E5",
        "description": "Aprecia ambientes estimulantes e vibrantes",
        "description_en": "Appreciates stimulating and vibrant environments",
        "detection_pattern": "Detectar preferência por ambientes animados",
        "example_phrases": json.dumps(["gosto de lugares agitados", "prefiro movimento", "adoro festas", "ambiente vibrante"])
    },
    {
        "fragment_id": "EXT_E5_004",
        "domain": "Extraversion",
        "facet": "E5: Excitement-Seeking",
        "facet_code": "E5",
        "description": "Entedia-se facilmente com rotina",
        "description_en": "Gets bored easily with routine",
        "detection_pattern": "Detectar tédio com rotina",
        "example_phrases": json.dumps(["rotina me cansa", "preciso de novidade", "enjoo rápido", "quero mudança"])
    },
    {
        "fragment_id": "EXT_E5_005",
        "domain": "Extraversion",
        "facet": "E5: Excitement-Seeking",
        "facet_code": "E5",
        "description": "Busca novidades e variedade constantemente",
        "description_en": "Constantly seeks novelty and variety",
        "detection_pattern": "Detectar busca por novidade",
        "example_phrases": json.dumps(["quero experimentar algo novo", "busco variedade", "gosto de mudar", "sempre algo diferente"])
    },

    # E6: Positive Emotions (Emoções Positivas) - 5 fragmentos
    {
        "fragment_id": "EXT_E6_001",
        "domain": "Extraversion",
        "facet": "E6: Positive Emotions",
        "facet_code": "E6",
        "description": "Experimenta alegria e entusiasmo frequentemente",
        "description_en": "Frequently experiences joy and enthusiasm",
        "detection_pattern": "Detectar expressões de alegria e entusiasmo",
        "example_phrases": json.dumps(["estou feliz", "que alegria", "animado com", "empolgado"])
    },
    {
        "fragment_id": "EXT_E6_002",
        "domain": "Extraversion",
        "facet": "E6: Positive Emotions",
        "facet_code": "E6",
        "description": "Ri e sorri com facilidade",
        "description_en": "Laughs and smiles easily",
        "detection_pattern": "Detectar expressões de riso e humor",
        "example_phrases": json.dumps(["ri muito", "achei engraçado", "sorri", "me divertindo"])
    },
    {
        "fragment_id": "EXT_E6_003",
        "domain": "Extraversion",
        "facet": "E6: Positive Emotions",
        "facet_code": "E6",
        "description": "Tem perspectiva otimista sobre a vida",
        "description_en": "Has optimistic outlook on life",
        "detection_pattern": "Detectar otimismo e esperança",
        "example_phrases": json.dumps(["vai dar certo", "tenho esperança", "o futuro é bom", "sou otimista"])
    },
    {
        "fragment_id": "EXT_E6_004",
        "domain": "Extraversion",
        "facet": "E6: Positive Emotions",
        "facet_code": "E6",
        "description": "Celebra conquistas e momentos positivos",
        "description_en": "Celebrates achievements and positive moments",
        "detection_pattern": "Detectar celebração de conquistas",
        "example_phrases": json.dumps(["comemorei", "celebramos", "que vitória", "momento especial"])
    },
    {
        "fragment_id": "EXT_E6_005",
        "domain": "Extraversion",
        "facet": "E6: Positive Emotions",
        "facet_code": "E6",
        "description": "Transmite bom humor aos outros",
        "description_en": "Spreads good mood to others",
        "detection_pattern": "Detectar transmissão de positividade",
        "example_phrases": json.dumps(["animei a galera", "transmiti alegria", "levantei o astral", "contagiei com energia"])
    },
]

# ========================================
# OPENNESS (O) - 30 fragmentos
# ========================================

OPENNESS_FRAGMENTS = [
    # O1: Fantasy (Imaginação) - 5 fragmentos
    {
        "fragment_id": "OPN_O1_001",
        "domain": "Openness",
        "facet": "O1: Fantasy",
        "facet_code": "O1",
        "description": "Tem imaginação rica e vívida",
        "description_en": "Has rich and vivid imagination",
        "detection_pattern": "Detectar imaginação e fantasia",
        "example_phrases": json.dumps(["imagino que", "sonho acordado", "fantasia", "na minha cabeça"])
    },
    {
        "fragment_id": "OPN_O1_002",
        "domain": "Openness",
        "facet": "O1: Fantasy",
        "facet_code": "O1",
        "description": "Sonha com possibilidades futuras",
        "description_en": "Dreams about future possibilities",
        "detection_pattern": "Detectar sonhos e visões de futuro",
        "example_phrases": json.dumps(["sonho em", "um dia vou", "imagino meu futuro", "seria incrível se"])
    },
    {
        "fragment_id": "OPN_O1_003",
        "domain": "Openness",
        "facet": "O1: Fantasy",
        "facet_code": "O1",
        "description": "Cria cenários mentais elaborados",
        "description_en": "Creates elaborate mental scenarios",
        "detection_pattern": "Detectar criação de cenários mentais",
        "example_phrases": json.dumps(["pensei em vários cenários", "e se fosse assim", "imaginei a cena", "visualizei"])
    },
    {
        "fragment_id": "OPN_O1_004",
        "domain": "Openness",
        "facet": "O1: Fantasy",
        "facet_code": "O1",
        "description": "Perde-se em devaneios frequentemente",
        "description_en": "Often loses oneself in daydreams",
        "detection_pattern": "Detectar devaneios e abstração",
        "example_phrases": json.dumps(["viajei na maionese", "me perdi em pensamentos", "estava viajando", "devaneando"])
    },
    {
        "fragment_id": "OPN_O1_005",
        "domain": "Openness",
        "facet": "O1: Fantasy",
        "facet_code": "O1",
        "description": "Aprecia ficção e histórias imaginativas",
        "description_en": "Appreciates fiction and imaginative stories",
        "detection_pattern": "Detectar apreciação por ficção",
        "example_phrases": json.dumps(["amo histórias", "livros de fantasia", "filmes imaginativos", "mundos fictícios"])
    },

    # O2: Aesthetics (Apreciação Estética) - 5 fragmentos
    {
        "fragment_id": "OPN_O2_001",
        "domain": "Openness",
        "facet": "O2: Aesthetics",
        "facet_code": "O2",
        "description": "Aprecia arte e beleza em várias formas",
        "description_en": "Appreciates art and beauty in various forms",
        "detection_pattern": "Detectar apreciação artística",
        "example_phrases": json.dumps(["achei lindo", "arte incrível", "beleza disso", "me emocionou"])
    },
    {
        "fragment_id": "OPN_O2_002",
        "domain": "Openness",
        "facet": "O2: Aesthetics",
        "facet_code": "O2",
        "description": "Emociona-se com música e outras artes",
        "description_en": "Gets moved by music and other arts",
        "detection_pattern": "Detectar emoção com arte",
        "example_phrases": json.dumps(["a música me tocou", "chorei com o filme", "me arrepiei", "fiquei emocionado"])
    },
    {
        "fragment_id": "OPN_O2_003",
        "domain": "Openness",
        "facet": "O2: Aesthetics",
        "facet_code": "O2",
        "description": "Busca experiências estéticas ativamente",
        "description_en": "Actively seeks aesthetic experiences",
        "detection_pattern": "Detectar busca por experiências estéticas",
        "example_phrases": json.dumps(["fui ao museu", "assisti ao concerto", "contemplei", "busquei beleza"])
    },
    {
        "fragment_id": "OPN_O2_004",
        "domain": "Openness",
        "facet": "O2: Aesthetics",
        "facet_code": "O2",
        "description": "Nota detalhes estéticos que outros ignoram",
        "description_en": "Notices aesthetic details others miss",
        "detection_pattern": "Detectar atenção a detalhes estéticos",
        "example_phrases": json.dumps(["reparei no detalhe", "a luz estava", "a composição", "percebi a harmonia"])
    },
    {
        "fragment_id": "OPN_O2_005",
        "domain": "Openness",
        "facet": "O2: Aesthetics",
        "facet_code": "O2",
        "description": "Valoriza ambiente agradável e bem decorado",
        "description_en": "Values pleasant and well-decorated environments",
        "detection_pattern": "Detectar valorização de ambientes",
        "example_phrases": json.dumps(["gosto do ambiente", "decoração bonita", "lugar agradável", "espaço bem cuidado"])
    },

    # O3: Feelings (Profundidade Emocional) - 5 fragmentos
    {
        "fragment_id": "OPN_O3_001",
        "domain": "Openness",
        "facet": "O3: Feelings",
        "facet_code": "O3",
        "description": "Experimenta emoções de forma profunda e intensa",
        "description_en": "Experiences emotions deeply and intensely",
        "detection_pattern": "Detectar profundidade emocional",
        "example_phrases": json.dumps(["sinto profundamente", "me afeta muito", "emoção intensa", "mexe comigo"])
    },
    {
        "fragment_id": "OPN_O3_002",
        "domain": "Openness",
        "facet": "O3: Feelings",
        "facet_code": "O3",
        "description": "Está em contato com suas emoções",
        "description_en": "Is in touch with own emotions",
        "detection_pattern": "Detectar consciência emocional",
        "example_phrases": json.dumps(["sei o que sinto", "reconheço minha emoção", "percebo que estou", "entendo meus sentimentos"])
    },
    {
        "fragment_id": "OPN_O3_003",
        "domain": "Openness",
        "facet": "O3: Feelings",
        "facet_code": "O3",
        "description": "Valoriza experiências emocionais",
        "description_en": "Values emotional experiences",
        "detection_pattern": "Detectar valorização de experiências emocionais",
        "example_phrases": json.dumps(["foi uma experiência emocional", "momento marcante", "sentir é importante", "viver intensamente"])
    },
    {
        "fragment_id": "OPN_O3_004",
        "domain": "Openness",
        "facet": "O3: Feelings",
        "facet_code": "O3",
        "description": "Expressa sentimentos abertamente",
        "description_en": "Expresses feelings openly",
        "detection_pattern": "Detectar expressão aberta de sentimentos",
        "example_phrases": json.dumps(["vou ser sincero", "preciso desabafar", "abri meu coração", "falei o que sentia"])
    },
    {
        "fragment_id": "OPN_O3_005",
        "domain": "Openness",
        "facet": "O3: Feelings",
        "facet_code": "O3",
        "description": "Busca entender as próprias emoções",
        "description_en": "Seeks to understand own emotions",
        "detection_pattern": "Detectar autorreflexão emocional",
        "example_phrases": json.dumps(["tentando entender o que sinto", "refletindo sobre", "por que me sinto assim", "analisando minhas emoções"])
    },

    # O4: Actions (Experimentação) - 5 fragmentos
    {
        "fragment_id": "OPN_O4_001",
        "domain": "Openness",
        "facet": "O4: Actions",
        "facet_code": "O4",
        "description": "Gosta de experimentar coisas novas",
        "description_en": "Likes trying new things",
        "detection_pattern": "Detectar abertura a experiências novas",
        "example_phrases": json.dumps(["quero experimentar", "vou tentar algo novo", "nunca fiz isso", "primeira vez"])
    },
    {
        "fragment_id": "OPN_O4_002",
        "domain": "Openness",
        "facet": "O4: Actions",
        "facet_code": "O4",
        "description": "Busca variedade em atividades e hobbies",
        "description_en": "Seeks variety in activities and hobbies",
        "detection_pattern": "Detectar busca por variedade",
        "example_phrases": json.dumps(["vários hobbies", "gosto de variar", "muitos interesses", "diferentes atividades"])
    },
    {
        "fragment_id": "OPN_O4_003",
        "domain": "Openness",
        "facet": "O4: Actions",
        "facet_code": "O4",
        "description": "Evita rotinas rígidas e previsíveis",
        "description_en": "Avoids rigid and predictable routines",
        "detection_pattern": "Detectar aversão à rotina rígida",
        "example_phrases": json.dumps(["não gosto de rotina", "prefiro flexibilidade", "mudo meus planos", "não sigo padrão"])
    },
    {
        "fragment_id": "OPN_O4_004",
        "domain": "Openness",
        "facet": "O4: Actions",
        "facet_code": "O4",
        "description": "Está aberto a diferentes culturas e costumes",
        "description_en": "Is open to different cultures and customs",
        "detection_pattern": "Detectar abertura cultural",
        "example_phrases": json.dumps(["culturas diferentes", "costumes interessantes", "aprendo com outras culturas", "diversidade"])
    },
    {
        "fragment_id": "OPN_O4_005",
        "domain": "Openness",
        "facet": "O4: Actions",
        "facet_code": "O4",
        "description": "Adapta-se facilmente a novas situações",
        "description_en": "Adapts easily to new situations",
        "detection_pattern": "Detectar adaptabilidade",
        "example_phrases": json.dumps(["me adaptei rápido", "flexível a mudanças", "lido bem com novidades", "me ajusto fácil"])
    },

    # O5: Ideas (Curiosidade Intelectual) - 5 fragmentos
    {
        "fragment_id": "OPN_O5_001",
        "domain": "Openness",
        "facet": "O5: Ideas",
        "facet_code": "O5",
        "description": "Tem curiosidade intelectual intensa",
        "description_en": "Has intense intellectual curiosity",
        "detection_pattern": "Detectar curiosidade intelectual",
        "example_phrases": json.dumps(["quero saber mais", "me interesso por", "curiosidade sobre", "busco conhecimento"])
    },
    {
        "fragment_id": "OPN_O5_002",
        "domain": "Openness",
        "facet": "O5: Ideas",
        "facet_code": "O5",
        "description": "Gosta de discutir ideias abstratas",
        "description_en": "Enjoys discussing abstract ideas",
        "detection_pattern": "Detectar discussão de ideias abstratas",
        "example_phrases": json.dumps(["filosofia", "teoria interessante", "conceito abstrato", "ideias complexas"])
    },
    {
        "fragment_id": "OPN_O5_003",
        "domain": "Openness",
        "facet": "O5: Ideas",
        "facet_code": "O5",
        "description": "Aprecia desafios intelectuais",
        "description_en": "Appreciates intellectual challenges",
        "detection_pattern": "Detectar apreciação por desafios intelectuais",
        "example_phrases": json.dumps(["gosto de desafios mentais", "problema interessante", "quebra-cabeça", "exercício intelectual"])
    },
    {
        "fragment_id": "OPN_O5_004",
        "domain": "Openness",
        "facet": "O5: Ideas",
        "facet_code": "O5",
        "description": "Questiona crenças e convenções",
        "description_en": "Questions beliefs and conventions",
        "detection_pattern": "Detectar questionamento de crenças",
        "example_phrases": json.dumps(["questiono isso", "por que assim", "não aceito de cara", "desafio a norma"])
    },
    {
        "fragment_id": "OPN_O5_005",
        "domain": "Openness",
        "facet": "O5: Ideas",
        "facet_code": "O5",
        "description": "Busca aprender continuamente",
        "description_en": "Seeks to learn continuously",
        "detection_pattern": "Detectar busca por aprendizado",
        "example_phrases": json.dumps(["estou estudando", "aprendendo sobre", "curso novo", "sempre aprendendo"])
    },

    # O6: Values (Flexibilidade de Valores) - 5 fragmentos
    {
        "fragment_id": "OPN_O6_001",
        "domain": "Openness",
        "facet": "O6: Values",
        "facet_code": "O6",
        "description": "Questiona valores tradicionais quando necessário",
        "description_en": "Questions traditional values when necessary",
        "detection_pattern": "Detectar questionamento de tradições",
        "example_phrases": json.dumps(["tradição não faz sentido", "por que seguir isso", "repensar valores", "questiono costumes"])
    },
    {
        "fragment_id": "OPN_O6_002",
        "domain": "Openness",
        "facet": "O6: Values",
        "facet_code": "O6",
        "description": "Aceita diferentes visões de mundo",
        "description_en": "Accepts different worldviews",
        "detection_pattern": "Detectar aceitação de visões diferentes",
        "example_phrases": json.dumps(["respeito a visão dele", "cada um tem sua verdade", "perspectivas diferentes", "entendo o ponto de vista"])
    },
    {
        "fragment_id": "OPN_O6_003",
        "domain": "Openness",
        "facet": "O6: Values",
        "facet_code": "O6",
        "description": "Reavalia suas próprias crenças periodicamente",
        "description_en": "Periodically reevaluates own beliefs",
        "detection_pattern": "Detectar reavaliação de crenças",
        "example_phrases": json.dumps(["mudei minha opinião", "antes pensava diferente", "revi meus valores", "evoluí meu pensamento"])
    },
    {
        "fragment_id": "OPN_O6_004",
        "domain": "Openness",
        "facet": "O6: Values",
        "facet_code": "O6",
        "description": "Valoriza autonomia e independência de pensamento",
        "description_en": "Values autonomy and independent thinking",
        "detection_pattern": "Detectar valorização de autonomia",
        "example_phrases": json.dumps(["penso por mim mesmo", "não sigo a massa", "independente", "minha própria opinião"])
    },
    {
        "fragment_id": "OPN_O6_005",
        "domain": "Openness",
        "facet": "O6: Values",
        "facet_code": "O6",
        "description": "Está aberto a mudanças sociais progressivas",
        "description_en": "Is open to progressive social changes",
        "detection_pattern": "Detectar abertura a mudanças sociais",
        "example_phrases": json.dumps(["sociedade evoluindo", "mudanças necessárias", "progresso social", "nova mentalidade"])
    },
]

# ========================================
# CONSCIENTIOUSNESS (C) - 30 fragmentos
# ========================================

CONSCIENTIOUSNESS_FRAGMENTS = [
    # C1: Competence (Competência) - 5 fragmentos
    {
        "fragment_id": "CON_C1_001",
        "domain": "Conscientiousness",
        "facet": "C1: Competence",
        "facet_code": "C1",
        "description": "Sente-se capaz e eficiente no que faz",
        "description_en": "Feels capable and efficient",
        "detection_pattern": "Detectar autoeficácia e competência",
        "example_phrases": json.dumps(["sou bom nisso", "consigo fazer", "tenho capacidade", "sei fazer bem"])
    },
    {
        "fragment_id": "CON_C1_002",
        "domain": "Conscientiousness",
        "facet": "C1: Competence",
        "facet_code": "C1",
        "description": "Prepara-se bem para tarefas importantes",
        "description_en": "Prepares well for important tasks",
        "detection_pattern": "Detectar preparação e planejamento",
        "example_phrases": json.dumps(["me preparei", "estudei antes", "planejei tudo", "estou pronto"])
    },
    {
        "fragment_id": "CON_C1_003",
        "domain": "Conscientiousness",
        "facet": "C1: Competence",
        "facet_code": "C1",
        "description": "Busca excelência em suas atividades",
        "description_en": "Strives for excellence",
        "detection_pattern": "Detectar busca por excelência",
        "example_phrases": json.dumps(["quero fazer bem feito", "busco excelência", "qualidade importa", "melhor resultado"])
    },
    {
        "fragment_id": "CON_C1_004",
        "domain": "Conscientiousness",
        "facet": "C1: Competence",
        "facet_code": "C1",
        "description": "Aprende com erros e busca melhorar",
        "description_en": "Learns from mistakes and improves",
        "detection_pattern": "Detectar aprendizado com erros",
        "example_phrases": json.dumps(["aprendi com o erro", "vou melhorar", "não repito", "cresci com isso"])
    },
    {
        "fragment_id": "CON_C1_005",
        "domain": "Conscientiousness",
        "facet": "C1: Competence",
        "facet_code": "C1",
        "description": "Tem confiança em suas habilidades",
        "description_en": "Has confidence in own abilities",
        "detection_pattern": "Detectar autoconfiança",
        "example_phrases": json.dumps(["confio na minha capacidade", "sei que consigo", "tenho habilidade", "posso fazer"])
    },

    # C2: Order (Organização) - 5 fragmentos
    {
        "fragment_id": "CON_C2_001",
        "domain": "Conscientiousness",
        "facet": "C2: Order",
        "facet_code": "C2",
        "description": "Mantém ambiente organizado e arrumado",
        "description_en": "Keeps environment organized and tidy",
        "detection_pattern": "Detectar organização física",
        "example_phrases": json.dumps(["organizado", "cada coisa em seu lugar", "arrumado", "ordem no ambiente"])
    },
    {
        "fragment_id": "CON_C2_002",
        "domain": "Conscientiousness",
        "facet": "C2: Order",
        "facet_code": "C2",
        "description": "Segue métodos e sistemas estabelecidos",
        "description_en": "Follows established methods and systems",
        "detection_pattern": "Detectar uso de sistemas",
        "example_phrases": json.dumps(["sigo um método", "tenho sistema", "processo definido", "rotina estruturada"])
    },
    {
        "fragment_id": "CON_C2_003",
        "domain": "Conscientiousness",
        "facet": "C2: Order",
        "facet_code": "C2",
        "description": "Planeja atividades com antecedência",
        "description_en": "Plans activities in advance",
        "detection_pattern": "Detectar planejamento antecipado",
        "example_phrases": json.dumps(["já planejei", "organizei a agenda", "marquei com antecedência", "preparei tudo"])
    },
    {
        "fragment_id": "CON_C2_004",
        "domain": "Conscientiousness",
        "facet": "C2: Order",
        "facet_code": "C2",
        "description": "Incomoda-se com bagunça e desordem",
        "description_en": "Gets bothered by mess and disorder",
        "detection_pattern": "Detectar incômodo com desordem",
        "example_phrases": json.dumps(["bagunça me incomoda", "preciso organizar", "não consigo na bagunça", "desordem me estressa"])
    },
    {
        "fragment_id": "CON_C2_005",
        "domain": "Conscientiousness",
        "facet": "C2: Order",
        "facet_code": "C2",
        "description": "Usa listas e ferramentas de organização",
        "description_en": "Uses lists and organization tools",
        "detection_pattern": "Detectar uso de ferramentas de organização",
        "example_phrases": json.dumps(["fiz uma lista", "uso agenda", "anoto tudo", "ferramenta de organização"])
    },

    # C3: Dutifulness (Senso de Dever) - 5 fragmentos
    {
        "fragment_id": "CON_C3_001",
        "domain": "Conscientiousness",
        "facet": "C3: Dutifulness",
        "facet_code": "C3",
        "description": "Cumpre compromissos e promessas fielmente",
        "description_en": "Faithfully fulfills commitments and promises",
        "detection_pattern": "Detectar cumprimento de compromissos",
        "example_phrases": json.dumps(["cumpri o prometido", "mantive minha palavra", "honrei o compromisso", "fiz o que disse"])
    },
    {
        "fragment_id": "CON_C3_002",
        "domain": "Conscientiousness",
        "facet": "C3: Dutifulness",
        "facet_code": "C3",
        "description": "Segue regras e regulamentos",
        "description_en": "Follows rules and regulations",
        "detection_pattern": "Detectar seguimento de regras",
        "example_phrases": json.dumps(["sigo as regras", "respeito as normas", "dentro do regulamento", "conforme o protocolo"])
    },
    {
        "fragment_id": "CON_C3_003",
        "domain": "Conscientiousness",
        "facet": "C3: Dutifulness",
        "facet_code": "C3",
        "description": "Tem forte senso de responsabilidade",
        "description_en": "Has strong sense of responsibility",
        "detection_pattern": "Detectar senso de responsabilidade",
        "example_phrases": json.dumps(["minha responsabilidade", "dever cumprido", "assumo minhas obrigações", "faço minha parte"])
    },
    {
        "fragment_id": "CON_C3_004",
        "domain": "Conscientiousness",
        "facet": "C3: Dutifulness",
        "facet_code": "C3",
        "description": "Sente culpa quando não cumpre deveres",
        "description_en": "Feels guilty when not fulfilling duties",
        "detection_pattern": "Detectar culpa por deveres não cumpridos",
        "example_phrases": json.dumps(["me sinto mal por não ter", "deveria ter feito", "culpa por falhar", "não deveria ter faltado"])
    },
    {
        "fragment_id": "CON_C3_005",
        "domain": "Conscientiousness",
        "facet": "C3: Dutifulness",
        "facet_code": "C3",
        "description": "Coloca deveres acima de desejos pessoais",
        "description_en": "Puts duties above personal desires",
        "detection_pattern": "Detectar priorização de deveres",
        "example_phrases": json.dumps(["dever primeiro", "obrigação antes de prazer", "preciso cumprir", "não posso falhar com"])
    },

    # C4: Achievement Striving (Busca por Realização) - 5 fragmentos
    {
        "fragment_id": "CON_C4_001",
        "domain": "Conscientiousness",
        "facet": "C4: Achievement Striving",
        "facet_code": "C4",
        "description": "Define e persegue metas ambiciosas",
        "description_en": "Sets and pursues ambitious goals",
        "detection_pattern": "Detectar metas ambiciosas",
        "example_phrases": json.dumps(["minha meta é", "quero alcançar", "objetivo ambicioso", "vou conseguir"])
    },
    {
        "fragment_id": "CON_C4_002",
        "domain": "Conscientiousness",
        "facet": "C4: Achievement Striving",
        "facet_code": "C4",
        "description": "Trabalha duro para atingir objetivos",
        "description_en": "Works hard to achieve objectives",
        "detection_pattern": "Detectar trabalho árduo",
        "example_phrases": json.dumps(["trabalhei muito", "me esforcei", "dediquei tempo", "não medi esforços"])
    },
    {
        "fragment_id": "CON_C4_003",
        "domain": "Conscientiousness",
        "facet": "C4: Achievement Striving",
        "facet_code": "C4",
        "description": "Tem motivação intrínseca para realizar",
        "description_en": "Has intrinsic motivation to achieve",
        "detection_pattern": "Detectar motivação para realizar",
        "example_phrases": json.dumps(["motivado a fazer", "quero realizar", "impulso interno", "preciso conquistar"])
    },
    {
        "fragment_id": "CON_C4_004",
        "domain": "Conscientiousness",
        "facet": "C4: Achievement Striving",
        "facet_code": "C4",
        "description": "Persiste diante de obstáculos",
        "description_en": "Persists in face of obstacles",
        "detection_pattern": "Detectar persistência",
        "example_phrases": json.dumps(["não desisto", "continuo tentando", "supero obstáculos", "persisto mesmo assim"])
    },
    {
        "fragment_id": "CON_C4_005",
        "domain": "Conscientiousness",
        "facet": "C4: Achievement Striving",
        "facet_code": "C4",
        "description": "Busca reconhecimento por realizações",
        "description_en": "Seeks recognition for achievements",
        "detection_pattern": "Detectar busca por reconhecimento",
        "example_phrases": json.dumps(["quero ser reconhecido", "mostrar resultados", "provar meu valor", "mereço reconhecimento"])
    },

    # C5: Self-Discipline (Autodisciplina) - 5 fragmentos
    {
        "fragment_id": "CON_C5_001",
        "domain": "Conscientiousness",
        "facet": "C5: Self-Discipline",
        "facet_code": "C5",
        "description": "Completa tarefas mesmo quando difíceis",
        "description_en": "Completes tasks even when difficult",
        "detection_pattern": "Detectar conclusão de tarefas difíceis",
        "example_phrases": json.dumps(["terminei mesmo difícil", "completei a tarefa", "não deixei pela metade", "fui até o fim"])
    },
    {
        "fragment_id": "CON_C5_002",
        "domain": "Conscientiousness",
        "facet": "C5: Self-Discipline",
        "facet_code": "C5",
        "description": "Resiste a tentações e distrações",
        "description_en": "Resists temptations and distractions",
        "detection_pattern": "Detectar resistência a distrações",
        "example_phrases": json.dumps(["foquei no trabalho", "ignorei distrações", "resisti à tentação", "mantive o foco"])
    },
    {
        "fragment_id": "CON_C5_003",
        "domain": "Conscientiousness",
        "facet": "C5: Self-Discipline",
        "facet_code": "C5",
        "description": "Mantém rotinas e hábitos consistentes",
        "description_en": "Maintains consistent routines and habits",
        "detection_pattern": "Detectar consistência em hábitos",
        "example_phrases": json.dumps(["mantenho a rotina", "hábito diário", "consistência", "faço sempre igual"])
    },
    {
        "fragment_id": "CON_C5_004",
        "domain": "Conscientiousness",
        "facet": "C5: Self-Discipline",
        "facet_code": "C5",
        "description": "Controla impulsos efetivamente",
        "description_en": "Controls impulses effectively",
        "detection_pattern": "Detectar controle de impulsos",
        "example_phrases": json.dumps(["me controlei", "segurei o impulso", "pensei antes de agir", "autocontrole"])
    },
    {
        "fragment_id": "CON_C5_005",
        "domain": "Conscientiousness",
        "facet": "C5: Self-Discipline",
        "facet_code": "C5",
        "description": "Adia gratificação em favor de metas",
        "description_en": "Delays gratification for goals",
        "detection_pattern": "Detectar adiamento de gratificação",
        "example_phrases": json.dumps(["posso esperar", "recompensa depois", "primeiro o trabalho", "sacrifico agora para depois"])
    },

    # C6: Deliberation (Ponderação) - 5 fragmentos
    {
        "fragment_id": "CON_C6_001",
        "domain": "Conscientiousness",
        "facet": "C6: Deliberation",
        "facet_code": "C6",
        "description": "Pensa cuidadosamente antes de agir",
        "description_en": "Thinks carefully before acting",
        "detection_pattern": "Detectar reflexão antes de ação",
        "example_phrases": json.dumps(["pensei bem antes", "refleti sobre", "considerei as opções", "analisei antes"])
    },
    {
        "fragment_id": "CON_C6_002",
        "domain": "Conscientiousness",
        "facet": "C6: Deliberation",
        "facet_code": "C6",
        "description": "Considera consequências de suas ações",
        "description_en": "Considers consequences of actions",
        "detection_pattern": "Detectar consideração de consequências",
        "example_phrases": json.dumps(["pensei nas consequências", "o que pode acontecer", "avaliei riscos", "consequências possíveis"])
    },
    {
        "fragment_id": "CON_C6_003",
        "domain": "Conscientiousness",
        "facet": "C6: Deliberation",
        "facet_code": "C6",
        "description": "Evita decisões impulsivas",
        "description_en": "Avoids impulsive decisions",
        "detection_pattern": "Detectar evitação de impulsividade",
        "example_phrases": json.dumps(["não agi por impulso", "esperei para decidir", "não me precipitei", "calma para decidir"])
    },
    {
        "fragment_id": "CON_C6_004",
        "domain": "Conscientiousness",
        "facet": "C6: Deliberation",
        "facet_code": "C6",
        "description": "Planeja com cuidado antes de executar",
        "description_en": "Plans carefully before executing",
        "detection_pattern": "Detectar planejamento cuidadoso",
        "example_phrases": json.dumps(["planejei com cuidado", "pensei em cada detalhe", "preparei o plano", "estruturei antes"])
    },
    {
        "fragment_id": "CON_C6_005",
        "domain": "Conscientiousness",
        "facet": "C6: Deliberation",
        "facet_code": "C6",
        "description": "Busca informações antes de decidir",
        "description_en": "Seeks information before deciding",
        "detection_pattern": "Detectar busca de informação para decisão",
        "example_phrases": json.dumps(["pesquisei antes", "busquei informação", "me informei", "quis saber mais antes"])
    },
]

# ========================================
# AGREEABLENESS (A) - 30 fragmentos
# ========================================

AGREEABLENESS_FRAGMENTS = [
    # A1: Trust (Confiança) - 5 fragmentos
    {
        "fragment_id": "AGR_A1_001",
        "domain": "Agreeableness",
        "facet": "A1: Trust",
        "facet_code": "A1",
        "description": "Tende a confiar nas pessoas",
        "description_en": "Tends to trust people",
        "detection_pattern": "Detectar confiança em outros",
        "example_phrases": json.dumps(["confio nele", "acredito nas pessoas", "dou o benefício da dúvida", "pessoas são boas"])
    },
    {
        "fragment_id": "AGR_A1_002",
        "domain": "Agreeableness",
        "facet": "A1: Trust",
        "facet_code": "A1",
        "description": "Acredita na boa intenção dos outros",
        "description_en": "Believes in others' good intentions",
        "detection_pattern": "Detectar crença em boas intenções",
        "example_phrases": json.dumps(["ela não quis fazer mal", "intenção era boa", "não foi por mal", "deve ter um motivo"])
    },
    {
        "fragment_id": "AGR_A1_003",
        "domain": "Agreeableness",
        "facet": "A1: Trust",
        "facet_code": "A1",
        "description": "Dá segundas chances facilmente",
        "description_en": "Easily gives second chances",
        "detection_pattern": "Detectar disposição para segundas chances",
        "example_phrases": json.dumps(["vou dar outra chance", "todo mundo erra", "posso perdoar", "deixa pra lá"])
    },
    {
        "fragment_id": "AGR_A1_004",
        "domain": "Agreeableness",
        "facet": "A1: Trust",
        "facet_code": "A1",
        "description": "Não é desconfiado por natureza",
        "description_en": "Is not naturally suspicious",
        "detection_pattern": "Detectar ausência de desconfiança",
        "example_phrases": json.dumps(["não desconfio", "não penso mal", "não sou paranoico", "levo na boa fé"])
    },
    {
        "fragment_id": "AGR_A1_005",
        "domain": "Agreeableness",
        "facet": "A1: Trust",
        "facet_code": "A1",
        "description": "Compartilha informações pessoais abertamente",
        "description_en": "Shares personal information openly",
        "detection_pattern": "Detectar abertura para compartilhar",
        "example_phrases": json.dumps(["posso contar", "vou compartilhar", "abro meu coração", "conto tudo"])
    },

    # A2: Straightforwardness (Franqueza) - 5 fragmentos
    {
        "fragment_id": "AGR_A2_001",
        "domain": "Agreeableness",
        "facet": "A2: Straightforwardness",
        "facet_code": "A2",
        "description": "É sincero e direto nas comunicações",
        "description_en": "Is sincere and direct in communications",
        "detection_pattern": "Detectar sinceridade e franqueza",
        "example_phrases": json.dumps(["vou ser sincero", "falando francamente", "diretamente", "sem rodeios"])
    },
    {
        "fragment_id": "AGR_A2_002",
        "domain": "Agreeableness",
        "facet": "A2: Straightforwardness",
        "facet_code": "A2",
        "description": "Evita manipulação e jogos",
        "description_en": "Avoids manipulation and games",
        "detection_pattern": "Detectar aversão a manipulação",
        "example_phrases": json.dumps(["não jogo", "sem manipulação", "não tenho segundas intenções", "transparente"])
    },
    {
        "fragment_id": "AGR_A2_003",
        "domain": "Agreeableness",
        "facet": "A2: Straightforwardness",
        "facet_code": "A2",
        "description": "Expressa opiniões genuínas",
        "description_en": "Expresses genuine opinions",
        "detection_pattern": "Detectar expressão genuína",
        "example_phrases": json.dumps(["o que realmente penso", "minha opinião verdadeira", "sendo honesto", "de verdade"])
    },
    {
        "fragment_id": "AGR_A2_004",
        "domain": "Agreeableness",
        "facet": "A2: Straightforwardness",
        "facet_code": "A2",
        "description": "Não esconde informações relevantes",
        "description_en": "Does not hide relevant information",
        "detection_pattern": "Detectar transparência",
        "example_phrases": json.dumps(["não escondo", "conto tudo", "você precisa saber", "vou revelar"])
    },
    {
        "fragment_id": "AGR_A2_005",
        "domain": "Agreeableness",
        "facet": "A2: Straightforwardness",
        "facet_code": "A2",
        "description": "Admite erros e falhas abertamente",
        "description_en": "Openly admits mistakes and failures",
        "detection_pattern": "Detectar admissão de erros",
        "example_phrases": json.dumps(["eu errei", "reconheço minha falha", "foi meu erro", "admito que"])
    },

    # A3: Altruism (Altruísmo) - 5 fragmentos
    {
        "fragment_id": "AGR_A3_001",
        "domain": "Agreeableness",
        "facet": "A3: Altruism",
        "facet_code": "A3",
        "description": "Ajuda os outros sem esperar retorno",
        "description_en": "Helps others without expecting return",
        "detection_pattern": "Detectar ajuda desinteressada",
        "example_phrases": json.dumps(["ajudei sem esperar nada", "faço por fazer bem", "não precisa retribuir", "ajudo porque quero"])
    },
    {
        "fragment_id": "AGR_A3_002",
        "domain": "Agreeableness",
        "facet": "A3: Altruism",
        "facet_code": "A3",
        "description": "Preocupa-se genuinamente com os necessitados",
        "description_en": "Genuinely cares for those in need",
        "detection_pattern": "Detectar preocupação com necessitados",
        "example_phrases": json.dumps(["me preocupo com quem precisa", "quero ajudar", "solidário", "sensível às necessidades"])
    },
    {
        "fragment_id": "AGR_A3_003",
        "domain": "Agreeableness",
        "facet": "A3: Altruism",
        "facet_code": "A3",
        "description": "Dedica tempo a causas sociais",
        "description_en": "Dedicates time to social causes",
        "detection_pattern": "Detectar dedicação a causas",
        "example_phrases": json.dumps(["trabalho voluntário", "dedico tempo a causas", "ajudo a comunidade", "participo de ações sociais"])
    },
    {
        "fragment_id": "AGR_A3_004",
        "domain": "Agreeableness",
        "facet": "A3: Altruism",
        "facet_code": "A3",
        "description": "Sente satisfação ao ajudar outros",
        "description_en": "Feels satisfaction when helping others",
        "detection_pattern": "Detectar satisfação em ajudar",
        "example_phrases": json.dumps(["me sinto bem ajudando", "satisfação de ajudar", "gratificante", "faz bem ao meu coração"])
    },
    {
        "fragment_id": "AGR_A3_005",
        "domain": "Agreeableness",
        "facet": "A3: Altruism",
        "facet_code": "A3",
        "description": "Coloca necessidades alheias antes das próprias",
        "description_en": "Puts others' needs before own",
        "detection_pattern": "Detectar priorização de outros",
        "example_phrases": json.dumps(["primeiro os outros", "ele precisa mais que eu", "posso esperar", "deixo para depois"])
    },

    # A4: Compliance (Complacência) - 5 fragmentos
    {
        "fragment_id": "AGR_A4_001",
        "domain": "Agreeableness",
        "facet": "A4: Compliance",
        "facet_code": "A4",
        "description": "Evita conflitos e confrontos",
        "description_en": "Avoids conflicts and confrontations",
        "detection_pattern": "Detectar evitação de conflito",
        "example_phrases": json.dumps(["não quero briga", "prefiro evitar conflito", "deixa pra lá", "não vale a pena discutir"])
    },
    {
        "fragment_id": "AGR_A4_002",
        "domain": "Agreeableness",
        "facet": "A4: Compliance",
        "facet_code": "A4",
        "description": "Cede em discussões para manter paz",
        "description_en": "Yields in arguments to keep peace",
        "detection_pattern": "Detectar concessão por paz",
        "example_phrases": json.dumps(["cedo para evitar briga", "deixo ele ganhar", "não vale a discussão", "prefiro concordar"])
    },
    {
        "fragment_id": "AGR_A4_003",
        "domain": "Agreeableness",
        "facet": "A4: Compliance",
        "facet_code": "A4",
        "description": "Coopera facilmente com outros",
        "description_en": "Cooperates easily with others",
        "detection_pattern": "Detectar cooperação",
        "example_phrases": json.dumps(["trabalho bem em equipe", "coopero sem problema", "faço minha parte", "colaboro sempre"])
    },
    {
        "fragment_id": "AGR_A4_004",
        "domain": "Agreeableness",
        "facet": "A4: Compliance",
        "facet_code": "A4",
        "description": "Busca harmonia nos relacionamentos",
        "description_en": "Seeks harmony in relationships",
        "detection_pattern": "Detectar busca por harmonia",
        "example_phrases": json.dumps(["quero harmonia", "paz no relacionamento", "evito tensão", "ambiente tranquilo"])
    },
    {
        "fragment_id": "AGR_A4_005",
        "domain": "Agreeableness",
        "facet": "A4: Compliance",
        "facet_code": "A4",
        "description": "Não guarda rancor após desentendimentos",
        "description_en": "Does not hold grudges after disagreements",
        "detection_pattern": "Detectar ausência de rancor",
        "example_phrases": json.dumps(["não guardo rancor", "passou passou", "já perdoei", "virei a página"])
    },

    # A5: Modesty (Modéstia) - 5 fragmentos
    {
        "fragment_id": "AGR_A5_001",
        "domain": "Agreeableness",
        "facet": "A5: Modesty",
        "facet_code": "A5",
        "description": "Não se gaba de conquistas",
        "description_en": "Does not brag about achievements",
        "detection_pattern": "Detectar humildade sobre conquistas",
        "example_phrases": json.dumps(["não é pra tanto", "nada demais", "qualquer um faria", "sorte minha"])
    },
    {
        "fragment_id": "AGR_A5_002",
        "domain": "Agreeableness",
        "facet": "A5: Modesty",
        "facet_code": "A5",
        "description": "Prefere não ser o centro das atenções",
        "description_en": "Prefers not being center of attention",
        "detection_pattern": "Detectar preferência por discrição",
        "example_phrases": json.dumps(["não gosto de holofotes", "prefiro nos bastidores", "discretamente", "não preciso de atenção"])
    },
    {
        "fragment_id": "AGR_A5_003",
        "domain": "Agreeableness",
        "facet": "A5: Modesty",
        "facet_code": "A5",
        "description": "Reconhece contribuição de outros",
        "description_en": "Acknowledges others' contributions",
        "detection_pattern": "Detectar reconhecimento de outros",
        "example_phrases": json.dumps(["graças a equipe", "ele ajudou muito", "não fiz sozinho", "todos contribuíram"])
    },
    {
        "fragment_id": "AGR_A5_004",
        "domain": "Agreeableness",
        "facet": "A5: Modesty",
        "facet_code": "A5",
        "description": "Subestima próprias habilidades",
        "description_en": "Underestimates own abilities",
        "detection_pattern": "Detectar subestimação de si",
        "example_phrases": json.dumps(["não sou tão bom", "outros são melhores", "tenho muito a aprender", "não me acho especial"])
    },
    {
        "fragment_id": "AGR_A5_005",
        "domain": "Agreeableness",
        "facet": "A5: Modesty",
        "facet_code": "A5",
        "description": "Aceita críticas sem defensividade",
        "description_en": "Accepts criticism without defensiveness",
        "detection_pattern": "Detectar aceitação de críticas",
        "example_phrases": json.dumps(["aceito a crítica", "tem razão", "vou melhorar isso", "obrigado pelo feedback"])
    },

    # A6: Tender-Mindedness (Sensibilidade) - 5 fragmentos
    {
        "fragment_id": "AGR_A6_001",
        "domain": "Agreeableness",
        "facet": "A6: Tender-Mindedness",
        "facet_code": "A6",
        "description": "Sente compaixão pelo sofrimento alheio",
        "description_en": "Feels compassion for others' suffering",
        "detection_pattern": "Detectar compaixão",
        "example_phrases": json.dumps(["sofro junto", "me comove", "sinto pena", "coração aperta"])
    },
    {
        "fragment_id": "AGR_A6_002",
        "domain": "Agreeableness",
        "facet": "A6: Tender-Mindedness",
        "facet_code": "A6",
        "description": "Preocupa-se com questões humanitárias",
        "description_en": "Cares about humanitarian issues",
        "detection_pattern": "Detectar preocupação humanitária",
        "example_phrases": json.dumps(["me preocupa a fome", "injustiça me incomoda", "causas humanitárias", "direitos humanos"])
    },
    {
        "fragment_id": "AGR_A6_003",
        "domain": "Agreeableness",
        "facet": "A6: Tender-Mindedness",
        "facet_code": "A6",
        "description": "Emociona-se facilmente com histórias tristes",
        "description_en": "Gets easily moved by sad stories",
        "detection_pattern": "Detectar emoção com histórias",
        "example_phrases": json.dumps(["chorei com a história", "me emocionei", "que tristeza", "mexeu comigo"])
    },
    {
        "fragment_id": "AGR_A6_004",
        "domain": "Agreeableness",
        "facet": "A6: Tender-Mindedness",
        "facet_code": "A6",
        "description": "Valoriza gentileza e bondade",
        "description_en": "Values kindness and goodness",
        "detection_pattern": "Detectar valorização de bondade",
        "example_phrases": json.dumps(["gentileza importa", "ser bom é essencial", "valorizo bondade", "pessoas gentis"])
    },
    {
        "fragment_id": "AGR_A6_005",
        "domain": "Agreeableness",
        "facet": "A6: Tender-Mindedness",
        "facet_code": "A6",
        "description": "Considera sentimentos nas decisões",
        "description_en": "Considers feelings in decisions",
        "detection_pattern": "Detectar consideração de sentimentos",
        "example_phrases": json.dumps(["penso em como ele se sente", "não quero magoar", "considero os sentimentos", "empatia na decisão"])
    },
]

# ========================================
# NEUROTICISM (N) - 30 fragmentos
# ========================================

NEUROTICISM_FRAGMENTS = [
    # N1: Anxiety (Ansiedade) - 5 fragmentos
    {
        "fragment_id": "NEU_N1_001",
        "domain": "Neuroticism",
        "facet": "N1: Anxiety",
        "facet_code": "N1",
        "description": "Preocupa-se frequentemente com o futuro",
        "description_en": "Frequently worries about the future",
        "detection_pattern": "Detectar preocupação com futuro",
        "example_phrases": json.dumps(["me preocupo com", "e se acontecer", "medo do futuro", "ansiedade sobre"])
    },
    {
        "fragment_id": "NEU_N1_002",
        "domain": "Neuroticism",
        "facet": "N1: Anxiety",
        "facet_code": "N1",
        "description": "Sente tensão e nervosismo frequentemente",
        "description_en": "Frequently feels tension and nervousness",
        "detection_pattern": "Detectar tensão e nervosismo",
        "example_phrases": json.dumps(["estou tenso", "nervoso com isso", "ansiedade me pega", "não consigo relaxar"])
    },
    {
        "fragment_id": "NEU_N1_003",
        "domain": "Neuroticism",
        "facet": "N1: Anxiety",
        "facet_code": "N1",
        "description": "Tem dificuldade para relaxar",
        "description_en": "Has difficulty relaxing",
        "detection_pattern": "Detectar dificuldade em relaxar",
        "example_phrases": json.dumps(["não consigo relaxar", "fico inquieto", "sempre alerta", "não descanso"])
    },
    {
        "fragment_id": "NEU_N1_004",
        "domain": "Neuroticism",
        "facet": "N1: Anxiety",
        "facet_code": "N1",
        "description": "Sente medo desproporcional de situações",
        "description_en": "Feels disproportionate fear of situations",
        "detection_pattern": "Detectar medo desproporcional",
        "example_phrases": json.dumps(["medo exagerado", "pavor de", "evito porque tenho medo", "apavorado com"])
    },
    {
        "fragment_id": "NEU_N1_005",
        "domain": "Neuroticism",
        "facet": "N1: Anxiety",
        "facet_code": "N1",
        "description": "Ruminação sobre problemas potenciais",
        "description_en": "Ruminates about potential problems",
        "detection_pattern": "Detectar ruminação de problemas",
        "example_phrases": json.dumps(["fico pensando no pior", "não paro de pensar", "cenários negativos", "e se der errado"])
    },

    # N2: Angry Hostility (Hostilidade) - 5 fragmentos
    {
        "fragment_id": "NEU_N2_001",
        "domain": "Neuroticism",
        "facet": "N2: Angry Hostility",
        "facet_code": "N2",
        "description": "Irrita-se facilmente com frustrações",
        "description_en": "Gets easily irritated by frustrations",
        "detection_pattern": "Detectar irritação fácil",
        "example_phrases": json.dumps(["me irrita", "fico com raiva", "perco a paciência", "me estresso fácil"])
    },
    {
        "fragment_id": "NEU_N2_002",
        "domain": "Neuroticism",
        "facet": "N2: Angry Hostility",
        "facet_code": "N2",
        "description": "Expressa raiva de forma intensa",
        "description_en": "Expresses anger intensely",
        "detection_pattern": "Detectar expressão intensa de raiva",
        "example_phrases": json.dumps(["explodi de raiva", "estava furioso", "dei um grito", "perdi a cabeça"])
    },
    {
        "fragment_id": "NEU_N2_003",
        "domain": "Neuroticism",
        "facet": "N2: Angry Hostility",
        "facet_code": "N2",
        "description": "Guarda ressentimento por ofensas",
        "description_en": "Holds resentment for offenses",
        "detection_pattern": "Detectar ressentimento",
        "example_phrases": json.dumps(["não esqueço o que fez", "guardo mágoa", "ainda me ressinto", "não perdoei"])
    },
    {
        "fragment_id": "NEU_N2_004",
        "domain": "Neuroticism",
        "facet": "N2: Angry Hostility",
        "facet_code": "N2",
        "description": "Sente hostilidade em situações competitivas",
        "description_en": "Feels hostility in competitive situations",
        "detection_pattern": "Detectar hostilidade competitiva",
        "example_phrases": json.dumps(["odeio perder", "raiva do concorrente", "quero vencer a qualquer custo", "inimizade"])
    },
    {
        "fragment_id": "NEU_N2_005",
        "domain": "Neuroticism",
        "facet": "N2: Angry Hostility",
        "facet_code": "N2",
        "description": "Reage com raiva a críticas",
        "description_en": "Reacts with anger to criticism",
        "detection_pattern": "Detectar raiva com críticas",
        "example_phrases": json.dumps(["não aceito crítica", "quem ele pensa que é", "me ofendeu", "fiquei com raiva da crítica"])
    },

    # N3: Depression (Depressão) - 5 fragmentos
    {
        "fragment_id": "NEU_N3_001",
        "domain": "Neuroticism",
        "facet": "N3: Depression",
        "facet_code": "N3",
        "description": "Sente tristeza frequentemente",
        "description_en": "Frequently feels sadness",
        "detection_pattern": "Detectar tristeza frequente",
        "example_phrases": json.dumps(["estou triste", "me sinto pra baixo", "desanimado", "sem alegria"])
    },
    {
        "fragment_id": "NEU_N3_002",
        "domain": "Neuroticism",
        "facet": "N3: Depression",
        "facet_code": "N3",
        "description": "Sente-se sem esperança às vezes",
        "description_en": "Sometimes feels hopeless",
        "detection_pattern": "Detectar desesperança",
        "example_phrases": json.dumps(["sem esperança", "não vai melhorar", "desisti", "não vejo saída"])
    },
    {
        "fragment_id": "NEU_N3_003",
        "domain": "Neuroticism",
        "facet": "N3: Depression",
        "facet_code": "N3",
        "description": "Tem dificuldade para sentir prazer",
        "description_en": "Has difficulty feeling pleasure",
        "detection_pattern": "Detectar anedonia",
        "example_phrases": json.dumps(["não sinto prazer", "nada me anima", "perdí interesse", "não tenho vontade"])
    },
    {
        "fragment_id": "NEU_N3_004",
        "domain": "Neuroticism",
        "facet": "N3: Depression",
        "facet_code": "N3",
        "description": "Sente-se sozinho mesmo acompanhado",
        "description_en": "Feels alone even when accompanied",
        "detection_pattern": "Detectar solidão emocional",
        "example_phrases": json.dumps(["me sinto sozinho", "isolado", "ninguém entende", "solidão mesmo com pessoas"])
    },
    {
        "fragment_id": "NEU_N3_005",
        "domain": "Neuroticism",
        "facet": "N3: Depression",
        "facet_code": "N3",
        "description": "Tem pensamentos negativos sobre si mesmo",
        "description_en": "Has negative thoughts about self",
        "detection_pattern": "Detectar pensamentos negativos sobre si",
        "example_phrases": json.dumps(["não sou bom o suficiente", "sou um fracasso", "me odeio", "não mereço"])
    },

    # N4: Self-Consciousness (Autoconsciência) - 5 fragmentos
    {
        "fragment_id": "NEU_N4_001",
        "domain": "Neuroticism",
        "facet": "N4: Self-Consciousness",
        "facet_code": "N4",
        "description": "Sente vergonha facilmente",
        "description_en": "Easily feels shame",
        "detection_pattern": "Detectar vergonha",
        "example_phrases": json.dumps(["que vergonha", "fiquei envergonhado", "morro de vergonha", "me senti constrangido"])
    },
    {
        "fragment_id": "NEU_N4_002",
        "domain": "Neuroticism",
        "facet": "N4: Self-Consciousness",
        "facet_code": "N4",
        "description": "Preocupa-se com o que outros pensam",
        "description_en": "Worries about what others think",
        "detection_pattern": "Detectar preocupação com julgamento",
        "example_phrases": json.dumps(["o que vão pensar", "medo de julgamento", "preocupado com a imagem", "vão me achar"])
    },
    {
        "fragment_id": "NEU_N4_003",
        "domain": "Neuroticism",
        "facet": "N4: Self-Consciousness",
        "facet_code": "N4",
        "description": "Sente desconforto em situações sociais",
        "description_en": "Feels discomfort in social situations",
        "detection_pattern": "Detectar desconforto social",
        "example_phrases": json.dumps(["desconfortável na festa", "não sei o que falar", "timidez", "me sinto fora do lugar"])
    },
    {
        "fragment_id": "NEU_N4_004",
        "domain": "Neuroticism",
        "facet": "N4: Self-Consciousness",
        "facet_code": "N4",
        "description": "Sente-se inferior aos outros",
        "description_en": "Feels inferior to others",
        "detection_pattern": "Detectar sentimento de inferioridade",
        "example_phrases": json.dumps(["sou pior que eles", "me sinto inferior", "não estou à altura", "todo mundo é melhor"])
    },
    {
        "fragment_id": "NEU_N4_005",
        "domain": "Neuroticism",
        "facet": "N4: Self-Consciousness",
        "facet_code": "N4",
        "description": "Evita ser o centro das atenções por medo",
        "description_en": "Avoids being center of attention out of fear",
        "detection_pattern": "Detectar evitação de atenção por medo",
        "example_phrases": json.dumps(["não quero atenção", "prefiro ficar quieto", "medo de falar em público", "evito exposição"])
    },

    # N5: Impulsiveness (Impulsividade) - 5 fragmentos
    {
        "fragment_id": "NEU_N5_001",
        "domain": "Neuroticism",
        "facet": "N5: Impulsiveness",
        "facet_code": "N5",
        "description": "Age por impulso sem pensar",
        "description_en": "Acts on impulse without thinking",
        "detection_pattern": "Detectar ação impulsiva",
        "example_phrases": json.dumps(["agi por impulso", "sem pensar", "me arrependi depois", "fiz sem querer"])
    },
    {
        "fragment_id": "NEU_N5_002",
        "domain": "Neuroticism",
        "facet": "N5: Impulsiveness",
        "facet_code": "N5",
        "description": "Tem dificuldade em resistir tentações",
        "description_en": "Has difficulty resisting temptations",
        "detection_pattern": "Detectar dificuldade com tentações",
        "example_phrases": json.dumps(["não resisti", "cedi à tentação", "fraqueza minha", "não consegui evitar"])
    },
    {
        "fragment_id": "NEU_N5_003",
        "domain": "Neuroticism",
        "facet": "N5: Impulsiveness",
        "facet_code": "N5",
        "description": "Come ou gasta demais quando estressado",
        "description_en": "Overeats or overspends when stressed",
        "detection_pattern": "Detectar comportamento compensatório",
        "example_phrases": json.dumps(["comi demais", "comprei por impulso", "gastei sem necessidade", "descontei na comida"])
    },
    {
        "fragment_id": "NEU_N5_004",
        "domain": "Neuroticism",
        "facet": "N5: Impulsiveness",
        "facet_code": "N5",
        "description": "Fala coisas que depois se arrepende",
        "description_en": "Says things later regretted",
        "detection_pattern": "Detectar fala impulsiva",
        "example_phrases": json.dumps(["falei demais", "não deveria ter dito", "escapou", "me arrependo de ter falado"])
    },
    {
        "fragment_id": "NEU_N5_005",
        "domain": "Neuroticism",
        "facet": "N5: Impulsiveness",
        "facet_code": "N5",
        "description": "Toma decisões precipitadas sob pressão",
        "description_en": "Makes hasty decisions under pressure",
        "detection_pattern": "Detectar decisões precipitadas",
        "example_phrases": json.dumps(["decidi na pressão", "me precipitei", "deveria ter esperado", "escolha apressada"])
    },

    # N6: Vulnerability (Vulnerabilidade) - 5 fragmentos
    {
        "fragment_id": "NEU_N6_001",
        "domain": "Neuroticism",
        "facet": "N6: Vulnerability",
        "facet_code": "N6",
        "description": "Sente-se sobrecarregado facilmente",
        "description_en": "Easily feels overwhelmed",
        "detection_pattern": "Detectar sobrecarga",
        "example_phrases": json.dumps(["sobrecarregado", "não dou conta", "é demais pra mim", "estou no limite"])
    },
    {
        "fragment_id": "NEU_N6_002",
        "domain": "Neuroticism",
        "facet": "N6: Vulnerability",
        "facet_code": "N6",
        "description": "Entra em pânico em crises",
        "description_en": "Panics in crises",
        "detection_pattern": "Detectar pânico em crises",
        "example_phrases": json.dumps(["entrei em pânico", "desesperei", "perdi o controle", "não sabia o que fazer"])
    },
    {
        "fragment_id": "NEU_N6_003",
        "domain": "Neuroticism",
        "facet": "N6: Vulnerability",
        "facet_code": "N6",
        "description": "Depende de outros para apoio emocional",
        "description_en": "Depends on others for emotional support",
        "detection_pattern": "Detectar dependência emocional",
        "example_phrases": json.dumps(["preciso de apoio", "não consigo sozinho", "preciso que me ajude", "dependendo de"])
    },
    {
        "fragment_id": "NEU_N6_004",
        "domain": "Neuroticism",
        "facet": "N6: Vulnerability",
        "facet_code": "N6",
        "description": "Sente-se desamparado em situações difíceis",
        "description_en": "Feels helpless in difficult situations",
        "detection_pattern": "Detectar desamparo",
        "example_phrases": json.dumps(["me sinto desamparado", "não tenho como resolver", "impotente", "sem recursos"])
    },
    {
        "fragment_id": "NEU_N6_005",
        "domain": "Neuroticism",
        "facet": "N6: Vulnerability",
        "facet_code": "N6",
        "description": "Recupera-se lentamente de estresse",
        "description_en": "Recovers slowly from stress",
        "detection_pattern": "Detectar recuperação lenta",
        "example_phrases": json.dumps(["ainda afetado", "demoro a me recuperar", "o estresse dura", "ainda não superei"])
    },
]


# ========================================
# FUNÇÃO PRINCIPAL DE AGREGAÇÃO
# ========================================

def get_all_fragments() -> List[Dict]:
    """
    Retorna todos os 150 fragmentos comportamentais.

    Returns:
        Lista de dicionários com dados dos fragmentos
    """
    all_fragments = []

    all_fragments.extend(EXTRAVERSION_FRAGMENTS)  # 30
    all_fragments.extend(OPENNESS_FRAGMENTS)  # 30
    all_fragments.extend(CONSCIENTIOUSNESS_FRAGMENTS)  # 30
    all_fragments.extend(AGREEABLENESS_FRAGMENTS)  # 30
    all_fragments.extend(NEUROTICISM_FRAGMENTS)  # 30

    return all_fragments


def get_fragments_by_domain(domain: str) -> List[Dict]:
    """
    Retorna fragmentos de um domínio específico.

    Args:
        domain: "Extraversion", "Openness", "Conscientiousness",
                "Agreeableness", ou "Neuroticism"

    Returns:
        Lista de 30 fragmentos do domínio
    """
    domain_map = {
        "Extraversion": EXTRAVERSION_FRAGMENTS,
        "Openness": OPENNESS_FRAGMENTS,
        "Conscientiousness": CONSCIENTIOUSNESS_FRAGMENTS,
        "Agreeableness": AGREEABLENESS_FRAGMENTS,
        "Neuroticism": NEUROTICISM_FRAGMENTS
    }

    return domain_map.get(domain, [])


def get_fragments_by_facet(facet_code: str) -> List[Dict]:
    """
    Retorna fragmentos de uma faceta específica.

    Args:
        facet_code: Ex: "E1", "O3", "C5", "A2", "N4"

    Returns:
        Lista de 5 fragmentos da faceta
    """
    all_fragments = get_all_fragments()
    return [f for f in all_fragments if f['facet_code'] == facet_code]


# ========================================
# ESTATÍSTICAS
# ========================================

def get_statistics() -> Dict:
    """Retorna estatísticas dos fragmentos."""
    all_fragments = get_all_fragments()

    stats = {
        "total": len(all_fragments),
        "by_domain": {},
        "by_facet": {}
    }

    for fragment in all_fragments:
        domain = fragment['domain']
        facet = fragment['facet_code']

        stats["by_domain"][domain] = stats["by_domain"].get(domain, 0) + 1
        stats["by_facet"][facet] = stats["by_facet"].get(facet, 0) + 1

    return stats


# ========================================
# TESTE
# ========================================

if __name__ == "__main__":
    print("IRT Fragments Seed - JungAgent")
    print("=" * 50)

    stats = get_statistics()
    print(f"\nTotal de fragmentos: {stats['total']}")

    print("\nPor domínio:")
    for domain, count in stats['by_domain'].items():
        print(f"  {domain}: {count}")

    print("\nPor faceta (primeiros 10):")
    for facet, count in list(stats['by_facet'].items())[:10]:
        print(f"  {facet}: {count}")

    print(f"\n✅ {stats['total']} fragmentos prontos para seed")
