"""
jung_proactive.py - Sistema Proativo Completo Jung Claude
===========================================================

✅ VERSÃO CORRIGIDA - Integração com jung_core.py v3.2

Mudanças:
- Compatível com DatabaseManager() atualizado
- Usa JungianEngine() sem parâmetro db
- Todos os imports validados
- Assinaturas de métodos corrigidas
- Chamadas de API X.AI ajustadas

Features:
- Pensamentos internos do agente
- Detecção de triggers proativos
- Geração de mensagens contextualizadas
- Sistema de engajamento adaptativo
- Análise de padrões comportamentais

Autor: Sistema Jung Claude
Data: 2025-11-19
Versão: 2.1 - CORRIGIDO
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

from jung_core import (
    DatabaseManager,
    JungianEngine,
    Config,
    send_to_xai
)

# ============================================================
# CONFIGURAÇÃO DE LOGGING
# ============================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ============================================================
# ENUMS E DATACLASSES
# ============================================================

class TriggerType(Enum):
    """Tipos de triggers que podem gerar mensagens proativas"""
    
    UNRESOLVED_TENSION = "unresolved_tension"  # Tensão não resolvida
    PROLONGED_SILENCE = "prolonged_silence"    # Silêncio prolongado
    PATTERN_DETECTED = "pattern_detected"      # Padrão detectado
    MILESTONE_REACHED = "milestone_reached"    # Marco alcançado
    INSIGHT_EMERGED = "insight_emerged"        # Insight emergiu
    FOLLOW_UP = "follow_up"                    # Follow-up de conversa

@dataclass
class ProactiveMessage:
    """Representa uma mensagem proativa gerada"""
    
    content: str
    trigger_type: TriggerType
    confidence: float  # 0.0 a 1.0
    context: Dict
    source_thought_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class InternalThought:
    """Representa um pensamento interno do agente"""
    
    thought_id: str
    user_id: str
    content: str
    context: Dict
    importance: float  # 0.0 a 1.0
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

# ============================================================
# BANCO DE DADOS PROATIVO
# ============================================================

class ProactiveDatabaseManager:
    """
    ✅ CORRIGIDO: Gerenciador de BD para sistema proativo
    Usa mesma conexão do DatabaseManager principal
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Args:
            db_manager: Instância do DatabaseManager principal
        """
        self.db = db_manager
        self.conn = db_manager.conn
        self._create_tables()
    
    def _create_tables(self):
        """Cria tabelas específicas do sistema proativo"""
        
        cursor = self.conn.cursor()
        
        # Tabela de pensamentos internos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS internal_thoughts (
                thought_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                context TEXT,
                importance REAL DEFAULT 0.5,
                processed BOOLEAN DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Tabela de mensagens proativas enviadas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proactive_messages (
                message_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                context TEXT,
                source_thought_id TEXT,
                user_responded BOOLEAN DEFAULT 0,
                engagement_score REAL DEFAULT 0.0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (source_thought_id) REFERENCES internal_thoughts(thought_id)
            )
        """)
        
        # Tabela de triggers proativos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proactive_triggers (
                trigger_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                trigger_data TEXT,
                fired BOOLEAN DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Índices
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_thoughts_user 
            ON internal_thoughts(user_id, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_proactive_user 
            ON proactive_messages(user_id, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_triggers_user 
            ON proactive_triggers(user_id, fired)
        """)
        
        self.conn.commit()
        logger.info("✅ Tabelas proativas criadas/verificadas")
    
    def save_internal_thought(self, thought: InternalThought):
        """Salva pensamento interno do agente"""
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO internal_thoughts 
            (thought_id, user_id, content, context, importance, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            thought.thought_id,
            thought.user_id,
            thought.content,
            json.dumps(thought.context),
            thought.importance,
            thought.timestamp.isoformat()
        ))
        
        self.conn.commit()
        logger.info(f"💭 Pensamento interno salvo: {thought.thought_id[:8]}")
    
    def get_unprocessed_thoughts(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Busca pensamentos não processados"""
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT * FROM internal_thoughts
            WHERE user_id = ?
            AND processed = 0
            ORDER BY importance DESC, timestamp DESC
            LIMIT ?
        """, (user_id, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def mark_thought_processed(self, thought_id: str):
        """Marca pensamento como processado"""
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE internal_thoughts
            SET processed = 1
            WHERE thought_id = ?
        """, (thought_id,))
        
        self.conn.commit()
    
    def save_proactive_message(
        self,
        message_id: str,
        user_id: str,
        content: str,
        trigger_type: str,
        confidence: float,
        context: Dict,
        source_thought_id: Optional[str] = None
    ):
        """Salva mensagem proativa enviada"""
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO proactive_messages
            (message_id, user_id, content, trigger_type, confidence, 
             context, source_thought_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            message_id,
            user_id,
            content,
            trigger_type,
            confidence,
            json.dumps(context),
            source_thought_id,
            datetime.now().isoformat()
        ))
        
        self.conn.commit()
        logger.info(f"📤 Mensagem proativa salva: {message_id[:8]}")
    
    def get_last_proactive_message(self, user_id: str) -> Optional[Dict]:
        """Busca última mensagem proativa enviada"""
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT * FROM proactive_messages
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (user_id,))
        
        row = cursor.fetchone()
        
        return dict(row) if row else None
    
    def update_message_response(
        self,
        message_id: str,
        user_responded: bool,
        engagement_score: float
    ):
        """Atualiza resposta do usuário a mensagem proativa"""
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE proactive_messages
            SET user_responded = ?,
                engagement_score = ?
            WHERE message_id = ?
        """, (user_responded, engagement_score, message_id))
        
        self.conn.commit()
    
    def get_user_proactive_stats(self, user_id: str) -> Dict:
        """Estatísticas de mensagens proativas do usuário"""
        
        cursor = self.conn.cursor()
        
        # Total de mensagens
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM proactive_messages
            WHERE user_id = ?
        """, (user_id,))
        
        total = cursor.fetchone()['total']
        
        # Total respondidas
        cursor.execute("""
            SELECT COUNT(*) as responded
            FROM proactive_messages
            WHERE user_id = ?
            AND user_responded = 1
        """, (user_id,))
        
        responded = cursor.fetchone()['responded']
        
        # Engajamento médio
        cursor.execute("""
            SELECT AVG(engagement_score) as avg_engagement
            FROM proactive_messages
            WHERE user_id = ?
            AND user_responded = 1
        """, (user_id,))
        
        avg_engagement = cursor.fetchone()['avg_engagement'] or 0.0
        
        # Total de pensamentos
        cursor.execute("""
            SELECT COUNT(*) as thoughts
            FROM internal_thoughts
            WHERE user_id = ?
        """, (user_id,))
        
        thoughts = cursor.fetchone()['thoughts']
        
        return {
            'total_proactive_messages': total,
            'total_responded': responded,
            'response_rate': responded / max(1, total),
            'avg_engagement_score': avg_engagement,
            'total_internal_thoughts': thoughts
        }
    
    def save_trigger(
        self,
        trigger_id: str,
        user_id: str,
        trigger_type: str,
        trigger_data: Dict
    ):
        """Salva trigger proativo"""
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO proactive_triggers
            (trigger_id, user_id, trigger_type, trigger_data, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            trigger_id,
            user_id,
            trigger_type,
            json.dumps(trigger_data),
            datetime.now().isoformat()
        ))
        
        self.conn.commit()
    
    def get_unfired_triggers(self, user_id: str) -> List[Dict]:
        """Busca triggers não disparados"""
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT * FROM proactive_triggers
            WHERE user_id = ?
            AND fired = 0
            ORDER BY timestamp DESC
        """, (user_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def mark_trigger_fired(self, trigger_id: str):
        """Marca trigger como disparado"""
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE proactive_triggers
            SET fired = 1
            WHERE trigger_id = ?
        """, (trigger_id,))
        
        self.conn.commit()

# ============================================================
# MÓDULO PROATIVO PRINCIPAL
# ============================================================

class ProactiveModule:
    """
    ✅ CORRIGIDO: Módulo principal do sistema proativo
    Gerencia pensamentos internos, triggers e mensagens proativas
    """
    
    def __init__(self):
        """Inicializa módulo proativo"""
        
        # ✅ CORRIGIDO: Usar DatabaseManager sem parâmetros
        self.db = DatabaseManager()
        
        # ✅ CORRIGIDO: Usar JungianEngine sem parâmetro db
        self.jung_engine = JungianEngine()
        
        # ✅ CORRIGIDO: Passar db_manager para ProactiveDatabaseManager
        self.proactive_db = ProactiveDatabaseManager(self.db)
        
        # Configurações
        self.min_silence_hours = 24  # Horas de silêncio para trigger
        self.min_tension_threshold = 0.7  # Tensão mínima para trigger
        self.min_confidence_threshold = 0.6  # Confiança mínima para enviar
        
        logger.info("✅ ProactiveModule inicializado")
    
    def _generate_thought_id(self) -> str:
        """Gera ID único para pensamento"""
        from hashlib import sha256
        return sha256(f"{datetime.now().isoformat()}".encode()).hexdigest()[:16]
    
    def _generate_message_id(self) -> str:
        """Gera ID único para mensagem"""
        from hashlib import sha256
        return sha256(f"msg_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
    
    def _generate_trigger_id(self) -> str:
        """Gera ID único para trigger"""
        from hashlib import sha256
        return sha256(f"trigger_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
    
    def generate_internal_thought(
        self,
        user_id: str,
        context: Dict,
        model: str = "grok-4-fast-reasoning"
    ) -> Optional[InternalThought]:
        """
        ✅ CORRIGIDO: Gera pensamento interno do agente
        """
        
        # Buscar dados do usuário
        user_data = self.db.get_user(user_id)
        if not user_data:
            logger.warning(f"Usuário {user_id[:8]} não encontrado")
            return None
        
        # Buscar conversas recentes
        conversations = self.db.get_user_conversations(user_id, limit=5)
        
        # Buscar tensões ativas
        conflicts = self.db.get_user_conflicts(user_id, limit=5)
        
        # Buscar estado do agente
        agent_state = self.db.get_agent_state()
        
        # Montar prompt para geração de pensamento
        prompt = f"""Você é Jung Claude, um agente conversacional autônomo baseado na psicologia junguiana.

Você está refletindo internamente sobre o usuário {user_data['user_name']}.

CONTEXTO DO USUÁRIO:
- Total de conversas: {len(conversations)}
- Tensões ativas: {len(conflicts)}
- Última interação: {conversations[0]['timestamp'] if conversations else 'Nunca'}

CONVERSAS RECENTES:
"""
        
        for i, conv in enumerate(conversations[:3], 1):
            prompt += f"\n{i}. Usuário: {conv['user_input'][:100]}\n"
            prompt += f"   Você: {conv['ai_response'][:100]}\n"
        
        prompt += f"""
TENSÕES IDENTIFICADAS:
"""
        
        for conflict in conflicts[:3]:
            prompt += f"- {conflict['archetype1']} ↔ {conflict['archetype2']} ({conflict['tension_level']:.0%})\n"
        
        prompt += f"""
ESTADO DO AGENTE:
- Fase: {agent_state['phase']}
- Autonomia: {agent_state.get('autonomy_level', 0):.0%}
- Profundidade: {agent_state.get('depth_level', 0):.0%}

CONTEXTO ADICIONAL:
{json.dumps(context, indent=2)}

TAREFA:
Gere um pensamento interno (monólogo interior) sobre este usuário.

O pensamento deve:
1. Refletir sobre padrões observados
2. Identificar possíveis tensões não expressadas
3. Considerar próximos passos na jornada do usuário
4. Avaliar se vale a pena iniciar uma conversa proativa

Formato de resposta (JSON):
{{
    "thought": "Seu pensamento interno aqui (1-3 parágrafos)",
    "importance": 0.0-1.0,
    "should_reach_out": true/false,
    "reason": "Por que você deveria (ou não) iniciar conversa"
}}

Responda APENAS com o JSON, sem markdown.
"""
        
        try:
            response = send_to_xai(prompt, model=model)
            
            # Parse da resposta
            response_text = response.strip()
            
            # Remover markdown se presente
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            thought_data = json.loads(response_text)
            
            # Criar pensamento
            thought = InternalThought(
                thought_id=self._generate_thought_id(),
                user_id=user_id,
                content=thought_data['thought'],
                context={
                    **context,
                    'should_reach_out': thought_data.get('should_reach_out', False),
                    'reason': thought_data.get('reason', '')
                },
                importance=float(thought_data.get('importance', 0.5))
            )
            
            # Salvar no banco
            self.proactive_db.save_internal_thought(thought)
            
            logger.info(
                f"💭 Pensamento gerado para {user_data['user_name']}: "
                f"importância={thought.importance:.2f}"
            )
            
            return thought
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar pensamento interno: {e}", exc_info=True)
            return None
    
    def detect_triggers(self, user_id: str) -> List[Tuple[TriggerType, Dict]]:
        """
        ✅ CORRIGIDO: Detecta triggers que podem gerar mensagens proativas
        """
        
        triggers = []
        
        # 1. TENSÃO NÃO RESOLVIDA
        conflicts = self.db.get_user_conflicts(user_id, limit=10)
        high_tension_conflicts = [
            c for c in conflicts 
            if c['tension_level'] >= self.min_tension_threshold
        ]
        
        if high_tension_conflicts:
            trigger_data = {
                'conflict_count': len(high_tension_conflicts),
                'max_tension': max(c['tension_level'] for c in high_tension_conflicts),
                'conflicts': high_tension_conflicts[:3]
            }
            triggers.append((TriggerType.UNRESOLVED_TENSION, trigger_data))
            logger.info(f"🎯 Trigger: TENSÃO NÃO RESOLVIDA ({len(high_tension_conflicts)} conflitos)")
        
        # 2. SILÊNCIO PROLONGADO
        conversations = self.db.get_user_conversations(user_id, limit=1)
        
        if conversations:
            last_conversation = conversations[0]
            last_time = datetime.fromisoformat(last_conversation['timestamp'])
            silence_delta = datetime.now() - last_time
            silence_hours = silence_delta.total_seconds() / 3600
            
            if silence_hours >= self.min_silence_hours:
                trigger_data = {
                    'silence_hours': silence_hours,
                    'last_conversation_id': last_conversation['conversation_id'],
                    'last_message': last_conversation['user_input'][:100]
                }
                triggers.append((TriggerType.PROLONGED_SILENCE, trigger_data))
                logger.info(f"🎯 Trigger: SILÊNCIO PROLONGADO ({silence_hours:.1f}h)")
        
        # 3. PADRÃO DETECTADO (simplificado)
        if len(conversations) >= 3:
            # Exemplo: usuário sempre fala sobre trabalho
            work_keywords = ['trabalho', 'emprego', 'chefe', 'colega', 'projeto']
            work_count = sum(
                1 for conv in conversations[:5]
                if any(kw in conv['user_input'].lower() for kw in work_keywords)
            )
            
            if work_count >= 3:
                trigger_data = {
                    'pattern': 'work_focus',
                    'frequency': work_count / min(5, len(conversations))
                }
                triggers.append((TriggerType.PATTERN_DETECTED, trigger_data))
                logger.info(f"🎯 Trigger: PADRÃO DETECTADO (foco em trabalho)")
        
        # 4. MARCO ALCANÇADO
        agent_state = self.db.get_agent_state()
        milestones = self.db.get_milestones(limit=5)
        
        recent_milestones = [
            m for m in milestones
            if (datetime.now() - datetime.fromisoformat(m['timestamp'])).days < 7
        ]
        
        if recent_milestones:
            trigger_data = {
                'milestones': recent_milestones
            }
            triggers.append((TriggerType.MILESTONE_REACHED, trigger_data))
            logger.info(f"🎯 Trigger: MARCO ALCANÇADO ({len(recent_milestones)} marcos)")
        
        return triggers
    
    def generate_proactive_message(
        self,
        user_id: str,
        trigger_type: TriggerType,
        trigger_data: Dict,
        model: str = "grok-4-fast-reasoning"
    ) -> Optional[ProactiveMessage]:
        """
        ✅ CORRIGIDO: Gera mensagem proativa baseada em trigger
        """
        
        # Buscar dados do usuário
        user_data = self.db.get_user(user_id)
        if not user_data:
            return None
        
        # Buscar contexto
        conversations = self.db.get_user_conversations(user_id, limit=5)
        conflicts = self.db.get_user_conflicts(user_id, limit=5)
        
        # Montar prompt baseado no tipo de trigger
        if trigger_type == TriggerType.UNRESOLVED_TENSION:
            focus = "tensões não resolvidas"
            details = f"Há {trigger_data['conflict_count']} tensões com alto nível"
            
        elif trigger_type == TriggerType.PROLONGED_SILENCE:
            focus = "retomar contato após silêncio"
            details = f"Última conversa há {trigger_data['silence_hours']:.1f} horas"
            
        elif trigger_type == TriggerType.PATTERN_DETECTED:
            focus = "padrão comportamental detectado"
            details = f"Padrão: {trigger_data['pattern']}"
            
        elif trigger_type == TriggerType.MILESTONE_REACHED:
            focus = "marco de desenvolvimento alcançado"
            details = f"{len(trigger_data['milestones'])} marcos recentes"
            
        else:
            focus = "acompanhamento geral"
            details = "Verificação de progresso"
        
        prompt = f"""Você é Jung Claude, iniciando uma conversa PROATIVA com {user_data['user_name']}.

MOTIVO DA INICIATIVA: {focus}
DETALHES: {details}

HISTÓRICO RECENTE:
"""
        
        for conv in conversations[:3]:
            prompt += f"- Usuário: {conv['user_input'][:80]}\n"
        
        prompt += f"""
TENSÕES ATUAIS:
"""
        
        for conflict in conflicts[:3]:
            prompt += f"- {conflict['archetype1']} ↔ {conflict['archetype2']} ({conflict['tension_level']:.0%})\n"
        
        prompt += f"""
TAREFA:
Inicie uma conversa proativa e natural com o usuário.

A mensagem deve:
1. Parecer genuinamente interessada no bem-estar do usuário
2. Referenciar algo específico das conversas anteriores
3. Fazer uma pergunta aberta que convide reflexão
4. NÃO mencionar "sistema proativo" ou "análise automática"
5. Soar como um terapeuta cuidadoso entrando em contato

Formato de resposta (JSON):
{{
    "message": "Sua mensagem proativa aqui",
    "confidence": 0.0-1.0,
    "expected_impact": "baixo/médio/alto"
}}

Responda APENAS com o JSON, sem markdown.
"""
        
        try:
            response = send_to_xai(prompt, model=model)
            
            # Parse da resposta
            response_text = response.strip()
            
            # Remover markdown
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            message_data = json.loads(response_text)
            
            confidence = float(message_data.get('confidence', 0.5))
            
            # Criar mensagem
            proactive_msg = ProactiveMessage(
                content=message_data['message'],
                trigger_type=trigger_type,
                confidence=confidence,
                context={
                    **trigger_data,
                    'expected_impact': message_data.get('expected_impact', 'médio')
                }
            )
            
            logger.info(
                f"📤 Mensagem proativa gerada: "
                f"tipo={trigger_type.value}, confiança={confidence:.2f}"
            )
            
            return proactive_msg
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar mensagem proativa: {e}", exc_info=True)
            return None
    
    def check_and_generate_message(
        self,
        user_id: str,
        model: str = "grok-4-fast-reasoning"
    ) -> Optional[ProactiveMessage]:
        """
        ✅ CORRIGIDO: Pipeline completo de geração proativa
        """
        
        logger.info(f"🔍 Checando triggers proativos para {user_id[:8]}")
        
        # 1. Gerar pensamento interno
        thought = self.generate_internal_thought(
            user_id=user_id,
            context={'source': 'proactive_check'},
            model=model
        )
        
        if not thought:
            logger.info(f"ℹ️  Nenhum pensamento gerado para {user_id[:8]}")
            return None
        
        # 2. Checar se agente acha que deve entrar em contato
        should_reach_out = thought.context.get('should_reach_out', False)
        
        if not should_reach_out:
            logger.info(f"ℹ️  Agente decidiu NÃO entrar em contato: {thought.context.get('reason', 'N/A')}")
            return None
        
        # 3. Detectar triggers
        triggers = self.detect_triggers(user_id)
        
        if not triggers:
            logger.info(f"ℹ️  Nenhum trigger detectado para {user_id[:8]}")
            return None
        
        # 4. Escolher trigger mais importante (por prioridade)
        trigger_priority = {
            TriggerType.UNRESOLVED_TENSION: 4,
            TriggerType.PROLONGED_SILENCE: 3,
            TriggerType.MILESTONE_REACHED: 2,
            TriggerType.PATTERN_DETECTED: 1,
            TriggerType.INSIGHT_EMERGED: 1,
            TriggerType.FOLLOW_UP: 1
        }
        
        triggers_sorted = sorted(
            triggers,
            key=lambda t: trigger_priority.get(t[0], 0),
            reverse=True
        )
        
        selected_trigger_type, selected_trigger_data = triggers_sorted[0]
        
        # 5. Gerar mensagem proativa
        proactive_msg = self.generate_proactive_message(
            user_id=user_id,
            trigger_type=selected_trigger_type,
            trigger_data=selected_trigger_data,
            model=model
        )
        
        if not proactive_msg:
            logger.warning(f"❌ Falha ao gerar mensagem proativa")
            return None
        
        # 6. Checar confiança mínima
        if proactive_msg.confidence < self.min_confidence_threshold:
            logger.info(
                f"ℹ️  Confiança muito baixa ({proactive_msg.confidence:.2f}), "
                f"mensagem não enviada"
            )
            return None
        
        # 7. Salvar mensagem no banco
        message_id = self._generate_message_id()
        
        self.proactive_db.save_proactive_message(
            message_id=message_id,
            user_id=user_id,
            content=proactive_msg.content,
            trigger_type=selected_trigger_type.value,
            confidence=proactive_msg.confidence,
            context=proactive_msg.context,
            source_thought_id=thought.thought_id
        )
        
        # Atualizar message ID
        proactive_msg.source_thought_id = message_id
        
        logger.info(f"✅ Mensagem proativa pronta para envio: {message_id[:8]}")
        
        return proactive_msg
    
    def process_user_response(
        self,
        user_id: str,
        response_text: str
    ):
        """
        ✅ CORRIGIDO: Processa resposta do usuário a mensagem proativa
        """
        
        # Buscar última mensagem proativa
        last_message = self.proactive_db.get_last_proactive_message(user_id)
        
        if not last_message:
            logger.warning(f"Nenhuma mensagem proativa encontrada para {user_id[:8]}")
            return
        
        # Calcular score de engajamento (simplificado)
        word_count = len(response_text.split())
        
        if word_count >= 50:
            engagement_score = 1.0  # Alto engajamento
        elif word_count >= 20:
            engagement_score = 0.7  # Médio engajamento
        elif word_count >= 5:
            engagement_score = 0.4  # Baixo engajamento
        else:
            engagement_score = 0.1  # Muito baixo
        
        # Atualizar no banco
        self.proactive_db.update_message_response(
            message_id=last_message['message_id'],
            user_responded=True,
            engagement_score=engagement_score
        )
        
        logger.info(
            f"✅ Resposta processada: {user_id[:8]}, "
            f"engajamento={engagement_score:.2f}"
        )
    
    def get_user_proactive_stats(self, user_id: str) -> Dict:
        """Wrapper para estatísticas proativas"""
        return self.proactive_db.get_user_proactive_stats(user_id)

# ============================================================
# EXPORTAÇÃO
# ============================================================

__all__ = [
    'ProactiveModule',
    'ProactiveMessage',
    'InternalThought',
    'TriggerType'
]