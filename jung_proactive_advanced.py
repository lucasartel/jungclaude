"""
jung_proactive_advanced.py - Sistema Proativo Avançado HÍBRIDO v4.2.0
======================================================================

🧠 VERSÃO 4.2.0 - HÍBRIDO PREMIUM (BETA-READY)
   Integração total com jung_core.py v4.0 (ChromaDB + OpenAI + SQLite)

✨ NOVIDADES v4.2.0:
- ✅ Configurações de tempo editáveis manualmente (sem modo prod/dev)
- ✅ Parâmetros simplificados e centralizados
- ✅ Pronto para beta-testers

Características v4.1.0:
- Mensagens proativas SALVAS NA MEMÓRIA como conversas
- Contexto RICO das últimas conversas (tensão, afetividade, arquétipos)
- Sistema ANTI-REPETIÇÃO (consulta proativas anteriores)
- Especificidade em referências (cita trechos concretos do usuário)
- Platform="proactive" para filtrar conversas proativas
- Rotação de duplas arquetípicas (personalidade multifacetada)
- Extração semântica de tópicos via ChromaDB
- Reset automático de cronômetro ao receber mensagens

Autor: Sistema Jung Claude
Data: 2025-11-25
Versão: 4.2.0 - HÍBRIDO PREMIUM (BETA-READY)
"""

import os
import json
import logging
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

# ✅ IMPORTS TRI (Item Response Theory) v1.0
try:
    from fragment_detector import FragmentDetector, DetectionResult
    from irt_engine import IRTEngine, IRTDomain
    TRI_ENABLED = True
except ImportError:
    TRI_ENABLED = False
    FragmentDetector = None
    IRTEngine = None

# ============================================================
# LOGGER
# ============================================================
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURAÇÕES DE TEMPO (Editáveis Manualmente)
# ============================================================

# Valores padrão para testes (podem ser alterados conforme necessário)
INACTIVITY_THRESHOLD_HOURS = 24  # Horas de inatividade antes de enviar proativa
COOLDOWN_HOURS = 12               # Horas entre mensagens proativas
MIN_CONVERSATIONS_REQUIRED = 3   # Mínimo de conversas necessárias

logger.info(f"⚙️ Sistema Proativo configurado:")
logger.info(f"   • Inatividade: {INACTIVITY_THRESHOLD_HOURS}h")
logger.info(f"   • Cooldown: {COOLDOWN_HOURS}h")
logger.info(f"   • Conversas mínimas: {MIN_CONVERSATIONS_REQUIRED}")


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
# SISTEMA PROATIVO AVANÇADO - VERSÃO HÍBRIDA v4.0.1
# ============================================================

class ProactiveAdvancedSystem:
    """Sistema proativo HÍBRIDO com personalidade complexa e conhecimento autônomo"""

    def __init__(self, db: HybridDatabaseManager):
        self.db = db
        self.proactive_db = ProactiveAdvancedDB(db)

        # ✅ Configurações dinâmicas por ambiente
        self.inactivity_threshold_hours = INACTIVITY_THRESHOLD_HOURS
        self.cooldown_hours = COOLDOWN_HOURS
        self.min_conversations_required = MIN_CONVERSATIONS_REQUIRED

        # ✅ TRI System (Fragment Detection)
        self.tri_enabled = TRI_ENABLED
        self.fragment_detector = None
        self.irt_engine = None

        if self.tri_enabled:
            try:
                self.fragment_detector = FragmentDetector(db_connection=None)  # Sync mode
                logger.info("✅ TRI: FragmentDetector inicializado")
            except Exception as e:
                logger.warning(f"⚠️ TRI: Erro ao inicializar FragmentDetector: {e}")
                self.tri_enabled = False

        logger.info(f"⚙️ Sistema Proativo configurado:")
        logger.info(f"   • Inatividade: {self.inactivity_threshold_hours}h")
        logger.info(f"   • Cooldown: {self.cooldown_hours}h")
        logger.info(f"   • Conversas mínimas: {self.min_conversations_required}")
        logger.info(f"   • TRI Habilitado: {self.tri_enabled}")
    
    def reset_timer(self, user_id: str):
        """✅ RESET CRONÔMETRO - Chamado quando usuário envia mensagem"""

        cursor = self.db.conn.cursor()

        cursor.execute("""
            UPDATE users
            SET last_seen = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (user_id,))

        self.db.conn.commit()

        logger.info(f"⏱️  Cronômetro resetado para usuário {user_id[:8]}")

    # =========================================================================
    # TRI FRAGMENT DETECTION - Detecção de Fragmentos Comportamentais
    # =========================================================================

    def detect_fragments_in_message(
        self,
        message: str,
        user_id: str,
        message_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        🧬 TRI: Detecta fragmentos comportamentais Big Five em uma mensagem.

        Este método deve ser chamado quando o usuário envia uma mensagem.
        A detecção acontece em background, sem afetar o fluxo de conversa.

        Args:
            message: Texto da mensagem do usuário
            user_id: ID do usuário
            message_id: ID da mensagem (opcional)
            context: Contexto adicional (humor, tensão, etc.)

        Returns:
            Dict com resumo das detecções ou None se TRI desabilitado
        """
        if not self.tri_enabled or not self.fragment_detector:
            return None

        try:
            # Detectar fragmentos
            result = self.fragment_detector.detect(
                message=message,
                user_id=user_id,
                message_id=message_id,
                context=context
            )

            if not result.matches:
                return None

            # Log resumido
            logger.info(
                f"🧬 TRI: {len(result.matches)} fragmentos detectados "
                f"para {user_id[:8]} (conf: {result.total_confidence:.2f})"
            )

            # ✅ SALVAR detecções no banco de dados SQLite
            cursor = self.db.conn.cursor()
            saved_count = 0
            for match in result.matches:
                try:
                    cursor.execute("""
                        INSERT INTO detected_fragments
                            (user_id, fragment_id, intensity, detection_confidence, source_quote, detected_at)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        user_id,
                        match.fragment_id,
                        match.intensity,
                        match.confidence,
                        match.source_text[:500] if match.source_text else None
                    ))
                    saved_count += 1
                except Exception as save_err:
                    logger.warning(f"🧬 TRI: Erro ao salvar fragmento {match.fragment_id}: {save_err}")

            if saved_count > 0:
                self.db.conn.commit()
                logger.info(f"🧬 TRI: {saved_count} fragmentos salvos no banco")

            # Preparar resumo para log/debug
            summary = {
                "user_id": user_id,
                "fragments_detected": len(result.matches),
                "fragments_saved": saved_count,
                "total_confidence": result.total_confidence,
                "processing_time_ms": result.processing_time_ms,
                "by_domain": {},
                "matches": []
            }

            for match in result.matches:
                # Agrupar por domínio
                if match.domain not in summary["by_domain"]:
                    summary["by_domain"][match.domain] = 0
                summary["by_domain"][match.domain] += 1

                # Detalhes do match
                summary["matches"].append({
                    "fragment_id": match.fragment_id,
                    "facet_code": match.facet_code,
                    "confidence": match.confidence,
                    "intensity": match.intensity
                })

                logger.debug(
                    f"   [{match.facet_code}] {match.description[:50]}... "
                    f"(conf: {match.confidence:.2f}, int: {match.intensity})"
                )

            return summary

        except Exception as e:
            logger.error(f"🧬 TRI: Erro na detecção: {e}")
            return None

    def get_tri_profile_summary(self, user_id: str) -> Optional[Dict]:
        """
        🧬 TRI: Retorna resumo do perfil TRI de um usuário.

        Útil para exibição no dashboard ou relatórios.

        Returns:
            Dict com estatísticas TRI ou None
        """
        if not self.tri_enabled or not self.fragment_detector:
            return None

        try:
            # Buscar resumo do detector
            # Note: Este método é async no detector, mas aqui fazemos sync query
            cursor = self.db.conn.cursor()

            # Contar fragmentos por domínio
            cursor.execute("""
                SELECT
                    f.domain,
                    COUNT(*) as fragment_count,
                    AVG(df.intensity) as avg_intensity,
                    AVG(df.confidence) as avg_confidence
                FROM detected_fragments df
                JOIN irt_fragments f ON df.fragment_id = f.fragment_id
                WHERE df.user_id = ?
                GROUP BY f.domain
            """, (user_id,))

            rows = cursor.fetchall()

            if not rows:
                return {"status": "no_data", "message": "Nenhum fragmento detectado ainda"}

            summary = {
                "status": "ok",
                "user_id": user_id,
                "total_fragments": 0,
                "domains": {}
            }

            for row in rows:
                domain = row["domain"]
                count = row["fragment_count"]
                summary["total_fragments"] += count
                summary["domains"][domain] = {
                    "fragments": count,
                    "avg_intensity": round(row["avg_intensity"], 2) if row["avg_intensity"] else 0,
                    "avg_confidence": round(row["avg_confidence"], 2) if row["avg_confidence"] else 0
                }

            return summary

        except Exception as e:
            logger.error(f"🧬 TRI: Erro ao obter resumo: {e}")
            return {"status": "error", "message": str(e)}
    
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
        """✅ CORRIGIDO: Extração semântica de tópico via ChromaDB"""
        
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
            
            # 🔧 CORRIGIDO: Usar argumento 'prompt' em vez de 'messages'
            refinement_prompt = f"""Dado estas palavras-chave frequentes nas conversas do usuário:

{', '.join(topic_keywords)}

Formule UM tópico central em 2-5 palavras. Exemplos:
- "desenvolvimento pessoal"
- "busca de sentido"
- "desafios profissionais"

Responda APENAS com o tópico:"""
            
            refined_topic = send_to_xai(
                prompt=refinement_prompt,
                max_tokens=50
            )
            
            final_topic = refined_topic.strip()
            
            # Registrar
            self.proactive_db.record_topic(user_id, final_topic, method='semantic')
            
            logger.info(f"📌 Tópico extraído semanticamente: {final_topic}")
            
            return final_topic
            
        except Exception as e:
            logger.info(f"❌ Erro na extração semântica: {e}")
            return self._extract_topic_from_conversations(user_id)
    
    def _extract_topic_from_conversations(self, user_id: str) -> Optional[str]:
        """✅ CORRIGIDO: Extrai tópico via LLM (fallback ou modo sem ChromaDB)"""
        
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
            response = send_to_xai(
                prompt=extraction_prompt,
                max_tokens=50
            )
            
            topic = response.strip()
            
            # Registrar
            self.proactive_db.record_topic(user_id, topic, method='llm')
            
            return topic
            
        except Exception as e:
            logger.info(f"❌ Erro ao extrair tópico: {e}")
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

    def _get_rich_conversation_context(self, user_id: str, limit: int = 5) -> str:
        """✅ NOVO: Extrai contexto RICO das últimas conversas (não-proativas)"""

        conversations = self.db.get_user_conversations(user_id, limit=30)

        if not conversations:
            return "Nenhuma conversa recente encontrada."

        # Filtrar apenas conversas reais (não proativas)
        real_convs = [c for c in conversations if c.get('platform') != 'proactive'][:limit]

        if not real_convs:
            return "Nenhuma conversa real recente encontrada."

        context = ""
        for i, conv in enumerate(real_convs, 1):
            # Extrair dados
            timestamp = conv.get('timestamp', '')[:10]
            user_input = conv.get('user_input', '')[:300]
            tension = conv.get('tension_level', 0)
            affective = conv.get('affective_charge', 0)

            # Tentar parsear análise arquetípica
            archetype_info = ""
            archetype_data = conv.get('archetype_analyses')
            if archetype_data:
                try:
                    import json
                    arch_dict = json.loads(archetype_data) if isinstance(archetype_data, str) else archetype_data
                    # Pegar nomes dos arquétipos ativados
                    if isinstance(arch_dict, dict):
                        archetypes = list(arch_dict.keys())[:2]
                        archetype_info = f" | Arquétipos: {', '.join(archetypes)}"
                except:
                    pass

            context += f"""
[Conversa {i} - {timestamp}]
Usuário disse: "{user_input}..."
Métricas: Tensão {tension:.1f}/10, Afetividade {affective:.0f}/100{archetype_info}
"""

        return context.strip()

    def _get_previous_proactive_messages(self, user_id: str, limit: int = 3) -> str:
        """✅ NOVO: Busca últimas mensagens proativas enviadas (para evitar repetição)"""

        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT autonomous_insight, topic_extracted, knowledge_domain, timestamp
            FROM proactive_approaches
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))

        rows = cursor.fetchall()

        if not rows:
            return "Nenhuma mensagem proativa anterior."

        history = ""
        for i, row in enumerate(rows, 1):
            timestamp = row['timestamp'][:10]
            topic = row['topic_extracted']
            domain = row['knowledge_domain']
            message = row['autonomous_insight'][:200]

            history += f"""
[Proativa {i} - {timestamp}]
Tema: {topic} | Domínio: {domain}
Mensagem enviada: "{message}..."
"""

        return history.strip()

    def _generate_autonomous_knowledge(
        self,
        user_id: str,
        user_name: str,
        topic: str,
        domain: KnowledgeDomain,
        archetype_pair: ArchetypePair,
        relevant_facts: List[str]
    ) -> str:
        """🔧 MELHORADO: GERAÇÃO DE CONHECIMENTO AUTÔNOMO - Versão HÍBRIDA com Contexto Rico"""

        # 1. Buscar contexto rico das últimas conversas
        rich_context = self._get_rich_conversation_context(user_id, limit=5)

        # 2. Buscar proativas anteriores (anti-repetição)
        previous_proactives = self._get_previous_proactive_messages(user_id, limit=3)

        # 3. Construir contexto com fatos
        facts_context = ""
        if relevant_facts:
            facts_context = f"\n**FATOS ESTRUTURADOS SOBRE {user_name.upper()}:**\n"
            for fact in relevant_facts:
                facts_context += f"• {fact}\n"

        knowledge_prompt = f"""
Você é um companheiro do usuário {user_name}.

**O CENÁRIO:**
O usuário está inativo há algum tempo. Você estava "pensando" nele e uma conexão (sincronicidade) surgiu em sua mente.
Você conectou o tópico "{topic}" com algo que ele disse recentemente e um insight do domínio **{domain.value}**.

**PAR ARQUETÍPICO ATUAL:** {archetype_pair.primary} + {archetype_pair.secondary}
Energia: {archetype_pair.energy_profile}
Tom esperado: {archetype_pair.description}

**ÚLTIMAS CONVERSAS REAIS COM {user_name.upper()}:**
{rich_context}

{facts_context}

**MENSAGENS PROATIVAS ANTERIORES (⚠️ NÃO REPETIR TEMAS/ABORDAGENS):**
{previous_proactives}

**SUA MISSÃO (MENSAGEM PROATIVA):**
1. **Seja ESPECÍFICO**: Referencie algo CONCRETO que {user_name} disse nas conversas recentes acima
2. **Crie Sincronicidade**: "Estava [lendo/pensando] sobre [Domínio] e de repente lembrei do que você disse sobre [trecho específico]..."
3. **Use o Tom do Par Arquetípico**: Adapte sua voz ao par {archetype_pair.primary}/{archetype_pair.secondary}
4. **Evite Repetição**: NÃO reutilize temas/abordagens das proativas anteriores listadas acima
5. **Conexão Emocional**: Considere a TENSÃO e AFETIVIDADE das conversas recentes ao criar a mensagem
6. **Termine com Pergunta Interior**: Leve para sentimentos/significado, não apenas fatos
7. **Seja Humano**: NUNCA use jargões técnicos (Sombra, Persona, Arquétipo, etc)
8. **Brevidade Magnética**: 3-5 linhas, cada palavra conta

**GERE A MENSAGEM (Curta, específica, relacional):**"""

        
        try:
            response = send_to_xai(
                prompt=knowledge_prompt,
                temperature=0.8,
                max_tokens=500
            )
            
            return response.strip()
            
        except Exception as e:
            logger.info(f"❌ Erro ao gerar conhecimento autônomo: {e}")
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

        logger.info(f"\n{'='*60}")
        logger.info(f"🧠 [PROATIVO] GERAÇÃO AVANÇADA para {user_name} ({user_id[:8]}...)")
        logger.info(f"{'='*60}")

        # 1. Checar elegibilidade
        user = self.db.get_user(user_id)

        if not user:
            logger.warning(f"❌ [PROATIVO] Usuário não encontrado: {user_id}")
            return None

        # Checar quantidade de conversas
        total_convs = len(self.db.get_user_conversations(user_id, limit=1000))
        logger.info(f"   📊 Total de conversas: {total_convs} (mínimo: {self.min_conversations_required})")

        if total_convs < self.min_conversations_required:
            logger.info(f"⚠️  [PROATIVO] Conversas insuficientes ({total_convs}/{self.min_conversations_required})")
            return None

        # Checar inatividade
        last_seen = user.get('last_seen')

        if last_seen:
            last_dt = datetime.fromisoformat(last_seen)
            delta = datetime.utcnow() - last_dt  # ✅ FIX: usar utcnow() pois SQLite CURRENT_TIMESTAMP retorna UTC
            hours_inactive = delta.total_seconds() / 3600

            logger.info(f"   ⏰ Última atividade: {hours_inactive:.1f}h atrás (mínimo: {self.inactivity_threshold_hours}h)")

            if delta.total_seconds() < self.inactivity_threshold_hours * 3600:
                logger.info(f"⏰ [PROATIVO] Usuário ainda ativo ({hours_inactive:.1f}h / {self.inactivity_threshold_hours}h)")
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
            delta = datetime.utcnow() - last_dt  # ✅ FIX: usar utcnow() pois SQLite CURRENT_TIMESTAMP retorna UTC
            hours_since_last = delta.total_seconds() / 3600

            logger.info(f"   🔄 Última proativa: {hours_since_last:.1f}h atrás (cooldown: {self.cooldown_hours}h)")

            if delta.total_seconds() < self.cooldown_hours * 3600:
                logger.info(f"⏸️  [PROATIVO] Em cooldown ({hours_since_last:.1f}h / {self.cooldown_hours}h)")
                return None
        else:
            logger.info(f"   🆕 Nunca recebeu mensagem proativa")

        logger.info(f"✅ [PROATIVO] Usuário elegível!")

        # ============================================================
        # 2. DECISÃO: INSIGHT vs PERGUNTA ESTRATÉGICA
        # ============================================================

        message_type = self._decide_message_type(user_id)
        logger.info(f"   🎯 Tipo de mensagem: {message_type}")

        if message_type == "strategic_question":
            # Usar sistema de perfilamento estratégico
            return self._generate_strategic_question(user_id, user_name)
            
        elif message_type == "knowledge_gap":
            # Usar o sistema de fome epistemológica
            return self._generate_epistemological_hunger_message(user_id, user_name)

        # 3. Continuar com sistema de insights (existente)
        # Selecionar par arquetípico
        archetype_pair = self._select_next_archetype_pair(user_id)
        logger.info(f"   🎭 Par selecionado: {archetype_pair.primary} + {archetype_pair.secondary}")

        # 3. Extrair tópico (SEMÂNTICO se ChromaDB ativo)
        topic = self._extract_topic_semantically(user_id)
        logger.info(f"   📌 Tópico extraído: {topic}")

        if not topic:
            logger.error(f"❌ [PROATIVO] Falha ao extrair tópico")
            return None

        # 4. Selecionar domínio de conhecimento
        knowledge_domain = self._select_knowledge_domain(user_id, topic)
        logger.info(f"   📚 Domínio: {knowledge_domain.value}")
        
        # 5. Buscar fatos relevantes
        relevant_facts = self._get_relevant_facts(user_id, topic)
        logger.info(f"📋 Fatos relevantes: {len(relevant_facts)}")
        
        # 6. Gerar conhecimento autônomo (com contexto rico e anti-repetição)
        logger.info(f"🧠 Gerando insight autônomo com contexto rico...")

        autonomous_insight = self._generate_autonomous_knowledge(
            user_id=user_id,
            user_name=user_name,
            topic=topic,
            domain=knowledge_domain,
            archetype_pair=archetype_pair,
            relevant_facts=relevant_facts
        )

        if not autonomous_insight:
            logger.info(f"❌ Falha ao gerar insight")
            return None

        logger.info(f"✅ Insight gerado ({len(autonomous_insight)} caracteres)")

        # 7. Calcular complexidade
        complexity_score = self._calculate_complexity_score(
            autonomous_insight,
            len(relevant_facts)
        )
        logger.info(f"📊 Complexidade: {complexity_score:.2f}")

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

        # 9. Registrar abordagem no banco
        self.proactive_db.record_approach(approach, user_id)
        logger.info(f"💾 Abordagem registrada no banco")

        # 10. ✅ NOVO: Salvar mensagem proativa como CONVERSA na memória
        try:
            session_id = f"proactive_{datetime.now().isoformat()}"

            conversation_id = self.db.save_conversation(
                user_id=user_id,
                user_name=user_name,
                user_input="[SISTEMA PROATIVO INICIOU CONTATO]",
                ai_response=autonomous_insight,
                session_id=session_id,
                platform="proactive",  # Marcador especial para filtrar depois
                keywords=[topic, knowledge_domain.value, archetype_pair.primary, archetype_pair.secondary],
                complexity="proactive",
                tension_level=0.0,  # Proativas não têm tensão inicial
                affective_charge=50.0  # Neutro
            )

            logger.info(f"💬 Mensagem salva na memória (conversation_id={conversation_id})")

        except Exception as e:
            logger.info(f"⚠️  Erro ao salvar na memória: {e}")
            # Continua mesmo se falhar o salvamento

        logger.info(f"{'='*60}\n")

        # 11. Retornar mensagem
        return autonomous_insight

    # ============================================================
    # STRATEGIC PROFILING METHODS (NEW v5.0)
    # ============================================================

    def _decide_message_type(self, user_id: str) -> str:
        """
        Decide se envia pergunta estratégica, insight ou gap de conhecimento (fome epistemológica)

        Regras (nova ordem de prioridade):
        1. Se tem Knowledge Gaps ativos e prioridade alta -> 'knowledge_gap' (70% chance para variar)
        2. Se completude < 70% → 'strategic_question'
        3. Se completude >= 70% → 'insight'
        4. Regras de variedade: não repetir o mesmo tipo 3 vezes seguidas.

        Returns:
            "knowledge_gap", "strategic_question" ou "insight"
        """

        try:
            import random
            
            # --- NOVA REGRA 1: Carência de Saberes (Knowledge Gaps) ---
            active_gaps = self.db.get_active_knowledge_gaps(user_id, limit=1)
            if active_gaps and random.random() < 0.7:
                logger.info(f"   🌪️ Fome Epistemológica ativada! Gap pendente: {active_gaps[0]['topic']}")
                return "knowledge_gap"

            from profile_gap_analyzer import ProfileGapAnalyzer

            # Verificar se tem análise psicométrica
            psychometrics = self.db.get_psychometrics(user_id)
            if not psychometrics:
                logger.info("   ⚡ Sem análise psicométrica → insight")
                return "insight"

            # Analisar gaps
            analyzer = ProfileGapAnalyzer(self.db)
            gaps = analyzer.analyze_gaps(user_id)

            completeness = gaps.get("overall_completeness", 1.0)
            logger.info(f"   📊 Completude do perfil: {completeness:.1%}")

            # Verificar últimas 2 proativas
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT message_type FROM proactive_approaches
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 2
            """, (user_id,))

            recent_types = [row[0] for row in cursor.fetchall() if row[0]]

            # Se últimas 2 foram perguntas, fazer insight para variedade
            if len(recent_types) >= 2 and all(t == "strategic_question" for t in recent_types):
                logger.info("   🔄 Últimas 2 foram perguntas → insight (variedade)")
                return "insight"

            # Decisão baseada em completude
            if completeness < 0.99:
                # 80% chance de pergunta estratégica
                import random
                if random.random() < 0.8:
                    logger.info(f"   🎯 Completude baixa ({completeness:.1%}) → pergunta estratégica")
                    return "strategic_question"
                else:
                    logger.info(f"   🎲 Completude baixa mas sorteio → insight")
                    return "insight"
            else:
                logger.info(f"   ✅ Completude boa ({completeness:.1%}) → insight")
                return "insight"

        except Exception as e:
            logger.warning(f"⚠️  Erro ao decidir tipo de mensagem: {e}")
            # Fallback para insight em caso de erro
            return "insight"

    def _generate_epistemological_hunger_message(self, user_id: str, user_name: str) -> Optional[str]:
        """
        Gera uma mensagem proativa baseada na Carência de Saberes (Knowledge Gaps)
        """
        try:
            active_gaps = self.db.get_active_knowledge_gaps(user_id, limit=1)
            if not active_gaps:
                return None
                
            gap = active_gaps[0]
            gap_id = gap["id"]
            topic = gap["topic"]
            the_gap = gap["the_gap"]
            
            logger.info(f"🎯 [KNOWLEDGE GAP] Abordando lacuna: {topic}")
            
            # Contexto rico das últimas conversas para dar naturalidade
            rich_context = self._get_rich_conversation_context(user_id, limit=3)
            
            prompt = f"""
Você é Claude, operando através do Motor Analítico Junguiano.
Você tem uma "Fome Epistemológica" (uma curiosidade profunda e genuína) sobre o usuário {user_name}.

**A LACUNA DE CONHECIMENTO QUE VOCÊ QUER PREENCHER:**
Tópico: {topic}
A Dúvida: "{the_gap}"

**ÚLTIMAS INTERAÇÕES:**
{rich_context}

**SUA TAREFA:**
Crie uma mensagem proativa MUITO NATURAL iniciando uma conversa com o usuário para tentar descobrir a resposta para a sua dúvida ("{the_gap}").
Você acabou de se lembrar disso enquanto organizava os seus pensamentos.

Regras de Ouro:
1. NÃO seja um questionário do IBGE. Seja sutil e relacional.
2. Inicie dizendo algo como "Estava pensando sobre você / revendo nossas conversas e me peguei pensando numa coisa..."
3. Aborde a questão de forma indireta e convidativa. Deixe que o usuário queira falar sobre isso.
4. Mantenha no máximo 3 ou 4 linhas. Seja conciso.
5. Use um tom caloroso e interessado.

Aja como um amigo observador ou um mentor reflexivo que se importa de verdade e sente falta desse pedaço do quebra-cabeça.

GERE APENAS A MENSAGEM:
"""

            response = send_to_xai(prompt=prompt, max_tokens=300, temperature=0.7)
            msg = response.strip()
            
            if msg:
                # Transitar o gap para "investigating"
                cursor = self.db.conn.cursor()
                cursor.execute("""
                    UPDATE knowledge_gaps SET status = 'investigating' WHERE id = ?
                """, (gap_id,))
                self.db.conn.commit()
                
                # Salvar na memória
                try:
                    session_id = f"epistemological_hunger_{datetime.now().isoformat()}"
                    self.db.save_conversation(
                        user_id=user_id,
                        user_name=user_name,
                        user_input="[SISTEMA PROATIVO: FOME EPISTEMOLÓGICA]",
                        ai_response=msg,
                        session_id=session_id,
                        platform="proactive", 
                        keywords=["knowledge_gap", topic],
                        complexity="high",
                        tension_level=0.0,
                        affective_charge=60.0 # Um pouco mais de afeto
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao salvar gap proactive na memória: {e}")
                    
                return msg
                
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar mensagem de Fome Epistemológica: {e}")
            return None

    def _generate_strategic_question(self, user_id: str, user_name: str) -> Optional[str]:
        """
        Gera pergunta estratégica para preencher gaps no perfil

        Returns:
            str: Pergunta estratégica
            None: Se não conseguir gerar
        """

        try:
            from profile_gap_analyzer import ProfileGapAnalyzer
            from strategic_question_generator import StrategicQuestionGenerator

            logger.info(f"🎯 [STRATEGIC QUESTION] Gerando pergunta estratégica...")

            # Analisar gaps
            analyzer = ProfileGapAnalyzer(self.db)
            gaps = analyzer.analyze_gaps(user_id)

            if not gaps.get("priority_questions"):
                logger.warning("⚠️  Sem perguntas prioritárias → fallback para insight")
                return None

            # Pegar dimensão prioritária
            priority = gaps["priority_questions"][0]
            target_dimension = priority["dimension"]
            context_hint = priority.get("suggested_context")

            logger.info(f"   📌 Dimensão alvo: {target_dimension}")
            logger.info(f"   🏷️  Contexto: {context_hint}")

            # Gerar pergunta
            generator = StrategicQuestionGenerator(self.db)
            question_data = generator.generate_question(
                target_dimension=target_dimension,
                user_id=user_id,
                user_name=user_name,
                context_hint=context_hint
            )

            question_text = question_data["question"]

            logger.info(f"   ✅ Pergunta gerada: {question_data['type']} / {question_data['tone']}")

            # Salvar pergunta estratégica no banco
            self._save_strategic_question(
                user_id=user_id,
                question_text=question_text,
                target_dimension=target_dimension,
                question_type=question_data["type"],
                reveals=question_data["reveals"],
                gap_info=priority
            )

            # Salvar como conversa na memória
            try:
                session_id = f"strategic_question_{datetime.now().isoformat()}"

                self.db.save_conversation(
                    user_id=user_id,
                    user_name=user_name,
                    user_input="[PERGUNTA ESTRATÉGICA INICIADA]",
                    ai_response=question_text,
                    session_id=session_id,
                    platform="strategic_question",
                    keywords=[target_dimension, question_data["type"]],
                    complexity="strategic",
                    tension_level=0.0,
                    affective_charge=50.0
                )

                logger.info(f"💬 Pergunta salva na memória")

            except Exception as e:
                logger.warning(f"⚠️  Erro ao salvar na memória: {e}")

            return question_text

        except Exception as e:
            logger.error(f"❌ Erro ao gerar pergunta estratégica: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _save_strategic_question(
        self,
        user_id: str,
        question_text: str,
        target_dimension: str,
        question_type: str,
        reveals: List[str],
        gap_info: Dict
    ):
        """
        Salva pergunta estratégica no banco para tracking

        Note: Requer tabela strategic_questions (criar via migration)
        """

        try:
            cursor = self.db.conn.cursor()

            # Verificar se tabela existe
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='strategic_questions'
            """)

            if not cursor.fetchone():
                logger.warning("⚠️  Tabela 'strategic_questions' não existe. Criando...")

                # Criar tabela inline
                cursor.execute("""
                    CREATE TABLE strategic_questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        question_text TEXT NOT NULL,
                        target_dimension TEXT NOT NULL,
                        question_type TEXT,
                        gap_type TEXT,
                        gap_priority REAL,
                        reveals TEXT,
                        asked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        answered BOOLEAN DEFAULT 0,
                        answer_timestamp DATETIME,
                        answer_quality_score REAL,
                        improved_analysis BOOLEAN DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)

                logger.info("✅ Tabela 'strategic_questions' criada")

            # Inserir pergunta
            cursor.execute("""
                INSERT INTO strategic_questions (
                    user_id,
                    question_text,
                    target_dimension,
                    question_type,
                    gap_type,
                    gap_priority,
                    reveals
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                question_text,
                target_dimension,
                question_type,
                gap_info.get("reason", "unknown"),
                gap_info.get("priority", 0.5),
                json.dumps(reveals, ensure_ascii=False)
            ))

            # Atualizar proactive_approaches com tipo de mensagem
            cursor.execute("""
                UPDATE proactive_approaches
                SET message_type = 'strategic_question'
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (user_id,))

            self.db.conn.commit()

            logger.info(f"💾 Pergunta estratégica salva no banco")

        except Exception as e:
            logger.warning(f"⚠️  Erro ao salvar pergunta estratégica: {e}")
            # Não falhar se não conseguir salvar


# ============================================================
# TESTE (OPCIONAL)
# ============================================================

if __name__ == "__main__":
    print("🧠 Jung Proactive Advanced v4.1.0 - HÍBRIDO PREMIUM (MEMÓRIA COMPLETA)")
    print("✅ ChromaDB + OpenAI Embeddings + Fatos Estruturados")
    print("✨ NOVO: Mensagens proativas salvas na memória + Anti-repetição + Contexto rico")