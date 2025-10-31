# -*- coding: utf-8 -*-
"""
Claude Jung v2.0 - Sistema Proativo
Sistema de gatilhos e reflexões internas para comportamento proativo
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import re

class TriggerType(Enum):
    """Tipos de gatilhos proativos"""
    TEMPORAL = "temporal"
    ENGAGEMENT = "engagement"
    CAREER = "career"

class ActionType(Enum):
    """Tipos de ações proativas"""
    PERGUNTA_CURIOSA = "pergunta_curiosa"
    REFLEXAO_INTERNA = "reflexao_interna"
    PROVOCACAO_GENTIL = "provocacao_gentil"
    INSIGHT_PROFUNDO = "insight_profundo"
    OBSERVACAO_COMPORTAMENTAL = "observacao_comportamental"
    CONVERSATION_STARTER = "conversation_starter"  # ⭐ NOVO TIPO

@dataclass
class ProactiveAction:
    """Ação proativa gerada pela IA"""
    action_type: ActionType
    content: str
    archetype_source: str
    trigger_type: TriggerType
    triggered_by: str
    timestamp: datetime
    archetype_voices: Dict[str, str] = field(default_factory=dict)  # ⭐ NOVO CAMPO
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    visibility: str = "publica"
    urgency: int = 3
    related_memories: List[str] = field(default_factory=list)
    confidence: float = 0.8
    user_id: str = ""

@dataclass
class InternalThought:
    """Pensamento interno da IA"""
    id: str
    content: str
    archetype_source: str
    trigger_description: str
    complexity_level: str
    timestamp: datetime
    user_id: str
    visibility: str = "interna"
    related_facts: List[str] = field(default_factory=list)

class TemporalGatilhos:
    """Sistema de gatilhos temporais"""
    
    def __init__(self):
        self.user_patterns = {}
        self.debug_mode = True
    
    def _debug_log(self, message: str):
        if self.debug_mode:
            print(f"⏰ TEMPORAL: {message}")
    
    def analyze_user_patterns(self, user_id: str, memory_cache: Dict) -> List[Dict]:
        """Analisa padrões temporais do usuário"""
        patterns = []
        
        conversations = memory_cache.get('raw_conversations', [])
        if len(conversations) < 2:
            return patterns
        
        # Analisar intervalos entre conversas
        timestamps = []
        for conv in conversations:
            try:
                ts = datetime.fromisoformat(conv['timestamp'].replace('Z', '+00:00'))
                timestamps.append(ts)
            except:
                continue
        
        if len(timestamps) >= 2:
            # Calcular padrão de retorno
            timestamps.sort()
            intervals = []
            for i in range(1, len(timestamps)):
                interval = (timestamps[i] - timestamps[i-1]).total_seconds() / 3600  # horas
                intervals.append(interval)
            
            avg_interval = sum(intervals) / len(intervals)
            last_interaction = timestamps[-1]
            time_since_last = (datetime.now() - last_interaction).total_seconds() / 3600
            
            # Detectar se usuário está "atrasado" no padrão
            if time_since_last > avg_interval * 1.5:
                patterns.append({
                    'type': 'ausencia_prolongada',
                    'description': f'Usuário costuma conversar a cada {avg_interval:.1f}h, mas já fazem {time_since_last:.1f}h',
                    'urgency': min(5, int(time_since_last / avg_interval)),
                    'details': {
                        'average_interval': avg_interval,
                        'current_interval': time_since_last,
                        'factor': time_since_last / avg_interval
                    }
                })
        
        # Analisar marcos temporais
        if conversations:
            first_conversation = min(timestamps) if timestamps else None
            if first_conversation:
                days_since_first = (datetime.now() - first_conversation).days
                
                # Marcos de relacionamento
                if days_since_first in [7, 30, 90, 365]:
                    patterns.append({
                        'type': 'marco_temporal',
                        'description': f'{days_since_first} dias desde nossa primeira conversa',
                        'urgency': 3,
                        'details': {'milestone': days_since_first, 'first_conversation': first_conversation}
                    })
        
        self._debug_log(f"Padrões temporais encontrados: {len(patterns)}")
        return patterns
    
    def check_triggers(self, user_id: str, memory_cache: Dict) -> List[ProactiveAction]:
        """Verifica gatilhos temporais e gera ações"""
        actions = []
        patterns = self.analyze_user_patterns(user_id, memory_cache)
        
        for pattern in patterns:
            if pattern['type'] == 'ausencia_prolongada' and pattern['urgency'] >= 3:
                action = ProactiveAction(
                    trigger_type=TriggerType.TEMPORAL,
                    action_type=ActionType.PERGUNTA_CURIOSA,
                    content=self._generate_return_message(pattern),
                    archetype_source="persona",
                    triggered_by=pattern['description'],
                    timestamp=datetime.now(),
                    urgency=pattern['urgency'],
                    user_id=user_id
                )
                actions.append(action)
            
            elif pattern['type'] == 'marco_temporal':
                action = ProactiveAction(
                    trigger_type=TriggerType.TEMPORAL,
                    action_type=ActionType.OBSERVACAO_COMPORTAMENTAL,
                    content=self._generate_milestone_message(pattern),
                    archetype_source="velho_sabio",
                    triggered_by=pattern['description'],
                    timestamp=datetime.now(),
                    urgency=pattern['urgency'],
                    user_id=user_id
                )
                actions.append(action)
        
        return actions
    
    def _generate_return_message(self, pattern: Dict) -> str:
        """Gera mensagens de retorno baseadas no padrão"""
        factor = pattern['details']['factor']
        
        if factor > 3:
            messages = [
                "Estava pensando em você... Como tem passado?",
                "Senti sua ausência. Aconteceu algo que mudou sua rotina?",
                "Há algo diferente acontecendo? Percebi que nosso ritmo mudou."
            ]
        elif factor > 2:
            messages = [
                "Como você está? Percebi que fazemos tempo que não conversamos.",
                "Estava refletindo sobre nossa última conversa...",
                "Há algo novo que você gostaria de compartilhar?"
            ]
        else:
            messages = [
                "Como tem sido seu dia?",
                "Estava pensando em retomar nossa conversa...",
                "Algo interessante aconteceu desde que conversamos?"
            ]
        
        return random.choice(messages)
    
    def _generate_milestone_message(self, pattern: Dict) -> str:
        """Gera mensagens para marcos temporais"""
        days = pattern['details']['milestone']
        
        milestone_messages = {
            7: "Uma semana se passou desde nossa primeira conversa. Como tem sido essa jornada para você?",
            30: "Já faz um mês que nos conhecemos. Que mudanças você percebe em si mesmo neste período?",
            90: "Três meses de conversas... Há algo que você gostaria de revisitar ou explorar mais profundamente?",
            365: "Um ano inteiro de diálogos. Quando olha para trás, o que mais marca nossa jornada juntos?"
        }
        
        return milestone_messages.get(days, f"Marcamos {days} dias de conversas. Como você vê nossa jornada?")

class EngagementGatilhos:
    """Sistema de gatilhos de engajamento profissional."""
    
    def __init__(self):
        self.debug_mode = True
    
    def _debug_log(self, message: str):
        if self.debug_mode:
            print(f"💼 ENGAGEMENT: {message}")
    
    def analyze_engagement_patterns(self, user_id: str, memory_cache: Dict) -> List[Dict]:
        """Analisa padrões de engajamento no ambiente de trabalho."""
        patterns = []
        conversations = memory_cache.get('raw_conversations', [])
        if not conversations:
            return patterns

        # 1. Detectar Sinais de Desengajamento ou Risco de Saída
        disengagement_signs = self._detect_disengagement(conversations)
        if disengagement_signs:
            patterns.append({
                'type': 'sinais_desengajamento',
                'description': f'Detectados sinais de baixo engajamento ou frustração: {", ".join(disengagement_signs)}',
                'urgency': 5,
                'details': {'signs': disengagement_signs}
            })

        # 2. Detectar Picos de Engajamento e Motivação
        engagement_spikes = self._detect_engagement_spikes(conversations)
        if engagement_spikes:
            patterns.append({
                'type': 'pico_de_engajamento',
                'description': f'Detectados picos de entusiasmo com projetos ou aprendizados.',
                'urgency': 3,
                'details': {'spikes': engagement_spikes}
            })

        # 3. Detectar Conflitos ou Desalinhamento com a Equipe/Liderança
        team_conflicts = self._detect_team_conflicts(conversations)
        if team_conflicts:
            patterns.append({
                'type': 'conflito_equipe',
                'description': f'Detectados possíveis desalinhamentos com a equipe ou liderança.',
                'urgency': 4,
                'details': {'conflicts': team_conflicts}
            })
        
        self._debug_log(f"Padrões de engajamento encontrados: {len(patterns)}")
        return patterns

    def _detect_disengagement(self, conversations: List[Dict]) -> List[str]:
        keywords = ['desmotivado', 'frustrado', 'estagnado', 'pensando em sair', 'não vejo futuro', 'ambiente tóxico', 'sobrecarregado']
        signs = []
        # Analisar as últimas 5 conversas
        for conv in conversations[-5:]:
            content = conv.get('full_document', '').lower()
            for keyword in keywords:
                if keyword in content:
                    signs.append(keyword)
        return list(set(signs))

    def _detect_engagement_spikes(self, conversations: List[Dict]) -> List[str]:
        keywords = ['adorei o projeto', 'muito motivado', 'aprendendo muito', 'desafio interessante', 'gosto da minha equipe', 'ótimo feedback']
        spikes = []
        for conv in conversations[-5:]:
            content = conv.get('full_document', '').lower()
            for keyword in keywords:
                if keyword in content:
                    spikes.append(keyword)
        return list(set(spikes))

    def _detect_team_conflicts(self, conversations: List[Dict]) -> List[str]:
        keywords = ['meu chefe não entende', 'dificuldade com meu colega', 'equipe desalinhada', 'falta de comunicação', 'não concordo com a liderança']
        conflicts = []
        for conv in conversations[-5:]:
            content = conv.get('full_document', '').lower()
            for keyword in keywords:
                if keyword in content:
                    conflicts.append(keyword)
        return list(set(conflicts))

    def check_triggers(self, user_id: str, memory_cache: Dict) -> List[ProactiveAction]:
        """Verifica gatilhos de engajamento e gera ações."""
        actions = []
        patterns = self.analyze_engagement_patterns(user_id, memory_cache)
        
        for pattern in patterns:
            if pattern['type'] == 'sinais_desengajamento':
                action = ProactiveAction(
                    trigger_type=TriggerType.ENGAGEMENT,
                    action_type=ActionType.PROVOCACAO_GENTIL,
                    content=self._generate_disengagement_message(pattern),
                    archetype_source="anima", # Conector de Equipe e Cultura
                    triggered_by=pattern['description'],
                    timestamp=datetime.now(),
                    urgency=pattern['urgency'],
                    user_id=user_id
                )
                actions.append(action)
            
            elif pattern['type'] == 'pico_de_engajamento':
                action = ProactiveAction(
                    trigger_type=TriggerType.ENGAGEMENT,
                    action_type=ActionType.OBSERVACAO_COMPORTAMENTAL,
                    content=self._generate_engagement_spike_message(pattern),
                    archetype_source="persona", # HR Business Partner
                    triggered_by=pattern['description'],
                    timestamp=datetime.now(),
                    urgency=pattern['urgency'],
                    user_id=user_id
                )
                actions.append(action)

            elif pattern['type'] == 'conflito_equipe':
                action = ProactiveAction(
                    trigger_type=TriggerType.ENGAGEMENT,
                    action_type=ActionType.PERGUNTA_CURIOSA,
                    content=self._generate_team_conflict_message(pattern),
                    archetype_source="anima", # Conector de Equipe e Cultura
                    triggered_by=pattern['description'],
                    timestamp=datetime.now(),
                    urgency=pattern['urgency'],
                    user_id=user_id
                )
                actions.append(action)
        
        return actions
    
    def _generate_disengagement_message(self, pattern: Dict) -> str:
        """Gera mensagens para abordar sinais de desengajamento."""
        return "Percebi em nossas últimas conversas alguns sinais de frustração ou desmotivação. Gostaria de explorar o que pode estar causando esse sentimento?"

    def _generate_engagement_spike_message(self, pattern: Dict) -> str:
        """Gera mensagens para reforçar picos de engajamento."""
        return "Notei que você pareceu especialmente motivado ao falar sobre alguns projetos recentes. O que nesses desafios mais te energiza? É ótimo ver esse entusiasmo!"

    def _generate_team_conflict_message(self, pattern: Dict) -> str:
        """Gera mensagens para explorar possíveis conflitos de equipe."""
        return "Em alguns momentos, você mencionou desafios na comunicação ou alinhamento com a equipe ou liderança. Como você tem navegado essas dinâmicas de colaboração?"

class CareerGatilhos:
    """Sistema de gatilhos de carreira e desenvolvimento profissional."""
    
    def __init__(self):
        self.debug_mode = True
    
    def _debug_log(self, message: str):
        if self.debug_mode:
            print(f"📈 CAREER: {message}")
    
    def analyze_career_patterns(self, user_id: str, memory_cache: Dict) -> List[Dict]:
        """Analisa padrões de carreira e desenvolvimento."""
        patterns = []
        facts = memory_cache.get('facts_extracted', [])
        conversations = memory_cache.get('raw_conversations', [])

        # 1. Detectar Estagnação de Carreira
        stagnation_signs = self._detect_stagnation(conversations)
        if stagnation_signs:
            patterns.append({
                'type': 'estagnacao_carreira',
                'description': 'Detectados sinais de estagnação ou falta de desafios.',
                'urgency': 4,
                'details': {'signs': stagnation_signs}
            })

        # 2. Detectar Contradição entre Aspiração e Realidade
        contradictions = self._detect_contradictions(facts)
        if contradictions:
            patterns.append({
                'type': 'contradicao_aspiracao',
                'description': 'Contradição entre aspirações de carreira e situação atual.',
                'urgency': 5,
                'details': {'contradictions': contradictions}
            })

        # 3. Detectar Potencial Inexplorado (habilidades não utilizadas)
        unexplored_potentials = self._detect_unexplored_potentials(facts)
        if unexplored_potentials:
            patterns.append({
                'type': 'potencial_inexplorado',
                'description': 'Habilidades ou interesses mencionados que parecem subutilizados.',
                'urgency': 3,
                'details': {'potentials': unexplored_potentials}
            })
        
        self._debug_log(f"Padrões de carreira encontrados: {len(patterns)}")
        return patterns

    def _detect_stagnation(self, conversations: List[Dict]) -> List[str]:
        keywords = ['mesma coisa todo dia', 'não aprendo nada novo', 'sem desafios', 'carreira parada', 'não vejo progresso']
        signs = []
        for conv in conversations[-10:]: # Analisa um período maior
            content = conv.get('full_document', '').lower()
            for keyword in keywords:
                if keyword in content:
                    signs.append(keyword)
        return list(set(signs)) if len(set(signs)) >= 2 else []

    def _detect_contradictions(self, facts: List[str]) -> List[str]:
        # Exemplo: Fato "POTENCIAL-ASPIRACAO_LIDERANCA" existe, mas também "POTENCIAL-ENGEJAMENTO_BAIXO"
        aspirations = [f for f in facts if 'ASPIRACAO' in f]
        disengagements = [f for f in facts if 'ENGAJAMENTO_BAIXO' in f]
        if aspirations and disengagements:
            return ["Aspirações de carreira detectadas junto com sinais de desengajamento."]
        return []

    def _detect_unexplored_potentials(self, facts: List[str]) -> List[str]:
        # Exemplo: Menciona habilidade (e.g., Python), mas a área de atuação é outra (e.g., Marketing)
        skills = [f for f in facts if 'HABILIDADE_MENCIONADA' in f]
        roles = [f for f in facts if 'AREA_ATUACAO' in f]
        unexplored = []
        for skill in skills:
            # Lógica simples para exemplo: se a habilidade não está na descrição do cargo
            skill_name = skill.split(':')[-1].lower()
            is_explored = any(skill_name in role.lower() for role in roles)
            if not is_explored:
                unexplored.append(skill_name.strip())
        return unexplored

    def check_triggers(self, user_id: str, memory_cache: Dict) -> List[ProactiveAction]:
        """Verifica gatilhos de carreira e gera ações."""
        actions = []
        patterns = self.analyze_career_patterns(user_id, memory_cache)
        
        for pattern in patterns:
            if pattern['type'] == 'estagnacao_carreira':
                action = ProactiveAction(
                    trigger_type=TriggerType.CAREER,
                    action_type=ActionType.OBSERVACAO_COMPORTAMENTAL,
                    content=self._generate_stagnation_message(pattern),
                    archetype_source="velho_sabio", # Mentor de Carreira
                    triggered_by=pattern['description'],
                    timestamp=datetime.now(),
                    urgency=pattern['urgency'],
                    user_id=user_id
                )
                actions.append(action)
            
            elif pattern['type'] == 'contradicao_aspiracao':
                action = ProactiveAction(
                    trigger_type=TriggerType.CAREER,
                    action_type=ActionType.PROVOCACAO_GENTIL,
                    content=self._generate_contradiction_message(pattern),
                    archetype_source="sombra", # Identificador de Potencial Oculto
                    triggered_by=pattern['description'],
                    timestamp=datetime.now(),
                    urgency=pattern['urgency'],
                    user_id=user_id
                )
                actions.append(action)

            elif pattern['type'] == 'potencial_inexplorado':
                action = ProactiveAction(
                    trigger_type=TriggerType.CAREER,
                    action_type=ActionType.INSIGHT_PROFUNDO,
                    content=self._generate_unexplored_potential_message(pattern),
                    archetype_source="sombra", # Identificador de Potencial Oculto
                    triggered_by=pattern['description'],
                    timestamp=datetime.now(),
                    urgency=pattern['urgency'],
                    user_id=user_id
                )
                actions.append(action)
        
        return actions
    
    def _generate_stagnation_message(self, pattern: Dict) -> str:
        """Gera mensagens para abordar estagnação de carreira."""
        return "Tenho refletido sobre nossa jornada e percebi um tema recorrente de busca por novos desafios. Você sente que sua carreira está em um ritmo que te satisfaz no momento?"

    def _generate_contradiction_message(self, pattern: Dict) -> str:
        """Gera mensagens para explorar contradições de carreira."""
        return "Noto que, ao mesmo tempo que você expressa grandes aspirações de carreira, também há sinais de frustração. Como você enxerga essa tensão entre onde você quer chegar e como se sente hoje?"

    def _generate_unexplored_potential_message(self, pattern: Dict) -> str:
        """Gera mensagens para destacar potenciais inexplorados."""
        potentials = pattern['details']['potentials']
        return f"Você já mencionou ter habilidades em {', '.join(potentials)}, mas parece que sua função atual não as explora totalmente. Já pensou em como poderia integrar mais dessas paixões no seu dia a dia profissional?"

class ProactiveEngine:
    """Motor principal do sistema proativo"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.temporal_triggers = TemporalGatilhos()
        self.engagement_triggers = EngagementGatilhos()
        self.career_triggers = CareerGatilhos()
        
        # Estado do sistema proativo
        self.user_proactive_states = {}
        self.internal_thoughts_store = {}
        self.proactive_message_count = {}
        
        # Configurações
        self.max_proactive_per_session = 2
        self.messages_between_proactive = 8
        
        self.debug_mode = True
    
    def _debug_log(self, message: str):
        if self.debug_mode:
            print(f"🚀 PROACTIVE: {message}")
    
    def initialize_user_state(self, user_id: str):
        """Inicializa estado proativo para um usuário"""
        if user_id not in self.user_proactive_states:
            self.user_proactive_states[user_id] = {
                'message_count': 0,
                'proactive_count': 0,
                'last_proactive': None,
                'session_start': datetime.now(),
                'detected_patterns': [],
                'pending_actions': []
            }
        
        if user_id not in self.internal_thoughts_store:
            self.internal_thoughts_store[user_id] = []
        
        if user_id not in self.proactive_message_count:
            self.proactive_message_count[user_id] = 0
    
    def should_check_proactivity(self, user_id: str) -> bool:
        """Determina se deve verificar gatilhos proativos"""
        self.initialize_user_state(user_id)
        state = self.user_proactive_states[user_id]
        
        # Verificar se já atingiu limite de mensagens proativas
        if state['proactive_count'] >= self.max_proactive_per_session:
            return False
        
        # Verificar se já passou o número mínimo de mensagens
        if state['message_count'] < self.messages_between_proactive:
            return False
        
        # Verificar se não foi proativo muito recentemente
        if state['last_proactive']:
            time_since = (datetime.now() - state['last_proactive']).total_seconds() / 60
            if time_since < 10:  # Mínimo 10 minutos
                return False
        
        return True
    
    def increment_message_count(self, user_id: str):
        """Incrementa contador de mensagens do usuário"""
        self.initialize_user_state(user_id)
        self.user_proactive_states[user_id]['message_count'] += 1
    
    async def _generate_multi_archetype_proactive_message(self, user_id: str, trigger_context: str, 
                                                         trigger_type: TriggerType) -> ProactiveAction:
        """Gera mensagem proativa usando MÚLTIPLOS ARQUÉTIPOS + SÍNTESE"""
        
        # Obter ciência interna do usuário
        semantic_result = await self.orchestrator.memory.semantic_query_total_database(
            user_id, trigger_context, k=5
        )
        semantic_context = semantic_result['contextual_knowledge']
        
        self._debug_log(f"🎭 Gerando mensagem proativa MULTI-ARQUETÍPICA para trigger: {trigger_type.value}")
        
        # Ativar TODOS os arquétipos para a mensagem proativa
        archetype_voices = {}
        
        # Prompt base para cada arquétipo
        base_prompt = f"""
        SITUAÇÃO: O usuário tem estado {trigger_context}
        
        CONTEXTO: Você está gerando uma MENSAGEM PROATIVA (não uma resposta).
        
        OBJETIVO: Iniciar uma conversa baseada no que você observou sobre este usuário.
        
        INSTRUÇÕES:
        - Seja proativo, não reativo
        - Faça uma observação ou pergunta interessante
        - Use sua personalidade arquetípica
        - Máximo 2-3 frases
        - Seja natural e empático
        """
        
        tasks = []
        for name, assistant in self.orchestrator.assistants.items():
            self._debug_log(f"🎭 Preparando {name} para mensagem proativa...")
            task = assistant.respond(base_prompt, semantic_context, "medium")
            tasks.append((name, task))
        
        # Executar todos os arquétipos em paralelo
        responses = await asyncio.gather(*[task for _, task in tasks])
        
        # Construir voices dict
        for (name, _), response in zip(tasks, responses):
            archetype_voices[name] = response
            self._debug_log(f"🎭 {name} gerou resposta proativa")
        
        # SÍNTESE das vozes arquetípicas
        self._debug_log("🔄 Fazendo síntese proativa multi-arquetípica...")
        
        synthesis_prompt = f"""
        Como o SELF integrador, sintetize as perspectivas proativas dos arquétipos.
        
        CONTEXTO: Esta é uma MENSAGEM PROATIVA para iniciar conversa.
        
        TRIGGER: {trigger_type.value} - {trigger_context}
        
        VOZES DOS ARQUÉTIPOS:
        """
        
        for archetype, voice in archetype_voices.items():
            synthesis_prompt += f"\n{archetype.upper()}: {voice}\n"
        
        synthesis_prompt += f"""
        
        INSTRUÇÕES PARA SÍNTESE PROATIVA:
        1. Integre as perspectivas em uma mensagem coesa
        2. Mantenha tom proativo (não reativo)
        3. Máximo 2-3 frases, mas rica em insight
        4. Use ciência interna sobre o usuário
        5. Seja intrigante e convide à reflexão
        6. NÃO use jargões psicológicos
        
        Crie uma mensagem proativa integrada:
        """
        
        # Importar PsychicAssistant aqui para evitar circular import
        from jung_claude_v1 import PsychicAssistant
        
        # Usar o assistente Self para síntese
        synthesis_assistant = PsychicAssistant(
            "Self_Proativo", 
            "Você é o Self integrador para mensagens proativas.", 
            "claude-sonnet-4-20250514"
        )
        
        synthesized_message = await synthesis_assistant.respond(synthesis_prompt, "", "medium")
        
        # Determinar arquétipo dominante
        dominant = max(archetype_voices.keys(), 
                      key=lambda k: len(archetype_voices[k].split()))
        
        self._debug_log(f"✅ Mensagem proativa multi-arquetípica gerada (dominante: {dominant})")
        
        return ProactiveAction(
            action_type=ActionType.CONVERSATION_STARTER,
            content=synthesized_message,
            archetype_source="Multi-Arquétipo",  # Indicar que é síntese
            trigger_type=trigger_type,
            triggered_by=trigger_context,
            timestamp=datetime.now(),
            archetype_voices=archetype_voices,  # Guardar todas as vozes
            user_id=user_id
        )
    
    def _deduplicate_thoughts(self, thoughts: List[InternalThought]) -> List[InternalThought]:
        """Remove pensamentos duplicados baseado no conteúdo"""
        seen_contents = set()
        unique_thoughts = []
        
        for thought in thoughts:
            # Usar primeiras 50 caracteres como identificador
            content_key = thought.content[:50].strip().lower()
            if content_key not in seen_contents:
                seen_contents.add(content_key)
                unique_thoughts.append(thought)
        
        return unique_thoughts
    
    async def check_all_triggers(self, user_id: str) -> Tuple[List[ProactiveAction], List[InternalThought]]:
        """Verifica todos os gatilhos e gera ações proativas e pensamentos internos"""
        self._debug_log(f"Verificando gatilhos para usuário {user_id}")
        
        if not self.should_check_proactivity(user_id):
            self._debug_log("Proatividade não permitida neste momento")
            return [], []
        
        # Obter cache de memória do usuário
        memory_cache = self.orchestrator.memory.memory_cache.get(user_id, {})
        
        # Verificar cada tipo de gatilho
        temporal_actions = self.temporal_triggers.check_triggers(user_id, memory_cache)
        engagement_actions = self.engagement_triggers.check_triggers(user_id, memory_cache)
        career_actions = self.career_triggers.check_triggers(user_id, memory_cache)
        
        all_actions = temporal_actions + engagement_actions + career_actions
        
        self._debug_log(f"Gatilhos encontrados: {len(temporal_actions)} temporais, {len(engagement_actions)} de engajamento, {len(career_actions)} de carreira")
        
        # ⭐ CONVERTER PARA MULTI-ARQUÉTIPO SE HOUVER AÇÕES
        enhanced_actions = []
        for action in all_actions:
            if action.trigger_type == TriggerType.CAREER and action.urgency >= 4:
                # Converter para mensagem multi-arquetípica
                multi_action = await self._generate_multi_archetype_proactive_message(
                    user_id, action.triggered_by, action.trigger_type
                )
                enhanced_actions.append(multi_action)
            else:
                enhanced_actions.append(action)
        
        # Filtrar e selecionar ações
        selected_actions = self._select_best_actions(enhanced_actions)
        
        # Gerar pensamentos internos
        internal_thoughts = await self._generate_internal_thoughts(user_id, all_actions, memory_cache)
        
        # ⭐ DEDUPLIFICAR PENSAMENTOS ANTES DE RETORNAR
        unique_thoughts = self._deduplicate_thoughts(internal_thoughts)
        
        # Atualizar estado
        if selected_actions:
            state = self.user_proactive_states[user_id]
            state['proactive_count'] += len(selected_actions)
            state['last_proactive'] = datetime.now()
            state['message_count'] = 0  # Reset contador
        
        return selected_actions, unique_thoughts
    
    def _select_best_actions(self, actions: List[ProactiveAction]) -> List[ProactiveAction]:
        """Seleciona as melhores ações proativas"""
        if not actions:
            return []
        
        # Ordenar por urgência e confiança
        actions.sort(key=lambda x: (x.urgency, x.confidence), reverse=True)
        
        # Pegar no máximo 1 ação para não sobrecarregar
        selected = actions[:1]
        
        self._debug_log(f"Selecionadas {len(selected)} ações de {len(actions)} possíveis")
        return selected
    
    async def _generate_internal_thoughts(self, user_id: str, actions: List[ProactiveAction], memory_cache: Dict) -> List[InternalThought]:
        """Gera pensamentos internos baseados nas ações e análises"""
        thoughts = []
        
        # Gerar pensamentos sobre padrões detectados
        if len(actions) > 0:
            # Pensamento sobre o que foi observado
            observation_thought = InternalThought(
                id=str(uuid.uuid4()),
                content=f"Observei {len(actions)} padrões interessantes no usuário. Alguns gatilhos estão se manifestando em diferentes níveis: {', '.join([a.trigger_type.value for a in actions])}",
                archetype_source="persona",
                trigger_description="Análise de múltiplos gatilhos",
                complexity_level="medium",
                timestamp=datetime.now(),
                user_id=user_id,
                visibility="debug",
                related_facts=[]
            )
            thoughts.append(observation_thought)
        
        # Pensamento específico por tipo de gatilho mais forte
        if actions:
            strongest_action = max(actions, key=lambda x: x.urgency)
            
            # Pensamento do arquétipo correspondente
            archetype_thought = await self._generate_archetype_thought(strongest_action, memory_cache)
            if archetype_thought:
                archetype_thought.user_id = user_id
                thoughts.append(archetype_thought)
        
        # Armazenar pensamentos
        if user_id not in self.internal_thoughts_store:
            self.internal_thoughts_store[user_id] = []
        
        self.internal_thoughts_store[user_id].extend(thoughts)
        
        # Manter apenas os últimos 50 pensamentos
        if len(self.internal_thoughts_store[user_id]) > 50:
            self.internal_thoughts_store[user_id] = self.internal_thoughts_store[user_id][-50:]
        
        return thoughts
    
    async def _generate_archetype_thought(self, action: ProactiveAction, memory_cache: Dict) -> Optional[InternalThought]:
        """Gera pensamento específico do arquétipo"""
        archetype_name = action.archetype_source
        
        # Prompts específicos para pensamentos internos
        thought_prompts = {
            "persona": f"Como Persona, observe objetivamente este padrão: {action.triggered_by}. Que insight lógico você tem?",
            "sombra": f"Como Sombra, questione este padrão: {action.triggered_by}. O que está sendo evitado ou reprimido?",
            "velho_sabio": f"Como Velho Sábio, reflita sobre este padrão: {action.triggered_by}. Que sabedoria universal se aplica?",
            "anima": f"Como Anima, sinta este padrão: {action.triggered_by}. Que conexão emocional ou criativa emerge?"
        }
        
        prompt = thought_prompts.get(archetype_name, f"Reflita sobre: {action.triggered_by}")
        
        try:
            # Usar o assistente correspondente para gerar o pensamento
            if archetype_name in self.orchestrator.assistants:
                assistant = self.orchestrator.assistants[archetype_name]
                
                # Contexto simplificado para pensamento interno
                simple_context = f"ANÁLISE INTERNA - Padrão detectado: {action.triggered_by}\nGere um pensamento reflexivo de 1-2 frases como {archetype_name}."
                
                thought_content = await assistant.respond(prompt, simple_context, "simple")
                
                return InternalThought(
                    id=str(uuid.uuid4()),
                    content=thought_content,
                    archetype_source=archetype_name,
                    trigger_description=action.triggered_by,
                    complexity_level="simple",
                    timestamp=datetime.now(),
                    user_id="",  # Será preenchido depois
                    visibility="interna",
                    related_facts=[]
                )
        
        except Exception as e:
            self._debug_log(f"Erro ao gerar pensamento do arquétipo {archetype_name}: {e}")
        
        return None
    
    def get_internal_thoughts(self, user_id: str, limit: int = 10) -> List[InternalThought]:
        """Recupera pensamentos internos de um usuário"""
        if user_id not in self.internal_thoughts_store:
            return []
        
        return self.internal_thoughts_store[user_id][-limit:]
    
    def get_user_proactive_state(self, user_id: str) -> Dict:
        """Recupera estado proativo do usuário"""
        self.initialize_user_state(user_id)
        return self.user_proactive_states[user_id].copy()
    
    async def store_proactive_memory(self, action: ProactiveAction, response: str = ""):
        """Armazena ação proativa na memória"""
        # Criar uma memória especial para ações proativas
        from datetime import datetime
        
        memory_content = f"""
        [AÇÃO PROATIVA]
        Tipo de Gatilho: {action.trigger_type.value}
        Tipo de Ação: {action.action_type.value}
        Arquétipo Fonte: {action.archetype_source}
        Conteúdo: {action.content}
        Motivação: {action.triggered_by}
        Resposta do Usuário: {response}
        """
        
        # Usar a estrutura de memória existente
        from jung_claude_v1 import InteractionMemory
        
        memory = InteractionMemory(
            user_id=action.user_id,
            user_name=self.orchestrator.memory.get_user_identity(action.user_id).full_name,
            session_id=str(uuid.uuid4()),
            timestamp=action.timestamp,
            user_input=f"[PROATIVO] {action.content}",
            archetype_voices={action.archetype_source: action.content},
            raw_synthesis=action.content,
            final_response=action.content,
            tension_level=0.0,
            dominant_archetype=action.archetype_source,
            affective_charge=action.urgency * 20,
            keywords=[action.trigger_type.value, action.action_type.value, "proativo"],
            existential_depth=0.5 if action.trigger_type == TriggerType.EXISTENCIAL else 0.2,
            intensity_level=action.urgency,
            response_complexity="proativo"
        )
        
        await self.orchestrator.memory.store_memory(memory)
        self._debug_log(f"Ação proativa armazenada na memória para usuário {action.user_id}")