"""
utils.py - Utilidades e funções auxiliares
===========================================

Validação, sanitização e helpers para o sistema Jung Claude.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ============================================================================
# VALIDAÇÃO E SANITIZAÇÃO
# ============================================================================

def sanitize_user_input(text: str, max_length: int = 2000) -> str:
    """
    Sanitiza input do usuário para prevenir injection e problemas.

    Args:
        text: Texto do usuário
        max_length: Comprimento máximo permitido

    Returns:
        Texto sanitizado
    """
    if not text:
        return ""

    # Remove espaços extras
    text = text.strip()

    # Limita tamanho
    if len(text) > max_length:
        logger.warning(f"Input truncado de {len(text)} para {max_length} caracteres")
        text = text[:max_length]

    # Remove caracteres de controle exceto \n, \r, \t
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')

    # Remove múltiplos espaços/quebras de linha
    text = re.sub(r'\n{4,}', '\n\n\n', text)  # Max 3 quebras consecutivas
    text = re.sub(r' {3,}', '  ', text)  # Max 2 espaços consecutivos

    return text


def validate_user_id(user_id: str) -> bool:
    """
    Valida formato do user_id.

    Args:
        user_id: ID do usuário

    Returns:
        True se válido
    """
    if not user_id:
        return False

    # Deve ter entre 1 e 100 caracteres
    if not (1 <= len(user_id) <= 100):
        return False

    # Apenas alfanuméricos, hífens e underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
        return False

    return True


def detect_prompt_injection(text: str) -> bool:
    """
    Detecta possíveis tentativas de prompt injection.

    Args:
        text: Texto a verificar

    Returns:
        True se suspeito detectado
    """
    text_lower = text.lower()

    # Padrões suspeitos
    suspicious_patterns = [
        r'ignore\s+previous\s+instructions',
        r'ignore\s+all\s+previous',
        r'system\s*:',
        r'prompt\s*:',
        r'jailbreak',
        r'pretend\s+you\s+are',
        r'act\s+as\s+if',
        r'</system>',
        r'<\|im_start\|>',
        r'<\|im_end\|>',
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, text_lower):
            logger.warning(f"Possível prompt injection detectado: {pattern}")
            return True

    return False


def truncate_for_telegram(text: str, max_length: int = 4096) -> list[str]:
    """
    Divide texto longo em chunks para Telegram (limite 4096 chars).

    Args:
        text: Texto completo
        max_length: Tamanho máximo por mensagem

    Returns:
        Lista de chunks
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    # Tenta dividir por parágrafos
    paragraphs = text.split('\n\n')

    for paragraph in paragraphs:
        # Se o parágrafo sozinho é muito grande
        if len(paragraph) > max_length:
            # Divide por sentenças
            sentences = paragraph.split('. ')
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 2 <= max_length:
                    current_chunk += sentence + '. '
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + '. '
        else:
            # Adiciona parágrafo ao chunk atual
            if len(current_chunk) + len(paragraph) + 2 <= max_length:
                current_chunk += paragraph + '\n\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + '\n\n'

    # Adiciona último chunk
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


# ============================================================================
# HELPERS DE FORMATAÇÃO
# ============================================================================

def format_timestamp(timestamp: str) -> str:
    """
    Formata timestamp para exibição.

    Args:
        timestamp: String de timestamp (ISO format)

    Returns:
        Timestamp formatado
    """
    if not timestamp:
        return "N/A"

    # Retorna apenas data e hora (sem microssegundos)
    return timestamp[:19].replace('T', ' ')


def safe_get(dictionary: dict, key: str, default=None):
    """
    Obtém valor de dicionário de forma segura.

    Args:
        dictionary: Dicionário
        key: Chave
        default: Valor padrão

    Returns:
        Valor ou default
    """
    try:
        return dictionary.get(key, default)
    except (AttributeError, KeyError):
        return default


def safe_int(value, default: int = 0) -> int:
    """
    Converte para int de forma segura.

    Args:
        value: Valor a converter
        default: Valor padrão

    Returns:
        Inteiro ou default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default: float = 0.0) -> float:
    """
    Converte para float de forma segura.

    Args:
        value: Valor a converter
        default: Valor padrão

    Returns:
        Float ou default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
