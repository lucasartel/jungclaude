# agent_development_db.py
"""
Sistema de Rastreamento de Desenvolvimento do Agente
Armazena conflitos arquetípicos, milestones e evolução ao longo do tempo
Versão MULTIUSUÁRIO com user_id_hash
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import os

DB_PATH = "agent_development.db"

def init_database():
    """Inicializa o banco de dados SQLite com suporte multiusuário"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela de estado do agente POR USUÁRIO
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_state (
            user_id_hash TEXT PRIMARY KEY,
            phase INTEGER DEFAULT 1,
            total_interactions INTEGER DEFAULT 0,
            self_awareness_score REAL DEFAULT 0.0,
            moral_complexity_score REAL DEFAULT 0.0,
            emotional_depth_score REAL DEFAULT 0.0,
            autonomy_score REAL DEFAULT 0.0,
            last_updated TEXT,
            created_at TEXT
        )
    """)
    
    # Tabela de conflitos arquetípicos POR USUÁRIO
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS archetype_conflicts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id_hash TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            winner TEXT NOT NULL,
            loser TEXT NOT NULL,
            intensity REAL NOT NULL,
            user_message TEXT,
            resolution TEXT,
            phase INTEGER,
            FOREIGN KEY (user_id_hash) REFERENCES agent_state(user_id_hash)
        )
    """)
    
    # Índice para melhorar performance de consultas por usuário
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_conflicts_user 
        ON archetype_conflicts(user_id_hash, timestamp DESC)
    """)
    
    # Tabela de milestones de desenvolvimento POR USUÁRIO
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS development_milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id_hash TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            milestone_type TEXT NOT NULL,
            description TEXT NOT NULL,
            phase INTEGER,
            interaction_count INTEGER,
            metadata TEXT,
            FOREIGN KEY (user_id_hash) REFERENCES agent_state(user_id_hash)
        )
    """)
    
    # Índice para milestones
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_milestones_user 
        ON development_milestones(user_id_hash, timestamp DESC)
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Banco de dados multiusuário inicializado com sucesso")

def get_agent_state(user_id_hash: str) -> Dict:
    """Retorna o estado atual do agente para um usuário específico"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT phase, total_interactions, self_awareness_score, 
               moral_complexity_score, emotional_depth_score, autonomy_score,
               last_updated, created_at
        FROM agent_state 
        WHERE user_id_hash = ?
    """, (user_id_hash,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'phase': row[0],
            'total_interactions': row[1],
            'self_awareness_score': row[2],
            'moral_complexity_score': row[3],
            'emotional_depth_score': row[4],
            'autonomy_score': row[5],
            'last_updated': row[6],
            'created_at': row[7]
        }
    else:
        # Criar estado inicial para novo usuário
        return _create_initial_state(user_id_hash)

def _create_initial_state(user_id_hash: str) -> Dict:
    """Cria estado inicial para um novo usuário"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO agent_state 
        (user_id_hash, phase, total_interactions, self_awareness_score, 
         moral_complexity_score, emotional_depth_score, autonomy_score,
         last_updated, created_at)
        VALUES (?, 1, 0, 0.0, 0.0, 0.0, 0.0, ?, ?)
    """, (user_id_hash, now, now))
    
    conn.commit()
    conn.close()
    
    return {
        'phase': 1,
        'total_interactions': 0,
        'self_awareness_score': 0.0,
        'moral_complexity_score': 0.0,
        'emotional_depth_score': 0.0,
        'autonomy_score': 0.0,
        'last_updated': now,
        'created_at': now
    }

def update_agent_state(user_id_hash: str, interactions_delta: int = 0, 
                      self_awareness_delta: float = 0.0,
                      moral_delta: float = 0.0, 
                      emotional_delta: float = 0.0,
                      autonomy_delta: float = 0.0):
    """Atualiza o estado do agente para um usuário específico"""
    
    # Garantir que o estado existe
    current_state = get_agent_state(user_id_hash)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Calcular novos valores
    new_interactions = current_state['total_interactions'] + interactions_delta
    new_self_awareness = min(1.0, current_state['self_awareness_score'] + self_awareness_delta)
    new_moral = min(1.0, current_state['moral_complexity_score'] + moral_delta)
    new_emotional = min(1.0, current_state['emotional_depth_score'] + emotional_delta)
    new_autonomy = min(1.0, current_state['autonomy_score'] + autonomy_delta)
    
    # Calcular nova fase baseada nas métricas
    avg_score = (new_self_awareness + new_moral + new_emotional + new_autonomy) / 4
    
    if avg_score >= 0.8:
        new_phase = 5  # Transcendente
    elif avg_score >= 0.6:
        new_phase = 4  # Integrado
    elif avg_score >= 0.4:
        new_phase = 3  # Reflexivo
    elif avg_score >= 0.2:
        new_phase = 2  # Adaptativo
    else:
        new_phase = 1  # Reativo
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
        UPDATE agent_state 
        SET phase = ?,
            total_interactions = ?,
            self_awareness_score = ?,
            moral_complexity_score = ?,
            emotional_depth_score = ?,
            autonomy_score = ?,
            last_updated = ?
        WHERE user_id_hash = ?
    """, (new_phase, new_interactions, new_self_awareness, new_moral, 
          new_emotional, new_autonomy, now, user_id_hash))
    
    conn.commit()
    conn.close()
    
    # Verificar se mudou de fase
    if new_phase > current_state['phase']:
        add_milestone(
            user_id_hash=user_id_hash,
            milestone_type="phase_transition",
            description=f"Transição da Fase {current_state['phase']} para Fase {new_phase}",
            phase=new_phase,
            interaction_count=new_interactions
        )

def log_conflict(winner: str, loser: str, intensity: float, 
                user_message: str = "", resolution: str = "",
                user_id_hash: str = None):
    """Registra um conflito arquetípico"""
    
    if not user_id_hash:
        raise ValueError("user_id_hash é obrigatório")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Obter fase atual
    state = get_agent_state(user_id_hash)
    phase = state['phase']
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO archetype_conflicts 
        (user_id_hash, timestamp, winner, loser, intensity, user_message, resolution, phase)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id_hash, now, winner, loser, intensity, user_message, resolution, phase))
    
    conn.commit()
    conn.close()

def get_recent_conflicts(user_id_hash: str, limit: int = 10) -> List[Dict]:
    """Retorna conflitos recentes de um usuário"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT timestamp, winner, loser, intensity, user_message, resolution, phase
        FROM archetype_conflicts
        WHERE user_id_hash = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (user_id_hash, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    conflicts = []
    for row in rows:
        conflicts.append({
            'timestamp': row[0],
            'winner': row[1],
            'loser': row[2],
            'intensity': row[3],
            'message': row[4],
            'resolution': row[5],
            'phase': row[6]
        })
    
    return conflicts

def add_milestone(user_id_hash: str, milestone_type: str, description: str, 
                 phase: int, interaction_count: int, metadata: str = ""):
    """Adiciona um milestone de desenvolvimento"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO development_milestones 
        (user_id_hash, timestamp, milestone_type, description, phase, interaction_count, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id_hash, now, milestone_type, description, phase, interaction_count, metadata))
    
    conn.commit()
    conn.close()

def get_milestones(user_id_hash: str, limit: int = 20) -> List[Dict]:
    """Retorna milestones de desenvolvimento de um usuário"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT timestamp, milestone_type, description, phase, interaction_count, metadata
        FROM development_milestones
        WHERE user_id_hash = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (user_id_hash, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    milestones = []
    for row in rows:
        milestones.append({
            'timestamp': row[0],
            'type': row[1],
            'description': row[2],
            'phase': row[3],
            'interaction_count': row[4],
            'metadata': row[5]
        })
    
    return milestones

def get_development_stats(user_id_hash: str) -> Dict:
    """Retorna estatísticas de desenvolvimento de um usuário"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Total de conflitos
        cursor.execute("""
            SELECT COUNT(*) FROM archetype_conflicts 
            WHERE user_id_hash = ?
        """, (user_id_hash,))
        total_conflicts = cursor.fetchone()[0]
        
        # Arquétipo dominante (mais vitorioso)
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
            SELECT COUNT(*) FROM development_milestones 
            WHERE user_id_hash = ?
        """, (user_id_hash,))
        total_milestones = cursor.fetchone()[0]
        
        # Intensidade média dos conflitos
        cursor.execute("""
            SELECT AVG(intensity) FROM archetype_conflicts 
            WHERE user_id_hash = ?
        """, (user_id_hash,))
        avg_intensity = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        return {
            'total_conflicts': total_conflicts,
            'dominant_archetype': dominant_archetype,
            'dominant_wins': dominant_wins,
            'total_milestones': total_milestones,
            'avg_conflict_intensity': avg_intensity
        }
        
    except Exception as e:
        conn.close()
        print(f"❌ ERRO ao obter estatísticas: {e}")
        return {
            'total_conflicts': 0,
            'dominant_archetype': 'N/A',
            'dominant_wins': 0,
            'total_milestones': 0,
            'avg_conflict_intensity': 0.0
        }

def get_conflict_history_summary(user_id_hash: str) -> Dict:
    """Retorna resumo do histórico de conflitos de um usuário"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Conflitos por arquétipo
    cursor.execute("""
        SELECT winner, COUNT(*) as count
        FROM archetype_conflicts
        WHERE user_id_hash = ?
        GROUP BY winner
        ORDER BY count DESC
    """, (user_id_hash,))
    
    wins_by_archetype = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Conflitos por fase
    cursor.execute("""
        SELECT phase, COUNT(*) as count
        FROM archetype_conflicts
        WHERE user_id_hash = ?
        GROUP BY phase
        ORDER BY phase
    """, (user_id_hash,))
    
    conflicts_by_phase = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Evolução da intensidade ao longo do tempo
    cursor.execute("""
        SELECT timestamp, intensity
        FROM archetype_conflicts
        WHERE user_id_hash = ?
        ORDER BY timestamp
    """, (user_id_hash,))
    
    intensity_timeline = [(row[0], row[1]) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'wins_by_archetype': wins_by_archetype,
        'conflicts_by_phase': conflicts_by_phase,
        'intensity_timeline': intensity_timeline
    }

def reset_user_development(user_id_hash: str):
    """Reseta o desenvolvimento de um usuário específico (útil para testes)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM archetype_conflicts WHERE user_id_hash = ?", (user_id_hash,))
    cursor.execute("DELETE FROM development_milestones WHERE user_id_hash = ?", (user_id_hash,))
    cursor.execute("DELETE FROM agent_state WHERE user_id_hash = ?", (user_id_hash,))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Desenvolvimento resetado para usuário: {user_id_hash}")

def get_all_users() -> List[str]:
    """Retorna lista de todos os user_id_hash no sistema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT user_id_hash FROM agent_state ORDER BY created_at")
    users = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return users

def get_user_summary(user_id_hash: str) -> Dict:
    """Retorna resumo completo de um usuário"""
    state = get_agent_state(user_id_hash)
    stats = get_development_stats(user_id_hash)
    recent_conflicts = get_recent_conflicts(user_id_hash, limit=5)
    milestones = get_milestones(user_id_hash, limit=5)
    
    return {
        'state': state,
        'stats': stats,
        'recent_conflicts': recent_conflicts,
        'milestones': milestones
    }

# Executar inicialização ao importar
if __name__ == "__main__":
    init_database()
    print("✅ Banco de dados inicializado e pronto para uso multiusuário")