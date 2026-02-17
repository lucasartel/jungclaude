"""
mem0_memory_adapter.py - Adaptador de Memória via mem0

Substitui:
- build_rich_context()       → get_context()
- _search_relevant_facts()   → get_context()
- flush_if_needed()          → não necessário (sem limite de janela)
- llm_fact_extractor.py      → mem0 extrai fatos automaticamente
- correction_detector.py     → mem0 deduplica automaticamente
- ChromaDB + BM25             → mem0.search() via pgvector

O que permanece inalterado:
- jung_rumination.py
- agent_identity_consolidation_job.py
- fragment_detector.py / irt_engine.py
- SQLite (fonte de verdade para jobs internos)

Configuração via variáveis de ambiente:
    DATABASE_URL         → PostgreSQL Railway (obrigatório)
    MEM0_LLM_PROVIDER    → "openai" (default)
    MEM0_LLM_MODEL       → "openai/gpt-4o-mini" (default)
    MEM0_LLM_BASE_URL    → "https://openrouter.ai/api/v1" (default)
    OPENROUTER_API_KEY   → chave do OpenRouter (já existe no projeto)
"""

import os
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


def _ensure_pgvector(database_url: str) -> None:
    """
    Cria a extensão pgvector no PostgreSQL se ainda não existir.
    Roda automaticamente antes de inicializar o mem0 — elimina a necessidade
    de executar o comando manualmente no Railway.
    """
    try:
        import psycopg2
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.close()
        conn.close()
        logger.info("✅ [MEM0] Extensão pgvector garantida no PostgreSQL")
    except Exception as e:
        logger.warning(f"⚠️ [MEM0] Não foi possível criar extensão vector: {e} (pode já existir ou requerer permissão de superuser)")


def _build_mem0_config() -> dict:
    """
    Constrói configuração do mem0 a partir de variáveis de ambiente.

    Usa PostgreSQL/pgvector como vector store (persistente no Railway).
    Usa OpenRouter como LLM para extração de fatos.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL não configurado — necessário para mem0 + pgvector")

    # Parsear DATABASE_URL: postgresql://user:pass@host:port/dbname
    # Formato Railway: postgresql://postgres:pass@host.railway.internal:5432/railway
    import urllib.parse
    parsed = urllib.parse.urlparse(database_url)

    llm_provider = os.getenv("MEM0_LLM_PROVIDER", "openai")
    llm_model = os.getenv("MEM0_LLM_MODEL", "openai/gpt-4o-mini")
    llm_base_url = os.getenv("MEM0_LLM_BASE_URL", "https://openrouter.ai/api/v1")
    llm_api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")

    config = {
        "vector_store": {
            "provider": "pgvector",
            "config": {
                "dbname": parsed.path.lstrip("/"),
                "user": parsed.username,
                "password": parsed.password,
                "host": parsed.hostname,
                "port": parsed.port or 5432,
            },
        },
        "llm": {
            "provider": llm_provider,
            "config": {
                "model": llm_model,
                "api_key": llm_api_key,
                "openai_base_url": llm_base_url,
            },
        },
        "embedder": {
            "provider": llm_provider,
            "config": {
                "model": "text-embedding-3-small",
                "api_key": llm_api_key,
                "openai_base_url": llm_base_url,
            },
        },
    }

    return config


class Mem0MemoryAdapter:
    """
    Interface unificada entre jung_core.py e mem0.

    Substitui: build_rich_context(), _search_relevant_facts(),
               flush_if_needed(), _save_fact_v2(), LLMFactExtractor.
    """

    def __init__(self):
        from mem0 import Memory
        database_url = os.getenv("DATABASE_URL")
        _ensure_pgvector(database_url)  # garante extensão antes de inicializar
        config = _build_mem0_config()
        self.mem = Memory.from_config(config)
        logger.info("✅ [MEM0] Adaptador inicializado (PostgreSQL + pgvector)")

    # ------------------------------------------------------------------
    # Recuperação de contexto (substitui build_rich_context)
    # ------------------------------------------------------------------

    def get_context(self, user_id: str, query: str, limit: int = 5) -> str:
        """
        Retorna contexto formatado para injeção no system prompt.
        Substitui build_rich_context().

        Args:
            user_id: ID do usuário
            query: Input atual do usuário (usado para busca semântica)
            limit: Número máximo de memórias a recuperar

        Returns:
            str: Bloco de texto formatado com memórias relevantes
        """
        try:
            results = self.mem.search(query=query, user_id=user_id, limit=limit)
            memories = results.get("results", []) if isinstance(results, dict) else results

            if not memories:
                return ""

            lines = ["[Memórias relevantes sobre o usuário:]"]
            for m in memories:
                memory_text = m.get("memory", "") if isinstance(m, dict) else str(m)
                if memory_text:
                    lines.append(f"- {memory_text}")

            context = "\n".join(lines)
            logger.info(f"✅ [MEM0] Contexto recuperado: {len(context)} chars ({len(memories)} memórias)")
            return context

        except Exception as e:
            logger.warning(f"⚠️ [MEM0] Erro ao recuperar contexto: {e}")
            return ""

    # ------------------------------------------------------------------
    # Persistência de troca (substitui save_conversation + fact_extractor)
    # ------------------------------------------------------------------

    def add_exchange(self, user_id: str, user_input: str, ai_response: str) -> None:
        """
        Persiste um par (usuário, assistente) no mem0.
        mem0 extrai fatos automaticamente via LLM interno.

        Args:
            user_id: ID do usuário
            user_input: Mensagem do usuário
            ai_response: Resposta do agente
        """
        try:
            messages = [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": ai_response},
            ]
            result = self.mem.add(messages=messages, user_id=user_id)

            # Contar fatos extraídos para log
            n_added = 0
            if isinstance(result, dict):
                added = result.get("results", [])
                n_added = sum(1 for r in added if r.get("event") == "ADD")

            logger.info(f"✅ [MEM0] Troca persistida (user={user_id[:8]}, ~{n_added} fatos extraídos)")

        except Exception as e:
            logger.warning(f"⚠️ [MEM0] Erro ao persistir troca: {e}")

    # ------------------------------------------------------------------
    # Fatos do usuário (para context builder e consolidação de identidade)
    # ------------------------------------------------------------------

    def get_all_facts(self, user_id: str) -> str:
        """
        Retorna todos os fatos persistentes do usuário como texto.
        Útil para context builders e consolidação de identidade.

        Returns:
            str: Lista de fatos formatados, ou string vazia
        """
        try:
            all_memories = self.mem.get_all(user_id=user_id)
            memories = all_memories.get("results", []) if isinstance(all_memories, dict) else all_memories

            if not memories:
                return ""

            lines = [f"- {m.get('memory', '')}" for m in memories if m.get("memory")]
            return "\n".join(lines)

        except Exception as e:
            logger.warning(f"⚠️ [MEM0] Erro ao recuperar todos os fatos: {e}")
            return ""

    # ------------------------------------------------------------------
    # Saúde / diagnóstico
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verifica se mem0 está operacional."""
        try:
            self.mem.get_all(user_id="__health_check__")
            return True
        except Exception:
            return False


def create_mem0_adapter() -> Optional[Mem0MemoryAdapter]:
    """
    Factory: cria Mem0MemoryAdapter se DATABASE_URL estiver configurado.
    Retorna None em caso de falha (fallback SQLite ativo).
    """
    if not os.getenv("DATABASE_URL"):
        logger.info("ℹ️ [MEM0] DATABASE_URL ausente — usando sistema SQLite existente")
        return None

    try:
        return Mem0MemoryAdapter()
    except ImportError:
        logger.warning("⚠️ [MEM0] mem0ai não instalado (pip install mem0ai) — usando SQLite")
        return None
    except Exception as e:
        logger.warning(f"⚠️ [MEM0] Falha ao inicializar: {e} — fallback SQLite ativo")
        return None
