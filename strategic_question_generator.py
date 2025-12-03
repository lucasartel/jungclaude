#!/usr/bin/env python3
"""
strategic_question_generator.py - Gerador de Perguntas Estratégicas
==================================================================

Gera perguntas conversacionais naturais para preencher gaps
em análises psicométricas.

Autor: Sistema Jung
Data: 2025-12-03
Versão: 1.0.0
"""

from typing import Dict, List, Optional
import random
import logging

logger = logging.getLogger(__name__)


class StrategicQuestionGenerator:
    """
    Gera perguntas estratégicas adaptadas ao perfil do usuário
    para enriquecer análise psicométrica de forma natural.
    """

    # ============================================================================
    # BANCO DE TEMPLATES DE PERGUNTAS POR DIMENSÃO
    # ============================================================================

    QUESTION_TEMPLATES = {
        "openness": [
            # Tipo: Direct Masked
            {
                "type": "direct_masked",
                "template": "Tenho refletido sobre como cada pessoa lida com mudanças... {name}, você costuma abraçar o novo ou prefere o familiar e conhecido?",
                "reveals": ["abertura a experiências", "tolerância ao risco"],
                "tone": "reflexivo"
            },
            {
                "type": "direct_masked",
                "template": "{name}, percebi que não conversamos muito sobre criatividade... Como você expressa seu lado criativo no dia a dia?",
                "reveals": ["criatividade", "expressão artística"],
                "tone": "curioso"
            },
            # Tipo: Storytelling
            {
                "type": "storytelling",
                "template": "Jung falava sobre pessoas que veem o mundo como um livro aberto, cheio de possibilidades inexploradas... Isso ressoa com você, {name}?",
                "reveals": ["curiosidade intelectual", "imaginação"],
                "tone": "filosófico"
            },
            {
                "type": "storytelling",
                "template": "Li recentemente que algumas pessoas preferem rotinas previsíveis, enquanto outras buscam constantemente experiências novas... Com qual você se identifica mais?",
                "reveals": ["preferência por novidade vs rotina"],
                "tone": "neutro"
            },
            # Tipo: Dilemma
            {
                "type": "dilemma",
                "template": "Imagine que você tem uma semana de férias inesperada. O que soa mais atraente: visitar um lugar totalmente novo ou revisitar um lugar favorito?",
                "reveals": ["busca por novidade", "zona de conforto"],
                "tone": "leve"
            },
            {
                "type": "dilemma",
                "template": "Se você pudesse escolher entre aprender algo prático e útil OU explorar um tópico fascinante mas 'inútil', qual escolheria?",
                "reveals": ["curiosidade intelectual", "pragmatismo"],
                "tone": "provocativo"
            },
            # Tipo: Reflexão
            {
                "type": "reflection",
                "template": "Tenho curiosidade, {name}... Quando foi a última vez que você fez algo pela primeira vez? Como foi?",
                "reveals": ["abertura a experiências", "busca por novidade"],
                "tone": "pessoal"
            },
            {
                "type": "reflection",
                "template": "Você se considera mais uma pessoa de 'arte e filosofia' ou 'números e fatos'? Ou talvez algo no meio?",
                "reveals": ["interesses intelectuais", "abstrato vs concreto"],
                "tone": "exploratório"
            },
            # Contextos específicos
            {
                "type": "contextual",
                "template": "No trabalho, você prefere seguir processos estabelecidos ou criar novos métodos?",
                "reveals": ["inovação", "conformidade"],
                "tone": "profissional",
                "context": "trabalho"
            },
            {
                "type": "contextual",
                "template": "Quando você encontra um problema, tende a buscar soluções criativas ou aplicar métodos testados?",
                "reveals": ["pensamento criativo", "preferências de resolução"],
                "tone": "prático",
                "context": "desafios"
            }
        ],

        "conscientiousness": [
            # Tipo: Direct Masked
            {
                "type": "direct_masked",
                "template": "Estava refletindo sobre como cada pessoa organiza sua vida... {name}, você se considera mais organizado e planejado, ou mais espontâneo e flexível?",
                "reveals": ["organização", "planejamento vs espontaneidade"],
                "tone": "reflexivo"
            },
            {
                "type": "direct_masked",
                "template": "Tenho curiosidade sobre algo, {name}... Como você lida com prazos e compromissos? Prefere antecipar ou resolver no último momento?",
                "reveals": ["autodisciplina", "procrastinação"],
                "tone": "direto"
            },
            # Tipo: Storytelling
            {
                "type": "storytelling",
                "template": "Existe um ditado que diz 'o importante é fazer, não como fazer'... Mas para algumas pessoas, o 'como' importa muito. O que você acha?",
                "reveals": ["atenção aos detalhes", "perfeccionismo"],
                "tone": "provocativo"
            },
            # Tipo: Dilemma
            {
                "type": "dilemma",
                "template": "Imagine que você tem um projeto importante mas sem prazo definido. Você: (A) cria seu próprio cronograma e segue, ou (B) trabalha conforme a inspiração vem?",
                "reveals": ["autodisciplina", "estrutura vs flexibilidade"],
                "tone": "situacional"
            },
            {
                "type": "dilemma",
                "template": "Dois caminhos: ser conhecido por 'sempre entregar resultados consistentes' OU 'ter ideias brilhantes ocasionalmente'. Qual ressoa mais com você?",
                "reveals": ["confiabilidade", "valores de trabalho"],
                "tone": "valores"
            },
            # Tipo: Reflexão
            {
                "type": "reflection",
                "template": "Como é sua mesa de trabalho/estudo agora? Organizada ou mais... 'criativa'? 😄",
                "reveals": ["organização física", "ordem"],
                "tone": "leve"
            },
            {
                "type": "reflection",
                "template": "{name}, você faz listas de tarefas? Se sim, o quanto você segue elas?",
                "reveals": ["planejamento", "follow-through"],
                "tone": "prático"
            },
            # Contextos específicos
            {
                "type": "contextual",
                "template": "No trabalho, você prefere ter tudo planejado com antecedência ou deixar espaço para improviso?",
                "reveals": ["planejamento profissional", "flexibilidade"],
                "tone": "profissional",
                "context": "trabalho"
            },
            {
                "type": "contextual",
                "template": "Quando você tem um objetivo importante, como você costuma abordar? Passo a passo ou visão geral primeiro?",
                "reveals": ["estratégia de objetivos", "método"],
                "tone": "estratégico",
                "context": "objetivos"
            }
        ],

        "extraversion": [
            # Tipo: Direct Masked
            {
                "type": "direct_masked",
                "template": "Estava pensando, {name}... Você recarrega suas energias estando com pessoas ou ficando um tempo sozinho?",
                "reveals": ["introversão vs extroversão", "fonte de energia"],
                "tone": "pessoal"
            },
            {
                "type": "direct_masked",
                "template": "Tenho curiosidade... Em um evento social, você costuma ser mais reservado e observador, ou ativo e interativo?",
                "reveals": ["sociabilidade", "comportamento social"],
                "tone": "observacional"
            },
            # Tipo: Storytelling
            {
                "type": "storytelling",
                "template": "Jung descrevia dois tipos de energia: uma que se expande para fora e busca estímulos externos, outra que se recolhe para reflexão interna... Qual ressoa mais com você?",
                "reveals": ["orientação energética", "preferência social"],
                "tone": "jungiano"
            },
            # Tipo: Dilemma
            {
                "type": "dilemma",
                "template": "Fim de semana livre: você preferiria um evento social animado com várias pessoas OU um encontro tranquilo com poucos amigos próximos?",
                "reveals": ["preferência social", "intensidade de interação"],
                "tone": "situacional"
            },
            {
                "type": "dilemma",
                "template": "Durante uma pausa, você sente vontade de conversar com alguém ou de ter um momento para si?",
                "reveals": ["necessidade de interação", "tempo sozinho"],
                "tone": "cotidiano"
            },
            # Tipo: Reflexão
            {
                "type": "reflection",
                "template": "Você se sente energizado ou esgotado após um dia cheio de interações sociais?",
                "reveals": ["impacto de socialização", "níveis de energia"],
                "tone": "autoconhecimento"
            },
            {
                "type": "reflection",
                "template": "{name}, você diria que gosta mais de falar ou de ouvir em uma conversa?",
                "reveals": ["estilo comunicativo", "assertividade social"],
                "tone": "comunicação"
            },
            # Contextos específicos
            {
                "type": "contextual",
                "template": "No trabalho, você prefere trabalhar em equipe ou de forma independente?",
                "reveals": ["preferência de trabalho", "colaboração"],
                "tone": "profissional",
                "context": "trabalho"
            },
            {
                "type": "contextual",
                "template": "Como você costuma fazer amigos? Você inicia conversas facilmente ou prefere que outros venham até você?",
                "reveals": ["iniciativa social", "approach social"],
                "tone": "relacional",
                "context": "relacionamentos"
            }
        ],

        "agreeableness": [
            # Tipo: Direct Masked
            {
                "type": "direct_masked",
                "template": "Tenho refletido sobre diferentes formas de lidar com conflitos... {name}, quando há um desacordo, você tende a buscar harmonia ou defender firmemente seu ponto?",
                "reveals": ["gestão de conflitos", "assertividade vs harmonização"],
                "tone": "situacional"
            },
            {
                "type": "direct_masked",
                "template": "Percebi algo interessante, {name}... Você se vê mais como alguém que ajuda os outros ou que incentiva as pessoas a serem independentes?",
                "reveals": ["altruísmo", "tendência a ajudar"],
                "tone": "observacional"
            },
            # Tipo: Storytelling
            {
                "type": "storytelling",
                "template": "Há uma tensão interessante entre ser empático e se proteger de ser aproveitado... Como você equilibra isso?",
                "reveals": ["empatia", "boundaries", "confiança"],
                "tone": "complexo"
            },
            # Tipo: Dilemma
            {
                "type": "dilemma",
                "template": "Se você vê alguém sendo injustiçado, você: (A) intervém imediatamente, ou (B) avalia a situação antes de agir?",
                "reveals": ["senso de justiça", "impulsividade altruísta"],
                "tone": "ético"
            },
            {
                "type": "dilemma",
                "template": "Em uma negociação, você prefere garantir que todos saiam ganhando OU focar em obter o melhor resultado para si?",
                "reveals": ["cooperação vs competição", "estratégia social"],
                "tone": "estratégico"
            },
            # Tipo: Reflexão
            {
                "type": "reflection",
                "template": "Você se considera mais uma pessoa competitiva ou colaborativa?",
                "reveals": ["orientação social", "competitividade"],
                "tone": "autoavaliação"
            },
            {
                "type": "reflection",
                "template": "{name}, quando alguém te pede ajuda, qual sua reação instintiva? Você ajuda prontamente ou pondera primeiro?",
                "reveals": ["disposição para ajudar", "boundaries"],
                "tone": "comportamental"
            },
            # Contextos específicos
            {
                "type": "contextual",
                "template": "No trabalho, você prefere ambientes colaborativos ou mais competitivos?",
                "reveals": ["preferência de ambiente", "dinâmica de trabalho"],
                "tone": "profissional",
                "context": "trabalho"
            },
            {
                "type": "contextual",
                "template": "Nos seus relacionamentos, você tende a perdoar facilmente ou leva tempo para processar mágoas?",
                "reveals": ["perdão", "gestão emocional"],
                "tone": "relacional",
                "context": "relacionamentos"
            }
        ],

        "neuroticism": [
            # Tipo: Direct Masked
            {
                "type": "direct_masked",
                "template": "Estava refletindo sobre como pessoas lidam com pressão... {name}, em situações estressantes, você costuma manter a calma ou sente a tensão mais intensamente?",
                "reveals": ["estabilidade emocional", "reação ao estresse"],
                "tone": "cuidadoso"
            },
            {
                "type": "direct_masked",
                "template": "Tenho curiosidade, {name}... Você diria que é mais uma pessoa que se preocupa com antecedência ou que lida com as coisas conforme surgem?",
                "reveals": ["ansiedade antecipatória", "preocupação"],
                "tone": "neutro"
            },
            # Tipo: Storytelling
            {
                "type": "storytelling",
                "template": "Jung dizia que a sensibilidade emocional pode ser tanto um dom quanto um desafio... Como você vê sua própria sensibilidade?",
                "reveals": ["sensibilidade emocional", "autopercepção"],
                "tone": "validador"
            },
            # Tipo: Dilemma
            {
                "type": "dilemma",
                "template": "Diante de um desafio inesperado, você: (A) se sente energizado para resolver, ou (B) sente um pouco de ansiedade primeiro?",
                "reveals": ["reação a desafios", "resiliência"],
                "tone": "situacional"
            },
            {
                "type": "dilemma",
                "template": "Você prefere saber de um problema com antecedência (mesmo que cause preocupação) OU descobrir apenas quando precisar lidar?",
                "reveals": ["tolerância a incerteza", "preferência por controle"],
                "tone": "escolha"
            },
            # Tipo: Reflexão
            {
                "type": "reflection",
                "template": "Como você descreveria seu nível de calma em uma escala de 'zen master' a 'mente sempre ativa'? 😊",
                "reveals": ["estabilidade emocional", "ansiedade"],
                "tone": "leve"
            },
            {
                "type": "reflection",
                "template": "{name}, quando algo te incomoda, você consegue 'deixar pra lá' facilmente ou fica pensando nisso?",
                "reveals": ["ruminação", "regulação emocional"],
                "tone": "prático"
            },
            # Contextos específicos
            {
                "type": "contextual",
                "template": "No trabalho, prazos apertados te motivam ou te estressam?",
                "reveals": ["reação a pressão", "thriving under pressure"],
                "tone": "profissional",
                "context": "trabalho"
            },
            {
                "type": "contextual",
                "template": "Quando enfrenta um período difícil, você costuma se recuperar rápido ou leva um tempo?",
                "reveals": ["resiliência", "recuperação emocional"],
                "tone": "resiliente",
                "context": "desafios"
            }
        ]
    }

    # ============================================================================
    # ADAPTIVE TONE RULES
    # ============================================================================

    TONE_ADAPTATION_RULES = {
        "high_openness": {
            "preferred_types": ["storytelling", "reflection", "dilemma"],
            "avoid_types": [],
            "style": "Use linguagem filosófica e abstrata"
        },
        "low_openness": {
            "preferred_types": ["direct_masked", "contextual"],
            "avoid_types": ["storytelling"],
            "style": "Use linguagem prática e concreta"
        },
        "high_conscientiousness": {
            "preferred_types": ["dilemma", "contextual"],
            "avoid_types": [],
            "style": "Estruture bem a pergunta"
        },
        "low_conscientiousness": {
            "preferred_types": ["reflection", "direct_masked"],
            "avoid_types": [],
            "style": "Mantenha casual e não-julgador"
        },
        "high_extraversion": {
            "preferred_types": ["direct_masked", "contextual"],
            "avoid_types": [],
            "style": "Tom energético e direto"
        },
        "low_extraversion": {
            "preferred_types": ["reflection", "storytelling"],
            "avoid_types": [],
            "style": "Tom gentil e contemplativo"
        },
        "high_agreeableness": {
            "preferred_types": ["reflection", "storytelling"],
            "avoid_types": [],
            "style": "Tom empático e colaborativo"
        },
        "low_agreeableness": {
            "preferred_types": ["dilemma", "direct_masked"],
            "avoid_types": [],
            "style": "Tom direto e objetivo"
        },
        "high_neuroticism": {
            "preferred_types": ["reflection", "storytelling"],
            "avoid_types": ["dilemma"],  # Evitar pressão
            "style": "Tom cuidadoso e validador"
        },
        "low_neuroticism": {
            "preferred_types": ["dilemma", "contextual"],
            "avoid_types": [],
            "style": "Tom descontraído e direto"
        }
    }

    def __init__(self, db):
        """
        Args:
            db: DatabaseManager instance
        """
        self.db = db

    def generate_question(
        self,
        target_dimension: str,
        user_id: str,
        user_name: str,
        context_hint: Optional[str] = None
    ) -> Dict:
        """
        Gera pergunta estratégica adaptada ao perfil do usuário

        Args:
            target_dimension: Dimensão Big Five alvo
            user_id: ID do usuário
            user_name: Nome do usuário
            context_hint: Contexto sugerido (opcional)

        Returns:
            {
                "question": str,
                "dimension": str,
                "type": str,
                "reveals": List[str],
                "tone": str,
                "metadata": Dict
            }
        """

        logger.info(f"🎯 [QUESTION GEN] Gerando pergunta para {target_dimension}")

        # Buscar perfil atual
        psychometrics = self.db.get_psychometrics(user_id)

        # Selecionar template apropriado
        template = self._select_best_template(
            dimension=target_dimension,
            psychometrics=psychometrics,
            context_hint=context_hint
        )

        # Gerar pergunta a partir do template
        question_text = template["template"].format(name=user_name)

        result = {
            "question": question_text,
            "dimension": target_dimension,
            "type": template["type"],
            "reveals": template["reveals"],
            "tone": template["tone"],
            "metadata": {
                "context": template.get("context", context_hint),
                "adapted": psychometrics is not None
            }
        }

        logger.info(f"   ✅ Pergunta gerada: {template['type']} / {template['tone']}")

        return result

    def _select_best_template(
        self,
        dimension: str,
        psychometrics: Optional[Dict],
        context_hint: Optional[str]
    ) -> Dict:
        """
        Seleciona melhor template baseado no perfil atual
        """

        templates = self.QUESTION_TEMPLATES.get(dimension, [])

        if not templates:
            # Fallback genérico
            return {
                "type": "direct_masked",
                "template": f"Tenho curiosidade sobre algo, {{name}}... Como você se vê em relação a {dimension}?",
                "reveals": [dimension],
                "tone": "genérico"
            }

        # Se não tem perfil, escolher aleatoriamente
        if not psychometrics:
            return random.choice(templates)

        # Filtrar por contexto se fornecido
        if context_hint:
            context_templates = [t for t in templates if t.get("context") == context_hint]
            if context_templates:
                templates = context_templates

        # Adaptar baseado em outras dimensões do perfil
        adapted_templates = self._filter_by_profile(templates, psychometrics)

        # Escolher aleatoriamente entre os adaptados
        return random.choice(adapted_templates if adapted_templates else templates)

    def _filter_by_profile(
        self,
        templates: List[Dict],
        psychometrics: Dict
    ) -> List[Dict]:
        """
        Filtra templates baseado no perfil conhecido
        """

        # Classificar perfil em high/low para cada dimensão
        profile_classification = self._classify_profile(psychometrics)

        # Coletar tipos preferidos e evitados
        preferred_types = set()
        avoid_types = set()

        for trait, level in profile_classification.items():
            key = f"{level}_{trait}"
            if key in self.TONE_ADAPTATION_RULES:
                rules = self.TONE_ADAPTATION_RULES[key]
                preferred_types.update(rules.get("preferred_types", []))
                avoid_types.update(rules.get("avoid_types", []))

        # Filtrar templates
        filtered = [
            t for t in templates
            if t["type"] not in avoid_types
        ]

        # Priorizar templates preferidos
        prioritized = [
            t for t in filtered
            if t["type"] in preferred_types
        ]

        return prioritized if prioritized else filtered

    def _classify_profile(self, psychometrics: Dict) -> Dict:
        """
        Classifica perfil em high/low para cada dimensão

        Returns:
            {"openness": "high", "conscientiousness": "low", ...}
        """

        classification = {}

        for dimension in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            score = psychometrics.get(f"{dimension}_score", 50)

            if score >= 65:
                classification[dimension] = "high"
            elif score <= 35:
                classification[dimension] = "low"
            else:
                classification[dimension] = "medium"

        return classification
