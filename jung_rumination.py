"""
Sistema de Ruminação Cognitiva - Jung Agent
Baseado em SISTEMA_RUMINACAO_v1.md

Implementa processamento profundo de tensões psíquicas através de 5 fases:
1. INGESTÃO: Extrai fragmentos significativos das conversas
2. DETECÇÃO: Identifica tensões entre fragmentos opostos
3. DIGESTÃO: Revisita tensões, atualiza maturidade
4. SÍNTESE: Gera símbolos quando tensão está madura
5. ENTREGA: Envia insights ao usuário via Telegram

Autor: Sistema Jung
Data: 2025-12-04
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3

from rumination_config import *
from rumination_prompts import *

logger = logging.getLogger(__name__)

# ============================================================
# CLASSE PRINCIPAL: RUMINATION ENGINE
# ============================================================

class RuminationEngine:
    """
    Motor de ruminação cognitiva.
    Processa conversas do admin user em busca de tensões profundas.
    """

    def __init__(self, db_manager):
        """
        Args:
            db_manager: Instância de HybridDatabaseManager
        """
        self.db = db_manager
        self.admin_user_id = ADMIN_USER_ID

        # Criar tabelas se não existirem
        self._create_tables()

        logger.info(f"🧠 RuminationEngine inicializado para admin: {self.admin_user_id}")

    def _create_tables(self):
        """Cria tabelas de ruminação no banco"""
        cursor = self.db.conn.cursor()

        # Tabela de fragmentos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rumination_fragments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                fragment_type TEXT NOT NULL,
                content TEXT NOT NULL,
                context TEXT,
                source_conversation_id INTEGER,
                source_quote TEXT,
                emotional_weight REAL DEFAULT 0.5,
                tension_level REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Tabela de tensões
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rumination_tensions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                tension_type TEXT NOT NULL,
                pole_a_content TEXT NOT NULL,
                pole_a_type TEXT,
                pole_a_fragment_ids TEXT,
                pole_b_content TEXT NOT NULL,
                pole_b_type TEXT,
                pole_b_fragment_ids TEXT,
                tension_description TEXT,
                intensity REAL DEFAULT 0.5,
                maturity_score REAL DEFAULT 0.0,
                revisit_count INTEGER DEFAULT 0,
                evidence_count INTEGER DEFAULT 2,
                connected_tension_ids TEXT,
                first_detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_revisited_at DATETIME,
                last_evidence_at DATETIME,
                status TEXT DEFAULT 'open',
                synthesis_symbol TEXT,
                synthesis_question TEXT,
                synthesis_generated_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Tabela de insights
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rumination_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                source_tension_id INTEGER,
                connected_tension_ids TEXT,
                insight_type TEXT DEFAULT 'símbolo',
                symbol_content TEXT,
                question_content TEXT,
                full_message TEXT NOT NULL,
                depth_score REAL DEFAULT 0.5,
                novelty_score REAL DEFAULT 0.5,
                maturation_days INTEGER DEFAULT 0,
                status TEXT DEFAULT 'ready',
                crystallized_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                delivered_at DATETIME,
                user_response_at DATETIME,
                user_engaged BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (source_tension_id) REFERENCES rumination_tensions(id)
            )
        """)

        # Tabela de log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rumination_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                phase TEXT NOT NULL,
                operation TEXT,
                input_summary TEXT,
                output_summary TEXT,
                affected_fragment_ids TEXT,
                affected_tension_ids TEXT,
                affected_insight_ids TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Índices para performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fragments_user ON rumination_fragments(user_id, processed)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tensions_user_status ON rumination_tensions(user_id, status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_insights_user_status ON rumination_insights(user_id, status)")

        self.db.conn.commit()
        logger.info("✅ Tabelas de ruminação criadas/verificadas")

    # ========================================
    # FASE 1: INGESTÃO
    # ========================================

    def ingest(self, conversation_data: Dict) -> List[int]:
        """
        Extrai fragmentos significativos de uma conversa.

        Args:
            conversation_data: {
                'user_id': str,
                'user_input': str,
                'ai_response': str,
                'conversation_id': int,
                'tension_level': float,
                'affective_charge': float
            }

        Returns:
            Lista de IDs de fragmentos criados
        """
        user_id = conversation_data['user_id']

        # Verificar se é admin
        if user_id != self.admin_user_id:
            return []

        # Verificar se conversa tem tensão mínima
        if conversation_data.get('tension_level', 0) < MIN_TENSION_LEVEL:
            logger.debug(f"⏭️  Conversa com tensão baixa ({conversation_data.get('tension_level')}) - pulando ingestão")
            return []

        user_input = conversation_data['user_input']

        # Montar prompt de extração
        prompt = EXTRACTION_PROMPT.format(
            user_input=user_input,
            tension_level=conversation_data.get('tension_level', 0),
            affective_charge=conversation_data.get('affective_charge', 0),
            response_length=len(conversation_data.get('ai_response', ''))
        )

        try:
            # Chamar LLM para extrair fragmentos
            from llm_providers import create_llm_provider

            claude = create_llm_provider("claude")
            response = claude.get_response(prompt, temperature=0.3, max_tokens=1000)

            # Parse JSON
            result = self._parse_json_response(response)

            fragments = result.get('fragments', [])

            if not fragments:
                logger.info("   ℹ️  Nenhum fragmento significativo encontrado")
                return []

            # Salvar fragmentos no banco
            fragment_ids = []
            cursor = self.db.conn.cursor()

            for frag in fragments[:MAX_FRAGMENTS_PER_CONVERSATION]:
                # Verificar peso emocional mínimo
                if frag.get('emotional_weight', 0) < MIN_EMOTIONAL_WEIGHT:
                    continue

                cursor.execute("""
                    INSERT INTO rumination_fragments (
                        user_id, fragment_type, content, context,
                        source_conversation_id, source_quote,
                        emotional_weight, tension_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    frag['type'],
                    frag['content'],
                    frag.get('context', ''),
                    conversation_data['conversation_id'],
                    frag['quote'],
                    frag['emotional_weight'],
                    conversation_data.get('tension_level', 0)
                ))

                fragment_ids.append(cursor.lastrowid)

            self.db.conn.commit()

            logger.info(f"   🧩 {len(fragment_ids)} fragmentos extraídos")

            # Log da operação
            self._log_operation(
                "ingestão",
                user_id,
                input_summary=f"{len(user_input)} chars",
                output_summary=f"{len(fragment_ids)} fragmentos",
                affected_fragment_ids=fragment_ids
            )

            # Disparar detecção de tensões se houver fragmentos novos
            if fragment_ids:
                self.detect_tensions(user_id)

            return fragment_ids

        except Exception as e:
            logger.error(f"❌ Erro na ingestão: {e}")
            return []

    # ========================================
    # FASE 2: DETECÇÃO DE TENSÕES
    # ========================================

    def detect_tensions(self, user_id: str) -> List[int]:
        """
        Analisa fragmentos buscando tensões entre eles.

        Args:
            user_id: ID do usuário

        Returns:
            Lista de IDs de tensões criadas
        """
        if user_id != self.admin_user_id:
            return []

        logger.info(f"⚡ Detectando tensões para {user_id}")

        cursor = self.db.conn.cursor()

        # Buscar fragmentos não processados
        cursor.execute("""
            SELECT id, fragment_type, content, source_quote, emotional_weight
            FROM rumination_fragments
            WHERE user_id = ? AND processed = 0
            ORDER BY created_at DESC
            LIMIT 10
        """, (user_id,))

        recent_fragments = cursor.fetchall()

        if len(recent_fragments) < 2:
            logger.info("   ℹ️  Poucos fragmentos para detectar tensões")
            return []

        # Buscar fragmentos históricos relevantes
        cursor.execute("""
            SELECT id, fragment_type, content, source_quote, emotional_weight
            FROM rumination_fragments
            WHERE user_id = ? AND processed = 1
            ORDER BY created_at DESC
            LIMIT 20
        """, (user_id,))

        historical_fragments = cursor.fetchall()

        # Formatar para o prompt
        recent_text = self._format_fragments_for_prompt(recent_fragments)
        historical_text = self._format_fragments_for_prompt(historical_fragments)

        # Montar prompt
        prompt = DETECTION_PROMPT.format(
            recent_fragments=recent_text,
            historical_fragments=historical_text
        )

        try:
            # Chamar LLM
            from llm_providers import create_llm_provider

            claude = create_llm_provider("claude")
            response = claude.get_response(prompt, temperature=0.4, max_tokens=1500)

            # Parse JSON
            result = self._parse_json_response(response)

            tensions = result.get('tensions', [])

            if not tensions:
                logger.info("   ℹ️  Nenhuma tensão detectada")
                # Marcar fragmentos como processados mesmo assim
                frag_ids = [f[0] for f in recent_fragments]
                cursor.execute(f"""
                    UPDATE rumination_fragments
                    SET processed = 1
                    WHERE id IN ({','.join(['?']*len(frag_ids))})
                """, frag_ids)
                self.db.conn.commit()
                return []

            # Salvar tensões
            tension_ids = []

            for tens in tensions:
                # Verificar intensidade mínima
                if tens.get('intensity', 0) < MIN_INTENSITY_FOR_TENSION:
                    continue

                cursor.execute("""
                    INSERT INTO rumination_tensions (
                        user_id, tension_type,
                        pole_a_content, pole_a_fragment_ids,
                        pole_b_content, pole_b_fragment_ids,
                        tension_description, intensity,
                        evidence_count, last_evidence_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    tens['type'],
                    tens['pole_a']['content'],
                    json.dumps(tens['pole_a']['fragment_ids']),
                    tens['pole_b']['content'],
                    json.dumps(tens['pole_b']['fragment_ids']),
                    tens['description'],
                    tens['intensity'],
                    len(tens['pole_a']['fragment_ids']) + len(tens['pole_b']['fragment_ids']),
                    datetime.now().isoformat()
                ))

                tension_ids.append(cursor.lastrowid)

            # Marcar fragmentos como processados
            all_fragment_ids = set()
            for f in recent_fragments:
                all_fragment_ids.add(f[0])

            if all_fragment_ids:
                cursor.execute(f"""
                    UPDATE rumination_fragments
                    SET processed = 1
                    WHERE id IN ({','.join(['?']*len(all_fragment_ids))})
                """, list(all_fragment_ids))

            self.db.conn.commit()

            logger.info(f"   ⚡ {len(tension_ids)} tensões detectadas")

            # Log
            self._log_operation(
                "detecção",
                user_id,
                input_summary=f"{len(recent_fragments)} fragmentos",
                output_summary=f"{len(tension_ids)} tensões",
                affected_tension_ids=tension_ids
            )

            return tension_ids

        except Exception as e:
            logger.error(f"❌ Erro na detecção: {e}")
            return []

    # ========================================
    # HELPERS INTERNOS
    # ========================================

    def _parse_json_response(self, response: str) -> Dict:
        """Parse robusto de resposta JSON do LLM"""
        import re

        # Remover markdown se houver
        response = response.strip()
        if response.startswith('```'):
            response = re.sub(r'```json\s*', '', response)
            response = re.sub(r'```\s*$', '', response)

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON: {e}")
            logger.error(f"Resposta bruta: {response[:500]}")
            return {}

    def _format_fragments_for_prompt(self, fragments: List[Tuple]) -> str:
        """Formata fragmentos para inclusão em prompt"""
        if not fragments:
            return "(nenhum)"

        lines = []
        for frag in fragments:
            frag_id, frag_type, content, quote, weight = frag
            lines.append(f"[ID {frag_id}] {frag_type.upper()}: {content}")
            lines.append(f"  Evidência: \"{quote}\"")
            lines.append(f"  Peso emocional: {weight:.2f}")
            lines.append("")

        return "\n".join(lines)

    def _log_operation(self, phase: str, user_id: str, **kwargs):
        """Registra operação no log"""
        if not LOG_ALL_PHASES:
            return

        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO rumination_log (
                user_id, phase, operation, input_summary, output_summary,
                affected_fragment_ids, affected_tension_ids, affected_insight_ids
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            phase,
            kwargs.get('operation', ''),
            kwargs.get('input_summary', ''),
            kwargs.get('output_summary', ''),
            json.dumps(kwargs.get('affected_fragment_ids', [])),
            json.dumps(kwargs.get('affected_tension_ids', [])),
            json.dumps(kwargs.get('affected_insight_ids', []))
        ))
        self.db.conn.commit()

    # ========================================
    # FASE 3: DIGESTÃO (Revisita)
    # ========================================

    def digest(self, user_id: str = None) -> Dict:
        """
        Job de digestão - revisita tensões abertas, atualiza maturidade.

        Args:
            user_id: ID do usuário (default: admin)

        Returns:
            Estatísticas da digestão
        """
        if user_id is None:
            user_id = self.admin_user_id

        if user_id != self.admin_user_id:
            return {}

        logger.info(f"🔄 Iniciando digestão para {user_id}")

        cursor = self.db.conn.cursor()

        # Buscar tensões abertas ou amadurecendo
        cursor.execute("""
            SELECT * FROM rumination_tensions
            WHERE user_id = ? AND status IN ('open', 'maturing')
            ORDER BY first_detected_at ASC
        """, (user_id,))

        open_tensions = cursor.fetchall()

        stats = {
            "tensions_processed": 0,
            "matured": 0,
            "archived": 0,
            "ready_for_synthesis": 0
        }

        for tension_row in open_tensions:
            tension = dict(tension_row)
            tension_id = tension['id']

            # 1. Buscar novas evidências desde última revisita
            last_revisit = tension.get('last_revisited_at') or tension['first_detected_at']

            cursor.execute("""
                SELECT id FROM rumination_fragments
                WHERE user_id = ? AND created_at > ?
                ORDER BY created_at DESC
                LIMIT 20
            """, (user_id, last_revisit))

            new_fragments = cursor.fetchall()

            # Verificar se algum fragmento reforça esta tensão
            new_evidence_count = self._count_related_fragments(
                new_fragments,
                tension
            )

            if new_evidence_count > 0:
                tension['evidence_count'] += new_evidence_count
                tension['last_evidence_at'] = datetime.now().isoformat()

            # 2. Calcular maturidade
            maturity = self._calculate_maturity(tension)

            # 3. Atualizar status baseado em maturidade
            days_since_detection = (datetime.now() - datetime.fromisoformat(tension['first_detected_at'])).days
            days_since_evidence = (datetime.now() - datetime.fromisoformat(tension.get('last_evidence_at', tension['first_detected_at']))).days

            new_status = tension['status']

            if maturity >= MIN_MATURITY_FOR_SYNTHESIS and days_since_detection >= MIN_DAYS_FOR_SYNTHESIS:
                new_status = "ready_for_synthesis"
                stats["ready_for_synthesis"] += 1
            elif maturity < 0.2 and days_since_evidence > DAYS_TO_ARCHIVE:
                new_status = "archived"
                stats["archived"] += 1
            else:
                new_status = "maturing"
                stats["matured"] += 1

            # 4. Atualizar tensão no banco
            cursor.execute("""
                UPDATE rumination_tensions
                SET maturity_score = ?,
                    revisit_count = revisit_count + 1,
                    last_revisited_at = ?,
                    status = ?,
                    evidence_count = ?,
                    last_evidence_at = ?
                WHERE id = ?
            """, (
                maturity,
                datetime.now().isoformat(),
                new_status,
                tension['evidence_count'],
                tension.get('last_evidence_at'),
                tension_id
            ))

            stats["tensions_processed"] += 1

        self.db.conn.commit()

        logger.info(f"   ✅ Digestão completa: {stats}")

        # Log
        self._log_operation(
            "digestão",
            user_id,
            output_summary=f"{stats['tensions_processed']} tensões processadas"
        )

        # Verificar sínteses prontas
        self.check_and_synthesize(user_id)

        return stats

    def _calculate_maturity(self, tension: Dict) -> float:
        """
        Calcula score de maturidade de uma tensão.

        Componentes:
        - Tempo desde detecção (25%)
        - Quantidade de evidências (25%)
        - Número de revisitas (15%)
        - Conexões com outras tensões (15%)
        - Intensidade (20%)
        """
        # Tempo
        days_since_detection = (datetime.now() - datetime.fromisoformat(tension['first_detected_at'])).days
        time_factor = min(1.0, days_since_detection / 7.0)  # Máximo em 7 dias

        # Evidências
        evidence_factor = min(1.0, tension['evidence_count'] / 5.0)  # Máximo em 5 evidências

        # Revisitas
        revisit_factor = min(1.0, tension['revisit_count'] / 4.0)  # Máximo em 4 revisitas

        # Conexões (por enquanto sempre 0, implementar depois)
        connection_factor = 0.0

        # Intensidade
        intensity_factor = tension['intensity']

        # Pesos
        maturity = (
            time_factor * MATURITY_WEIGHTS['time'] +
            evidence_factor * MATURITY_WEIGHTS['evidence'] +
            revisit_factor * MATURITY_WEIGHTS['revisit'] +
            connection_factor * MATURITY_WEIGHTS['connection'] +
            intensity_factor * MATURITY_WEIGHTS['intensity']
        )

        return min(1.0, maturity)

    def _count_related_fragments(self, fragments: List, tension: Dict) -> int:
        """Conta quantos fragmentos são relacionados a uma tensão"""
        # Simplificado: conta fragmentos que são do tipo dos polos
        pole_a_ids = json.loads(tension.get('pole_a_fragment_ids', '[]'))
        pole_b_ids = json.loads(tension.get('pole_b_fragment_ids', '[]'))

        # Por enquanto retorna 0 (implementação futura: usar similaridade semântica)
        return 0

    # ========================================
    # FASE 4: SÍNTESE
    # ========================================

    def check_and_synthesize(self, user_id: str = None) -> List[int]:
        """
        Verifica tensões prontas e gera sínteses.

        Args:
            user_id: ID do usuário (default: admin)

        Returns:
            Lista de IDs de insights criados
        """
        if user_id is None:
            user_id = self.admin_user_id

        if user_id != self.admin_user_id:
            return []

        logger.info(f"💎 Verificando sínteses para {user_id}")

        cursor = self.db.conn.cursor()

        # Buscar tensões prontas para síntese
        cursor.execute("""
            SELECT * FROM rumination_tensions
            WHERE user_id = ? AND status = 'ready_for_synthesis'
            ORDER BY maturity_score DESC, intensity DESC
            LIMIT 3
        """, (user_id,))

        ready_tensions = cursor.fetchall()

        if not ready_tensions:
            logger.info("   ℹ️  Nenhuma tensão pronta para síntese")
            return []

        insight_ids = []

        for tension_row in ready_tensions:
            tension = dict(tension_row)

            # Gerar síntese
            insight_id = self._synthesize_tension(tension)

            if insight_id:
                insight_ids.append(insight_id)

                # Atualizar tensão
                cursor.execute("""
                    UPDATE rumination_tensions
                    SET status = 'synthesized',
                        synthesis_generated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), tension['id']))

        self.db.conn.commit()

        logger.info(f"   💎 {len(insight_ids)} insights gerados")

        return insight_ids

    def _synthesize_tension(self, tension: Dict) -> Optional[int]:
        """
        Gera símbolo/insight a partir de tensão madura.

        Args:
            tension: Dict com dados da tensão

        Returns:
            ID do insight criado ou None
        """
        user_id = tension['user_id']

        # Buscar dados do usuário
        user = self.db.get_user(user_id)
        user_name = user.get('user_name', 'Admin')

        # Buscar conversas recentes para contexto
        recent_convs = self.db.get_user_conversations(user_id, limit=5)
        recent_text = "\n\n".join([
            f"Usuário: {c['user_input'][:200]}..."
            for c in recent_convs
        ])

        # Calcular dias de maturação
        days = (datetime.now() - datetime.fromisoformat(tension['first_detected_at'])).days

        # Montar prompt
        prompt = SYNTHESIS_PROMPT.format(
            user_name=user_name,
            days=days,
            evidence_count=tension['evidence_count'],
            tension_type=tension['tension_type'],
            pole_a_content=tension['pole_a_content'],
            pole_b_content=tension['pole_b_content'],
            tension_description=tension['tension_description'],
            intensity=tension['intensity'],
            maturity=tension['maturity_score'],
            connected_info="",  # Por enquanto vazio
            recent_conversations=recent_text
        )

        try:
            # Chamar LLM
            from llm_providers import create_llm_provider

            claude = create_llm_provider("claude")
            response = claude.get_response(prompt, temperature=0.7, max_tokens=800)

            # Parse JSON
            result = self._parse_json_response(response)

            if not result or 'full_message' not in result:
                logger.error("Síntese não retornou mensagem válida")
                return None

            # Validar novidade
            if not self._validate_novelty(result['full_message'], user_id):
                logger.info("   ⏭️  Insight rejeitado por falta de novidade")
                return None

            # Salvar insight
            cursor = self.db.conn.cursor()
            cursor.execute("""
                INSERT INTO rumination_insights (
                    user_id, source_tension_id,
                    symbol_content, question_content, full_message,
                    depth_score, novelty_score, maturation_days,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ready')
            """, (
                user_id,
                tension['id'],
                result.get('symbol', ''),
                result.get('question', ''),
                result['full_message'],
                result.get('depth_score', 0.5),
                result.get('novelty_score', 0.8),
                days
            ))

            insight_id = cursor.lastrowid
            self.db.conn.commit()

            logger.info(f"   💎 Insight {insight_id} criado (depth: {result.get('depth_score', 0)})")

            # Log
            self._log_operation(
                "síntese",
                user_id,
                input_summary=f"tensão {tension['id']}",
                output_summary=f"insight {insight_id}",
                affected_insight_ids=[insight_id]
            )

            return insight_id

        except Exception as e:
            logger.error(f"❌ Erro na síntese: {e}")
            return None

    def _validate_novelty(self, new_message: str, user_id: str) -> bool:
        """
        Valida se insight é novo o suficiente.

        Args:
            new_message: Mensagem do novo insight
            user_id: ID do usuário

        Returns:
            True se é novel, False se é repetitivo
        """
        cursor = self.db.conn.cursor()

        # Buscar insights dos últimos 14 dias
        two_weeks_ago = (datetime.now() - timedelta(days=14)).isoformat()

        cursor.execute("""
            SELECT full_message FROM rumination_insights
            WHERE user_id = ? AND crystallized_at > ?
            ORDER BY crystallized_at DESC
            LIMIT 5
        """, (user_id, two_weeks_ago))

        previous = cursor.fetchall()

        if not previous:
            return True  # Primeiro insight é sempre novel

        previous_text = "\n\n".join([f"- {p[0]}" for p in previous])

        # Prompt de validação
        prompt = NOVELTY_VALIDATION_PROMPT.format(
            new_insight=new_message,
            previous_insights=previous_text
        )

        try:
            from llm_providers import create_llm_provider

            claude = create_llm_provider("claude")
            response = claude.get_response(prompt, temperature=0.3, max_tokens=300)

            result = self._parse_json_response(response)

            novelty_score = result.get('novelty_score', 0.5)

            return novelty_score >= 0.6

        except Exception as e:
            logger.error(f"Erro na validação de novidade: {e}")
            return True  # Em caso de erro, permitir

    # ========================================
    # FASE 5: ENTREGA
    # ========================================

    def check_and_deliver(self, user_id: str = None) -> Optional[int]:
        """
        Verifica condições e entrega insight se apropriado.

        Args:
            user_id: ID do usuário (default: admin)

        Returns:
            ID do insight entregue ou None
        """
        if user_id is None:
            user_id = self.admin_user_id

        if user_id != self.admin_user_id:
            return None

        # Verificar se deve entregar
        if not self._should_deliver(user_id):
            return None

        # Buscar insight pronto
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT * FROM rumination_insights
            WHERE user_id = ? AND status = 'ready'
            ORDER BY depth_score DESC, crystallized_at ASC
            LIMIT 1
        """, (user_id,))

        insight_row = cursor.fetchone()

        if not insight_row:
            return None

        insight = dict(insight_row)

        # Entregar
        return self._deliver_insight(insight)

    def _should_deliver(self, user_id: str) -> bool:
        """Verifica se deve entregar insight agora"""
        user = self.db.get_user(user_id)

        if not user:
            return False

        # 1. Usuário inativo há tempo suficiente?
        last_seen = user.get('last_seen')
        if last_seen:
            hours_inactive = (datetime.now() - datetime.fromisoformat(last_seen)).total_seconds() / 3600
            if hours_inactive < INACTIVITY_THRESHOLD_HOURS:
                return False

        # 2. Cooldown desde última entrega?
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT delivered_at FROM rumination_insights
            WHERE user_id = ? AND status = 'delivered'
            ORDER BY delivered_at DESC
            LIMIT 1
        """, (user_id,))

        last_delivery = cursor.fetchone()

        if last_delivery:
            hours_since = (datetime.now() - datetime.fromisoformat(last_delivery[0])).total_seconds() / 3600
            if hours_since < COOLDOWN_HOURS:
                return False

        # 3. Há insight pronto?
        cursor.execute("""
            SELECT id FROM rumination_insights
            WHERE user_id = ? AND status = 'ready'
            LIMIT 1
        """, (user_id,))

        return cursor.fetchone() is not None

    def _deliver_insight(self, insight: Dict) -> Optional[int]:
        """
        Entrega insight ao usuário via Telegram.

        Args:
            insight: Dict com dados do insight

        Returns:
            ID do insight entregue
        """
        user_id = insight['user_id']
        message = insight['full_message']

        logger.info(f"📤 Entregando insight {insight['id']} para {user_id}")

        try:
            # Enviar via Telegram
            import telegram_bot  # Import dinâmico para evitar circular

            bot = telegram_bot.bot
            if bot:
                bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )

            # Atualizar status
            cursor = self.db.conn.cursor()
            cursor.execute("""
                UPDATE rumination_insights
                SET status = 'delivered',
                    delivered_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), insight['id']))

            # Salvar na memória como conversa proativa
            self.db.save_conversation(
                user_id=user_id,
                user_input="[INSIGHT RUMINADO - SISTEMA PROATIVO]",
                ai_response=message,
                platform="proactive_rumination",
                session_id=f"rumination_{insight['id']}",
                keywords=[
                    f"tensão:{insight.get('source_tension_id')}",
                    f"maturação:{insight.get('maturation_days')}dias"
                ]
            )

            self.db.conn.commit()

            logger.info(f"   ✅ Insight {insight['id']} entregue com sucesso")

            # Log
            self._log_operation(
                "entrega",
                user_id,
                output_summary=f"insight {insight['id']} entregue",
                affected_insight_ids=[insight['id']]
            )

            return insight['id']

        except Exception as e:
            logger.error(f"❌ Erro na entrega: {e}")
            return None

    # ========================================
    # MÉTODOS PÚBLICOS AUXILIARES
    # ========================================

    def get_stats(self, user_id: str = None) -> Dict:
        """Retorna estatísticas do sistema de ruminação"""
        if user_id is None:
            user_id = self.admin_user_id

        cursor = self.db.conn.cursor()

        stats = {}

        # Fragmentos
        cursor.execute("SELECT COUNT(*) FROM rumination_fragments WHERE user_id = ?", (user_id,))
        stats['fragments_total'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM rumination_fragments WHERE user_id = ? AND processed = 0", (user_id,))
        stats['fragments_unprocessed'] = cursor.fetchone()[0]

        # Tensões
        cursor.execute("SELECT COUNT(*) FROM rumination_tensions WHERE user_id = ?", (user_id,))
        stats['tensions_total'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM rumination_tensions WHERE user_id = ? AND status = 'open'", (user_id,))
        stats['tensions_open'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM rumination_tensions WHERE user_id = ? AND status = 'maturing'", (user_id,))
        stats['tensions_maturing'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM rumination_tensions WHERE user_id = ? AND status = 'ready_for_synthesis'", (user_id,))
        stats['tensions_ready'] = cursor.fetchone()[0]

        # Insights
        cursor.execute("SELECT COUNT(*) FROM rumination_insights WHERE user_id = ?", (user_id,))
        stats['insights_total'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM rumination_insights WHERE user_id = ? AND status = 'ready'", (user_id,))
        stats['insights_ready'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM rumination_insights WHERE user_id = ? AND status = 'delivered'", (user_id,))
        stats['insights_delivered'] = cursor.fetchone()[0]

        return stats

    def reset_user_activity(self, user_id: str):
        """Atualiza timestamp de atividade do usuário"""
        # Implementado no jung_core, apenas placeholder
        pass

