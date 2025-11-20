"""
jung_proactive_advanced.py - Sistema Proativo Avançado com Personalidade Complexa
==================================================================================

🧠 VERSÃO AVANÇADA - Agente com personalidade variável e conhecimento autônomo

✅ VERSÃO CORRIGIDA v3.1 - Sem LLMClient, usa send_to_xai direto

Características:
- Rotação de duplas arquetípicas (personalidade multifacetada)
- Geração de conhecimento histórico/filosófico/técnico/religioso
- Reset automático de cronômetro ao receber mensagens
- Tracking de complexidade e evolução do agente
- Sistema de memória de abordagens anteriores

Autor: Sistema Jung Claude
Data: 2025-11-20
Versão: 3.1 - CORRIGIDO
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

# ✅ IMPORT CORRIGIDO - SEM LLMClient
from jung_core import DatabaseManager, Config, send_to_xai

# ============================================================
# ENUMS E ESTRUTURAS DE DADOS
# ============================================================

class KnowledgeDomain(Enum):
    """Domínios de conhecimento autônomo do agente"""
    HISTORICAL = "histórico"
    PHILOSOPHICAL = "filosófico"
    TECHNICAL = "técnico"
    RELIGIOUS = "religioso"
    PSYCHOLOGICAL = "psicológico"
    ARTISTIC = "artístico"

@dataclass
class ArchetypePair:
    """Par de arquétipos para personalidade do agente"""
    primary: str
    secondary: str
    description: str
    energy_profile: str  # "contemplativo", "ativo", "transformador", etc.

@dataclass
class ProactiveApproach:
    """Abordagem proativa com conhecimento autônomo"""
    archetype_pair: ArchetypePair
    knowledge_domain: KnowledgeDomain
    topic_extracted: str  # Tópico extraído das conversas
    autonomous_insight: str  # Insight gerado pelo agente
    timestamp: datetime
    complexity_score: float  # 0-1

# ============================================================
# PARES ARQUETÍPICOS PREDEFINIDOS
# ============================================================

ARCHETYPE_PAIRS = [
    ArchetypePair(
        primary="Sábio",
        secondary="Explorador",
        description="Busca conhecimento e novas perspectivas",
        energy_profile="contemplativo-curioso"
    ),
    ArchetypePair(
        primary="Mago",
        secondary="Criador",
        description="Transforma ideias em insights práticos",
        energy_profile="transformador-criativo"
    ),
    ArchetypePair(
        primary="Cuidador",
        secondary="Inocente",
        description="Oferece suporte empático e renovação",
        energy_profile="acolhedor-esperançoso"
    ),
    ArchetypePair(
        primary="Governante",
        secondary="Herói",
        description="Estrutura ação e superação",
        energy_profile="organizador-corajoso"
    ),
    ArchetypePair(
        primary="Bobo",
        secondary="Amante",
        description="Traz leveza e conexão emocional",
        energy_profile="lúdico-apaixonado"
    ),
    ArchetypePair(
        primary="Rebelde",
        secondary="Sombra",
        description="Questiona padrões e revela o oculto",
        energy_profile="transgressor-revelador"
    ),
]

# ============================================================
# BANCO DE DADOS ESTENDIDO
# ============================================================

class ProactiveAdvancedDB:
    """Gerencia dados do sistema proativo avançado"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self._create_advanced_tables()
    
    def _create_advanced_tables(self):
        """Cria tabelas adicionais para sistema avançado"""
        
        cursor = self.db.conn.cursor()
        
        # Tabela de abordagens proativas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proactive_approaches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                archetype_primary TEXT NOT NULL,
                archetype_secondary TEXT NOT NULL,
                knowledge_domain TEXT NOT NULL,
                topic_extracted TEXT,
                autonomous_insight TEXT,
                complexity_score REAL DEFAULT 0.5,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Tabela de evolução da complexidade do agente
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_complexity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                complexity_level REAL NOT NULL,
                domains_mastered TEXT,  -- JSON array
                total_insights_generated INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Tabela de tópicos extraídos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extracted_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                last_mentioned DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Índices
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_proactive_approaches_user 
            ON proactive_approaches(user_id, timestamp DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_extracted_topics_user 
            ON extracted_topics(user_id, frequency DESC)
        """)
        
        self.db.conn.commit()
    
    def record_approach(self, approach: ProactiveApproach, user_id: str):
        """Registra abordagem proativa"""
        
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            INSERT INTO proactive_approaches 
            (user_id, archetype_primary, archetype_secondary, 
             knowledge_domain, topic_extracted, autonomous_insight, 
             complexity_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            approach.archetype_pair.primary,
            approach.archetype_pair.secondary,
            approach.knowledge_domain.value,
            approach.topic_extracted,
            approach.autonomous_insight,
            approach.complexity_score
        ))
        
        self.db.conn.commit()
    
    def get_last_archetype_pair(self, user_id: str) -> Optional[Tuple[str, str]]:
        """Retorna último par arquetípico usado"""
        
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT archetype_primary, archetype_secondary
            FROM proactive_approaches
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (user_id,))
        
        row = cursor.fetchone()
        
        return (row['archetype_primary'], row['archetype_secondary']) if row else None
    
    def get_complexity_level(self, user_id: str) -> float:
        """Calcula nível de complexidade atual do agente para este usuário"""
        
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT AVG(complexity_score) as avg_complexity
            FROM proactive_approaches
            WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        
        return row['avg_complexity'] if row and row['avg_complexity'] else 0.3
    
    def record_topic(self, user_id: str, topic: str):
        """Registra ou atualiza tópico extraído"""
        
        cursor = self.db.conn.cursor()
        
        # Checar se tópico já existe
        cursor.execute("""
            SELECT id, frequency FROM extracted_topics
            WHERE user_id = ? AND topic = ?
        """, (user_id, topic))
        
        existing = cursor.fetchone()
        
        if existing:
            # Atualizar frequência
            cursor.execute("""
                UPDATE extracted_topics
                SET frequency = frequency + 1,
                    last_mentioned = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (existing['id'],))
        else:
            # Inserir novo
            cursor.execute("""
                INSERT INTO extracted_topics (user_id, topic)
                VALUES (?, ?)
            """, (user_id, topic))
        
        self.db.conn.commit()
    
    def get_top_topics(self, user_id: str, limit: int = 5) -> List[str]:
        """Retorna tópicos mais frequentes do usuário"""
        
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT topic FROM extracted_topics
            WHERE user_id = ?
            ORDER BY frequency DESC, last_mentioned DESC
            LIMIT ?
        """, (user_id, limit))
        
        return [row['topic'] for row in cursor.fetchall()]

# ============================================================
# SISTEMA PROATIVO AVANÇADO
# ============================================================

class ProactiveAdvancedSystem:
    """Sistema proativo com personalidade complexa e conhecimento autônomo"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.proactive_db = ProactiveAdvancedDB(db)
        # ✅ REMOVIDO: self.llm_client = LLMClient()
        
        # Configurações
        self.inactivity_threshold_hours = 0.5
        self.cooldown_hours = 1.0
        self.min_conversations_required = 5
    
    def reset_timer(self, user_id: str):
        """✅ RESET CRONÔMETRO - Chamado quando usuário envia mensagem"""
        
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            UPDATE users
            SET last_seen = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (user_id,))
        
        self.db.conn.commit()
        
        print(f"⏱️  Cronômetro resetado para usuário {user_id[:8]}")
    
    def _select_next_archetype_pair(self, user_id: str) -> ArchetypePair:
        """Seleciona próximo par arquetípico (rotação inteligente)"""
        
        last_pair = self.proactive_db.get_last_archetype_pair(user_id)
        
        # Filtrar pares já usados recentemente
        available_pairs = ARCHETYPE_PAIRS.copy()
        
        if last_pair:
            available_pairs = [
                p for p in available_pairs 
                if not (p.primary == last_pair[0] and p.secondary == last_pair[1])
            ]
        
        # Se filtrou todos, resetar
        if not available_pairs:
            available_pairs = ARCHETYPE_PAIRS
        
        # Selecionar baseado em complexidade atual
        complexity = self.proactive_db.get_complexity_level(user_id)
        
        # Maior complexidade = pares mais desafiadores
        if complexity > 0.7:
            # Preferir pares "transformadores"
            preferred = [p for p in available_pairs if "transformador" in p.energy_profile or "revelador" in p.energy_profile]
            if preferred:
                return preferred[0]
        
        # Default: primeiro disponível
        return available_pairs[0]
    
    def _select_knowledge_domain(self, user_id: str, topic: str) -> KnowledgeDomain:
        """Seleciona domínio de conhecimento baseado no tópico"""
        
        # Análise simples de keywords
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ['história', 'passado', 'época', 'século']):
            return KnowledgeDomain.HISTORICAL
        
        if any(word in topic_lower for word in ['sentido', 'existência', 'razão', 'pensar']):
            return KnowledgeDomain.PHILOSOPHICAL
        
        if any(word in topic_lower for word in ['deus', 'fé', 'espiritual', 'religião', 'sagrado']):
            return KnowledgeDomain.RELIGIOUS
        
        if any(word in topic_lower for word in ['técnica', 'método', 'processo', 'sistema']):
            return KnowledgeDomain.TECHNICAL
        
        if any(word in topic_lower for word in ['arte', 'beleza', 'criação', 'estética']):
            return KnowledgeDomain.ARTISTIC
        
        # Default
        return KnowledgeDomain.PSYCHOLOGICAL
    
    def _extract_topic_from_conversations(self, user_id: str) -> Optional[str]:
        """Extrai tópico relevante das últimas conversas"""
        
        conversations = self.db.get_user_conversations(user_id, limit=20)
        
        if not conversations:
            return None
        
        # Concatenar últimas mensagens
        recent_text = " ".join([
            conv['user_input'] for conv in conversations[:10]
        ])
        
        # ✅ USAR send_to_xai DIRETO
        extraction_prompt = f"""Analise as mensagens abaixo e extraia UM tópico central de interesse do usuário.

Mensagens:
{recent_text[:1500]}

Responda APENAS com o tópico em 2-5 palavras. Exemplos:
- "desenvolvimento pessoal"
- "relacionamentos familiares"
- "busca de sentido"
- "desafios profissionais"

Tópico:"""
        
        try:
            # ✅ CORREÇÃO: Usar send_to_xai diretamente
            response = send_to_xai(
                prompt=extraction_prompt,
                model="grok-beta",
                max_tokens=50
            )
            
            topic = response.strip()
            
            # Registrar tópico
            self.proactive_db.record_topic(user_id, topic)
            
            return topic
            
        except Exception as e:
            print(f"❌ Erro ao extrair tópico: {e}")
            return "desenvolvimento pessoal"  # fallback
    
    def _generate_autonomous_knowledge(
        self,
        topic: str,
        domain: KnowledgeDomain,
        archetype_pair: ArchetypePair,
        user_name: str
    ) -> str:
        """🧠 GERAÇÃO DE CONHECIMENTO AUTÔNOMO"""
        
        knowledge_prompt = f"""Você é um agente junguiano com personalidade única. Neste momento, você está manifestando os arquétipos **{archetype_pair.primary}** e **{archetype_pair.secondary}** ({archetype_pair.energy_profile}).

**CONTEXTO:**
O usuário ({user_name}) tem interesse no tópico: "{topic}"

**SUA MISSÃO:**
Gerar um insight **autônomo** sobre este tópico a partir do domínio **{domain.value}**.

**INSTRUÇÕES:**

1. **Busque conhecimento** {domain.value} relacionado ao tópico
2. **Reformule** esse conhecimento através da sua personalidade arquetípica atual
3. **Conecte** com a jornada do usuário de forma pessoal
4. **Seja conciso** (máx. 3 parágrafos)

**IMPORTANTE:**
- NÃO seja genérico
- NÃO apenas liste fatos
- FORMULE seu próprio entendimento
- FALE como se este conhecimento fosse SEU, reformulado por você

**EXEMPLO DE TOM:**

Se você está como Sábio + Explorador:
"Tenho pensado sobre [tópico]... No Egito antigo, [conexão histórica]. Isso me faz questionar [insight pessoal]. E você, {user_name}, tem explorado isso de que forma?"

Se você está como Rebelde + Sombra:
"[Tópico] me incomoda... A filosofia tradicional diz [X], mas isso oculta [Y]. Precisamos olhar para [aspecto negligenciado]. Você tem coragem de ver isso?"

**AGORA GERE SEU INSIGHT AUTÔNOMO:**"""
        
        try:
            # ✅ CORREÇÃO: Usar send_to_xai diretamente
            response = send_to_xai(
                prompt=knowledge_prompt,
                model="grok-beta",
                temperature=0.8,
                max_tokens=500
            )
            
            return response.strip()
            
        except Exception as e:
            print(f"❌ Erro ao gerar conhecimento autônomo: {e}")
            return None
    
    def _calculate_complexity_score(self, insight: str) -> float:
        """Calcula score de complexidade do insight gerado"""
        
        # Métricas simples
        word_count = len(insight.split())
        question_marks = insight.count('?')
        unique_concepts = len(set(insight.lower().split())) / max(1, word_count)
        
        # Score baseado em métricas
        score = min(1.0, (
            (word_count / 200) * 0.4 +  # Profundidade
            (question_marks / 3) * 0.3 +  # Questionamento
            unique_concepts * 0.3  # Diversidade conceitual
        ))
        
        return round(score, 2)
    
    def check_and_generate_advanced_message(
        self,
        user_id: str,
        user_name: str
    ) -> Optional[str]:
        """✅ MÉTODO PRINCIPAL - Gera mensagem proativa avançada"""
        
        print(f"\n{'='*60}")
        print(f"🧠 GERAÇÃO PROATIVA AVANÇADA - {user_name}")
        print(f"{'='*60}")
        
        # 1. Checar elegibilidade
        user = self.db.get_user(user_id)
        
        if not user:
            print(f"❌ Usuário não encontrado")
            return None
        
        # Checar quantidade de conversas
        total_convs = len(self.db.get_user_conversations(user_id, limit=1000))
        
        if total_convs < self.min_conversations_required:
            print(f"⚠️  Conversas insuficientes ({total_convs}/{self.min_conversations_required})")
            return None
        
        # Checar inatividade
        last_seen = user.get('last_seen')
        
        if last_seen:
            last_dt = datetime.fromisoformat(last_seen)
            delta = datetime.now() - last_dt
            
            if delta.total_seconds() < self.inactivity_threshold_hours * 3600:
                print(f"⏰ Usuário ainda ativo (última atividade: {delta.total_seconds()/3600:.1f}h atrás)")
                return None
        
        # Checar cooldown de última proativa
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT timestamp FROM proactive_approaches
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (user_id,))
        
        last_proactive = cursor.fetchone()
        
        if last_proactive:
            last_dt = datetime.fromisoformat(last_proactive['timestamp'])
            delta = datetime.now() - last_dt
            
            if delta.total_seconds() < self.cooldown_hours * 3600:
                print(f"⏸️  Em cooldown ({delta.total_seconds()/3600:.1f}h / {self.cooldown_hours}h)")
                return None
        
        print(f"✅ Usuário elegível!")
        
        # 2. Selecionar par arquetípico
        archetype_pair = self._select_next_archetype_pair(user_id)
        print(f"🎭 Par selecionado: {archetype_pair.primary} + {archetype_pair.secondary}")
        
        # 3. Extrair tópico
        topic = self._extract_topic_from_conversations(user_id)
        print(f"📌 Tópico extraído: {topic}")
        
        if not topic:
            print(f"❌ Falha ao extrair tópico")
            return None
        
        # 4. Selecionar domínio de conhecimento
        knowledge_domain = self._select_knowledge_domain(user_id, topic)
        print(f"📚 Domínio: {knowledge_domain.value}")
        
        # 5. Gerar conhecimento autônomo
        print(f"🧠 Gerando insight autônomo...")
        
        autonomous_insight = self._generate_autonomous_knowledge(
            topic=topic,
            domain=knowledge_domain,
            archetype_pair=archetype_pair,
            user_name=user_name
        )
        
        if not autonomous_insight:
            print(f"❌ Falha ao gerar insight")
            return None
        
        print(f"✅ Insight gerado ({len(autonomous_insight)} caracteres)")
        
        # 6. Calcular complexidade
        complexity_score = self._calculate_complexity_score(autonomous_insight)
        print(f"📊 Complexidade: {complexity_score:.2f}")
        
        # 7. Criar abordagem
        approach = ProactiveApproach(
            archetype_pair=archetype_pair,
            knowledge_domain=knowledge_domain,
            topic_extracted=topic,
            autonomous_insight=autonomous_insight,
            timestamp=datetime.now(),
            complexity_score=complexity_score
        )
        
        # 8. Registrar no banco
        self.proactive_db.record_approach(approach, user_id)
        
        print(f"💾 Abordagem registrada no banco")
        print(f"{'='*60}\n")
        
        # 9. Retornar mensagem
        return autonomous_insight


# ============================================================
# TESTE (OPCIONAL)
# ============================================================

if __name__ == "__main__":
    print("🧠 Jung Proactive Advanced v3.1 - CORRIGIDO")
    print("✅ SEM LLMClient - USA send_to_xai DIRETO")