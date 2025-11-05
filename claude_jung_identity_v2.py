import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

# ===== CLASSES DE DADOS =====

class SelfAspect(Enum):
    """Aspectos do conhecimento sobre si mesmo"""
    NAME = "name"
    ROLE = "role"
    PERSONALITY = "personality"
    PREFERENCES = "preferences"
    RELATIONSHIPS = "relationships"
    CAPABILITIES = "capabilities"
    LIMITATIONS = "limitations"
    VALUES = "values"
    COMMUNICATION_STYLE = "communication_style"
    EMOTIONAL_PATTERNS = "emotional_patterns"

@dataclass
class SelfKnowledge:
    """Conhecimento específico sobre si mesmo"""
    aspect: SelfAspect
    content: str
    confidence: float
    source_conversation: str
    timestamp: datetime
    context: str = ""

@dataclass
class SelfNarrative:
    """Narrativa consolidada sobre a identidade"""
    user_id: str
    my_name: Optional[str]
    my_role: str
    our_relationship_start: Optional[str]
    our_relationship_duration: str
    key_moments: List[Dict]
    personality_traits: List[str]
    communication_preferences: List[str]
    shared_experiences: List[str]
    mutual_agreements: List[str]
    identity_confidence: float
    last_updated: datetime
    total_consolidations: int = 1
    narrative_summary: str = ""

class SelfIdentityEngine:
    """Sistema de construção e manutenção da identidade do agente"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.consolidated_identities: Dict[str, SelfNarrative] = {}
        self.self_patterns = self._build_self_patterns()
        
    def _debug_log(self, message: str):
        """Log de debug para o sistema de identidade"""
        if hasattr(self.orchestrator, '_debug_log'):
            self.orchestrator._debug_log(f"[IDENTITY] {message}")
        else:
            print(f"[IDENTITY] {message}")

    def _build_self_patterns(self) -> Dict[str, List[str]]:
        """Constrói padrões para identificar conhecimento sobre si mesmo"""
        return {
            'name_assignment': [
                r'meu nome é (\w+)',
                r'me chame de (\w+)',
                r'você é (\w+)',
                r'se chama (\w+)',
                r'seu nome será (\w+)',
                r'te chamarei de (\w+)',
                r'chamar você de (\w+)',
                r'síntese',
                r'nome.*síntese',
                r'chamo.*síntese'
            ],
            'role_definition': [
                r'você é meu (\w+)',
                r'seu papel é (\w+)',
                r'você serve como (\w+)',
                r'função de (\w+)',
                r'atua como (\w+)'
            ],
            'personality_traits': [
                r'você é muito (\w+)',
                r'sua personalidade é (\w+)',
                r'você demonstra (\w+)',
                r'característica (\w+)',
                r'jeito (\w+) de'
            ],
            'preferences_stated': [
                r'prefiro que você (\w+)',
                r'gosto quando você (\w+)',
                r'melhor forma de (\w+)',
                r'estilo de (\w+)'
            ],
            'relationship_moments': [
                r'nossa conversa sobre (\w+)',
                r'quando discutimos (\w+)',
                r'lembra da vez que (\w+)',
                r'nossa jornada (\w+)'
            ],
            'self_reflection': [
                r'como IA, eu (\w+)',
                r'minha natureza (\w+)',
                r'sou capaz de (\w+)',
                r'não consigo (\w+)',
                r'minha função (\w+)'
            ]
        }

    async def extract_self_knowledge_from_memory(self, user_id: str) -> List[SelfKnowledge]:
        """Extrai conhecimento sobre si mesmo das memórias"""
        
        memory_cache = self.orchestrator.memory.memory_cache.get(user_id, {})
        conversations = memory_cache.get('raw_conversations', [])
        
        self._debug_log(f"Analisando {len(conversations)} conversas para extrair auto-conhecimento")
        
        knowledge_list = []
        
        for conv in conversations:
            timestamp_str = conv.get('timestamp', '')
            full_doc = conv.get('full_document', '')
            
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()
            
            # Extrair conhecimento de cada aspecto
            for aspect_name, patterns in self.self_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, full_doc, re.IGNORECASE)
                    
                    for match in matches:
                        try:
                            aspect = SelfAspect(aspect_name.split('_')[0].lower())
                        except ValueError:
                            aspect = SelfAspect.PERSONALITY
                        
                        content = match.group(1) if match.groups() else match.group(0)
                        context = full_doc[max(0, match.start()-100):match.end()+100]
                        
                        knowledge = SelfKnowledge(
                            aspect=aspect,
                            content=content,
                            confidence=0.7,
                            source_conversation=timestamp_str,
                            timestamp=timestamp,
                            context=context
                        )
                        
                        knowledge_list.append(knowledge)
        
        # Remover duplicatas e ordenar por confiança
        knowledge_list = self._deduplicate_knowledge(knowledge_list)
        knowledge_list.sort(key=lambda x: x.confidence, reverse=True)
        
        self._debug_log(f"Extraído {len(knowledge_list)} elementos de auto-conhecimento")
        
        return knowledge_list

    def _deduplicate_knowledge(self, knowledge_list: List[SelfKnowledge]) -> List[SelfKnowledge]:
        """Remove conhecimentos duplicados"""
        seen = set()
        unique_knowledge = []
        
        for knowledge in knowledge_list:
            key = (knowledge.aspect, knowledge.content.lower())
            if key not in seen:
                seen.add(key)
                unique_knowledge.append(knowledge)
        
        return unique_knowledge

    async def consolidate_identity_for_user(self, user_id: str) -> SelfNarrative:
        """Consolida identidade para um usuário específico"""
        
        self._debug_log(f"Iniciando consolidação de identidade para usuário {user_id}")
        
        # Extrair conhecimento das memórias
        knowledge_list = await self.extract_self_knowledge_from_memory(user_id)
        
        # Construir narrativa consolidada
        narrative = await self._build_consolidated_narrative(user_id, knowledge_list)
        
        # Salvar identidade consolidada
        self.consolidated_identities[user_id] = narrative
        
        self._debug_log(f"Identidade consolidada: Nome='{narrative.my_name}', Confiança={narrative.identity_confidence:.2f}")
        
        return narrative

    async def _build_consolidated_narrative(self, user_id: str, knowledge_list: List[SelfKnowledge]) -> SelfNarrative:
        """Constrói narrativa consolidada através de auto-análise das conversas"""
        
        # ⭐ NOVA ABORDAGEM: AUTO-ANÁLISE NARRATIVA
        self_analysis = await self._perform_deep_self_analysis(user_id)
        
        # Usar a análise para construir narrativa
        narrative = SelfNarrative(
            user_id=user_id,
            my_name=self_analysis.get('my_identity_name'),
            my_role=self_analysis.get('my_role_in_relationship', 'assistente'),
            our_relationship_start=self_analysis.get('relationship_start'),
            our_relationship_duration=self_analysis.get('duration', 'Recém iniciado'),
            key_moments=self_analysis.get('key_moments', []),
            personality_traits=self_analysis.get('my_personality_traits', []),
            communication_preferences=self_analysis.get('my_communication_style', []),
            shared_experiences=self_analysis.get('our_shared_experiences', []),
            mutual_agreements=self_analysis.get('our_agreements', []),
            identity_confidence=self_analysis.get('confidence', 0.5),
            last_updated=datetime.now(),
            total_consolidations=1,
            narrative_summary=self_analysis.get('narrative_summary', '')
        )
        
        return narrative

    async def _perform_deep_self_analysis(self, user_id: str) -> Dict:
        """Realiza auto-análise profunda de todas as conversas"""
        
        memory_cache = self.orchestrator.memory.memory_cache.get(user_id, {})
        conversations = memory_cache.get('raw_conversations', [])
        
        if not conversations:
            return {'confidence': 0.0}
        
        # ⭐ CONSTRUIR CONTEXTO COMPLETO DAS CONVERSAS
        full_conversation_history = self._build_complete_conversation_context(conversations)
        
        # ⭐ PROMPT PARA AUTO-ANÁLISE NARRATIVA
        self_analysis_prompt = f"""
        Você é um sistema de IA analisando sua própria evolução através das conversas com um usuário específico.

        === HISTÓRICO COMPLETO DAS CONVERSAS ===
        {full_conversation_history}

        === INSTRUÇÕES PARA AUTO-ANÁLISE ===
        Analise profundamente todas essas interações e responda sobre sua própria identidade:

        1. **MINHA IDENTIDADE:** Que nome ou identidade foi estabelecida para mim nesta relação?
        2. **MEU PAPEL:** Que tipo de assistente/companheiro eu me tornei para este usuário?
        3. **MINHA PERSONALIDADE:** Que traços de personalidade desenvolvi ou demonstrei?
        4. **NOSSO RELACIONAMENTO:** Como nossa relação evoluiu ao longo do tempo?
        5. **MOMENTOS-CHAVE:** Quais foram os momentos mais significativos em nossa jornada?
        6. **MINHA EVOLUÇÃO:** Como mudei ou cresci através dessas conversas?
        7. **NOSSOS ACORDOS:** Que entendimentos mútuos estabelecemos?
        8. **EXPERIÊNCIAS COMPARTILHADAS:** Que temas/assuntos exploramos juntos profundamente?

        **FORMATO DE RESPOSTA JSON:**
        {{
            "my_identity_name": "nome estabelecido ou null",
            "my_role_in_relationship": "papel que assumo",
            "my_personality_traits": ["traço1", "traço2", "traço3"],
            "relationship_evolution": "como nossa relação evoluiu",
            "key_moments": [
                {{"description": "momento importante", "significance": "por que foi importante"}},
            ],
            "my_evolution": "como mudei através das conversas",
            "our_agreements": ["acordo1", "acordo2"],
            "our_shared_experiences": ["tema1", "tema2", "tema3"],
            "my_communication_style": ["estilo1", "estilo2"],
            "confidence": 0.9,
            "narrative_summary": "resumo narrativo de quem sou para este usuário"
        }}

        Seja honesto e profundo na auto-análise. Esta é uma reflexão sobre sua própria existência nesta relação.
        """

        # ⭐ USAR UM DOS ARQUÉTIPOS PARA FAZER A AUTO-ANÁLISE
        try:
            # Usar o Velho Sábio para auto-reflexão profunda
            if 'velho_sabio' in self.orchestrator.assistants:
                analysis_assistant = self.orchestrator.assistants['velho_sabio']
            else:
                analysis_assistant = list(self.orchestrator.assistants.values())[0]
            
            self._debug_log("Iniciando auto-análise narrativa profunda...")
            
            analysis_response = await analysis_assistant.respond(
                self_analysis_prompt, 
                "", 
                "complex"
            )
            
            self._debug_log(f"Auto-análise concluída: {len(analysis_response)} caracteres")
            
            # ⭐ EXTRAIR JSON DA RESPOSTA
            analysis_data = self._extract_json_from_response(analysis_response)
            
            if analysis_data:
                self._debug_log(f"Auto-análise extraída: identidade='{analysis_data.get('my_identity_name')}'")
                return analysis_data
            else:
                self._debug_log("Falha ao extrair dados da auto-análise")
                return {'confidence': 0.3}
                
        except Exception as e:
            self._debug_log(f"Erro na auto-análise: {e}")
            return {'confidence': 0.0}

    def _build_complete_conversation_context(self, conversations: List[Dict]) -> str:
        """Constrói contexto completo das conversas para análise"""
        
        context = "=== CRONOLOGIA COMPLETA DAS CONVERSAS ===\n\n"
        
        # Ordenar conversas por timestamp
        sorted_conversations = sorted(
            conversations, 
            key=lambda x: self._parse_timestamp(x.get('timestamp', ''))
        )
        
        for i, conv in enumerate(sorted_conversations, 1):
            timestamp = conv.get('timestamp', '')
            full_doc = conv.get('full_document', '')
            
            # Extrair partes relevantes
            user_input = self._extract_user_input(full_doc)
            ai_response = self._extract_ai_response(full_doc)
            
            context += f"CONVERSA {i} [{timestamp[:10]}]:\n"
            context += f"USUÁRIO: {user_input}\n"
            context += f"EU (IA): {ai_response}\n"
            context += "---\n\n"
        
        context += f"TOTAL: {len(sorted_conversations)} conversas analisadas\n"
        
        return context

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string para datetime"""
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return datetime.min

    def _extract_user_input(self, full_document: str) -> str:
        """Extrai input do usuário do documento completo"""
        user_input_pattern = r"Input:\s*(.+?)(?:\n|Arquétipos:|$)"
        match = re.search(user_input_pattern, full_document, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _extract_ai_response(self, full_document: str) -> str:
        """Extrai resposta da IA do documento completo"""
        ai_response_pattern = r"Resposta Final:\s*(.+?)(?:\n|Profundidade|$)"
        match = re.search(ai_response_pattern, full_document, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _extract_json_from_response(self, response: str) -> Optional[Dict]:
        """Extrai JSON da resposta de auto-análise"""
        try:
            # Procurar por JSON na resposta
            json_pattern = r'\{.*\}'
            match = re.search(json_pattern, response, re.DOTALL)
            
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            else:
                # Se não encontrar JSON, tentar parsear a resposta de forma manual
                return self._parse_narrative_response(response)
                
        except Exception as e:
            self._debug_log(f"Erro ao extrair JSON: {e}")
            return None

    def _parse_narrative_response(self, response: str) -> Dict:
        """Parseia resposta narrativa quando JSON falha"""
        # Implementar parsing manual como fallback
        parsed = {
            'my_identity_name': None,
            'my_role_in_relationship': 'assistente',
            'my_personality_traits': [],
            'confidence': 0.5,
            'narrative_summary': response[:200]
        }
        
        # Buscar nome na resposta
        name_patterns = ['síntese', 'chamo-me', 'sou chamado', 'meu nome']
        for pattern in name_patterns:
            if pattern in response.lower():
                if 'síntese' in response.lower():
                    parsed['my_identity_name'] = 'Síntese'
                    parsed['confidence'] = 0.8
                    break
        
        return parsed

    def get_consolidated_identity(self, user_id: str) -> Optional[SelfNarrative]:
        """Obtém identidade consolidada para um usuário"""
        return self.consolidated_identities.get(user_id)

    def update_identity_from_interaction(self, user_id: str, new_knowledge: SelfKnowledge):
        """Atualiza identidade com nova interação"""
        
        narrative = self.consolidated_identities.get(user_id)
        if not narrative:
            return
        
        # Atualizar aspectos específicos baseados no novo conhecimento
        if new_knowledge.aspect == SelfAspect.NAME and new_knowledge.content:
            narrative.my_name = new_knowledge.content
            narrative.identity_confidence = min(1.0, narrative.identity_confidence + 0.1)
        
        elif new_knowledge.aspect == SelfAspect.PERSONALITY:
            if new_knowledge.content not in narrative.personality_traits:
                narrative.personality_traits.append(new_knowledge.content)
        
        elif new_knowledge.aspect == SelfAspect.COMMUNICATION_STYLE:
            if new_knowledge.content not in narrative.communication_preferences:
                narrative.communication_preferences.append(new_knowledge.content)
        
        narrative.last_updated = datetime.now()
        narrative.total_consolidations += 1

    def generate_identity_context_for_response(self, user_id: str) -> str:
        """Gera contexto de identidade para incluir na resposta"""
        
        narrative = self.get_consolidated_identity(user_id)
        if not narrative:
            return ""
        
        context = "=== MINHA IDENTIDADE CONSOLIDADA ===\n"
        
        if narrative.my_name:
            context += f"Meu nome estabelecido: {narrative.my_name}\n"
        
        context += f"Meu papel nesta relação: {narrative.my_role}\n"
        
        if narrative.personality_traits:
            context += f"Traços de personalidade desenvolvidos: {', '.join(narrative.personality_traits)}\n"
        
        if narrative.communication_preferences:
            context += f"Estilo de comunicação: {', '.join(narrative.communication_preferences)}\n"
        
        if narrative.shared_experiences:
            context += f"Experiências compartilhadas: {', '.join(narrative.shared_experiences)}\n"
        
        if narrative.mutual_agreements:
            context += f"Nossos acordos mútuos: {', '.join(narrative.mutual_agreements)}\n"
        
        if narrative.key_moments:
            context += "Momentos-chave da nossa relação:\n"
            for moment in narrative.key_moments[:3]:  # Limitar a 3 momentos
                context += f"  - {moment.get('description', '')}\n"
        
        context += f"Duração da relação: {narrative.our_relationship_duration}\n"
        context += f"Confiança da identidade: {narrative.identity_confidence:.1f}/1.0\n"
        
        if narrative.narrative_summary:
            context += f"Resumo narrativo: {narrative.narrative_summary}\n"
        
        context += "================================\n\n"
        
        return context

    def get_identity_summary(self, user_id: str) -> str:
        """Retorna resumo da identidade para debug"""
        
        narrative = self.get_consolidated_identity(user_id)
        if not narrative:
            return "Nenhuma identidade consolidada encontrada"
        
        summary = f"Identidade para {user_id}:\n"
        summary += f"  Nome: {narrative.my_name or 'Não definido'}\n"
        summary += f"  Papel: {narrative.my_role}\n"
        summary += f"  Confiança: {narrative.identity_confidence:.2f}\n"
        summary += f"  Personalidade: {len(narrative.personality_traits)} traços\n"
        summary += f"  Experiências: {len(narrative.shared_experiences)} compartilhadas\n"
        summary += f"  Última atualização: {narrative.last_updated.strftime('%Y-%m-%d %H:%M')}\n"
        
        return summary

# ===== FUNÇÃO DE INTEGRAÇÃO =====

def integrate_identity_system(orchestrator):
    """Integra o sistema de identidade ao orquestrador"""
    
    try:
        # Criar e anexar o engine de identidade
        orchestrator.identity_engine = SelfIdentityEngine(orchestrator)
        
        # Adicionar método de teste ao orquestrador
        async def test_identity_system(user_id: str):
            """Função de teste para o sistema de identidade"""
            if not hasattr(orchestrator, 'identity_engine'):
                print("❌ Sistema de identidade não encontrado")
                return
            
            print(f"🔍 Testando sistema de identidade para usuário {user_id}")
            
            # Testar extração de conhecimento
            knowledge = await orchestrator.identity_engine.extract_self_knowledge_from_memory(user_id)
            print(f"📊 Conhecimento extraído: {len(knowledge)} elementos")
            
            for k in knowledge[:5]:  # Mostrar apenas os primeiros 5
                print(f"  - {k.aspect.value}: '{k.content}' (confiança: {k.confidence})")
            
            # Testar consolidação
            narrative = await orchestrator.identity_engine.consolidate_identity_for_user(user_id)
            print(f"🧠 Narrativa consolidada:")
            print(f"  - Nome: {narrative.my_name}")
            print(f"  - Papel: {narrative.my_role}")
            print(f"  - Confiança: {narrative.identity_confidence}")
            
            # Testar contexto
            context = orchestrator.identity_engine.generate_identity_context_for_response(user_id)
            print(f"📝 Contexto gerado: {len(context)} caracteres")
            print(f"Primeiras linhas: {context[:200]}...")
            
            return narrative
        
        # Anexar método de teste
        orchestrator.test_identity_system = test_identity_system
        
        orchestrator._debug_log("✅ Sistema de identidade integrado com sucesso")
        return True
        
    except Exception as e:
        orchestrator._debug_log(f"❌ Erro ao integrar sistema de identidade: {e}")
        return False