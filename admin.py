# admin.py (VERSÃO CORRIGIDA - v2.1)
"""
Jung Claude - Analytics Dashboard
Sistema de análise psicológica integrado com ChromaDB + SQLite
CORREÇÕES: Validação por memórias ChromaDB + Diagnóstico de sincronização
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import json
from typing import List, Dict, Any, Optional, Tuple
import os
from pathlib import Path
from dotenv import load_dotenv
from collections import Counter
import re
import hashlib

# Imports condicionais
try:
    from openai import OpenAI
    import chromadb
    ANALYTICS_AVAILABLE = True
except ImportError as e:
    ANALYTICS_AVAILABLE = False
    st.error(f"⚠️ Módulos não disponíveis: {e}")

load_dotenv()

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

class AdminConfig:
    BASE_DIR = Path(__file__).resolve().parent
    CHROMA_DIR = BASE_DIR / "chroma_db"
    AGENT_DB = BASE_DIR / "agent_development.db"
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    XAI_API_KEY = os.getenv("XAI_API_KEY", "")
    
    MIN_INTERACTIONS_FOR_ANALYSIS = 10  # ✅ Baseado em memórias ChromaDB
    
    SPECTRUM_THRESHOLD_WEAK = 20
    SPECTRUM_THRESHOLD_MODERATE = 60
    
    DEVELOPMENT_PHASES = {
        1: "Reativo",
        2: "Adaptativo",
        3: "Reflexivo",
        4: "Integrado",
        5: "Transcendente"
    }

# ============================================================================
# UTILITÁRIOS
# ============================================================================

def get_user_hash(user_id: str) -> str:
    """Gera hash MD5 do user_id (mesmo método do app.py)"""
    return hashlib.md5(user_id.encode()).hexdigest()

def interpret_spectrum_score(score: float) -> str:
    """Interpreta score espectral"""
    abs_score = abs(score)
    
    if abs_score < AdminConfig.SPECTRUM_THRESHOLD_WEAK:
        return "Indefinido/Ambivertido"
    elif abs_score < AdminConfig.SPECTRUM_THRESHOLD_MODERATE:
        return "Moderado"
    else:
        return "Claro/Pronunciado"

# ============================================================================
# GERENCIADOR DE DADOS (SQLITE)
# ============================================================================

class SQLiteManager:
    """Gerencia operações com SQLite"""
    
    def __init__(self, db_path: Path = AdminConfig.AGENT_DB):
        self.db_path = db_path
        self._verify_database()
    
    def _verify_database(self):
        """Verifica se o banco existe e tem a estrutura correta"""
        if not self.db_path.exists():
            st.error(f"❌ Banco de dados não encontrado: {self.db_path}")
            st.info("Execute o app.py primeiro para criar o banco de dados")
            st.stop()
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Verifica tabelas existentes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['agent_state', 'archetype_conflicts', 'development_milestones']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            st.error(f"❌ Tabelas faltando: {', '.join(missing_tables)}")
            st.info("Execute o app.py primeiro para criar a estrutura do banco")
            conn.close()
            st.stop()
        
        # Verifica colunas da agent_state
        cursor.execute("PRAGMA table_info(agent_state)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'user_id_hash' not in columns:
            st.error("❌ Estrutura do banco desatualizada!")
            st.info("Execute: python fix_database.py")
            conn.close()
            st.stop()
        
        conn.close()
    
    def get_all_user_hashes(self) -> List[str]:
        """Retorna todos os user_id_hash no sistema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT user_id_hash FROM agent_state ORDER BY created_at DESC")
        hashes = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return hashes
    
    def get_agent_state(self, user_id_hash: str) -> Optional[Dict]:
        """Retorna estado do agente para um usuário"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM agent_state WHERE user_id_hash = ?
        """, (user_id_hash,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_all_users_summary(self) -> List[Dict]:
        """Retorna resumo de todos os usuários"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM agent_state 
            ORDER BY total_interactions DESC
        """)
        
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return users
    
    def get_conflicts(self, user_id_hash: str = None, limit: int = 50) -> List[Dict]:
        """Retorna conflitos (opcionalmente filtrados por usuário)"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if user_id_hash:
            cursor.execute("""
                SELECT * FROM archetype_conflicts 
                WHERE user_id_hash = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (user_id_hash, limit))
        else:
            cursor.execute("""
                SELECT * FROM archetype_conflicts 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
        
        conflicts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return conflicts
    
    def get_milestones(self, user_id_hash: str = None, limit: int = 20) -> List[Dict]:
        """Retorna milestones (opcionalmente filtrados por usuário)"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if user_id_hash:
            cursor.execute("""
                SELECT * FROM development_milestones 
                WHERE user_id_hash = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (user_id_hash, limit))
        else:
            cursor.execute("""
                SELECT * FROM development_milestones 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
        
        milestones = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return milestones
    
    def get_development_stats(self, user_id_hash: str) -> Dict:
        """Retorna estatísticas de desenvolvimento"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Total de conflitos
        cursor.execute("""
            SELECT COUNT(*) FROM archetype_conflicts WHERE user_id_hash = ?
        """, (user_id_hash,))
        total_conflicts = cursor.fetchone()[0]
        
        # Arquétipo dominante
        cursor.execute("""
            SELECT winner, COUNT(*) as wins 
            FROM archetype_conflicts 
            WHERE user_id_hash = ?
            GROUP BY winner 
            ORDER BY wins DESC 
            LIMIT 1
        """, (user_id_hash,))
        
        dominant = cursor.fetchone()
        dominant_archetype = dominant[0] if dominant else "N/A"
        dominant_wins = dominant[1] if dominant else 0
        
        # Total de milestones
        cursor.execute("""
            SELECT COUNT(*) FROM development_milestones WHERE user_id_hash = ?
        """, (user_id_hash,))
        total_milestones = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_conflicts': total_conflicts,
            'dominant_archetype': dominant_archetype,
            'dominant_wins': dominant_wins,
            'total_milestones': total_milestones
        }

# ============================================================================
# GERENCIADOR DE DADOS (CHROMADB)
# ============================================================================

class ChromaManager:
    """Gerencia operações com ChromaDB"""
    
    def __init__(self):
        self.available = False
        self.collection = None
        
        try:
            if not AdminConfig.CHROMA_DIR.exists():
                st.warning(f"⚠️ Diretório ChromaDB não encontrado: {AdminConfig.CHROMA_DIR}")
                return
            
            self.client = chromadb.PersistentClient(path=str(AdminConfig.CHROMA_DIR))
            
            # Tenta acessar a coleção
            try:
                self.collection = self.client.get_collection(name="langchain")
                self.available = True
            except:
                st.warning("⚠️ Coleção 'langchain' não encontrada no ChromaDB")
                return
                
        except Exception as e:
            st.warning(f"⚠️ Erro ao conectar ChromaDB: {e}")
    
    def get_all_users(self) -> List[Dict]:
        """Retorna lista de todos os usuários no ChromaDB"""
        if not self.available:
            return []
        
        try:
            all_docs = self.collection.get()
            users_data = {}
            
            for metadata in all_docs.get('metadatas', []):
                user_id = metadata.get('user_id')
                user_name = metadata.get('user_name', user_id)
                
                if user_id:
                    user_hash = get_user_hash(user_id)
                    
                    if user_hash not in users_data:
                        users_data[user_hash] = {
                            'user_id': user_id,
                            'user_id_hash': user_hash,
                            'user_name': user_name,
                            'interaction_count': 0
                        }
                    users_data[user_hash]['interaction_count'] += 1
            
            return list(users_data.values())
            
        except Exception as e:
            st.error(f"❌ Erro ao buscar usuários do ChromaDB: {e}")
            return []
    
    def get_user_memories(self, user_id: str) -> List[Dict]:
        """Retorna memórias de um usuário específico"""
        if not self.available:
            return []
        
        try:
            results = self.collection.get(
                where={"user_id": user_id},
                include=["documents", "metadatas"]
            )
            
            memories = []
            for doc, metadata in zip(results.get('documents', []), results.get('metadatas', [])):
                memories.append({
                    'content': doc,
                    'metadata': metadata
                })
            
            # Ordenar por timestamp se disponível
            memories.sort(key=lambda m: m['metadata'].get('timestamp', ''), reverse=False)
            
            return memories
            
        except Exception as e:
            st.error(f"❌ Erro ao buscar memórias: {e}")
            return []
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Retorna estatísticas de um usuário"""
        memories = self.get_user_memories(user_id)
        
        if not memories:
            return {
                'total_interactions': 0,
                'avg_length': 0,
                'keywords': [],
                'avg_tension': 0.0,
                'avg_affective_charge': 0.0,
                'avg_existential_depth': 0.0
            }
        
        total = len(memories)
        avg_length = sum(len(m['content']) for m in memories) / total if total > 0 else 0
        
        all_keywords = []
        tension_levels = []
        affective_charges = []
        existential_depths = []
        
        for m in memories:
            metadata = m['metadata']
            
            keywords = metadata.get('keywords', '')
            if keywords:
                all_keywords.extend(keywords.split(','))
            
            if 'tension_level' in metadata:
                try:
                    tension_levels.append(float(metadata['tension_level']))
                except:
                    pass
            
            if 'affective_charge' in metadata:
                try:
                    affective_charges.append(float(metadata['affective_charge']))
                except:
                    pass
            
            if 'existential_depth' in metadata:
                try:
                    existential_depths.append(float(metadata['existential_depth']))
                except:
                    pass
        
        keyword_counter = Counter(all_keywords)
        top_keywords = [k.strip() for k, _ in keyword_counter.most_common(10) if k.strip()]
        
        return {
            'total_interactions': total,
            'avg_length': int(avg_length),
            'keywords': top_keywords,
            'avg_tension': sum(tension_levels) / len(tension_levels) if tension_levels else 0.0,
            'avg_affective_charge': sum(affective_charges) / len(affective_charges) if affective_charges else 0.0,
            'avg_existential_depth': sum(existential_depths) / len(existential_depths) if existential_depths else 0.0
        }

# ============================================================================
# ANALISADOR JUNGUIANO
# ============================================================================

class JungianAnalyzer:
    """Análise junguiana via Grok"""
    
    def __init__(self):
        self.available = False
        
        if AdminConfig.XAI_API_KEY:
            try:
                self.client = OpenAI(
                    api_key=AdminConfig.XAI_API_KEY,
                    base_url="https://api.x.ai/v1"
                )
                self.available = True
            except:
                pass
    
    def analyze_user(self, user_stats: Dict, memories: List[Dict]) -> Dict:
        """Análise psicológica completa"""
        
        if not self.available or not memories:
            return self._fallback_analysis()
        
        # Extrai inputs do usuário
        user_inputs = []
        for memory in memories[:30]:
            content = memory['content']
            match = re.search(r"Input:\s*(.+?)(?:\n|Arquétipos:|$)", content, re.DOTALL)
            if match:
                user_input = match.group(1).strip()
                if user_input:
                    user_inputs.append(user_input)
        
        if not user_inputs:
            return self._fallback_analysis()
        
        # Monta prompt
        sample_size = min(15, len(user_inputs))
        first_inputs = user_inputs[:sample_size // 2]
        last_inputs = user_inputs[-(sample_size // 2):] if len(user_inputs) > sample_size // 2 else []
        
        inputs_text = "**Mensagens Iniciais:**\n"
        inputs_text += "\n".join([f"- {inp[:120]}..." for inp in first_inputs])
        
        if last_inputs:
            inputs_text += "\n\n**Mensagens Recentes:**\n"
            inputs_text += "\n".join([f"- {inp[:120]}..." for inp in last_inputs])
        
        prompt = f"""
Analise o padrão psicológico deste usuário seguindo princípios junguianos.

**ESTATÍSTICAS:**
- Total de interações: {user_stats['total_interactions']}
- Comprimento médio: {user_stats['avg_length']} caracteres
- Tensão média: {user_stats['avg_tension']:.2f}/10
- Carga afetiva média: {user_stats['avg_affective_charge']:.1f}/100
- Profundidade existencial: {user_stats['avg_existential_depth']:.2f}
- Palavras-chave: {', '.join(user_stats['keywords'][:10])}

**MENSAGENS DO USUÁRIO:**
{inputs_text}

Retorne JSON com esta estrutura:
{{
    "type_indicator": "XXXX (ex: INFP)",
    "confidence": 0-100,
    "dimensions": {{
        "E_I": {{
            "score": -100 a +100 (negativo=E, positivo=I),
            "interpretation": "Análise com evidências",
            "key_indicators": ["indicador1", "indicador2"]
        }},
        "S_N": {{"score": -100 a +100, "interpretation": "...", "key_indicators": [...]}},
        "T_F": {{"score": -100 a +100, "interpretation": "...", "key_indicators": [...]}},
        "J_P": {{"score": -100 a +100, "interpretation": "...", "key_indicators": [...]}}
    }},
    "dominant_function": "Ex: Ni (Intuição Introvertida)",
    "auxiliary_function": "Ex: Fe",
    "summary": "Resumo analítico",
    "potentials": ["potencial1", "potencial2"],
    "challenges": ["desafio1", "desafio2"],
    "recommendations": ["recomendação1", "recomendação2"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="grok-4-fast-reasoning",
                messages=[
                    {"role": "system", "content": "Você é um analista jungiano. Responda APENAS com JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            # Adiciona labels de espectro
            if 'dimensions' in analysis:
                for dim_key in ['E_I', 'S_N', 'T_F', 'J_P']:
                    if dim_key in analysis['dimensions']:
                        score = analysis['dimensions'][dim_key].get('score', 0)
                        analysis['dimensions'][dim_key]['spectrum_label'] = interpret_spectrum_score(score)
            
            return analysis
            
        except Exception as e:
            st.warning(f"⚠️ Erro na análise Grok: {e}")
            return self._fallback_analysis()
    
    def _fallback_analysis(self) -> Dict:
        """Análise padrão quando API não disponível"""
        return {
            "type_indicator": "XXXX",
            "confidence": 0,
            "dimensions": {
                "E_I": {"score": 0, "interpretation": "Dados insuficientes", "spectrum_label": "Indefinido", "key_indicators": []},
                "S_N": {"score": 0, "interpretation": "Dados insuficientes", "spectrum_label": "Indefinido", "key_indicators": []},
                "T_F": {"score": 0, "interpretation": "Dados insuficientes", "spectrum_label": "Indefinido", "key_indicators": []},
                "J_P": {"score": 0, "interpretation": "Dados insuficientes", "spectrum_label": "Indefinido", "key_indicators": []}
            },
            "dominant_function": "Indeterminado",
            "auxiliary_function": "Indeterminado",
            "summary": "Análise não disponível - API não configurada ou dados insuficientes",
            "potentials": [],
            "challenges": [],
            "recommendations": ["Configure XAI_API_KEY para análise completa"]
        }

# ============================================================================
# DASHBOARD PRINCIPAL
# ============================================================================

class AdminDashboard:
    """Dashboard administrativo"""
    
    def __init__(self):
        self.sqlite_db = SQLiteManager()
        self.chroma_db = ChromaManager()
        self.analyzer = JungianAnalyzer()
        
        st.set_page_config(
            page_title="Jung Claude Admin",
            page_icon="🧠",
            layout="wide"
        )
    
    def render(self):
        st.title("🧠 Jung Claude - Analytics Dashboard")
        st.caption("Sistema Híbrido: ChromaDB + SQLite")
        
        # Tabs principais
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Visão Geral",
            "👥 Perfis Detalhados",
            "⚡ Conflitos",
            "🏆 Milestones"
        ])
        
        with tab1:
            self._render_overview()
        
        with tab2:
            self._render_profiles()
        
        with tab3:
            self._render_conflicts()
        
        with tab4:
            self._render_milestones()
    
    def _render_overview(self):
        """Visão geral do sistema"""
        st.header("📊 Visão Geral do Sistema")
        
        # Buscar dados
        sqlite_users = self.sqlite_db.get_all_users_summary()
        chroma_users = self.chroma_db.get_all_users()
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Usuários (SQLite)", len(sqlite_users))
        
        with col2:
            st.metric("💬 Usuários (ChromaDB)", len(chroma_users))
        
        with col3:
            total_interactions = sum(u['total_interactions'] for u in sqlite_users)
            st.metric("🔄 Interações Totais", total_interactions)
        
        with col4:
            if chroma_users:
                total_memories = sum(u['interaction_count'] for u in chroma_users)
                st.metric("🧠 Memórias Totais", total_memories)
            else:
                st.metric("🧠 Memórias Totais", 0)
        
        st.divider()
        
        # Ranking de usuários
        if sqlite_users:
            st.subheader("🏆 Ranking de Desenvolvimento")
            
            for i, user in enumerate(sqlite_users[:10], 1):
                user_hash = user['user_id_hash']
                
                # Buscar nome no ChromaDB
                user_name = "Desconhecido"
                for cu in chroma_users:
                    if cu['user_id_hash'] == user_hash:
                        user_name = cu['user_name']
                        break
                
                phase_name = AdminConfig.DEVELOPMENT_PHASES.get(user['phase'], 'N/A')
                
                with st.expander(f"#{i} - {user_name} | Fase: {phase_name}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Fase", f"{user['phase']}/5")
                        st.metric("Interações", user['total_interactions'])
                    
                    with col2:
                        st.metric("Auto-consciência", f"{user['self_awareness_score']:.1%}")
                        st.metric("Complexidade Moral", f"{user['moral_complexity_score']:.1%}")
                    
                    with col3:
                        st.metric("Prof. Emocional", f"{user['emotional_depth_score']:.1%}")
                        st.metric("Autonomia", f"{user['autonomy_score']:.1%}")
                    
                    if user.get('last_updated'):
                        st.caption(f"Última atualização: {user['last_updated'][:16]}")
        else:
            st.info("📊 Nenhum usuário encontrado no sistema")
    
    def _render_profiles(self):
        """Perfis detalhados dos usuários"""
        st.header("👥 Perfis Psicológicos Detalhados")
        
        # Buscar usuários do ChromaDB
        chroma_users = self.chroma_db.get_all_users()
        
        if not chroma_users:
            st.warning("⚠️ Nenhum usuário encontrado no ChromaDB")
            return
        
        # Seletor de usuário
        user_options = {
            f"{u['user_name']} ({u['interaction_count']} memórias)": u 
            for u in chroma_users
        }
        
        selected_display = st.selectbox("Selecione um usuário:", list(user_options.keys()))
        selected_user = user_options[selected_display]
        
        user_id = selected_user['user_id']
        user_hash = selected_user['user_id_hash']
        
        st.divider()
        
        # Dados SQLite
        agent_state = self.sqlite_db.get_agent_state(user_hash)
        
        if not agent_state:
            st.warning(f"⚠️ Usuário {selected_user['user_name']} não tem dados no SQLite")
            return
        
        # Seção: Desenvolvimento
        st.subheader("🤖 Desenvolvimento do Agente")
        
        phase_name = AdminConfig.DEVELOPMENT_PHASES.get(agent_state['phase'], 'N/A')
        st.write(f"**Fase Atual:** {phase_name} ({agent_state['phase']}/5)")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Interações (SQLite)", agent_state['total_interactions'])
        
        with col2:
            st.metric("Auto-consciência", f"{agent_state['self_awareness_score']:.1%}")
            st.progress(agent_state['self_awareness_score'])
        
        with col3:
            st.metric("Complexidade Moral", f"{agent_state['moral_complexity_score']:.1%}")
            st.progress(agent_state['moral_complexity_score'])
        
        with col4:
            st.metric("Prof. Emocional", f"{agent_state['emotional_depth_score']:.1%}")
            st.progress(agent_state['emotional_depth_score'])
        
        st.metric("Autonomia", f"{agent_state['autonomy_score']:.1%}")
        st.progress(agent_state['autonomy_score'])
        
        st.divider()
        
        # Estatísticas de desenvolvimento
        stats = self.sqlite_db.get_development_stats(user_hash)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Conflitos", stats['total_conflicts'])
        
        with col2:
            st.metric("Arquétipo Dominante", stats['dominant_archetype'].title())
        
        with col3:
            st.metric("Total de Milestones", stats['total_milestones'])
        
        st.divider()
        
        # Dados ChromaDB
        st.subheader("🧠 Análise de Memórias")
        
        chroma_stats = self.chroma_db.get_user_stats(user_id)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Memórias (ChromaDB)", chroma_stats['total_interactions'])
            st.metric("Comp. Médio", f"{chroma_stats['avg_length']} chars")
        
        with col2:
            st.metric("Tensão Média", f"{chroma_stats['avg_tension']:.1f}/10")
            st.metric("Carga Afetiva", f"{chroma_stats['avg_affective_charge']:.0f}/100")
        
        with col3:
            st.metric("Prof. Existencial", f"{chroma_stats['avg_existential_depth']:.2f}")
        
        if chroma_stats['keywords']:
            st.write("**Palavras-chave:**", ", ".join(chroma_stats['keywords']))
        
        st.divider()
        
        # ========================================
        # ✅ CORREÇÃO: Diagnóstico de Sincronização
        # ========================================
        with st.expander("🔍 Diagnóstico de Sincronização de Dados"):
            st.write("**Verificação de Consistência entre SQLite e ChromaDB:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**SQLite (agent_state):**")
                st.json({
                    'user_id_hash': user_hash[:16] + '...',
                    'total_interactions': agent_state['total_interactions'],
                    'phase': agent_state['phase'],
                    'last_updated': agent_state.get('last_updated', 'N/A')[:19] if agent_state.get('last_updated') else 'N/A'
                })
            
            with col2:
                st.write("**ChromaDB:**")
                memories = self.chroma_db.get_user_memories(user_id)
                st.json({
                    'user_id': user_id,
                    'total_memories': len(memories),
                    'has_timestamps': all('timestamp' in m['metadata'] for m in memories) if memories else False,
                    'sample_metadata': memories[0]['metadata'] if memories else {}
                })
            
            # ✅ Análise de descasamento
            sqlite_count = agent_state['total_interactions']
            chroma_count = len(memories)
            
            if sqlite_count != chroma_count:
                diff = abs(sqlite_count - chroma_count)
                st.warning(f"""
                ⚠️ **Descasamento detectado!**
                
                - SQLite registrou **{sqlite_count}** interações
                - ChromaDB possui **{chroma_count}** memórias
                - Diferença: **{diff}** registros
                
                **Possíveis causas:**
                1. Memórias sendo armazenadas apenas parcialmente no ChromaDB
                2. Erro no processo de sincronização
                3. Interações registradas no SQLite sem análise arquetípica completa
                
                **Solução:**
                Para análise psicológica, o sistema usa as **memórias do ChromaDB** 
                (que contêm o contexto completo das conversas).
                """)
            else:
                st.success(f"✅ Dados sincronizados: {sqlite_count} registros em ambas as fontes")
        
        st.divider()
        
        # ========================================
        # ✅ CORREÇÃO: Análise Jungiana (usa ChromaDB)
        # ========================================
        st.subheader("🧠 Análise Psicológica Jungiana")
        
        # ✅ USA MEMÓRIAS DO CHROMADB, NÃO SQLITE
        total_memories = chroma_stats['total_interactions']
        
        # Mostrar ambas as contagens
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Interações (SQLite)", agent_state['total_interactions'])
        
        with col2:
            st.metric("Memórias (ChromaDB)", total_memories, 
                     help="A análise usa memórias do ChromaDB (contexto completo)")
        
        # ✅ Validação baseada em memórias ChromaDB
        if total_memories < AdminConfig.MIN_INTERACTIONS_FOR_ANALYSIS:
            missing = AdminConfig.MIN_INTERACTIONS_FOR_ANALYSIS - total_memories
            
            st.warning(f"""
            ⚠️ **Memórias insuficientes para análise psicológica**
            
            Para análise junguiana rigorosa, são necessárias **{AdminConfig.MIN_INTERACTIONS_FOR_ANALYSIS} memórias** 
            no sistema de busca semântica (ChromaDB).
            
            **Status atual:**
            - 💾 SQLite (rastreamento): {agent_state['total_interactions']} interações
            - 🧠 ChromaDB (memórias completas): {total_memories} memórias
            - ⚠️ Faltam: **{missing}** memórias
            
            💡 **Por que pode haver diferença?**
            O SQLite rastreia *qualquer* interação (incluindo simples "oi" ou "tchau"), 
            enquanto o ChromaDB armazena apenas memórias completas com análise arquetípica 
            profunda (conversas substantivas).
            
            **O que fazer:**
            Continue conversando com o sistema. Cada conversa significativa adiciona 
            memórias ao ChromaDB.
            """)
        else:
            st.success(f"✅ Dados suficientes para análise ({total_memories} memórias disponíveis)")
            
            if st.button("🔍 Realizar Análise Jungiana Completa", use_container_width=True, type="primary"):
                with st.spinner("Analisando padrões psicológicos profundos..."):
                    memories = self.chroma_db.get_user_memories(user_id)
                    
                    if not memories:
                        st.error("❌ Erro ao carregar memórias do ChromaDB")
                    else:
                        analysis = self.analyzer.analyze_user(chroma_stats, memories)
                        self._display_jungian_analysis(analysis)
    
    def _display_jungian_analysis(self, analysis: Dict):
        """Exibe análise jungiana"""
        
        st.success("✅ Análise concluída!")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Tipo MBTI", analysis.get('type_indicator', 'XXXX'))
        
        with col2:
            st.metric("Confiança", f"{analysis.get('confidence', 0)}%")
        
        with col3:
            st.metric("Função Dominante", analysis.get('dominant_function', 'N/A'))
        
        st.divider()
        
        # Dimensões
        st.subheader("📐 Análise das Dimensões")
        
        dimensions = analysis.get('dimensions', {})
        
        for dim_key, dim_data in dimensions.items():
            score = dim_data.get('score', 0)
            spectrum = dim_data.get('spectrum_label', 'Indefinido')
            
            # Labels
            labels = {
                'E_I': ('E (Extroversão)', 'I (Introversão)'),
                'S_N': ('S (Sensação)', 'N (Intuição)'),
                'T_F': ('T (Pensamento)', 'F (Sentimento)'),
                'J_P': ('J (Julgamento)', 'P (Percepção)')
            }
            
            neg_label, pos_label = labels.get(dim_key, ('Neg', 'Pos'))
            
            st.markdown(f"**{dim_key}: {spectrum}**")
            
            # Barra de progresso
            normalized = (score + 100) / 200
            st.progress(normalized)
            
            # Indicador
            if score < -60:
                tendency = f"✅ {neg_label} (Score: {score})"
            elif score < -20:
                tendency = f"↗️ Tendência {neg_label} (Score: {score})"
            elif score <= 20:
                tendency = f"⚖️ Indefinido (Score: {score})"
            elif score <= 60:
                tendency = f"↗️ Tendência {pos_label} (Score: {score})"
            else:
                tendency = f"✅ {pos_label} (Score: {score})"
            
            st.caption(tendency)
            
            with st.expander(f"Ver detalhes de {dim_key}"):
                st.write(dim_data.get('interpretation', 'Sem análise'))
                
                if dim_data.get('key_indicators'):
                    st.write("**Evidências:**")
                    for indicator in dim_data['key_indicators']:
                        st.write(f"• {indicator}")
        
        st.divider()
        
        # Resumo
        st.subheader("📝 Síntese")
        st.write(analysis.get('summary', 'Sem resumo disponível'))
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🌟 Potenciais:**")
            for pot in analysis.get('potentials', []):
                st.write(f"✅ {pot}")
        
        with col2:
            st.markdown("**⚠️ Desafios:**")
            for chall in analysis.get('challenges', []):
                st.write(f"⚡ {chall}")
        
        if analysis.get('recommendations'):
            st.divider()
            st.markdown("**💡 Recomendações:**")
            for rec in analysis['recommendations']:
                st.write(f"→ {rec}")
    
    def _render_conflicts(self):
        """Visualização de conflitos"""
        st.header("⚡ Conflitos Arquetípicos")
        
        # Buscar usuários
        chroma_users = self.chroma_db.get_all_users()
        
        if not chroma_users:
            st.warning("⚠️ Nenhum usuário encontrado")
            return
        
        # Seletor
        user_options = {
            f"{u['user_name']} ({u['interaction_count']} interações)": u 
            for u in chroma_users
        }
        user_options["[TODOS OS USUÁRIOS]"] = None
        
        selected_display = st.selectbox("Filtrar por usuário:", list(user_options.keys()), key="conflicts_user")
        selected_user = user_options[selected_display]
        
        user_hash = selected_user['user_id_hash'] if selected_user else None
        
        limit = st.slider("Número de conflitos:", 10, 100, 30, key="conflicts_limit")
        
        st.divider()
        
        # Buscar conflitos
        conflicts = self.sqlite_db.get_conflicts(user_hash, limit)
        
        if conflicts:
            st.caption(f"Exibindo {len(conflicts)} conflitos")
            
            for i, c in enumerate(conflicts, 1):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    winner = c.get('winner', 'N/A').title()
                    loser = c.get('loser', 'N/A').title()
                    
                    st.markdown(f"**#{i} | {winner}** ⚔️ **{loser}**")
                    
                    if c.get('resolution'):
                        st.write(f"_{c['resolution'][:150]}..._")
                    
                    if c.get('user_message'):
                        with st.expander("Ver contexto"):
                            st.write(c['user_message'])
                
                with col2:
                    st.metric("Tensão", f"{c.get('intensity', 0):.2f}")
                    timestamp = c.get('timestamp', 'N/A')
                    if timestamp != 'N/A':
                        timestamp = timestamp[:16]
                    st.caption(f"🕒 {timestamp}")
                
                st.markdown("---")
        else:
            st.info("😇 Nenhum conflito registrado")
    
    def _render_milestones(self):
        """Visualização de milestones"""
        st.header("🏆 Milestones de Desenvolvimento")
        
        # Buscar usuários
        chroma_users = self.chroma_db.get_all_users()
        
        if not chroma_users:
            st.warning("⚠️ Nenhum usuário encontrado")
            return
        
        # Seletor
        user_options = {
            f"{u['user_name']} ({u['interaction_count']} interações)": u 
            for u in chroma_users
        }
        user_options["[TODOS OS USUÁRIOS]"] = None
        
        selected_display = st.selectbox("Filtrar por usuário:", list(user_options.keys()), key="milestones_user")
        selected_user = user_options[selected_display]
        
        user_hash = selected_user['user_id_hash'] if selected_user else None
        
        limit = st.slider("Número de milestones:", 10, 50, 20, key="milestones_limit")
        
        st.divider()
        
        # Buscar milestones
        milestones = self.sqlite_db.get_milestones(user_hash, limit)
        
        if milestones:
            st.caption(f"Exibindo {len(milestones)} milestones")
            
            for i, m in enumerate(milestones, 1):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    milestone_type = m.get('milestone_type', 'N/A').replace('_', ' ').title()
                    st.markdown(f"**#{i} | {milestone_type}**")
                    st.write(f"_{m.get('description', 'Sem descrição')}_")
                
                with col2:
                    st.metric("Fase", m.get('phase', 'N/A'))
                    timestamp = m.get('timestamp', 'N/A')
                    if timestamp != 'N/A':
                        timestamp = timestamp[:16]
                    st.caption(f"🕒 {timestamp}")
                
                st.markdown("---")
        else:
            st.info("🌱 Nenhum milestone registrado ainda")

# ============================================================================
# MAIN
# ============================================================================

def main():
    if not ANALYTICS_AVAILABLE:
        st.error("❌ Módulos necessários não disponíveis!")
        st.info("Instale: pip install openai chromadb")
        st.stop()
    
    dashboard = AdminDashboard()
    dashboard.render()

if __name__ == "__main__":
    main()