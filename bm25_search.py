"""
bm25_search.py - Busca por palavra-chave (BM25) sobre os logs de sessão

Complementa a busca vetorial do ChromaDB para queries onde a linguagem
varia muito (ex: "firma"/"empresa"/"trabalho") capturando matches exatos
que a busca semântica pode perder.

O índice é construído em memória de forma lazy por usuário e invalidado
quando um novo arquivo de sessão é detectado no dia.
"""

import os
import re
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

SESSIONS_BASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "users"
)

# Cache por user_id: (mtime_str → índice)
_cache: Dict[str, Tuple[str, object, List[Dict]]] = {}


def _sessions_dir(user_id: str) -> str:
    return os.path.join(SESSIONS_BASE, user_id, "sessions")


def _cache_key(user_id: str) -> Optional[str]:
    """Retorna uma chave baseada no mtime do arquivo mais recente da pasta de sessões."""
    sdir = _sessions_dir(user_id)
    if not os.path.isdir(sdir):
        return None
    files = [os.path.join(sdir, f) for f in os.listdir(sdir) if f.endswith(".md")]
    if not files:
        return None
    latest_mtime = max(os.path.getmtime(f) for f in files)
    return f"{len(files)}_{latest_mtime}"


def _load_chunks(user_id: str) -> List[Dict]:
    """
    Carrega todos os arquivos de sessão e os divide em chunks por entrada.
    Cada chunk é um dict com 'date', 'text', 'tokens'.
    """
    sdir = _sessions_dir(user_id)
    if not os.path.isdir(sdir):
        return []

    chunks = []
    for fname in sorted(os.listdir(sdir)):
        if not fname.endswith(".md"):
            continue
        date_str = fname.replace(".md", "")
        fpath = os.path.join(sdir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        # Dividir por bloco de entrada (## HH:MM)
        blocks = re.split(r"\n## \d{2}:\d{2}", content)
        for block in blocks[1:]:  # primeiro bloco é o cabeçalho do dia
            text = re.sub(r"[_*#\[\]`]", " ", block).strip()
            tokens = re.findall(r"[a-záéíóúãõâêôàüçñ]+", text.lower())
            if tokens:
                chunks.append({"date": date_str, "text": text, "tokens": tokens})

    return chunks


def _build_index(user_id: str):
    """Constrói (ou retorna do cache) o índice BM25 para o usuário."""
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        logger.warning("⚠️ rank_bm25 não instalado — busca BM25 desabilitada")
        return None, []

    key = _cache_key(user_id)
    if key and user_id in _cache and _cache[user_id][0] == key:
        _, index, chunks = _cache[user_id]
        return index, chunks

    chunks = _load_chunks(user_id)
    if not chunks:
        return None, []

    corpus = [c["tokens"] for c in chunks]
    index = BM25Okapi(corpus)
    if key:
        _cache[user_id] = (key, index, chunks)

    logger.info(f"📑 BM25: índice construído para {user_id} ({len(chunks)} chunks)")
    return index, chunks


def search(user_id: str, query: str, k: int = 5) -> List[Dict]:
    """
    Busca BM25 nos logs de sessão do usuário.

    Retorna lista de dicts:
        date, text, bm25_score (normalizado 0-1)
    """
    index, chunks = _build_index(user_id)
    if index is None or not chunks:
        return []

    query_tokens = re.findall(r"[a-záéíóúãõâêôàüçñ]+", query.lower())
    if not query_tokens:
        return []

    try:
        scores = index.get_scores(query_tokens)
    except Exception as e:
        logger.warning(f"⚠️ BM25 get_scores falhou: {e}")
        return []

    max_score = max(scores) if max(scores) > 0 else 1.0
    indexed = sorted(
        enumerate(scores), key=lambda x: x[1], reverse=True
    )[:k]

    results = []
    for idx, score in indexed:
        if score <= 0:
            continue
        results.append({
            "date": chunks[idx]["date"],
            "text": chunks[idx]["text"][:400],
            "bm25_score": round(score / max_score, 4),
        })

    return results
