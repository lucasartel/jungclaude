"""
jung_memory_metrics.py - Sistema de Monitoramento de Qualidade de Memória

Responsável por:
- Calcular cobertura de memórias (% de conversas embedadas)
- Detectar gaps (períodos sem memórias)
- Estatísticas de retrieval semântico
- Relatórios individuais e globais
- Métricas de qualidade do sistema
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)


class MemoryQualityMetrics:
    """
    Calcula métricas de qualidade do sistema de memória
    """

    def __init__(self, db_manager):
        """
        Args:
            db_manager: HybridDatabaseManager instance
        """
        self.db = db_manager

    def calculate_coverage(self, user_id: str) -> Dict:
        """
        Calcula % de conversas que estão embedadas no ChromaDB

        Args:
            user_id: ID do usuário

        Returns:
            Dict com {
                "total_conversations": int,
                "embedded_conversations": int,
                "coverage_percentage": float
            }
        """
        logger.info(f"📊 Calculando cobertura de memória para user_id={user_id}")

        # Total de conversas no SQLite
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM conversations WHERE user_id = ?
        """, (user_id,))
        total_conversations = cursor.fetchone()[0]

        if total_conversations == 0:
            return {
                "total_conversations": 0,
                "embedded_conversations": 0,
                "coverage_percentage": 0.0
            }

        # Conversas no ChromaDB
        embedded_conversations = 0
        if self.db.chroma_enabled:
            try:
                # Buscar todos os docs do usuário (exceto consolidados)
                results = self.db.vectorstore._collection.get(
                    where={
                        "$and": [
                            {"user_id": {"$eq": user_id}},
                            {"type": {"$ne": "consolidated"}}
                        ]
                    }
                )
                embedded_conversations = len(results.get('ids', []))
            except Exception as e:
                logger.warning(f"Erro ao contar docs no ChromaDB: {e}")

        coverage = (embedded_conversations / total_conversations) * 100 if total_conversations > 0 else 0.0

        return {
            "total_conversations": total_conversations,
            "embedded_conversations": embedded_conversations,
            "coverage_percentage": round(coverage, 2)
        }

    def detect_memory_gaps(self, user_id: str, gap_threshold_days: int = 7) -> List[Dict]:
        """
        Detecta períodos sem memórias (gaps)

        Args:
            user_id: ID do usuário
            gap_threshold_days: Mínimo de dias para considerar gap (default: 7)

        Returns:
            Lista de gaps: [
                {"start": "2025-01-01", "end": "2025-01-10", "days": 10},
                ...
            ]
        """
        logger.info(f"🔍 Detectando gaps de memória para user_id={user_id} (threshold={gap_threshold_days} dias)")

        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT timestamp
            FROM conversations
            WHERE user_id = ?
            ORDER BY timestamp ASC
        """, (user_id,))

        timestamps = [datetime.fromisoformat(row[0]) for row in cursor.fetchall()]

        if len(timestamps) < 2:
            return []

        gaps = []
        for i in range(1, len(timestamps)):
            prev_timestamp = timestamps[i - 1]
            curr_timestamp = timestamps[i]

            gap_days = (curr_timestamp - prev_timestamp).days

            if gap_days >= gap_threshold_days:
                gaps.append({
                    "start": prev_timestamp.strftime("%Y-%m-%d"),
                    "end": curr_timestamp.strftime("%Y-%m-%d"),
                    "days": gap_days
                })

        return gaps

    def calculate_retrieval_stats(self, user_id: str) -> Dict:
        """
        Calcula estatísticas de retrieval semântico

        Args:
            user_id: ID do usuário

        Returns:
            Dict com {
                "total_searches": int,  # Estimado
                "avg_memories_retrieved": float,
                "avg_consolidated_in_results": float,
                "avg_semantic_score": float,
                "top_topics": List[str]
            }
        """
        logger.info(f"📈 Calculando estatísticas de retrieval para user_id={user_id}")

        # Como não temos log de buscas, vamos fazer uma busca de teste
        # para simular estatísticas

        if not self.db.chroma_enabled:
            return {
                "error": "ChromaDB desabilitado",
                "avg_memories_retrieved": 0,
                "avg_consolidated_in_results": 0,
                "avg_semantic_score": 0.0,
                "top_topics": []
            }

        try:
            # Fazer uma busca genérica para ter amostra
            test_results = self.db.semantic_search(
                user_id=user_id,
                query="vida trabalho família",
                k=None,  # Adaptive
                chat_history=[]
            )

            avg_memories = len(test_results)
            consolidated_count = sum(1 for m in test_results if m.get('metadata', {}).get('type') == 'consolidated')
            avg_score = sum(m.get('final_score', 0) for m in test_results) / len(test_results) if test_results else 0.0

            # Extrair tópicos mais comuns
            topics = []
            for mem in test_results:
                topic = mem.get('metadata', {}).get('topics', '')
                if topic:
                    topics.extend(topic.split(','))

            from collections import Counter
            topic_counter = Counter([t.strip() for t in topics if t.strip()])
            top_topics = [topic for topic, _ in topic_counter.most_common(5)]

            return {
                "avg_memories_retrieved": avg_memories,
                "avg_consolidated_in_results": consolidated_count,
                "avg_semantic_score": round(avg_score, 3),
                "top_topics": top_topics
            }

        except Exception as e:
            logger.error(f"Erro ao calcular retrieval stats: {e}")
            return {
                "error": str(e),
                "avg_memories_retrieved": 0,
                "avg_consolidated_in_results": 0,
                "avg_semantic_score": 0.0,
                "top_topics": []
            }

    def generate_user_report(self, user_id: str) -> str:
        """
        Gera relatório completo de métricas do usuário

        Args:
            user_id: ID do usuário

        Returns:
            Relatório formatado em texto
        """
        logger.info(f"📋 Gerando relatório de memória para user_id={user_id}")

        # Buscar nome do usuário
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT user_name FROM conversations WHERE user_id = ? LIMIT 1
        """, (user_id,))
        row = cursor.fetchone()
        user_name = row[0] if row else "Desconhecido"

        # Calcular métricas
        coverage = self.calculate_coverage(user_id)
        gaps = self.detect_memory_gaps(user_id, gap_threshold_days=7)
        retrieval_stats = self.calculate_retrieval_stats(user_id)

        # Montar relatório
        report = f"""
=== MEMORY QUALITY REPORT ===
User: {user_name} ({user_id[:12]}...)
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

─────────────────────────────────────────────
📊 COBERTURA DE MEMÓRIA
─────────────────────────────────────────────
Total de conversas: {coverage['total_conversations']}
Conversas embedadas: {coverage['embedded_conversations']}
Cobertura: {coverage['coverage_percentage']}%

{"✅ Excelente cobertura!" if coverage['coverage_percentage'] >= 95 else "⚠️ Cobertura abaixo do ideal (ideal: ≥95%)" if coverage['coverage_percentage'] >= 80 else "❌ Cobertura crítica!"}

─────────────────────────────────────────────
🔍 GAPS DETECTADOS (períodos sem memórias)
─────────────────────────────────────────────
"""

        if gaps:
            report += f"Total de gaps encontrados: {len(gaps)}\n\n"
            for i, gap in enumerate(gaps[:5], 1):  # Limitar a 5 para não poluir
                report += f"{i}. {gap['start']} → {gap['end']} ({gap['days']} dias)\n"
            if len(gaps) > 5:
                report += f"... e mais {len(gaps) - 5} gaps\n"
        else:
            report += "✅ Nenhum gap detectado (threshold: 7 dias)\n"

        report += f"""
─────────────────────────────────────────────
📈 ESTATÍSTICAS DE RETRIEVAL
─────────────────────────────────────────────
Memórias recuperadas (média): {retrieval_stats.get('avg_memories_retrieved', 0)}
Memórias consolidadas (média): {retrieval_stats.get('avg_consolidated_in_results', 0)}
Score semântico (média): {retrieval_stats.get('avg_semantic_score', 0.0):.3f}

Tópicos mais frequentes:
"""

        if retrieval_stats.get('top_topics'):
            for topic in retrieval_stats['top_topics']:
                report += f"  • {topic}\n"
        else:
            report += "  (nenhum tópico identificado)\n"

        report += """
─────────────────────────────────────────────
"""

        return report

    def generate_system_metrics(self) -> Dict:
        """
        Gera métricas globais do sistema

        Returns:
            Dict com estatísticas globais
        """
        logger.info("🌍 Gerando métricas globais do sistema")

        cursor = self.db.conn.cursor()

        # Total de usuários
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM conversations")
        total_users = cursor.fetchone()[0]

        # Total de conversas
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_conversations = cursor.fetchone()[0]

        # Conversas nos últimos 30 dias
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        cursor.execute("""
            SELECT COUNT(*) FROM conversations WHERE timestamp >= ?
        """, (thirty_days_ago,))
        recent_conversations = cursor.fetchone()[0]

        # Total de fatos (V2)
        try:
            cursor.execute("SELECT COUNT(*) FROM user_facts_v2 WHERE is_current = 1")
            total_facts = cursor.fetchone()[0]
        except Exception:
            total_facts = 0

        # Métricas do ChromaDB
        chroma_metrics = {
            "total_documents": 0,
            "consolidated_memories": 0,
            "global_coverage": 0.0
        }

        if self.db.chroma_enabled:
            try:
                # Total de docs
                all_docs = self.db.vectorstore._collection.get()
                total_docs = len(all_docs.get('ids', []))

                # Docs consolidados
                consolidated_docs = self.db.vectorstore._collection.get(
                    where={"type": {"$eq": "consolidated"}}
                )
                consolidated_count = len(consolidated_docs.get('ids', []))

                # Cobertura global
                embedded_conversations = total_docs - consolidated_count
                global_coverage = (embedded_conversations / total_conversations) * 100 if total_conversations > 0 else 0.0

                chroma_metrics = {
                    "total_documents": total_docs,
                    "consolidated_memories": consolidated_count,
                    "global_coverage": round(global_coverage, 2)
                }

            except Exception as e:
                logger.warning(f"Erro ao buscar métricas do ChromaDB: {e}")

        # Usuários mais ativos (top 5)
        cursor.execute("""
            SELECT user_id, user_name, COUNT(*) as conversation_count
            FROM conversations
            GROUP BY user_id
            ORDER BY conversation_count DESC
            LIMIT 5
        """)

        top_users = [
            {
                "user_id": row[0],  # ID completo
                "user_id_display": row[0][:12] + "...",  # ID truncado para display
                "user_name": row[1],
                "conversation_count": row[2]
            }
            for row in cursor.fetchall()
        ]

        return {
            "timestamp": datetime.now().isoformat(),
            "users": {
                "total_users": total_users,
                "top_active_users": top_users
            },
            "conversations": {
                "total_conversations": total_conversations,
                "recent_conversations_30d": recent_conversations
            },
            "facts": {
                "total_facts": total_facts
            },
            "chromadb": chroma_metrics,
            "health_status": self._calculate_health_status(chroma_metrics['global_coverage'])
        }

    def _calculate_health_status(self, coverage: float) -> str:
        """
        Determina status de saúde do sistema baseado na cobertura

        Args:
            coverage: % de cobertura global

        Returns:
            Status: "excellent", "good", "warning", "critical"
        """
        if coverage >= 95:
            return "excellent"
        elif coverage >= 85:
            return "good"
        elif coverage >= 70:
            return "warning"
        else:
            return "critical"


def generate_formatted_system_report(db_manager) -> str:
    """
    Gera relatório global formatado do sistema

    Args:
        db_manager: HybridDatabaseManager instance

    Returns:
        Relatório formatado em texto
    """
    metrics = MemoryQualityMetrics(db_manager)
    system_metrics = metrics.generate_system_metrics()

    health_emoji = {
        "excellent": "✅",
        "good": "🟢",
        "warning": "⚠️",
        "critical": "❌"
    }

    report = f"""
╔══════════════════════════════════════════════════════════╗
║         JUNG MEMORY SYSTEM - GLOBAL METRICS              ║
╚══════════════════════════════════════════════════════════╝

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

─────────────────────────────────────────────
👥 USERS
─────────────────────────────────────────────
Total Users: {system_metrics['users']['total_users']}

Top 5 Active Users:
"""

    for i, user in enumerate(system_metrics['users']['top_active_users'], 1):
        report += f"  {i}. {user['user_name']} - {user['conversation_count']} conversations\n"

    report += f"""
─────────────────────────────────────────────
💬 CONVERSATIONS
─────────────────────────────────────────────
Total Conversations: {system_metrics['conversations']['total_conversations']}
Recent (30 days): {system_metrics['conversations']['recent_conversations_30d']}

─────────────────────────────────────────────
🧠 MEMORY SYSTEM
─────────────────────────────────────────────
Total Facts (V2): {system_metrics['facts']['total_facts']}

ChromaDB:
  • Total Documents: {system_metrics['chromadb']['total_documents']}
  • Consolidated Memories: {system_metrics['chromadb']['consolidated_memories']}
  • Global Coverage: {system_metrics['chromadb']['global_coverage']}%

─────────────────────────────────────────────
🏥 HEALTH STATUS
─────────────────────────────────────────────
Status: {health_emoji.get(system_metrics['health_status'], '❓')} {system_metrics['health_status'].upper()}

"""

    if system_metrics['health_status'] == 'excellent':
        report += "✅ Sistema de memória operando perfeitamente!\n"
    elif system_metrics['health_status'] == 'good':
        report += "🟢 Sistema de memória em boas condições.\n"
    elif system_metrics['health_status'] == 'warning':
        report += "⚠️ Atenção: Cobertura abaixo do ideal. Investigar gaps.\n"
    else:
        report += "❌ CRÍTICO: Cobertura muito baixa! Verificar sistema de embedding.\n"

    report += """
─────────────────────────────────────────────
"""

    return report
