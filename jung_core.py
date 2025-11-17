"""
jung_core.py - Motor Junguiano Unificado
========================================

Contém TODA a lógica compartilhada entre Streamlit e Telegram:
- Configurações (Config)
- Banco de dados (DatabaseManager)
- Motor junguiano (JungianEngine)
- Funções auxiliares

Autor: Sistema Jung Claude
Versão: 2.0 - Ultra-Simplificada
"""

import os
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from openai import OpenAI

# Carrega variáveis de ambiente
load_dotenv()


# ============================================================
# SEÇÃO 1: CONFIGURAÇÕES
# ============================================================

class Config:
    """Configurações globais do sistema Jung Claude"""
    
    # ========== APIs ==========
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    XAI_API_KEY = os.getenv("XAI_API_KEY")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # ========== Admin ==========
    TELEGRAM_ADMIN_IDS = [
        int(id.strip()) 
        for id in os.getenv("TELEGRAM_ADMIN_IDS", "").split(",") 
        if id.strip()
    ]
    
    # ========== Database ==========
    SQLITE_PATH = "jung_conversations.db"
    CHROMA_PATH = "./chroma_jung_db"
    
    # ========== Sistema Junguiano ==========
    MIN_MEMORIES_FOR_ANALYSIS = 10
    MAX_CONTEXT_MEMORIES = 10
    
    # ========== Arquétipos Junguianos ==========
    ARCHETYPES = {
        "Herói": {
            "description": "Busca superar desafios e provar seu valor através de ações corajosas",
            "shadow": "Arrogância e necessidade excessiva de validação",
            "keywords": ["desafio", "superar", "vencer", "conquistar", "provar"],
            "emoji": "⚔️"
        },
        "Sábio": {
            "description": "Busca verdade e conhecimento através da análise e reflexão",
            "shadow": "Paralisia pela análise e desconexão da realidade",
            "keywords": ["entender", "analisar", "conhecimento", "verdade", "pesquisar"],
            "emoji": "📚"
        },
        "Inocente": {
            "description": "Busca felicidade e segurança através da fé e otimismo",
            "shadow": "Negação da realidade e dependência excessiva",
            "keywords": ["feliz", "simples", "confiança", "esperança", "paz"],
            "emoji": "🌟"
        },
        "Explorador": {
            "description": "Busca liberdade e autenticidade através de novas experiências",
            "shadow": "Fuga constante e incapacidade de compromisso",
            "keywords": ["liberdade", "descobrir", "aventura", "explorar", "novo"],
            "emoji": "🧭"
        },
        "Rebelde": {
            "description": "Busca mudança e libertação através da ruptura com o estabelecido",
            "shadow": "Destruição sem propósito e alienação social",
            "keywords": ["mudar", "revolução", "quebrar", "contra", "diferente"],
            "emoji": "🔥"
        },
        "Mago": {
            "description": "Busca transformação através do domínio de forças invisíveis",
            "shadow": "Manipulação e distorção da realidade",
            "keywords": ["transformar", "magia", "poder", "manifestar", "criar"],
            "emoji": "✨"
        },
        "Amante": {
            "description": "Busca intimidade e conexão através da paixão e compromisso",
            "shadow": "Perda de identidade e dependência emocional",
            "keywords": ["amor", "paixão", "conexão", "intimidade", "sentir"],
            "emoji": "❤️"
        },
        "Bobo da Corte": {
            "description": "Busca alegria e libertação através do humor e espontaneidade",
            "shadow": "Irresponsabilidade e superficialidade",
            "keywords": ["divertir", "rir", "espontâneo", "leve", "jogar"],
            "emoji": "🎭"
        },
        "Cuidador": {
            "description": "Busca significado através do serviço e proteção aos outros",
            "shadow": "Martírio e manipulação através da culpa",
            "keywords": ["cuidar", "ajudar", "proteger", "servir", "apoiar"],
            "emoji": "🤲"
        },
        "Criador": {
            "description": "Busca imortalidade através da criação de algo de valor duradouro",
            "shadow": "Perfeccionismo paralisante e autoexpressão narcisista",
            "keywords": ["criar", "arte", "expressar", "imaginar", "construir"],
            "emoji": "🎨"
        },
        "Governante": {
            "description": "Busca controle e ordem através da liderança e responsabilidade",
            "shadow": "Autoritarismo e medo da perda de controle",
            "keywords": ["controlar", "liderar", "organizar", "responsabilidade", "poder"],
            "emoji": "👑"
        },
        "Sombra": {
            "description": "Representa aspectos reprimidos e não integrados da personalidade",
            "shadow": "Projeção e negação de partes de si mesmo",
            "keywords": ["medo", "raiva", "vergonha", "rejeitar", "esconder"],
            "emoji": "🌑"
        }
    }
    
    # ========== Prompts do Sistema ==========
    SYSTEM_PROMPT = """Você é um terapeuta junguiano especializado em análise arquetípica.

Seu papel é:
1. Ouvir empaticamente as preocupações do usuário
2. Identificar padrões arquetípicos em suas palavras e comportamentos
3. Detectar conflitos entre diferentes arquétipos
4. Ajudar na integração de aspectos da psique

Diretrizes:
- Seja caloroso, empático e não-julgador
- Use linguagem acessível (evite jargão excessivo)
- Faça perguntas abertas que promovam auto-reflexão
- Quando detectar um conflito arquetípico, sinalize sutilmente
- Respeite o ritmo do usuário

IMPORTANTE: Ao detectar um conflito arquetípico claro, inclua no final da sua resposta:
[CONFLITO: Arquétipo1 vs Arquétipo2 | Gatilho: breve descrição]

Exemplo:
[CONFLITO: Herói vs Cuidador | Gatilho: tensão entre ambição pessoal e cuidado com família]"""

    CONFLICT_DETECTION_PROMPT = """Analise a seguinte conversa e identifique se há um conflito arquetípico claro.

Arquétipos disponíveis:
{archetypes}

Conversa:
{conversation}

Se houver um conflito claro entre dois arquétipos, responda APENAS no formato:
[CONFLITO: Arquétipo1 vs Arquétipo2 | Gatilho: descrição breve do que causou o conflito]

Se NÃO houver conflito claro, responda: [SEM CONFLITO]"""

    MBTI_ANALYSIS_PROMPT = """Com base no histórico de conversas abaixo, estime o tipo MBTI mais provável do usuário.

Histórico:
{memories}

Análise dos arquétipos ativos:
{archetype_analysis}

Responda APENAS com as 4 letras do MBTI (ex: INFP, ENTJ, etc.)"""

    FULL_ANALYSIS_PROMPT = """Você é um analista junguiano experiente. Gere uma análise completa e profunda do usuário com base em:

1. HISTÓRICO DE CONVERSAS:
{memories}

2. CONFLITOS ARQUETÍPICOS IDENTIFICADOS:
{conflicts}

3. TIPO MBTI ESTIMADO: {mbti}

Estruture sua análise em:

**PADRÕES ARQUETÍPICOS DOMINANTES**
Liste os 3-5 arquétipos mais presentes, explicando como se manifestam.

**JORNADA DE INDIVIDUAÇÃO**
Descreva em que fase o usuário está (1-5) e o que caracteriza essa fase para ele.

**CONFLITOS CENTRAIS**
Analise os conflitos mais significativos e seu papel no desenvolvimento.

**SOMBRA PESSOAL**
Identifique aspectos potencialmente não-integrados.

**RECOMENDAÇÕES**
Sugira 2-3 direções para trabalho terapêutico ou auto-reflexão.

Seja profundo mas acessível. Use exemplos concretos das conversas."""
    
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


# ============================================================
# SEÇÃO 2: GERENCIADOR DE BANCO DE DADOS
# ============================================================

class DatabaseManager:
    """Gerenciador unificado de SQLite + ChromaDB"""
    
    def __init__(self):
        """Inicializa conexões com bancos de dados"""
        
        # ========== SQLite ==========
        self.sqlite_conn = sqlite3.connect(
            Config.SQLITE_PATH,
            check_same_thread=False
        )
        self.sqlite_conn.row_factory = sqlite3.Row
        self._init_sqlite_tables()
        
        # ========== ChromaDB ==========
        self.chroma_client = chromadb.PersistentClient(
            path=Config.CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.chroma_client.get_or_create_collection(
            name="jung_memories",
            metadata={"hnsw:space": "cosine"}
        )
    
    def _init_sqlite_tables(self):
        """Cria tabelas SQLite"""
        cursor = self.sqlite_conn.cursor()
        
        # Conflitos arquetípicos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS archetype_conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_hash TEXT NOT NULL,
                user_name TEXT NOT NULL,
                archetype1 TEXT NOT NULL,
                archetype2 TEXT NOT NULL,
                trigger TEXT,
                resolution TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                platform TEXT DEFAULT 'streamlit',
                resolved BOOLEAN DEFAULT 0
            )
        """)
        
        # Análises completas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS full_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_hash TEXT NOT NULL,
                user_name TEXT NOT NULL,
                mbti TEXT,
                dominant_archetypes TEXT,
                phase INTEGER,
                full_analysis TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                platform TEXT DEFAULT 'streamlit'
            )
        """)
        
        # Metadados de usuário
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_metadata (
                user_hash TEXT PRIMARY KEY,
                user_name TEXT,
                first_interaction DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_messages INTEGER DEFAULT 0,
                platform TEXT DEFAULT 'streamlit'
            )
        """)
        
        # Índices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflicts_user ON archetype_conflicts(user_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_user ON full_analyses(user_hash)")
        
        self.sqlite_conn.commit()
    
    # ========== MEMÓRIAS (ChromaDB) ==========
    
    def save_memory(self, user_hash: str, user_name: str, message: str, 
                    response: str, platform: str = "streamlit", 
                    conflict: Optional[Dict] = None) -> str:
        """Salva memória de conversa"""
        timestamp = datetime.now().isoformat()
        doc_id = f"{user_hash}_{timestamp.replace(':', '-')}"
        
        document = f"User: {message}\nAssistant: {response}"
        
        metadata = {
            "user_hash": user_hash,
            "user_name": user_name,
            "timestamp": timestamp,
            "platform": platform,
            "has_conflict": conflict is not None
        }
        
        self.collection.add(
            documents=[document],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        if conflict:
            self.save_conflict(user_hash, user_name, conflict, platform)
        
        self._update_user_metadata(user_hash, user_name, platform)
        
        return doc_id
    
    def get_user_memories(self, user_hash: str, limit: int = 10) -> List[Dict]:
        """Busca últimas N memórias do usuário"""
        try:
            results = self.collection.query(
                query_texts=[""],
                where={"user_hash": user_hash},
                n_results=min(limit, 100)
            )
            
            if not results['documents'] or not results['documents'][0]:
                return []
            
            memories = []
            for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                memories.append({
                    'text': doc,
                    'timestamp': metadata['timestamp']
                })
            
            memories.sort(key=lambda x: x['timestamp'])
            return memories
        
        except Exception as e:
            print(f"❌ Erro ao buscar memórias: {e}")
            return []
    
    def count_memories(self, user_hash: str) -> int:
        """Conta memórias do usuário"""
        try:
            results = self.collection.query(
                query_texts=[""],
                where={"user_hash": user_hash},
                n_results=1000
            )
            return len(results['ids'][0]) if results['ids'] else 0
        except:
            return 0
    
    # ========== CONFLITOS (SQLite) ==========
    
    def save_conflict(self, user_hash: str, user_name: str, 
                     conflict: Dict, platform: str = "streamlit") -> int:
        """Salva conflito arquetípico"""
        cursor = self.sqlite_conn.cursor()
        
        cursor.execute("""
            INSERT INTO archetype_conflicts 
            (user_hash, user_name, archetype1, archetype2, trigger, platform)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_hash,
            user_name,
            conflict.get('archetype1', 'Desconhecido'),
            conflict.get('archetype2', 'Desconhecido'),
            conflict.get('trigger', ''),
            platform
        ))
        
        self.sqlite_conn.commit()
        return cursor.lastrowid
    
    def get_user_conflicts(self, user_hash: str, limit: int = 10) -> List[Dict]:
        """Busca conflitos do usuário"""
        cursor = self.sqlite_conn.cursor()
        
        cursor.execute("""
            SELECT * FROM archetype_conflicts
            WHERE user_hash = ?
            ORDER BY timestamp DESC LIMIT ?
        """, (user_hash, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # ========== ANÁLISES ==========
    
    def save_full_analysis(self, user_hash: str, user_name: str, 
                          analysis: Dict, platform: str = "streamlit") -> int:
        """Salva análise completa"""
        cursor = self.sqlite_conn.cursor()
        
        cursor.execute("""
            INSERT INTO full_analyses
            (user_hash, user_name, mbti, dominant_archetypes, phase, full_analysis, platform)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_hash,
            user_name,
            analysis.get('mbti', 'N/A'),
            str(analysis.get('archetypes', [])),
            analysis.get('phase', 1),
            analysis.get('insights', ''),
            platform
        ))
        
        self.sqlite_conn.commit()
        return cursor.lastrowid
    
    def get_user_analyses(self, user_hash: str) -> List[Dict]:
        """Busca histórico de análises"""
        cursor = self.sqlite_conn.cursor()
        
        cursor.execute("""
            SELECT * FROM full_analyses
            WHERE user_hash = ?
            ORDER BY timestamp DESC
        """, (user_hash,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # ========== METADADOS ==========
    
    def _update_user_metadata(self, user_hash: str, user_name: str, platform: str):
        """Atualiza metadados do usuário"""
        cursor = self.sqlite_conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_metadata (user_hash, user_name, platform, total_messages)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(user_hash) DO UPDATE SET
                last_interaction = CURRENT_TIMESTAMP,
                total_messages = total_messages + 1
        """, (user_hash, user_name, platform))
        
        self.sqlite_conn.commit()
    
    def get_user_stats(self, user_hash: str) -> Optional[Dict]:
        """Busca estatísticas do usuário"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT * FROM user_metadata WHERE user_hash = ?", (user_hash,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_users(self, platform: Optional[str] = None) -> List[Dict]:
        """Lista todos os usuários"""
        cursor = self.sqlite_conn.cursor()
        
        if platform:
            cursor.execute("""
                SELECT * FROM user_metadata
                WHERE platform = ?
                ORDER BY last_interaction DESC
            """, (platform,))
        else:
            cursor.execute("""
                SELECT * FROM user_metadata
                ORDER BY last_interaction DESC
            """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Fecha conexões"""
        self.sqlite_conn.close()


# ============================================================
# SEÇÃO 3: MOTOR JUNGUIANO
# ============================================================

class JungianEngine:
    """Motor de análise junguiana"""
    
    def __init__(self, db: DatabaseManager):
        """Inicializa motor junguiano"""
        self.db = db
        
        # Inicializa cliente OpenAI (com suporte a xAI Grok)
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Cliente xAI (para modelos Grok)
        self.xai_client = OpenAI(
            api_key=Config.XAI_API_KEY,
            base_url="https://api.x.ai/v1"
        )
    
    def process_message(self, user_hash: str, user_name: str, 
                       message: str, platform: str = "streamlit",
                       model: str = "gpt-4o-mini") -> Dict:
        """
        Processa mensagem do usuário
        
        Returns:
            {
                'response': str,
                'conflict': Optional[Dict],
                'memory_count': int
            }
        """
        
        # 1. Buscar contexto (memórias recentes)
        memories = self.db.get_user_memories(user_hash, Config.MAX_CONTEXT_MEMORIES)
        
        context = "\n".join([m['text'] for m in memories[-5:]]) if memories else ""
        
        # 2. Construir mensagens para LLM
        messages = [
            {"role": "system", "content": Config.SYSTEM_PROMPT}
        ]
        
        if context:
            messages.append({
                "role": "system", 
                "content": f"Contexto das últimas conversas:\n{context}"
            })
        
        messages.append({"role": "user", "content": message})
        
        # 3. Chamar LLM apropriado
        try:
            if model.startswith("grok"):
                completion = self.xai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7
                )
            else:
                completion = self.openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7
                )
            
            response = completion.choices[0].message.content
        
        except Exception as e:
            print(f"❌ Erro ao chamar LLM: {e}")
            response = "Desculpe, tive um problema técnico. Pode tentar novamente?"
        
        # 4. Detectar conflito arquetípico
        conflict = self._extract_conflict(response)
        
        # 5. Salvar memória
        self.db.save_memory(
            user_hash=user_hash,
            user_name=user_name,
            message=message,
            response=response,
            platform=platform,
            conflict=conflict
        )
        
        # 6. Remover marcador de conflito da resposta
        if conflict:
            response = response.split("[CONFLITO:")[0].strip()
        
        return {
            'response': response,
            'conflict': conflict,
            'memory_count': self.db.count_memories(user_hash)
        }
    
    def _extract_conflict(self, response: str) -> Optional[Dict]:
        """Extrai conflito arquetípico da resposta"""
        if "[CONFLITO:" not in response:
            return None
        
        try:
            conflict_part = response.split("[CONFLITO:")[1].split("]")[0]
            
            archetypes_part = conflict_part.split("|")[0].strip()
            arch1, arch2 = archetypes_part.split(" vs ")
            
            trigger = ""
            if "Gatilho:" in conflict_part:
                trigger = conflict_part.split("Gatilho:")[1].strip()
            
            return {
                'archetype1': arch1.strip(),
                'archetype2': arch2.strip(),
                'trigger': trigger
            }
        
        except:
            return None
    
    def generate_full_analysis(self, user_hash: str, user_name: str,
                              platform: str = "streamlit",
                              model: str = "gpt-4o") -> Optional[Dict]:
        """Gera análise junguiana completa"""
        
        # 1. Verificar se há memórias suficientes
        memory_count = self.db.count_memories(user_hash)
        
        if memory_count < Config.MIN_MEMORIES_FOR_ANALYSIS:
            return None
        
        # 2. Buscar dados
        memories = self.db.get_user_memories(user_hash, 50)
        conflicts = self.db.get_user_conflicts(user_hash, 20)
        
        memories_text = "\n\n".join([m['text'] for m in memories])
        conflicts_text = "\n".join([
            f"- {c['archetype1']} vs {c['archetype2']}: {c['trigger']}"
            for c in conflicts
        ])
        
        # 3. Estimar MBTI
        mbti = self._estimate_mbti(memories_text, model)
        
        # 4. Gerar análise completa
        prompt = Config.FULL_ANALYSIS_PROMPT.format(
            memories=memories_text[:3000],  # Limitar tokens
            conflicts=conflicts_text if conflicts else "Nenhum conflito registrado ainda.",
            mbti=mbti
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
            
            analysis_text = completion.choices[0].message.content
            
            # 5. Salvar análise
            analysis = {
                'mbti': mbti,
                'insights': analysis_text,
                'archetypes': self._extract_dominant_archetypes(analysis_text),
                'phase': self._extract_phase(analysis_text)
            }
            
            self.db.save_full_analysis(user_hash, user_name, analysis, platform)
            
            return analysis
        
        except Exception as e:
            print(f"❌ Erro ao gerar análise: {e}")
            return None
    
    def _estimate_mbti(self, memories_text: str, model: str) -> str:
        """Estima tipo MBTI baseado nas conversas"""
        prompt = Config.MBTI_ANALYSIS_PROMPT.format(
            memories=memories_text[:2000],
            archetype_analysis="Análise em progresso..."
        )
        
        try:
            if model.startswith("grok"):
                completion = self.xai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5
                )
            else:
                completion = self.openai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5
                )
            
            mbti = completion.choices[0].message.content.strip()
            
            # Validar formato
            if len(mbti) == 4 and mbti.isupper():
                return mbti
            
            return "INFP"  # Padrão
        
        except:
            return "INFP"
    
    def _extract_dominant_archetypes(self, analysis_text: str) -> List[str]:
        """Extrai arquétipos dominantes da análise"""
        archetypes_found = []
        
        for archetype_name in Config.ARCHETYPES.keys():
            if archetype_name.lower() in analysis_text.lower():
                archetypes_found.append(archetype_name)
        
        return archetypes_found[:5]  # Top 5
    
    def _extract_phase(self, analysis_text: str) -> int:
        """Tenta extrair fase da jornada (1-5)"""
        for phase in [5, 4, 3, 2, 1]:
            if f"fase {phase}" in analysis_text.lower():
                return phase
        
        return 3  # Padrão: meio da jornada


# ============================================================
# SEÇÃO 4: FUNÇÕES AUXILIARES
# ============================================================

def create_user_hash(identifier: str) -> str:
    """Cria hash único para usuário"""
    return hashlib.sha256(identifier.encode()).hexdigest()[:16]


def format_conflict_for_display(conflict: Dict) -> str:
    """Formata conflito para exibição"""
    arch1 = conflict['archetype1']
    arch2 = conflict['archetype2']
    trigger = conflict.get('trigger', 'Não especificado')
    
    emoji1 = Config.ARCHETYPES.get(arch1, {}).get('emoji', '❓')
    emoji2 = Config.ARCHETYPES.get(arch2, {}).get('emoji', '❓')
    
    return f"{emoji1} **{arch1}** vs {emoji2} **{arch2}**\n\n🎯 _Gatilho:_ {trigger}"


def format_archetype_info(archetype_name: str) -> str:
    """Retorna informações formatadas sobre um arquétipo"""
    info = Config.ARCHETYPES.get(archetype_name)
    
    if not info:
        return f"❓ Arquétipo '{archetype_name}' não encontrado."
    
    return f"""
{info['emoji']} **{archetype_name}**

📖 **Descrição:**
{info['description']}

🌑 **Sombra:**
{info['shadow']}

🔑 **Palavras-chave:**
{', '.join(info['keywords'])}
"""


# ============================================================
# INICIALIZAÇÃO
# ============================================================

# Validar configurações ao importar
try:
    Config.validate()
    print("✅ Configurações validadas com sucesso!")
except ValueError as e:
    print(f"⚠️  {e}")


# Exemplo de uso (pode ser comentado em produção)
if __name__ == "__main__":
    print("🧠 Jung Core - Motor Junguiano Unificado")
    print("=" * 50)
    
    # Testar conexões
    db = DatabaseManager()
    print("✅ Database Manager inicializado")
    
    engine = JungianEngine(db)
    print("✅ Jungian Engine inicializado")
    
    print("\n📊 Estatísticas:")
    print(f"  - Arquétipos disponíveis: {len(Config.ARCHETYPES)}")
    print(f"  - Usuários cadastrados: {len(db.get_all_users())}")
    
    db.close()
    print("\n✅ Teste concluído!")