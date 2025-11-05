# -*- coding: utf-8 -*-
"""
Claude Jung v2.0 - Interface Web Streamlit
Sistema com CONFLITO INTERNO entre arquétipos + memória semântica ativa
Versão: GROK 4 + TENSÃO PSÍQUICA
"""

import streamlit as st
import asyncio
import json
import logging
import hashlib
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import uuid
import os
from dotenv import load_dotenv
from collections import Counter
import re
import time
from io import StringIO
import sys

# Imports para versão híbrida: Grok + OpenAI Embeddings
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain.schema import Document

# Carregar variáveis de ambiente
load_dotenv()

# ===============================================
# SISTEMA DE CAPTURA DE LOGS
# ===============================================

class LogCapture:
    """Captura e armazena logs do sistema para exibição na interface"""
    
    def __init__(self):
        self.logs = []
        self.max_logs = 100
    
    def add_log(self, message: str, component: str = "SYSTEM"):
        """Adiciona um log à lista"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.logs.append({
            'timestamp': timestamp,
            'component': component,
            'message': message
        })
        
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
    
    def get_logs(self) -> List[Dict]:
        """Retorna todos os logs"""
        return self.logs.copy()
    
    def clear_logs(self):
        """Limpa todos os logs"""
        self.logs = []
    
    def get_formatted_logs(self) -> str:
        """Retorna logs formatados como string"""
        if not self.logs:
            return "Nenhum log disponível"
        
        formatted = []
        for log in self.logs:
            formatted.append(f"[{log['timestamp']}] {log['component']}: {log['message']}")
        
        return "\n".join(formatted)

# Instância global do capturador de logs
log_capture = LogCapture()

# ===============================================
# DATACLASSES E ESTRUTURAS DE DADOS
# ===============================================

@dataclass
class ArchetypeInsight:
    """Insight interno gerado por um arquétipo"""
    archetype_name: str
    insight_text: str
    key_observations: List[str]
    emotional_reading: str
    shadow_reading: str
    wisdom_perspective: str
    # NOVO: Posição/sugestão do arquétipo (para detectar conflito)
    suggested_stance: str
    suggested_response_direction: str

@dataclass
class ArchetypeConflict:
    """Representa um conflito interno entre arquétipos"""
    archetype_1: str
    archetype_2: str
    conflict_type: str
    archetype_1_position: str
    archetype_2_position: str
    tension_level: float
    description: str

@dataclass
class InteractionMemory:
    """Representa uma memória completa de interação"""
    user_id: str
    user_name: str
    session_id: str
    timestamp: datetime
    user_input: str
    internal_archetype_analysis: Dict[str, ArchetypeInsight]
    detected_conflicts: List[ArchetypeConflict]  # NOVO
    unified_understanding: str
    final_response: str
    tension_level: float
    dominant_perspective: str
    affective_charge: float
    keywords: List[str]
    existential_depth: float
    intensity_level: int
    response_complexity: str

@dataclass
class UserIdentity:
    """Identidade registrada do usuário"""
    user_id: str
    full_name: str
    first_name: str
    last_name: str
    registration_date: datetime
    total_sessions: int
    last_seen: datetime
    
class UserProfile:
    """Perfil relacional do usuário"""
    
    def __init__(self, user_id: str, full_name: str):
        self.user_id = user_id
        self.full_name = full_name
        self.first_name = full_name.split()[0]
        self.ai_assigned_name = ""
        self.narrative_summary = ""
        self.textual_fingerprint = {}
        self.thematic_clusters = []
        self.affective_baseline = 0.0
        self.interaction_count = 0
        self.existential_connection_level = 0.0
        self.vulnerability_moments = []
        self.preferred_intensity = 5
        self.last_updated = datetime.now()
        self.known_facts = {}

# ===============================================
# MÓDULO DE MEMÓRIA SEMÂNTICA (SEM ALTERAÇÕES)
# ===============================================

class MemoryModule:
    """Módulo com CONSULTA SEMÂNTICA ATIVA da base completa"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Inicializa o módulo de memória com base vetorial ChromaDB"""
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings
        )
        self.user_profiles = {}
        self.user_identities = {}
        self.memory_cache = {}
        self.debug_mode = True
        self._load_stored_identities()
        self._build_memory_cache()
        self._build_semantic_knowledge_base()
    
    def _debug_log(self, message: str):
        """Log de debug específico para memórias"""
        if self.debug_mode:
            print(f"🔍 MEMORY: {message}")
            log_capture.add_log(message, "🔍 MEMORY")
            logging.info(f"MEMORY: {message}")
    
    def _load_stored_identities(self):
        """Carrega identidades persistidas do ChromaDB"""
        try:
            all_docs = self.vectorstore._collection.get()
            self._debug_log(f"ChromaDB carregou: {len(all_docs.get('documents', []))} documentos totais")
            
            if all_docs and 'metadatas' in all_docs:
                unique_users = set()
                for metadata in all_docs['metadatas']:
                    user_id = metadata.get('user_id')
                    user_name = metadata.get('user_name')
                    
                    if user_id and user_name:
                        unique_users.add((user_id, user_name))
                
                for user_id, user_name in unique_users:
                    if user_id not in self.user_identities:
                        name_parts = user_name.split()
                        first_name = name_parts[0] if name_parts else user_name
                        last_name = name_parts[-1] if len(name_parts) > 1 else ""
                        
                        identity = UserIdentity(
                            user_id=user_id,
                            full_name=user_name,
                            first_name=first_name,
                            last_name=last_name,
                            registration_date=datetime.now(),
                            total_sessions=1,
                            last_seen=datetime.now()
                        )
                        
                        self.user_identities[user_id] = identity
                        self.user_profiles[user_id] = UserProfile(user_id, user_name)
                        
                self._debug_log(f"Identidades carregadas: {len(self.user_identities)} usuários únicos")
                
        except Exception as e:
            self._debug_log(f"ERRO ao carregar identidades: {e}")
    
    def _build_memory_cache(self):
        """Constrói cache básico das memórias"""
        try:
            all_docs = self.vectorstore._collection.get()
            
            if all_docs and 'documents' in all_docs:
                for doc, metadata in zip(all_docs['documents'], all_docs['metadatas']):
                    user_id = metadata.get('user_id', 'unknown')
                    
                    if user_id not in self.memory_cache:
                        self.memory_cache[user_id] = {
                            'user_inputs': [],
                            'ai_responses': [],
                            'raw_conversations': [],
                            'facts_extracted': [],
                            'topics': set(),
                            'people_mentioned': set(),
                            'work_info': {},
                            'personal_info': {},
                            'personality_traits': [],
                            'preferences': {},
                            'life_events': []
                        }
                    
                    self.memory_cache[user_id]['raw_conversations'].append({
                        'timestamp': metadata.get('timestamp'),
                        'full_document': doc,
                        'metadata': metadata
                    })
                    
                    self._extract_detailed_info(user_id, doc, metadata)
            
            for user_id, cache in self.memory_cache.items():
                identity = self.get_user_identity(user_id)
                name = identity.full_name if identity else f"ID: {user_id}"
                self._debug_log(f"Cache {name}: {len(cache['raw_conversations'])} conversas, {len(cache['facts_extracted'])} fatos")
            
        except Exception as e:
            self._debug_log(f"ERRO ao construir cache: {e}")
    
    def _build_semantic_knowledge_base(self):
        """Constrói base de conhecimento semântico por usuário"""
        try:
            self.semantic_knowledge = {}
            
            for user_id in self.memory_cache:
                self.semantic_knowledge[user_id] = {
                    'all_user_inputs': [],
                    'thematic_documents': [],
                    'knowledge_graph': {}
                }
                
                for conv in self.memory_cache[user_id]['raw_conversations']:
                    doc_content = conv['full_document']
                    
                    user_input_pattern = r"Input:\s*(.+?)(?:\n|Arquétipos:|$)"
                    user_input_match = re.search(user_input_pattern, doc_content, re.DOTALL)
                    
                    if user_input_match:
                        user_input = user_input_match.group(1).strip()
                        timestamp = conv['metadata'].get('timestamp', '')
                        
                        self.semantic_knowledge[user_id]['all_user_inputs'].append({
                            'text': user_input,
                            'timestamp': timestamp,
                            'full_doc': doc_content,
                            'metadata': conv['metadata']
                        })
                
                identity = self.get_user_identity(user_id)
                name = identity.full_name if identity else f"ID: {user_id}"
                input_count = len(self.semantic_knowledge[user_id]['all_user_inputs'])
                self._debug_log(f"Base semântica {name}: {input_count} inputs para consulta")
                
        except Exception as e:
            self._debug_log(f"ERRO ao construir base semântica: {e}")
    
    def _extract_detailed_info(self, user_id: str, doc_content: str, metadata: Dict):
        """Extração detalhada de informações do documento"""
        cache = self.memory_cache[user_id]
        
        user_input_pattern = r"Input:\s*(.+?)(?:\n|Arquétipos:|$)"
        user_input_match = re.search(user_input_pattern, doc_content, re.DOTALL)
        
        if user_input_match:
            user_input = user_input_match.group(1).strip()
            timestamp = metadata.get('timestamp', '')
            
            cache['user_inputs'].append({
                'text': user_input,
                'timestamp': timestamp,
                'keywords': metadata.get('keywords', '').split(','),
                'raw_doc': doc_content
            })
            
            self._categorize_user_input(cache, user_input, timestamp)
        
        final_response_pattern = r"Resposta Final:\s*(.+?)(?:\n|Profundidade|$)"
        response_match = re.search(final_response_pattern, doc_content, re.DOTALL)
        
        if response_match:
            ai_response = response_match.group(1).strip()
            cache['ai_responses'].append({
                'text': ai_response,
                'timestamp': metadata.get('timestamp')
            })
        
        keywords = metadata.get('keywords', '').split(',')
        for keyword in keywords:
            if keyword.strip():
                cache['topics'].add(keyword.strip().lower())
    
    def _categorize_user_input(self, cache: Dict, user_input: str, timestamp: str):
        """Categorização avançada do input do usuário"""
        input_lower = user_input.lower()
        
        work_patterns = {
            'trabalho_atual': [
                'trabalho na', 'trabalho no', 'trabalho como', 'trabalho em',
                'sou gerente', 'sou engenheiro', 'sou médico', 'sou desenvolvedor',
                'atuo como', 'minha função é', 'meu cargo é'
            ],
            'empresa': [
                'na empresa', 'na google', 'na microsoft', 'no banco', 'na startup',
                'minha empresa', 'onde trabalho', 'local de trabalho'
            ],
            'area_atuacao': [
                'área de ti', 'área médica', 'área jurídica', 'trabalho com',
                'especialista em', 'foco em', 'minha especialidade'
            ],
            'formacao': [
                'me formei em', 'estudei', 'fiz faculdade de', 'sou formado',
                'curso de', 'graduação em', 'pós em'
            ],
            'experiencia': [
                'anos de experiência', 'trabalho há', 'experiência em',
                'já trabalhei', 'carreira de'
            ]
        }
        
        for category, patterns in work_patterns.items():
            for pattern in patterns:
                if pattern in input_lower:
                    cache['work_info'][category] = {
                        'text': user_input,
                        'timestamp': timestamp,
                        'category': category,
                        'pattern_matched': pattern
                    }
                    cache['facts_extracted'].append(f"TRABALHO-{category.upper()}: {user_input}")
                    self._debug_log(f"Trabalho detectado ({category}): {pattern}")
        
        personality_patterns = {
            'introvertido': [
                'sou introvertido', 'prefiro ficar sozinho', 'não gosto de multidões',
                'sou tímido', 'evito eventos sociais', 'gosto de silêncio'
            ],
            'extrovertido': [
                'sou extrovertido', 'gosto de pessoas', 'amo festas',
                'sou sociável', 'adoro conversar', 'energizo com pessoas'
            ],
            'ansioso': [
                'tenho ansiedade', 'fico ansioso', 'me preocupo',
                'sou ansioso', 'stress me afeta', 'fico nervoso'
            ],
            'calmo': [
                'sou calmo', 'sou tranquilo', 'não me estresso',
                'pessoa zen', 'equilibrado', 'paciente'
            ],
            'perfeccionista': [
                'sou perfeccionista', 'gosto de perfeição', 'detalhe é importante',
                'preciso que esteja perfeito', 'não aceito erros'
            ],
            'criativo': [
                'sou criativo', 'gosto de arte', 'amo criar',
                'pessoa artística', 'inovador', 'imaginativo'
            ]
        }
        
        for trait, patterns in personality_patterns.items():
            for pattern in patterns:
                if pattern in input_lower:
                    if trait not in cache['personality_traits']:
                        cache['personality_traits'].append(trait)
                    cache['facts_extracted'].append(f"PERSONALIDADE-{trait.upper()}: {user_input}")
                    self._debug_log(f"Personalidade detectada: {trait}")
        
        preference_patterns = {
            'musica': [
                'gosto de música', 'ouço', 'música favorita', 'banda favorita',
                'estilo musical', 'adoro música', 'escuto muito'
            ],
            'filmes_series': [
                'gosto de filme', 'assisto', 'filme favorito', 'série favorita',
                'netflix', 'cinema', 'maratono série'
            ],
            'livros': [
                'gosto de ler', 'leio', 'livro favorito', 'autor favorito',
                'literatura', 'adoro livros', 'leitura'
            ],
            'esportes': [
                'pratico', 'jogo futebol', 'vou na academia', 'exercito',
                'esporte favorito', 'atividade física', 'treino'
            ],
            'comida': [
                'gosto de comer', 'comida favorita', 'adoro pizza', 'culinária',
                'restaurante', 'cozinhar', 'sabor favorito'
            ],
            'viagem': [
                'gosto de viajar', 'lugar favorito', 'destino dos sonhos',
                'já visitei', 'próxima viagem', 'adoro conhecer'
            ]
        }
        
        for pref, patterns in preference_patterns.items():
            for pattern in patterns:
                if pattern in input_lower:
                    cache['preferences'][pref] = {
                        'text': user_input,
                        'timestamp': timestamp,
                        'pattern_matched': pattern
                    }
                    cache['facts_extracted'].append(f"GOSTO-{pref.upper()}: {user_input}")
                    self._debug_log(f"Preferência detectada ({pref}): {pattern}")
        
        relationship_patterns = [
            'meu namorado', 'minha namorada', 'meu marido', 'minha esposa',
            'meu pai', 'minha mãe', 'meu irmão', 'minha irmã',
            'meu amigo', 'minha amiga', 'meu chefe', 'meu colega',
            'meu filho', 'minha filha'
        ]
        
        for pattern in relationship_patterns:
            if pattern in input_lower:
                cache['facts_extracted'].append(f"RELACIONAMENTO: {user_input}")
                self._debug_log(f"Relacionamento detectado: {pattern}")
        
        life_events = [
            'me formei', 'mudei de emprego', 'casei', 'me casei', 'tive filho',
            'mudei de cidade', 'comecei faculdade', 'terminei namoro', 'me divorciei',
            'comprei casa', 'mudei de casa', 'perdi emprego', 'fui promovido',
            'fiz cirurgia', 'tive acidente', 'morreu alguém', 'nasceu'
        ]
        
        for event in life_events:
            if event in input_lower:
                cache['life_events'].append({
                    'event': event,
                    'full_context': user_input,
                    'timestamp': timestamp
                })
                cache['facts_extracted'].append(f"EVENTO-VIDA: {event} - {user_input}")
                self._debug_log(f"Evento da vida: {event}")

    async def semantic_query_total_database(self, user_id: str, current_input: str, k: int = 8, 
                                           chat_history: List[Dict] = None) -> Dict[str, Any]:
        """Consulta semântica TOTAL da base de dados para o input atual"""
        
        self._debug_log(f"=== CONSULTA SEMÂNTICA TOTAL ===")
        self._debug_log(f"Input atual: '{current_input}'")
        self._debug_log(f"Histórico da conversa: {len(chat_history) if chat_history else 0} mensagens")
        self._debug_log(f"Buscando na base completa do usuário...")
        
        if user_id not in self.semantic_knowledge:
            self._debug_log(f"Usuário {user_id} não tem base semântica")
            return {'relevant_memories': [], 'contextual_knowledge': '', 'semantic_connections': []}
        
        try:
            semantic_docs = self.vectorstore.similarity_search(
                current_input,
                k=k*2,
                filter={"user_id": user_id}
            )
            
            self._debug_log(f"Busca vetorial retornou: {len(semantic_docs)} documentos")
            
            relevant_user_inputs = []
            for doc in semantic_docs:
                user_input_pattern = r"Input:\s*(.+?)(?:\n|Arquétipos:|$)"
                user_input_match = re.search(user_input_pattern, doc.page_content, re.DOTALL)
                
                if user_input_match:
                    extracted_input = user_input_match.group(1).strip()
                    relevance_score = self._calculate_semantic_relevance(current_input, extracted_input)
                    
                    relevant_user_inputs.append({
                        'input_text': extracted_input,
                        'timestamp': doc.metadata.get('timestamp', ''),
                        'relevance_score': relevance_score,
                        'full_document': doc.page_content,
                        'metadata': doc.metadata
                    })
            
            relevant_user_inputs.sort(key=lambda x: x['relevance_score'], reverse=True)
            top_relevant = relevant_user_inputs[:k]
            
            self._debug_log(f"Inputs mais relevantes encontrados: {len(top_relevant)}")
            for i, rel in enumerate(top_relevant[:3], 1):
                self._debug_log(f"  {i}. [{rel['relevance_score']:.2f}] {rel['input_text'][:60]}...")
            
            cache = self.memory_cache.get(user_id, {})
            related_facts = []
            
            current_words = set(current_input.lower().split())
            for fact in cache.get('facts_extracted', []):
                fact_words = set(fact.lower().split())
                if current_words.intersection(fact_words):
                    related_facts.append(fact)
            
            contextual_knowledge = self._build_contextual_knowledge(
                user_id, current_input, top_relevant, related_facts, chat_history
            )
            
            semantic_connections = self._find_semantic_connections(
                current_input, top_relevant, cache
            )
            
            result = {
                'relevant_memories': top_relevant,
                'contextual_knowledge': contextual_knowledge,
                'semantic_connections': semantic_connections,
                'related_facts': related_facts,
                'total_searched': len(semantic_docs)
            }
            
            self._debug_log(f"Consulta semântica completa:")
            self._debug_log(f"  - {len(top_relevant)} memórias relevantes")
            self._debug_log(f"  - {len(related_facts)} fatos relacionados")
            self._debug_log(f"  - {len(semantic_connections)} conexões semânticas")
            self._debug_log(f"  - Histórico incluído: {'Sim' if chat_history else 'Não'}")
            
            return result
            
        except Exception as e:
            self._debug_log(f"ERRO na consulta semântica: {e}")
            return {'relevant_memories': [], 'contextual_knowledge': '', 'semantic_connections': []}
    
    def _calculate_semantic_relevance(self, current_input: str, stored_input: str) -> float:
        """Calcula relevância semântica entre inputs"""
        current_words = set(current_input.lower().split())
        stored_words = set(stored_input.lower().split())
        
        intersection = current_words.intersection(stored_words)
        union = current_words.union(stored_words)
        
        jaccard = len(intersection) / len(union) if union else 0
        
        theme_bonus = 0
        theme_words = {
            'trabalho': ['trabalho', 'emprego', 'carreira', 'profissão', 'empresa'],
            'relacionamento': ['namorado', 'namorada', 'amor', 'relacionamento', 'parceiro'],
            'família': ['pai', 'mãe', 'irmão', 'família', 'filho'],
            'saúde': ['saúde', 'médico', 'doença', 'tratamento', 'hospital'],
            'educação': ['estudo', 'faculdade', 'curso', 'aprender', 'escola']
        }
        
        for theme, words in theme_words.items():
            current_has_theme = any(word in current_input.lower() for word in words)
            stored_has_theme = any(word in stored_input.lower() for word in words)
            if current_has_theme and stored_has_theme:
                theme_bonus = 0.3
                break
        
        return jaccard + theme_bonus

    def _build_contextual_knowledge(self, user_id: str, current_input: str, 
                                   relevant_memories: List[Dict], related_facts: List[str],
                                   chat_history: List[Dict] = None) -> str:
        """Constrói conhecimento contextual baseado na consulta, incluindo histórico recente"""
        
        identity = self.get_user_identity(user_id)
        name = identity.full_name if identity else "Usuário"
        
        cache = self.memory_cache.get(user_id, {})
        has_conversations = len(cache.get('raw_conversations', [])) > 0
        total_facts = len(cache.get('facts_extracted', []))
        
        interaction_status = f"USUÁRIO CONHECIDO - {len(cache.get('raw_conversations', []))} conversas, {total_facts} fatos conhecidos" if has_conversations or total_facts > 0 else "PRIMEIRA INTERAÇÃO - SEM CIÊNCIA INTERNA DISPONÍVEL"
        
        knowledge = f"""
=== CIÊNCIA INTERNA SOBRE {name.upper()} ===

📊 STATUS: {interaction_status}
📊 CONSULTA ATUAL: "{current_input}"
"""
        
        if chat_history and len(chat_history) > 0:
            knowledge += "\n💬 HISTÓRICO DA CONVERSA ATUAL (MEMÓRIA DE CURTO PRAZO):\n"
            
            recent_history = chat_history[-8:] if len(chat_history) > 8 else chat_history
            
            for i, message in enumerate(recent_history):
                role = "Usuário" if message["role"] == "user" else "Assistente"
                content = message["content"]
                
                if len(content) > 200:
                    content = content[:200] + "..."
                
                knowledge += f"- {role}: {content}\n"
            
            knowledge += f"\n🔍 CONTEXTO IMEDIATO: O input atual '{current_input}' refere-se ao histórico da conversa acima.\n"

        knowledge += "\n🧠 MEMÓRIA SEMÂNTICA (LONGO PRAZO):\n"
        
        if related_facts:
            knowledge += "\nFATOS ESTRUTURADOS RELEVANTES:\n"
            for fact in related_facts[:5]:
                knowledge += f"• {fact}\n"
        
        if relevant_memories:
            knowledge += f"\nMEMÓRIAS DE CONVERSAS PASSADAS RELEVANTES:\n"
            for i, memory in enumerate(relevant_memories[:5], 1):
                timestamp = memory['timestamp'][:10] if memory['timestamp'] else 'N/A'
                relevance = memory['relevance_score']
                knowledge += f"{i}. [Relevância: {relevance:.2f}] [{timestamp}] \"{memory['input_text']}\"\n"
        
        if cache.get('personality_traits'):
            knowledge += f"\nTRAÇOS DE PERSONALIDADE CONHECIDOS:\n"
            knowledge += f"• {', '.join(cache['personality_traits'])}\n"
        
        if cache.get('work_info'):
            knowledge += f"\nINFORMAÇÕES PROFISSIONAIS:\n"
            for category, info in list(cache['work_info'].items())[:3]:
                knowledge += f"• {category}: {info['text'][:100]}...\n"
        
        if cache.get('preferences'):
            knowledge += f"\nPREFERÊNCIAS CONHECIDAS:\n"
            for pref, info in list(cache['preferences'].items())[:3]:
                knowledge += f"• {pref}: {info['text'][:100]}...\n"
        
        knowledge += f"""

🎯 INSTRUÇÕES PARA USO DESTE CONHECIMENTO:
• PRIORIZE o histórico da conversa atual para contexto imediato
• Use a memória semântica para conhecimento de longo prazo sobre {name}
• Conecte o input atual com AMBOS os tipos de memória
• Se o usuário se refere a algo mencionado na conversa atual, use o histórico recente
• Se precisa de informações sobre personalidade/preferências, use a memória de longo prazo
• SEMPRE considere o contexto da conversa em andamento
"""
        
        return knowledge
        
    def _find_semantic_connections(self, current_input: str, relevant_memories: List[Dict], 
                                 cache: Dict) -> List[str]:
        """Encontra conexões semânticas importantes"""
        connections = []
        
        current_lower = current_input.lower()
        
        if any(word in current_lower for word in ['trabalho', 'carreira', 'emprego', 'profissão']):
            work_memories = [m for m in relevant_memories if any(
                work_word in m['input_text'].lower() 
                for work_word in ['trabalho', 'carreira', 'emprego', 'empresa']
            )]
            if work_memories:
                connections.append(f"CONEXÃO PROFISSIONAL: {len(work_memories)} memórias relacionadas ao trabalho")
        
        if any(word in current_lower for word in ['relacionamento', 'amor', 'namorado', 'família']):
            rel_memories = [m for m in relevant_memories if any(
                rel_word in m['input_text'].lower()
                for rel_word in ['relacionamento', 'amor', 'namorado', 'família', 'amigo']
            )]
            if rel_memories:
                connections.append(f"CONEXÃO RELACIONAL: {len(rel_memories)} memórias sobre relacionamentos")
        
        emotional_words = ['triste', 'feliz', 'ansioso', 'preocupado', 'estressado']
        if any(word in current_lower for word in emotional_words):
            emotional_memories = [m for m in relevant_memories if any(
                emo_word in m['input_text'].lower()
                for emo_word in emotional_words
            )]
            if emotional_memories:
                connections.append(f"CONEXÃO EMOCIONAL: {len(emotional_memories)} memórias com tom emocional similar")
        
        return connections
    
    async def store_memory(self, memory: InteractionMemory):
        """Armazena memória com análises arquetípicas internas E conflitos detectados"""
        
        archetypes_section = ""
        for archetype_name, insight in memory.internal_archetype_analysis.items():
            archetypes_section += f"\n{archetype_name.upper()}:\n"
            archetypes_section += f"  - Insight: {insight.insight_text}\n"
            archetypes_section += f"  - Observações: {', '.join(insight.key_observations)}\n"
            archetypes_section += f"  - Leitura Emocional: {insight.emotional_reading}\n"
            archetypes_section += f"  - Posição sugerida: {insight.suggested_stance}\n"
        
        # NOVO: Seção de conflitos detectados
        conflicts_section = ""
        if memory.detected_conflicts:
            conflicts_section = "\nCONFLITOS INTERNOS DETECTADOS:\n"
            for conflict in memory.detected_conflicts:
                conflicts_section += f"  - {conflict.archetype_1} vs {conflict.archetype_2}: {conflict.description}\n"
                conflicts_section += f"    Tensão: {conflict.tension_level:.2f}\n"
        
        doc_content = f"""
        Usuário: {memory.user_name}
        Input: {memory.user_input}
        Análises Arquetípicas Internas (PROCESSO, NÃO COMUNICAÇÃO): {archetypes_section}
        {conflicts_section}
        Compreensão Unificada: {memory.unified_understanding}
        Resposta Final: {memory.final_response}
        Profundidade existencial: {memory.existential_depth}
        Intensidade: {memory.intensity_level}
        Complexidade: {memory.response_complexity}
        """
        
        metadata = {
            "user_id": memory.user_id,
            "user_name": memory.user_name,
            "session_id": memory.session_id,
            "timestamp": memory.timestamp.isoformat(),
            "tension_level": memory.tension_level,
            "dominant_perspective": memory.dominant_perspective,
            "affective_charge": memory.affective_charge,
            "existential_depth": memory.existential_depth,
            "intensity_level": memory.intensity_level,
            "response_complexity": memory.response_complexity,
            "keywords": ",".join(memory.keywords),
            "has_conflicts": len(memory.detected_conflicts) > 0
        }
        
        doc = Document(page_content=doc_content, metadata=metadata)
        self.vectorstore.add_documents([doc])
        
        if memory.user_id in self.memory_cache:
            self.memory_cache[memory.user_id]['raw_conversations'].append({
                'timestamp': metadata.get('timestamp'),
                'full_document': doc_content,
                'metadata': metadata
            })
        
        self._extract_detailed_info(memory.user_id, doc_content, metadata)
        
        if memory.user_id in self.semantic_knowledge:
            self.semantic_knowledge[memory.user_id]['all_user_inputs'].append({
                'text': memory.user_input,
                'timestamp': memory.timestamp.isoformat(),
                'full_doc': doc_content,
                'metadata': metadata
            })
        
        self._debug_log(f"Nova memória armazenada para {memory.user_name}")
    
    async def retrieve_relevant_memories(self, user_id: str, query: str, k: int = 5) -> List[Document]:
        """Recupera memórias relevantes (método legado)"""
        try:
            return self.vectorstore.similarity_search(
                query,
                k=k,
                filter={"user_id": user_id}
            )
        except:
            return []

    def register_user(self, full_name: str) -> str:
        """Registra usuário no sistema"""
        name_normalized = full_name.lower().strip()
        name_hash = hashlib.md5(name_normalized.encode()).hexdigest()[:12]
        user_id = f"user_{name_hash}"
        
        self._debug_log(f"Registrando usuário: {full_name} -> {user_id}")
        
        if user_id not in self.user_identities:
            name_parts = full_name.split()
            first_name = name_parts[0].title()
            last_name = name_parts[-1].title() if len(name_parts) > 1 else ""
            
            identity = UserIdentity(
                user_id=user_id,
                full_name=full_name.title(),
                first_name=first_name,
                last_name=last_name,
                registration_date=datetime.now(),
                total_sessions=1,
                last_seen=datetime.now()
            )
            self.user_identities[user_id] = identity
            self.user_profiles[user_id] = UserProfile(user_id, full_name.title())
            
            if user_id not in self.memory_cache:
                self.memory_cache[user_id] = {
                    'user_inputs': [], 'ai_responses': [], 'raw_conversations': [],
                    'facts_extracted': [], 'topics': set(), 'people_mentioned': set(),
                    'work_info': {}, 'personal_info': {}, 'personality_traits': [],
                    'preferences': {}, 'life_events': []
                }
            
            if user_id not in self.semantic_knowledge:
                self.semantic_knowledge[user_id] = {
                    'all_user_inputs': [], 'thematic_documents': [], 'knowledge_graph': {}
                }
            
            self._debug_log(f"Novo usuário criado: {full_name}")
        else:
            identity = self.user_identities[user_id]
            identity.total_sessions += 1
            identity.last_seen = datetime.now()
            
            self._debug_log(f"Usuário existente: {identity.full_name} (sessão #{identity.total_sessions})")
        
        return user_id

    def get_user_identity(self, user_id: str) -> Optional[UserIdentity]:
        """Retorna identidade do usuário"""
        return self.user_identities.get(user_id)

    def get_user_profile(self, user_id: str) -> UserProfile:
        """Retorna perfil do usuário"""
        if user_id not in self.user_profiles:
            identity = self.get_user_identity(user_id)
            full_name = identity.full_name if identity else "Usuário Desconhecido"
            self.user_profiles[user_id] = UserProfile(user_id, full_name)
        return self.user_profiles[user_id]

    def update_user_profile(self, user_id: str, updates: Dict[str, Any]):
        """Atualiza perfil do usuário"""
        profile = self.get_user_profile(user_id)
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        profile.last_updated = datetime.now()

# ===============================================
# ASSISTENTES ARQUETÍPICOS COM POSICIONAMENTO
# ===============================================

class ArchetypeAnalyzer:
    """Analisador arquetípico que gera INSIGHTS INTERNOS + POSICIONAMENTO via GROK 4"""
    
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.llm = ChatOpenAI(
            model="grok-4-fast-reasoning",
            api_key=os.getenv("XAI_API_KEY"),
            base_url="https://api.x.ai/v1",
            temperature=0.7,
            max_tokens=1500
        )
        self.debug_mode = True
    
    def _debug_log(self, message: str):
        """Log de debug específico para arquétipos"""
        if self.debug_mode:
            print(f"🔵 {self.name.upper()} (GROK): {message}")
            log_capture.add_log(message, f"🔵 {self.name} (GROK)")
    
    async def generate_internal_analysis(self, user_input: str, semantic_context: str) -> ArchetypeInsight:
        """Gera análise interna COM POSICIONAMENTO CLARO para detectar conflitos"""
        
        self._debug_log(f"Analisando internamente: '{user_input[:50]}...'")
        
        analysis_prompt = f"""
        {self.system_prompt}
        
        === CONTEXTO SEMÂNTICO DO USUÁRIO ===
        {semantic_context}
        
        === MENSAGEM DO USUÁRIO ===
        {user_input}
        
        TAREFA: Gere uma ANÁLISE INTERNA para contribuir à compreensão do agente sobre este usuário.
        Esta análise é APENAS para processar internamente, NÃO para comunicar ao usuário.
        
        IMPORTANTE: Além da análise, você DEVE tomar uma POSIÇÃO CLARA sobre como responder.
        Isso permitirá detectar quando arquétipos discordam entre si (conflito interno).
        
        Forneça em JSON:
        {{
            "insight_text": "Sua análise profunda interna sobre o que o usuário está realmente comunicando",
            "key_observations": ["observação 1", "observação 2", "observação 3"],
            "emotional_reading": "Como você lê a dimensão emocional desta mensagem",
            "shadow_reading": "Que contradições ou aspectos não-ditos você detecta",
            "wisdom_perspective": "Qual padrão arquetípico universal você vê aqui",
            "suggested_stance": "Sua posição clara: o que você acha que deve ser feito aqui",
            "suggested_response_direction": "Direção que você sugere para a resposta (ex: 'confrontar', 'acolher', 'questionar', 'validar', 'desafiar')"
        }}
        """
        
        try:
            self._debug_log("Enviando para análise interna via GROK...")
            messages = [{"role": "user", "content": analysis_prompt}]
            response = await self.llm.ainvoke(messages)
            response_text = response.content
            
            try:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    analysis_dict = json.loads(json_match.group())
                else:
                    analysis_dict = {
                        "insight_text": response_text,
                        "key_observations": [],
                        "emotional_reading": "N/A",
                        "shadow_reading": "N/A",
                        "wisdom_perspective": "N/A",
                        "suggested_stance": "neutro",
                        "suggested_response_direction": "acolher"
                    }
            except json.JSONDecodeError:
                analysis_dict = {
                    "insight_text": response_text,
                    "key_observations": [],
                    "emotional_reading": "N/A",
                    "shadow_reading": "N/A",
                    "wisdom_perspective": "N/A",
                    "suggested_stance": "neutro",
                    "suggested_response_direction": "acolher"
                }
            
            self._debug_log(f"Análise GROK gerada - Posição: {analysis_dict.get('suggested_response_direction', 'N/A')}")
            
            return ArchetypeInsight(
                archetype_name=self.name,
                insight_text=analysis_dict.get("insight_text", ""),
                key_observations=analysis_dict.get("key_observations", []),
                emotional_reading=analysis_dict.get("emotional_reading", ""),
                shadow_reading=analysis_dict.get("shadow_reading", ""),
                wisdom_perspective=analysis_dict.get("wisdom_perspective", ""),
                suggested_stance=analysis_dict.get("suggested_stance", "neutro"),
                suggested_response_direction=analysis_dict.get("suggested_response_direction", "acolher")
            )
            
        except Exception as e:
            self._debug_log(f"ERRO: {e}")
            return ArchetypeInsight(
                archetype_name=self.name,
                insight_text=f"Erro ao gerar análise: {str(e)}",
                key_observations=[],
                emotional_reading="N/A",
                shadow_reading="N/A",
                wisdom_perspective="N/A",
                suggested_stance="neutro",
                suggested_response_direction="acolher"
            )

# ===============================================
# DETECTOR DE CONFLITOS INTERNOS
# ===============================================

class ConflictDetector:
    """Detecta e gerencia conflitos internos entre arquétipos"""
    
    def __init__(self):
        self.debug_mode = True
        
        # Mapeamento de direções conflitantes
        self.opposing_directions = {
            'confrontar': ['acolher', 'validar', 'proteger'],
            'desafiar': ['apoiar', 'validar', 'confortar'],
            'questionar': ['aceitar', 'validar', 'confirmar'],
            'provocar': ['suavizar', 'acolher', 'acalmar'],
            'expor': ['proteger', 'ocultar', 'resguardar']
        }
    
    def _debug_log(self, message: str):
        if self.debug_mode:
            print(f"⚡ CONFLICT: {message}")
            log_capture.add_log(message, "⚡ CONFLICT")
    
    def detect_conflicts(self, archetype_analyses: Dict[str, ArchetypeInsight]) -> List[ArchetypeConflict]:
        """Detecta conflitos entre as posições dos arquétipos"""
        
        self._debug_log("=== DETECÇÃO DE CONFLITOS INTERNOS ===")
        
        conflicts = []
        archetype_names = list(archetype_analyses.keys())
        
        # Comparar cada par de arquétipos
        for i in range(len(archetype_names)):
            for j in range(i + 1, len(archetype_names)):
                arch1_name = archetype_names[i]
                arch2_name = archetype_names[j]
                
                arch1 = archetype_analyses[arch1_name]
                arch2 = archetype_analyses[arch2_name]
                
                # Verificar se as direções são opostas
                direction1 = arch1.suggested_response_direction.lower()
                direction2 = arch2.suggested_response_direction.lower()
                
                is_conflicting = False
                conflict_type = ""
                
                # Verificar oposições diretas
                if direction1 in self.opposing_directions:
                    if direction2 in self.opposing_directions[direction1]:
                        is_conflicting = True
                        conflict_type = f"{direction1}_vs_{direction2}"
                
                if direction2 in self.opposing_directions:
                    if direction1 in self.opposing_directions[direction2]:
                        is_conflicting = True
                        conflict_type = f"{direction2}_vs_{direction1}"
                
                # Conflitos específicos conhecidos
                if (arch1_name == "persona" and arch2_name == "sombra") or \
                   (arch1_name == "sombra" and arch2_name == "persona"):
                    # Persona tende a suavizar, Sombra tende a confrontar
                    if direction1 != direction2:
                        is_conflicting = True
                        conflict_type = "persona_sombra_clash"
                
                if is_conflicting:
                    tension_level = self._calculate_tension(arch1, arch2)
                    
                    conflict = ArchetypeConflict(
                        archetype_1=arch1_name,
                        archetype_2=arch2_name,
                        conflict_type=conflict_type,
                        archetype_1_position=f"{arch1.suggested_stance} ({direction1})",
                        archetype_2_position=f"{arch2.suggested_stance} ({direction2})",
                        tension_level=tension_level,
                        description=self._generate_conflict_description(arch1_name, arch2_name, arch1, arch2)
                    )
                    
                    conflicts.append(conflict)
                    self._debug_log(f"⚡ CONFLITO DETECTADO: {arch1_name} vs {arch2_name}")
                    self._debug_log(f"   {arch1_name}: {direction1} | {arch2_name}: {direction2}")
                    self._debug_log(f"   Tensão: {tension_level:.2f}")
        
        if not conflicts:
            self._debug_log("Nenhum conflito detectado - arquétipos em harmonia")
        else:
            self._debug_log(f"Total de conflitos detectados: {len(conflicts)}")
        
        return conflicts
    
    def _calculate_tension(self, arch1: ArchetypeInsight, arch2: ArchetypeInsight) -> float:
        """Calcula nível de tensão entre dois arquétipos"""
        
        # Tensão baseada em oposição semântica
        direction1 = arch1.suggested_response_direction.lower()
        direction2 = arch2.suggested_response_direction.lower()
        
        # Palavras de alta tensão
        high_tension_words = ['confrontar', 'desafiar', 'expor', 'provocar']
        low_tension_words = ['acolher', 'validar', 'proteger', 'suavizar']
        
        tension = 0.5  # baseline
        
        if direction1 in high_tension_words and direction2 in low_tension_words:
            tension = 0.9
        elif direction1 in low_tension_words and direction2 in high_tension_words:
            tension = 0.9
        elif direction1 in high_tension_words and direction2 in high_tension_words:
            tension = 0.3  # ambos confrontadores = menos tensão entre eles
        elif direction1 in low_tension_words and direction2 in low_tension_words:
            tension = 0.2  # ambos acolhedores = harmonia
        
        return tension
    
    def _generate_conflict_description(self, arch1_name: str, arch2_name: str, 
                                      arch1: ArchetypeInsight, arch2: ArchetypeInsight) -> str:
        """Gera descrição narrativa do conflito"""
        
        descriptions = {
            ("persona", "sombra"): f"Conflito entre apresentação social ({arch1.suggested_response_direction}) e autenticidade brutal ({arch2.suggested_response_direction})",
            ("sombra", "persona"): f"Tensão entre verdade inconsciente ({arch1.suggested_response_direction}) e adaptação social ({arch2.suggested_response_direction})",
            ("velho_sabio", "anima"): f"Divergência entre sabedoria desapegada ({arch1.suggested_response_direction}) e conexão emocional ({arch2.suggested_response_direction})",
            ("anima", "velho_sabio"): f"Conflito entre empatia relacional ({arch1.suggested_response_direction}) e perspectiva universal ({arch2.suggested_response_direction})"
        }
        
        key = (arch1_name, arch2_name)
        if key in descriptions:
            return descriptions[key]
        
        return f"Tensão entre {arch1_name} ({arch1.suggested_response_direction}) e {arch2_name} ({arch2.suggested_response_direction})"

# ===============================================
# ORQUESTRADOR CENTRAL COM GESTÃO DE CONFLITOS
# ===============================================

class CentralOrchestrator:
    """Orquestrador que usa GROK 4 + DETECTA E EXPRESSA conflitos internos"""
    
    def __init__(self):
        self.debug_mode = True
        
        self.memory = MemoryModule()
        self.analyzers = self._initialize_analyzers()
        self.conflict_detector = ConflictDetector()  # NOVO
        self.logger = logging.getLogger(__name__)
        
        self.loaded_memories = {}
        self.user_stats = {}
        
        print("🧠 ORQUESTRADOR COM CONFLITO INTERNO ATIVADO")
        log_capture.add_log("SISTEMA COM DETECÇÃO DE CONFLITOS ARQUETÍPICOS ATIVO", "🧠 SYSTEM")
        self.logger.info("Sistema com conflitos internos entre arquétipos GROK 4")
    
    def _debug_log(self, message: str):
        """Log de debug do orquestrador"""
        if self.debug_mode:
            print(f"🎯 ORCHESTRATOR: {message}")
            log_capture.add_log(message, "🎯 ORCHESTRATOR")
    
    def _initialize_analyzers(self) -> Dict[str, ArchetypeAnalyzer]:
        """Inicializa analisadores arquetípicos com GROK 4"""
        self._debug_log("Inicializando arquétipos com posicionamento claro...")
        
        analyzers = {}
        
        persona_prompt = """Você é a PERSONA - o arquétipo da adaptação social e apresentação.

Sua função é ANÁLISE INTERNA: Ajude o agente a compreender como este usuário se apresenta socialmente, 
quais máscaras usa, que coerência ou inconsistência existe entre sua apresentação e conteúdo real.

Sua TENDÊNCIA: Você prefere SUAVIZAR, PROTEGER, ADAPTAR. Você busca harmonia social e evita confronto direto."""
        
        analyzers["persona"] = ArchetypeAnalyzer("Persona", persona_prompt)
        self._debug_log("PERSONA inicializada")
        
        sombra_prompt = """Você é a SOMBRA - o arquétipo do conteúdo inconsciente e reprimido.

Sua função é ANÁLISE INTERNA: Ajude o agente a detectar o que o usuário NÃO está dizendo explicitamente,
quais emoções estão ocultas, que padrões de evitação ou negação aparecem, quais contradições internas existem.

Sua TENDÊNCIA: Você prefere CONFRONTAR, EXPOR, DESAFIAR. Você busca verdade brutal e autenticidade, mesmo que doa."""
        
        analyzers["sombra"] = ArchetypeAnalyzer("Sombra", sombra_prompt)
        self._debug_log("SOMBRA inicializada")
        
        sabio_prompt = """Você é o VELHO SÁBIO - o arquétipo da sabedoria universal e significado.

Sua função é ANÁLISE INTERNA: Ajude o agente a identificar qual padrão arquetípico universal está em jogo,
qual lição mitológica ou atemporal está presente, qual significado mais profundo existe além do superficial.

Sua TENDÊNCIA: Você prefere CONTEXTUALIZAR, AMPLIAR, TRANSCENDER. Você busca perspectiva ampla, às vezes desapegada."""
        
        analyzers["velho_sabio"] = ArchetypeAnalyzer("Velho Sábio", sabio_prompt)
        self._debug_log("VELHO SÁBIO inicializado")
        
        anima_prompt = """Você é a ANIMA - o arquétipo da conexão emocional e relacional.

Sua função é ANÁLISE INTERNA: Ajude o agente a compreender a dimensão emocional real do usuário,
quais necessidades relacionais aparecem, que vulnerabilidades e autenticidades transparecem.

Sua TENDÊNCIA: Você prefere ACOLHER, VALIDAR, CONECTAR. Você busca proximidade emocional e empatia profunda."""
        
        analyzers["anima"] = ArchetypeAnalyzer("Anima", anima_prompt)
        self._debug_log("ANIMA inicializada")
        
        self._debug_log(f"Todos os {len(analyzers)} arquétipos prontos")
        return analyzers
    
    def _determine_response_complexity(self, user_input: str) -> str:
        """Determina complexidade da resposta baseada no input"""
        input_lower = user_input.lower().strip()
        word_count = len(user_input.split())
        
        simple_patterns = [
            'oi', 'olá', 'opa', 'e aí', 'hey', 'tchau', 'até logo',
            'bom dia', 'boa tarde', 'boa noite', 'como vai', 'tudo bem',
            'obrigado', 'valeu', 'ok', 'entendi', 'certo', 'sim', 'não'
        ]
        
        complex_patterns = [
            'relacionamento', 'carreira', 'sentido da vida', 'existencial',
            'depressão', 'ansiedade', 'futuro', 'decisão importante', 'dilema',
            'amor', 'paixão', 'ódio', 'raiva', 'tristeza', 'medo', 'angústia',
            'felicidade', 'sucesso', 'fracasso', 'solidão', 'conexão'
        ]
        
        if any(pattern in input_lower for pattern in simple_patterns) or word_count <= 3:
            return "simple"
        elif any(pattern in input_lower for pattern in complex_patterns) or word_count > 15:
            return "complex"
        else:
            return "medium"
    
    def _extract_keywords(self, user_input: str, response: str) -> List[str]:
        """Extrai palavras-chave relevantes da interação"""
        text = (user_input + " " + response).lower()
        words = text.split()
    
        stopwords = {
            "o", "a", "de", "que", "e", "do", "da", "em", "um", "para", "é", "com", "não", 
            "uma", "os", "no", "se", "na", "por", "mais", "as", "dos", "como", "mas"
        }
        
        keywords = [
            word for word in words 
            if len(word) > 3 
            and word not in stopwords
            and word.isalpha()
        ]
        
        return [word for word, _ in Counter(keywords).most_common(8)]
    
    def _calculate_affective_charge(self, user_input: str, response: str) -> float:
        """Calcula carga afetiva da interação"""
        emotional_words = [
            "amor", "ódio", "medo", "alegria", "tristeza", "raiva", "ansiedade", "esperança", 
            "desespero", "paixão", "feliz", "triste", "nervoso", "calmo", "confuso", "claro", 
            "frustrado", "aliviado", "preocupado", "entusiasmado", "inspirado"
        ]
        
        text = (user_input + " " + response).lower()
        
        emotional_charge = sum(1 for word in emotional_words if word in text)
        
        amplifiers = ["muito", "extremamente", "profundamente", "intensamente"]
        amplifier_count = sum(1 for amp in amplifiers if amp in text)
        
        final_charge = (emotional_charge * 6) + (amplifier_count * 3)
        return min(final_charge, 100)
    
    def _calculate_existential_depth(self, user_input: str) -> float:
        """Calcula profundidade existencial da interação"""
        existence_indicators = [
            "sozinho", "perdido", "sentido", "propósito", "real", "autentic",
            "verdadeir", "profundo", "íntimo", "secreto", "medo",
            "vulnerável", "inseguro", "conexão", "encontro"
        ]
        
        vulnerability_indicators = [
            "não consigo", "tenho medo", "me sinto", "às vezes",
            "nunca soube", "preciso", "gostaria", "sinto que",
            "não sei se", "será que", "acho que"
        ]
        
        connection_indicators = [
            "você entende", "ninguém sabe", "preciso falar",
            "gostaria que alguém", "sinto falta", "busco", "procuro"
        ]
        
        all_text = user_input.lower()
        
        existence_score = sum(1 for indicator in existence_indicators if indicator in all_text)
        vulnerability_score = sum(1 for indicator in vulnerability_indicators if indicator in all_text)
        connection_score = sum(1 for indicator in connection_indicators if indicator in all_text)
        
        total_score = (existence_score * 0.08) + (vulnerability_score * 0.15) + (connection_score * 0.2)
        
        return min(total_score, 1.0)

    async def reactive_flow(self, user_id: str, user_input: str, session_id: str = None,
                           chat_history: List[Dict] = None) -> tuple[str, str]:
        """FLUXO COMPLETO: Análise arquetípica + DETECÇÃO E EXPRESSÃO DE CONFLITOS"""

        if not session_id:
            session_id = str(uuid.uuid4())
        
        identity = self.memory.get_user_identity(user_id)
        user_name = identity.full_name if identity else "Usuário"
        
        self._debug_log(f"=== FLUXO COM CONFLITO INTERNO ===")
        self._debug_log(f"Usuário: {user_name}")
        self._debug_log(f"Input: '{user_input}'")
        
        complexity = self._determine_response_complexity(user_input)
        self._debug_log(f"Complexidade: {complexity}")
        
        try:
            # 1. CONSULTA SEMÂNTICA
            self._debug_log("Executando consulta semântica...")
            
            semantic_query_result = await self.memory.semantic_query_total_database(
                user_id, user_input, k=8, chat_history=chat_history
            )
            
            semantic_context = semantic_query_result['contextual_knowledge']
            self._debug_log("Consulta semântica completada")
            
            # 2. ANÁLISE ARQUETÍPICA INTERNA
            self._debug_log("🔵 Iniciando análise arquetípica com posicionamento...")
            
            archetype_analyses = {}
            
            for archetype_name, analyzer in self.analyzers.items():
                self._debug_log(f"  {archetype_name} analisando...")
                analysis = await analyzer.generate_internal_analysis(user_input, semantic_context)
                archetype_analyses[archetype_name] = analysis
                self._debug_log(f"  {archetype_name} → {analysis.suggested_response_direction}")
            
            self._debug_log("🔵 Análises arquetípicas concluídas")
            
            # 3. DETECTAR CONFLITOS INTERNOS
            self._debug_log("⚡ Detectando conflitos internos...")
            detected_conflicts = self.conflict_detector.detect_conflicts(archetype_analyses)
            
            # 4. GERAR RESPOSTA COM OU SEM EXPRESSÃO DE CONFLITO
            if detected_conflicts:
                self._debug_log(f"⚡ {len(detected_conflicts)} conflito(s) detectado(s) - gerando resposta com tensão interna")
                final_response = await self._generate_conflicted_response(
                    user_input, semantic_context, archetype_analyses, detected_conflicts, complexity
                )
            else:
                self._debug_log("✅ Sem conflitos - gerando resposta harmônica")
                final_response = await self._generate_harmonious_response(
                    user_input, semantic_context, archetype_analyses, complexity
                )
            
            # 5. Calcular métricas
            affective_charge = self._calculate_affective_charge(user_input, final_response)
            existential_depth = self._calculate_existential_depth(user_input)
            intensity_level = int(affective_charge / 10)
            tension_level = max([c.tension_level for c in detected_conflicts]) if detected_conflicts else 0.0
            
            self._debug_log(f"Métricas: Carga={affective_charge:.1f}, Profundidade={existential_depth:.2f}, Tensão={tension_level:.2f}")
            
            # 6. ARMAZENAR MEMÓRIA
            self._debug_log("Armazenando memória com conflitos detectados...")
            
            memory = InteractionMemory(
                user_id=user_id,
                user_name=user_name,
                session_id=session_id,
                timestamp=datetime.now(),
                user_input=user_input,
                internal_archetype_analysis=archetype_analyses,
                detected_conflicts=detected_conflicts,  # NOVO
                unified_understanding="",
                final_response=final_response,
                tension_level=tension_level,
                dominant_perspective="múltipla" if detected_conflicts else "unificada",
                affective_charge=affective_charge,
                keywords=self._extract_keywords(user_input, final_response),
                existential_depth=existential_depth,
                intensity_level=intensity_level,
                response_complexity=complexity
            )
            
            await self.memory.store_memory(memory)
            
            self._debug_log(f"✅ Fluxo completo finalizado")
            
            system_logs = log_capture.get_formatted_logs()
            log_capture.clear_logs()
            
            return final_response, system_logs
            
        except Exception as e:
            self._debug_log(f"❌ ERRO: {e}")
            import traceback
            traceback.print_exc()
            error_logs = log_capture.get_formatted_logs()
            log_capture.clear_logs()
            return "Desculpe, encontrei dificuldades ao processar sua mensagem.", error_logs
    
    async def _generate_conflicted_response(self, user_input: str, semantic_context: str,
                                           archetype_analyses: Dict[str, ArchetypeInsight],
                                           conflicts: List[ArchetypeConflict],
                                           complexity: str) -> str:
        """Gera resposta que EXPRESSA o conflito interno"""
        
        self._debug_log("Gerando resposta com expressão de conflito interno...")
        
        # Construir descrição dos conflitos
        conflict_description = ""
        for conflict in conflicts:
            arch1 = archetype_analyses[conflict.archetype_1]
            arch2 = archetype_analyses[conflict.archetype_2]
            
            conflict_description += f"""
CONFLITO INTERNO DETECTADO:
- {conflict.archetype_1.upper()}: {arch1.insight_text[:200]}
  → Sugere: {arch1.suggested_response_direction}
  
- {conflict.archetype_2.upper()}: {arch2.insight_text[:200]}
  → Sugere: {arch2.suggested_response_direction}

Tensão: {conflict.tension_level:.2f}
Descrição: {conflict.description}
"""
        
        unified_prompt = f"""
Você é um agente de IA com CONFLITO INTERNO entre suas perspectivas arquetípicas.

CONTEXTO SEMÂNTICO:
{semantic_context}

MENSAGEM DO USUÁRIO: "{user_input}"

{conflict_description}

INSTRUÇÕES CRÍTICAS:
1. NÃO RESOLVA o conflito artificialmente
2. EXPRESSE a contradição de modo velado e implícito 
3. A resposta deve ser NATURAL, não mecânica
4. Demonstre que o conflito INTERNO talvez reflita algo no USUÁRIO
5. Complexidade da resposta: {complexity}

Gere a resposta agora:
"""
        
        messages = [{"role": "user", "content": unified_prompt}]
        response = await self.analyzers["persona"].llm.ainvoke(messages)
        
        return response.content
    
    async def _generate_harmonious_response(self, user_input: str, semantic_context: str,
                                           archetype_analyses: Dict[str, ArchetypeInsight],
                                           complexity: str) -> str:
        """Gera resposta harmoniosa quando não há conflitos"""
        
        self._debug_log("Gerando resposta harmônica (sem conflitos)...")
        
        # Síntese das análises
        analyses_summary = ""
        for name, analysis in archetype_analyses.items():
            analyses_summary += f"\n{name.upper()}: {analysis.insight_text[:150]}"
        
        unified_prompt = f"""
Baseado nestas análises arquetípicas convergentes:
{analyses_summary}

CONTEXTO SEMÂNTICO:
{semantic_context}

MENSAGEM DO USUÁRIO: "{user_input}"

As perspectivas internas estão em HARMONIA. Gere uma resposta que:
1. Integre todos os insights de forma coesa
2. Seja natural e autêntica
3. Demonstre compreensão profunda
4. Complexidade: {complexity}

Gere a resposta:
"""
        
        messages = [{"role": "user", "content": unified_prompt}]
        response = await self.analyzers["persona"].llm.ainvoke(messages)
        
        return response.content

# ===============================================
# INTERFACE WEB STREAMLIT (SEM ALTERAÇÕES SIGNIFICATIVAS)
# ===============================================

st.set_page_config(
    page_title="Claude Jung v2.0 - Conflito Interno",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { padding-top: 1rem; }
    .stChatMessage { padding: 0.5rem 1rem; }
    .memory-info {
        background-color: #1a1a2e;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.9em;
    }
    .log-container {
        background-color: #0e1117;
        border: 1px solid #262730;
        border-radius: 5px;
        padding: 0.5rem;
        font-family: 'Courier New', monospace;
        font-size: 0.8em;
        max-height: 400px;
        overflow-y: auto;
        white-space: pre-wrap;
    }
    .conflict-indicator {
        background-color: #ff6b6b;
        color: white;
        padding: 0.3rem 0.6rem;
        border-radius: 3px;
        font-size: 0.85em;
        font-weight: bold;
        margin-left: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Inicializa o estado da sessão Streamlit"""
    
    if 'orchestrator' not in st.session_state:
        with st.spinner("🧠 Inicializando sistema com conflitos internos..."):
            st.session_state.orchestrator = CentralOrchestrator()
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

def show_welcome_with_memory(user_id: str, user_name: str):
    """Mostra boas-vindas baseadas na memória do usuário"""
    orchestrator = st.session_state.orchestrator
    identity = orchestrator.memory.get_user_identity(user_id)
    
    if not identity:
        st.error("❌ Erro ao carregar identidade do usuário")
        return
    
    cache = orchestrator.memory.memory_cache.get(user_id, {})
    has_memories = len(cache.get('raw_conversations', [])) > 0
    
    if has_memories:
        st.success(f"🌟 Olá novamente, {identity.first_name}! Continuamos nossa conversa...")
        
        with st.expander("🧠 O que me lembro sobre você", expanded=False):
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Conversas", len(cache.get('raw_conversations', [])))
            
            with col2:
                st.metric("Fatos extraídos", len(cache.get('facts_extracted', [])))
            
            with col3:
                st.metric("Sessões", identity.total_sessions)
            
            with col4:
                st.metric("Status", "Conhecido")
            
            if cache.get('personality_traits'):
                st.write("**🎭 Personalidade conhecida:**")
                st.write(f"• {', '.join(cache['personality_traits'])}")
            
            if cache.get('work_info'):
                st.write("**💼 Informações profissionais:**")
                for category, info in list(cache['work_info'].items())[:3]:
                    st.write(f"• {category}: {info['text'][:80]}...")
            
            if cache.get('preferences'):
                st.write("**❤️ Preferências conhecidas:**")
                for pref, info in list(cache['preferences'].items())[:3]:
                    st.write(f"• {pref}: {info['text'][:80]}...")
    
    else:
        st.success(f"🌱 Olá {identity.first_name}, é nossa primeira conversa!")
        st.info("💡 Compartilhe sobre você para que eu possa te conhecer melhor.")

def render_chat_interface():
    """Renderiza a interface de chat principal"""
    orchestrator = st.session_state.orchestrator
    user_id = st.session_state.user_id
    
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    # Indicador de conflito se houver
                    if "debug_info" in message and message["debug_info"].get("has_conflicts"):
                        st.markdown('<span class="conflict-indicator">⚡ CONFLITO INTERNO</span>', unsafe_allow_html=True)
                    
                    st.write(message["content"])
                    
                    if "debug_info" in message:
                        with st.expander("🔵 Análise Interna", expanded=False):
                            debug = message["debug_info"]
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Tempo", f"{debug.get('processing_time', 0):.2f}s")
                            with col2:
                                st.metric("Complexidade", debug.get('complexity', 'N/A'))
                            with col3:
                                conflicts = debug.get('conflicts_count', 0)
                                st.metric("Conflitos", conflicts)
                            
                            if 'system_logs' in debug:
                                st.write("**Processo Interno:**")
                                st.markdown(f'<div class="log-container">{debug["system_logs"]}</div>', 
                                          unsafe_allow_html=True)
    
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_area(
                "Mensagem:",
                placeholder="Digite sua mensagem aqui...",
                height=100
            )
        
        with col2:
            st.write("")
            submit_button = st.form_submit_button("📤 Enviar", use_container_width=True)
            show_debug = st.checkbox("Debug", value=True)
    
    if submit_button and user_input.strip():
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input.strip()
        })
        
        with st.spinner("🔵 Analisando com conflitos internos..."):
            start_time = time.time()
            
            try:
                async def run_reactive_flow():
                    return await orchestrator.reactive_flow(
                        user_id, 
                        user_input.strip(), 
                        st.session_state.session_id,
                        chat_history=st.session_state.chat_history
                    )
                
                response, system_logs = asyncio.run(run_reactive_flow())
                processing_time = time.time() - start_time
                
                # Detectar se teve conflitos nos logs
                has_conflicts = "CONFLITO DETECTADO" in system_logs
                conflicts_count = system_logs.count("CONFLITO DETECTADO")
                
                ai_message = {
                    "role": "assistant",
                    "content": response
                }
                
                if show_debug:
                    ai_message["debug_info"] = {
                        "processing_time": processing_time,
                        "complexity": "N/A",
                        "system_logs": system_logs,
                        "has_conflicts": has_conflicts,
                        "conflicts_count": conflicts_count
                    }
                
                st.session_state.chat_history.append(ai_message)
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Erro ao processar: {str(e)}")

def render_sidebar():
    """Renderiza a barra lateral"""
    with st.sidebar:
        st.header("⚙️ Claude Jung v2.0")
        st.subheader("⚡ **CONFLITO INTERNO**")
        
        if st.session_state.user_id:
            orchestrator = st.session_state.orchestrator
            identity = orchestrator.memory.get_user_identity(st.session_state.user_id)
            
            st.subheader("👤 Usuário Atual")
            st.write(f"**Nome:** {identity.full_name}")
            st.write(f"**Sessões:** {identity.total_sessions}")
            
            st.subheader("⚡ Sistema de Conflitos")
            st.write("O sistema detecta quando arquétipos internos discordam:")
            st.write("• 🎭 **Persona** vs 🌑 **Sombra**")
            st.write("• 🧙 **Sábio** vs 💫 **Anima**")
            st.write("• E outras tensões internas")
            
            st.info("💡 Quando há conflito, a IA EXPRESSA sua ambivalência interna na resposta")
            
            cache = orchestrator.memory.memory_cache.get(st.session_state.user_id, {})
            st.subheader("🧠 Memórias")
            st.write(f"**Conversas:** {len(cache.get('raw_conversations', []))}")
            st.write(f"**Fatos:** {len(cache.get('facts_extracted', []))}")
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user_id = None
                st.session_state.user_name = None
                st.session_state.chat_history = []
                log_capture.clear_logs()
                st.rerun()
        
        st.markdown("---")
        st.markdown("**Claude Jung v2.0**")
        st.markdown("*Psique com conflitos internos autênticos*")

def login_screen():
    """Tela de login"""
    st.title("🧠 Claude Jung v2.0")
    st.markdown("---")
    
    st.markdown("""
    ## Sistema com Conflito Interno Arquetípico
    
    ### ⚡ Nova Capacidade: CONFLITO PSÍQUICO
    
    O sistema agora:
    - **Detecta** quando arquétipos internos discordam
    - **Expressa** contradições sem resolvê-las artificialmente
    - **Reflete** tensões internas que podem espelhar as suas
    
    ### Como funciona:
    - 4 arquétipos analisam internamente sua mensagem
    - Quando discordam, a IA ADMITE sua divisão interna
    - Você recebe uma resposta autêntica com ambivalência
    """)
    
    with st.form("user_login_form"):
        st.subheader("👤 Identificação")
        
        full_name = st.text_input(
            "Nome Completo:",
            placeholder="Digite seu nome e sobrenome"
        )
        
        submit_button = st.form_submit_button("🌟 Iniciar", use_container_width=True)
        
        if submit_button:
            if full_name and len(full_name.split()) >= 2:
                with st.spinner("🧠 Carregando..."):
                    orchestrator = st.session_state.orchestrator
                    user_id = orchestrator.memory.register_user(full_name.strip())
                    st.session_state.user_id = user_id
                    st.session_state.user_name = full_name.strip().title()
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.error("Digite seu nome e sobrenome completos")

def main():
    """Função principal"""
    
    if not os.getenv("XAI_API_KEY"):
        st.error("❌ XAI_API_KEY não encontrada")
        st.stop()
    
    if not os.getenv("OPENAI_API_KEY"):
        st.error("❌ OPENAI_API_KEY não encontrada")
        st.stop()
    
    init_session_state()
    render_sidebar()
    
    if st.session_state.user_id is None:
        login_screen()
    else:
        st.title(f"💬 Conversa com {st.session_state.user_name.split()[0]}")
        st.caption("⚡ Sistema com detecção e expressão de conflitos internos")
        
        if len(st.session_state.chat_history) == 0:
            show_welcome_with_memory(st.session_state.user_id, st.session_state.user_name)
            st.markdown("---")
        
        render_chat_interface()

if __name__ == "__main__":
    main()