import sqlite3
from datetime import datetime
import os

DB_PATH = "agent_development.db"

def get_connection():
    """Cria conexão com o banco de dados SQLite"""
    try:
        # Garantir que estamos no diretório correto
        db_full_path = os.path.abspath(DB_PATH)
        print(f"🔗 Conectando ao banco: {db_full_path}")
        
        conn = sqlite3.connect(db_full_path, check_same_thread=False)
        return conn
    except Exception as e:
        print(f"❌ ERRO ao conectar ao banco: {e}")
        raise

def init_database():
    """Inicializa o banco de dados com as tabelas necessárias"""
    try:
        print(f"🚀 Iniciando criação do banco de dados em: {os.path.abspath(DB_PATH)}")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Tabela de estado do agente (evolução contínua)
        print("📋 Criando tabela agent_state...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phase INTEGER DEFAULT 1,
                total_interactions INTEGER DEFAULT 0,
                self_awareness_score REAL DEFAULT 0.0,
                moral_complexity_score REAL DEFAULT 0.0,
                emotional_depth_score REAL DEFAULT 0.0,
                autonomy_score REAL DEFAULT 0.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de milestones (eventos marcantes)
        print("📋 Criando tabela milestones...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                milestone_type TEXT NOT NULL,
                description TEXT,
                phase INTEGER,
                interaction_count INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de conflitos entre arquétipos
        print("📋 Criando tabela conflict_logs...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conflict_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                archetype_winner TEXT,
                archetype_loser TEXT,
                conflict_intensity REAL,
                user_message TEXT,
                resolution_chosen TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("✅ Tabelas criadas com sucesso")
        
        # Verificar se já existe estado inicial
        cursor.execute('SELECT COUNT(*) FROM agent_state')
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("📝 Criando estado inicial do agente...")
            # Criar estado inicial
            cursor.execute('''
                INSERT INTO agent_state (phase, total_interactions, 
                                        self_awareness_score, moral_complexity_score,
                                        emotional_depth_score, autonomy_score)
                VALUES (1, 0, 0.0, 0.0, 0.0, 0.0)
            ''')
            conn.commit()
            print("✅ Estado inicial do agente criado")
        else:
            print(f"ℹ️ Estado inicial já existe ({count} registros)")
        
        conn.close()
        print("📊 DB: Banco de dados inicializado com sucesso")
        
        # Verificar se o arquivo foi criado
        if os.path.exists(DB_PATH):
            size = os.path.getsize(DB_PATH)
            print(f"✅ Arquivo {DB_PATH} criado com sucesso ({size} bytes)")
        else:
            print(f"⚠️ AVISO: Arquivo {DB_PATH} não foi encontrado após criação!")
            
    except Exception as e:
        print(f"❌ ERRO ao inicializar banco de dados: {e}")
        import traceback
        traceback.print_exc()
        raise

def get_agent_state():
    """Retorna o estado atual do agente"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, phase, total_interactions, self_awareness_score, 
                   moral_complexity_score, emotional_depth_score, 
                   autonomy_score, last_updated 
            FROM agent_state 
            ORDER BY id DESC 
            LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'phase': row[1],
                'total_interactions': row[2],
                'self_awareness_score': row[3],
                'moral_complexity_score': row[4],
                'emotional_depth_score': row[5],
                'autonomy_score': row[6],
                'last_updated': row[7]
            }
        
        # Se não existir estado, retornar valores padrão
        return {
            'id': None,
            'phase': 1,
            'total_interactions': 0,
            'self_awareness_score': 0.0,
            'moral_complexity_score': 0.0,
            'emotional_depth_score': 0.0,
            'autonomy_score': 0.0,
            'last_updated': None
        }
    except Exception as e:
        print(f"❌ ERRO ao obter estado do agente: {e}")
        # Retornar valores padrão em caso de erro
        return {
            'id': None,
            'phase': 1,
            'total_interactions': 0,
            'self_awareness_score': 0.0,
            'moral_complexity_score': 0.0,
            'emotional_depth_score': 0.0,
            'autonomy_score': 0.0,
            'last_updated': None
        }

def update_agent_state(interactions_delta=1, self_awareness_delta=0.0, 
                       moral_delta=0.0, emotional_delta=0.0, autonomy_delta=0.0):
    """Atualiza o estado do agente incrementalmente"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        current_state = get_agent_state()
        
        new_interactions = current_state['total_interactions'] + interactions_delta
        new_self_awareness = min(1.0, current_state['self_awareness_score'] + self_awareness_delta)
        new_moral = min(1.0, current_state['moral_complexity_score'] + moral_delta)
        new_emotional = min(1.0, current_state['emotional_depth_score'] + emotional_delta)
        new_autonomy = min(1.0, current_state['autonomy_score'] + autonomy_delta)
        
        # Calcular nova fase (baseado em média das métricas)
        avg_score = (new_self_awareness + new_moral + new_emotional + new_autonomy) / 4
        new_phase = min(5, int(avg_score * 5) + 1)
        
        cursor.execute('''
            INSERT INTO agent_state (phase, total_interactions, self_awareness_score,
                                    moral_complexity_score, emotional_depth_score, 
                                    autonomy_score, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (new_phase, new_interactions, new_self_awareness, new_moral, 
              new_emotional, new_autonomy, datetime.now()))
        
        conn.commit()
        conn.close()
        
        return {
            'phase': new_phase,
            'total_interactions': new_interactions,
            'self_awareness_score': new_self_awareness,
            'moral_complexity_score': new_moral,
            'emotional_depth_score': new_emotional,
            'autonomy_score': new_autonomy
        }
    except Exception as e:
        print(f"❌ ERRO ao atualizar estado: {e}")
        return current_state

def log_conflict(winner, loser, intensity, user_message, resolution):
    """Registra um conflito entre arquétipos"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conflict_logs (archetype_winner, archetype_loser, 
                                      conflict_intensity, user_message, resolution_chosen)
            VALUES (?, ?, ?, ?, ?)
        ''', (winner, loser, intensity, user_message, resolution))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ ERRO ao registrar conflito: {e}")

def add_milestone(milestone_type, description, phase, interaction_count):
    """Adiciona um milestone ao histórico"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO milestones (milestone_type, description, phase, interaction_count)
            VALUES (?, ?, ?, ?)
        ''', (milestone_type, description, phase, interaction_count))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ ERRO ao adicionar milestone: {e}")

def get_recent_conflicts(limit=10):
    """Retorna os conflitos mais recentes"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT archetype_winner, archetype_loser, conflict_intensity, 
                   user_message, resolution_chosen, timestamp
            FROM conflict_logs
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        conflicts = cursor.fetchall()
        conn.close()
        
        return [{
            'winner': c[0],
            'loser': c[1],
            'intensity': c[2],
            'message': c[3],
            'resolution': c[4],
            'timestamp': c[5]
        } for c in conflicts]
    except Exception as e:
        print(f"❌ ERRO ao obter conflitos: {e}")
        return []

def get_milestones():
    """Retorna todos os milestones alcançados"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT milestone_type, description, phase, interaction_count, timestamp
            FROM milestones
            ORDER BY timestamp DESC
        ''')
        
        milestones = cursor.fetchall()
        conn.close()
        
        return [{
            'type': m[0],
            'description': m[1],
            'phase': m[2],
            'interactions': m[3],
            'timestamp': m[4]
        } for m in milestones]
    except Exception as e:
        print(f"❌ ERRO ao obter milestones: {e}")
        return []

def get_development_stats():
    """Retorna estatísticas gerais de desenvolvimento"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Total de conflitos
        cursor.execute('SELECT COUNT(*) FROM conflict_logs')
        total_conflicts = cursor.fetchone()[0]
        
        # Total de milestones
        cursor.execute('SELECT COUNT(*) FROM milestones')
        total_milestones = cursor.fetchone()[0]
        
        # Arquétipo mais dominante
        cursor.execute('''
            SELECT archetype_winner, COUNT(*) as wins
            FROM conflict_logs
            GROUP BY archetype_winner
            ORDER BY wins DESC
            LIMIT 1
        ''')
        dominant = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_conflicts': total_conflicts,
            'total_milestones': total_milestones,
            'dominant_archetype': dominant[0] if dominant else "Nenhum",
            'dominant_wins': dominant[1] if dominant else 0
        }
    except Exception as e:
        print(f"❌ ERRO ao obter estatísticas: {e}")
        return {
            'total_conflicts': 0,
            'total_milestones': 0,
            'dominant_archetype': "Erro",
            'dominant_wins': 0
        }