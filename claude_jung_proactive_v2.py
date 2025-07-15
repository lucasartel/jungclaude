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
    RELACIONAL = "relacional" 
    EXISTENCIAL = "existencial"

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

class RelationalGatilhos:
    """Sistema de gatilhos relacionais"""
    
    def __init__(self):
        self.emotional_patterns = {}
        self.debug_mode = True
    
    def _debug_log(self, message: str):
        if self.debug_mode:
            print(f"💫 RELACIONAL: {message}")
    
    def analyze_emotional_patterns(self, user_id: str, memory_cache: Dict) -> List[Dict]:
        """Analisa padrões emocionais e relacionais"""
        patterns = []
        
        facts = memory_cache.get('facts_extracted', [])
        conversations = memory_cache.get('raw_conversations', [])
        
        # Detectar temas evitados
        avoided_themes = self._detect_avoided_themes(conversations)
        if avoided_themes:
            patterns.append({
                'type': 'tema_evitado',
                'description': f'Usuário evita falar sobre: {", ".join(avoided_themes)}',
                'urgency': 4,
                'details': {'themes': avoided_themes}
            })
        
        # Detectar lacunas afetivas
        affective_gaps = self._detect_affective_gaps(facts)
        if affective_gaps:
            patterns.append({
                'type': 'lacuna_afetiva',
                'description': f'Falta de menções sobre: {", ".join(affective_gaps)}',
                'urgency': 3,
                'details': {'gaps': affective_gaps}
            })
        
        # Detectar padrões de intensidade emocional
        emotional_spikes = self._detect_emotional_spikes(conversations)
        if emotional_spikes:
            patterns.append({
                'type': 'spike_emocional',
                'description': 'Detectados picos emocionais não resolvidos',
                'urgency': 5,
                'details': {'spikes': emotional_spikes}
            })
        
        self._debug_log(f"Padrões relacionais encontrados: {len(patterns)}")
        return patterns
    
    def _detect_avoided_themes(self, conversations: List[Dict]) -> List[str]:
        """Detecta temas que o usuário evita"""
        theme_mentions = {
            'família': 0, 'relacionamento': 0, 'trabalho': 0,
            'futuro': 0, 'sentimentos': 0, 'medos': 0
        }
        
        total_conversations = len(conversations)
        if total_conversations < 5:
            return []
        
        for conv in conversations:
            content = conv.get('full_document', '').lower()
            for theme in theme_mentions:
                if theme in content:
                    theme_mentions[theme] += 1
        
        # Detectar temas mencionados menos de 20% das vezes
        avoided = []
        for theme, count in theme_mentions.items():
            ratio = count / total_conversations
            if ratio < 0.2 and total_conversations > 10:
                avoided.append(theme)
        
        return avoided
    
    def _detect_affective_gaps(self, facts: List[str]) -> List[str]:
        """Detecta lacunas afetivas baseadas nos fatos extraídos"""
        categories = {
            'relacionamentos': ['RELACIONAMENTO'],
            'família': ['família', 'pai', 'mãe', 'irmão'],
            'intimidade': ['amor', 'paixão', 'intimidade'],
            'vulnerabilidade': ['medo', 'insegurança', 'fragilidade']
        }
        
        mentioned_categories = set()
        for fact in facts:
            for category, keywords in categories.items():
                if any(keyword.lower() in fact.lower() for keyword in keywords):
                    mentioned_categories.add(category)
        
        all_categories = set(categories.keys())
        gaps = list(all_categories - mentioned_categories)
        
        return gaps
    
    def _detect_emotional_spikes(self, conversations: List[Dict]) -> List[Dict]:
        """Detecta picos emocionais não resolvidos"""
        emotional_words = [
            'tristeza', 'raiva', 'medo', 'ansiedade', 'frustração',
            'solidão', 'angústia', 'desespero', 'confusão'
        ]
        
        spikes = []
        for i, conv in enumerate(conversations):
            content = conv.get('full_document', '').lower()
            
            emotional_count = sum(1 for word in emotional_words if word in content)
            if emotional_count >= 2:
                # Verificar se foi "resolvido" nas próximas conversas
                resolved = False
                for j in range(i+1, min(i+4, len(conversations))):
                    next_content = conversations[j].get('full_document', '').lower()
                    resolution_words = ['melhor', 'resolvido', 'claro', 'tranquilo', 'paz']
                    if any(word in next_content for word in resolution_words):
                        resolved = True
                        break
                
                if not resolved:
                    spikes.append({
                        'timestamp': conv.get('timestamp'),
                        'emotional_intensity': emotional_count,
                        'content_preview': content[:100]
                    })
        
        return spikes
    
    def check_triggers(self, user_id: str, memory_cache: Dict) -> List[ProactiveAction]:
        """Verifica gatilhos relacionais e gera ações"""
        actions = []
        patterns = self.analyze_emotional_patterns(user_id, memory_cache)
        
        for pattern in patterns:
            if pattern['type'] == 'tema_evitado':
                action = ProactiveAction(
                    trigger_type=TriggerType.RELACIONAL,
                    action_type=ActionType.PERGUNTA_CURIOSA,
                    content=self._generate_avoided_theme_message(pattern),
                    archetype_source="anima",
                    triggered_by=pattern['description'],
                    timestamp=datetime.now(),
                    urgency=pattern['urgency'],
                    user_id=user_id
                )
                actions.append(action)
            
            elif pattern['type'] == 'lacuna_afetiva':
                action = ProactiveAction(
                    trigger_type=TriggerType.RELACIONAL,
                    action_type=ActionType.OBSERVACAO_COMPORTAMENTAL,
                    content=self._generate_affective_gap_message(pattern),
                    archetype_source="anima",
                    triggered_by=pattern['description'],
                    timestamp=datetime.now(),
                    urgency=pattern['urgency'],
                    user_id=user_id
                )
                actions.append(action)
            
            elif pattern['type'] == 'spike_emocional':
                action = ProactiveAction(
                    trigger_type=TriggerType.RELACIONAL,
                    action_type=ActionType.PROVOCACAO_GENTIL,
                    content=self._generate_emotional_spike_message(pattern),
                    archetype_source="sombra",
                    triggered_by=pattern['description'],
                    timestamp=datetime.now(),
                    urgency=pattern['urgency'],
                    user_id=user_id
                )
                actions.append(action)
        
        return actions
    
    def _generate_avoided_theme_message(self, pattern: Dict) -> str:
        """Gera mensagens sobre temas evitados"""
        themes = pattern['details']['themes']
        
        if 'família' in themes:
            return "Percebo que falamos sobre muitas coisas, mas família é um tema que não surge muito. É uma escolha consciente?"
        
        if 'relacionamento' in themes:
            return "Você compartilha muito sobre trabalho e objetivos, mas como estão suas conexões pessoais?"
        
        if 'sentimentos' in themes:
            return "Vejo que você aborda as situações de forma bastante racional. Como você costuma lidar com o lado emocional das coisas?"
        
        return f"Há algumas áreas que não exploramos muito em nossas conversas: {', '.join(themes)}. Alguma delas te chama atenção?"
    
    def _generate_affective_gap_message(self, pattern: Dict) -> str:
        """Gera mensagens sobre lacunas afetivas"""
        gaps = pattern['details']['gaps']
        
        messages = {
            'relacionamentos': "Como você se sente em relação às suas conexões com outras pessoas?",
            'família': "Sua família tem um papel importante na sua vida atualmente?",
            'intimidade': "Como você experiencia momentos de proximidade e intimidade?",
            'vulnerabilidade': "Há situações onde você se permite ser mais vulnerável?"
        }
        
        for gap in gaps:
            if gap in messages:
                return messages[gap]
        
        return "Há aspectos da sua vida emocional que você gostaria de explorar mais?"
    
    def _generate_emotional_spike_message(self, pattern: Dict) -> str:
        """Gera mensagens sobre picos emocionais"""
        spikes = pattern['details']['spikes']
        recent_spike = spikes[-1] if spikes else None
        
        if recent_spike:
            messages = [
                "Lembro que você mencionou estar passando por um momento difícil. Como isso evoluiu?",
                "Percebi uma intensidade emocional em nossa conversa anterior. Gostaria de revisitar isso?",
                "Às vezes questões emocionais complexas precisam de mais tempo para se resolverem. Como você está se sentindo agora?"
            ]
            return random.choice(messages)
        
        return "Há alguma questão emocional que ainda ressoa em você?"

class ExistencialGatilhos:
    """Sistema de gatilhos existenciais"""
    
    def __init__(self):
        self.contradiction_patterns = {}
        self.debug_mode = True
    
    def _debug_log(self, message: str):
        if self.debug_mode:
            print(f"🤔 EXISTENCIAL: {message}")
    
    def analyze_existential_patterns(self, user_id: str, memory_cache: Dict) -> List[Dict]:
        """Analisa padrões existenciais e contradições"""
        patterns = []
        
        facts = memory_cache.get('facts_extracted', [])
        conversations = memory_cache.get('raw_conversations', [])
        
        # Detectar contradições internas
        contradictions = self._detect_contradictions(facts, conversations)
        if contradictions:
            patterns.append({
                'type': 'contradicao_interna',
                'description': 'Contradições detectadas entre declarações',
                'urgency': 4,
                'details': {'contradictions': contradictions}
            })
        
        # Detectar potenciais não explorados
        unexplored_potentials = self._detect_unexplored_potentials(facts)
        if unexplored_potentials:
            patterns.append({
                'type': 'potencial_nao_explorado',
                'description': 'Potenciais mencionados mas não desenvolvidos',
                'urgency': 3,
                'details': {'potentials': unexplored_potentials}
            })
        
        # Detectar questões sobre propósito
        purpose_concerns = self._detect_purpose_concerns(conversations)
        if purpose_concerns:
            patterns.append({
                'type': 'questao_proposito',
                'description': 'Questões sobre sentido e propósito detectadas',
                'urgency': 5,
                'details': {'concerns': purpose_concerns}
            })
        
        # Detectar deriva existencial
        existential_drift = self._detect_existential_drift(conversations)
        if existential_drift:
            patterns.append({
                'type': 'deriva_existencial',
                'description': 'Padrão de deriva ou falta de direção',
                'urgency': 4,
                'details': {'drift_indicators': existential_drift}
            })
        
        self._debug_log(f"Padrões existenciais encontrados: {len(patterns)}")
        return patterns
    
    def _detect_contradictions(self, facts: List[str], conversations: List[Dict]) -> List[Dict]:
        """Detecta contradições entre declarações"""
        contradictions = []
        
        # Analisar contradições em valores vs comportamentos
        value_keywords = {
            'autenticidade': ['autêntico', 'verdadeiro', 'genuíno'],
            'liberdade': ['livre', 'liberdade', 'independente'],
            'crescimento': ['crescer', 'desenvolver', 'evoluir'],
            'conexão': ['conectar', 'relacionar', 'próximo']
        }
        
        behavior_keywords = {
            'conformidade': ['seguir regras', 'fazer o esperado', 'conformar'],
            'limitação': ['limitado', 'preso', 'restrito'],
            'estagnação': ['mesmo', 'rotina', 'não mudar'],
            'isolamento': ['sozinho', 'distante', 'isolado']
        }
        
        value_contradictions = {
            'autenticidade': 'conformidade',
            'liberdade': 'limitação',
            'crescimento': 'estagnação',
            'conexão': 'isolamento'
        }
        
        all_text = ' '.join([fact for fact in facts] + 
                           [conv.get('full_document', '') for conv in conversations])
        all_text = all_text.lower()
        
        for value, contradiction in value_contradictions.items():
            value_present = any(keyword in all_text for keyword in value_keywords[value])
            contradiction_present = any(keyword in all_text for keyword in behavior_keywords[contradiction])
            
            if value_present and contradiction_present:
                contradictions.append({
                    'type': 'valor_vs_comportamento',
                    'value': value,
                    'contradiction': contradiction,
                    'description': f'Valoriza {value} mas demonstra {contradiction}'
                })
        
        return contradictions
    
    def _detect_unexplored_potentials(self, facts: List[str]) -> List[Dict]:
        """Detecta potenciais mencionados mas não desenvolvidos"""
        potential_indicators = {
            'criatividade': ['criativo', 'arte', 'música', 'escrever'],
            'liderança': ['liderar', 'gerenciar', 'comandar'],
            'ensino': ['ensinar', 'explicar', 'orientar'],
            'empreendedorismo': ['negócio próprio', 'empreender', 'startup'],
            'aventura': ['viajar', 'explorar', 'aventura'],
            'espiritualidade': ['espiritual', 'meditação', 'significado']
        }
        
        development_indicators = {
            'criatividade': ['projeto criativo', 'obra', 'criação'],
            'liderança': ['equipe', 'projeto liderado', 'responsabilidade'],
            'ensino': ['alunos', 'curso', 'workshop'],
            'empreendedorismo': ['empresa', 'produto', 'clientes'],
            'aventura': ['viagem realizada', 'expedição', 'descoberta'],
            'espiritualidade': ['prática espiritual', 'reflexão profunda', 'crescimento']
        }
        
        all_facts = ' '.join(facts).lower()
        unexplored = []
        
        for potential, keywords in potential_indicators.items():
            mentioned = any(keyword in all_facts for keyword in keywords)
            developed = any(keyword in all_facts for keyword in development_indicators[potential])
            
            if mentioned and not developed:
                unexplored.append({
                    'potential': potential,
                    'mentioned': True,
                    'developed': False,
                    'description': f'Mencionou interesse em {potential} mas não desenvolveu'
                })
        
        return unexplored
    
    def _detect_purpose_concerns(self, conversations: List[Dict]) -> List[Dict]:
        """Detecta questões sobre propósito e sentido"""
        purpose_keywords = [
            'propósito', 'sentido', 'significado', 'para que serve',
            'qual o ponto', 'vale a pena', 'faz sentido',
            'direção', 'caminho', 'objetivo de vida'
        ]
        
        concerns = []
        for conv in conversations:
            content = conv.get('full_document', '').lower()
            
            purpose_mentions = sum(1 for keyword in purpose_keywords if keyword in content)
            if purpose_mentions >= 2:
                concerns.append({
                    'timestamp': conv.get('timestamp'),
                    'intensity': purpose_mentions,
                    'content_preview': content[:150]
                })
        
        return concerns
    
    def _detect_existential_drift(self, conversations: List[Dict]) -> List[str]:
        """Detecta padrões de deriva existencial"""
        drift_indicators = [
            'não sei o que quero',
            'perdido',
            'sem direção',
            'vida sem sentido',
            'rotina sem propósito',
            'fazendo no automático',
            'dias iguais',
            'não vejo progresso'
        ]
        
        drift_patterns = []
        recent_conversations = conversations[-10:] if len(conversations) > 10 else conversations
        
        for conv in recent_conversations:
            content = conv.get('full_document', '').lower()
            
            for indicator in drift_indicators:
                if indicator in content:
                    drift_patterns.append(indicator)
        
        # Se 3 ou mais indicadores aparecem nas últimas conversas
        if len(set(drift_patterns)) >= 3:
            return list(set(drift_patterns))
        
        return []
    
    def check_triggers(self, user_id: str, memory_cache: Dict) -> List[ProactiveAction]:
        """Verifica gatilhos existenciais e gera ações"""
        actions = []
        patterns = self.analyze_existential_patterns(user_id, memory_cache)
        
        for pattern in patterns:
            if pattern['type'] == 'contradicao_interna':
                action = ProactiveAction(
                    trigger_type=TriggerType.EXISTENCIAL,
                    action_type=ActionType.PROVOCACAO_GENTIL,
                    content=self._generate_contradiction_message(pattern),
                    archetype_source="sombra",
                    triggered_by=pattern['description'],
                    timestamp=datetime.now(),
                    urgency=pattern['urgency'],
                    user_id=user_id
                )
                actions.append(action)
            
            elif pattern['type'] == 'potencial_nao_explorado':
                action = ProactiveAction(
                    trigger_type=TriggerType.EXISTENCIAL,
                    action_type=ActionType.INSIGHT_PROFUNDO,
                    content=self._generate_potential_message(pattern),
                    archetype_source="velho_sabio",
                    triggered_by=pattern['description'],
                    timestamp=datetime.now(),
                    urgency=pattern['urgency'],
                    user_id=user_id
                )
                actions.append(action)
            
            elif pattern['type'] == 'questao_proposito':
                action = ProactiveAction(
                    trigger_type=TriggerType.EXISTENCIAL,
                    action_type=ActionType.PERGUNTA_CURIOSA,
                    content=self._generate_purpose_message(pattern),
                    archetype_source="velho_sabio",
                    triggered_by=pattern['description'],
                    timestamp=datetime.now(),
                    urgency=pattern['urgency'],
                    user_id=user_id
                )
                actions.append(action)
            
            elif pattern['type'] == 'deriva_existencial':
                action = ProactiveAction(
                    trigger_type=TriggerType.EXISTENCIAL,
                    action_type=ActionType.OBSERVACAO_COMPORTAMENTAL,
                    content=self._generate_drift_message(pattern),
                    archetype_source="anima",
                    triggered_by=pattern['description'],
                    timestamp=datetime.now(),
                    urgency=pattern['urgency'],
                    user_id=user_id
                )
                actions.append(action)
        
        return actions
    
    def _generate_contradiction_message(self, pattern: Dict) -> str:
        """Gera mensagens sobre contradições"""
        contradictions = pattern['details']['contradictions']
        
        if contradictions:
            contradiction = contradictions[0]
            value = contradiction['value']
            conflict = contradiction['contradiction']
            
            messages = {
                'autenticidade': f"Você valoriza a autenticidade, mas às vezes parece se conformar com expectativas externas. Como você navega essa tensão?",
                'liberdade': f"Percebo que a liberdade é importante para você, mas também vejo sinais de que se sente limitado. Onde está o conflito?",
                'crescimento': f"Você busca crescimento, mas também vejo padrões que sugerem resistência à mudança. O que está acontecendo aí?",
                'conexão': f"Você valoriza conexões, mas às vezes parece se isolar. Como você entende essa aparente contradição?"
            }
            
            return messages.get(value, "Percebi algumas contradições interessantes em como você se vê versus como age. Já notou isso?")
        
        return "Há algo interessante sobre as contradições que carregamos. Já reparou em alguma sua?"
    
    def _generate_potential_message(self, pattern: Dict) -> str:
        """Gera mensagens sobre potenciais não explorados"""
        potentials = pattern['details']['potentials']
        
        if potentials:
            potential = potentials[0]
            area = potential['potential']
            
            messages = {
                'criatividade': "Você mencionou ter lado criativo, mas parece que não tem explorado muito isso. O que te impede?",
                'liderança': "Percebo que você tem características de liderança, mas talvez não tenha tido oportunidade de desenvolvê-las. Como se sente sobre isso?",
                'ensino': "Você demonstra habilidade para explicar e orientar. Já pensou em explorar o ensino de alguma forma?",
                'empreendedorismo': "Vejo um espírito empreendedor em você, mas parece que ainda não se manifestou concretamente. O que falta?",
                'aventura': "Você fala sobre explorar e viajar, mas parece que isso fica mais no desejo. O que te prende?",
                'espiritualidade': "Há uma busca por significado em você que talvez mereça mais atenção. Como você se conecta com essa dimensão?"
            }
            
            return messages.get(area, f"Há potenciais em você relacionados a {area} que parecem não estar sendo explorados. Já percebeu isso?")
        
        return "Às vezes temos potenciais adormecidos esperando uma oportunidade. Há algum que você sente mas não desenvolve?"
    
    def _generate_purpose_message(self, pattern: Dict) -> str:
        """Gera mensagens sobre questões de propósito"""
        concerns = pattern['details']['concerns']
        
        if concerns and len(concerns) >= 2:
            messages = [
                "Você tem questionado o sentido das coisas com frequência. O que está por trás dessa busca?",
                "Percebo uma inquietação existencial em você. Como tem lidado com essas questões sobre propósito?",
                "Há algo sobre direção de vida que tem te incomodado? Você parece estar repensando muitas coisas.",
                "Quando você se pergunta sobre o sentido das coisas, que tipo de resposta você está buscando?"
            ]
            return random.choice(messages)
        
        return "Questões sobre propósito e sentido são naturais, mas também podem ser sinais de transição. Como você vê isso?"
    
    def _generate_drift_message(self, pattern: Dict) -> str:
        """Gera mensagens sobre deriva existencial"""
        drift_indicators = pattern['details']['drift_indicators']
        
        messages = [
            "Tenho percebido uma certa sensação de deriva em você... como se estivesse navegando sem bússola. É assim que se sente?",
            "Às vezes a vida pode parecer estar no automático. Você tem sentido isso ultimamente?",
            "Há uma qualidade de 'estar perdido' em algumas coisas que você compartilha. Como você percebe isso?",
            "Percebo que você tem questionado a direção que sua vida está tomando. O que te daria mais clareza?"
        ]
        
        return random.choice(messages)

class ProactiveEngine:
    """Motor principal do sistema proativo"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.temporal_triggers = TemporalGatilhos()
        self.relational_triggers = RelationalGatilhos()
        self.existential_triggers = ExistencialGatilhos()
        
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
        relational_actions = self.relational_triggers.check_triggers(user_id, memory_cache)
        existential_actions = self.existential_triggers.check_triggers(user_id, memory_cache)
        
        all_actions = temporal_actions + relational_actions + existential_actions
        
        self._debug_log(f"Gatilhos encontrados: {len(temporal_actions)} temporais, {len(relational_actions)} relacionais, {len(existential_actions)} existenciais")
        
        # ⭐ CONVERTER PARA MULTI-ARQUÉTIPO SE HOUVER AÇÕES
        enhanced_actions = []
        for action in all_actions:
            if action.trigger_type == TriggerType.EXISTENCIAL and action.urgency >= 4:
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