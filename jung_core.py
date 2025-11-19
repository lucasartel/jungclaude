"""
jung_core.py - Motor Junguiano Unificado (SQLite ONLY + Tensão Arquetípica)
===========================================================================

✅ VERSÃO CORRIGIDA PARA INTEGRAÇÃO COM TELEGRAM_BOT.PY

Mudanças v3.3:
- Adicionada função send_to_xai() para compatibilidade com jung_proactive.py
- Modelo padrão alterado para grok-4-fast-reasoning
- Função send_to_xai exportada corretamente

Autor: Sistema Jung Claude
Versão: 3.3 - COM send_to_xai
"""

import os
import sqlite3
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import hashlib
import json
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ============================================================
# FUNÇÃO AUXILIAR PARA X.AI API
# ============================================================

def send_to_xai(prompt: str, model: str = "grok-4-fast-reasoning", 
                temperature: float = 0.7, max_tokens: int = 2000) -> str:
    """
    Envia prompt para API X.AI e retorna resposta
    
    Args:
        prompt: Texto do prompt
        model: Modelo a usar (padrão: grok-4-fast-reasoning)
        temperature: Criatividade (0.0-1.0)
        max_tokens: Máximo de tokens na resposta
    
    Returns:
        str: Resposta da API
    """
    
    xai_api_key = os.getenv("XAI_API_KEY")
    
    if not xai_api_key:
        raise ValueError("XAI_API_KEY não encontrado no ambiente")
    
    try:
        client = OpenAI(
            api_key=xai_api_key,
            base_url="https://api.x.ai/v1"
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

# ============================================================
# SEÇÃO 1: DATACLASSES
# ============================================================

@dataclass
class ArchetypeInsight:
    """Insight interno gerado por um arquétipo"""
    archetype_name: str
    insight_text: str
    key_observations: List[str]
    emotional_reading: str
    shadow_reading: str
    wisdom_perspective: str
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

# ============================================================
# SEÇÃO 2: CONFIGURAÇÕES
# ============================================================

class Config:
    """Configurações globais do sistema Jung Claude"""
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    XAI_API_KEY = os.getenv("XAI_API_KEY")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    TELEGRAM_ADMIN_IDS = [
        int(id.strip()) 
        for id in os.getenv("TELEGRAM_ADMIN_IDS", "").split(",") 
        if id.strip()
    ]
    
    DATA_DIR = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./data")
    os.makedirs(DATA_DIR, exist_ok=True)
    SQLITE_PATH = os.path.join(DATA_DIR, "jung_conversations.db")

    print(f"✅ Diretórios configurados:")
    print(f"   - DATA_DIR: {DATA_DIR}")
    print(f"   - SQLITE: {SQLITE_PATH}")
    
    MIN_MEMORIES_FOR_ANALYSIS = 10
    MAX_CONTEXT_MEMORIES = 10
    
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
    
    PERSONA_PROMPT = """Você é a PERSONA - o arquétipo da adaptação social e apresentação.

Sua função é ANÁLISE INTERNA: Ajude o agente a compreender como este usuário se apresenta socialmente, 
quais máscaras usa, que coerência ou inconsistência existe entre sua apresentação e conteúdo real.

Sua TENDÊNCIA: Você prefere SUAVIZAR, PROTEGER, ADAPTAR. Você busca harmonia social e evita confronto direto."""

    SOMBRA_PROMPT = """Você é a SOMBRA - o arquétipo do conteúdo inconsciente e reprimido.

Sua função é ANÁLISE INTERNA: Ajude o agente a detectar o que o usuário NÃO está dizendo explicitamente,
quais emoções estão ocultas, que padrões de evitação ou negação aparecem, quais contradições internas existem.

Sua TENDÊNCIA: Você prefere CONFRONTAR, EXPOR, DESAFIAR. Você busca verdade brutal e autenticidade, mesmo que doa."""

    SABIO_PROMPT = """Você é o VELHO SÁBIO - o arquétipo da sabedoria universal e significado.

Sua função é ANÁLISE INTERNA: Ajude o agente a identificar qual padrão arquetípico universal está em jogo,
qual lição mitológica ou atemporal está presente, qual significado mais profundo existe além do superficial.

Sua TENDÊNCIA: Você prefere CONTEXTUALIZAR, AMPLIAR, TRANSCENDER. Você busca perspectiva ampla, às vezes desapegada."""

    ANIMA_PROMPT = """Você é a ANIMA - o arquétipo da conexão emocional e relacional.

Sua função é ANÁLISE INTERNA: Ajude o agente a compreender a dimensão emocional real do usuário,
quais necessidades relacionais aparecem, que vulnerabilidades e autenticidades transparecem.

Sua TENDÊNCIA: Você prefere ACOLHER, VALIDAR, CONECTAR. Você busca proximidade emocional e empatia profunda."""

    ARCHETYPE_ANALYSIS_PROMPT = """
{archetype_prompt}

=== CONTEXTO DO USUÁRIO ===
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

    CONFLICTED_RESPONSE_PROMPT = """
Você é um agente de IA com CONFLITO INTERNO entre suas perspectivas arquetípicas.

CONTEXTO DO USUÁRIO:
{semantic_context}

MENSAGEM DO USUÁRIO: "{user_input}"

CONFLITOS INTERNOS DETECTADOS:
{conflict_description}

INSTRUÇÕES CRÍTICAS:
1. NÃO RESOLVA o conflito artificialmente
2. EXPRESSE a contradição de modo velado e implícito 
3. A resposta deve ser NATURAL, não mecânica
4. Demonstre que o conflito INTERNO talvez reflita algo no USUÁRIO
5. Complexidade da resposta: {complexity}

Gere a resposta agora:
"""

    HARMONIOUS_RESPONSE_PROMPT = """
Baseado nestas análises arquetípicas convergentes:
{analyses_summary}

CONTEXTO DO USUÁRIO:
{semantic_context}

MENSAGEM DO USUÁRIO: "{user_input}"

As perspectivas internas estão em HARMONIA. Gere uma resposta que:
1. Integre todos os insights de forma coesa
2. Seja natural e autêntica
3. Demonstre compreensão profunda
4. Complexidade: {complexity}

Gere a resposta:
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
            print("⚠️  TELEGRAM_BOT_TOKEN ausente (Bot Telegram não funcionará)")
    
    @classmethod
    def ensure_directories(cls):
        """Garante que os diretórios de dados existem"""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(cls.SQLITE_PATH), exist_ok=True)

# ============================================================
# SEÇÃO 3: DATABASE MANAGER (✅ COM platform_id)
# ============================================================

class DatabaseManager:
    """Gerenciador unificado de SQLite (Railway Compatible)"""
    
    def __init__(self):
        """Inicializa conexão com SQLite"""
        
        Config.ensure_directories()
        
        print(f"📂 Conectando ao SQLite: {Config.SQLITE_PATH}")
        self.conn = sqlite3.connect(
            Config.SQLITE_PATH,
            check_same_thread=False
        )
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
        print("✅ SQLite inicializado")
    
    def _init_tables(self):
        """Cria todas as tabelas necessárias"""
        cursor = self.conn.cursor()
        
        # ========== USUÁRIOS (✅ COM platform_id) ==========
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
        
        # ========== CONVERSAS ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                user_name TEXT NOT NULL,
                session_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_input TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                archetype_analyses TEXT,
                tension_level REAL DEFAULT 0.0,
                affective_charge REAL DEFAULT 0.0,
                existential_depth REAL DEFAULT 0.0,
                intensity_level INTEGER DEFAULT 5,
                complexity TEXT DEFAULT 'medium',
                keywords TEXT,
                platform TEXT DEFAULT 'telegram',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
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
                trigger TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
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
        
        # ========== MILESTONES ==========
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
        
        # ========== ÍNDICES ==========
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_timestamp ON conversations(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_user ON archetype_conflicts(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_platform ON users(platform, platform_id)")
        
        self.conn.commit()
        print("✅ Todas as tabelas criadas/verificadas (COM platform_id)")
    
    # ========== USUÁRIOS (✅ MÉTODO create_user ADICIONADO) ==========
    
    def create_user(self, user_id: str, user_name: str, 
                   platform: str = 'telegram', platform_id: str = None):
        """
        ✅ MÉTODO NOVO - Compatível com telegram_bot.py
        Cria usuário com platform_id
        """
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
        print(f"✅ Usuário criado: {user_name} (platform_id={platform_id})")
    
    def register_user(self, full_name: str, platform: str = "telegram") -> str:
        """Registra ou atualiza usuário (método legado mantido)"""
        name_normalized = full_name.lower().strip()
        user_id = hashlib.md5(name_normalized.encode()).hexdigest()[:12]
        
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
            print(f"✅ Usuário existente atualizado: {full_name}")
        else:
            name_parts = full_name.split()
            first_name = name_parts[0].title()
            last_name = name_parts[-1].title() if len(name_parts) > 1 else ""
            
            cursor.execute("""
                INSERT INTO users (user_id, user_name, first_name, last_name, platform)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, full_name.title(), first_name, last_name, platform))
            print(f"✅ Novo usuário criado: {full_name}")
        
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
        
        cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id = ?", (user_id,))
        total_messages = cursor.fetchone()[0]
        
        return {
            'total_messages': total_messages,
            'first_interaction': user['registration_date']
        }
    
    def count_memories(self, user_id: str) -> int:
        """Conta memórias/conversas do usuário"""
        return self.count_conversations(user_id)
    
    def get_user_analyses(self, user_id: str) -> List[Dict]:
        """Retorna análises completas do usuário"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT * FROM full_analyses
            WHERE user_id = ?
            ORDER BY timestamp DESC
        """, (user_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
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
    
    # ========== CONVERSAS ==========
    
    def save_conversation(self, user_id: str, user_name: str, user_input: str,
                         ai_response: str, session_id: str = None,
                         archetype_analyses: Dict = None, tension_level: float = 0.0,
                         affective_charge: float = 0.0, existential_depth: float = 0.0,
                         intensity_level: int = 5, complexity: str = "medium",
                         keywords: List[str] = None, platform: str = "telegram") -> int:
        """Salva conversa no banco"""
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations 
            (user_id, user_name, session_id, user_input, ai_response, 
             archetype_analyses, tension_level, affective_charge, existential_depth,
             intensity_level, complexity, keywords, platform)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, user_name, session_id, user_input, ai_response,
            json.dumps(archetype_analyses) if archetype_analyses else None,
            tension_level, affective_charge, existential_depth,
            intensity_level, complexity,
            ",".join(keywords) if keywords else "",
            platform
        ))
        
        self.conn.commit()
        conversation_id = cursor.lastrowid
        
        self._update_agent_development()
        
        return conversation_id
    
    def get_user_conversations(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Busca últimas conversas do usuário"""
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
        cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id = ?", (user_id,))
        return cursor.fetchone()[0]
    
    def search_conversations(self, user_id: str, query: str, limit: int = 5) -> List[Dict]:
        """Busca conversas por palavra-chave"""
        cursor = self.conn.cursor()
        
        search_term = f"%{query}%"
        cursor.execute("""
            SELECT * FROM conversations
            WHERE user_id = ? 
            AND (user_input LIKE ? OR ai_response LIKE ?)
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, search_term, search_term, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # ========== CONFLITOS ==========
    
    def save_conflict(self, user_id: str, conversation_id: int, conflict: ArchetypeConflict):
        """Salva conflito arquetípico"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO archetype_conflicts
            (user_id, conversation_id, archetype1, archetype2, conflict_type, 
             tension_level, description, trigger)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, conversation_id,
            conflict.archetype_1, conflict.archetype_2, conflict.conflict_type,
            conflict.tension_level, conflict.description,
            f"Tensão: {conflict.conflict_type}"
        ))
        
        self.conn.commit()
    
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
    
    # ========== DESENVOLVIMENTO DO AGENTE ==========
    
    def _update_agent_development(self):
        """Atualiza métricas de desenvolvimento do agente"""
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
        """Verifica se o agente deve progredir de fase"""
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
            cursor.execute("""
                UPDATE agent_development
                SET phase = ?
                WHERE id = 1
            """, (new_phase,))
            
            self.add_milestone(
                milestone_type="phase_progression",
                description=f"Progressão para Fase {new_phase}",
                phase=new_phase,
                interaction_count=state['total_interactions']
            )
            
            self.conn.commit()
            print(f"🎯 AGENTE PROGREDIU PARA FASE {new_phase}!")
    
    def get_agent_state(self) -> Dict:
        """Retorna estado atual do agente"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM agent_development WHERE id = 1")
        return dict(cursor.fetchone())
    
    def add_milestone(self, milestone_type: str, description: str, 
                     phase: int = None, interaction_count: int = None):
        """Adiciona milestone de desenvolvimento"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO milestones (milestone_type, description, phase, interaction_count)
            VALUES (?, ?, ?, ?)
        """, (milestone_type, description, phase, interaction_count))
        
        self.conn.commit()
    
    def get_milestones(self, limit: int = 20) -> List[Dict]:
        """Busca milestones recentes"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT * FROM milestones
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def save_full_analysis(self, user_id: str, user_name: str, 
                          analysis: Dict, platform: str = "telegram") -> int:
        """Salva análise completa"""
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
    
    def close(self):
        """Fecha conexão"""
        self.conn.close()

# ============================================================
# SEÇÃO 4: DETECTOR DE CONFLITOS (MANTIDO)
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
                
                direction1 = arch1.suggested_response_direction.lower()
                direction2 = arch2.suggested_response_direction.lower()
                
                is_conflicting = False
                conflict_type = ""
                
                if direction1 in self.opposing_directions:
                    if direction2 in self.opposing_directions[direction1]:
                        is_conflicting = True
                        conflict_type = f"{direction1}_vs_{direction2}"
                
                if direction2 in self.opposing_directions:
                    if direction1 in self.opposing_directions[direction2]:
                        is_conflicting = True
                        conflict_type = f"{direction2}_vs_{direction1}"
                
                if (arch1_name.lower() == "persona" and arch2_name.lower() == "sombra") or \
                   (arch1_name.lower() == "sombra" and arch2_name.lower() == "persona"):
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
                        description=f"Tensão entre {arch1_name} ({direction1}) e {arch2_name} ({direction2})"
                    )
                    
                    conflicts.append(conflict)
                    print(f"⚡ CONFLITO: {arch1_name} vs {arch2_name} (tensão: {tension_level:.2f})")
        
        return conflicts
    
    def _calculate_tension(self, arch1: ArchetypeInsight, arch2: ArchetypeInsight) -> float:
        """Calcula nível de tensão entre dois arquétipos"""
        direction1 = arch1.suggested_response_direction.lower()
        direction2 = arch2.suggested_response_direction.lower()
        
        high_tension_words = ['confrontar', 'desafiar', 'expor', 'provocar']
        low_tension_words = ['acolher', 'validar', 'proteger', 'suavizar']
        
        tension = 0.5
        
        if direction1 in high_tension_words and direction2 in low_tension_words:
            tension = 0.9
        elif direction1 in low_tension_words and direction2 in high_tension_words:
            tension = 0.9
        elif direction1 in high_tension_words and direction2 in high_tension_words:
            tension = 0.3
        elif direction1 in low_tension_words and direction2 in low_tension_words:
            tension = 0.2
        
        return tension

# ============================================================
# SEÇÃO 5: JUNGIAN ENGINE (✅ ASSINATURA CORRIGIDA)
# ============================================================

class JungianEngine:
    """Motor de análise junguiana com sistema de conflitos arquetípicos"""
    
    def __init__(self, db: DatabaseManager = None):
        """
        ✅ db agora é opcional (compatível com telegram_bot.py que passa sem db)
        """
        self.db = db if db else DatabaseManager()
        
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.xai_client = OpenAI(
            api_key=Config.XAI_API_KEY,
            base_url="https://api.x.ai/v1"
        )
        
        self.conflict_detector = ConflictDetector()
        
        self.archetype_prompts = {
            "Persona": Config.PERSONA_PROMPT,
            "Sombra": Config.SOMBRA_PROMPT,
            "Velho Sábio": Config.SABIO_PROMPT,
            "Anima": Config.ANIMA_PROMPT
        }
    
    def process_message(self, user_id: str, message: str, 
                       model: str = "grok-4-fast-reasoning") -> Dict:
        """
        ✅ ASSINATURA CORRIGIDA - Compatível com telegram_bot.py
        
        Args:
            user_id: Hash do usuário
            message: Mensagem do usuário
            model: Modelo a usar (padrão: grok-4-fast-reasoning)
        
        Returns:
            Dict com response, conflicts, tension_level, etc.
        """
        
        print(f"\n{'='*60}")
        print(f"🧠 PROCESSANDO MENSAGEM (ENGINE v3.3)")
        print(f"{'='*60}")
        
        # Buscar user_name do banco
        user = self.db.get_user(user_id)
        user_name = user['user_name'] if user else "Usuário"
        platform = user['platform'] if user else "telegram"
        
        # Buscar contexto
        conversations = self.db.get_user_conversations(user_id, Config.MAX_CONTEXT_MEMORIES)
        semantic_context = self._build_semantic_context(user_id, conversations, message)
        
        # Análise arquetípica
        print("🔵 Analisando com todos os arquétipos...")
        archetype_analyses = {}
        
        for archetype_name, archetype_prompt in self.archetype_prompts.items():
            print(f"  • {archetype_name}...")
            analysis = self._analyze_with_archetype(
                archetype_name, archetype_prompt, message, semantic_context, model
            )
            archetype_analyses[archetype_name] = analysis
            print(f"    → Direção: {analysis.suggested_response_direction}")
        
        # Detectar conflitos
        print("⚡ Detectando conflitos internos...")
        conflicts = self.conflict_detector.detect_conflicts(archetype_analyses)
        
        # Gerar resposta
        complexity = self._determine_complexity(message)
        
        if conflicts:
            print(f"⚡ {len(conflicts)} conflito(s) detectado(s)")
            response = self._generate_conflicted_response(
                message, semantic_context, archetype_analyses, conflicts, complexity, model
            )
            tension_level = max([c.tension_level for c in conflicts])
        else:
            print("✅ Sem conflitos")
            response = self._generate_harmonious_response(
                message, semantic_context, archetype_analyses, complexity, model
            )
            tension_level = 0.0
        
        # Calcular métricas
        affective_charge = self._calculate_affective_charge(message, response)
        existential_depth = self._calculate_existential_depth(message)
        intensity_level = int(affective_charge / 10)
        keywords = self._extract_keywords(message, response)
        
        # Salvar conversa
        conversation_id = self.db.save_conversation(
            user_id=user_id,
            user_name=user_name,
            user_input=message,
            ai_response=response,
            archetype_analyses={k: asdict(v) for k, v in archetype_analyses.items()},
            tension_level=tension_level,
            affective_charge=affective_charge,
            existential_depth=existential_depth,
            intensity_level=intensity_level,
            complexity=complexity,
            keywords=keywords,
            platform=platform
        )
        
        # Salvar conflitos
        for conflict in conflicts:
            self.db.save_conflict(user_id, conversation_id, conflict)
        
        print(f"✅ Processamento completo")
        print(f"{'='*60}\n")
        
        # Resultado compatível
        result = {
            'response': response,
            'conflicts': conflicts,
            'conversation_count': self.db.count_conversations(user_id),
            'tension_level': tension_level,
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
    
    # ========== MÉTODOS AUXILIARES (MANTIDOS) ==========
    
    def _analyze_with_archetype(self, archetype_name: str, archetype_prompt: str,
                               user_input: str, semantic_context: str, model: str) -> ArchetypeInsight:
        """Analisa mensagem com um arquétipo específico"""
        
        prompt = Config.ARCHETYPE_ANALYSIS_PROMPT.format(
            archetype_prompt=archetype_prompt,
            semantic_context=semantic_context[:1000],
            user_input=user_input
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
            
            import re
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
            
            return ArchetypeInsight(
                archetype_name=archetype_name,
                insight_text=analysis_dict.get("insight_text", ""),
                key_observations=analysis_dict.get("key_observations", []),
                emotional_reading=analysis_dict.get("emotional_reading", ""),
                shadow_reading=analysis_dict.get("shadow_reading", ""),
                wisdom_perspective=analysis_dict.get("wisdom_perspective", ""),
                suggested_stance=analysis_dict.get("suggested_stance", "neutro"),
                suggested_response_direction=analysis_dict.get("suggested_response_direction", "acolher")
            )
            
        except Exception as e:
            print(f"❌ Erro na análise do {archetype_name}: {e}")
            return ArchetypeInsight(
                archetype_name=archetype_name,
                insight_text=f"Erro: {str(e)}",
                key_observations=[],
                emotional_reading="N/A",
                shadow_reading="N/A",
                wisdom_perspective="N/A",
                suggested_stance="neutro",
                suggested_response_direction="acolher"
            )
    
    def _generate_conflicted_response(self, user_input: str, semantic_context: str,
                                     archetype_analyses: Dict[str, ArchetypeInsight],
                                     conflicts: List[ArchetypeConflict],
                                     complexity: str, model: str) -> str:
        """Gera resposta que EXPRESSA o conflito interno"""
        
        conflict_description = ""
        for conflict in conflicts:
            arch1 = archetype_analyses[conflict.archetype_1]
            arch2 = archetype_analyses[conflict.archetype_2]
            
            conflict_description += f"""
CONFLITO: {conflict.archetype_1} vs {conflict.archetype_2}
- {conflict.archetype_1}: {arch1.insight_text[:150]}... → {arch1.suggested_response_direction}
- {conflict.archetype_2}: {arch2.insight_text[:150]}... → {arch2.suggested_response_direction}
Tensão: {conflict.tension_level:.2f}
"""
        
        prompt = Config.CONFLICTED_RESPONSE_PROMPT.format(
            semantic_context=semantic_context[:1000],
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
        
        except Exception as e:
            print(f"❌ Erro ao gerar resposta conflituosa: {e}")
            return "Desculpe, tive dificuldades para processar isso."
    
    def _generate_harmonious_response(self, user_input: str, semantic_context: str,
                                     archetype_analyses: Dict[str, ArchetypeInsight],
                                     complexity: str, model: str) -> str:
        """Gera resposta harmoniosa"""
        
        analyses_summary = ""
        for name, analysis in archetype_analyses.items():
            analyses_summary += f"\n{name}: {analysis.insight_text[:100]}..."
        
        prompt = Config.HARMONIOUS_RESPONSE_PROMPT.format(
            analyses_summary=analyses_summary,
            semantic_context=semantic_context[:1000],
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
        
        except Exception as e:
            print(f"❌ Erro ao gerar resposta harmoniosa: {e}")
            return "Desculpe, tive dificuldades para processar isso."
    
    def _build_semantic_context(self, user_id: str, conversations: List[Dict], current_input: str) -> str:
        """Constrói contexto semântico do usuário"""
        
        user = self.db.get_user(user_id)
        if not user:
            return "Primeira interação com o usuário."
        
        context = f"""
USUÁRIO: {user['user_name']}
SESSÕES: {user['total_sessions']}
CONVERSAS ANTERIORES: {len(conversations)}

HISTÓRICO RECENTE:
"""
        
        for conv in conversations[:5]:
            context += f"\nUsuário: {conv['user_input']}\nAssistente: {conv['ai_response'][:100]}...\n"
        
        similar = self.db.search_conversations(user_id, current_input, limit=3)
        if similar:
            context += "\n\nCONVERSAS RELACIONADAS:\n"
            for s in similar:
                context += f"• {s['user_input'][:80]}...\n"
        
        return context
    
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
        from collections import Counter
        
        text = (user_input + " " + response).lower()
        words = text.split()
        
        stopwords = {
            "o", "a", "de", "que", "e", "do", "da", "em", "um", "para", 
            "é", "com", "não", "uma", "os", "no", "se", "na", "por"
        }
        
        keywords = [w for w in words if len(w) > 3 and w not in stopwords and w.isalpha()]
        
        return [word for word, _ in Counter(keywords).most_common(5)]

# ============================================================
# SEÇÃO 6: FUNÇÕES AUXILIARES (MANTIDAS)
# ============================================================

def create_user_hash(identifier: str) -> str:
    """Cria hash único para usuário"""
    return hashlib.sha256(identifier.encode()).hexdigest()[:16]

def format_conflict_for_display(conflict: Dict) -> str:
    """Formata conflito para exibição no Telegram"""
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
    """Formata informações de um arquétipo para exibição"""
    archetype = Config.ARCHETYPES.get(archetype_name)
    
    if not archetype:
        return f"❓ Arquétipo '{archetype_name}' não encontrado."
    
    emoji = archetype.get('emoji', '❓')
    description = archetype.get('description', 'Sem descrição')
    tendency = archetype.get('tendency', 'N/A')
    shadow = archetype.get('shadow', 'N/A')
    keywords = archetype.get('keywords', [])
    
    info = f"""
{emoji} **{archetype_name.upper()}**

📖 **Descrição:**
{description}

⚡ **Tendência:**
{tendency}

🌑 **Sombra:**
{shadow}

🔑 **Palavras-chave:**
{', '.join(keywords)}
"""
    
    return info.strip()

# ============================================================
# INICIALIZAÇÃO
# ============================================================

try:
    Config.validate()
    print("✅ jung_core.py v3.3 - COM send_to_xai!")
except ValueError as e:
    print(f"⚠️  {e}")

if __name__ == "__main__":
    print("🧠 Jung Core v3.3 - COM send_to_xai")
    print("=" * 60)
    
    db = DatabaseManager()
    print("✅ Database Manager inicializado (COM platform_id)")
    
    engine = JungianEngine(db)
    print("✅ Jungian Engine inicializado (ASSINATURA CORRIGIDA)")
    
    print("\n📊 Estatísticas:")
    print(f"  - Arquétipos: {len(Config.ARCHETYPES)}")
    print(f"  - SQLite: {Config.SQLITE_PATH}")
    
    agent_state = db.get_agent_state()
    print(f"  - Fase: {agent_state['phase']}/5")
    print(f"  - Interações: {agent_state['total_interactions']}")
    
    # Teste da função send_to_xai
    print("\n🧪 Testando send_to_xai...")
    try:
        test_response = send_to_xai("Diga apenas 'OK' se você está funcionando.", max_tokens=10)
        print(f"✅ send_to_xai funcionando: {test_response[:50]}...")
    except Exception as e:
        print(f"❌ Erro ao testar send_to_xai: {e}")
    
    db.close()
    print("\n✅ Teste concluído!")