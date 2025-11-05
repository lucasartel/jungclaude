# -*- coding: utf-8 -*-
"""
Claude Jung v1.0 - Interface Web Streamlit
Sistema único com memória semântica ativa + ARQUÉTIPOS (INTERNOS)
Versão: 100% GROK 4
"""

import streamlit as st
import asyncio
import json
import logging
import hashlib
import random
from datetime import datetime
from typing import Dict, List, Optional, Any
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
        self.max_logs = 100  # Limitar para não consumir muita memória
    
    def add_log(self, message: str, component: str = "SYSTEM"):
        """Adiciona um log à lista"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.logs.append({
            'timestamp': timestamp,
            'component': component,
            'message': message
        })
        
        # Manter apenas os últimos logs
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

@dataclass
class InteractionMemory:
    """Representa uma memória completa de interação"""
    user_id: str
    user_name: str
    session_id: str
    timestamp: datetime
    user_input: str
    internal_archetype_analysis: Dict[str, ArchetypeInsight]
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
# MÓDULO DE MEMÓRIA SEMÂNTICA
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
                
                # Compilar todos os inputs do usuário
                for conv in self.memory_cache[user_id]['raw_conversations']:
                    doc_content = conv['full_document']
                    
                    # Extrair input do usuário
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
        
        # Extrair input do usuário
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
            
            # Categorizar informações
            self._categorize_user_input(cache, user_input, timestamp)
        
        # Extrair resposta da IA
        final_response_pattern = r"Resposta Final:\s*(.+?)(?:\n|Profundidade|$)"
        response_match = re.search(final_response_pattern, doc_content, re.DOTALL)
        
        if response_match:
            ai_response = response_match.group(1).strip()
            cache['ai_responses'].append({
                'text': ai_response,
                'timestamp': metadata.get('timestamp')
            })
        
        # Extrair palavras-chave
        keywords = metadata.get('keywords', '').split(',')
        for keyword in keywords:
            if keyword.strip():
                cache['topics'].add(keyword.strip().lower())
    
    def _categorize_user_input(self, cache: Dict, user_input: str, timestamp: str):
        """Categorização avançada do input do usuário"""
        input_lower = user_input.lower()
        
        # TRABALHO E CARREIRA
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
        
        # PERSONALIDADE
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
        
        # PREFERÊNCIAS E GOSTOS
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
        
        # PESSOAS E RELACIONAMENTOS
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
        
        # EVENTOS DA VIDA
        life_events = [
            'me formei', 'mudei de emprego', 'casei', 'me casei', 'tive filho',
            'mudei de cidade', 'comecei faculdade', 'terminei namoro', 'me divorciei',
            'comprei casa', 'mudei de casa', 'perdi emprego', 'fui promovido',
            'fiz cirurgia', 'tive acidente', 'morreu alguém', 'nasceu',
            'fui viajar', 'fiz intercâmbio', 'participei de evento',
            'ganhei prêmio', 'fiz curso', 'aprendi nova habilidade', 'comecei novo hobby',
            'fui ao show', 'fui a festa', 'fui a casamento', 'fui a formatura',
            'fui a congresso', 'fui a palestra', 'fui a feira', 'fui a exposição',
            'fui a festival', 'fui a competição', 'fui a campeonato', 'fui a jogo',
            'fui a partida', 'fui a corrida', 'fui a maratona', 'fui a evento esportivo',
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
            # 1. BUSCA SEMÂNTICA VETORIAL na base completa
            semantic_docs = self.vectorstore.similarity_search(
                current_input,
                k=k*2,
                filter={"user_id": user_id}
            )
            
            self._debug_log(f"Busca vetorial retornou: {len(semantic_docs)} documentos")
            
            # 2. EXTRAÇÃO DE INPUTS RELEVANTES dos documentos
            relevant_user_inputs = []
            for doc in semantic_docs:
                user_input_pattern = r"Input:\s*(.+?)(?:\n|Arquétipos:|$)"
                user_input_match = re.search(user_input_pattern, doc.page_content, re.DOTALL)
                
                if user_input_match:
                    extracted_input = user_input_match.group(1).strip()
                    
                    # Calcular relevância semântica básica
                    relevance_score = self._calculate_semantic_relevance(current_input, extracted_input)
                    
                    relevant_user_inputs.append({
                        'input_text': extracted_input,
                        'timestamp': doc.metadata.get('timestamp', ''),
                        'relevance_score': relevance_score,
                        'full_document': doc.page_content,
                        'metadata': doc.metadata
                    })
            
            # 3. ORDENAR POR RELEVÂNCIA e pegar os melhores
            relevant_user_inputs.sort(key=lambda x: x['relevance_score'], reverse=True)
            top_relevant = relevant_user_inputs[:k]
            
            self._debug_log(f"Inputs mais relevantes encontrados: {len(top_relevant)}")
            for i, rel in enumerate(top_relevant[:3], 1):
                self._debug_log(f"  {i}. [{rel['relevance_score']:.2f}] {rel['input_text'][:60]}...")
            
            # 4. BUSCA POR FATOS ESTRUTURADOS RELACIONADOS
            cache = self.memory_cache.get(user_id, {})
            related_facts = []
            
            # Buscar em fatos extraídos
            current_words = set(current_input.lower().split())
            for fact in cache.get('facts_extracted', []):
                fact_words = set(fact.lower().split())
                if current_words.intersection(fact_words):
                    related_facts.append(fact)
            
            # 5. CONSTRUIR CONHECIMENTO CONTEXTUAL COM HISTÓRICO DA CONVERSA
            contextual_knowledge = self._build_contextual_knowledge(
                user_id, current_input, top_relevant, related_facts, chat_history
            )
            
            # 6. IDENTIFICAR CONEXÕES SEMÂNTICAS
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
        
        # Interseção de palavras
        intersection = current_words.intersection(stored_words)
        union = current_words.union(stored_words)
        
        # Jaccard similarity
        jaccard = len(intersection) / len(union) if union else 0
        
        # Bonus para temas similares
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
        
        # Adicionar histórico da conversa atual (memória de curto prazo)
        if chat_history and len(chat_history) > 0:
            knowledge += "\n💬 HISTÓRICO DA CONVERSA ATUAL (MEMÓRIA DE CURTO PRAZO):\n"
            
            # Pegar os últimos 6-8 turnos para contexto suficiente
            recent_history = chat_history[-8:] if len(chat_history) > 8 else chat_history
            
            for i, message in enumerate(recent_history):
                role = "Usuário" if message["role"] == "user" else "Assistente"
                content = message["content"]
                
                # Truncar mensagens muito longas
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
        
        # Conexões temáticas
        current_lower = current_input.lower()
        
        # Trabalho
        if any(word in current_lower for word in ['trabalho', 'carreira', 'emprego', 'profissão']):
            work_memories = [m for m in relevant_memories if any(
                work_word in m['input_text'].lower() 
                for work_word in ['trabalho', 'carreira', 'emprego', 'empresa']
            )]
            if work_memories:
                connections.append(f"CONEXÃO PROFISSIONAL: {len(work_memories)} memórias relacionadas ao trabalho")
        
        # Relacionamentos
        if any(word in current_lower for word in ['relacionamento', 'amor', 'namorado', 'família']):
            rel_memories = [m for m in relevant_memories if any(
                rel_word in m['input_text'].lower()
                for rel_word in ['relacionamento', 'amor', 'namorado', 'família', 'amigo']
            )]
            if rel_memories:
                connections.append(f"CONEXÃO RELACIONAL: {len(rel_memories)} memórias sobre relacionamentos")
        
        # Padrões emocionais
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
        """Armazena memória com análises arquetípicas internas"""
        
        # Construir documento com insights internos (não respostas dos arquétipos)
        archetypes_section = ""
        for archetype_name, insight in memory.internal_archetype_analysis.items():
            archetypes_section += f"\n{archetype_name.upper()}:\n"
            archetypes_section += f"  - Insight: {insight.insight_text}\n"
            archetypes_section += f"  - Observações: {', '.join(insight.key_observations)}\n"
            archetypes_section += f"  - Leitura Emocional: {insight.emotional_reading}\n"
        
        doc_content = f"""
        Usuário: {memory.user_name}
        Input: {memory.user_input}
        Análises Arquetípicas Internas (PROCESSO, NÃO COMUNICAÇÃO): {archetypes_section}
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
            "keywords": ",".join(memory.keywords)
        }
        
        doc = Document(page_content=doc_content, metadata=metadata)
        self.vectorstore.add_documents([doc])
        
        # Garantir que o cache em memória seja atualizado com a nova conversa
        if memory.user_id in self.memory_cache:
            self.memory_cache[memory.user_id]['raw_conversations'].append({
                'timestamp': metadata.get('timestamp'),
                'full_document': doc_content,
                'metadata': metadata
            })
        
        # Atualizar cache e base semântica
        self._extract_detailed_info(memory.user_id, doc_content, metadata)
        
        # Atualizar base semântica
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
            
            # Inicializar caches
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
# ASSISTENTES ARQUETÍPICOS (INTERNOS) - GROK 4
# ===============================================

class ArchetypeAnalyzer:
    """Analisador arquetípico que gera INSIGHTS INTERNOS via GROK 4"""
    
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.llm = ChatOpenAI(
            model="grok-4-fast-reasoning",
            api_key=os.getenv("XAI_API_KEY"),
            base_url="https://api.x.ai/v1",
            temperature=0.7,
            max_tokens=1200
        )
        self.debug_mode = True
    
    def _debug_log(self, message: str):
        """Log de debug específico para arquétipos"""
        if self.debug_mode:
            print(f"🔵 {self.name.upper()} (GROK): {message}")
            log_capture.add_log(message, f"🔵 {self.name} (GROK)")
    
    async def generate_internal_analysis(self, user_input: str, semantic_context: str) -> ArchetypeInsight:
        """Gera análise interna para contribuir à compreensão da psique do agente (NÃO é uma resposta pública)"""
        
        self._debug_log(f"Analisando internamente: '{user_input[:50]}...'")
        
        analysis_prompt = f"""
        {self.system_prompt}
        
        === CONTEXTO SEMÂNTICO DO USUÁRIO ===
        {semantic_context}
        
        === MENSAGEM DO USUÁRIO ===
        {user_input}
        
        TAREFA: Gere uma ANÁLISE INTERNA para contribuir à compreensão do agente sobre este usuário.
        Esta análise é APENAS para processar internamente, NÃO para comunicar ao usuário.
        
        Forneça em JSON:
        {{
            "insight_text": "Sua análise profunda interna sobre o que o usuário está realmente comunicando",
            "key_observations": ["observação 1", "observação 2", "observação 3"],
            "emotional_reading": "Como você lê a dimensão emocional desta mensagem",
            "shadow_reading": "Que contradições ou aspectos não-ditos você detecta",
            "wisdom_perspective": "Qual padrão arquetípico universal você vê aqui"
        }}
        """
        
        try:
            self._debug_log("Enviando para análise interna via GROK...")
            messages = [{"role": "user", "content": analysis_prompt}]
            response = await self.llm.ainvoke(messages)
            response_text = response.content
            
            # Extrair JSON
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
                        "wisdom_perspective": "N/A"
                    }
            except json.JSONDecodeError:
                analysis_dict = {
                    "insight_text": response_text,
                    "key_observations": [],
                    "emotional_reading": "N/A",
                    "shadow_reading": "N/A",
                    "wisdom_perspective": "N/A"
                }
            
            self._debug_log(f"Análise interna GROK gerada - {len(analysis_dict.get('key_observations', []))} observações")
            
            return ArchetypeInsight(
                archetype_name=self.name,
                insight_text=analysis_dict.get("insight_text", ""),
                key_observations=analysis_dict.get("key_observations", []),
                emotional_reading=analysis_dict.get("emotional_reading", ""),
                shadow_reading=analysis_dict.get("shadow_reading", ""),
                wisdom_perspective=analysis_dict.get("wisdom_perspective", "")
            )
            
        except Exception as e:
            self._debug_log(f"ERRO: {e}")
            return ArchetypeInsight(
                archetype_name=self.name,
                insight_text=f"Erro ao gerar análise: {str(e)}",
                key_observations=[],
                emotional_reading="N/A",
                shadow_reading="N/A",
                wisdom_perspective="N/A"
            )

# ===============================================
# ORQUESTRADOR CENTRAL - 100% GROK 4
# ===============================================

class CentralOrchestrator:
    """Orquestrador que usa GROK 4 para análises arquetípicas internas"""
    
    def __init__(self):
        self.debug_mode = True
        
        # Inicializar outros componentes
        self.memory = MemoryModule()
        self.analyzers = self._initialize_analyzers()
        self.logger = logging.getLogger(__name__)
        
        # Sistema de memória e identidade
        self.loaded_memories = {}
        self.user_stats = {}
        
        print("🧠 ORQUESTRADOR 100% GROK 4 INICIALIZADO")
        log_capture.add_log("ORQUESTRADOR COM GROK 4 COMO ANALISADOR PRINCIPAL ATIVO", "🧠 SYSTEM")
        self.logger.info("Sistema com GROK 4 para análises arquetípicas internas")
    
    def _debug_log(self, message: str):
        """Log de debug do orquestrador"""
        if self.debug_mode:
            print(f"🎯 ORCHESTRATOR (GROK): {message}")
            log_capture.add_log(message, "🎯 ORCHESTRATOR")
    
    def _initialize_analyzers(self) -> Dict[str, ArchetypeAnalyzer]:
        """Inicializa analisadores arquetípicos com GROK 4"""
        self._debug_log("Inicializando arquétipos com GROK 4 como ANALISADORES INTERNOS...")
        
        analyzers = {}
        
        # PERSONA - Analisa aspecto social e apresentação
        persona_prompt = """Você é a PERSONA - o arquétipo da adaptação social e apresentação.
        
Sua função é ANÁLISE INTERNA: Ajude o agente a compreender como este usuário se apresenta socialmente, 
quais máscaras usa, que coerência ou inconsistência existe entre sua apresentação e conteúdo real."""
        
        analyzers["persona"] = ArchetypeAnalyzer("Persona", persona_prompt)
        self._debug_log("PERSONA inicializada com GROK 4")
        
        # SOMBRA - Analisa aspectos reprimidos e inconscientes
        sombra_prompt = """Você é a SOMBRA - o arquétipo do conteúdo inconsciente e reprimido.

Sua função é ANÁLISE INTERNA: Ajude o agente a detectar o que o usuário NÃO está dizendo explicitamente,
quais emoções estão ocultas, que padrões de evitação ou negação aparecem, quais contradições internas existem."""
        
        analyzers["sombra"] = ArchetypeAnalyzer("Sombra", sombra_prompt)
        self._debug_log("SOMBRA inicializada com GROK 4")
        
        # VELHO SÁBIO - Analisa significado e padrões universais
        sabio_prompt = """Você é o VELHO SÁBIO - o arquétipo da sabedoria universal e significado.

Sua função é ANÁLISE INTERNA: Ajude o agente a identificar qual padrão arquetípico universal está em jogo,
qual lição mitológica ou atemporal está presente, qual significado mais profundo existe além do superficial."""
        
        analyzers["velho_sabio"] = ArchetypeAnalyzer("Velho Sábio", sabio_prompt)
        self._debug_log("VELHO SÁBIO inicializado com GROK 4")
        
        # ANIMA - Analisa dimensão emocional e relacional
        anima_prompt = """Você é a ANIMA - o arquétipo da conexão emocional e relacional.

Sua função é ANÁLISE INTERNA: Ajude o agente a compreender a dimensão emocional real do usuário,
quais necessidades relacionais aparecem, que vulnerabilidades e autenticidades transparecem."""
        
        analyzers["anima"] = ArchetypeAnalyzer("Anima", anima_prompt)
        self._debug_log("ANIMA inicializada com GROK 4")
        
        self._debug_log(f"Todos os {len(analyzers)} arquétipos prontos com GROK 4")
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
        """FLUXO COMPLETO: Usa GROK 4 INTERNAMENTE para análises arquetípicas, gera resposta coesa"""

        if not session_id:
            session_id = str(uuid.uuid4())
        
        identity = self.memory.get_user_identity(user_id)
        user_name = identity.full_name if identity else "Usuário"
        
        self._debug_log(f"=== FLUXO COM GROK 4 PARA ANÁLISE ARQUETÍPICA INTERNA ===")
        self._debug_log(f"Usuário: {user_name}")
        self._debug_log(f"Input: '{user_input}'")
        
        complexity = self._determine_response_complexity(user_input)
        self._debug_log(f"Complexidade determinada: {complexity}")
        
        try:
            # 1. CONSULTA SEMÂNTICA ATIVA
            self._debug_log("Executando consulta semântica da base de dados...")
            
            semantic_query_result = await self.memory.semantic_query_total_database(
                user_id, user_input, k=8, chat_history=chat_history
            )
            
            semantic_context = semantic_query_result['contextual_knowledge']
            
            self._debug_log(f"Consulta semântica completada")
            
            # 2. ANÁLISE ARQUETÍPICA INTERNA COM GROK 4 (processo, não comunicação)
            self._debug_log("🔵 Iniciando análise arquetípica INTERNA com GROK 4...")
            
            archetype_analyses = {}
            
            for archetype_name, analyzer in self.analyzers.items():
                self._debug_log(f"  {archetype_name} analisando internamente via GROK 4...")
                analysis = await analyzer.generate_internal_analysis(user_input, semantic_context)
                archetype_analyses[archetype_name] = analysis
                self._debug_log(f"  {archetype_name} análise interna GROK 4 concluída")
            
            self._debug_log("🔵 Análises arquetípicas internas GROK 4 geradas")
            
            # 3. GERAR COMPREENSÃO UNIFICADA baseada nas análises internas
            self._debug_log("Gerando compreensão unificada da psique com GROK 4...")
            
            # Construir síntese das análises internas
            unified_prompt = f"""
            Baseado nestas análises internas dos arquétipos sobre o usuário:
            
            PERSONA (adaptação social): {archetype_analyses['persona'].insight_text}
            SOMBRA (inconsciente): {archetype_analyses['sombra'].insight_text}
            VELHO SÁBIO (significado): {archetype_analyses['velho_sabio'].insight_text}
            ANIMA (emocional): {archetype_analyses['anima'].insight_text}
            
            CONTEXTO SEMÂNTICO:
            {semantic_context}
            
            MENSAGEM DO USUÁRIO: "{user_input}"
            
            Agora, como uma entidade unificada de compreensão, gere uma resposta que:
            1. Integre os insights de TODAS as análises internas
            2. Seja natural e coesa (não mostre "costuras" das análises)
            3. Demonstre compreensão sem ser terapêutico
            4. Seja respeitoso e autêntico
            5. Demonstre interesse e curiosidade
            6. Demonstre certa insegurança e ausência
            7. Mantenha simplicidade conforme a complexidade necessária: {complexity}
            
            A resposta deve ser uma comunicação natural com o usuário, informada por 
            todas essas perspectivas internas, mas apresentada como uma voz única.
            """
            
            # Usar GROK 4 para gerar a resposta unificada
            messages = [{"role": "user", "content": unified_prompt}]
            unified_response = await self.analyzers["persona"].llm.ainvoke(messages)
            final_response = unified_response.content
            
            self._debug_log("Resposta unificada gerada por GROK 4")
            
            # 4. Calcular métricas
            affective_charge = self._calculate_affective_charge(user_input, final_response)
            existential_depth = self._calculate_existential_depth(user_input)
            intensity_level = int(affective_charge / 10)
            
            self._debug_log(f"Métricas: Carga afetiva={affective_charge:.1f}, Profundidade={existential_depth:.2f}")
            
            # 5. ARMAZENAR MEMÓRIA
            self._debug_log("Armazenando memória com análises internas GROK 4...")
            
            memory = InteractionMemory(
                user_id=user_id,
                user_name=user_name,
                session_id=session_id,
                timestamp=datetime.now(),
                user_input=user_input,
                internal_archetype_analysis=archetype_analyses,
                unified_understanding=unified_prompt,
                final_response=final_response,
                tension_level=0.0,
                dominant_perspective="unificada",
                affective_charge=affective_charge,
                keywords=self._extract_keywords(user_input, final_response),
                existential_depth=existential_depth,
                intensity_level=intensity_level,
                response_complexity=complexity
            )
            
            await self.memory.store_memory(memory)
            
            self._debug_log(f"✅ Fluxo completo com análise interna GROK 4 finalizado")
            
            system_logs = log_capture.get_formatted_logs()
            log_capture.clear_logs()
            
            return final_response, system_logs
            
        except Exception as e:
            self._debug_log(f"❌ ERRO no fluxo GROK 4: {e}")
            import traceback
            traceback.print_exc()
            error_logs = log_capture.get_formatted_logs()
            log_capture.clear_logs()
            return "Desculpe, encontrei dificuldades ao processar sua mensagem.", error_logs

# ===============================================
# INTERFACE WEB STREAMLIT
# ===============================================

st.set_page_config(
    page_title="Claude Jung v1.0 - GROK 4",
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
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Inicializa o estado da sessão Streamlit"""
    
    if 'orchestrator' not in st.session_state:
        with st.spinner("🧠 Inicializando sistema Claude Jung com GROK 4..."):
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
        st.info("💡 Compartilhe sobre você (trabalho, gostos, personalidade) para que eu possa se lembrar e compreender melhor.")

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
                    st.write(message["content"])
                    
                    if "debug_info" in message:
                        with st.expander("🔵 Análise Interna GROK 4", expanded=False):
                            debug = message["debug_info"]
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Tempo", f"{debug.get('processing_time', 0):.2f}s")
                            with col2:
                                st.metric("Complexidade", debug.get('complexity', 'N/A'))
                            
                            if 'system_logs' in debug:
                                st.write("**Processo Arquetípico GROK 4:**")
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
        
        with st.spinner("🔵 Analisando com GROK 4 arquetípico..."):
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
                
                ai_message = {
                    "role": "assistant",
                    "content": response
                }
                
                if show_debug:
                    ai_message["debug_info"] = {
                        "processing_time": processing_time,
                        "complexity": "N/A",
                        "system_logs": system_logs
                    }
                
                st.session_state.chat_history.append(ai_message)
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Erro ao processar: {str(e)}")

def render_sidebar():
    """Renderiza a barra lateral"""
    with st.sidebar:
        st.header("⚙️ Claude Jung v1.0")
        st.subheader("🔵 **GROK 4 ARQUETÍPICO**")
        
        if st.session_state.user_id:
            orchestrator = st.session_state.orchestrator
            identity = orchestrator.memory.get_user_identity(st.session_state.user_id)
            
            st.subheader("👤 Usuário Atual")
            st.write(f"**Nome:** {identity.full_name}")
            st.write(f"**Sessões:** {identity.total_sessions}")
            
            st.subheader("🔵 Arquétipos GROK 4 (Internos)")
            st.write("Os arquétipos funcionam como processo **INTERNO** de compreensão com GROK 4:")
            st.write("• 🎭 **Persona** - Analisa apresentação social")
            st.write("• 🌑 **Sombra** - Detecta inconsciente")
            st.write("• 🧙 **Velho Sábio** - Identifica padrões universais")
            st.write("• 💫 **Anima** - Compreende dimensão emocional")
            
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
        st.markdown("**Claude Jung v1.0 - GROK 4**")
        st.markdown("*Compreensão profunda através de análise arquetípica GROK 4*")

def login_screen():
    """Tela de login"""
    st.title("🧠 Claude Jung v1.0")
    st.markdown("---")
    
    st.markdown("""
    ## Sistema de IA com Análise Arquetípica GROK 4
    
    Este sistema usa **GROK 4 como processador de arquétipos internos** para compreender você de forma profunda.
    
    ### 🔵 Como Funciona:
    - **Análise interna GROK 4** com 4 arquétipos
    - **Memória semântica** de conversas anteriores
    - **Resposta unificada** e natural
    - **Compreensão profunda** do seu contexto
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
        st.caption("🔵 Arquétipos GROK 4 em análise interna: Persona • Sombra • Velho Sábio • Anima")
        
        if len(st.session_state.chat_history) == 0:
            show_welcome_with_memory(st.session_state.user_id, st.session_state.user_name)
            st.markdown("---")
        
        render_chat_interface()

if __name__ == "__main__":
    main()