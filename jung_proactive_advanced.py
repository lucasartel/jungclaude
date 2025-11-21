"""
jung_proactive_advanced.py - Sistema Proativo Avançado HÍBRIDO v4.0
====================================================================

🧠 VERSÃO 4.0 - HÍBRIDO PREMIUM
   Integração total com jung_core.py v4.0 (ChromaDB + OpenAI + SQLite)

Características APRIMORADAS:
- Rotação de duplas arquetípicas (personalidade multifacetada)
- Extração semântica de tópicos via ChromaDB
- Uso de fatos estruturados para insights personalizados
- Geração de conhecimento autônomo em múltiplos domínios
- Reset automático de cronômetro ao receber mensagens
- Tracking de complexidade e evolução do agente
- Sistema de memória de abordagens anteriores

Autor: Sistema Jung Claude
Data: 2025-11-20
Versão: 4.0 - HÍBRIDO PREMIUM
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

# ✅ IMPORTS HÍBRIDOS v4.0
from jung_core import (
    HybridDatabaseManager,
    Config,
    send_to_xai
)

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
    SCIENTIFIC = "científico"
    MYTHOLOGICAL = "mitológico"

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
    facts_used: List[str]  # Fatos estruturados usados

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
# BANCO DE DADOS ESTENDIDO (COMPATÍVEL COM HÍBRIDO)
# ============================================================

class ProactiveAdvancedDB:
    """Gerencia dados do sistema proativo avançado - COMPATÍVEL v4.0"""
    
    def __init__(self, db: HybridDatabaseManager):
        self.db = db
        self._create_advanced_tables()
    
    def _create_advanced_tables(self):
        """Cria tabelas adicionais para sistema avançado (se não existirem)"""
        
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
                facts_used TEXT,  -- JSON array
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
                extraction_method TEXT DEFAULT 'llm',  -- 'llm', 'semantic', 'pattern'
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
             complexity_score, facts_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            approach.archetype_pair.primary,
            approach.archetype_pair.secondary,
            approach.knowledge_domain.value,
            approach.topic_extracted,
            approach.autonomous_insight,
            approach.complexity_score,
            json.dumps(approach.facts_used)
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
    
    def record_topic(self, user_id: str, topic: str, method: str = 'llm'):
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
                INSERT INTO extracted_topics (user_id, topic, extraction_method)
                VALUES (?, ?, ?)
            """, (user_id, topic, method))
        
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
# SISTEMA PROATIVO AVANÇADO - VERSÃO HÍBRIDA v4.0
# ============================================================

class ProactiveAdvancedSystem:
    """Sistema proativo HÍBRIDO com personalidade complexa e conhecimento autônomo"""
    
    def __init__(self, db: HybridDatabaseManager):
        self.db = db
        self.proactive_db = ProactiveAdvancedDB(db)
        
        # Configurações (podem ser ajustadas)
        self.inactivity_threshold_hours = 3  # Horas de inatividade necessárias
        self.cooldown_hours = 6  # Cooldown entre mensagens proativas
        self.min_conversations_required = 5  # Mínimo de conversas para ativar
    
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
        
        # Análise de keywords
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ['história', 'passado', 'época', 'século', 'guerra', 'civilização']):
            return KnowledgeDomain.HISTORICAL
        
        if any(word in topic_lower for word in ['sentido', 'existência', 'razão', 'pensar', 'verdade', 'ética']):
            return KnowledgeDomain.PHILOSOPHICAL
        
        if any(word in topic_lower for word in ['deus', 'fé', 'espiritual', 'religião', 'sagrado', 'divino']):
            return KnowledgeDomain.RELIGIOUS
        
        if any(word in topic_lower for word in ['técnica', 'método', 'processo', 'sistema', 'tecnologia']):
            return KnowledgeDomain.TECHNICAL
        
        if any(word in topic_lower for word in ['arte', 'beleza', 'criação', 'estética', 'música', 'pintura']):
            return KnowledgeDomain.ARTISTIC
        
        if any(word in topic_lower for word in ['ciência', 'experimento', 'física', 'biologia', 'química']):
            return KnowledgeDomain.SCIENTIFIC
        
        if any(word in topic_lower for word in ['mito', 'lenda', 'arquétipo', 'herói', 'jornada']):
            return KnowledgeDomain.MYTHOLOGICAL
        
        # Default
        return KnowledgeDomain.PSYCHOLOGICAL
    
    def _extract_topic_semantically(self, user_id: str) -> Optional[str]:
        """✅ NOVO: Extração semântica de tópico via ChromaDB"""
        
        if not self.db.chroma_enabled:
            print("⚠️  ChromaDB desabilitado, usando extração LLM")
            return self._extract_topic_from_conversations(user_id)
        
        try:
            # Buscar últimas conversas
            conversations = self.db.get_user_conversations(user_id, limit=20)
            
            if not conversations:
                return None
            
            # Concatenar inputs do usuário
            user_inputs = [c['user_input'] for c in conversations[:10]]
            combined_text = " ".join(user_inputs)
            
            # Extrair palavras-chave frequentes
            from collections import Counter
            import re
            
            # Tokenizar
            words = re.findall(r'\b\w{4,}\b', combined_text.lower())
            
            # Stopwords simples
            stopwords = {
                'para', 'com', 'que', 'não', 'uma', 'isso', 'mas', 'por',
                'como', 'mais', 'sem', 'onde', 'quando', 'quem', 'sobre'
            }
            
            filtered_words = [w for w in words if w not in stopwords]
            
            # Contar frequências
            word_counts = Counter(filtered_words)
            
            # Top 5 palavras
            top_words = word_counts.most_common(5)
            
            if not top_words:
                return self._extract_topic_from_conversations(user_id)
            
            # Formular tópico
            topic_keywords = [word for word, _ in top_words]
            topic = " ".join(topic_keywords[:3])  # Pegar top 3
            
            # Refinar com LLM
            refinement_prompt = f"""Dado estas palavras-chave frequentes nas conversas do usuário:

{', '.join(topic_keywords)}

Formule UM tópico central em 2-5 palavras. Exemplos:
- "desenvolvimento pessoal"
- "busca de sentido"
- "desafios profissionais"

Responda APENAS com o tópico:"""
            
            messages = [{"role": "user", "content": refinement_prompt}]
            
            refined_topic = send_to_xai(
                messages=messages,
                model="grok-4-fast-reasoning",
                max_tokens=50
            )
            
            final_topic = refined_topic.strip()
            
            # Registrar
            self.proactive_db.record_topic(user_id, final_topic, method='semantic')
            
            print(f"📌 Tópico extraído semanticamente: {final_topic}")
            
            return final_topic
            
        except Exception as e:
            print(f"❌ Erro na extração semântica: {e}")
            return self._extract_topic_from_conversations(user_id)
    
    def _extract_topic_from_conversations(self, user_id: str) -> Optional[str]:
        """Extrai tópico via LLM (fallback ou modo sem ChromaDB)"""
        
        conversations = self.db.get_user_conversations(user_id, limit=20)
        
        if not conversations:
            return None
        
        # Concatenar últimas mensagens
        recent_text = " ".join([
            conv['user_input'] for conv in conversations[:10]
        ])
        
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
            messages = [{"role": "user", "content": extraction_prompt}]
            
            response = send_to_xai(
                messages=messages,
                model="grok-4-fast-reasoning",
                max_tokens=50
            )
            
            topic = response.strip()
            
            # Registrar
            self.proactive_db.record_topic(user_id, topic, method='llm')
            
            return topic
            
        except Exception as e:
            print(f"❌ Erro ao extrair tópico: {e}")
            return "desenvolvimento pessoal"  # fallback
    
    def _get_relevant_facts(self, user_id: str, topic: str) -> List[str]:
        """✅ NOVO: Busca fatos estruturados relevantes ao tópico"""
        
        cursor = self.db.conn.cursor()
        
        # Buscar fatos que mencionam palavras-chave do tópico
        topic_words = topic.lower().split()
        
        facts = []
        
        cursor.execute("""
            SELECT fact_category, fact_key, fact_value
            FROM user_facts
            WHERE user_id = ? AND is_current = 1
        """, (user_id,))
        
        all_facts = cursor.fetchall()
        
        for fact in all_facts:
            fact_text = f"{fact['fact_key']}: {fact['fact_value']}".lower()
            
            # Checar se alguma palavra do tópico aparece
            if any(word in fact_text for word in topic_words):
                facts.append(f"{fact['fact_category']} - {fact['fact_key']}: {fact['fact_value']}")
        
        return facts[:5]  # Máximo 5 fatos
    
    def _generate_autonomous_knowledge(
        self,
        topic: str,
        domain: KnowledgeDomain,
        archetype_pair: ArchetypePair,
        user_name: str,
        relevant_facts: List[str]
    ) -> str:
        """🧠 GERAÇÃO DE CONHECIMENTO AUTÔNOMO - Versão HÍBRIDA"""
        
        # Construir contexto com fatos
        facts_context = ""
        if relevant_facts:
            facts_context = f"\n**FATOS SOBRE {user_name.upper()}:**\n"
            for fact in relevant_facts:
                facts_context += f"• {fact}\n"
        
        knowledge_prompt = f"""Você é um agente junguiano com personalidade única. Neste momento, você está manifestando os arquétipos **{archetype_pair.primary}** e **{archetype_pair.secondary}** ({archetype_pair.energy_profile}).

**CONTEXTO:**
O usuário ({user_name}) tem interesse no tópico: "{topic}"
{facts_context}

**SUA MISSÃO:**
Gerar um insight **autônomo** sobre este tópico a partir do domínio **{domain.value}**.

**INSTRUÇÕES:**

1. **Busque conhecimento** {domain.value} relacionado ao tópico
2. **Reformule** esse conhecimento através da sua personalidade arquetípica atual
3. **Conecte** com os fatos conhecidos sobre {user_name} (se houver)
4. **Personalize** a mensagem de forma autêntica
5. **Seja conciso** (máx. 3 parágrafos curtos)

**IMPORTANTE:**
- NÃO seja genérico
- NÃO apenas liste fatos
- FORMULE seu próprio entendimento reformulado
- FALE como se este conhecimento fosse SEU
- USE os fatos sobre {user_name} se forem relevantes

**EXEMPLO DE TOM:**

Se você está como **Sábio + Explorador**:
"Tenho pensado sobre [tópico]... No Egito antigo, [conexão histórica]. Isso me faz questionar [insight pessoal]. E você, {user_name}, considerando que [fato relevante], tem explorado isso de que forma?"

Se você está como **Rebelde + Sombra**:
"[Tópico] me incomoda... A filosofia tradicional diz [X], mas isso oculta [Y]. Precisamos olhar para [aspecto negligenciado]. Você, {user_name}, que [fato relevante], tem coragem de ver isso?"

**AGORA GERE SEU INSIGHT AUTÔNOMO:**"""
        
        try:
            messages = [{"role": "user", "content": knowledge_prompt}]
            
            response = send_to_xai(
                messages=messages,
                model="grok-4-fast-reasoning",
                temperature=0.8,
                max_tokens=500
            )
            
            return response.strip()
            
        except Exception as e:
            print(f"❌ Erro ao gerar conhecimento autônomo: {e}")
            return None
    
    def _calculate_complexity_score(self, insight: str, facts_used: int) -> float:
        """Calcula score de complexidade do insight gerado"""
        
        # Métricas
        word_count = len(insight.split())
        question_marks = insight.count('?')
        unique_concepts = len(set(insight.lower().split())) / max(1, word_count)
        
        # Score baseado em métricas
        score = min(1.0, (
            (word_count / 200) * 0.3 +  # Profundidade
            (question_marks / 3) * 0.2 +  # Questionamento
            unique_concepts * 0.3 +  # Diversidade conceitual
            (facts_used / 5) * 0.2  # Uso de fatos personalizados
        ))
        
        return round(score, 2)
    
    def check_and_generate_advanced_message(
        self,
        user_id: str,
        user_name: str
    ) -> Optional[str]:
        """✅ MÉTODO PRINCIPAL - Gera mensagem proativa avançada HÍBRIDA"""
        
        print(f"\n{'='*60}")
        print(f"🧠 GERAÇÃO PROATIVA AVANÇADA (HÍBRIDO v4.0) - {user_name}")
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
        
        # 3. Extrair tópico (SEMÂNTICO se ChromaDB ativo)
        topic = self._extract_topic_semantically(user_id)
        print(f"📌 Tópico extraído: {topic}")
        
        if not topic:
            print(f"❌ Falha ao extrair tópico")
            return None
        
        # 4. Selecionar domínio de conhecimento
        knowledge_domain = self._select_knowledge_domain(user_id, topic)
        print(f"📚 Domínio: {knowledge_domain.value}")
        
        # 5. Buscar fatos relevantes
        relevant_facts = self._get_relevant_facts(user_id, topic)
        print(f"📋 Fatos relevantes: {len(relevant_facts)}")
        
        # 6. Gerar conhecimento autônomo
        print(f"🧠 Gerando insight autônomo...")
        
        autonomous_insight = self._generate_autonomous_knowledge(
            topic=topic,
            domain=knowledge_domain,
            archetype_pair=archetype_pair,
            user_name=user_name,
            relevant_facts=relevant_facts
        )
        
        if not autonomous_insight:
            print(f"❌ Falha ao gerar insight")
            return None
        
        print(f"✅ Insight gerado ({len(autonomous_insight)} caracteres)")
        
        # 7. Calcular complexidade
        complexity_score = self._calculate_complexity_score(
            autonomous_insight, 
            len(relevant_facts)
        )
        print(f"📊 Complexidade: {complexity_score:.2f}")
        
        # 8. Criar abordagem
        approach = ProactiveApproach(
            archetype_pair=archetype_pair,
            knowledge_domain=knowledge_domain,
            topic_extracted=topic,
            autonomous_insight=autonomous_insight,
            timestamp=datetime.now(),
            complexity_score=complexity_score,
            facts_used=relevant_facts
        )
        
        # 9. Registrar no banco
        self.proactive_db.record_approach(approach, user_id)
        
        print(f"💾 Abordagem registrada no banco")
        print(f"{'='*60}\n")
        
        # 10. Retornar mensagem
        return autonomous_insight


# ============================================================
# TESTE (OPCIONAL)
# ============================================================

if __name__ == "__main__":
    print("🧠 Jung Proactive Advanced v4.0 - HÍBRIDO PREMIUM")
    print("✅ ChromaDB + OpenAI Embeddings + Fatos Estruturados")