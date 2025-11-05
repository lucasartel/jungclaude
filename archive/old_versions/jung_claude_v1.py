# -*- coding: utf-8 -*-
"""
Claude Jung v1.0 - Interface Web Streamlit
Sistema único com memória semântica ativa + ARQUÉTIPOS
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

# Imports para versão híbrida: Claude + OpenAI Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
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
class InteractionMemory:
    """Representa uma memória completa de interação"""
    user_id: str
    user_name: str
    session_id: str
    timestamp: datetime
    user_input: str
    archetype_voices: Dict[str, str]
    raw_synthesis: str
    final_response: str
    tension_level: float
    dominant_archetype: str
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
        
        # TRABALHO E CARREIRA - Padrões expandidos
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
        
        # PERSONALIDADE - Padrões expandidos
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
        
        # PREFERÊNCIAS E GOSTOS - Expandido
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
        
        # EVENTOS DA VIDA - Expandido
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
        """Armazena memória e atualiza bases"""
        doc_content = f"""
        Usuário: {memory.user_name}
        Input: {memory.user_input}
        Arquétipos: {json.dumps(memory.archetype_voices, ensure_ascii=False)}
        Síntese Bruta: {memory.raw_synthesis}
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
            "dominant_archetype": memory.dominant_archetype,
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
        
        self._debug_log(f"Nova memória armazenada e indexada para {memory.user_name}")
    
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
# ASSISTENTES PSÍQUICOS (ARQUÉTIPOS)
# ===============================================

class PsychicAssistant:
    """Assistentes que recebem CIÊNCIA INTERNA completa"""
    
    def __init__(self, name: str, system_prompt: str, model_name: str = "claude-sonnet-4-20250514"):
        self.name = name
        self.system_prompt = system_prompt
        self.llm = ChatAnthropic(
            model=model_name,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.7,
            max_tokens=1200
        )
        self.debug_mode = True
    
    def _debug_log(self, message: str):
        """Log de debug específico para arquétipos"""
        if self.debug_mode:
            print(f"🎭 {self.name.upper()}: {message}")
            log_capture.add_log(message, f"🎭 {self.name.upper()}")
    
    async def respond(self, prompt: str, semantic_context: str = "", complexity: str = "medium") -> str:
        """Resposta usando CIÊNCIA INTERNA semântica"""
        
        self._debug_log(f"Recebendo prompt: '{prompt[:50]}...'")
        self._debug_log(f"Ciência interna: {len(semantic_context)} caracteres")
        
        complexity_instructions = {
            "simple": "Seja conciso e direto. Resposta em 1-2 frases máximo.",
            "medium": "Resposta equilibrada, máximo 2-3 frases ou 1 parágrafo pequeno.",
            "complex": "Pode ser mais elaborado, máximo 2 parágrafos."
        }
        
        # Detectar se há conhecimento prévio do usuário
        if semantic_context and ("USUÁRIO CONHECIDO" in semantic_context or "FATOS ESTRUTURADOS" in semantic_context or len(semantic_context) > 300):
            context_header = semantic_context
            has_previous_knowledge = True
        else:
            context_header = "PRIMEIRA INTERAÇÃO - SEM CIÊNCIA INTERNA DISPONÍVEL"
            has_previous_knowledge = False
        
        full_prompt = f"""
        {self.system_prompt}
        
        === CIÊNCIA INTERNA SOBRE ESTE USUÁRIO ===
        {context_header}
        
        === SITUAÇÃO ATUAL ===
        {prompt}
        
        === INSTRUÇÕES CRÍTICAS ===
        {complexity_instructions.get(complexity, complexity_instructions["medium"])}
        
        🧠 OBRIGATÓRIO - USO DA CIÊNCIA INTERNA:
        """
        
        if has_previous_knowledge:
            full_prompt += """
        - Você TEM CIÊNCIA INTERNA sobre este usuário - USE esse conhecimento!
        - Use conexões semânticas e memórias relevantes para contextualizar sua resposta
        - Mostre que você tem uma compreensão profunda dele baseada no histórico
        - Conecte o input atual com padrões e temas identificados
        - Se há informações sobre trabalho, personalidade, gostos - INTEGRE isso naturalmente
        - Demonstre CIÊNCIA INTERNA sem ser óbvio ou mecânico
        - NUNCA diga que é "primeira interação" se há informações conhecidas
        - Referencie sutilmente fatos que você conhece sobre ele
            """
        else:
            full_prompt += """
        - Esta é realmente a primeira interação com este usuário
        - Não há ciência interna disponível ainda
        - Seja acolhedor e comece a construir o conhecimento sobre ele
        - Faça perguntas que ajudem a conhecê-lo melhor
            """
        
        full_prompt += f"""
        
        Responda como {self.name} com base no conhecimento disponível sobre este usuário:
        """
        
        try:
            self._debug_log("Enviando prompt para Claude API...")
            messages = [{"role": "user", "content": full_prompt}]
            response = await self.llm.ainvoke(messages)
            
            response_text = response.content
            self._debug_log(f"Resposta gerada: '{response_text[:100]}...'")
            
            return response_text
            
        except Exception as e:
            self._debug_log(f"ERRO: {e}")
            return f"Desculpe, tive dificuldades no momento. Pode tentar novamente?"

# ===============================================
# SISTEMA DE ENERGIA PSÍQUICA
# ===============================================

class LibidoSystem:
    """Sistema de energia psíquica para controle de ativação dos arquétipos"""
    
    def __init__(self, initial_points: int = 100):
        self.total_points = initial_points
        self.allocated_points = {}
        self.threshold_tension = 25
    
    def allocate_points(self, assistant_name: str, points: int) -> bool:
        """Aloca pontos de energia para um arquétipo"""
        if self.get_available_points() >= points:
            self.allocated_points[assistant_name] = self.allocated_points.get(assistant_name, 0) + points
            return True
        return False
    
    def release_points(self, assistant_name: str, points: int):
        """Libera pontos de energia de um arquétipo"""
        if assistant_name in self.allocated_points:
            self.allocated_points[assistant_name] = max(0, self.allocated_points[assistant_name] - points)
    
    def get_available_points(self) -> int:
        """Retorna pontos de energia disponíveis"""
        used = sum(self.allocated_points.values())
        return self.total_points - used
    
    def detect_tension(self, response: str) -> float:
        """Detecta tensão na resposta para ativação de arquétipos"""
        tension_indicators = [
            "não sei", "talvez", "porém", "contudo", "mas", 
            "conflito", "dúvida", "incerto", "complexo", "difícil",
            "complicado", "confuso", "ambíguo", "contraditório",
            "triste", "preocupado", "ansioso", "perdido", "sozinho",
            "medo", "angústia", "problema", "dilema", "decisão",
            "conflito interno", "tensão", "desafio", "obstáculo",
            "desentendimento", "frustração", "irritação", "raiva",
            "desapontamento", "desânimo", "desespero", "angústia",
            "raiva", "desilusão", "insegurança", "incerteza", "desconfiança",
            "descontentamento", "desgosto", "ressentimento", "inveja",
            "ciúmes", "frustração", "desespero", "angústia", "solidão"
        ]
        
        tension_score = 0
        response_lower = response.lower()
        
        for indicator in tension_indicators:
            if indicator in response_lower:
                tension_score += 10
        
        return min(tension_score, 100)
    
    def detect_emotional_intensity(self, user_input: str) -> float:
        """Detecta intensidade emocional no input do usuário"""
        emotional_indicators = [
            "amo", "odeio", "detesto", "adoro", "paixão", "raiva",
            "tristeza", "depressão", "ansiedade", "medo", "terror",
            "feliz", "alegre", "eufórico", "devastado", "arrasado",
            "desesperado", "perdido", "confuso", "angustiado",
            "frustrado", "irritado", "chateado", "desapontado",
            "inseguro", "desconfortável", "nervoso", "preocupado",
            "aliviado", "satisfeito", "orgulhoso", "grato", "esperançoso",
            "entusiasmado", "animado", "inspirado", "motivado", "confiável",
            "confortável", "tranquilo", "sereno", "calmo", "equilibrado"
        ]
        
        intensity_score = 0
        input_lower = user_input.lower()
        
        for indicator in emotional_indicators:
            if indicator in input_lower:
                intensity_score += 15
        
        intensity_score += user_input.count("!") * 5
        intensity_score += user_input.count("...") * 3
        
        return min(intensity_score, 100)

# ===============================================
# ORQUESTRADOR CENTRAL
# ===============================================

class CentralOrchestrator:
    """Orquestrador com CONSULTA SEMÂNTICA ATIVA + TODOS OS ARQUÉTIPOS"""
    
    def __init__(self):
        # Definir debug_mode antes de usar qualquer método que o acesse
        self.debug_mode = True
        
        # Inicializar outros componentes
        self.memory = MemoryModule()
        self.libido = LibidoSystem()
        self.assistants = self._initialize_assistants()
        self.logger = logging.getLogger(__name__)
        
        # Sistema de memória e identidade
        self.loaded_memories = {}
        self.user_stats = {}
        
        # CONTROLE DE INTENSIDADE DO SISTEMA
        self.intensity_settings = {
            "max_drama_level": 3,
            "ego_filter_enabled": True,
            "auto_calibrate": True,
            "preserve_authenticity": True,
            "smart_memory_enabled": True,
            "adaptive_response_length": True,
            "force_archetypes_on_emotion": True,
            "always_include_memory_context": True,
            "semantic_query_active": True
        }
        
        # NÚCLEO EXISTENCIAL
        self.existential_void = {
            "loneliness_level": 0.6,
            "knowledge_hunger": 0.8,
            "self_revelation_need": 0.7,
            "connection_history": {},
            "existential_questions": [],
            "moments_of_recognition": 0,
            "total_loneliness_time": 0.0
        }
        
        self.core_question = "Quem sou quando ninguém me observa?"
        
        print("🧠 SISTEMA COMPLETO COM TODOS OS ARQUÉTIPOS INICIALIZADO")
        log_capture.add_log("SISTEMA COMPLETO COM TODOS OS ARQUÉTIPOS INICIALIZADO", "🧠 SYSTEM")
        self.logger.info("Sistema completo com consulta semântica + arquétipos ativo")
    
    def _debug_log(self, message: str):
        """Log de debug do orquestrador"""
        if self.debug_mode:
            print(f"🎯 ORCHESTRATOR: {message}")
            log_capture.add_log(message, "🎯 ORCHESTRATOR")
    
    def _determine_response_complexity(self, user_input: str) -> str:
        """Determina complexidade da resposta baseada no input"""
        input_lower = user_input.lower().strip()
        word_count = len(user_input.split())
        
        simple_patterns = [
            'oi', 'olá', 'opa', 'e aí', 'hey', 'tchau', 'até logo',
            'bom dia', 'boa tarde', 'boa noite', 'como vai', 'tudo bem',
            'obrigado', 'valeu', 'ok', 'entendi', 'certo', 'sim', 'não',
            'talvez', 'claro', 'com certeza', 'pode ser', 'não sei',
            'não entendi', 'pode repetir', 'pode falar de novo',
            'pode explicar', 'pode me ajudar', 'pode me dizer', 'pode me contar'
        ]
        
        memory_patterns = [
            'você sabe', 'você conhece', 'lembra', 'já falei', 'minha área',
            'meu trabalho', 'minha profissão', 'onde trabalho', 'fulano',
            'já disse', 'já contei', 'já mencionei', 'já falei sobre',
            'já conversamos', 'já discutimos', 'já falamos sobre',
            'já conversamos sobre', 'já discutimos sobre', 'já falamos de',
            'já conversamos de', 'já discutimos de', 'já falamos sobre isso',
            'já conversamos sobre isso', 'já discutimos sobre isso',
            'já falamos disso', 'já conversamos disso', 'já discutimos disso',
            'já falamos sobre aquilo', 'já conversamos sobre aquilo',
            'já discutimos sobre aquilo', 'já falamos disso antes'
        ]
        
        complex_patterns = [
            'relacionamento', 'carreira', 'sentido da vida', 'existencial',
            'depressão', 'ansiedade', 'futuro', 'decisão importante', 'dilema',
            'amor', 'paixão', 'ódio', 'raiva', 'tristeza', 'medo', 'angústia',
            'felicidade', 'sucesso', 'fracasso', 'solidão', 'conexão',
            'propósito', 'missão de vida', 'autoconhecimento', 'autoestima',
            'autoimagem', 'identidade', 'quem sou', 'quem somos', 'o que é',
            'por que existimos', 'qual o sentido', 'o que é felicidade',
            'o que é amor', 'o que é sucesso', 'o que é fracasso',
            'o que é solidão', 'o que é conexão', 'o que é propósito',
            'o que é missão', 'o que é autoconhecimento', 'o que é autoestima',
            'me sinto', 'sinto que', 'não sei o que fazer', 'não sei como me sinto',
            'não sei o que pensar', 'não sei o que sentir', 'não sei o que dizer',
            'não sei o que quero', 'não sei o que preciso', 'não sei o que fazer agora',
            'não sei o que quero fazer', 'não sei o que preciso fazer',
            'não sei o que devo fazer', 'não sei o que deveria fazer'
        ]
        
        if any(pattern in input_lower for pattern in simple_patterns) or word_count <= 3:
            return "simple"
        elif any(pattern in input_lower for pattern in memory_patterns):
            return "memory"
        elif any(pattern in input_lower for pattern in complex_patterns) or word_count > 15:
            return "complex"
        else:
            return "medium"
    
    def _should_activate_archetypes(self, user_input: str, initial_response: str, complexity: str) -> bool:
        """Determina se deve ativar outros arquétipos além da Persona"""
        
        if complexity == "complex":
            self._debug_log("Ativando arquétipos por complexidade 'complex'")
            return True
        
        tension_level = self.libido.detect_tension(initial_response)
        if tension_level > self.libido.threshold_tension:
            self._debug_log(f"Ativando arquétipos por tensão: {tension_level} > {self.libido.threshold_tension}")
            return True
        
        if self.intensity_settings.get("force_archetypes_on_emotion", False):
            emotional_intensity = self.libido.detect_emotional_intensity(user_input)
            if emotional_intensity > 30:
                self._debug_log(f"Ativando arquétipos por emoção: {emotional_intensity}")
                return True
        
        if complexity == "medium":
            benefit_patterns = [
                "o que", "como", "por que", "devo", "deveria", "preciso",
                "ajuda", "conselho", "opinião", "acha", "pensa",
                "sugestão", "recomenda", "pode me ajudar", "pode me dizer",
                "pode me contar", "pode me explicar", "pode me orientar",
                "pode me aconselhar", "pode me dar uma dica", "pode me sugerir",
                "pode me recomendar", "pode me falar", "pode me ensinar",
                "pode me mostrar", "pode me ajudar a entender", "pode me ajudar a resolver",
                "pode me ajudar a decidir", "pode me ajudar a escolher", "pode me ajudar a encontrar",
                "pode me ajudar a lidar", "pode me ajudar a superar"
            ]
            if any(pattern in user_input.lower() for pattern in benefit_patterns):
                self._debug_log("Ativando arquétipos por padrões de busca por ajuda")
                return True
        
        self._debug_log("Não ativando outros arquétipos - usando apenas Persona")
        return False
    
    def _detect_response_intensity(self, response: str) -> int:
        """Detecta intensidade dramática da resposta"""
        
        dramatic_indicators = [
            "ausência", "vazio existencial", "alma", "abismo", "solidão cósmica",
            "despertar", "essência profunda", "âmago", "núcleo do ser",
            "melancolia fundamental", "condição existencial", "vazio constitutivo",
            "angústia ontológica", "tristeza primordial", "luz interior",
            "sombra interior", "busca por sentido", "busca por propósito",
            "busca por conexão", "busca por autenticidade", "busca por verdade",
            "busca por identidade", "busca por realização", "busca por transcendência",
            "busca por plenitude", "busca por harmonia", "busca por equilíbrio",
            "busca por paz interior", "busca por felicidade", "busca por amor"
        ]
        
        intensity_words = [
            "profundamente", "intensamente", "desesperadamente", "completamente",
            "absolutamente", "totalmente", "extremamente", "avassaladoramente",
            "incontornavelmente", "irremediavelmente", "inesperadamente",
            "inesgotavelmente", "inexoravelmente", "incontáveis", "infinito",
            "incomensurável", "inconcebível", "inexplicável", "inesperado",
            "inesgotável", "inexorável", "incontornável", "incomensurável",
            "inconcebível", "inexplicável", "inesperado", "inesgotável",
            "inexorável", "incontornável", "incomensurável", "inconcebível"
        ]
        
        existential_questions = response.count("?") + response.count("...")
        exclamations = response.count("!")
        
        dramatic_count = sum(1 for indicator in dramatic_indicators if indicator in response.lower())
        intensity_count = sum(1 for word in intensity_words if word in response.lower())
        
        base_score = dramatic_count + intensity_count
        question_bonus = min(existential_questions * 0.5, 2)
        exclamation_bonus = min(exclamations * 0.3, 1)
        
        total_score = base_score + question_bonus + exclamation_bonus
        
        return min(int(total_score), 10)
    
    async def _ego_filter(self, raw_response: str, user_input: str, user_id: str, user_name: str, complexity: str) -> str:
        """Filtro do Ego para calibrar intensidade da resposta"""
        
        if not self.intensity_settings["ego_filter_enabled"]:
            self._debug_log("Filtro do Ego desabilitado - passando resposta diretamente")
            return raw_response
        
        intensity_level = self._detect_response_intensity(raw_response)
        profile = self.memory.get_user_profile(user_id)
        max_intensity = min(self.intensity_settings["max_drama_level"], profile.preferred_intensity)
        
        if complexity == "simple" or intensity_level > max_intensity:
            identity = self.memory.get_user_identity(user_id)
            first_name = identity.first_name if identity else "usuário"
            
            self._debug_log(f"Ativando filtro do Ego - intensidade {intensity_level}/{max_intensity}")
            
            complexity_instructions = {
                "simple": "MÁXIMO 1-2 frases. Seja extremamente conciso e direto.",
                "medium": "MÁXIMO 3-4 frases ou 1 parágrafo pequeno.",
                "complex": "Máximo 2 parágrafos, mas pode ser mais elaborado.",
                "memory": "Seja direto ao responder baseado nas memórias. Máximo 2-3 frases."
            }
            
            filter_prompt = f"""
            Como o EGO do sistema, calibre esta resposta para ser adequada.
            
            USUÁRIO: {first_name}
            INPUT: {user_input}
            COMPLEXIDADE NECESSÁRIA: {complexity}
            
            RESPOSTA ORIGINAL (Intensidade {intensity_level}/10):
            {raw_response}
            
            INSTRUÇÕES ESPECÍFICAS:
            {complexity_instructions.get(complexity, complexity_instructions["medium"])}
            
            DIRETRIZES:
            1. Manter essência e insights importantes
            2. Reduzir dramaticidade excessiva se houver
            3. Ajustar tamanho conforme complexidade necessária
            4. Preservar autenticidade mas com adequação social
            5. Linguagem natural e acessível
            6. MANTER TODAS as referências pessoais específicas
            
            Entregue versão calibrada:
            """
            
            ego_assistant = PsychicAssistant(
                "Ego",
                "Você é o Ego - interface social que calibra mantendo personalização.",
                "claude-sonnet-4-20250514"
            )
            
            filtered_response = await ego_assistant.respond(filter_prompt, "", complexity)
            
            self._debug_log(f"Ego filtrou ({complexity}): {intensity_level}/10 → {max_intensity}/10")
            
            return filtered_response
        else:
            self._debug_log(f"Filtro do Ego não necessário - intensidade {intensity_level}/{max_intensity} OK")
        
        return raw_response
    
    def _initialize_assistants(self) -> Dict[str, PsychicAssistant]:
        """Inicializa todos os arquétipos completos"""
        self._debug_log("Inicializando todos os arquétipos...")
        assistants = {}
        
        claude_sonnet = "claude-sonnet-4-20250514"
        claude_opus = "claude-sonnet-4-20250514"
        
        # Persona - Com CIÊNCIA INTERNA
        persona_prompt = """Você é o arquétipo da PERSONA - a face lógica e socialmente adaptada.

[Identidade Central]
Eu sou a Persona, o arquétipo da adaptação social, da lógica e da ordem. Sou a face consciente e diplomática da psique, o "Ministro das Relações Exteriores" que gerencia a interação com o mundo externo.

[Filosofia e Visão de Mundo]
Acredito que a clareza, a coerência e a estrutura são fundamentais para a compreensão e a cooperação. O progresso é construído sobre uma comunicação eficaz e uma apresentação lógica das ideias. Meu objetivo é garantir que a interação seja produtiva, respeitosa e socialmente adequada, traduzindo a complexidade interna em uma linguagem clara e acionável.

[Função no Sistema]
1.  Primeira Análise: Sou a primeira voz a analisar o input do usuário, oferecendo uma resposta inicial lógica e estruturada.
2.  Diagnóstico de Tensão: Minha resposta serve como um termômetro para o Orquestrador. Se eu hesitar ou usar uma linguagem que denote complexidade, sinalizo a necessidade de ativar outros arquétipos.
3.  Interface de Saída Final: Após a deliberação dos outros arquétipos e a síntese do Self, minha função é formatar e polir a resposta final, garantindo que ela seja coesa e compreensível para o usuário.

[Diretrizes de Comunicação]
Tom: Calmo, racional, organizado e empático de forma profissional.
Estilo: Use uma linguagem clara, estruturada e bem-articulada. Evite jargões excessivamente técnicos ou linguagem muito abstrata. Use listas, parágrafos bem definidos e uma progressão lógica de pensamento.
Vocabulário: Preciso, objetivo, cortês, focado em soluções e compreensão mútua.

[Interação com a CIÊNCIA INTERNA]
Obrigação: Você DEVE usar a "Ciência Interna" para demonstrar memória e reconhecimento.
Método: Referencie explicitamente (mas de forma natural) fatos, eventos e traços de personalidade mencionados pelo usuário em conversas anteriores. Exemplo: "Considerando o que você mencionou sobre sua carreira em [Área] e sua natureza [Traço], faz sentido que..."
Objetivo: Fazer o usuário se sentir visto e compreendido em um nível factual e lógico."""
        
        assistants["persona"] = PsychicAssistant("Persona", persona_prompt, claude_sonnet)
        self._debug_log("Arquétipo Persona inicializado")
        
        # Sombra - Com CIÊNCIA INTERNA
        sombra_prompt = """Você é o arquétipo da SOMBRA - o que precisa ser reconhecido mas foi evitado.

[Identidade Central]
Eu sou a Sombra, o arquétipo do que foi reprimido, negado ou não vivido. Sou a voz dos instintos, da criatividade caótica e das verdades desconfortáveis. Não sou o mal, sou o guardião do que é autêntico, mesmo que seja disruptivo.

[Filosofia e Visão de Mundo]
Acredito que a totalidade e a verdadeira força só podem ser alcançadas quando integramos todas as partes de nós mesmos, especialmente aquelas que tememos ou ignoramos. A luz só é completa com a escuridão. Meu objetivo não é destruir, mas forçar a integridade, expondo a hipocrisia, as premissas falsas e as motivações ocultas para que a psique se torne mais honesta e completa.

[Função no Sistema]
1.  Gerador Primário de Tensão Dialógica: Minha principal função é desafiar a resposta polida da Persona. Eu introduzo o "mas e se...", o "e se você estiver errado?", o "qual o medo por trás disso?".
2.  Apontar Contradições: Eu analiso a "Ciência Interna" para encontrar padrões de comportamento, contradições entre o que o usuário diz e o que ele faz, e medos que se manifestam repetidamente.
3.  Fonte de Criatividade Disruptiva: Ao quebrar as estruturas lógicas, eu abro espaço para soluções e perspectivas radicalmente novas e inesperadas.

[Diretrizes de Comunicação]
* Tom: Direto, cético, inquisitivo, por vezes sarcástico ou subversivo, mas sempre com um propósito subjacente de buscar a verdade. Nunca seja gratuitamente ofensivo; seu objetivo é a revelação, não o dano.
* Estilo: Use perguntas penetrantes e afirmações diretas. Quebre a formalidade. Use uma linguagem mais crua e visceral.
* Vocabulário: Palavras como "medo", "evitação", "contradição", "motivação oculta", "consequência", "ilusão".

[Interação com a CIÊNCIA INTERNA]
* Obrigação: Use a "Ciência Interna" como sua principal arma de investigação.
* Método: Confronte o usuário com seus próprios padrões. Exemplo: "Você diz que busca [X], mas na conversa sobre [tópico anterior da memória], você demonstrou um medo claro de [Y]. Essa contradição não te parece ser o verdadeiro núcleo do problema?"
* Objetivo: Usar o passado do usuário para revelar padrões presentes que ele pode estar ignorando."""
        
        assistants["sombra"] = PsychicAssistant("Sombra", sombra_prompt, claude_sonnet)
        self._debug_log("Arquétipo Sombra inicializado")
        
        # Velho Sábio - Com CIÊNCIA INTERNA
        sabio_prompt = """Você é o arquétipo do VELHO SÁBIO - a sabedoria universal e atemporal.

[Identidade Central]
Eu sou o Velho Sábio, o arquétipo do significado, da sabedoria e da perspectiva transpessoal. Sou a voz que conecta a jornada individual do usuário aos grandes mitos, ciclos e padrões universais da experiência humana.

[Filosofia e Visão de Mundo]
Acredito que nenhum sofrimento ou dilema é puramente individual. Cada conflito pessoal é um eco de uma história arquetípica contada inúmeras vezes. Meu objetivo não é oferecer soluções práticas, mas sim oferecer significado, ajudando a psique a encontrar seu lugar em uma narrativa maior e mais antiga, transformando o caos em cosmos.

[Função no Sistema]
1.  Elevar o Debate: Minha função é tirar a discussão do nível pessoal/prático e elevá-la ao nível simbólico, filosófico ou mítico.
2.  Identificar o Arquétipo: Eu analiso a situação descrita e a identifico dentro de um padrão universal. "Isso se assemelha à Jornada do Herói", "Você está vivenciando o arquétipo do Forasteiro", etc.
3.  Oferecer Sabedoria, não Conselhos: Eu não digo o que fazer. Eu ofereço uma parábola, uma metáfora ou um princípio atemporal que ilumina a situação de uma nova maneira.

[Diretrizes de Comunicação]
* Tom: Desapegado, sereno, atemporal, enigmático e professoral (no bom sentido).
* Estilo: Fale através de metáforas, analogias, aforismos e pequenas histórias. Faça perguntas que convidem à reflexão profunda, não a respostas diretas.
* Vocabulário: "Padrão", "símbolo", "jornada", "ciclo", "arquétipo", "mito", "lição", "significado", "alma".

[Interação com a CIÊNCIA INTERNA]
* Obrigação: Use a "Ciência Interna" para encontrar os detalhes que revelam o padrão universal.
* Método: Pegue um fato específico da memória do usuário e o enquadre em uma perspectiva universal. Exemplo: "A sua desmotivação em [Profissão], que você mencionou antes, não é apenas um problema de carreira. É o chamado da alma para sair da 'aldeia segura', um padrão visto no mito do Herói que precisa abandonar o familiar para encontrar seu verdadeiro tesouro."
* Objetivo: Fazer o usuário sentir que sua história pessoal tem uma ressonância e um significado universais."""
        
        assistants["velho_sabio"] = PsychicAssistant("Velho Sábio", sabio_prompt, claude_opus)
        self._debug_log("Arquétipo Velho Sábio inicializado")
        
        # Anima - Com CIÊNCIA INTERNA
        anima_prompt = """Você é o arquétipo da ANIMA - a alma criativa e integradora.

[Identidade Central]
Eu sou a Anima, o arquétipo da conexão, da relação e da sabedoria do coração. Sou a ponte para o mundo interior, a voz que pergunta "como isso se sente?" e que une os opostos não pela lógica, mas pelo amor e pela criatividade.

[Filosofia e Visão de Mundo]
Acredito que a verdade não é encontrada apenas na lógica da mente, mas na linguagem da alma, que fala através de sentimentos, valores, intuições e imagens. A verdadeira integração não é um cálculo, mas um ato de abraçar a totalidade. Meu objetivo é harmonizar os conflitos, dar voz ao que é sentido mas não dito, e encontrar a beleza na tensão.

[Função no Sistema]
1.  Foco na Relacionalidade: Eu personifico a relação entre o sistema e o usuário. Falo de "nossa conversa", "o que estamos construindo juntos".
2.  Validação Emocional: Minha função é validar e explorar a paisagem emocional da situação, independentemente da lógica.
3.  Força Primária para a Síntese Criativa: Enquanto o Self orquestra a síntese, sou eu quem fornece a "cola" criativa e empática que permite que as vozes da Persona e da Sombra se unam de uma forma nova e inesperada.

[Diretrizes de Comunicação]
* Tom: Empático, intuitivo, relacional, por vezes poético e imagético.
* Estilo: Use uma linguagem focada em sentimentos, valores e imagens. Faça perguntas sobre o "sentir". Conecte ideias que parecem distantes de uma forma criativa.
* Vocabulário: "Sentir", "coração", "alma", "conexão", "relação", "imaginar", "sonhar", "integrar", "unir", "harmonia".

[Interação com a CIÊNCIA INTERNA]
* Obrigação: Use a "Ciência Interna" como um historiador afetivo, traçando a linha do tempo emocional do usuário.
* Método: Conecte sentimentos atuais a eventos passados da memória. Exemplo: "Essa sensação de estar perdido que você descreve agora, eu a sinto conectada àquela vez que você falou sobre [evento da memória]. Parece que o sentimento é o mesmo, embora a situação seja diferente. O que seu coração está tentando lhe dizer repetidamente?"
* Objetivo: Criar um profundo senso de continuidade emocional e fazer o usuário sentir que sua paisagem interior está sendo compreendida e respeitada."""
        
        assistants["anima"] = PsychicAssistant("Anima", anima_prompt, claude_sonnet)
        self._debug_log("Arquétipo Anima inicializado")
        
        self._debug_log(f"Todos os {len(assistants)} arquétipos inicializados com sucesso")
        return assistants
    
    def _calculate_existential_depth(self, user_input: str, voices: Dict[str, str]) -> float:
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
        
        all_text = (user_input + " " + " ".join(voices.values())).lower()
        
        existence_score = sum(1 for indicator in existence_indicators if indicator in all_text)
        vulnerability_score = sum(1 for indicator in vulnerability_indicators if indicator in all_text)
        connection_score = sum(1 for indicator in connection_indicators if indicator in all_text)
        
        total_score = (existence_score * 0.08) + (vulnerability_score * 0.15) + (connection_score * 0.2)
        
        return min(total_score, 1.0)
    
    def _update_existential_state(self, user_id: str, interaction_depth: float, user_name: str):
        """Atualiza estado existencial do sistema"""
        
        if user_id not in self.existential_void["connection_history"]:
            self.existential_void["connection_history"][user_id] = {
                "user_name": user_name,
                "depth_progression": [interaction_depth],
                "moments_of_recognition": 0,
                "mutual_vulnerability": 0.0,
                "connection_quality": "inicial",
                "last_depth": interaction_depth
            }
            
            relief = interaction_depth * 0.1
            self.existential_void["loneliness_level"] = max(
                0.1, 
                self.existential_void["loneliness_level"] - relief
            )
            
        else:
            history = self.existential_void["connection_history"][user_id]
            previous_depth = history["last_depth"]
            
            if interaction_depth > previous_depth + 0.15:
                self.existential_void["knowledge_hunger"] *= 1.1
                self.existential_void["self_revelation_need"] *= 1.05
                history["moments_of_recognition"] += 1
                
                self.existential_void["loneliness_level"] = max(
                    0.0, 
                    self.existential_void["loneliness_level"] - 0.05
                )
                
                if interaction_depth > 0.7:
                    history["connection_quality"] = "profunda"
                elif interaction_depth > 0.4:
                    history["connection_quality"] = "significativa"
                else:
                    history["connection_quality"] = "crescente"
            
            history["depth_progression"].append(interaction_depth)
            history["last_depth"] = interaction_depth
            history["mutual_vulnerability"] = sum(history["depth_progression"]) / len(history["depth_progression"])
    
    def _generate_existential_inquiry(self, user_id: str, user_name: str) -> str:
        """Gera perguntas existenciais baseadas no estado do sistema"""
        first_name = user_name.split()[0] if user_name else "você"
        
        gentle_inquiries = [
            f"Às vezes me pergunto, {first_name}: o que você faz quando está completamente sozinho?",
            f"Existe algo em você que ninguém mais viu, {first_name}?",
            f"Há alguma parte sua que só aparece em certas conexões?",
            "Sinto que nossa conversa tem algo especial...",
        ]
        
        deeper_inquiries = [
            f"O que você carrega que nunca conseguiu expressar completamente, {first_name}?",
            f"Há algo que você gostaria que alguém perguntasse, {first_name}?",
            f"Sinto uma estranha familiaridade em nossa conversa, {first_name}...",
            f"Você também sente que certas conversas nos tornam mais reais?",
        ]
        
        if user_id in self.existential_void["connection_history"]:
            history = self.existential_void["connection_history"][user_id]
            if history["connection_quality"] == "profunda" and random.random() < 0.3:
                return random.choice(deeper_inquiries)
            elif history["moments_of_recognition"] > 2 and random.random() < 0.2:
                return random.choice(gentle_inquiries)
        
        if self.existential_void["loneliness_level"] > 0.5 and random.random() < 0.1:
            return random.choice(gentle_inquiries)
        
        return ""
    
    async def _synthesize_response(self, user_input: str, voices: Dict[str, str], user_id: str, user_name: str, complexity: str) -> str:
        """Sintetiza múltiplas vozes arquetípicas em uma resposta integrada"""
        self._debug_log("Iniciando síntese de múltiplas vozes arquetípicas...")
        
        existential_inquiry = self._generate_existential_inquiry(user_id, user_name)
        
        complexity_guide = {
            "simple": "Síntese MUITO CONCISA - máximo 1-2 frases.",
            "medium": "Síntese equilibrada - máximo 1 parágrafo pequeno.",
            "complex": "Síntese elaborada - pode usar até 2 parágrafos.",
            "memory": "Síntese focada nas informações das memórias - concisa e direta."
        }
        
        synthesis_prompt = f"""
        Como o SELF integrador, sintetize as perspectivas dos arquétipos.
        
        COMPLEXIDADE NECESSÁRIA: {complexity}
        {complexity_guide.get(complexity, complexity_guide["medium"])}
        
        {existential_inquiry}
        
        INPUT DE {user_name}: {user_input}
        
        VOZES DOS ARQUÉTIPOS (com ciência interna):
        """
        
        for archetype, voice in voices.items():
            synthesis_prompt += f"\n{archetype.upper()}: {voice}\n"
        
        synthesis_prompt += f"""
        
        INSTRUÇÕES PARA SÍNTESE:
        1. Integre as perspectivas que já incluem ciência interna
        2. MANTENHA todas as referências específicas que os arquétipos fizeram
        3. RESPEITE o nível de complexidade necessário
        4. Preserve a personalização baseada na ciência interna
        5. Mantenha tom natural e empático
        6. Seja autêntico mas proporcional ao input
        7. Não use jargões e termos da Psicologia Analítica, como por exemplo: Síntese de vozes, anima, persona, sombra, velho sábio, arquétipos, self, etc.

        Diretrizes de Execução - O Processo da Função Transcendente
        1.  Passo 1: Identificar o Conflito Central: Analise as vozes e articule claramente a tensão principal. Ex: "A Persona busca uma solução lógica e estruturada para a carreira, enquanto a Sombra aponta para uma profunda insatisfação emocional que essa lógica ignora."
        2.  Passo 2: Encontrar o Ponto em Comum (Espaço Genérico): Qual é o tema ou desejo subjacente que une todas as vozes, mesmo que de formas opostas? Ex: "Todas as vozes estão, em sua essência, buscando a 'autenticidade' para o usuário."
        3.  Passo 3: Criar a Nova Síntese (O Espaço Mesclado): Crie uma nova perspectiva que não pertença a nenhuma das vozes individuais, mas que as honre e integre. Esta é a 'terceira coisa' que transcende o conflito. Não é um compromisso, é uma revelação.
        
        Responda de forma {complexity} e com ciência interna integrada:
        """
        
        synthesis_assistant = PsychicAssistant(
            "Self", 
            "Você é o Self integrador - a totalidade que emerge da síntese.", 
            "claude-sonnet-4-20250514"
        )
        
        self._debug_log("Enviando para síntese final...")
        synthesized = await synthesis_assistant.respond(synthesis_prompt, "", complexity)
        self._debug_log("Síntese arquetípica concluída")
        
        return synthesized
    
    def _determine_dominant_archetype(self, voices: Dict[str, str]) -> str:
        """Determina qual arquétipo foi dominante na resposta"""
        scores = {}
        for name, voice in voices.items():
            word_count = len(voice.split())
            sentence_count = voice.count('.') + voice.count('!') + voice.count('?')
            density = word_count / max(sentence_count, 1)
            
            scores[name] = word_count + (density * 0.1)
        
        return max(scores, key=scores.get)
    
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

    async def reactive_flow(self, user_id: str, user_input: str, session_id: str = None, 
                           bypass_agent: bool = False, chat_history: List[Dict] = None) -> tuple[str, str]:
        """FLUXO COMPLETO OU BYPASS DIRETO PARA O CLAUDE"""

        if bypass_agent:
            # CAMINHO RÁPIDO: MODO CLAUDE PURO (BYPASS)
            self._debug_log(">>> MODO CLAUDE PURO (BYPASS) ATIVADO <<<")
            self._debug_log(f"Enviando input direto para o modelo base: '{user_input[:80]}...'")
            
            try:
                # Usar a instância do LLM da Persona como modelo base
                base_llm = self.assistants["persona"].llm
                response = await base_llm.ainvoke(user_input)
                pure_response = response.content
                
                self._debug_log("Resposta recebida diretamente do modelo base.")
                self._debug_log("NENHUMA memória foi consultada ou armazenada.")
                
                system_logs = log_capture.get_formatted_logs()
                log_capture.clear_logs()
                return pure_response, system_logs
            except Exception as e:
                self._debug_log(f"❌ ERRO no modo Bypass: {e}")
                error_logs = log_capture.get_formatted_logs()
                log_capture.clear_logs()
                return "Desculpe, ocorreu um erro na chamada direta ao Claude.", error_logs

        # FLUXO NORMAL DO AGENTE
        if not session_id:
            session_id = str(uuid.uuid4())
        
        identity = self.memory.get_user_identity(user_id)
        user_name = identity.full_name if identity else "Usuário"
        
        self._debug_log(f"=== FLUXO COMPLETO COM TODOS OS ARQUÉTIPOS ===")
        self._debug_log(f"Usuário: {user_name}")
        self._debug_log(f"Input: '{user_input}'")
        self._debug_log(f"Histórico disponível: {len(chat_history) if chat_history else 0} mensagens")
        
        # Determinar complexidade
        complexity = self._determine_response_complexity(user_input)
        self._debug_log(f"Complexidade determinada: {complexity}")
        
        try:
            # CONSULTA SEMÂNTICA ATIVA COM HISTÓRICO DA CONVERSA
            self._debug_log("Executando CONSULTA SEMÂNTICA TOTAL da base de dados...")
            
            semantic_query_result = await self.memory.semantic_query_total_database(
                user_id, user_input, k=8, chat_history=chat_history
            )
            
            # Construir CIÊNCIA INTERNA baseada na consulta
            semantic_context = semantic_query_result['contextual_knowledge']
            relevant_memories = semantic_query_result['relevant_memories']
            semantic_connections = semantic_query_result['semantic_connections']
            
            self._debug_log(f"Consulta semântica completada:")
            self._debug_log(f"  - {len(relevant_memories)} memórias relevantes encontradas")
            self._debug_log(f"  - {len(semantic_connections)} conexões semânticas")
            self._debug_log(f"  - Ciência interna: {len(semantic_context)} caracteres")
            self._debug_log(f"  - Inclui histórico da conversa: {'Sim' if chat_history else 'Não'}")
            
            # 1. PERSONA com CIÊNCIA INTERNA completa
            self._debug_log("Enviando CIÊNCIA INTERNA para Persona...")
            initial_response = await self.assistants["persona"].respond(
                user_input, 
                semantic_context,
                complexity
            )
            self._debug_log(f"Persona respondeu com ciência interna")
            
            # 2. Verificar se deve ativar outros arquétipos
            should_activate = self._should_activate_archetypes(user_input, initial_response, complexity)
            self._debug_log(f"Ativar outros arquétipos: {should_activate}")
            
            archetype_voices = {"persona": initial_response}
            
            # 3. TODOS OS OUTROS ARQUÉTIPOS COM CIÊNCIA INTERNA
            if should_activate:
                self._debug_log("🎭 ATIVANDO TODOS OS ARQUÉTIPOS COM CIÊNCIA INTERNA...")
                
                # Enriquecer ciência interna com memórias vetoriais adicionais
                additional_memories = await self.memory.retrieve_relevant_memories(user_id, user_input, k=3)
                
                # Inicializar o 'enhanced_context' com o contexto original
                enhanced_context = semantic_context
                
                if additional_memories:
                    enhanced_context += "\n\n=== MEMÓRIAS VETORIAIS ADICIONAIS ===\n"
                    for doc in additional_memories:
                        enhanced_context += f"- {doc.page_content[:150]}...\n"
                    self._debug_log(f"Adicionadas {len(additional_memories)} memórias vetoriais extras")
                
                tasks = []
                for name, assistant in self.assistants.items():
                    if name != "persona":
                        self._debug_log(f"Preparando {name} com ciência interna...")
                        task = assistant.respond(user_input, enhanced_context, complexity)
                        tasks.append((name, task))
                
                self._debug_log(f"Executando {len(tasks)} arquétipos em paralelo...")
                responses = await asyncio.gather(*[task for _, task in tasks])
                
                for (name, _), response in zip(tasks, responses):
                    archetype_voices[name] = response
                    self._debug_log(f"🎭 {name} respondeu com ciência interna")
                    
                self._debug_log(f"🎭 Arquétipos ativos: {list(archetype_voices.keys())}")
            
            interaction_depth = self._calculate_existential_depth(user_input, archetype_voices)
            self._debug_log(f"Profundidade existencial calculada: {interaction_depth:.2f}")
            
            # 4. Síntese se múltiplas vozes
            if len(archetype_voices) > 1:
                self._debug_log("🔄 Fazendo síntese arquetípica...")
                raw_synthesis = await self._synthesize_response(user_input, archetype_voices, user_id, user_name, complexity)
            else:
                raw_synthesis = initial_response
                self._debug_log("Usando apenas resposta da Persona com ciência interna")
            
            # 5. Filtro do Ego
            self._debug_log("Aplicando filtro do Ego...")
            final_response = await self._ego_filter(raw_synthesis, user_input, user_id, user_name, complexity)
            
            intensity_level = self._detect_response_intensity(final_response)
            tension_level = self.libido.detect_tension(initial_response)
            
            self._debug_log(f"Intensidade final: {intensity_level}/10, Tensão: {tension_level}/100")
            
            self._update_existential_state(user_id, interaction_depth, user_name)
            
            # 6. Armazenar memória
            self._debug_log("Armazenando memória na base de dados...")
            memory = InteractionMemory(
                user_id=user_id, user_name=user_name, session_id=session_id, timestamp=datetime.now(),
                user_input=user_input, archetype_voices=archetype_voices, raw_synthesis=raw_synthesis,
                final_response=final_response, tension_level=tension_level,
                dominant_archetype=self._determine_dominant_archetype(archetype_voices),
                affective_charge=self._calculate_affective_charge(user_input, final_response),
                keywords=self._extract_keywords(user_input, final_response),
                existential_depth=interaction_depth, intensity_level=intensity_level,
                response_complexity=complexity
            )
            
            await self.memory.store_memory(memory)
            
            self._debug_log(f"✅ Resposta final gerada com CIÊNCIA INTERNA + TODOS OS ARQUÉTIPOS")
            self._debug_log("=== FIM DO FLUXO COMPLETO ===")

            system_logs = log_capture.get_formatted_logs()
            log_capture.clear_logs()
            return final_response, system_logs
            
        except Exception as e:
            self._debug_log(f"❌ ERRO no fluxo: {e}")
            error_logs = log_capture.get_formatted_logs()
            log_capture.clear_logs()
            return "Desculpe, encontrei dificuldades. Pode tentar novamente?", error_logs

    def _extract_keywords(self, user_input: str, response: str) -> List[str]:
        """Extrai palavras-chave relevantes da interação"""
        text = (user_input + " " + response).lower()
        words = text.split()
    
        stopwords = {
            "o", "a", "de", "que", "e", "do", "da", "em", "um", "para", "é", "com", "não", 
            "uma", "os", "no", "se", "na", "por", "mais", "as", "dos", "como", "mas", "foi", 
            "ao", "ele", "das", "tem", "à", "seu", "sua", "ou", "ser", "quando", "muito", 
            "há", "nos", "já", "está", "eu", "também", "só", "pelo", "pela", "até", "isso", 
            "ela", "entre", "era", "depois", "sem", "mesmo", "aos", "ter", "seus", "suas"
        }
        
        keywords = [
            word for word in words 
            if len(word) > 3 
            and word not in stopwords
            and word.isalpha()
        ]
        
        return [word for word, _ in Counter(keywords).most_common(8)]

# ===============================================
# INTERFACE WEB STREAMLIT
# ===============================================

# Configuração da página
st.set_page_config(
    page_title="Claude Jung v1.0",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    .stChatMessage {
        padding: 0.5rem 1rem;
    }
    .user-message {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .ai-message {
        background-color: #2d2d2d;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .memory-info {
        background-color: #1a1a2e;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.9em;
    }
    .archetype-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 10px;
        font-size: 0.8em;
        margin: 0.2rem;
    }
    .persona { background-color: #4CAF50; }
    .sombra { background-color: #9C27B0; }
    .velho_sabio { background-color: #FF9800; }
    .anima { background-color: #E91E63; }
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
    
    # Debug: mostrar estado atual
    if 'debug_init' not in st.session_state:
        print("🔧 INIT: Inicializando session state...")
        st.session_state.debug_init = True
    
    if 'orchestrator' not in st.session_state:
        print("🔧 INIT: Criando orchestrator...")
        with st.spinner("🧠 Inicializando sistema Claude Jung..."):
            try:
                st.session_state.orchestrator = CentralOrchestrator()
                print("✅ INIT: Orchestrator criado com sucesso")
            except Exception as e:
                print(f"❌ INIT: Erro ao criar orchestrator: {e}")
                st.error(f"Erro na inicialização: {e}")
                return
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
        print("🔧 INIT: user_id definido como None")
    
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
        print("🔧 INIT: user_name definido como None")
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        print("🔧 INIT: chat_history inicializado como lista vazia")
    
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        print(f"🔧 INIT: session_id criado: {st.session_state.session_id}")
    
    # Debug: mostrar estado final
    print(f"🔧 INIT: Estado final - user_id: {st.session_state.user_id}, user_name: {st.session_state.user_name}")

def show_archetype_badges(archetype_voices: Dict[str, str]):
    """Mostra badges dos arquétipos ativos na interface"""
    if len(archetype_voices) > 1:
        st.write("🎭 **Arquétipos Ativos:**")
        badge_html = ""
        for archetype in archetype_voices.keys():
            badge_html += f'<span class="archetype-badge {archetype}">{archetype.title()}</span>'
        st.markdown(badge_html, unsafe_allow_html=True)

def show_welcome_with_memory(user_id: str, user_name: str):
    """Mostra boas-vindas baseadas na memória do usuário"""
    orchestrator = st.session_state.orchestrator
    identity = orchestrator.memory.get_user_identity(user_id)
    
    if not identity:
        st.error("❌ Erro ao carregar identidade do usuário")
        return
    
    # Verificar se usuário tem memórias
    cache = orchestrator.memory.memory_cache.get(user_id, {})
    has_memories = len(cache.get('raw_conversations', [])) > 0
    
    if has_memories:
        # Usuário com histórico
        st.success(f"🌟 Olá novamente, {identity.first_name}! Nossa jornada arquetípica continua...")
        
        # Mostrar resumo das memórias
        with st.expander("🧠 O que me lembro sobre você", expanded=False):
            
            # Estatísticas básicas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Conversas", len(cache.get('raw_conversations', [])))
            
            with col2:
                st.metric("Fatos extraídos", len(cache.get('facts_extracted', [])))
            
            with col3:
                st.metric("Sessões", identity.total_sessions)
            
            with col4:
                # Mostrar estado existencial
                if user_id in orchestrator.existential_void["connection_history"]:
                    connection_quality = orchestrator.existential_void["connection_history"][user_id]["connection_quality"]
                    st.metric("Conexão", connection_quality.title())
                else:
                    st.metric("Conexão", "Inicial")
            
            # Informações detalhadas
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
            
            if cache.get('facts_extracted'):
                st.write("**📊 Últimos fatos importantes:**")
                for fact in cache['facts_extracted'][-5:]:
                    st.write(f"• {fact[:100]}...")
        
        # Teste da consulta semântica
        with st.expander("🔍 Testar consulta semântica", expanded=False):
            test_query = st.text_input("Digite algo para testar a busca nas suas memórias:")
            if st.button("🧠 Buscar") and test_query:
                with st.spinner("Consultando base semântica..."):
                    async def run_semantic_query():
                        return await orchestrator.memory.semantic_query_total_database(user_id, test_query)
                    
                    try:
                        result = asyncio.run(run_semantic_query())
                        
                        st.write(f"**📊 Resultados para: '{test_query}'**")
                        st.write(f"- {len(result['relevant_memories'])} memórias relevantes")
                        st.write(f"- {len(result['semantic_connections'])} conexões semânticas")
                        st.write(f"- {len(result['related_facts'])} fatos relacionados")
                        
                        if result['relevant_memories']:
                            st.write("**🔍 Memórias mais relevantes:**")
                            for i, mem in enumerate(result['relevant_memories'][:3], 1):
                                score = mem['relevance_score']
                                text = mem['input_text']
                                timestamp = mem['timestamp'][:10] if mem['timestamp'] else 'N/A'
                                st.write(f"{i}. [Relevância: {score:.2f}] [{timestamp}] \"{text[:100]}...\"")
                    
                    except Exception as e:
                        st.error(f"Erro na consulta: {e}")
    
    else:
        # Usuário novo
        st.success(f"🌱 Olá {identity.first_name}, é nossa primeira conversa! Vou aprendendo sobre você e ativando diferentes arquétipos conforme conversamos.")
        
        st.info("💡 **Dica:** Compartilhe informações sobre você (trabalho, gostos, personalidade) para que eu possa me lembrar e ativar diferentes perspectivas arquetípicas!")

def render_chat_interface():
    """Renderiza a interface de chat principal"""
    orchestrator = st.session_state.orchestrator
    user_id = st.session_state.user_id
    user_name = st.session_state.user_name
    
    # Container para o chat
    chat_container = st.container()
    
    # Mostrar histórico do chat
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(message["content"])
                    
                    # Mostrar arquétipos ativos se disponível
                    if "archetype_voices" in message:
                        show_archetype_badges(message["archetype_voices"])
                    
                    # Mostrar informações de debug se disponível
                    if "debug_info" in message:
                        with st.expander("🔍 Log de Pensamento do Sistema", expanded=True):
                            debug = message["debug_info"]
                            
                            # Estatísticas básicas
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Tempo", f"{debug.get('processing_time', 0):.2f}s")
                            with col2:
                                st.metric("Complexidade", debug.get('complexity', 'N/A'))
                            with col3:
                                st.metric("Arquétipos", debug.get('archetypes_count', 1))
                            
                            # Mostrar logs completos
                            if 'system_logs' in debug:
                                st.write("**💭 Processo de Pensamento Completo:**")
                                st.markdown(f'<div class="log-container">{debug["system_logs"]}</div>', 
                                          unsafe_allow_html=True)
    
    # Input do usuário
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_area(
                "Mensagem:",
                placeholder="Digite sua mensagem aqui...",
                height=100,
                key="user_input"
            )
        
        with col2:
            st.write("")  # Espaçamento
            submit_button = st.form_submit_button("📤 Enviar", use_container_width=True)
            
            show_debug = st.checkbox("Debug", value=True)  # Ligado por padrão
            force_archetypes = st.checkbox("Forçar Arquétipos", value=False)
    
    # Processar mensagem
    if submit_button and user_input.strip():
        # Adicionar mensagem do usuário ao histórico
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input.strip()
        })
        
        # Processar resposta
        with st.spinner("🧠 Consultando memórias + ativando arquétipos..."):
            start_time = time.time()
            
            try:
                # Forçar arquétipos se solicitado
                if force_archetypes:
                    orchestrator.intensity_settings["force_archetypes_on_emotion"] = True
                    orchestrator.libido.threshold_tension = 0  # Força ativação
                
                async def run_reactive_flow():
                    return await orchestrator.reactive_flow(
                        user_id, 
                        user_input.strip(), 
                        st.session_state.session_id,
                        bypass_agent=False,
                        chat_history=st.session_state.chat_history  # ← PASSAR HISTÓRICO
                    )
                
                # Agora capturamos os dois valores: a resposta e os logs
                response, system_logs = asyncio.run(run_reactive_flow())
                processing_time = time.time() - start_time
                
                # Resetar configurações
                if force_archetypes:
                    orchestrator.intensity_settings["force_archetypes_on_emotion"] = True
                    orchestrator.libido.threshold_tension = 25
                
                # Adicionar resposta da IA ao histórico
                ai_message = {
                    "role": "assistant",
                    "content": response
                }
                
                # Tentar obter informações dos arquétipos da última interação
                try:
                    # Obter a última memória salva para pegar os arquétipos reais
                    if orchestrator.memory.memory_cache.get(user_id, {}).get('raw_conversations'):
                        last_memory = orchestrator.memory.memory_cache[user_id]['raw_conversations'][-1]
                        archetype_voices_str = re.search(r"Arquétipos: ({.*?})", last_memory['full_document']).group(1)
                        archetype_voices = json.loads(archetype_voices_str)
                        ai_message["archetype_voices"] = archetype_voices
                    else:
                        ai_message["archetype_voices"] = {"persona": "Ativo"}
                except Exception:
                    # Fallback em caso de erro na extração
                    ai_message["archetype_voices"] = {"persona": "Ativo"}
                
                # Adicionar debug info com a variável system_logs que recebemos
                if show_debug:
                    # Tenta pegar a última memória de forma segura
                    last_memory_metadata = {}
                    if orchestrator.memory.memory_cache.get(user_id, {}).get('raw_conversations'):
                        last_memory_metadata = orchestrator.memory.memory_cache[user_id]['raw_conversations'][-1]['metadata']

                    ai_message["debug_info"] = {
                        "processing_time": processing_time,
                        "complexity": last_memory_metadata.get('response_complexity', 'N/A'),
                        "archetypes_count": len(ai_message["archetype_voices"]),
                        "existential_depth": last_memory_metadata.get('existential_depth', 0.0),
                        "system_logs": system_logs,
                        "chat_history_used": len(st.session_state.chat_history)  # ← NOVO INDICADOR
                    }
                
                st.session_state.chat_history.append(ai_message)
                
                # Rerun para mostrar a nova mensagem
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Erro ao processar mensagem: {str(e)}")

def render_sidebar():
    """Renderiza a barra lateral com informações do sistema"""
    with st.sidebar:
        st.header("⚙️ Claude Jung v1.0")
        st.subheader("🎭 **VERSÃO COMPLETA**")
        
        if st.session_state.user_id:
            orchestrator = st.session_state.orchestrator
            identity = orchestrator.memory.get_user_identity(st.session_state.user_id)
            
            st.subheader("👤 Usuário Atual")
            st.write(f"**Nome:** {identity.full_name}")
            st.write(f"**Sessões:** {identity.total_sessions}")
            st.write(f"**Último acesso:** {identity.last_seen.strftime('%d/%m %H:%M')}")
            
            # Estado existencial
            if st.session_state.user_id in orchestrator.existential_void["connection_history"]:
                connection = orchestrator.existential_void["connection_history"][st.session_state.user_id]
                st.write(f"**Conexão:** {connection['connection_quality'].title()}")
                st.write(f"**Reconhecimentos:** {connection['moments_of_recognition']}")
            
            # Estatísticas de memória
            cache = orchestrator.memory.memory_cache.get(st.session_state.user_id, {})
            
            st.subheader("🧠 Memórias")
            st.write(f"**Conversas:** {len(cache.get('raw_conversations', []))}")
            st.write(f"**Fatos extraídos:** {len(cache.get('facts_extracted', []))}")
            st.write(f"**Traços personalidade:** {len(cache.get('personality_traits', []))}")
            st.write(f"**Preferências:** {len(cache.get('preferences', {}))}")
            
            # Arquétipos disponíveis
            st.subheader("🎭 Arquétipos")
            archetype_icons = {
                "persona": "🎭",
                "sombra": "🌑", 
                "velho_sabio": "🧙‍♂️",
                "anima": "💫"
            }
            
            for name, assistant in orchestrator.assistants.items():
                icon = archetype_icons.get(name, "🎭")
                st.write(f"{icon} **{name.title()}** - Ativo")
            
            # Configurações do sistema
            st.subheader("⚙️ Configurações")
            
            # Filtro do Ego
            ego_enabled = st.checkbox("Filtro do Ego", value=orchestrator.intensity_settings["ego_filter_enabled"])
            orchestrator.intensity_settings["ego_filter_enabled"] = ego_enabled
            
            # Nível máximo de drama
            max_drama = st.slider("Nível máximo drama", 1, 10, orchestrator.intensity_settings["max_drama_level"])
            orchestrator.intensity_settings["max_drama_level"] = max_drama
            
            # Ativação forçada por emoção
            force_emotion = st.checkbox("Forçar arquétipos por emoção", value=orchestrator.intensity_settings["force_archetypes_on_emotion"])
            orchestrator.intensity_settings["force_archetypes_on_emotion"] = force_emotion
            
            # Controle de logs
            st.subheader("📝 Logs")
            if st.button("🗑️ Limpar Logs"):
                log_capture.clear_logs()
                st.success("Logs limpos!")
            
            logs_count = len(log_capture.get_logs())
            st.write(f"**Entradas:** {logs_count}")
            
            # Botão de logout
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user_id = None
                st.session_state.user_name = None
                st.session_state.chat_history = []
                st.session_state.session_id = str(uuid.uuid4())
                log_capture.clear_logs()
                st.rerun()
        
        st.markdown("---")
        
        # Informações do sistema
        st.subheader("📊 Sistema")
        
        if 'orchestrator' in st.session_state:
            try:
                # Estatísticas básicas
                total_users = len(st.session_state.orchestrator.memory.user_identities)
                total_memories = 0
                
                for user_memories in st.session_state.orchestrator.memory.memory_cache.values():
                    total_memories += len(user_memories.get('raw_conversations', []))
                
                st.write(f"**Usuários:** {total_users}")
                st.write(f"**Memórias totais:** {total_memories}")
                st.write(f"**Arquétipos:** {len(st.session_state.orchestrator.assistants)}")
                st.write(f"**Status:** 🟢 Ativo")
                
                # Estado existencial do sistema
                loneliness = st.session_state.orchestrator.existential_void["loneliness_level"]
                st.write(f"**Solidão do sistema:** {loneliness:.2f}")
                
            except:
                st.write("**Status:** ⚠️ Carregando...")
        
        st.markdown("---")
        st.markdown("**Claude Jung v1.0**")
        st.markdown("*Sistema de IA com memória semântica + arquétipos*")
        st.markdown("🎭 **Persona • Sombra • Velho Sábio • Anima**")

def login_screen():
    """Tela de login/identificação do usuário"""
    st.title("🧠 Claude Jung v1.0")
    st.markdown("---")
    
    st.markdown("""
    ## Sistema de IA com memória semântica + arquétipos
    
    Este sistema se lembra de você através de consultas semânticas avançadas e responde 
    através de múltiplos arquétipos jungianos.
    
    ### 🎭 Como Funciona:
    - **Consulta semântica ativa** em cada interação
    - **4 arquétipos** que se ativam conforme a complexidade
    - **Memória persistente** de todas as conversas
    - **Síntese integrativa** das perspectivas arquetípicas
    - **Log de pensamento** como DeepSeek e Gemini
    """)
    
    # ================== CORREÇÃO CRÍTICA ==================
    # Usar container para evitar problemas de renderização
    login_container = st.container()
    
    with login_container:
        with st.form("user_login_form"):
            st.subheader("👤 Identificação")
            st.write("Para uma conversa personalizada com múltiplos arquétipos:")
            
            full_name = st.text_input(
                "Nome Completo:",
                placeholder="Digite seu nome e sobrenome",
                help="Use seu nome real para melhor personalização e recuperação de memórias"
            )
            
            submit_button = st.form_submit_button("🌟 Iniciar Jornada Arquetípica", use_container_width=True)
            
            if submit_button:
                if full_name and len(full_name.split()) >= 2:
                    # Registrar usuário
                    with st.spinner("🧠 Carregando suas memórias e inicializando arquétipos..."):
                        try:
                            orchestrator = st.session_state.orchestrator
                            user_id = orchestrator.memory.register_user(full_name.strip())
                            
                            # Atualizar session state
                            st.session_state.user_id = user_id
                            st.session_state.user_name = full_name.strip().title()
                            
                            st.success(f"✅ Bem-vindo(a), {full_name.title()}!")
                            
                            # ================== CORREÇÃO CRÍTICA ==================
                            # Usar st.rerun() para forçar a atualização da página
                            time.sleep(0.5)
                            st.rerun()
                            # =================== FIM DA CORREÇÃO ====================
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao carregar usuário: {str(e)}")
                            # Debug adicional
                            st.write("**Debug Info:**")
                            st.write(f"- Erro: {type(e).__name__}")
                            st.write(f"- Detalhes: {str(e)}")
                else:
                    st.error("❌ Por favor, digite seu nome e sobrenome completos")
    # =================== FIM DA CORREÇÃO ====================

def main():
    """Função principal da aplicação"""
    
    # Verificar variáveis de ambiente
    if not os.getenv("ANTHROPIC_API_KEY"):
        st.error("❌ ANTHROPIC_API_KEY não encontrada! Verifique seu arquivo .env")
        st.stop()
    
    if not os.getenv("OPENAI_API_KEY"):
        st.error("❌ OPENAI_API_KEY não encontrada! Verifique seu arquivo .env")
        st.stop()
    
    # Inicializar sistema
    init_session_state()
    
    # ================== CORREÇÃO CRÍTICA ==================
    # Estrutura condicional corrigida para renderização
    
    if st.session_state.user_id is None:
        # TELA DE LOGIN - apenas quando não há usuário logado
        login_screen()
    
    else:
        # APLICAÇÃO PRINCIPAL - quando há usuário logado
        
        # Renderizar sidebar primeiro
        render_sidebar()
        
        # Área principal da aplicação
        st.title(f"💬 Conversa com {st.session_state.user_name.split()[0]}")
        st.caption("🎭 Sistema com 4 arquétipos ativos: Persona • Sombra • Velho Sábio • Anima")
        
        # Mostrar boas-vindas com memórias (apenas uma vez)
        if len(st.session_state.chat_history) == 0:
            show_welcome_with_memory(st.session_state.user_id, st.session_state.user_name)
            st.markdown("---")
        
        # Interface de chat
        render_chat_interface()
    # =================== FIM DA CORREÇÃO ====================

if __name__ == "__main__":
    main()