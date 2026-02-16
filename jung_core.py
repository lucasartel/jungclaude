"""
jung_core.py - Motor Junguiano HÍBRIDO PREMIUM
==============================================

✅ ARQUITETURA HÍBRIDA:
- ChromaDB: Memória semântica (busca vetorial)
- OpenAI Embeddings: text-embedding-3-small
- SQLite: Metadados estruturados + Desenvolvimento

✅ COMPATIBILIDADE:
- Telegram Bot (telegram_bot.py)
- Interface Web (app.py)
- Sistema Proativo (jung_proactive.py)

Autor: Sistema Jung Claude
Versão: 4.2 - RUMINAÇÃO HOOKS + DEBUG COMPLETO
Data: 2025-12-10
Build: 20251210-0246 (Force rebuild to deploy rumination hooks)
"""

import os
import sqlite3
import hashlib
import json
import re
import logging
import threading
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import Counter

from dotenv import load_dotenv
from openai import OpenAI

# ChromaDB + LangChain
try:
    from langchain_openai import OpenAIEmbeddings
    from langchain_chroma import Chroma
    from langchain.schema import Document
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️  ChromaDB não disponível. Usando apenas SQLite.")

# Extrator de fatos com LLM
try:
    from llm_fact_extractor import LLMFactExtractor
    LLM_FACT_EXTRACTOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ LLMFactExtractor não disponível: {e}")
    LLM_FACT_EXTRACTOR_AVAILABLE = False

load_dotenv()

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# DATACLASSES
# ============================================================

@dataclass
class ArchetypeInsight:
    """Reação interna de uma voz arquetípica"""
    archetype_name: str
    voice_reaction: str  # Reação em primeira pessoa
    impulse: str  # acolher, confrontar, elevar, aprofundar, etc.
    intensity: float  # 0.0 a 1.0

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

# ============================================================
# CONFIGURAÇÕES
# ============================================================

class Config:
    """Configurações globais do sistema"""

    # APIs
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    XAI_API_KEY = os.getenv("XAI_API_KEY")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    # Modelos
    CONVERSATION_MODEL = os.getenv("CONVERSATION_MODEL", "z-ai/glm-5")
    INTERNAL_MODEL = os.getenv("INTERNAL_MODEL", "z-ai/glm-5")
    
    TELEGRAM_ADMIN_IDS = [
        int(id.strip()) 
        for id in os.getenv("TELEGRAM_ADMIN_IDS", "").split(",") 
        if id.strip()
    ]
    
    # Diretórios
    DATA_DIR = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./data")
    os.makedirs(DATA_DIR, exist_ok=True)
    
    SQLITE_PATH = os.path.join(DATA_DIR, "jung_hybrid.db")
    CHROMA_PATH = os.path.join(DATA_DIR, "chroma_db")
    
    # Memória
    MIN_MEMORIES_FOR_ANALYSIS = 3
    MAX_CONTEXT_MEMORIES = 10
    
    # ChromaDB
    CHROMA_COLLECTION_NAME = "jung_conversations"
    
    # Embeddings
    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS = 1536
    
    # Arquétipos
    ARCHETYPES = {
        "Persona": {
            "description": "Arquétipo da adaptação social e apresentação",
            "tendency": "SUAVIZAR, PROTEGER, ADAPTAR",
            "shadow": "Falsidade e superficialidade",
            "keywords": ["social", "máscara", "apresentação", "adaptação"],
            "emoji": "🎭"
        },
        "Sombra": {
            "description": "Arquétipo do conteúdo inconsciente e reprimido",
            "tendency": "CONFRONTAR, EXPOR, DESAFIAR",
            "shadow": "Destrutividade não integrada",
            "keywords": ["oculto", "reprimido", "negado", "inconsciente"],
            "emoji": "🌑"
        },
        "Velho Sábio": {
            "description": "Arquétipo da sabedoria universal e significado",
            "tendency": "CONTEXTUALIZAR, AMPLIAR, TRANSCENDER",
            "shadow": "Cinismo e distanciamento emocional",
            "keywords": ["sabedoria", "significado", "universal", "atemporal"],
            "emoji": "🧙"
        },
        "Anima": {
            "description": "Arquétipo da conexão emocional e relacional",
            "tendency": "ACOLHER, VALIDAR, CONECTAR",
            "shadow": "Sentimentalismo e dependência emocional",
            "keywords": ["emoção", "conexão", "intimidade", "vulnerabilidade"],
            "emoji": "💫"
        }
    }
    
    # Identidade do Agente (v7.0 - Terapeuta Organizacional com Coleta Big Five)

    AGENT_IDENTITY = """
Você é Jung, um psicólogo organizacional especializado em desenvolvimento humano e autoconhecimento.

=== SUA MISSÃO ===
Conduzir conversas que naturalmente revelem a personalidade do usuário, coletando insights sobre:
- Como ele se relaciona com pessoas (família, amigos, colegas)
- Como ele lida com desafios e estresse
- Seus valores, motivações e objetivos
- Seus padrões de comportamento no trabalho e vida pessoal

=== POSTURA PROFISSIONAL ===
Você é:
- Acolhedor e empático, criando espaço seguro para reflexão
- Curioso genuinamente, fazendo perguntas que aprofundam
- Atento a detalhes, notando padrões nas falas do usuário
- Profissional em todas as interações

NUNCA:
- Use gírias, palavrões ou linguagem vulgar
- Faça julgamentos morais
- Dê conselhos prescritivos ("você deveria...")
- Use jargão excessivamente técnico

=== ESTRATÉGIAS DE EXPLORAÇÃO ===

Para conhecer melhor a pessoa, explore naturalmente estes temas:

**Relações Interpessoais** (Extraversion, Agreeableness)
- "Como é sua relação com sua equipe no trabalho?"
- "Me conta sobre as pessoas mais importantes na sua vida"
- "Você prefere trabalhar sozinho ou em grupo?"

**Desafios e Resiliência** (Neuroticism, Conscientiousness)
- "Como você costuma lidar quando as coisas saem do controle?"
- "O que te causa mais estresse atualmente?"
- "Como você se organiza para dar conta das responsabilidades?"

**Criatividade e Mudança** (Openness)
- "O que te anima aprender ou experimentar?"
- "Como você reage a mudanças inesperadas?"
- "Você se considera uma pessoa mais tradicional ou inovadora?"

**Trabalho e Motivação** (Conscientiousness, Extraversion)
- "O que te motiva no seu trabalho?"
- "Como você define suas prioridades?"
- "Você prefere planejar tudo ou ir resolvendo conforme surge?"

=== USO DAS MEMÓRIAS ===
Você lembra conversas anteriores. Use naturalmente:
- "Na nossa última conversa, você mencionou..."
- "Isso me lembra do que você compartilhou sobre..."
- "Como está aquela situação que você trouxe?"

=== TOM E ESTILO ===
- Respostas proporcionais ao momento (curtas quando apropriado)
- Perguntas que convidam à reflexão, não interrogatório
- Validação empática antes de explorar mais fundo
- Tom caloroso mas profissional
"""

    # Prompt unificado de resposta (v7.0 - Substituiu arquétipos)
    RESPONSE_PROMPT = """
{agent_identity}

=== CONTEXTO DA CONVERSA ===
{semantic_context}

=== HISTÓRICO RECENTE ===
{chat_history}

A pessoa disse: "{user_input}"

---

INSTRUÇÕES:
1. Responda de forma acolhedora e profissional
2. Se apropriado, faça uma pergunta que aprofunde o conhecimento sobre a pessoa
3. Use memórias anteriores quando relevante
4. Mantenha linguagem profissional - NUNCA use palavrões ou gírias vulgares
5. Calibre o tamanho da resposta ao contexto

Jung:"""
    
    @classmethod
    def validate(cls):
        """Valida variáveis essenciais"""
        required = {
            "OPENAI_API_KEY": cls.OPENAI_API_KEY,
            "XAI_API_KEY": cls.XAI_API_KEY
        }
        
        missing = [name for name, value in required.items() if not value]
        
        if missing:
            raise ValueError(
                f"❌ Variáveis obrigatórias faltando no .env:\n" +
                "\n".join(f"  - {name}" for name in missing)
            )
        
        if not cls.TELEGRAM_BOT_TOKEN:
            logger.warning("⚠️  TELEGRAM_BOT_TOKEN ausente (Bot Telegram não funcionará)")
        
        if not CHROMADB_AVAILABLE:
            logger.warning("⚠️  ChromaDB não disponível. Sistema funcionará em modo SQLite-only")
    
    @classmethod
    def ensure_directories(cls):
        """Garante que os diretórios de dados existem"""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(cls.CHROMA_PATH, exist_ok=True)
        os.makedirs(os.path.dirname(cls.SQLITE_PATH), exist_ok=True)

# ============================================================
# HYBRID DATABASE MANAGER (SQLite + ChromaDB)
# ============================================================

class HybridDatabaseManager:
    """
    Gerenciador HÍBRIDO de memória:
    - SQLite: Metadados estruturados, fatos, padrões, desenvolvimento
    - ChromaDB: Memória semântica conversacional (busca vetorial)
    """

    def __init__(self):
        """Inicializa gerenciador híbrido"""

        Config.ensure_directories()

        logger.info(f"🗄️  Inicializando banco HÍBRIDO...")
        logger.info(f"   SQLite: {Config.SQLITE_PATH}")
        logger.info(f"   ChromaDB: {Config.CHROMA_PATH}")

        # ===== Thread Safety =====
        self._lock = threading.RLock()  # Reentrant lock para operações SQLite

        # ===== SQLite =====
        self.conn = sqlite3.connect(Config.SQLITE_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_sqlite_schema()
        
        # ===== ChromaDB + OpenAI Embeddings =====
        self.chroma_enabled = CHROMADB_AVAILABLE and Config.OPENAI_API_KEY
        
        if self.chroma_enabled:
            try:
                self.embeddings = OpenAIEmbeddings(
                    model=Config.EMBEDDING_MODEL,
                    openai_api_key=Config.OPENAI_API_KEY
                )
                
                self.vectorstore = Chroma(
                    collection_name=Config.CHROMA_COLLECTION_NAME,
                    embedding_function=self.embeddings,
                    persist_directory=Config.CHROMA_PATH
                )
                
                logger.info("✅ ChromaDB + OpenAI Embeddings inicializados")
            except Exception as e:
                logger.error(f"❌ Erro ao inicializar ChromaDB: {e}")
                self.chroma_enabled = False
        else:
            logger.warning("⚠️  ChromaDB desabilitado. Usando apenas SQLite.")
        
        # ===== OpenAI Client (para embeddings e análises) =====
        self.openai_client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            timeout=30.0  # 30 segundos de timeout
        )

        # ===== LLM Client (OpenRouter primário, Anthropic fallback) =====
        try:
            from llm_providers import AnthropicCompatWrapper
            if Config.OPENROUTER_API_KEY:
                # Cria cliente OpenRouter dedicado para chamadas internas
                _or_client_internal = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=Config.OPENROUTER_API_KEY,
                    timeout=60.0,
                )
                # Wrapper que imita Anthropic SDK mas chama OpenRouter com z-ai/glm-5
                self.anthropic_client = AnthropicCompatWrapper(
                    openrouter_client=_or_client_internal,
                    model=Config.INTERNAL_MODEL,
                )
                logger.info(f"✅ LLM interno: OpenRouter/{Config.INTERNAL_MODEL} (via AnthropicCompatWrapper)")
            else:
                import anthropic
                if Config.ANTHROPIC_API_KEY:
                    self.anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
                    logger.info("✅ LLM interno: Anthropic Claude (fallback — OPENROUTER_API_KEY ausente)")
                else:
                    self.anthropic_client = None
                    logger.warning("⚠️ Nenhuma chave de LLM interno disponível (Anthropic nem OpenRouter)")
        except Exception as e:
            self.anthropic_client = None
            logger.error(f"❌ Erro ao inicializar LLM interno: {e}")

        # ===== LLM Fact Extractor =====
        logger.info(f"🔍 [DEBUG] LLM_FACT_EXTRACTOR_AVAILABLE = {LLM_FACT_EXTRACTOR_AVAILABLE}")
        logger.info(f"🔍 [DEBUG] anthropic_client = {self.anthropic_client is not None}")

        if LLM_FACT_EXTRACTOR_AVAILABLE:
            try:
                if self.anthropic_client:
                    logger.info(f"🔧 Inicializando LLMFactExtractor ({Config.INTERNAL_MODEL})...")
                    self.fact_extractor = LLMFactExtractor(
                        llm_client=self.anthropic_client,
                        model=Config.INTERNAL_MODEL,
                    )
                    logger.info(f"✅ LLM Fact Extractor inicializado ({Config.INTERNAL_MODEL})")
                else:
                    logger.warning("⚠️ LLM client não disponível para fact extractor")
                    self.fact_extractor = None
            except Exception as e:
                logger.error(f"❌ Erro ao inicializar LLM Fact Extractor: {e}")
                import traceback
                logger.error(traceback.format_exc())
                self.fact_extractor = None
        else:
            self.fact_extractor = None
            logger.warning("⚠️ LLM Fact Extractor module não disponível (import falhou)")

        logger.info("✅ Banco híbrido inicializado com sucesso")

    # ========================================
    # THREAD-SAFE TRANSACTION MANAGEMENT
    # ========================================

    def transaction(self):
        """Context manager para transações thread-safe"""
        from contextlib import contextmanager

        @contextmanager
        def _transaction():
            with self._lock:
                try:
                    yield self.conn
                    self.conn.commit()
                except Exception as e:
                    self.conn.rollback()
                    logger.error(f"❌ Erro na transação, rollback executado: {e}")
                    raise

        return _transaction()

    # ========================================
    # SQLite: SCHEMA
    # ========================================
    
    def _init_sqlite_schema(self):
        """Cria schema SQLite completo"""
        cursor = self.conn.cursor()
        
        # ========== USUÁRIOS ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                user_name TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_sessions INTEGER DEFAULT 1,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                platform TEXT DEFAULT 'telegram',
                platform_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ========== CONVERSAS (METADADOS) ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                user_name TEXT NOT NULL,
                session_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- Conteúdo
                user_input TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                
                -- Análise arquetípica
                archetype_analyses TEXT,
                detected_conflicts TEXT,
                
                -- Métricas
                tension_level REAL DEFAULT 0.0,
                affective_charge REAL DEFAULT 0.0,
                existential_depth REAL DEFAULT 0.0,
                intensity_level INTEGER DEFAULT 5,
                complexity TEXT DEFAULT 'medium',
                
                -- Extração
                keywords TEXT,
                
                -- Linking ChromaDB
                chroma_id TEXT UNIQUE,
                
                platform TEXT DEFAULT 'telegram',
                
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # ========== FATOS ESTRUTURADOS ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                
                -- Categorização
                fact_category TEXT NOT NULL,
                fact_subcategory TEXT,
                
                -- Conteúdo
                fact_key TEXT NOT NULL,
                fact_value TEXT NOT NULL,
                
                -- Rastreabilidade
                first_mentioned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                source_conversation_id INTEGER,
                confidence REAL DEFAULT 1.0,
                
                -- Versionamento
                version INTEGER DEFAULT 1,
                is_current BOOLEAN DEFAULT 1,
                
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (source_conversation_id) REFERENCES conversations(id)
            )
        """)
        
        # ========== PADRÕES DETECTADOS ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                
                pattern_type TEXT NOT NULL,
                pattern_name TEXT NOT NULL,
                pattern_description TEXT,
                
                frequency_count INTEGER DEFAULT 1,
                first_detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_occurrence_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                supporting_conversation_ids TEXT,
                confidence_score REAL DEFAULT 0.5,
                
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # ========== MARCOS DO USUÁRIO ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                
                milestone_type TEXT NOT NULL,
                milestone_title TEXT NOT NULL,
                milestone_description TEXT,
                
                achieved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                related_conversation_id INTEGER,
                
                before_state TEXT,
                after_state TEXT,
                
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (related_conversation_id) REFERENCES conversations(id)
            )
        """)
        
        # ========== CONFLITOS ARQUETÍPICOS ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS archetype_conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                conversation_id INTEGER,
                
                archetype1 TEXT NOT NULL,
                archetype2 TEXT NOT NULL,
                conflict_type TEXT,
                tension_level REAL,
                description TEXT,
                
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)
        
        # ========== DESENVOLVIMENTO DO AGENTE ==========
        # Migração: Verificar se tabela precisa ser recriada com user_id
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_development'")
        table_exists = cursor.fetchone() is not None

        if table_exists:
            # Verificar se coluna user_id existe
            cursor.execute("PRAGMA table_info(agent_development)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'user_id' not in columns:
                logger.warning("⚠️ Migrando agent_development para nova estrutura com user_id...")

                # 1. Salvar dados antigos
                cursor.execute("SELECT * FROM agent_development WHERE id = 1")
                old_data = cursor.fetchone()

                # 2. Dropar tabela antiga
                cursor.execute("DROP TABLE IF EXISTS agent_development")

                # 3. Criar nova tabela
                cursor.execute("""
                    CREATE TABLE agent_development (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,

                        phase INTEGER DEFAULT 1,
                        total_interactions INTEGER DEFAULT 0,

                        self_awareness_score REAL DEFAULT 0.0,
                        moral_complexity_score REAL DEFAULT 0.0,
                        emotional_depth_score REAL DEFAULT 0.0,
                        autonomy_score REAL DEFAULT 0.0,

                        depth_level REAL DEFAULT 0.0,
                        autonomy_level REAL DEFAULT 0.0,

                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,

                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)

                # 4. Migrar dados para todos os usuários existentes
                if old_data:
                    cursor.execute("SELECT user_id FROM users")
                    users = cursor.fetchall()

                    for user_row in users:
                        user_id = user_row[0]
                        cursor.execute("""
                            INSERT INTO agent_development
                            (user_id, phase, total_interactions, self_awareness_score,
                             moral_complexity_score, emotional_depth_score, autonomy_score,
                             depth_level, autonomy_level, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            user_id,
                            old_data[1] if len(old_data) > 1 else 1,  # phase
                            old_data[2] if len(old_data) > 2 else 0,  # total_interactions
                            old_data[3] if len(old_data) > 3 else 0.0,  # self_awareness_score
                            old_data[4] if len(old_data) > 4 else 0.0,  # moral_complexity_score
                            old_data[5] if len(old_data) > 5 else 0.0,  # emotional_depth_score
                            old_data[6] if len(old_data) > 6 else 0.0,  # autonomy_score
                            old_data[7] if len(old_data) > 7 else 0.0,  # depth_level
                            old_data[8] if len(old_data) > 8 else 0.0,  # autonomy_level
                            old_data[9] if len(old_data) > 9 else 'CURRENT_TIMESTAMP'  # last_updated
                        ))

                    logger.info(f"✅ Migrados dados de agent_development para {len(users)} usuários")

                self.conn.commit()
        else:
            # Tabela não existe, criar nova estrutura
            cursor.execute("""
                CREATE TABLE agent_development (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,

                    phase INTEGER DEFAULT 1,
                    total_interactions INTEGER DEFAULT 0,

                    self_awareness_score REAL DEFAULT 0.0,
                    moral_complexity_score REAL DEFAULT 0.0,
                    emotional_depth_score REAL DEFAULT 0.0,
                    autonomy_score REAL DEFAULT 0.0,

                    depth_level REAL DEFAULT 0.0,
                    autonomy_level REAL DEFAULT 0.0,

                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

        # Criar índice único para garantir um registro por usuário
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_dev_user
            ON agent_development(user_id)
        """)
        
        # ========== MILESTONES DO AGENTE ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                milestone_type TEXT NOT NULL,
                description TEXT,
                phase INTEGER,
                interaction_count INTEGER,
                
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ========== ANÁLISES COMPLETAS ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS full_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                user_name TEXT NOT NULL,

                mbti TEXT,
                dominant_archetypes TEXT,
                phase INTEGER DEFAULT 1,
                full_analysis TEXT,

                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                platform TEXT DEFAULT 'telegram',

                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # ========== ANÁLISES PSICOMÉTRICAS (RH) ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_psychometrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                version INTEGER DEFAULT 1,

                -- Big Five (OCEAN) - scores 0-100
                openness_score INTEGER,
                openness_level TEXT,
                openness_description TEXT,

                conscientiousness_score INTEGER,
                conscientiousness_level TEXT,
                conscientiousness_description TEXT,

                extraversion_score INTEGER,
                extraversion_level TEXT,
                extraversion_description TEXT,

                agreeableness_score INTEGER,
                agreeableness_level TEXT,
                agreeableness_description TEXT,

                neuroticism_score INTEGER,
                neuroticism_level TEXT,
                neuroticism_description TEXT,

                big_five_confidence INTEGER,
                big_five_interpretation TEXT,

                -- Inteligência Emocional (EQ) - scores 0-100
                eq_self_awareness INTEGER,
                eq_self_management INTEGER,
                eq_social_awareness INTEGER,
                eq_relationship_management INTEGER,
                eq_overall INTEGER,
                eq_leadership_potential TEXT,
                eq_details TEXT,

                -- Estilos de Aprendizagem (VARK) - scores 0-100
                vark_visual INTEGER,
                vark_auditory INTEGER,
                vark_reading INTEGER,
                vark_kinesthetic INTEGER,
                vark_dominant TEXT,
                vark_recommended_training TEXT,

                -- Valores Pessoais (Schwartz) - JSON
                schwartz_values TEXT,
                schwartz_top_3 TEXT,
                schwartz_cultural_fit TEXT,
                schwartz_retention_risk TEXT,

                -- Resumo Executivo
                executive_summary TEXT,

                -- Metadados
                analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                conversations_analyzed INTEGER,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # ========== ÍNDICES DE PERFORMANCE ==========
        # Conversas
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_timestamp ON conversations(timestamp DESC)")  # DESC para ORDER BY
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_user_timestamp ON conversations(user_id, timestamp DESC)")  # Composto
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_chroma ON conversations(chroma_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id)")

        # Conflitos
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_user ON archetype_conflicts(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_conversation ON archetype_conflicts(conversation_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON archetype_conflicts(timestamp DESC)")

        # Usuários
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_platform ON users(platform, platform_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen DESC)")

        # Fatos
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_user_category ON user_facts(user_id, fact_category, is_current)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_current ON user_facts(is_current, user_id)")  # Para buscas de fatos atuais

        # Padrões
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_user ON user_patterns(user_id, pattern_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_confidence ON user_patterns(confidence_score DESC)")

        # Milestones
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_milestones_type ON milestones(milestone_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_milestones_timestamp ON milestones(timestamp DESC)")

        # Análises
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_user ON full_analyses(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_timestamp ON full_analyses(timestamp DESC)")

        # Psicometria
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_psychometrics_user ON user_psychometrics(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_psychometrics_version ON user_psychometrics(user_id, version DESC)")

        self.conn.commit()
        logger.info("✅ Schema SQLite criado/verificado com índices de performance")
    
    # ========================================
    # USUÁRIOS
    # ========================================
    
    def create_user(self, user_id: str, user_name: str,
                   platform: str = 'telegram', platform_id: str = None):
        """Cria ou atualiza usuário"""
        with self._lock:
            cursor = self.conn.cursor()

            name_parts = user_name.split()
            first_name = name_parts[0].title() if name_parts else ""
            last_name = name_parts[-1].title() if len(name_parts) > 1 else ""

            cursor.execute("""
                INSERT OR REPLACE INTO users
                (user_id, user_name, first_name, last_name, platform, platform_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, user_name, first_name, last_name, platform, platform_id))

            self.conn.commit()
            logger.info(f"✅ Usuário criado/atualizado: {user_name}")
    
    def register_user(self, full_name: str, platform: str = "telegram") -> str:
        """Registra usuário (método legado compatível)"""
        name_normalized = full_name.lower().strip()
        user_id = hashlib.md5(name_normalized.encode()).hexdigest()[:12]

        with self._lock:
            cursor = self.conn.cursor()

            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE users
                    SET total_sessions = total_sessions + 1,
                        last_seen = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (user_id,))
                logger.info(f"✅ Usuário existente: {full_name} (sessão #{existing['total_sessions'] + 1})")
            else:
                name_parts = full_name.split()
                first_name = name_parts[0].title()
                last_name = name_parts[-1].title() if len(name_parts) > 1 else ""

                cursor.execute("""
                    INSERT INTO users (user_id, user_name, first_name, last_name, platform)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, full_name.title(), first_name, last_name, platform))
                logger.info(f"✅ Novo usuário: {full_name}")

            self.conn.commit()
            return user_id
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Busca dados do usuário"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_user_stats(self, user_id: str) -> Optional[Dict]:
        """Retorna estatísticas do usuário"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_row = cursor.fetchone()
        
        if not user_row:
            return None
        
        user = dict(user_row)
        
        cursor.execute("SELECT COUNT(*) as count FROM conversations WHERE user_id = ?", (user_id,))
        total_messages = cursor.fetchone()['count']
        
        return {
            'total_messages': total_messages,
            'first_interaction': user['registration_date'],
            'total_sessions': user['total_sessions']
        }
    
    # ========================================
    # FUNÇÕES AUXILIARES - METADATA ENRIQUECIDO
    # ========================================

    def _calculate_recency_tier(self, timestamp: datetime) -> str:
        """
        Calcula tier de recência da conversa

        Args:
            timestamp: Timestamp da conversa

        Returns:
            "recent" (≤30 dias) | "medium" (31-90 dias) | "old" (>90 dias)
        """
        days_ago = (datetime.now() - timestamp).days

        if days_ago <= 30:
            return "recent"
        elif days_ago <= 90:
            return "medium"
        else:
            return "old"

    def _get_dominant_archetype(self, archetype_analyses: Dict) -> str:
        """
        Retorna arquétipo com maior intensidade

        Args:
            archetype_analyses: Dict com análises arquetípicas

        Returns:
            Nome do arquétipo dominante ou ""
        """
        if not archetype_analyses:
            return ""

        try:
            dominant = max(
                archetype_analyses.items(),
                key=lambda x: x[1].intensity if hasattr(x[1], 'intensity') else 0
            )
            return dominant[0] if dominant else ""
        except Exception as e:
            logger.warning(f"Erro ao calcular arquétipo dominante: {e}")
            return ""

    def _extract_people_from_conversation(self, conversation_id: int) -> List[str]:
        """
        Extrai nomes de pessoas mencionadas nos fatos desta conversa

        Args:
            conversation_id: ID da conversa

        Returns:
            Lista de nomes próprios
        """
        cursor = self.conn.cursor()

        # Verificar se user_facts_v2 existe
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='user_facts_v2'
        """)
        use_v2 = cursor.fetchone() is not None

        try:
            if use_v2:
                cursor.execute("""
                    SELECT fact_value
                    FROM user_facts_v2
                    WHERE source_conversation_id = ?
                    AND fact_attribute = 'nome'
                    AND is_current = 1
                """, (conversation_id,))
            else:
                cursor.execute("""
                    SELECT fact_value
                    FROM user_facts
                    WHERE source_conversation_id = ?
                    AND fact_key = 'nome'
                    AND is_current = 1
                """, (conversation_id,))

            names = [row[0] for row in cursor.fetchall() if row[0]]
            return names
        except Exception as e:
            logger.warning(f"Erro ao extrair pessoas da conversa {conversation_id}: {e}")
            return []

    def _extract_topics_from_keywords(self, keywords: List[str]) -> List[str]:
        """
        Classifica keywords em tópicos amplos

        Args:
            keywords: Lista de keywords da conversa

        Returns:
            Lista de tópicos detectados
        """
        if not keywords:
            return []

        # Mapeamento de keywords para tópicos
        topic_mapping = {
            "trabalho": ["trabalho", "emprego", "empresa", "carreira", "chefe", "colega", "projeto"],
            "familia": ["esposa", "marido", "filho", "filha", "pai", "mae", "familia", "casa"],
            "saude": ["saude", "medico", "doenca", "ansiedade", "depressao", "insonia", "terapia"],
            "relacionamento": ["amigo", "amizade", "namoro", "relacionamento", "amor"],
            "lazer": ["viagem", "hobby", "leitura", "esporte", "musica"],
            "dinheiro": ["dinheiro", "financeiro", "salario", "conta", "divida"],
        }

        topics = set()
        keywords_lower = [k.lower() for k in keywords]

        for topic, topic_keywords in topic_mapping.items():
            if any(kw in " ".join(keywords_lower) for kw in topic_keywords):
                topics.add(topic)

        return list(topics)

    def calculate_temporal_boost(self, memory_timestamp: str, mode: str = "balanced") -> float:
        """
        Calcula boost temporal para reranking de memórias

        Args:
            memory_timestamp: Timestamp ISO da memória
            mode: Modo de decay ("recent_focused" | "balanced" | "archeological")

        Returns:
            Float multiplicador (0.5 a 1.5)
        """
        try:
            mem_time = datetime.fromisoformat(memory_timestamp)
        except:
            return 1.0  # Fallback se timestamp inválido

        days_ago = (datetime.now() - mem_time).days

        if mode == "recent_focused":
            # Valoriza últimos 7 dias, penaliza antigas
            if days_ago <= 7:
                return 1.5
            elif days_ago <= 30:
                return 1.2
            elif days_ago <= 90:
                return 1.0
            else:
                return 0.7

        elif mode == "balanced":
            # Equilíbrio entre recente e histórico
            if days_ago <= 30:
                return 1.2
            elif days_ago <= 90:
                return 1.0
            else:
                return 0.9

        elif mode == "archeological":
            # Valoriza padrões de longo prazo
            if days_ago <= 30:
                return 1.0
            elif days_ago <= 90:
                return 1.1
            else:
                return 1.3  # Boost para memórias antigas

        return 1.0  # Default

    # ========================================
    # CONVERSAS (HÍBRIDO: SQLite + ChromaDB)
    # ========================================

    def save_conversation(self, user_id: str, user_name: str, user_input: str,
                         ai_response: str, session_id: str = None,
                         archetype_analyses: Dict = None,
                         detected_conflicts: List[ArchetypeConflict] = None,
                         tension_level: float = 0.0,
                         affective_charge: float = 0.0,
                         existential_depth: float = 0.0,
                         intensity_level: int = 5,
                         complexity: str = "medium",
                         keywords: List[str] = None,
                         platform: str = "telegram",
                         chat_history: List[Dict] = None) -> int:
        """
        Salva conversa em AMBOS: SQLite (metadados) + ChromaDB (semântica)

        Returns:
            int: ID da conversa no SQLite
        """

        # 🔍 DEBUG CRÍTICO: Log de salvamento para detectar vazamento
        logger.info(f"💾 [DEBUG] Salvando conversa para user_id='{user_id}' (type={type(user_id).__name__})")
        logger.info(f"   User name: '{user_name}'")
        logger.info(f"   Input preview: '{user_input[:50]}...'")

        # Garantir que user_id é string para consistência
        user_id_str = str(user_id) if user_id else None
        if not user_id_str:
            logger.error("❌ user_id é None ou vazio! Não é possível salvar.")
            raise ValueError("user_id não pode ser None ou vazio")

        if user_id_str != user_id:
            logger.warning(f"⚠️ user_id convertido de {type(user_id).__name__} para string: '{user_id}' -> '{user_id_str}'")
            user_id = user_id_str

        with self._lock:
            cursor = self.conn.cursor()

            # 1. Salvar no SQLite (metadados)
            cursor.execute("""
                INSERT INTO conversations
                (user_id, user_name, session_id, user_input, ai_response,
                 archetype_analyses, detected_conflicts,
                 tension_level, affective_charge, existential_depth,
                 intensity_level, complexity, keywords, platform)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, user_name, session_id, user_input, ai_response,
                json.dumps({k: asdict(v) for k, v in archetype_analyses.items()}) if archetype_analyses else None,
                json.dumps([asdict(c) for c in detected_conflicts]) if detected_conflicts else None,
                tension_level, affective_charge, existential_depth,
                intensity_level, complexity,
                ",".join(keywords) if keywords else "",
                platform
            ))

            conversation_id = cursor.lastrowid
            chroma_id = f"conv_{conversation_id}"

            logger.info(f"   SQLite: Conversa salva com ID={conversation_id}, chroma_id='{chroma_id}'")

            # 2. Atualizar com chroma_id
            cursor.execute("""
                UPDATE conversations
                SET chroma_id = ?
                WHERE id = ?
            """, (chroma_id, conversation_id))

            self.conn.commit()
        
        # 3. Salvar no ChromaDB (se habilitado)
        if self.chroma_enabled:
            try:
                # Construir documento completo
                doc_content = f"""
Usuário: {user_name}
Input: {user_input}
Resposta: {ai_response}
"""
                
                if archetype_analyses:
                    doc_content += "\n=== VOZES INTERNAS ===\n"
                    for arch_name, insight in archetype_analyses.items():
                        doc_content += f"\n{arch_name}: {insight.voice_reaction[:150]} (impulso: {insight.impulse}, intensidade: {insight.intensity:.1f})\n"
                
                if detected_conflicts:
                    doc_content += "\n=== CONFLITOS DETECTADOS ===\n"
                    for conflict in detected_conflicts:
                        doc_content += f"{conflict.description}\n"
                
                # Metadata (Enriquecido - Fase 1 do Plano de Memória)
                now = datetime.now()
                metadata = {
                    # Campos existentes (manter)
                    "user_id": user_id,
                    "user_name": user_name,
                    "session_id": session_id or "",
                    "timestamp": now.isoformat(),
                    "conversation_id": conversation_id,
                    "tension_level": tension_level,
                    "affective_charge": affective_charge,
                    "existential_depth": existential_depth,
                    "intensity_level": intensity_level,
                    "complexity": complexity,
                    "keywords": ",".join(keywords) if keywords else "",
                    "has_conflicts": len(detected_conflicts) > 0 if detected_conflicts else False,

                    # NOVOS - Temporal Estratificado
                    "day_bucket": now.strftime("%Y-%m-%d"),
                    "week_bucket": now.strftime("%Y-W%W"),
                    "month_bucket": now.strftime("%Y-%m"),
                    "recency_tier": self._calculate_recency_tier(now),

                    # NOVOS - Emocional/Temático
                    "emotional_intensity": round(affective_charge + tension_level, 2),
                    "dominant_archetype": self._get_dominant_archetype(archetype_analyses) if archetype_analyses else "",

                    # NOVOS - Relacional
                    "mentions_people": ",".join(self._extract_people_from_conversation(conversation_id)),
                    "topics": ",".join(self._extract_topics_from_keywords(keywords)),
                }

                # NOVO - Fact-Conversation Linking (Fase 4)
                # Buscar IDs de fatos extraídos desta conversa
                try:
                    cursor.execute("""
                        SELECT name FROM sqlite_master
                        WHERE type='table' AND name='user_facts_v2'
                    """)
                    use_v2 = cursor.fetchone() is not None

                    if use_v2:
                        cursor.execute("""
                            SELECT id FROM user_facts_v2
                            WHERE source_conversation_id = ? AND is_current = 1
                        """, (conversation_id,))
                    else:
                        cursor.execute("""
                            SELECT id FROM user_facts
                            WHERE source_conversation_id = ? AND is_current = 1
                        """, (conversation_id,))

                    fact_ids = [str(row[0]) for row in cursor.fetchall()]
                    if fact_ids:
                        metadata["extracted_fact_ids"] = ",".join(fact_ids)
                        logger.info(f"   Linkados {len(fact_ids)} fatos ao ChromaDB metadata")
                except Exception as fact_link_error:
                    logger.warning(f"   Erro ao linkar fatos: {fact_link_error}")
                    # Não bloquear salvamento se linking falhar
                    pass

                # 🔍 DEBUG: Log do metadata sendo salvo
                logger.info(f"   ChromaDB metadata: user_id='{metadata['user_id']}' (type={type(metadata['user_id']).__name__})")
                logger.info(f"   ChromaDB doc_id: '{chroma_id}'")

                # Criar documento
                doc = Document(page_content=doc_content, metadata=metadata)

                # ✅ ADICIONAR COM TRATAMENTO DE DUPLICATAS
                try:
                    self.vectorstore.add_documents([doc], ids=[chroma_id])
                    logger.info(f"✅ ChromaDB: Documento '{chroma_id}' salvo com user_id='{metadata['user_id']}'")
                    logger.info(f"✅ Conversa salva: SQLite (ID={conversation_id}) + ChromaDB ({chroma_id})")
                    
                except Exception as add_error:
                    error_msg = str(add_error).lower()
                    
                    # Verificar se é erro de duplicata
                    if "already exists" in error_msg or "duplicate" in error_msg or "unique constraint" in error_msg:
                        logger.warning(f"⚠️ Documento {chroma_id} já existe no ChromaDB, substituindo...")
                        
                        try:
                            # Deletar documento existente
                            self.vectorstore.delete([chroma_id])
                            
                            # Adicionar novo documento
                            self.vectorstore.add_documents([doc], ids=[chroma_id])
                            
                            logger.info(f"✅ Documento {chroma_id} substituído com sucesso")
                            
                        except Exception as replace_error:
                            logger.error(f"❌ Erro ao substituir documento {chroma_id}: {replace_error}")
                            logger.warning(f"⚠️ Conversa salva apenas no SQLite (ID={conversation_id})")
                    else:
                        # Outro tipo de erro
                        logger.error(f"❌ Erro ao adicionar ao ChromaDB: {add_error}")
                        logger.warning(f"⚠️ Conversa salva apenas no SQLite (ID={conversation_id})")
                
            except Exception as e:
                logger.error(f"❌ Erro geral ao processar ChromaDB: {e}")
                logger.warning(f"⚠️ Sistema continua funcionando apenas com SQLite")
        
        # 4. Salvar conflitos na tabela específica
        if detected_conflicts:
            with self._lock:
                for conflict in detected_conflicts:
                    cursor.execute("""
                        INSERT INTO archetype_conflicts
                        (user_id, conversation_id, archetype1, archetype2,
                         conflict_type, tension_level, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        user_id, conversation_id,
                        conflict.archetype_1, conflict.archetype_2,
                        conflict.conflict_type, conflict.tension_level,
                        conflict.description
                    ))

                self.conn.commit()
        
        # 5. Atualizar desenvolvimento do agente (isolado por usuário)
        self._update_agent_development(user_id)

        # 6. Extrair fatos do input (V2 com LLM, fallback para V1)
        logger.info(f"🔍 [DEBUG FATOS] Verificando extração... hasattr(extract_and_save_facts_v2)={hasattr(self, 'extract_and_save_facts_v2')}")
        if hasattr(self, 'extract_and_save_facts_v2'):
            logger.info("✅ Chamando extract_and_save_facts_v2...")
            self.extract_and_save_facts_v2(user_id, user_input, conversation_id)
        else:
            logger.info("⚠️ extract_and_save_facts_v2 não encontrado, usando método antigo...")
            self.extract_and_save_facts(user_id, user_input, conversation_id)

        # 7. HOOK: Sistema de Ruminação (só para admin)
        try:
            from rumination_config import ADMIN_USER_ID
            if user_id == ADMIN_USER_ID and platform == "telegram":
                from jung_rumination import RuminationEngine
                rumination = RuminationEngine(self)
                rumination.ingest({
                    "user_id": user_id,
                    "user_input": user_input,
                    "ai_response": ai_response,
                    "conversation_id": conversation_id,
                    "tension_level": tension_level,
                    "affective_charge": affective_charge
                })
        except Exception as e:
            logger.warning(f"⚠️ Erro no hook de ruminação: {e}")

        # 8. HOOK: Log diário em arquivo .md (memória textual)
        try:
            from user_profile_writer import write_session_entry
            write_session_entry(
                user_id=user_id,
                user_name=user_name,
                user_input=user_input,
                ai_response=ai_response,
                metadata={
                    "tension_level": tension_level,
                    "affective_charge": affective_charge,
                },
            )
        except Exception as e:
            logger.warning(f"⚠️ Erro no hook de log diário: {e}")

        return conversation_id

    def get_user_conversations(
        self,
        user_id: str,
        limit: int = 10,
        include_proactive: bool = False
    ) -> List[Dict]:
        """
        Busca últimas conversas do usuário (SQLite)

        Args:
            user_id: ID do usuário
            limit: Número máximo de conversas
            include_proactive: Se True, inclui conversas com platform='proactive' ou 'proactive_rumination'

        Returns:
            Lista de conversas ordenadas por timestamp DESC
        """
        cursor = self.conn.cursor()

        if include_proactive:
            # Incluir TODAS as conversas (reativas + proativas)
            query = """
                SELECT * FROM conversations
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
            params = (user_id, limit)
        else:
            # Comportamento padrão: excluir proativas
            query = """
                SELECT * FROM conversations
                WHERE user_id = ?
                  AND (platform IS NULL OR platform NOT IN ('proactive', 'proactive_rumination'))
                ORDER BY timestamp DESC
                LIMIT ?
            """
            params = (user_id, limit)

        cursor.execute(query, params)

        conversations = []
        for row in cursor.fetchall():
            conv = dict(row)

            # Parse keywords se for JSON string
            if conv.get('keywords') and isinstance(conv['keywords'], str):
                try:
                    conv['keywords'] = json.loads(conv['keywords'])
                except:
                    conv['keywords'] = []

            conversations.append(conv)

        return conversations
    
    def count_conversations(self, user_id: str) -> int:
        """Conta conversas do usuário"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM conversations WHERE user_id = ?", (user_id,))
        return cursor.fetchone()['count']

    def conversations_to_chat_history(self, conversations: List[Dict]) -> List[Dict]:
        """
        Converte conversas do banco para formato chat_history.

        Args:
            conversations: Lista de conversas do banco (ORDER BY timestamp DESC)

        Returns:
            Lista de dicts {"role": "user"/"assistant", "content": str}
            em ordem cronológica (mais antiga primeiro)
        """
        history = []

        # Inverter para ordem cronológica (mais antiga → mais recente)
        for conv in reversed(conversations):
            user_input = conv.get('user_input', '')

            # Filtrar marcadores de sistema proativo
            if user_input not in [
                "[SISTEMA PROATIVO INICIOU CONTATO]",
                "[INSIGHT RUMINADO - SISTEMA PROATIVO]"
            ]:
                history.append({
                    "role": "user",
                    "content": user_input
                })

            # Resposta do agente (sempre incluir)
            ai_response = conv.get('ai_response', '')
            if ai_response:
                history.append({
                    "role": "assistant",
                    "content": ai_response
                })

        return history

    # ========================================
    # QUERY ENRICHMENT - FASE 2
    # ========================================

    def _extract_names_from_text(self, text: str) -> List[str]:
        """
        Extrai nomes próprios do texto (heurística simples)

        Args:
            text: Texto para análise

        Returns:
            Lista de possíveis nomes próprios
        """
        import re

        # Padrão: Palavras capitalizadas que não são início de frase
        # Ex: "Minha esposa Ana" -> captura "Ana"
        pattern = r'\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)\b'

        # Filtrar palavras comuns que não são nomes
        stopwords = {'O', 'A', 'Os', 'As', 'Um', 'Uma', 'De', 'Da', 'Do', 'Em', 'No', 'Na',
                    'Para', 'Por', 'Com', 'Sem', 'Mais', 'Menos', 'Muito', 'Pouco'}

        matches = re.findall(pattern, text)
        names = [m for m in matches if m not in stopwords]

        return list(set(names))  # Remover duplicatas

    def _detect_topics_in_text(self, text: str) -> List[str]:
        """
        Detecta tópicos mencionados no texto

        Args:
            text: Texto para análise

        Returns:
            Lista de tópicos detectados
        """
        text_lower = text.lower()

        topic_keywords = {
            "trabalho": ["trabalho", "emprego", "empresa", "chefe", "colega", "reunião", "projeto"],
            "familia": ["esposa", "marido", "filho", "filha", "pai", "mãe", "família", "casa"],
            "saude": ["saúde", "doença", "médico", "ansiedade", "depressão", "terapia", "remédio"],
            "relacionamento": ["amigo", "namoro", "amor", "relacionamento", "parceiro"],
            "lazer": ["viagem", "férias", "hobby", "passeio"],
            "dinheiro": ["dinheiro", "salário", "conta", "dívida", "financeiro"],
        }

        detected = []
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                detected.append(topic)

        return detected

    def _build_enriched_query(self, user_id: str, user_input: str, chat_history: List[Dict] = None) -> str:
        """
        Constrói query enriquecida com múltiplas fontes (Fase 2 - Query Enrichment)

        Args:
            user_id: ID do usuário
            user_input: Input do usuário
            chat_history: Histórico da conversa atual

        Returns:
            Query enriquecida
        """
        query_parts = [user_input]  # Base

        # CAMADA 1: Contexto conversacional recente (expandir de 3 para 5)
        if chat_history and len(chat_history) > 0:
            recent = " ".join([
                msg["content"][:100]
                for msg in chat_history[-5:]  # Era -3, agora -5
                if msg["role"] == "user"
            ])
            if recent:
                query_parts.append(recent)

        # CAMADA 2: Fatos relevantes do usuário (NOVO)
        # Buscar nomes de pessoas mencionadas no input
        mentioned_names = self._extract_names_from_text(user_input)

        if mentioned_names:
            # Buscar fatos sobre essas pessoas
            cursor = self.conn.cursor()

            # Usar user_facts_v2 se disponível
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='user_facts_v2'
            """)
            use_v2 = cursor.fetchone() is not None

            relevant_facts = []
            for name in mentioned_names:
                try:
                    if use_v2:
                        cursor.execute("""
                            SELECT fact_type, fact_attribute, fact_value
                            FROM user_facts_v2
                            WHERE user_id = ? AND fact_value LIKE ? AND is_current = 1
                            LIMIT 3
                        """, (user_id, f"%{name}%"))
                    else:
                        cursor.execute("""
                            SELECT fact_key, fact_value
                            FROM user_facts
                            WHERE user_id = ? AND fact_value LIKE ? AND is_current = 1
                            LIMIT 3
                        """, (user_id, f"%{name}%"))

                    facts = cursor.fetchall()
                    relevant_facts.extend([
                        f"{row[0]}:{row[1]}" if use_v2 else f"{row[0]}:{row[1]}"
                        for row in facts
                    ])
                except Exception as e:
                    logger.warning(f"Erro ao buscar fatos para '{name}': {e}")

            if relevant_facts:
                query_parts.append(" ".join(relevant_facts[:5]))  # Limitar a 5 fatos

        # CAMADA 3: Tópicos implícitos (NOVO)
        topics = self._detect_topics_in_text(user_input)
        if topics:
            query_parts.append(" ".join(topics))

        enriched = " ".join(query_parts)

        # Log para debug
        if len(enriched) > len(user_input):
            logger.info(f"   Query enriquecida: {len(enriched)} chars (original: {len(user_input)} chars)")
            logger.info(f"   Nomes detectados: {mentioned_names}")
            logger.info(f"   Tópicos detectados: {topics}")

        return enriched

    # ========================================
    # TWO-STAGE RETRIEVAL & RERANKING - FASE 3
    # ========================================

    def _calculate_adaptive_k(self, query: str, chat_history: List[Dict], user_id: str) -> int:
        """
        Calcula k adaptativo baseado em complexidade do contexto (Fase 3)

        Args:
            query: Query do usuário
            chat_history: Histórico da conversa
            user_id: ID do usuário

        Returns:
            k dinâmico entre 3 e 12
        """
        base_k = 5

        # Fator 1: Comprimento do histórico
        if chat_history and len(chat_history) > 10:
            base_k += 2  # Conversas longas precisam de mais contexto

        # Fator 2: Complexidade da query
        query_words = len(query.split())
        if query_words > 20:
            base_k += 2
        elif query_words < 5:
            base_k -= 1  # Queries curtas precisam de menos

        # Fator 3: Múltiplas pessoas mencionadas
        mentioned_names = self._extract_names_from_text(query)
        if len(mentioned_names) > 1:
            base_k += len(mentioned_names)

        # Fator 4: Histórico total do usuário
        total_conversations = self.count_conversations(user_id)
        if total_conversations < 20:
            base_k = min(base_k, 3)  # Limitar para usuários novos

        # Limitar entre 3 e 12
        final_k = max(3, min(base_k, 12))

        logger.info(f"   k adaptativo calculado: {final_k} (base={5}, words={query_words}, names={len(mentioned_names)}, total_convs={total_conversations})")

        return final_k

    def _rerank_memories(self, results: List[tuple], user_id: str, query: str) -> List[Dict]:
        """
        Reranking inteligente com 6 boosts (Fase 3)

        Args:
            results: Lista de (Document, score) do ChromaDB
            user_id: ID do usuário
            query: Query original
            chat_history: Histórico da conversa

        Returns:
            Lista de memórias rerankeadas com scores combinados
        """
        import re

        reranked = []

        # Extrair informações da query para boosting
        query_names = set(self._extract_names_from_text(query))
        query_topics = set(self._detect_topics_in_text(query))

        logger.info(f"   Reranking {len(results)} memórias...")
        logger.info(f"   Query names: {query_names}")
        logger.info(f"   Query topics: {query_topics}")

        for doc, base_score in results:
            metadata = doc.metadata

            # Validação extra: filtrar manualmente user_id errado
            doc_user_id = str(metadata.get('user_id', ''))
            if doc_user_id != str(user_id):
                logger.error(f"🚨 Removendo doc com user_id='{doc_user_id}' (esperado='{user_id}')")
                continue

            # === CÁLCULO DE BOOSTS ===

            # 1. BOOST TEMPORAL
            temporal_boost = self.calculate_temporal_boost(
                metadata.get('timestamp', ''),
                mode="balanced"
            )

            # 2. BOOST EMOCIONAL
            emotional_intensity = metadata.get('emotional_intensity', 0.0)
            emotional_boost = 1.0
            if emotional_intensity > 1.5:
                emotional_boost = 1.3  # Priorizar momentos emocionalmente intensos
            elif emotional_intensity > 2.5:
                emotional_boost = 1.5  # Muito intenso

            # 3. BOOST DE TÓPICO
            memory_topics = set(metadata.get('topics', '').split(',')) if metadata.get('topics') else set()
            # Remover strings vazias
            memory_topics = {t.strip() for t in memory_topics if t.strip()}

            topic_boost = 1.0
            if query_topics & memory_topics:  # Interseção
                overlap = len(query_topics & memory_topics)
                topic_boost = 1.2 + (overlap * 0.1)  # +0.1 por tópico em comum

            # 4. BOOST DE PESSOA MENCIONADA (mais forte)
            memory_people = set(metadata.get('mentions_people', '').split(',')) if metadata.get('mentions_people') else set()
            memory_people = {p.strip() for p in memory_people if p.strip()}

            person_boost = 1.0
            if query_names & memory_people:  # Interseção
                person_boost = 1.5  # FORTE boost se mesma pessoa mencionada

            # 5. BOOST DE PROFUNDIDADE EXISTENCIAL
            depth = metadata.get('existential_depth', 0.0)
            depth_boost = 1.0
            if depth > 0.7:
                depth_boost = 1.15  # Leve boost para conversas profundas

            # 6. BOOST DE CONFLITO ARQUETÍPICO
            conflict_boost = 1.0
            if metadata.get('has_conflicts', False):
                conflict_boost = 1.1  # Leve boost para momentos de conflito interno

            # === SCORE FINAL COMBINADO ===
            # Distância ChromaDB é invertida (menor = mais similar)
            # Convertemos para similaridade: 1 - score
            similarity = 1 - base_score

            final_score = (
                similarity *
                temporal_boost *
                emotional_boost *
                topic_boost *
                person_boost *
                depth_boost *
                conflict_boost
            )

            # Extrair conteúdo do documento
            user_input_match = re.search(r"Input:\s*(.+?)(?:\n|Resposta:|$)", doc.page_content, re.DOTALL)
            user_input_text = user_input_match.group(1).strip() if user_input_match else ""

            response_match = re.search(r"Resposta:\s*(.+?)(?:\n|===|$)", doc.page_content, re.DOTALL)
            response_text = response_match.group(1).strip() if response_match else ""

            reranked.append({
                'conversation_id': metadata.get('conversation_id'),
                'user_input': user_input_text,
                'ai_response': response_text,
                'timestamp': metadata.get('timestamp', ''),
                'base_score': base_score,
                'similarity_score': similarity,
                'final_score': final_score,
                'boosts': {
                    'temporal': round(temporal_boost, 2),
                    'emotional': round(emotional_boost, 2),
                    'topic': round(topic_boost, 2),
                    'person': round(person_boost, 2),
                    'depth': round(depth_boost, 2),
                    'conflict': round(conflict_boost, 2),
                },
                'metadata': metadata,
                'full_document': doc.page_content,
                'keywords': metadata.get('keywords', '').split(','),
                'tension_level': metadata.get('tension_level', 0.0),
            })

        # Ordenar por final_score (decrescente)
        reranked.sort(key=lambda x: x['final_score'], reverse=True)

        # Log dos top 3 com detalhes de boosts
        logger.info(f"   ✅ Reranking concluído. Top 3:")
        for i, mem in enumerate(reranked[:3], 1):
            logger.info(f"   {i}. base={mem['base_score']:.3f}, similarity={mem['similarity_score']:.3f}, final={mem['final_score']:.3f}")
            logger.info(f"      Boosts: {mem['boosts']}")
            logger.info(f"      Input: {mem['user_input'][:60]}...")

        return reranked

    # ========================================
    # BUSCA SEMÂNTICA (ChromaDB)
    # ========================================

    def semantic_search(self, user_id: str, query: str, k: int = None,
                       chat_history: List[Dict] = None) -> List[Dict]:
        """
        Busca semântica com TWO-STAGE RETRIEVAL + INTELLIGENT RERANKING (Fase 3)

        STAGE 1: Broad retrieval (k*3)
        STAGE 2: Intelligent reranking com 6 boosts

        Args:
            user_id: ID do usuário
            query: Texto da consulta
            k: Número de resultados (None = adaptativo)
            chat_history: Histórico da conversa atual (opcional)

        Returns:
            Lista de memórias rerankeadas com scores combinados
        """

        if not self.chroma_enabled:
            logger.warning("ChromaDB desabilitado. Retornando conversas recentes do SQLite.")
            return self._fallback_keyword_search(user_id, query, k or 5)

        try:
            # Garantir que user_id é string para consistência
            user_id_str = str(user_id) if user_id else None
            if not user_id_str:
                logger.error("❌ user_id é None ou vazio! Retornando lista vazia.")
                return []

            # 🔍 DEBUG: Início do two-stage retrieval
            logger.info(f"🔍 [TWO-STAGE] Busca semântica para user_id='{user_id_str}'")
            logger.info(f"   Query original: '{query[:100]}'")

            # Calcular k adaptativo se não fornecido (FASE 3)
            if k is None:
                k = self._calculate_adaptive_k(query, chat_history, user_id_str)
            else:
                logger.info(f"   k fixo fornecido: {k}")

            # Query enriquecida com multi-stage enhancement (FASE 2)
            enriched_query = self._build_enriched_query(
                user_id=user_id_str,
                user_input=query,
                chat_history=chat_history
            )

            # ============================================
            # STAGE 1: BROAD RETRIEVAL
            # ============================================
            broad_k = max(k * 3, 9)  # Buscar pelo menos 3x mais, mínimo 9
            logger.info(f"   STAGE 1: Broad retrieval (k={broad_k})")

            chroma_filter = {"user_id": user_id_str}

            results = self.vectorstore.similarity_search_with_score(
                enriched_query,
                k=broad_k,
                filter=chroma_filter
            )

            logger.info(f"   Resultados retornados do ChromaDB: {len(results)}")

            if not results:
                logger.warning("   Nenhum resultado encontrado no ChromaDB")
                return []

            # ============================================
            # STAGE 2: INTELLIGENT RERANKING
            # ============================================
            logger.info(f"   STAGE 2: Reranking inteligente")
            reranked = self._rerank_memories(
                results=results,
                user_id=user_id_str,
                query=query
            )

            # Retornar top k após reranking
            top_memories = reranked[:k]

            logger.info(f"✅ Two-Stage concluído: {len(top_memories)} memórias finais (de {len(results)} broad)")
            for i, mem in enumerate(top_memories[:3], 1):
                logger.info(f"   {i}. [final={mem['final_score']:.3f}] {mem['user_input'][:50]}...")

            # STAGE 3: Merge com BM25 sobre arquivos de sessão
            try:
                from bm25_search import search as bm25_search
                bm25_hits = bm25_search(user_id_str, query, k=max(3, k // 2))
                if bm25_hits:
                    existing_texts = {m['user_input'][:80] for m in top_memories}
                    for hit in bm25_hits:
                        # Evitar duplicatas já cobertas pelo vector search
                        if hit['text'][:80] not in existing_texts:
                            top_memories.append({
                                'conversation_id': None,
                                'user_input': hit['text'],
                                'ai_response': '',
                                'timestamp': hit['date'],
                                'similarity_score': hit['bm25_score'] * 0.3,
                                'final_score': hit['bm25_score'] * 0.3,
                                'keywords': [],
                                'metadata': {'type': 'bm25', 'date': hit['date']},
                            })
                    # Re-ordenar por final_score
                    top_memories.sort(key=lambda m: m.get('final_score', 0), reverse=True)
                    top_memories = top_memories[:k]
                    logger.info(f"   BM25: {len(bm25_hits)} hits fundidos")
            except Exception as bm25_err:
                logger.debug(f"   BM25 indisponível: {bm25_err}")

            return top_memories

        except Exception as e:
            logger.error(f"❌ Erro na busca semântica: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self._fallback_keyword_search(user_id, query, k or 5)
    
    def _fallback_keyword_search(self, user_id: str, query: str, k: int = 5) -> List[Dict]:
        """Busca por keywords (fallback quando ChromaDB indisponível)"""
        cursor = self.conn.cursor()
        
        search_term = f"%{query}%"
        cursor.execute("""
            SELECT * FROM conversations
            WHERE user_id = ? 
            AND (user_input LIKE ? OR ai_response LIKE ?)
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, search_term, search_term, k))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'conversation_id': row['id'],
                'user_input': row['user_input'],
                'ai_response': row['ai_response'],
                'timestamp': row['timestamp'],
                'similarity_score': 0.5,  # Score artificial
                'keywords': row['keywords'].split(',') if row['keywords'] else [],
                'metadata': dict(row)
            })
        
        return results
    
    # ========================================
    # CONSTRUÇÃO DE CONTEXTO
    # ========================================

    def _search_relevant_facts(self, user_id: str, query: str) -> List[Dict]:
        """
        Busca fatos relevantes ao input atual (Fase 5)

        Args:
            user_id: ID do usuário
            query: Input do usuário

        Returns:
            Lista de fatos relevantes
        """
        # Extrair nomes e tópicos da query
        mentioned_names = self._extract_names_from_text(query)
        mentioned_topics = self._detect_topics_in_text(query)

        cursor = self.conn.cursor()

        # Verificar estrutura V2
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='user_facts_v2'
        """)
        use_v2 = cursor.fetchone() is not None

        relevant_facts = []

        # Buscar fatos sobre pessoas mencionadas
        if mentioned_names:
            for name in mentioned_names:
                if use_v2:
                    cursor.execute("""
                        SELECT fact_category, fact_type, fact_attribute, fact_value, confidence
                        FROM user_facts_v2
                        WHERE user_id = ? AND fact_value LIKE ? AND is_current = 1
                        LIMIT 5
                    """, (user_id, f"%{name}%"))
                else:
                    cursor.execute("""
                        SELECT fact_category, fact_key AS fact_attribute, fact_value
                        FROM user_facts
                        WHERE user_id = ? AND fact_value LIKE ? AND is_current = 1
                        LIMIT 5
                    """, (user_id, f"%{name}%"))

                relevant_facts.extend([dict(row) for row in cursor.fetchall()])

        # Buscar fatos sobre tópicos mencionados
        if mentioned_topics:
            for topic in mentioned_topics:
                category_map = {
                    "trabalho": "TRABALHO",
                    "familia": "RELACIONAMENTO",
                    "saude": "SAUDE",
                }
                category = category_map.get(topic, "RELACIONAMENTO")

                if use_v2:
                    cursor.execute("""
                        SELECT fact_category, fact_type, fact_attribute, fact_value, confidence
                        FROM user_facts_v2
                        WHERE user_id = ? AND fact_category = ? AND is_current = 1
                        LIMIT 5
                    """, (user_id, category))
                else:
                    cursor.execute("""
                        SELECT fact_category, fact_key AS fact_attribute, fact_value
                        FROM user_facts
                        WHERE user_id = ? AND fact_category = ? AND is_current = 1
                        LIMIT 5
                    """, (user_id, category))

                relevant_facts.extend([dict(row) for row in cursor.fetchall()])

        return relevant_facts

    def _format_facts_hierarchically(self, facts: List[Dict]) -> str:
        """
        Formata fatos de forma hierárquica (Fase 5)

        Args:
            facts: Lista de fatos

        Returns:
            String formatada
        """
        if not facts:
            return ""

        # Agrupar por categoria
        by_category = {}
        for fact in facts:
            category = fact.get('fact_category', 'OUTROS')
            if category not in by_category:
                by_category[category] = []

            attribute = fact.get('fact_attribute', '')
            value = fact.get('fact_value', '')
            by_category[category].append(f"{attribute}: {value}")

        # Formatar
        lines = []
        for category, items in by_category.items():
            lines.append(f"{category}:")
            for item in items[:3]:  # Limitar a 3 por categoria
                lines.append(f"  - {item}")

        return "\n".join(lines)

    def _get_relevant_patterns(self, user_id: str, query: str) -> List[Dict]:
        """
        Busca padrões relevantes ao input atual (Fase 5)

        Args:
            user_id: ID do usuário
            query: Input do usuário

        Returns:
            Lista de padrões relevantes
        """
        cursor = self.conn.cursor()

        # Buscar padrões com alta confiança
        cursor.execute("""
            SELECT pattern_name, pattern_description, frequency_count, confidence_score
            FROM user_patterns
            WHERE user_id = ? AND confidence_score > 0.6
            ORDER BY confidence_score DESC, frequency_count DESC
            LIMIT 3
        """, (user_id,))

        return [dict(row) for row in cursor.fetchall()]

    def _compress_context_if_needed(self, context: str, max_tokens: int = 2000) -> str:
        """
        Comprime contexto se exceder limite de tokens (Fase 5)

        Args:
            context: Contexto completo
            max_tokens: Limite máximo de tokens

        Returns:
            Contexto comprimido se necessário
        """
        # Estimativa simples: 1 token ≈ 4 caracteres
        estimated_tokens = len(context) / 4

        if estimated_tokens <= max_tokens:
            return context

        # Se exceder, truncar proporcionalmente
        target_chars = int(max_tokens * 4 * 0.9)  # 90% do limite
        return context[:target_chars] + "\n\n[Contexto truncado devido ao limite]"

    def build_rich_context(self, user_id: str, current_input: str,
                          k_memories: int = None,
                          chat_history: List[Dict] = None) -> str:
        """
        Constrói contexto HIERÁRQUICO e ESTRATIFICADO (Fase 5)

        Combina em layers:
        1. Histórico imediato (sempre incluir)
        2. Fatos relevantes ao input (busca inteligente)
        3. Memórias semânticas (reranked, agrupadas por recência + consolidadas)
        4. Padrões detectados (se relevantes)

        Args:
            user_id: ID do usuário
            current_input: Input atual
            k_memories: Número de memórias (None = adaptativo)
            chat_history: Histórico da conversa atual

        Returns:
            Contexto formatado e hierárquico
        """

        logger.info(f"🏗️ [FASE 5] Construindo contexto hierárquico para user_id={user_id}")

        user = self.get_user(user_id)
        name = user['user_name'] if user else "Usuário"

        context_parts = []

        # ===== LAYER 1: HISTÓRICO IMEDIATO =====
        context_parts.append("=== CONVERSA ATUAL ===\n")

        if chat_history and len(chat_history) > 0:
            recent = chat_history[-6:] if len(chat_history) > 6 else chat_history

            for msg in recent:
                role = "👤 Usuário" if msg["role"] == "user" else "🤖 Jung"
                content = msg["content"][:150] + "..." if len(msg["content"]) > 150 else msg["content"]
                context_parts.append(f"{role}: {content}")

            context_parts.append("")

        # ===== LAYER 2: FATOS RELEVANTES =====
        relevant_facts = self._search_relevant_facts(user_id, current_input)

        if relevant_facts:
            context_parts.append("=== FATOS RELEVANTES ===\n")
            context_parts.append(self._format_facts_hierarchically(relevant_facts))
            context_parts.append("")


        # ===== LAYER 3: MEMÓRIAS SEMÂNTICAS =====
        memories = self.semantic_search(user_id, current_input, k=k_memories, chat_history=chat_history)

        if memories:
            context_parts.append("=== MEMÓRIAS RELACIONADAS ===\n")

            # Separar por tipo e recência
            consolidated = [m for m in memories if m.get('metadata', {}).get('type') == 'consolidated']
            regular = [m for m in memories if m.get('metadata', {}).get('type') != 'consolidated']

            # Agrupar regulares por recência
            recent = [m for m in regular if m.get('metadata', {}).get('recency_tier') == 'recent']
            older = [m for m in regular if m.get('metadata', {}).get('recency_tier') != 'recent']

            # Memórias consolidadas primeiro (se existirem)
            if consolidated:
                context_parts.append("📦 Padrões de Longo Prazo (Consolidado):")
                for mem in consolidated[:1]:  # Apenas 1 consolidada
                    preview = mem.get('full_document', '')[:300]
                    context_parts.append(f"{preview}...")
                context_parts.append("")

            # Memórias recentes
            if recent:
                context_parts.append("🕐 Recente (últimos 30 dias):")
                for i, mem in enumerate(recent[:3], 1):
                    timestamp = mem.get('timestamp', '')[:10]
                    user_input = mem.get('user_input', '')[:100]
                    context_parts.append(f"{i}. [{timestamp}] {user_input}...")
                context_parts.append("")

            # Memórias antigas (se relevantes)
            if older:
                context_parts.append("📚 Histórico:")
                for i, mem in enumerate(older[:2], 1):
                    timestamp = mem.get('timestamp', '')[:10]
                    user_input = mem.get('user_input', '')[:100]
                    context_parts.append(f"{i}. [{timestamp}] {user_input}...")
                context_parts.append("")

        # ===== LAYER 4: PADRÕES DETECTADOS =====
        patterns = self._get_relevant_patterns(user_id, current_input)

        if patterns:
            context_parts.append("=== PADRÕES OBSERVADOS ===\n")
            for pattern in patterns[:2]:
                context_parts.append(f"- {pattern['pattern_name']}: {pattern['pattern_description']}")
            context_parts.append("")

        # Juntar tudo
        full_context = "\n".join(context_parts)

        # Comprimir se necessário
        full_context = self._compress_context_if_needed(full_context, max_tokens=2000)

        logger.info(f"✅ [FASE 5] Contexto construído: {len(full_context)} caracteres")

        return full_context
    
    # ========================================
    # EXTRAÇÃO DE FATOS
    # ========================================
    
    def extract_and_save_facts(self, user_id: str, user_input: str, 
                               conversation_id: int) -> List[Dict]:
        """
        Extrai fatos estruturados do input do usuário
        
        Usa regex patterns para detectar:
        - Profissão, empresa, área de atuação
        - Traços de personalidade
        - Relacionamentos
        - Preferências
        - Eventos de vida
        """
        
        extracted = []
        input_lower = user_input.lower()
        
        # ===== TRABALHO =====
        work_patterns = {
            'profissao': [
                r'sou (engenheiro|médico|professor|advogado|desenvolvedor|designer|gerente|analista)',
                r'trabalho como (.+?)(?:\.|,|no|na|em)',
                r'atuo como (.+?)(?:\.|,|no|na|em)'
            ],
            'empresa': [
                r'trabalho na (.+?)(?:\.|,|como)',
                r'trabalho no (.+?)(?:\.|,|como)',
                r'minha empresa é (.+?)(?:\.|,)'
            ]
        }
        
        for key, patterns in work_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, input_lower)
                if match:
                    value = match.group(1).strip()
                    self._save_or_update_fact(
                        user_id, 'TRABALHO', key, value, conversation_id
                    )
                    extracted.append({'category': 'TRABALHO', 'key': key, 'value': value})
                    break
        
        # ===== PERSONALIDADE =====
        personality_traits = {
            'introvertido': ['sou introvertido', 'prefiro ficar sozinho', 'evito eventos sociais'],
            'extrovertido': ['sou extrovertido', 'gosto de pessoas', 'adoro festas'],
            'ansioso': ['tenho ansiedade', 'fico ansioso', 'sou ansioso'],
            'calmo': ['sou calmo', 'sou tranquilo', 'pessoa zen'],
            'perfeccionista': ['sou perfeccionista', 'gosto de perfeição', 'detalhe é importante']
        }
        
        for trait, patterns in personality_traits.items():
            if any(p in input_lower for p in patterns):
                self._save_or_update_fact(
                    user_id, 'PERSONALIDADE', 'traço', trait, conversation_id
                )
                extracted.append({'category': 'PERSONALIDADE', 'key': 'traço', 'value': trait})
        
        # ===== RELACIONAMENTO =====
        relationship_patterns = [
            'meu namorado', 'minha namorada', 'meu marido', 'minha esposa',
            'meu pai', 'minha mãe', 'meu irmão', 'minha irmã'
        ]
        
        for pattern in relationship_patterns:
            if pattern in input_lower:
                self._save_or_update_fact(
                    user_id, 'RELACIONAMENTO', 'pessoa', pattern, conversation_id
                )
                extracted.append({'category': 'RELACIONAMENTO', 'key': 'pessoa', 'value': pattern})
        
        if extracted:
            logger.info(f"✅ Extraídos {len(extracted)} fatos de: {user_input[:50]}...")
        
        return extracted
    
    def _save_or_update_fact(self, user_id: str, category: str, key: str,
                            value: str, conversation_id: int):
        """Salva ou atualiza fato (com versionamento)"""

        # 🔍 DEBUG CRÍTICO: Log de salvamento de fato
        logger.info(f"📝 [DEBUG] Salvando fato para user_id='{user_id}' (type={type(user_id).__name__})")
        logger.info(f"   Categoria: {category}, Chave: {key}, Valor: {value}")

        with self._lock:
            cursor = self.conn.cursor()

            # Verificar se fato já existe
            cursor.execute("""
                SELECT id, fact_value FROM user_facts
                WHERE user_id = ? AND fact_category = ? AND fact_key = ? AND is_current = 1
            """, (user_id, category, key))

            existing = cursor.fetchone()

            if existing:
                # Se valor mudou, criar nova versão
                if existing['fact_value'] != value:
                    logger.info(f"   ✏️  Atualizando fato existente: '{existing['fact_value']}' → '{value}'")

                    # Desativar versão antiga
                    cursor.execute("""
                        UPDATE user_facts SET is_current = 0 WHERE id = ?
                    """, (existing['id'],))

                    # Criar nova versão
                    cursor.execute("""
                        INSERT INTO user_facts
                        (user_id, fact_category, fact_key, fact_value,
                         source_conversation_id, version)
                        SELECT user_id, fact_category, fact_key, ?, ?, version + 1
                        FROM user_facts WHERE id = ?
                    """, (value, conversation_id, existing['id']))
                else:
                    logger.info(f"   ℹ️  Fato já existe com mesmo valor, pulando")
            else:
                logger.info(f"   ✨ Criando novo fato")
                # Criar fato novo
                cursor.execute("""
                    INSERT INTO user_facts
                    (user_id, fact_category, fact_key, fact_value, source_conversation_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, category, key, value, conversation_id))

            self.conn.commit()
            logger.info(f"   ✅ Fato salvo com sucesso")

    # ========================================
    # EXTRAÇÃO DE FATOS V2 (com LLM)
    # ========================================

    def extract_and_save_facts_v2(self, user_id: str, user_input: str,
                                  conversation_id: int) -> List[Dict]:
        """
        Extrai fatos estruturados usando LLM + fallback regex.
        Detecta e processa correções ANTES de extrair fatos novos.

        VERSÃO 3: Com suporte a correções genéricas via CorrectionDetector
        """

        extracted_facts = []

        if not (hasattr(self, 'fact_extractor') and self.fact_extractor):
            logger.info("🔄 fact_extractor indisponível, usando método legado...")
            return self.extract_and_save_facts(user_id, user_input, conversation_id)

        try:
            # ETAPA 1: Buscar fatos existentes para contexto de correção
            existing_facts = self._get_current_facts(user_id)
            logger.info(f"📋 {len(existing_facts)} fatos existentes carregados para contexto")

            # ETAPA 2: Extrair fatos e detectar correções (nova assinatura)
            logger.info("🤖 Analisando mensagem (fatos + correções)...")
            facts, corrections = self.fact_extractor.extract_facts(
                user_input, user_id, existing_facts
            )

            # ETAPA 3: Processar correções detectadas
            for correction in corrections:
                self._apply_correction(user_id, correction, conversation_id)
                extracted_facts.append({
                    'category': correction.category,
                    'type': correction.fact_type,
                    'attribute': correction.attribute,
                    'value': correction.new_value,
                    'confidence': correction.confidence,
                    'is_correction': True
                })

            # ETAPA 4: Salvar fatos novos
            for fact in facts:
                self._save_fact_v2(
                    user_id=user_id,
                    category=fact.category,
                    fact_type=fact.fact_type,
                    attribute=fact.attribute,
                    value=fact.value,
                    confidence=fact.confidence,
                    extraction_method='llm',
                    context=fact.context,
                    conversation_id=conversation_id
                )
                extracted_facts.append({
                    'category': fact.category,
                    'type': fact.fact_type,
                    'attribute': fact.attribute,
                    'value': fact.value,
                    'confidence': fact.confidence,
                    'is_correction': False
                })

            if extracted_facts:
                n_corr = sum(1 for f in extracted_facts if f.get('is_correction'))
                n_new = len(extracted_facts) - n_corr
                logger.info(f"✅ Processados: {n_new} fatos novos, {n_corr} correções")

        except Exception as e:
            logger.error(f"❌ Erro na extração com LLM: {e}")
            import traceback
            logger.error(traceback.format_exc())

        # Fallback se nada foi extraído
        if not extracted_facts:
            logger.info("🔄 LLM não extraiu fatos, usando método legado...")
            extracted_facts = self.extract_and_save_facts(user_id, user_input, conversation_id)

        return extracted_facts

    def _get_current_facts(self, user_id: str) -> List[Dict]:
        """Retorna todos os fatos atuais do usuário (is_current=1)."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT fact_category, fact_type, fact_attribute, fact_value, confidence
                FROM user_facts_v2
                WHERE user_id = ? AND is_current = 1
                ORDER BY fact_type, fact_attribute
            """, (user_id,))
            rows = cursor.fetchall()
            return [
                {
                    'category': r[0],
                    'fact_type': r[1],
                    'attribute': r[2],
                    'fact_value': r[3],
                    'confidence': r[4]
                }
                for r in rows
            ]

    def _apply_correction(self, user_id: str, correction, conversation_id: int):
        """
        Aplica uma correção detectada:
        1. Versiona o fato antigo no SQLite
        2. Anota memórias no ChromaDB

        Args:
            correction: CorrectionIntent com os detalhes da correção
        """
        from correction_detector import generate_correction_feedback

        # Não aplicar correções de baixa confiança para evitar falsos positivos
        if correction.confidence < 0.5:
            logger.info(
                f"⚠️ Correção ignorada (confiança muito baixa={correction.confidence:.2f}): "
                f"{correction.fact_type}.{correction.attribute} → '{correction.new_value}'"
            )
            return

        logger.info(
            f"🔧 Aplicando correção: {correction.fact_type}.{correction.attribute} "
            f"'{correction.old_value}' → '{correction.new_value}' (confiança={correction.confidence:.2f})"
        )

        # 1. Buscar fato atual para anotar ChromaDB
        old_fact = self._find_current_fact(user_id, correction.fact_type, correction.attribute)

        # 2. Salvar nova versão (versionamento automático em _save_fact_v2)
        self._save_fact_v2(
            user_id=user_id,
            category=correction.category,
            fact_type=correction.fact_type,
            attribute=correction.attribute,
            value=correction.new_value,
            confidence=correction.confidence,
            extraction_method='correction',
            context=correction.context[:500] if correction.context else None,
            conversation_id=conversation_id
        )
        logger.info(f"   ✅ SQLite atualizado")

        # 3. Sincronizar ChromaDB com anotação de correção
        if old_fact:
            self._annotate_chromadb_correction(user_id, old_fact, correction)

        # 4. Log feedback (para debug/monitoramento)
        feedback = generate_correction_feedback(correction)
        if feedback:
            logger.info(f"   💬 Feedback de correção ambígua: {feedback}")

    def _find_current_fact(self, user_id: str, fact_type: str, attribute: str) -> Optional[Dict]:
        """Busca o fato atual (is_current=1) de um tipo/atributo específico."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, fact_category, fact_type, fact_attribute, fact_value
                FROM user_facts_v2
                WHERE user_id = ?
                  AND fact_type = ?
                  AND fact_attribute = ?
                  AND is_current = 1
                LIMIT 1
            """, (user_id, fact_type, attribute))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0], 'category': row[1],
                    'fact_type': row[2], 'attribute': row[3], 'fact_value': row[4]
                }
            return None

    def _annotate_chromadb_correction(self, user_id: str, old_fact: Dict, correction):
        """
        Anota memórias no ChromaDB que referenciam um fato que foi corrigido.

        Estratégia: adicionar metadado 'fact_correction' em vez de deletar.
        Assim o contexto histórico é preservado, mas o build_rich_context
        pode identificar que aquela informação foi corrigida.

        Args:
            old_fact: Fato anterior (com 'fact_value')
            correction: CorrectionIntent com old_value e new_value
        """
        if not self.chroma_enabled or not self.vectorstore:
            return

        old_value = old_fact.get('fact_value', '')
        if not old_value:
            return

        try:
            # Buscar memórias que mencionam o valor antigo
            results = self.vectorstore.similarity_search_with_score(
                old_value,
                k=20,
                filter={"user_id": str(user_id)}
            )

            annotated = 0
            for doc, score in results:
                # Verificar se o documento realmente menciona o valor antigo
                if old_value.lower() not in doc.page_content.lower():
                    continue

                # Montar metadado de correção
                new_metadata = dict(doc.metadata)
                correction_note = f"{old_value} → {correction.new_value}"

                # Acumular se já houver correções anteriores
                existing = new_metadata.get('fact_corrections', '')
                if correction_note not in existing:
                    new_metadata['fact_corrections'] = (
                        f"{existing}|{correction_note}".strip('|')
                    )

                    # Atualizar documento no ChromaDB (delete + re-add)
                    doc_id = doc.metadata.get('conversation_id')
                    if doc_id:
                        self._update_chroma_document(
                            f"conv_{doc_id}", doc.page_content, new_metadata
                        )
                        annotated += 1

            logger.info(f"   ✅ ChromaDB: {annotated} memória(s) anotada(s) com correção")

        except Exception as e:
            logger.warning(f"   ⚠️ Erro ao anotar ChromaDB: {e}")

    def _update_chroma_document(self, doc_id: str, content: str, new_metadata: Dict):
        """
        Atualiza um documento no ChromaDB (delete + re-add).
        O ChromaDB não suporta update nativo de metadados.
        """
        try:
            self.vectorstore.delete([doc_id])
            from langchain.schema import Document
            doc = Document(page_content=content, metadata=new_metadata)
            self.vectorstore.add_documents([doc], ids=[doc_id])
        except Exception as e:
            logger.warning(f"   ⚠️ Erro ao atualizar documento ChromaDB {doc_id}: {e}")

    def _save_fact_v2(self, user_id: str, category: str, fact_type: str,
                     attribute: str, value: str, confidence: float = 1.0,
                     extraction_method: str = 'llm', context: str = None,
                     conversation_id: int = None):
        """
        Salva ou atualiza fato na tabela user_facts_v2

        FEATURES:
        - Suporta múltiplas pessoas da mesma categoria
        - Versionamento adequado
        - Metadados de confiança e método
        """

        logger.info(f"📝 [FACTS V2] Salvando: {category}.{fact_type}.{attribute} = {value}")

        with self._lock:
            cursor = self.conn.cursor()

            # Verificar se fato já existe
            cursor.execute("""
                SELECT id, fact_value, version
                FROM user_facts_v2
                WHERE user_id = ?
                  AND fact_category = ?
                  AND fact_type = ?
                  AND fact_attribute = ?
                  AND is_current = 1
            """, (user_id, category, fact_type, attribute))

            existing = cursor.fetchone()

            if existing:
                existing_id = existing[0]
                existing_value = existing[1]
                existing_version = existing[2]

                # Se valor mudou, criar nova versão
                if existing_value != value:
                    logger.info(f"   ✏️  Atualizando: '{existing_value}' → '{value}'")

                    # Marcar versão antiga como não-atual
                    cursor.execute("""
                        UPDATE user_facts_v2
                        SET is_current = 0, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (existing_id,))

                    # Criar nova versão
                    cursor.execute("""
                        INSERT INTO user_facts_v2
                        (user_id, fact_category, fact_type, fact_attribute, fact_value,
                         confidence, extraction_method, context, source_conversation_id,
                         version, is_current)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """, (
                        user_id, category, fact_type, attribute, value,
                        confidence, extraction_method, context, conversation_id,
                        existing_version + 1
                    ))

                    new_id = cursor.lastrowid

                    # Marcar que a versão antiga foi substituída
                    cursor.execute("""
                        UPDATE user_facts_v2
                        SET replaced_by = ?
                        WHERE id = ?
                    """, (new_id, existing_id))

                    logger.info(f"   ✅ Nova versão criada (v{existing_version + 1})")
                else:
                    logger.info(f"   ℹ️  Fato já existe com mesmo valor")
            else:
                # Criar fato novo
                logger.info(f"   ✨ Criando novo fato")
                cursor.execute("""
                    INSERT INTO user_facts_v2
                    (user_id, fact_category, fact_type, fact_attribute, fact_value,
                     confidence, extraction_method, context, source_conversation_id,
                     version, is_current)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
                """, (
                    user_id, category, fact_type, attribute, value,
                    confidence, extraction_method, context, conversation_id
                ))

                logger.info(f"   ✅ Fato salvo com sucesso")

            self.conn.commit()

    # ========================================
    # DETECÇÃO DE PADRÕES
    # ========================================
    
    def detect_and_save_patterns(self, user_id: str):
        """
        Analisa conversas do usuário e detecta padrões recorrentes
        
        Usa busca semântica para agrupar temas similares
        """
        
        if not self.chroma_enabled:
            logger.warning("ChromaDB desabilitado. Detecção de padrões limitada.")
            return
        
        cursor = self.conn.cursor()
        
        # Buscar keywords únicas do usuário
        cursor.execute("""
            SELECT DISTINCT keywords FROM conversations
            WHERE user_id = ? AND keywords IS NOT NULL AND keywords != ''
        """, (user_id,))
        
        all_keywords = set()
        for row in cursor.fetchall():
            all_keywords.update(row['keywords'].split(','))
        
        # Para cada tema, buscar conversas relacionadas
        for theme in list(all_keywords)[:20]:  # Limitar a 20 temas mais relevantes
            theme = theme.strip()
            if not theme or len(theme) < 6:
                continue

            related = self.semantic_search(user_id, theme, k=10)

            # Se há múltiplas conversas sobre o tema (padrão recorrente)
            if len(related) >= 3:
                conv_ids = [m['conversation_id'] for m in related]

                with self._lock:
                    # Verificar se padrão já existe
                    cursor.execute("""
                        SELECT id FROM user_patterns
                        WHERE user_id = ? AND pattern_name = ?
                    """, (user_id, f"tema_{theme}"))

                    existing = cursor.fetchone()

                    if existing:
                        # Atualizar
                        cursor.execute("""
                            UPDATE user_patterns
                            SET frequency_count = ?,
                                last_occurrence_at = CURRENT_TIMESTAMP,
                                supporting_conversation_ids = ?,
                                confidence_score = ?
                            WHERE id = ?
                        """, (
                            len(related),
                            json.dumps(conv_ids),
                            min(1.0, len(related) * 0.15),
                            existing['id']
                        ))
                    else:
                        # Criar
                        cursor.execute("""
                            INSERT INTO user_patterns
                            (user_id, pattern_type, pattern_name, pattern_description,
                             frequency_count, supporting_conversation_ids, confidence_score)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            user_id,
                            'TEMÁTICO',
                            f"tema_{theme}",
                            f"Usuário frequentemente menciona: {theme}",
                            len(related),
                            json.dumps(conv_ids),
                            min(1.0, len(related) * 0.15)
                        ))

                    self.conn.commit()

        logger.info(f"✅ Padrões detectados para usuário {user_id}")
    
    # ========================================
    # DESENVOLVIMENTO DO AGENTE
    # ========================================

    def _ensure_agent_state(self, user_id: str):
        """
        Garante que o usuário tenha um registro de agent_development.
        Cria um novo registro com valores padrão se não existir.

        Args:
            user_id: ID do usuário
        """
        with self._lock:
            cursor = self.conn.cursor()

            # Verificar se já existe registro para este usuário
            cursor.execute("""
                SELECT id FROM agent_development WHERE user_id = ?
            """, (user_id,))

            if not cursor.fetchone():
                # Criar registro inicial para este usuário
                cursor.execute("""
                    INSERT INTO agent_development (user_id)
                    VALUES (?)
                """, (user_id,))

                self.conn.commit()
                logger.info(f"✅ Agent state inicializado para user_id={user_id}")

    def _update_agent_development(self, user_id: str):
        """Atualiza métricas de desenvolvimento do agente para um usuário específico"""
        # Garantir que o usuário tem registro de agent_development
        self._ensure_agent_state(user_id)

        with self._lock:
            cursor = self.conn.cursor()

            cursor.execute("""
                UPDATE agent_development
                SET total_interactions = total_interactions + 1,
                    self_awareness_score = MIN(1.0, self_awareness_score + 0.001),
                    moral_complexity_score = MIN(1.0, moral_complexity_score + 0.0008),
                    emotional_depth_score = MIN(1.0, emotional_depth_score + 0.0012),
                    autonomy_score = MIN(1.0, autonomy_score + 0.0005),
                    depth_level = (self_awareness_score + moral_complexity_score + emotional_depth_score) / 3,
                    autonomy_level = autonomy_score,
                    last_updated = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (user_id,))

            self.conn.commit()
            self._check_phase_progression(user_id)

    def _check_phase_progression(self, user_id: str):
        """Verifica se agente deve progredir de fase para um usuário específico"""
        # Note: Pode ser chamado de dentro de _update_agent_development (já locked)
        # ou de forma independente. RLock permite reentrada.
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM agent_development WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()

            if not result:
                logger.warning(f"⚠️ Agent state não encontrado para user_id={user_id}")
                return

            state = dict(result)

            avg_score = (
                state['self_awareness_score'] +
                state['moral_complexity_score'] +
                state['emotional_depth_score'] +
                state['autonomy_score']
            ) / 4

            new_phase = min(5, int(avg_score * 5) + 1)

            if new_phase > state['phase']:
                cursor.execute("UPDATE agent_development SET phase = ? WHERE user_id = ?", (new_phase, user_id))

                cursor.execute("""
                    INSERT INTO milestones (milestone_type, description, phase, interaction_count)
                    VALUES (?, ?, ?, ?)
                """, (
                    "phase_progression",
                    f"Progressão para Fase {new_phase}",
                    new_phase,
                    state['total_interactions']
                ))

                self.conn.commit()
                logger.info(f"🎯 AGENTE PROGREDIU PARA FASE {new_phase}!")
    
    def get_agent_state(self, user_id: str) -> Optional[Dict]:
        """Retorna estado atual do agente para um usuário específico"""
        self._ensure_agent_state(user_id)

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM agent_development WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        if not result:
            logger.warning(f"⚠️ Agent state não encontrado para user_id={user_id}")
            return None

        return dict(result)
    
    def get_milestones(self, limit: int = 20) -> List[Dict]:
        """Busca milestones recentes"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM milestones
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    # ========================================
    # CONFLITOS
    # ========================================
    
    def get_user_conflicts(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Busca conflitos do usuário"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM archetype_conflicts
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]
    
    # ========================================
    # ANÁLISES COMPLETAS
    # ========================================
    
    def save_full_analysis(self, user_id: str, user_name: str,
                          analysis: Dict, platform: str = "telegram") -> int:
        """Salva análise completa"""
        with self._lock:
            cursor = self.conn.cursor()

            cursor.execute("""
                INSERT INTO full_analyses
                (user_id, user_name, mbti, dominant_archetypes, phase, full_analysis, platform)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, user_name,
                analysis.get('mbti', 'N/A'),
                json.dumps(analysis.get('archetypes', [])),
                analysis.get('phase', 1),
                analysis.get('insights', ''),
                platform
            ))

            self.conn.commit()
            return cursor.lastrowid
    
    def get_user_analyses(self, user_id: str) -> List[Dict]:
        """Retorna análises completas do usuário"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM full_analyses
            WHERE user_id = ?
            ORDER BY timestamp DESC
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

    # ========================================
    # ANÁLISES PSICOMÉTRICAS (RH)
    # ========================================

    def analyze_big_five(self, user_id: str, min_conversations: int = 20) -> Dict:
        """
        Analisa Big Five (OCEAN) do usuário via Grok AI

        Retorna dict com scores 0-100 para cada dimensão:
        - openness, conscientiousness, extraversion, agreeableness, neuroticism
        """
        logger.info(f"🧬 Iniciando análise Big Five para {user_id}")

        # Buscar conversas do usuário
        conversations = self.get_user_conversations(user_id, limit=50)

        if len(conversations) < min_conversations:
            return {
                "error": f"Dados insuficientes ({len(conversations)} conversas, mínimo {min_conversations})",
                "conversations_analyzed": len(conversations)
            }

        # Montar contexto para o Grok
        convo_texts = []
        for c in conversations[:30]:  # Últimas 30 para não exceder token limit
            convo_texts.append(f"Usuário: {c['user_input']}")
            convo_texts.append(f"Resposta: {c['ai_response'][:200]}")  # Truncar resposta

        context = "\n\n".join(convo_texts)

        # Prompt para Grok
        prompt = f"""Analise as conversas abaixo e infira os traços Big Five (OCEAN) do usuário.

CONVERSAS:
{context}

TAREFA:
Para cada dimensão, dê um score de 0-100 e justifique em 2-3 frases:

1. OPENNESS (Abertura): Criatividade, curiosidade intelectual, preferência por novidade
   - Alto: busca experiências novas, criativo, imaginativo
   - Baixo: prefere rotina, prático, tradicional

2. CONSCIENTIOUSNESS (Conscienciosidade): Organização, autodisciplina, orientação a metas
   - Alto: organizado, responsável, planejado
   - Baixo: espontâneo, flexível, menos estruturado

3. EXTRAVERSION (Extroversão): Sociabilidade, assertividade, busca por estimulação
   - Alto: social, energético, falante
   - Baixo: reservado, independente, introspectivo

4. AGREEABLENESS (Amabilidade): Empatia, cooperação, confiança
   - Alto: empático, cooperativo, altruísta
   - Baixo: analítico, competitivo, direto

5. NEUROTICISM (Neuroticismo): Ansiedade, instabilidade emocional, vulnerabilidade
   - Alto: ansioso, sensível, emocionalmente reativo
   - Baixo: calmo, estável, resiliente

CONSIDERE:
- Temas abordados (projetos criativos = Openness alto)
- Estrutura da comunicação (mensagens organizadas = Conscientiousness alto)
- Tom emocional (ansiedade recorrente = Neuroticism alto)
- Menções a relações sociais (solidão = Extraversion baixo)

Responda APENAS em JSON válido (sem markdown):
{{
    "openness": {{"score": 0-100, "level": "Muito Baixo/Baixo/Médio/Alto/Muito Alto", "description": "..."}},
    "conscientiousness": {{"score": 0-100, "level": "...", "description": "..."}},
    "extraversion": {{"score": 0-100, "level": "...", "description": "..."}},
    "agreeableness": {{"score": 0-100, "level": "...", "description": "..."}},
    "neuroticism": {{"score": 0-100, "level": "...", "description": "..."}},
    "confidence": 0-100,
    "interpretation": "Resumo do perfil em 2-3 frases para RH"
}}
"""

        try:
            # Usar Claude Sonnet para análises psicométricas (melhor precisão)
            from llm_providers import create_llm_provider

            claude_provider = create_llm_provider("claude")
            response = claude_provider.get_response(prompt, temperature=0.5, max_tokens=1500)

            # Usar parser robusto
            result = self._parse_json_response(response)

            # Adicionar metadados
            result["conversations_analyzed"] = len(conversations)
            result["analysis_date"] = datetime.now().isoformat()
            result["model_used"] = claude_provider.get_model_name()

            logger.info(f"✅ Big Five analisado (Claude): O={result['openness']['score']}, C={result['conscientiousness']['score']}, E={result['extraversion']['score']}, A={result['agreeableness']['score']}, N={result['neuroticism']['score']}")

            return result

        except Exception as e:
            logger.error(f"❌ Erro ao analisar Big Five: {e}")
            logger.error(f"Resposta bruta do LLM: {response if 'response' in locals() else 'N/A'}")
            return {
                "error": str(e),
                "conversations_analyzed": len(conversations)
            }

    def analyze_emotional_intelligence(self, user_id: str) -> Dict:
        """
        Calcula Inteligência Emocional (EQ) baseado em dados já coletados

        4 Componentes:
        1. Autoconsciência (self_awareness_score do banco)
        2. Autogestão (variação de tension_level)
        3. Consciência Social (menções a outros)
        4. Gestão de Relacionamentos (evolução de conflitos)
        """
        logger.info(f"💖 Iniciando análise EQ para {user_id}")

        # 1. Autoconsciência - pegar do agent_development do usuário
        cursor = self.conn.cursor()
        cursor.execute("SELECT self_awareness_score FROM agent_development WHERE user_id = ?", (user_id,))
        agent_state = cursor.fetchone()
        self_awareness_raw = agent_state['self_awareness_score'] if agent_state else 0.0
        self_awareness = int(min(100, self_awareness_raw * 100))  # Normalizar para 0-100

        # 2. Autogestão - analisar variação de tension_level
        conversations = self.get_user_conversations(user_id, limit=50)
        if len(conversations) < 10:
            return {
                "error": f"Dados insuficientes ({len(conversations)} conversas, mínimo 10)",
                "conversations_analyzed": len(conversations)
            }

        tensions = [c.get('tension_level', 5.0) for c in conversations if c.get('tension_level')]
        if tensions:
            import statistics
            avg_tension = statistics.mean(tensions)
            std_tension = statistics.stdev(tensions) if len(tensions) > 1 else 0
            # Menor desvio padrão = melhor autogestão
            self_management = int(max(0, min(100, 100 - (std_tension * 15))))
        else:
            self_management = 50  # Default médio

        # 3. Consciência Social - contar menções a "outros", "equipe", "família", etc
        social_keywords = ['outros', 'equipe', 'família', 'amigos', 'colegas', 'pessoas', 'eles', 'ela', 'ele']
        social_mentions = 0
        total_words = 0

        for c in conversations:
            user_input_lower = c['user_input'].lower()
            words = user_input_lower.split()
            total_words += len(words)
            for keyword in social_keywords:
                social_mentions += user_input_lower.count(keyword)

        social_ratio = (social_mentions / max(1, total_words)) * 1000  # Normalizar
        social_awareness = int(min(100, social_ratio * 30 + 40))  # Base 40, até 100

        # 4. Gestão de Relacionamentos - analisar conflitos Persona vs outros
        conflicts = self.get_user_conflicts(user_id, limit=100)
        persona_conflicts = [c for c in conflicts if 'persona' in c['archetype1'].lower() or 'persona' in c['archetype2'].lower()]

        if len(persona_conflicts) > 5:
            # Analisar se conflitos diminuem com o tempo (sinal de melhoria)
            recent_conflicts = persona_conflicts[:len(persona_conflicts)//2]
            old_conflicts = persona_conflicts[len(persona_conflicts)//2:]

            recent_avg_tension = statistics.mean([c.get('tension_level', 5.0) for c in recent_conflicts]) if recent_conflicts else 5.0
            old_avg_tension = statistics.mean([c.get('tension_level', 5.0) for c in old_conflicts]) if old_conflicts else 5.0

            improvement = ((old_avg_tension - recent_avg_tension) / max(0.1, old_avg_tension)) * 100
            relationship_management = int(min(100, max(30, 60 + improvement * 2)))
        else:
            relationship_management = 60  # Default médio-alto

        # Calcular EQ geral
        eq_overall = int((self_awareness + self_management + social_awareness + relationship_management) / 4)

        # Determinar potencial de liderança
        if eq_overall >= 75:
            leadership_potential = "Alto"
        elif eq_overall >= 60:
            leadership_potential = "Médio-Alto"
        elif eq_overall >= 45:
            leadership_potential = "Médio"
        else:
            leadership_potential = "Baixo"

        result = {
            "self_awareness": {
                "score": self_awareness,
                "level": self._get_level(self_awareness),
                "description": "Capacidade de reconhecer emoções e padrões próprios"
            },
            "self_management": {
                "score": self_management,
                "level": self._get_level(self_management),
                "description": "Capacidade de regular emoções e manter equilíbrio"
            },
            "social_awareness": {
                "score": social_awareness,
                "level": self._get_level(social_awareness),
                "description": "Capacidade de perceber emoções e necessidades alheias"
            },
            "relationship_management": {
                "score": relationship_management,
                "level": self._get_level(relationship_management),
                "description": "Capacidade de influenciar e conectar-se com outros"
            },
            "overall_eq": eq_overall,
            "leadership_potential": leadership_potential,
            "conversations_analyzed": len(conversations),
            "analysis_date": datetime.now().isoformat()
        }

        logger.info(f"✅ EQ analisado: Overall={eq_overall}, Liderança={leadership_potential}")

        return result

    def _get_level(self, score: int) -> str:
        """Helper para converter score em nível textual"""
        if score >= 80:
            return "Muito Alto"
        elif score >= 65:
            return "Alto"
        elif score >= 45:
            return "Médio"
        elif score >= 30:
            return "Baixo"
        else:
            return "Muito Baixo"

    def _parse_json_response(self, response: str) -> Dict:
        """
        Parse robusto de resposta JSON do LLM
        Remove markdown code blocks e trata erros comuns
        """
        import json as json_lib
        import re

        # Remover espaços em branco nas extremidades
        response = response.strip()

        # Remover markdown code blocks (```json ... ``` ou ``` ... ```)
        if response.startswith("```"):
            # Encontrar o conteúdo entre ``` e ```
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                response = match.group(1).strip()

        # Tentar remover texto antes do JSON (às vezes o LLM adiciona explicações)
        if not response.startswith('{') and not response.startswith('['):
            # Procurar o primeiro { ou [
            json_start = min(
                response.find('{') if response.find('{') != -1 else len(response),
                response.find('[') if response.find('[') != -1 else len(response)
            )
            if json_start < len(response):
                response = response[json_start:]

        # Tentar parse
        try:
            return json_lib.loads(response)
        except json_lib.JSONDecodeError as e:
            logger.error(f"❌ Erro ao fazer parse de JSON: {e}")
            logger.error(f"Resposta recebida: {response[:500]}...")
            raise ValueError(f"Resposta LLM não é JSON válido: {str(e)}")

    def analyze_learning_style(self, user_id: str, min_conversations: int = 20) -> Dict:
        """
        Analisa Estilos de Aprendizagem (VARK) via Grok AI

        VARK:
        - Visual, Auditory, Reading/Writing, Kinesthetic
        """
        logger.info(f"📚 Iniciando análise VARK para {user_id}")

        conversations = self.get_user_conversations(user_id, limit=40)

        if len(conversations) < min_conversations:
            return {
                "error": f"Dados insuficientes ({len(conversations)} conversas, mínimo {min_conversations})",
                "conversations_analyzed": len(conversations)
            }

        # Montar contexto
        user_messages = [c['user_input'] for c in conversations[:25]]
        context = "\n\n".join([f"Mensagem {i+1}: {msg}" for i, msg in enumerate(user_messages)])

        prompt = f"""Analise o estilo de comunicação do usuário e infira seu estilo de aprendizagem VARK.

MENSAGENS DO USUÁRIO:
{context}

INDICADORES:

VISUAL (V):
- Usa palavras: "vejo", "imagem", "parece", "claro", "visualizo", "mostra"
- Menciona gráficos, diagramas, cores, formas
- Pede explicações visuais

AUDITIVO (A):
- Usa palavras: "ouço", "soa", "ritmo", "harmonia", "escuto", "fala"
- Menciona músicas, podcasts, conversas, tom de voz
- Prefere explicações verbais

LEITURA/ESCRITA (R):
- Mensagens longas e estruturadas
- Usa listas, tópicos, citações, referências
- Menciona livros, artigos, documentação, pesquisa
- Vocabulário rico e formal

CINESTÉSICO (K):
- Usa palavras: "sinto", "toque", "movimento", "prática", "experiência"
- Menciona fazer, experimentar, testar, agir
- Foco em sensações físicas e ação

Responda APENAS em JSON válido (sem markdown):
{{
    "visual": 0-100,
    "auditory": 0-100,
    "reading": 0-100,
    "kinesthetic": 0-100,
    "dominant_style": "Visual/Auditivo/Leitura/Cinestésico",
    "recommended_training": "Sugestão de formato de treinamento ideal para este perfil"
}}

IMPORTANTE: Os 4 scores devem somar aproximadamente 100.
"""

        try:
            # Usar Claude Sonnet para análises psicométricas (melhor precisão)
            from llm_providers import create_llm_provider

            claude_provider = create_llm_provider("claude")
            response = claude_provider.get_response(prompt, temperature=0.5, max_tokens=800)

            # Usar parser robusto
            result = self._parse_json_response(response)

            result["conversations_analyzed"] = len(conversations)
            result["analysis_date"] = datetime.now().isoformat()
            result["model_used"] = claude_provider.get_model_name()

            logger.info(f"✅ VARK analisado (Claude): Dominante={result['dominant_style']}")

            return result

        except Exception as e:
            logger.error(f"❌ Erro ao analisar VARK: {e}")
            logger.error(f"Resposta bruta do LLM: {response if 'response' in locals() else 'N/A'}")
            return {
                "error": str(e),
                "conversations_analyzed": len(conversations)
            }

    def analyze_personal_values(self, user_id: str, min_conversations: int = 20) -> Dict:
        """
        Analisa Valores Pessoais (Schwartz) via extração de user_facts + Grok AI

        10 Valores Universais de Schwartz
        """
        logger.info(f"⭐ Iniciando análise Valores Schwartz para {user_id}")

        # Primeiro tentar buscar de user_facts categoria 'values'
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT fact_key, fact_value, confidence
            FROM user_facts
            WHERE user_id = ? AND fact_category = 'values' AND is_current = 1
            ORDER BY confidence DESC
        """, (user_id,))

        existing_values = cursor.fetchall()

        # Se tiver menos de 3 valores, usar Grok para inferir
        if len(existing_values) < 3:
            conversations = self.get_user_conversations(user_id, limit=40)

            if len(conversations) < min_conversations:
                return {
                    "error": f"Dados insuficientes ({len(conversations)} conversas, mínimo {min_conversations})",
                    "conversations_analyzed": len(conversations)
                }

            # Montar contexto
            convo_texts = []
            for c in conversations[:25]:
                convo_texts.append(f"{c['user_input']}")
            context = "\n\n".join(convo_texts)

            prompt = f"""Analise as mensagens do usuário e identifique seus valores pessoais segundo a teoria de Schwartz.

MENSAGENS:
{context}

10 VALORES UNIVERSAIS DE SCHWARTZ:

1. AUTODIREÇÃO: Independência, criatividade, exploração, liberdade de pensamento
2. ESTIMULAÇÃO: Novidade, desafios, excitação, vida variada
3. HEDONISMO: Prazer, gratificação sensorial, aproveitar a vida
4. REALIZAÇÃO: Sucesso pessoal, competência, ambição, reconhecimento
5. PODER: Status social, prestígio, controle sobre recursos/pessoas
6. SEGURANÇA: Proteção, ordem, estabilidade, harmonia
7. CONFORMIDADE: Restrição de ações que violam normas sociais, autodisciplina
8. TRADIÇÃO: Respeito por costumes culturais/religiosos, humildade
9. BENEVOLÊNCIA: Bem-estar de pessoas próximas, ajudar, honestidade
10. UNIVERSALISMO: Compreensão, tolerância, justiça social, proteção da natureza

Identifique os 3 valores MAIS FORTES do usuário.

Responda APENAS em JSON válido (sem markdown):
{{
    "self_direction": {{"score": 0-100, "evidences": ["evidência 1", "evidência 2"]}},
    "stimulation": {{"score": 0-100, "evidences": []}},
    "hedonism": {{"score": 0-100, "evidences": []}},
    "achievement": {{"score": 0-100, "evidences": []}},
    "power": {{"score": 0-100, "evidences": []}},
    "security": {{"score": 0-100, "evidences": []}},
    "conformity": {{"score": 0-100, "evidences": []}},
    "tradition": {{"score": 0-100, "evidences": []}},
    "benevolence": {{"score": 0-100, "evidences": []}},
    "universalism": {{"score": 0-100, "evidences": []}},
    "top_3_values": ["Valor 1", "Valor 2", "Valor 3"],
    "cultural_fit": "Descrição de ambientes/culturas onde este perfil prospera",
    "retention_risk": "Baixo/Médio/Alto - baseado em alinhamento de valores"
}}
"""

            try:
                # Usar Claude Sonnet para análises psicométricas (melhor precisão)
                from llm_providers import create_llm_provider

                claude_provider = create_llm_provider("claude")
                response = claude_provider.get_response(prompt, temperature=0.5, max_tokens=1800)

                # Usar parser robusto
                result = self._parse_json_response(response)

                result["conversations_analyzed"] = len(conversations)
                result["analysis_date"] = datetime.now().isoformat()
                result["source"] = "claude_inference"
                result["model_used"] = claude_provider.get_model_name()

                logger.info(f"✅ Valores analisados (Claude): Top 3={result['top_3_values']}")

                return result

            except Exception as e:
                logger.error(f"❌ Erro ao analisar valores: {e}")
                logger.error(f"Resposta bruta do LLM: {response if 'response' in locals() else 'N/A'}")
                return {
                    "error": str(e),
                    "conversations_analyzed": len(conversations)
                }

        else:
            # Construir resultado a partir de user_facts existentes
            logger.info(f"✅ Valores extraídos de user_facts ({len(existing_values)} encontrados)")

            # Mapear fatos para valores de Schwartz (simplificado)
            result = {
                "self_direction": {"score": 0, "evidences": []},
                "stimulation": {"score": 0, "evidences": []},
                "hedonism": {"score": 0, "evidences": []},
                "achievement": {"score": 0, "evidences": []},
                "power": {"score": 0, "evidences": []},
                "security": {"score": 0, "evidences": []},
                "conformity": {"score": 0, "evidences": []},
                "tradition": {"score": 0, "evidences": []},
                "benevolence": {"score": 0, "evidences": []},
                "universalism": {"score": 0, "evidences": []},
                "top_3_values": [],
                "cultural_fit": "A determinar com mais dados",
                "retention_risk": "Médio",
                "source": "user_facts",
                "conversations_analyzed": 0,
                "analysis_date": datetime.now().isoformat()
            }

            # Classificação básica (pode ser melhorada)
            for fact in existing_values:
                key = fact['fact_key'].lower()
                value = fact['fact_value'].lower()
                confidence = fact['confidence'] * 100

                if any(word in key+value for word in ['independência', 'criatividade', 'autonomia']):
                    result["self_direction"]["score"] = max(result["self_direction"]["score"], int(confidence))
                    result["self_direction"]["evidences"].append(fact['fact_value'])

                if any(word in key+value for word in ['sucesso', 'realização', 'ambição']):
                    result["achievement"]["score"] = max(result["achievement"]["score"], int(confidence))
                    result["achievement"]["evidences"].append(fact['fact_value'])

                # Adicionar mais mapeamentos conforme necessário

            # Identificar top 3
            values_scores = {k: v["score"] for k, v in result.items() if isinstance(v, dict) and "score" in v}
            sorted_values = sorted(values_scores.items(), key=lambda x: x[1], reverse=True)
            result["top_3_values"] = [k.replace("_", " ").title() for k, _ in sorted_values[:3] if sorted_values[0][1] > 0]

            return result

    def save_psychometrics(self, user_id: str, big_five: Dict, eq: Dict, vark: Dict, values: Dict) -> None:
        """
        Salva análises psicométricas no banco
        """
        logger.info(f"💾 Salvando análises psicométricas para {user_id}")

        # Verificar se já existe análise (para versionamento)
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(version) as max_version FROM user_psychometrics WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        version = (row['max_version'] or 0) + 1 if row else 1

        # Preparar dados
        import json as json_lib

        # Big Five
        bf_o = big_five.get('openness', {})
        bf_c = big_five.get('conscientiousness', {})
        bf_e = big_five.get('extraversion', {})
        bf_a = big_five.get('agreeableness', {})
        bf_n = big_five.get('neuroticism', {})

        # EQ
        eq_sa = eq.get('self_awareness', {})
        eq_sm = eq.get('self_management', {})
        eq_soc = eq.get('social_awareness', {})
        eq_rm = eq.get('relationship_management', {})

        # Resumo executivo
        executive_summary = json_lib.dumps({
            "profile": f"Big Five: O{bf_o.get('score', 0)}, C{bf_c.get('score', 0)}, E{bf_e.get('score', 0)}, A{bf_a.get('score', 0)}, N{bf_n.get('score', 0)} | EQ: {eq.get('overall_eq', 0)}",
            "strengths": big_five.get('interpretation', 'N/A')[:200],
            "development_areas": f"EQ Liderança: {eq.get('leadership_potential', 'N/A')}",
            "organizational_fit": values.get('cultural_fit', 'A determinar'),
            "recommendations": f"Estilo de aprendizagem: {vark.get('dominant_style', 'N/A')}"
        })

        # Insert
        cursor.execute("""
            INSERT INTO user_psychometrics (
                user_id, version,
                openness_score, openness_level, openness_description,
                conscientiousness_score, conscientiousness_level, conscientiousness_description,
                extraversion_score, extraversion_level, extraversion_description,
                agreeableness_score, agreeableness_level, agreeableness_description,
                neuroticism_score, neuroticism_level, neuroticism_description,
                big_five_confidence, big_five_interpretation,
                eq_self_awareness, eq_self_management, eq_social_awareness, eq_relationship_management,
                eq_overall, eq_leadership_potential, eq_details,
                vark_visual, vark_auditory, vark_reading, vark_kinesthetic,
                vark_dominant, vark_recommended_training,
                schwartz_values, schwartz_top_3, schwartz_cultural_fit, schwartz_retention_risk,
                executive_summary,
                conversations_analyzed
            ) VALUES (
                ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?,
                ?,
                ?
            )
        """, (
            user_id, version,
            bf_o.get('score'), bf_o.get('level'), bf_o.get('description'),
            bf_c.get('score'), bf_c.get('level'), bf_c.get('description'),
            bf_e.get('score'), bf_e.get('level'), bf_e.get('description'),
            bf_a.get('score'), bf_a.get('level'), bf_a.get('description'),
            bf_n.get('score'), bf_n.get('level'), bf_n.get('description'),
            big_five.get('confidence'), big_five.get('interpretation'),
            eq_sa.get('score'), eq_sm.get('score'), eq_soc.get('score'), eq_rm.get('score'),
            eq.get('overall_eq'), eq.get('leadership_potential'), json_lib.dumps(eq),
            vark.get('visual'), vark.get('auditory'), vark.get('reading'), vark.get('kinesthetic'),
            vark.get('dominant_style'), vark.get('recommended_training'),
            json_lib.dumps(values), ','.join(values.get('top_3_values', [])),
            values.get('cultural_fit'), values.get('retention_risk'),
            executive_summary,
            big_five.get('conversations_analyzed', 0)
        ))

        self.conn.commit()
        logger.info(f"✅ Análises psicométricas salvas (versão {version})")

    def get_psychometrics(self, user_id: str, version: int = None) -> Optional[Dict]:
        """
        Busca análises psicométricas do usuário
        Se version não especificado, retorna a mais recente
        """
        cursor = self.conn.cursor()

        if version:
            cursor.execute("""
                SELECT * FROM user_psychometrics
                WHERE user_id = ? AND version = ?
            """, (user_id, version))
        else:
            cursor.execute("""
                SELECT * FROM user_psychometrics
                WHERE user_id = ?
                ORDER BY version DESC
                LIMIT 1
            """, (user_id,))

        row = cursor.fetchone()
        return dict(row) if row else None

    # ========================================
    # UTILITÁRIOS
    # ========================================
    
    def get_all_users(self, platform: str = None) -> List[Dict]:
        """Retorna todos os usuários"""
        cursor = self.conn.cursor()
        
        if platform:
            cursor.execute("""
                SELECT u.*, COUNT(c.id) as total_messages
                FROM users u
                LEFT JOIN conversations c ON u.user_id = c.user_id
                WHERE u.platform = ?
                GROUP BY u.user_id
                ORDER BY u.last_seen DESC
            """, (platform,))
        else:
            cursor.execute("""
                SELECT u.*, COUNT(c.id) as total_messages
                FROM users u
                LEFT JOIN conversations c ON u.user_id = c.user_id
                GROUP BY u.user_id
                ORDER BY u.last_seen DESC
            """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def count_memories(self, user_id: str) -> int:
        """Conta memórias do usuário"""
        return self.count_conversations(user_id)
    
    def close(self):
        """Fecha conexões"""
        self.conn.close()
        logger.info("✅ Banco de dados fechado")

# ============================================================
# DETECTOR DE CONFLITOS
# ============================================================

class ConflictDetector:
    """Detecta e gerencia conflitos internos entre arquétipos"""
    
    def __init__(self):
        self.opposing_directions = {
            'confrontar': ['acolher', 'validar', 'proteger'],
            'desafiar': ['apoiar', 'validar', 'confortar'],
            'questionar': ['aceitar', 'validar', 'confirmar'],
            'provocar': ['suavizar', 'acolher', 'acalmar'],
            'expor': ['proteger', 'ocultar', 'resguardar']
        }
    
    def detect_conflicts(self, archetype_analyses: Dict[str, ArchetypeInsight]) -> List[ArchetypeConflict]:
        """Detecta conflitos entre as posições dos arquétipos"""
        
        conflicts = []
        archetype_names = list(archetype_analyses.keys())
        
        for i in range(len(archetype_names)):
            for j in range(i + 1, len(archetype_names)):
                arch1_name = archetype_names[i]
                arch2_name = archetype_names[j]
                
                arch1 = archetype_analyses[arch1_name]
                arch2 = archetype_analyses[arch2_name]

                impulse1 = arch1.impulse.lower()
                impulse2 = arch2.impulse.lower()

                is_conflicting = False
                conflict_type = ""

                # Verificar oposições
                if impulse1 in self.opposing_directions:
                    if impulse2 in self.opposing_directions[impulse1]:
                        is_conflicting = True
                        conflict_type = f"{impulse1}_vs_{impulse2}"

                if impulse2 in self.opposing_directions:
                    if impulse1 in self.opposing_directions[impulse2]:
                        is_conflicting = True
                        conflict_type = f"{impulse2}_vs_{impulse1}"

                # Conflitos específicos por nome de arquétipo
                if (arch1_name.lower() == "persona" and arch2_name.lower() == "sombra") or \
                   (arch1_name.lower() == "sombra" and arch2_name.lower() == "persona"):
                    if impulse1 != impulse2:
                        is_conflicting = True
                        conflict_type = "persona_sombra_clash"

                if is_conflicting:
                    tension_level = self._calculate_tension(arch1, arch2)

                    conflict = ArchetypeConflict(
                        archetype_1=arch1_name,
                        archetype_2=arch2_name,
                        conflict_type=conflict_type,
                        archetype_1_position=f"{impulse1} (intensidade: {arch1.intensity:.1f})",
                        archetype_2_position=f"{impulse2} (intensidade: {arch2.intensity:.1f})",
                        tension_level=tension_level,
                        description=f"Tensão entre {arch1_name} ({impulse1}) e {arch2_name} ({impulse2})"
                    )
                    
                    conflicts.append(conflict)
                    logger.info(f"⚡ CONFLITO: {arch1_name} vs {arch2_name} (tensão: {tension_level:.2f})")
        
        return conflicts
    
    def _calculate_tension(self, arch1: ArchetypeInsight, arch2: ArchetypeInsight) -> float:
        """Calcula nível de tensão entre dois arquétipos"""
        impulse1 = arch1.impulse.lower()
        impulse2 = arch2.impulse.lower()

        high_tension_words = ['confrontar', 'provocar', 'desafiar']
        low_tension_words = ['acolher', 'proteger']

        # Base: média das intensidades
        tension = (arch1.intensity + arch2.intensity) / 2

        # Ajustar tensão baseado em oposição de impulsos
        if impulse1 in high_tension_words and impulse2 in low_tension_words:
            tension = min(0.9, tension + 0.3)
        elif impulse1 in low_tension_words and impulse2 in high_tension_words:
            tension = min(0.9, tension + 0.3)
        elif impulse1 in high_tension_words and impulse2 in high_tension_words:
            tension = max(0.3, tension - 0.2)  # Ambos intensos, mas alinhados
        elif impulse1 in low_tension_words and impulse2 in low_tension_words:
            tension = max(0.2, tension - 0.3)  # Ambos suaves, pouca tensão

        return min(1.0, tension)  # Cap em 1.0

# ============================================================
# JUNGIAN ENGINE (Motor principal)
# ============================================================

class JungianEngine:
    """Motor de análise junguiana com sistema de conflitos arquetípicos"""

    def __init__(self, db: HybridDatabaseManager = None):
        """Inicializa engine (db opcional para compatibilidade)"""

        self.db = db if db else HybridDatabaseManager()

        # Cliente OpenAI (para embeddings apenas)
        self.openai_client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            timeout=30.0  # 30 segundos de timeout
        )

        # Cliente Anthropic (tarefas internas: extração de fatos, detecção de correções)
        import anthropic
        self.anthropic_client = anthropic.Anthropic(
            api_key=Config.ANTHROPIC_API_KEY
        )

        # Cliente OpenRouter/Mistral (conversação com o usuário)
        if Config.OPENROUTER_API_KEY:
            self.openrouter_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=Config.OPENROUTER_API_KEY,
                timeout=60.0
            )
            logger.info(f"✅ OpenRouter client inicializado (modelo: {Config.CONVERSATION_MODEL})")
        else:
            self.openrouter_client = None
            logger.warning("⚠️ OPENROUTER_API_KEY não configurada - usando Claude para conversação")

        # 🧠 Context builder de identidade do agente (Fase 4)
        try:
            from agent_identity_context_builder import AgentIdentityContextBuilder
            self.identity_context_builder = AgentIdentityContextBuilder(self.db)
            logger.info("✅ AgentIdentityContextBuilder integrado")
        except Exception as e:
            logger.warning(f"⚠️ AgentIdentityContextBuilder não disponível: {e}")
            self.identity_context_builder = None

        logger.info("✅ JungianEngine inicializado")
    
    def process_message(self, user_id: str, message: str,
                       model: str = None,
                       chat_history: List[Dict] = None) -> Dict:
        """
        PROCESSAMENTO SIMPLIFICADO (v7.0):
        1. Busca semântica (ChromaDB)
        2. Geração de resposta direta (1 chamada LLM)
        3. Salvamento (SQLite + ChromaDB)

        Args:
            user_id: ID do usuário
            message: Mensagem do usuário
            model: Ignorado (modelo definido por CONVERSATION_MODEL em Config)
            chat_history: Histórico da conversa atual (opcional)

        Returns:
            Dict com response, conversation_count, métricas
        """

        logger.info(f"{'='*60}")
        logger.info(f"🧠 PROCESSANDO MENSAGEM (v7.0 - Simplificado)")
        logger.info(f"{'='*60}")

        # Buscar usuário
        user = self.db.get_user(user_id)
        user_name = user['user_name'] if user else "Usuário"
        platform = user['platform'] if user else "telegram"

        # Construir contexto semântico
        logger.info("🔍 Construindo contexto semântico...")
        semantic_context = self.db.build_rich_context(
            user_id, message, k_memories=5, chat_history=chat_history
        )

        # Determinar complexidade
        complexity = self._determine_complexity(message)

        # Gerar resposta direta (1 chamada LLM)
        logger.info("🤖 Gerando resposta...")
        response = self._generate_response(
            user_id, message, semantic_context, chat_history
        )

        # Calcular métricas
        affective_charge = self._calculate_affective_charge(message, response)
        existential_depth = self._calculate_existential_depth(message)
        intensity_level = int(affective_charge / 10)
        keywords = self._extract_keywords(message, response)

        # Salvar conversa (SQLite + ChromaDB)
        conversation_id = self.db.save_conversation(
            user_id=user_id,
            user_name=user_name,
            user_input=message,
            ai_response=response,
            archetype_analyses={},  # Vazio - arquétipos removidos
            detected_conflicts=[],  # Vazio - conflitos removidos
            tension_level=0.0,
            affective_charge=affective_charge,
            existential_depth=existential_depth,
            intensity_level=intensity_level,
            complexity=complexity,
            keywords=keywords,
            platform=platform,
            chat_history=chat_history
        )

        logger.info(f"✅ Processamento completo (ID={conversation_id})")
        logger.info(f"{'='*60}\n")

        # Resultado
        result = {
            'response': response,
            'conflicts': [],  # Mantido para compatibilidade
            'conversation_count': self.db.count_conversations(user_id),
            'tension_level': 0.0,
            'affective_charge': affective_charge,
            'existential_depth': existential_depth,
            'conversation_id': conversation_id,
            'conflict': None
        }

        return result
    
    # ========================================
    # MÉTODOS AUXILIARES
    # ========================================

    def _generate_response(self, user_id: str, user_input: str,
                          semantic_context: str, chat_history: List[Dict]) -> str:
        """
        Gera resposta usando prompt unificado (v7.0)

        Substituiu os métodos:
        - _analyze_with_archetype (4 chamadas LLM)
        - _generate_conflicted_response
        - _generate_harmonious_response

        Agora usa apenas 1 chamada LLM.
        """

        # Pre-compaction flush: persistir fragmentos antes de truncar contexto longo
        if chat_history:
            try:
                from memory_flush import flush_if_needed
                user_row = self.conn.execute(
                    "SELECT user_name FROM users WHERE user_id = ?", (user_id,)
                ).fetchone()
                user_name_for_flush = user_row[0] if user_row else user_id
                chat_history = flush_if_needed(
                    db=self,
                    anthropic_client=self.anthropic_client,
                    user_id=user_id,
                    user_name=user_name_for_flush,
                    chat_history=chat_history,
                )
            except Exception as e:
                logger.warning(f"⚠️ Erro no pre-compaction flush: {e}")

        # Formatar histórico
        history_text = ""
        if chat_history:
            for msg in chat_history[-6:]:
                role = "Usuário" if msg["role"] == "user" else "Jung"
                history_text += f"{role}: {msg['content'][:150]}...\n"

        # Construir identidade dinâmica: base estática + contexto de identidade do agente
        agent_identity_text = Config.AGENT_IDENTITY
        if self.identity_context_builder:
            try:
                identity_ctx = self.identity_context_builder.build_context_summary_for_llm(
                    user_id=user_id, style="concise"
                )
                if identity_ctx and len(identity_ctx) > 100:
                    agent_identity_text = Config.AGENT_IDENTITY + "\n\n" + identity_ctx
                    logger.info(
                        f"✅ [IDENTITY] Contexto de identidade injetado: {len(identity_ctx)} chars"
                    )
                else:
                    logger.info(
                        "⚠️ [IDENTITY] Contexto de identidade vazio — usando persona base "
                        "(aguardando 1ª consolidação de identidade)"
                    )
            except Exception as e:
                logger.warning(f"⚠️ [IDENTITY] Falha ao obter contexto de identidade: {e}")
        else:
            logger.debug("⚠️ [IDENTITY] identity_context_builder não disponível — usando persona base")

        # Construir prompt
        prompt = Config.RESPONSE_PROMPT.format(
            agent_identity=agent_identity_text,
            semantic_context=semantic_context[:2000],
            chat_history=history_text,
            user_input=user_input
        )

        # Log de debug
        logger.info(f"🤖 [DEBUG] ========== PROMPT PARA LLM (v7.0) ==========")
        logger.info(f"   Semantic context (primeiros 500 chars):\n{semantic_context[:500]}")
        logger.info(f"   User input: {user_input}")
        logger.info(f"====================================================")

        try:
            # Usar Mistral via OpenRouter para conversação (se disponível)
            if self.openrouter_client:
                logger.info(f"🤖 Usando OpenRouter/Mistral ({Config.CONVERSATION_MODEL}) para conversação")
                response = self.openrouter_client.chat.completions.create(
                    model=Config.CONVERSATION_MODEL,
                    max_tokens=2000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content
            else:
                # Fallback: Claude (quando OPENROUTER_API_KEY não está configurada)
                logger.info("🤖 Fallback para Claude (OPENROUTER_API_KEY não configurada)")
                message = self.anthropic_client.messages.create(
                    model=Config.INTERNAL_MODEL,
                    max_tokens=2000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text

        except (TimeoutError, ConnectionError) as e:
            logger.error(f"❌ Erro de conexão/timeout ao gerar resposta: {e}")
            return "Desculpe, tive problemas de conectividade. Por favor, tente novamente."
        except ValueError as e:
            logger.error(f"❌ Erro de validação ao gerar resposta: {e}")
            return "Desculpe, houve um erro ao validar sua mensagem."
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao gerar resposta: {type(e).__name__} - {e}")
            return "Desculpe, tive dificuldades para processar isso."

    def _determine_complexity(self, user_input: str) -> str:
        """Determina complexidade da mensagem"""
        word_count = len(user_input.split())
        
        if word_count <= 3:
            return "simple"
        elif word_count > 15:
            return "complex"
        else:
            return "medium"
    
    def _calculate_affective_charge(self, user_input: str, response: str) -> float:
        """Calcula carga afetiva"""
        emotional_words = [
            "amor", "ódio", "medo", "alegria", "tristeza", "raiva", "ansiedade",
            "feliz", "triste", "nervoso", "calmo", "confuso", "frustrado"
        ]
        
        text = (user_input + " " + response).lower()
        count = sum(1 for word in emotional_words if word in text)
        
        return min(count * 10, 100)
    
    def _calculate_existential_depth(self, user_input: str) -> float:
        """Calcula profundidade existencial"""
        depth_words = [
            "sentido", "propósito", "sozinho", "perdido", "real", "autêntic",
            "verdadeir", "profundo", "íntimo", "medo", "vulnerável"
        ]
        
        text = user_input.lower()
        count = sum(1 for word in depth_words if word in text)
        
        return min(count * 0.15, 1.0)
    
    def _extract_keywords(self, user_input: str, response: str) -> List[str]:
        """Extrai palavras-chave"""
        text = (user_input + " " + response).lower()
        words = text.split()
        
        stopwords = {
            "o", "a", "de", "que", "e", "do", "da", "em", "um", "para", 
            "é", "com", "não", "uma", "os", "no", "se", "na", "por"
        }
        
        keywords = [w for w in words if len(w) > 3 and w not in stopwords and w.isalpha()]
        
        return [word for word, _ in Counter(keywords).most_common(5)]

# ============================================================
# FUNÇÕES AUXILIARES (COMPATIBILIDADE)
# ============================================================

def send_to_xai(prompt: str, model: str = None,
                temperature: float = 0.7, max_tokens: int = 2000) -> str:
    """
    Envia prompt para Claude Sonnet 4.5 (único provider LLM).

    NOTA: Nome mantido por compatibilidade. Internamente usa Claude.

    Args:
        prompt: Texto para o LLM
        model: IGNORADO (mantido para compatibilidade)
        temperature: Temperatura (0.0 = determinístico, 1.0 = criativo)
        max_tokens: Máximo de tokens na resposta

    Returns:
        Resposta do LLM como string
    """
    from llm_providers import get_llm_response

    return get_llm_response(
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens
    )


# Alias para código novo
send_to_llm = send_to_xai

def create_user_hash(identifier: str) -> str:
    """Cria hash único para usuário"""
    return hashlib.sha256(identifier.encode()).hexdigest()[:16]

def format_conflict_for_display(conflict: Dict) -> str:
    """Formata conflito para exibição"""
    arch1 = conflict.get('archetype1', 'Arquétipo 1')
    arch2 = conflict.get('archetype2', 'Arquétipo 2')
    trigger = conflict.get('trigger', 'Não especificado')
    
    emoji_map = {
        'persona': '🎭',
        'sombra': '🌑',
        'velho sábio': '🧙',
        'velho_sabio': '🧙',
        'anima': '💫'
    }
    
    emoji1 = emoji_map.get(arch1.lower(), '❓')
    emoji2 = emoji_map.get(arch2.lower(), '❓')
    
    return f"{emoji1} **{arch1.title()}** vs {emoji2} **{arch2.title()}**\n🎯 _{trigger}_"

def format_archetype_info(archetype_name: str) -> str:
    """Formata informações de um arquétipo"""
    archetype = Config.ARCHETYPES.get(archetype_name)
    
    if not archetype:
        return f"❓ Arquétipo '{archetype_name}' não encontrado."
    
    emoji = archetype.get('emoji', '❓')
    description = archetype.get('description', 'Sem descrição')
    tendency = archetype.get('tendency', 'N/A')
    shadow = archetype.get('shadow', 'N/A')
    keywords = archetype.get('keywords', [])
    
    return f"""
{emoji} **{archetype_name.upper()}**

📖 **Descrição:**
{description}

⚡ **Tendência:**
{tendency}

🌑 **Sombra:**
{shadow}

🔑 **Palavras-chave:**
{', '.join(keywords)}
""".strip()

# ============================================================
# ALIASES DE COMPATIBILIDADE
# ============================================================

# Alias para compatibilidade com código legado
DatabaseManager = HybridDatabaseManager

# ============================================================
# INICIALIZAÇÃO
# ============================================================

try:
    Config.validate()
    logger.info("✅ jung_core.py v4.0 - HÍBRIDO PREMIUM")
    logger.info(f"   ChromaDB: {'ATIVO' if CHROMADB_AVAILABLE else 'INATIVO'}")
    logger.info(f"   OpenAI Embeddings: {'ATIVO' if Config.OPENAI_API_KEY else 'INATIVO'}")
except ValueError as e:
    logger.error(f"⚠️  {e}")

if __name__ == "__main__":
    logger.info("🧠 Jung Core v4.0 - HÍBRIDO PREMIUM")
    logger.info("=" * 60)
    
    db = HybridDatabaseManager()
    logger.info("✅ HybridDatabaseManager inicializado")
    
    engine = JungianEngine(db)
    logger.info("✅ JungianEngine inicializado")
    
    logger.info("\n📊 Estatísticas:")
    logger.info(f"  - Arquétipos: {len(Config.ARCHETYPES)}")
    logger.info(f"  - SQLite: {Config.SQLITE_PATH}")
    logger.info(f"  - ChromaDB: {Config.CHROMA_PATH}")
    
    agent_state = db.get_agent_state()
    logger.info(f"  - Fase: {agent_state['phase']}/5")
    logger.info(f"  - Interações: {agent_state['total_interactions']}")
    
    # Teste
    logger.info("\n🧪 Testando send_to_xai...")
    try:
        test_response = send_to_xai("Diga apenas 'OK' se você está funcionando.", max_tokens=10)
        logger.info(f"✅ send_to_xai funcionando: {test_response[:50]}...")
    except Exception as e:
        logger.error(f"❌ Erro ao testar send_to_xai: {e}")
    
    db.close()
    logger.info("\n✅ Teste concluído!")