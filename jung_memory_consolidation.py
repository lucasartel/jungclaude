"""
jung_memory_consolidation.py - Sistema de Consolidação de Memórias

Responsável por:
- Agrupar memórias similares por período
- Gerar resumos temáticos com LLM
- Criar documentos "consolidated" no ChromaDB
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
import json

logger = logging.getLogger(__name__)


class MemoryConsolidator:
    """
    Consolida memórias similares em resumos temáticos
    """

    def __init__(self, db_manager):
        """
        Args:
            db_manager: HybridDatabaseManager instance
        """
        self.db = db_manager

    def consolidate_user_memories(self, user_id: str, lookback_days: int = 90):
        """
        Consolida memórias de um usuário nos últimos N dias

        Args:
            user_id: ID do usuário
            lookback_days: Período de lookback (default: 90 dias)
        """
        logger.info(f"📦 Iniciando consolidação de memórias para user_id={user_id} (lookback={lookback_days} dias)")

        # 1. Buscar todas as memórias do período
        start_date = datetime.now() - timedelta(days=lookback_days)

        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, user_input, ai_response, timestamp, keywords,
                   tension_level, affective_charge, existential_depth
            FROM conversations
            WHERE user_id = ?
            AND timestamp >= ?
            ORDER BY timestamp ASC
        """, (user_id, start_date.isoformat()))

        memories = [dict(row) for row in cursor.fetchall()]

        if len(memories) < 5:
            logger.info(f"   Menos de 5 memórias encontradas ({len(memories)}), consolidação não necessária")
            return

        logger.info(f"   Encontradas {len(memories)} memórias para consolidar")

        # 2. Agrupar por tópico usando keywords
        clusters = self._cluster_by_topic(memories)

        logger.info(f"   Identificados {len(clusters)} clusters temáticos")

        # 3. Para cada cluster grande (≥5 memórias), gerar resumo
        for topic, cluster_memories in clusters.items():
            if len(cluster_memories) >= 5:
                logger.info(f"   Consolidando cluster '{topic}' ({len(cluster_memories)} memórias)")
                self._create_consolidated_memory(
                    user_id=user_id,
                    topic=topic,
                    memories=cluster_memories,
                    lookback_days=lookback_days
                )

    def _cluster_by_topic(self, memories: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Agrupa memórias por tópico baseado em keywords

        Args:
            memories: Lista de memórias

        Returns:
            Dict {topic: [memórias]}
        """
        clusters = {}

        for memory in memories:
            keywords = memory.get('keywords', '').split(',')

            # Detectar tópico principal
            topic = self._identify_main_topic(keywords)

            if topic not in clusters:
                clusters[topic] = []

            clusters[topic].append(memory)

        return clusters

    def _identify_main_topic(self, keywords: List[str]) -> str:
        """
        Identifica tópico principal baseado em keywords

        Args:
            keywords: Lista de keywords

        Returns:
            Nome do tópico
        """
        if not keywords or not keywords[0]:
            return "geral"

        keywords_lower = [k.lower().strip() for k in keywords if k]

        topic_mapping = {
            "trabalho": ["trabalho", "emprego", "empresa", "carreira", "chefe", "colega"],
            "família": ["esposa", "marido", "filho", "filha", "pai", "mae", "familia"],
            "saúde": ["saude", "doença", "ansiedade", "depressao", "insonia", "terapia"],
            "relacionamento": ["amigo", "namoro", "amor", "relacionamento"],
            "lazer": ["viagem", "hobby", "leitura"],
            "dinheiro": ["dinheiro", "financeiro", "salario", "conta", "divida"],
        }

        for topic, topic_keywords in topic_mapping.items():
            if any(kw in " ".join(keywords_lower) for kw in topic_keywords):
                return topic

        return "geral"

    def _create_consolidated_memory(self, user_id: str, topic: str,
                                    memories: List[Dict], lookback_days: int):
        """
        Cria memória consolidada e salva no ChromaDB

        Args:
            user_id: ID do usuário
            topic: Tópico do cluster
            memories: Memórias do cluster
            lookback_days: Período de lookback
        """
        # Gerar resumo com LLM
        summary = self._generate_summary_with_llm(topic, memories)

        # IDs das conversas originais
        source_ids = [mem['id'] for mem in memories]

        # Calcular métricas agregadas
        avg_tension = sum(m.get('tension_level', 0) for m in memories) / len(memories)
        avg_affective = sum(m.get('affective_charge', 0) for m in memories) / len(memories)
        avg_depth = sum(m.get('existential_depth', 0) for m in memories) / len(memories)

        # Período da consolidação
        timestamps = [datetime.fromisoformat(m['timestamp']) for m in memories]
        period_start = min(timestamps).strftime("%Y-%m-%d")
        period_end = max(timestamps).strftime("%Y-%m-%d")

        # Construir documento consolidado
        doc_content = f"""
=== MEMÓRIA CONSOLIDADA ===
TÓPICO: {topic.upper()}
PERÍODO: {period_start} a {period_end} ({len(memories)} conversas)

{summary}

MÉTRICAS DO PERÍODO:
- Tensão média: {avg_tension:.2f}
- Carga afetiva média: {avg_affective:.2f}
- Profundidade média: {avg_depth:.2f}
"""

        # Metadata
        metadata = {
            "user_id": user_id,
            "user_name": "",  # Will be populated from first memory
            "type": "consolidated",
            "topic": topic,
            "period_start": period_start,
            "period_end": period_end,
            "count": len(memories),
            "source_ids": json.dumps(source_ids),
            "avg_tension": round(avg_tension, 2),
            "avg_affective": round(avg_affective, 2),
            "avg_depth": round(avg_depth, 2),
            "timestamp": datetime.now().isoformat(),
            "recency_tier": "consolidated",  # Tier especial
            "emotional_intensity": round(avg_affective + avg_tension, 2),
            "has_conflicts": False,
            "keywords": topic,
            "topics": topic,
        }

        # Salvar no ChromaDB
        chroma_id = f"consolidated_{user_id}_{topic}_{period_end}"

        from langchain.schema import Document
        doc = Document(page_content=doc_content, metadata=metadata)

        try:
            # Tentar adicionar
            self.db.vectorstore.add_documents([doc], ids=[chroma_id])
            logger.info(f"✅ Memória consolidada criada: {chroma_id}")
        except Exception as e:
            # Se já existe, substituir
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                logger.info(f"   Substituindo memória consolidada existente: {chroma_id}")
                try:
                    self.db.vectorstore.delete([chroma_id])
                    self.db.vectorstore.add_documents([doc], ids=[chroma_id])
                    logger.info(f"✅ Memória consolidada atualizada: {chroma_id}")
                except Exception as delete_error:
                    logger.error(f"❌ Erro ao substituir memória consolidada: {delete_error}")
            else:
                logger.error(f"❌ Erro ao criar memória consolidada: {e}")

    def _generate_summary_with_llm(self, topic: str, memories: List[Dict]) -> str:
        """
        Gera resumo temático das memórias usando LLM

        Args:
            topic: Tópico do cluster
            memories: Lista de memórias

        Returns:
            Resumo gerado
        """
        # Construir prompt com as memórias
        memories_text = "\n\n".join([
            f"[{mem['timestamp'][:10]}] Usuário: {mem['user_input'][:200]}\nJung: {mem['ai_response'][:200]}"
            for mem in memories[:10]  # Limitar a 10 para não estourar tokens
        ])

        prompt = f"""Você é um sistema de consolidação de memórias do Jung.

Analise as {len(memories)} conversas abaixo sobre o tema "{topic}" e gere um RESUMO CONSOLIDADO estruturado:

CONVERSAS:
{memories_text}

Gere um resumo seguindo este formato:

FATOS CONSOLIDADOS:
- [Liste 3-5 fatos principais mencionados repetidamente]

PADRÕES EMOCIONAIS:
- [Descreva padrões emocionais recorrentes, gatilhos, sentimentos]

EVOLUÇÃO:
- [Descreva como o tema evoluiu ao longo do período, se houve mudanças]

Seja conciso mas informativo. Máximo 200 palavras."""

        try:
            if self.db.anthropic_client:
                response = self.db.anthropic_client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                summary = response.content[0].text.strip()
            elif self.db.xai_client:
                response = self.db.xai_client.chat.completions.create(
                    model="grok-beta",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500
                )
                summary = response.choices[0].message.content.strip()
            else:
                # Fallback: resumo manual básico
                summary = f"Consolidação de {len(memories)} conversas sobre {topic}."

            return summary

        except Exception as e:
            logger.error(f"Erro ao gerar resumo com LLM: {e}")
            return f"Consolidação de {len(memories)} conversas sobre {topic}."


def run_consolidation_job(db_manager):
    """
    Job para rodar consolidação em todos os usuários (síncrono)

    Args:
        db_manager: HybridDatabaseManager instance
    """
    logger.info("🔄 Iniciando job de consolidação de memórias")

    consolidator = MemoryConsolidator(db_manager)

    # Buscar todos os usuários
    cursor = db_manager.conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM conversations")
    user_ids = [row[0] for row in cursor.fetchall()]

    logger.info(f"   Consolidando memórias para {len(user_ids)} usuários")

    for user_id in user_ids:
        try:
            consolidator.consolidate_user_memories(user_id, lookback_days=90)
        except Exception as e:
            logger.error(f"Erro ao consolidar memórias de {user_id}: {e}")

    logger.info("✅ Job de consolidação concluído")


async def run_consolidation_job_async(db_manager):
    """
    Versão assíncrona do job de consolidação (para APScheduler AsyncIO)

    Args:
        db_manager: HybridDatabaseManager instance
    """
    import asyncio
    # Executar a versão síncrona em thread separada para não bloquear event loop
    await asyncio.to_thread(run_consolidation_job, db_manager)
