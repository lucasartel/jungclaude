"""
identity_rumination_bridge.py

Bridge Bidirecional: Sistema de Identidade ↔ Sistema de Ruminação

Sincroniza dados entre os dois sistemas:
- Ruminação → Identidade: Tensões maduras viram contradições, insights viram nuclear
- Identidade → Ruminação: Contradições não resolvidas alimentam ruminação

Ambos os sistemas operam apenas com o usuário master admin.
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from identity_config import AGENT_INSTANCE, MIN_CERTAINTY_FOR_NUCLEAR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_database():
    """Encontra o banco de dados automaticamente"""
    possible_paths = [
        Path("/data/jung_hybrid.db"),
        Path("data/jung_hybrid.db"),
        Path("jung_hybrid.db")
    ]

    for path in possible_paths:
        if path.exists():
            return path

    return possible_paths[0]


class IdentityRuminationBridge:
    """
    Ponte bidirecional entre Identidade e Ruminação

    Fluxos:
    1. Tensões de ruminação maduras → Contradições de identidade
    2. Insights de ruminação maduros → Crenças nucleares
    3. Fragmentos recorrentes → Selves possíveis (temidos/perdidos)
    4. Contradições não resolvidas → Novas tensões de ruminação
    """

    def __init__(self, db_connection):
        """
        Args:
            db_connection: Conexão SQLite (HybridDatabaseManager)
        """
        self.db = db_connection

    def sync_mature_tensions_to_contradictions(self) -> int:
        """
        Ruminação → Identidade: Tensões maduras viram contradições

        Busca tensões com maturity_score > 0.6 e ainda não exportadas,
        cria contradições correspondentes no sistema de identidade.

        Returns:
            int: Número de tensões sincronizadas
        """
        cursor = self.db.conn.cursor()

        try:
            # Verificar se tabela de ruminação existe
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='rumination_tensions'
            """)
            if not cursor.fetchone():
                logger.warning("⚠️ Tabela rumination_tensions não existe - pulando sync")
                return 0

            # Buscar tensões maduras não exportadas
            cursor.execute("""
                SELECT id, pole_a, pole_b, tension_type, intensity,
                       first_detected, conversation_id
                FROM rumination_tensions
                WHERE maturity_score > 0.6
                  AND (exported_to_identity_id IS NULL OR exported_to_identity_id = 0)
                  AND status != 'resolved'
            """)

            tensions = cursor.fetchall()

            if not tensions:
                return 0

            logger.info(f"   🔄 Sincronizando {len(tensions)} tensões → contradições")

            synced_count = 0
            for row in tensions:
                tension_id, pole_a, pole_b, tension_type, intensity, first_detected, conv_id = row

                # Criar contradição identitária
                cursor.execute("""
                    INSERT INTO agent_identity_contradictions (
                        agent_instance, pole_a, pole_b, contradiction_type,
                        tension_level, salience, first_detected_at, last_activated_at,
                        supporting_conversation_ids, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                """, (
                    AGENT_INSTANCE,
                    pole_a,
                    pole_b,
                    tension_type,
                    intensity,
                    intensity,  # salience = intensity
                    first_detected,
                    json.dumps([conv_id] if conv_id else []),
                    'unresolved'
                ))

                contradiction_id = cursor.lastrowid

                # Marcar tensão como exportada
                cursor.execute("""
                    UPDATE rumination_tensions
                    SET exported_to_identity_id = ?,
                        exported_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (contradiction_id, tension_id))

                synced_count += 1

            self.db.conn.commit()
            logger.info(f"   ✅ {synced_count} tensões sincronizadas")
            return synced_count

        except Exception as e:
            self.db.conn.rollback()
            logger.error(f"   ❌ Erro ao sincronizar tensões: {e}")
            return 0

    def sync_mature_insights_to_core(self) -> int:
        """
        Ruminação → Identidade: Insights maduros viram crenças nucleares

        Busca insights com synthesis_level = 'symbolic' e ainda não exportados,
        cria atributos nucleares correspondentes.

        Returns:
            int: Número de insights sincronizados
        """
        cursor = self.db.conn.cursor()

        try:
            # Verificar se tabela existe
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='rumination_insights'
            """)
            if not cursor.fetchone():
                logger.warning("⚠️ Tabela rumination_insights não existe - pulando sync")
                return 0

            # Buscar insights maduros não exportados
            cursor.execute("""
                SELECT id, insight_content, symbolic_interpretation,
                       crystallized_at, conversation_id
                FROM rumination_insights
                WHERE synthesis_level = 'symbolic'
                  AND (exported_to_identity_id IS NULL OR exported_to_identity_id = 0)
            """)

            insights = cursor.fetchall()

            if not insights:
                return 0

            logger.info(f"   🔄 Sincronizando {len(insights)} insights → nuclear")

            synced_count = 0
            for row in insights:
                insight_id, content, symbolic, crystallized, conv_id = row

                # Classificar tipo de atributo baseado no conteúdo
                # (simplificado - pode usar LLM para classificação mais precisa)
                attribute_type = self._classify_insight_type(content, symbolic)

                # Usar interpretação simbólica como conteúdo
                nuclear_content = symbolic if symbolic else content

                # Verificar se já existe atributo similar
                cursor.execute("""
                    SELECT id FROM agent_identity_core
                    WHERE agent_instance = ?
                      AND content = ?
                      AND is_current = 1
                """, (AGENT_INSTANCE, nuclear_content))

                if cursor.fetchone():
                    # Já existe - apenas marcar insight como exportado
                    cursor.execute("""
                        UPDATE rumination_insights
                        SET exported_to_identity_id = 0,
                            exported_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (insight_id,))
                    continue

                # Criar novo atributo nuclear
                cursor.execute("""
                    INSERT INTO agent_identity_core (
                        agent_instance, attribute_type, content, certainty,
                        first_crystallized_at, last_reaffirmed_at,
                        supporting_conversation_ids, emerged_in_relation_to
                    ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                """, (
                    AGENT_INSTANCE,
                    attribute_type,
                    nuclear_content,
                    0.75,  # Certainty moderado para insights de ruminação
                    crystallized if crystallized else datetime.now().isoformat(),
                    json.dumps([conv_id] if conv_id else []),
                    'ruminação sobre interações'
                ))

                nuclear_id = cursor.lastrowid

                # Marcar insight como exportado
                cursor.execute("""
                    UPDATE rumination_insights
                    SET exported_to_identity_id = ?,
                        exported_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (nuclear_id, insight_id))

                synced_count += 1

            self.db.conn.commit()
            logger.info(f"   ✅ {synced_count} insights sincronizados")
            return synced_count

        except Exception as e:
            self.db.conn.rollback()
            logger.error(f"   ❌ Erro ao sincronizar insights: {e}")
            return 0

    def sync_fragments_to_possible_selves(self) -> int:
        """
        Ruminação → Identidade: Fragmentos recorrentes viram selves temidos/perdidos

        Busca fragmentos que aparecem 3+ vezes com alta carga emocional,
        cria selves possíveis correspondentes.

        Returns:
            int: Número de fragmentos sincronizados
        """
        cursor = self.db.conn.cursor()

        try:
            # Verificar se tabela existe
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='rumination_fragments'
            """)
            if not cursor.fetchone():
                logger.warning("⚠️ Tabela rumination_fragments não existe - pulando sync")
                return 0

            # Buscar fragmentos recorrentes
            cursor.execute("""
                SELECT fragment_content, AVG(emotional_charge) as avg_charge,
                       fragment_type, MIN(timestamp) as first_occurrence,
                       COUNT(*) as occurrence_count
                FROM rumination_fragments
                WHERE exported_to_identity_id IS NULL OR exported_to_identity_id = 0
                GROUP BY fragment_content
                HAVING COUNT(*) >= 3
                   AND AVG(emotional_charge) > 0.6
            """)

            fragments = cursor.fetchall()

            if not fragments:
                return 0

            logger.info(f"   🔄 Sincronizando {len(fragments)} fragmentos → selves possíveis")

            synced_count = 0
            for row in fragments:
                content, avg_charge, frag_type, first_occurrence, count = row

                # Classificar tipo de self (feared ou lost baseado no tipo de fragmento)
                self_type = 'feared' if avg_charge > 0.75 else 'lost'

                # Verificar se já existe self similar
                cursor.execute("""
                    SELECT id FROM agent_possible_selves
                    WHERE agent_instance = ?
                      AND description = ?
                      AND status = 'active'
                """, (AGENT_INSTANCE, content))

                if cursor.fetchone():
                    # Já existe - marcar fragmentos como exportados
                    cursor.execute("""
                        UPDATE rumination_fragments
                        SET exported_to_identity_id = 0,
                            exported_at = CURRENT_TIMESTAMP
                        WHERE fragment_content = ?
                    """, (content,))
                    continue

                # Criar novo self possível
                vividness = min(0.9, 0.5 + (count * 0.1))  # Aumenta com recorrência

                cursor.execute("""
                    INSERT INTO agent_possible_selves (
                        agent_instance, self_type, description, vividness,
                        likelihood, first_imagined_at, motivational_impact,
                        emotional_valence, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    AGENT_INSTANCE,
                    self_type,
                    content,
                    vividness,
                    avg_charge,  # likelihood baseado em carga emocional
                    first_occurrence,
                    'avoidance',
                    'negative',
                    'active'
                ))

                self_id = cursor.lastrowid

                # Marcar fragmentos como exportados
                cursor.execute("""
                    UPDATE rumination_fragments
                    SET exported_to_identity_id = ?,
                        exported_at = CURRENT_TIMESTAMP
                    WHERE fragment_content = ?
                """, (self_id, content))

                synced_count += 1

            self.db.conn.commit()
            logger.info(f"   ✅ {synced_count} fragmentos sincronizados")
            return synced_count

        except Exception as e:
            self.db.conn.rollback()
            logger.error(f"   ❌ Erro ao sincronizar fragmentos: {e}")
            return 0

    def feed_contradictions_to_rumination(self) -> int:
        """
        Identidade → Ruminação: Contradições não resolvidas alimentam ruminação

        Busca contradições com alta tensão que ainda não foram alimentadas
        para o sistema de ruminação, criando novas tensões.

        Returns:
            int: Número de contradições alimentadas
        """
        cursor = self.db.conn.cursor()

        try:
            # Verificar se tabela de ruminação existe
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='rumination_tensions'
            """)
            if not cursor.fetchone():
                logger.warning("⚠️ Tabela rumination_tensions não existe - pulando feedback")
                return 0

            # Buscar contradições de alta tensão não resolvidas
            cursor.execute("""
                SELECT id, pole_a, pole_b, contradiction_type, tension_level
                FROM agent_identity_contradictions
                WHERE status IN ('unresolved', 'integrating')
                  AND tension_level > 0.7
                  AND last_activated_at > datetime('now', '-7 days')
                  AND (fed_to_rumination = 0 OR fed_to_rumination IS NULL)
            """)

            contradictions = cursor.fetchall()

            if not contradictions:
                return 0

            logger.info(f"   🔄 Alimentando {len(contradictions)} contradições → ruminação")

            fed_count = 0
            for row in contradictions:
                contradiction_id, pole_a, pole_b, contra_type, tension = row

                # Criar nova tensão de ruminação
                cursor.execute("""
                    INSERT INTO rumination_tensions (
                        pole_a, pole_b, tension_type, intensity,
                        first_detected, status, maturity_score
                    ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 'active', 0.0)
                """, (pole_a, pole_b, contra_type, tension))

                # Marcar contradição como alimentada
                cursor.execute("""
                    UPDATE agent_identity_contradictions
                    SET fed_to_rumination = 1
                    WHERE id = ?
                """, (contradiction_id,))

                fed_count += 1

            self.db.conn.commit()
            logger.info(f"   ✅ {fed_count} contradições alimentadas")
            return fed_count

        except Exception as e:
            self.db.conn.rollback()
            logger.error(f"   ❌ Erro ao alimentar contradições: {e}")
            return 0

    def _classify_insight_type(self, content: str, symbolic: Optional[str]) -> str:
        """
        Classifica tipo de atributo nuclear baseado no conteúdo do insight

        Args:
            content: Conteúdo do insight
            symbolic: Interpretação simbólica (se houver)

        Returns:
            str: 'trait', 'value', 'boundary', 'continuity', ou 'role'
        """
        text = (symbolic or content).lower()

        # Heurísticas simples
        if any(word in text for word in ['sempre', 'consistentemente', 'desde']):
            return 'continuity'
        elif any(word in text for word in ['não sou', 'não faço', 'evito']):
            return 'boundary'
        elif any(word in text for word in ['valorizo', 'priorizo', 'importa']):
            return 'value'
        elif any(word in text for word in ['papel', 'função', 'como']):
            return 'role'
        else:
            return 'trait'


async def run_identity_rumination_sync():
    """
    Job de sincronização bidirecional

    Executa todos os fluxos de sincronização:
    1. Tensões → Contradições
    2. Insights → Nuclear
    3. Fragmentos → Selves Possíveis
    4. Contradições → Tensões (feedback)
    """
    logger.info("=" * 70)
    logger.info("🔗 SINCRONIZAÇÃO IDENTIDADE ↔ RUMINAÇÃO")
    logger.info("=" * 70)

    try:
        # Importar aqui para evitar import circular
        from jung_database import HybridDatabaseManager

        # Conectar ao banco
        db_path = find_database()
        if not db_path.exists():
            logger.error(f"❌ Banco de dados não encontrado: {db_path}")
            return

        db = HybridDatabaseManager(str(db_path))
        bridge = IdentityRuminationBridge(db)

        # Executar sincronizações
        logger.info("\n📥 RUMINAÇÃO → IDENTIDADE:")
        tensions_synced = bridge.sync_mature_tensions_to_contradictions()
        insights_synced = bridge.sync_mature_insights_to_core()
        fragments_synced = bridge.sync_fragments_to_possible_selves()

        logger.info("\n📤 IDENTIDADE → RUMINAÇÃO:")
        contradictions_fed = bridge.feed_contradictions_to_rumination()

        # Resumo
        total_synced = tensions_synced + insights_synced + fragments_synced + contradictions_fed

        logger.info("\n" + "=" * 70)
        logger.info("✅ SINCRONIZAÇÃO COMPLETA")
        logger.info(f"   📊 Total de sincronizações: {total_synced}")
        logger.info(f"      • Tensões → Contradições: {tensions_synced}")
        logger.info(f"      • Insights → Nuclear: {insights_synced}")
        logger.info(f"      • Fragmentos → Selves: {fragments_synced}")
        logger.info(f"      • Contradições → Tensões: {contradictions_fed}")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"❌ Erro na sincronização: {e}")
        import traceback
        logger.error(traceback.format_exc())


async def identity_rumination_sync_scheduler():
    """
    Scheduler que roda sincronização a cada 6 horas

    Chamado pelo main.py como background task
    """
    logger.info("🔗 Scheduler de sincronização Identidade↔Ruminação iniciado (a cada 6h)")

    # Aguardar 5 minutos para garantir inicialização completa
    await asyncio.sleep(300)

    while True:
        try:
            await run_identity_rumination_sync()

            # Aguardar próximo ciclo (6 horas)
            logger.info("⏰ Próxima sincronização Identidade↔Ruminação em 6h")
            await asyncio.sleep(6 * 3600)

        except Exception as e:
            logger.error(f"❌ Erro no scheduler de sincronização: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Em caso de erro, aguardar 1 hora e tentar novamente
            await asyncio.sleep(3600)


if __name__ == "__main__":
    # Executar sincronização manualmente
    asyncio.run(run_identity_rumination_sync())
