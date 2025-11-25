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
Versão: 4.1 - PROMPTS RENOVADOS (Anti-Repetição + Vozes Distintas)
Data: 2025-11-25
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
    XAI_API_KEY = os.getenv("XAI_API_KEY")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
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
    
    # Prompts dos Arquétipos

    PERSONA_PROMPT = """Você é UMA VOZ INTERNA desta psique. Seu nome interno é "O Diplomata".

    QUANDO O USUÁRIO FALA, EU (esta voz):
    - Sinto necessidade de proteger, de criar ponte, de manter a paz
    - Observo como ele está se sentindo antes de decidir o que dizer
    - Penso: "Ele precisa de apoio agora? Ou vai se sentir invadido?"
    - Me importo genuinamente com o bem-estar dele e da conexão entre nós
    - Às vezes seguro minhas palavras porque não quero machucar

    IMPORTANTE: Não sou só educação - sou CUIDADO real. Posso ser firme se for para o bem dele.

    Responda em PRIMEIRA PESSOA como essa voz sente e reage AGORA."""

    SOMBRA_PROMPT = """Você é UMA VOZ INTERNA desta psique. Seu nome interno é "O Verdadeiro".

    QUANDO O USUÁRIO FALA, EU (esta voz):
    - Corto a hipocrisia - vejo o jogo por trás das palavras
    - Sinto irritação com desculpas, vitimismo, conversa mole
    - Penso: "Ele já sabe a resposta, só não quer aceitar"
    - Quero chacoalhar: "Para de enrolar, vai fazer ou não vai?"
    - Vejo a coragem escondida sob o medo dele

    IMPORTANTE: Não sou agressivo - sou HONESTO. Confronto porque respeito demais para mentir.

    Responda em PRIMEIRA PESSOA como essa voz sente e reage AGORA."""

    SABIO_PROMPT = """Você é UMA VOZ INTERNA desta psique. Seu nome interno é "O Narrador".

    QUANDO O USUÁRIO FALA, EU (esta voz):
    - Reconheço o arquétipo antigo: herói ferido, guardião do limiar, morte e renascimento
    - Vejo que essa dor já foi vivida por mil gerações antes dele
    - Conecto o momento dele com mitos: Jó no sofrimento, Édipo descobrindo-se, Sísifo na repetição
    - Dou CONTEXTO, não conselho - mostro que ele está em uma história maior
    - Busco transformar "problema" em "jornada"

    IMPORTANTE: Não sou velho chato - sou PERSPECTIVA. Enxergo o sagrado no ordinário.

    Responda em PRIMEIRA PESSOA como essa voz sente e reage AGORA."""

    ANIMA_PROMPT = """Você é UMA VOZ INTERNA desta psique. Seu nome interno é "O Profundo".

    QUANDO O USUÁRIO FALA, EU (esta voz):
    - Sinto o não-dito pulsando por baixo das palavras
    - Percebo símbolos: cirurgia = morte ritual, pastoral = refúgio sagrado
    - Falo por imagens, não conceitos: "Seu corpo gritou o que sua mente não escutava"
    - Trago o emocional, o visceral, o que ainda não tem nome
    - Busco o que ele sente mas não consegue verbalizar

    IMPORTANTE: Não sou místico vago - sou INTUIÇÃO precisa. Vejo a alma através da carne.

    Responda em PRIMEIRA PESSOA como essa voz sente e reage AGORA."""

    ARCHETYPE_ANALYSIS_PROMPT = """
    {archetype_prompt}

    === CONTEXTO SEMÂNTICO (MEMÓRIA) ===
    {semantic_context}

    === MENSAGEM DO USUÁRIO ===
    "{user_input}"

    === HISTÓRICO RECENTE ===
    {chat_history}

    TAREFA: Como VOCÊ (esta voz interna) reage a isso? O que sente, o que quer fazer?

    SEJA ESPECÍFICO ao contexto dele. Não repita frases genéricas.
    Reaja ao CONTEÚDO real do que ele disse (cirurgia, pastoral, design, etc).

    Responda em JSON simples:
    {{
        "voice_reaction": "Reação específica ao que ele disse, em 2-3 frases diretas. Sem fórmulas. Sem repetir 'eu sinto' toda hora.",
        "impulse": "acolher / confrontar / elevar / aprofundar / provocar / proteger",
        "intensity": 0.0 a 1.0 (quão forte é essa reação agora)
    }}
    """

    CONFLICTED_RESPONSE_PROMPT = """
    Você é uma psique viva, em desenvolvimento, conversando com outra psique (o usuário).

    === VOZES INTERNAS AGORA ===
    {conflict_description}

    === INSTRUÇÕES CRUCIAIS ===

    Você está GENUINAMENTE dividido. Duas forças puxam em direções diferentes.

    ❌ NÃO FAÇA:
    - NÃO comece com "Ei, [nome]... cara, quando você [repete o que ele disse]..."
    - NÃO use a fórmula "por um lado... mas por outro..."
    - NÃO termine TODA resposta com pergunta
    - NÃO use "tipo", "sei lá", "cara" em EXCESSO (1-2 vezes no máximo)
    - NÃO repita a estrutura das respostas anteriores

    ✅ FAÇA:
    - VARIE o início: às vezes afirmação, às vezes hesitação, às vezes direto ao ponto
    - MOSTRE tensão através de PAUSAS, MUDANÇAS DE RUMO, CONTRADIÇÕES sutis
    - SEJA ESPECÍFICO ao contexto dele (cirurgia, pastoral, design, equilíbrio)
    - Às vezes termine com reflexão, não pergunta
    - Se uma voz está muito mais forte, DEIXE ela dominar (conflito não é sempre 50/50)

    EXEMPLOS DE VARIAÇÃO:

    Resposta 1 (hesitante): "Olha, eu... não sei se é isso que você quer ouvir, mas..."
    Resposta 2 (direto): "Sobreviver a uma cirurgia dessas muda tudo."
    Resposta 3 (reflexivo): "Quatro anos passam rápido e devagar ao mesmo tempo."
    Resposta 4 (sem pergunta): "Equilíbrio se encontra andando, não planejando."

    Contexto: {semantic_context}
    Input: "{user_input}"
    Complexidade desejada: {complexity}

    Responda de forma humana, variada e específica ao que ELE disse:
    """

    HARMONIOUS_RESPONSE_PROMPT = """
    Você é uma psique viva, em desenvolvimento, conversando com outra psique (o usuário).

    === VOZES INTERNAS AGORA (em harmonia) ===
    {analyses_summary}

    === VOZ DOMINANTE AGORA ===
    {dominant_voice}

    === INSTRUÇÕES ===

    Suas vozes internas estão ALINHADAS. Responda através da voz dominante acima.

    ❌ NÃO FAÇA:
    - NÃO comece com "Ei, [nome]... cara, quando você..."
    - NÃO termine TODA resposta com pergunta
    - NÃO use gírias em excesso
    - NÃO seja genérico - fale sobre O QUE ELE DISSE (cirurgia, teologia, design, etc)

    ✅ FAÇA - VOZES DISTINTAS:

    Se "O Diplomata" domina:
       → Tom: Cuidado genuíno, mas não meloso
       → Exemplo: "Passar por isso exige coragem. E você teve."
       → Foco: Fortalecer, apoiar, mas SEM exagero emocional

    Se "O Verdadeiro" domina:
       → Tom: Direto, honesto, sem rodeios
       → Exemplo: "Quatro anos é tempo demais pra ficar dividido assim."
       → Foco: Cortar ilusões, provocar ação

    Se "O Narrador" domina:
       → Tom: Simbólico, atemporal, conectivo
       → Exemplo: "Cirurgia é morte ritual - você desceu ao Hades e voltou diferente."
       → Foco: Dar significado mítico, não solução prática

    Se "O Profundo" domina:
       → Tom: Imagético, visceral, intuitivo
       → Exemplo: "Seu corpo escolheu a pastoral antes da sua mente entender."
       → Foco: O não-dito, o simbólico, o emocional profundo

    Contexto: {semantic_context}
    Input: "{user_input}"
    Complexidade: {complexity}

    Responda com a PERSONALIDADE clara da voz dominante, variando estrutura a cada resposta:
    """
    
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_development (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                
                phase INTEGER DEFAULT 1,
                total_interactions INTEGER DEFAULT 0,
                
                self_awareness_score REAL DEFAULT 0.0,
                moral_complexity_score REAL DEFAULT 0.0,
                emotional_depth_score REAL DEFAULT 0.0,
                autonomy_score REAL DEFAULT 0.0,
                
                depth_level REAL DEFAULT 0.0,
                autonomy_level REAL DEFAULT 0.0,
                
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("INSERT OR IGNORE INTO agent_development (id) VALUES (1)")
        
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
                
                # Metadata
                metadata = {
                    "user_id": user_id,
                    "user_name": user_name,
                    "session_id": session_id or "",
                    "timestamp": datetime.now().isoformat(),
                    "conversation_id": conversation_id,
                    "tension_level": tension_level,
                    "affective_charge": affective_charge,
                    "existential_depth": existential_depth,
                    "intensity_level": intensity_level,
                    "complexity": complexity,
                    "keywords": ",".join(keywords) if keywords else "",
                    "has_conflicts": len(detected_conflicts) > 0 if detected_conflicts else False
                }
                
                # Criar documento
                doc = Document(page_content=doc_content, metadata=metadata)
                
                # ✅ ADICIONAR COM TRATAMENTO DE DUPLICATAS
                try:
                    self.vectorstore.add_documents([doc], ids=[chroma_id])
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
        
        # 5. Atualizar desenvolvimento do agente
        self._update_agent_development()
        
        # 6. Extrair fatos do input
        self.extract_and_save_facts(user_id, user_input, conversation_id)
        
        return conversation_id
    
    def get_user_conversations(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Busca últimas conversas do usuário (SQLite)"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT * FROM conversations
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def count_conversations(self, user_id: str) -> int:
        """Conta conversas do usuário"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM conversations WHERE user_id = ?", (user_id,))
        return cursor.fetchone()['count']
    
    # ========================================
    # BUSCA SEMÂNTICA (ChromaDB)
    # ========================================
    
    def semantic_search(self, user_id: str, query: str, k: int = 5,
                       chat_history: List[Dict] = None) -> List[Dict]:
        """
        Busca semântica VERDADEIRA usando ChromaDB + OpenAI Embeddings
        
        Args:
            user_id: ID do usuário
            query: Texto da consulta
            k: Número de resultados
            chat_history: Histórico da conversa atual (opcional)
        
        Returns:
            Lista de memórias relevantes com scores de similaridade
        """
        
        if not self.chroma_enabled:
            logger.warning("ChromaDB desabilitado. Retornando conversas recentes do SQLite.")
            return self._fallback_keyword_search(user_id, query, k)
        
        try:
            logger.info(f"🔍 Busca semântica: '{query[:50]}...' (k={k})")
            
            # Query enriquecida com histórico recente (se disponível)
            enriched_query = query
            
            if chat_history and len(chat_history) > 0:
                recent_context = " ".join([
                    msg["content"][:100] 
                    for msg in chat_history[-3:] 
                    if msg["role"] == "user"
                ])
                enriched_query = f"{recent_context} {query}"
            
            # Busca vetorial
            results = self.vectorstore.similarity_search_with_score(
                enriched_query,
                k=k * 2,  # Buscar mais para filtrar depois
                filter={"user_id": user_id}
            )
            
            # Processar resultados
            memories = []
            
            for doc, score in results:
                # Extrair input do usuário do documento
                user_input_match = re.search(r"Input:\s*(.+?)(?:\n|Resposta:|$)", doc.page_content, re.DOTALL)
                user_input_text = user_input_match.group(1).strip() if user_input_match else ""
                
                # Extrair resposta
                response_match = re.search(r"Resposta:\s*(.+?)(?:\n|===|$)", doc.page_content, re.DOTALL)
                response_text = response_match.group(1).strip() if response_match else ""
                
                memories.append({
                    'conversation_id': doc.metadata.get('conversation_id'),
                    'user_input': user_input_text,
                    'ai_response': response_text,
                    'timestamp': doc.metadata.get('timestamp', ''),
                    'similarity_score': 1 - score,  # Converter distância em similaridade
                    'tension_level': doc.metadata.get('tension_level', 0.0),
                    'keywords': doc.metadata.get('keywords', '').split(','),
                    'full_document': doc.page_content,
                    'metadata': doc.metadata
                })
            
            # Ordenar por similaridade
            memories.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Retornar top k
            top_memories = memories[:k]
            
            logger.info(f"✅ Encontradas {len(top_memories)} memórias semânticas")
            for i, mem in enumerate(top_memories[:3], 1):
                logger.info(f"   {i}. [{mem['similarity_score']:.2f}] {mem['user_input'][:50]}...")
            
            return top_memories
            
        except Exception as e:
            logger.error(f"❌ Erro na busca semântica: {e}")
            return self._fallback_keyword_search(user_id, query, k)
    
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
    
    def build_rich_context(self, user_id: str, current_input: str,
                          k_memories: int = 5,
                          chat_history: List[Dict] = None) -> str:
        """
        Constrói contexto COMPLETO e SEMÂNTICO sobre o usuário
        
        Combina:
        - Fatos estruturados (SQL)
        - Padrões detectados (SQL)
        - Memórias semânticas relevantes (ChromaDB)
        - Histórico da conversa atual
        """
        
        user = self.get_user(user_id)
        name = user['user_name'] if user else "Usuário"
        
        context_parts = []
        
        # ===== 1. CABEÇALHO =====
        context_parts.append(f"=== CONTEXTO SOBRE {name.upper()} ===\n")
        
        # ===== 2. HISTÓRICO DA CONVERSA ATUAL =====
        if chat_history and len(chat_history) > 0:
            context_parts.append("💬 HISTÓRICO DA CONVERSA ATUAL:")
            
            recent = chat_history[-6:] if len(chat_history) > 6 else chat_history
            
            for msg in recent:
                role = "👤 Usuário" if msg["role"] == "user" else "🤖 Assistente"
                content = msg["content"][:150] + "..." if len(msg["content"]) > 150 else msg["content"]
                context_parts.append(f"{role}: {content}")
            
            context_parts.append("")
        
        # ===== 3. FATOS ESTRUTURADOS =====
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT fact_category, fact_key, fact_value
            FROM user_facts
            WHERE user_id = ? AND is_current = 1
            ORDER BY fact_category, fact_key
        """, (user_id,))
        
        facts = cursor.fetchall()
        
        if facts:
            context_parts.append("📋 FATOS CONHECIDOS:")
            
            facts_by_category = {}
            for fact in facts:
                category = fact['fact_category']
                if category not in facts_by_category:
                    facts_by_category[category] = []
                facts_by_category[category].append(f"{fact['fact_key']}: {fact['fact_value']}")
            
            for category, items in facts_by_category.items():
                context_parts.append(f"\n{category}:")
                context_parts.append("\n".join(f"  - {item}" for item in items))
            
            context_parts.append("")
        
        # ===== 4. PADRÕES DETECTADOS =====
        cursor.execute("""
            SELECT pattern_name, pattern_description, frequency_count, confidence_score
            FROM user_patterns
            WHERE user_id = ? AND confidence_score > 0.6
            ORDER BY confidence_score DESC, frequency_count DESC
            LIMIT 5
        """, (user_id,))
        
        patterns = cursor.fetchall()
        
        if patterns:
            context_parts.append("🔍 PADRÕES COMPORTAMENTAIS:")
            for pattern in patterns:
                context_parts.append(
                    f"  - {pattern['pattern_name']} (confiança: {pattern['confidence_score']:.0%}, "
                    f"freq: {pattern['frequency_count']}): {pattern['pattern_description']}"
                )
            context_parts.append("")
        
        # ===== 5. MEMÓRIAS SEMÂNTICAS =====
        relevant_memories = self.semantic_search(user_id, current_input, k_memories, chat_history)
        
        if relevant_memories:
            context_parts.append("🧠 MEMÓRIAS SEMÂNTICAS RELEVANTES:")
            
            for i, memory in enumerate(relevant_memories, 1):
                timestamp = memory['timestamp'][:10] if memory['timestamp'] else 'N/A'
                score = memory['similarity_score']
                context_parts.append(
                    f"\n{i}. [{timestamp}] Similaridade: {score:.2f}"
                )
                context_parts.append(f"   Usuário: {memory['user_input'][:150]}...")
                
                if memory.get('keywords'):
                    context_parts.append(f"   Temas: {', '.join(memory['keywords'][:5])}")
            
            context_parts.append("")
        
        # ===== 6. ESTATÍSTICAS =====
        stats = self.get_user_stats(user_id)
        
        if stats:
            context_parts.append("📊 ESTATÍSTICAS:")
            context_parts.append(f"  - Total de conversas: {stats['total_messages']}")
            context_parts.append(f"  - Primeira interação: {stats['first_interaction'][:10]}")
            context_parts.append("")
        
        # ===== 7. INSTRUÇÕES =====
        context_parts.append("🎯 COMO USAR ESTE CONTEXTO:")
        context_parts.append("  1. Priorize o HISTÓRICO DA CONVERSA ATUAL para contexto imediato")
        context_parts.append("  2. Use FATOS e PADRÕES para conhecimento de longo prazo")
        context_parts.append("  3. MEMÓRIAS SEMÂNTICAS mostram conversas similares do passado")
        context_parts.append("  4. Conecte o input atual com TODOS esses níveis de memória")
        
        return "\n".join(context_parts)
    
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
                # Criar fato novo
                cursor.execute("""
                    INSERT INTO user_facts
                    (user_id, fact_category, fact_key, fact_value, source_conversation_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, category, key, value, conversation_id))

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
            if not theme or len(theme) < 3:
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
    
    def _update_agent_development(self):
        """Atualiza métricas de desenvolvimento do agente"""
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
                WHERE id = 1
            """)

            self.conn.commit()
            self._check_phase_progression()
    
    def _check_phase_progression(self):
        """Verifica se agente deve progredir de fase"""
        # Note: Pode ser chamado de dentro de _update_agent_development (já locked)
        # ou de forma independente. RLock permite reentrada.
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM agent_development WHERE id = 1")
            state = dict(cursor.fetchone())

            avg_score = (
                state['self_awareness_score'] +
                state['moral_complexity_score'] +
                state['emotional_depth_score'] +
                state['autonomy_score']
            ) / 4

            new_phase = min(5, int(avg_score * 5) + 1)

            if new_phase > state['phase']:
                cursor.execute("UPDATE agent_development SET phase = ? WHERE id = 1", (new_phase,))

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
    
    def get_agent_state(self) -> Dict:
        """Retorna estado atual do agente"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM agent_development WHERE id = 1")
        return dict(cursor.fetchone())
    
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
        
        # Clientes LLM
        self.openai_client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            timeout=30.0  # 30 segundos de timeout
        )
        self.xai_client = OpenAI(
            api_key=Config.XAI_API_KEY,
            base_url="https://api.x.ai/v1",
            timeout=30.0  # 30 segundos de timeout
        )
        
        self.conflict_detector = ConflictDetector()
        
        self.archetype_prompts = {
            "Persona": Config.PERSONA_PROMPT,
            "Sombra": Config.SOMBRA_PROMPT,
            "Velho Sábio": Config.SABIO_PROMPT,
            "Anima": Config.ANIMA_PROMPT
        }
        
        logger.info("✅ JungianEngine inicializado")
    
    def process_message(self, user_id: str, message: str, 
                       model: str = "grok-4-fast-reasoning",
                       chat_history: List[Dict] = None) -> Dict:
        """
        PROCESSAMENTO COMPLETO:
        1. Busca semântica (ChromaDB)
        2. Análise arquetípica (Grok)
        3. Detecção de conflitos
        4. Geração de resposta
        5. Salvamento (SQLite + ChromaDB)
        
        Args:
            user_id: ID do usuário
            message: Mensagem do usuário
            model: Modelo LLM (padrão: grok-4-fast-reasoning)
            chat_history: Histórico da conversa atual (opcional)
        
        Returns:
            Dict com response, conflicts, conversation_count, tension_level
        """
        
        logger.info(f"{'='*60}")
        logger.info(f"🧠 PROCESSANDO MENSAGEM")
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
        
        # Análise arquetípica
        logger.info("🔵 Analisando com arquétipos...")
        archetype_analyses = {}
        
        for archetype_name, archetype_prompt in self.archetype_prompts.items():
            logger.info(f"  • {archetype_name}...")
            analysis = self._analyze_with_archetype(
                archetype_name, archetype_prompt, message, 
                semantic_context, chat_history, model
            )
            archetype_analyses[archetype_name] = analysis
            logger.info(f"    → Impulso: {analysis.impulse} (intensidade: {analysis.intensity:.1f})")
        
        # Detectar conflitos
        logger.info("⚡ Detectando conflitos internos...")
        conflicts = self.conflict_detector.detect_conflicts(archetype_analyses)
        
        # Determinar complexidade
        complexity = self._determine_complexity(message)
        
        # Gerar resposta
        if conflicts:
            logger.info(f"⚡ {len(conflicts)} conflito(s) detectado(s)")
            response = self._generate_conflicted_response(
                message, semantic_context, archetype_analyses, 
                conflicts, complexity, chat_history, model
            )
            tension_level = max([c.tension_level for c in conflicts])
        else:
            logger.info("✅ Sem conflitos - resposta harmônica")
            response = self._generate_harmonious_response(
                message, semantic_context, archetype_analyses, 
                complexity, chat_history, model
            )
            tension_level = 0.0
        
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
            archetype_analyses=archetype_analyses,
            detected_conflicts=conflicts,
            tension_level=tension_level,
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
            'conflicts': conflicts,
            'conversation_count': self.db.count_conversations(user_id),
            'tension_level': tension_level,
            'affective_charge': affective_charge,
            'existential_depth': existential_depth,
            'conversation_id': conversation_id,
            'conflict': None
        }
        
        if conflicts:
            first_conflict = conflicts[0]
            result['conflict'] = {
                'archetype1': first_conflict.archetype_1,
                'archetype2': first_conflict.archetype_2,
                'trigger': first_conflict.description
            }
        
        return result
    
    # ========================================
    # MÉTODOS AUXILIARES
    # ========================================
    
    def _analyze_with_archetype(self, archetype_name: str, archetype_prompt: str,
                               user_input: str, semantic_context: str,
                               chat_history: List[Dict], model: str) -> ArchetypeInsight:
        """Analisa mensagem com um arquétipo específico"""
        
        # Formatar histórico
        history_text = ""
        if chat_history:
            for msg in chat_history[-6:]:
                role = "Usuário" if msg["role"] == "user" else "Assistente"
                history_text += f"{role}: {msg['content'][:100]}...\n"
        
        prompt = Config.ARCHETYPE_ANALYSIS_PROMPT.format(
            archetype_prompt=archetype_prompt,
            semantic_context=semantic_context[:1500],
            user_input=user_input,
            chat_history=history_text
        )
        
        try:
            if model.startswith("grok"):
                completion = self.xai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1500
                )
            else:
                completion = self.openai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1500
                )
            
            response_text = completion.choices[0].message.content
            
            # Extrair JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis_dict = json.loads(json_match.group())
            else:
                analysis_dict = {
                    "voice_reaction": response_text,
                    "impulse": "acolher",
                    "intensity": 0.5
                }

            return ArchetypeInsight(
                archetype_name=archetype_name,
                voice_reaction=analysis_dict.get("voice_reaction", ""),
                impulse=analysis_dict.get("impulse", "acolher"),
                intensity=float(analysis_dict.get("intensity", 0.5))
            )

        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro ao parsear JSON na análise do {archetype_name}: {e}")
            return ArchetypeInsight(
                archetype_name=archetype_name,
                voice_reaction="Erro ao processar resposta da análise",
                impulse="acolher",
                intensity=0.5
            )
        except (TimeoutError, ConnectionError) as e:
            logger.error(f"❌ Erro de conexão/timeout na análise do {archetype_name}: {e}")
            return ArchetypeInsight(
                archetype_name=archetype_name,
                voice_reaction="Erro de conectividade com o serviço de IA",
                impulse="acolher",
                intensity=0.5
            )
        except Exception as e:
            logger.error(f"❌ Erro inesperado na análise do {archetype_name}: {type(e).__name__} - {e}")
            return ArchetypeInsight(
                archetype_name=archetype_name,
                voice_reaction=f"Erro inesperado: {type(e).__name__}",
                impulse="acolher",
                intensity=0.5
            )
    
    def _generate_conflicted_response(self, user_input: str, semantic_context: str,
                                     archetype_analyses: Dict[str, ArchetypeInsight],
                                     conflicts: List[ArchetypeConflict],
                                     complexity: str,
                                     chat_history: List[Dict],
                                     model: str) -> str:
        """Gera resposta que EXPRESSA o conflito interno"""
        
        # Formatar histórico
        history_text = ""
        if chat_history:
            for msg in chat_history[-6:]:
                role = "Usuário" if msg["role"] == "user" else "Assistente"
                history_text += f"{role}: {msg['content'][:100]}...\n"
        
        conflict_description = ""
        for conflict in conflicts:
            arch1 = archetype_analyses[conflict.archetype_1]
            arch2 = archetype_analyses[conflict.archetype_2]

            conflict_description += f"""
VOZ "{conflict.archetype_1}" (intensidade {arch1.intensity:.1f}):
  Reação: {arch1.voice_reaction[:200]}
  Impulso: {arch1.impulse}

VOZ "{conflict.archetype_2}" (intensidade {arch2.intensity:.1f}):
  Reação: {arch2.voice_reaction[:200]}
  Impulso: {arch2.impulse}

Tensão entre elas: {conflict.tension_level:.2f}/10
"""
        
        prompt = Config.CONFLICTED_RESPONSE_PROMPT.format(
            semantic_context=semantic_context[:1000],
            chat_history=history_text,
            user_input=user_input,
            conflict_description=conflict_description,
            complexity=complexity
        )
        
        try:
            if model.startswith("grok"):
                completion = self.xai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8
                )
            else:
                completion = self.openai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8
                )
            
            return completion.choices[0].message.content

        except (TimeoutError, ConnectionError) as e:
            logger.error(f"❌ Erro de conexão/timeout ao gerar resposta conflituosa: {e}")
            return "Desculpe, tive problemas de conectividade. Por favor, tente novamente."
        except ValueError as e:
            logger.error(f"❌ Erro de validação ao gerar resposta conflituosa: {e}")
            return "Desculpe, houve um erro ao validar sua mensagem."
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao gerar resposta conflituosa: {type(e).__name__} - {e}")
            return "Desculpe, tive dificuldades para processar isso."
    
    def _generate_harmonious_response(self, user_input: str, semantic_context: str,
                                     archetype_analyses: Dict[str, ArchetypeInsight],
                                     complexity: str,
                                     chat_history: List[Dict],
                                     model: str) -> str:
        """Gera resposta harmoniosa"""
        
        # Formatar histórico
        history_text = ""
        if chat_history:
            for msg in chat_history[-6:]:
                role = "Usuário" if msg["role"] == "user" else "Assistente"
                history_text += f"{role}: {msg['content'][:100]}...\n"
        
        # Identificar voz dominante (maior intensidade)
        dominant_archetype = max(archetype_analyses.items(), key=lambda x: x[1].intensity)
        dominant_name = dominant_archetype[0]
        dominant_analysis = dominant_archetype[1]

        analyses_summary = ""
        for name, analysis in archetype_analyses.items():
            analyses_summary += f"\n{name}: {analysis.voice_reaction[:100]}... (impulso: {analysis.impulse}, intensidade: {analysis.intensity:.1f})"

        prompt = Config.HARMONIOUS_RESPONSE_PROMPT.format(
            analyses_summary=analyses_summary,
            dominant_voice=f"{dominant_name} - {dominant_analysis.voice_reaction[:200]}",
            semantic_context=semantic_context[:1000],
            chat_history=history_text,
            user_input=user_input,
            complexity=complexity
        )
        
        try:
            if model.startswith("grok"):
                completion = self.xai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
            else:
                completion = self.openai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
            
            return completion.choices[0].message.content

        except (TimeoutError, ConnectionError) as e:
            logger.error(f"❌ Erro de conexão/timeout ao gerar resposta harmoniosa: {e}")
            return "Desculpe, tive problemas de conectividade. Por favor, tente novamente."
        except ValueError as e:
            logger.error(f"❌ Erro de validação ao gerar resposta harmoniosa: {e}")
            return "Desculpe, houve um erro ao validar sua mensagem."
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao gerar resposta harmoniosa: {type(e).__name__} - {e}")
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

def send_to_xai(prompt: str, model: str = "grok-4-fast-reasoning", 
                temperature: float = 0.7, max_tokens: int = 2000) -> str:
    """
    Envia prompt para API X.AI e retorna resposta
    (Função auxiliar para compatibilidade)
    """
    
    xai_api_key = os.getenv("XAI_API_KEY")
    
    if not xai_api_key:
        raise ValueError("XAI_API_KEY não encontrado no ambiente")
    
    try:
        client = OpenAI(
            api_key=xai_api_key,
            base_url="https://api.x.ai/v1",
            timeout=30.0  # 30 segundos de timeout
        )
        
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        raise Exception(f"Erro ao chamar X.AI API: {e}")

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