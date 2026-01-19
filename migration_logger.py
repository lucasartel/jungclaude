"""
migration_logger.py

Logger especializado para migrations do Sistema TRI com:
- Arquivo de log dedicado com timestamp
- Console output colorido
- Timestamps ISO em cada entrada
- Stack traces completos para erros
- Métricas de execução
- Suporte a rollback

Uso:
    from migration_logger import *

    log_migration_start("TRI System v1.0")
    log_table_created("irt_fragments", 12)
    log_seed_progress(30, 150, "fragmentos")
    log_migration_complete("TRI System v1.0", {"tabelas": 6})
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# ========================================
# CONFIGURAÇÃO DE DIRETÓRIOS
# ========================================

# Criar diretório de logs se não existir
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Arquivo de log com timestamp único
LOG_FILE = LOGS_DIR / f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# ========================================
# CONFIGURAÇÃO DO LOGGER
# ========================================

# Logger principal para migrations
migration_logger = logging.getLogger("migrations")
migration_logger.setLevel(logging.DEBUG)

# Evitar duplicação de handlers se módulo for reimportado
if not migration_logger.handlers:
    # Handler para arquivo (detalhado - inclui DEBUG)
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))

    # Handler para console (resumido - apenas INFO+)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(message)s'
    ))

    migration_logger.addHandler(file_handler)
    migration_logger.addHandler(console_handler)

# ========================================
# FUNÇÕES DE LOG
# ========================================

def log_migration_start(name: str) -> None:
    """
    Registra início de uma migration.

    Args:
        name: Nome identificador da migration (ex: "TRI System v1.0")
    """
    migration_logger.info("=" * 60)
    migration_logger.info(f"INICIANDO MIGRATION: {name}")
    migration_logger.info(f"Timestamp: {datetime.now().isoformat()}")
    migration_logger.info(f"Log file: {LOG_FILE}")
    migration_logger.info("=" * 60)


def log_table_created(table_name: str, columns: int) -> None:
    """
    Registra criação bem-sucedida de tabela.

    Args:
        table_name: Nome da tabela criada
        columns: Número de colunas na tabela
    """
    migration_logger.info(f"✅ Tabela '{table_name}' criada ({columns} colunas)")


def log_table_exists(table_name: str) -> None:
    """
    Registra que tabela já existia (não foi criada).

    Args:
        table_name: Nome da tabela existente
    """
    migration_logger.debug(f"ℹ️  Tabela '{table_name}' já existe (mantida)")


def log_index_created(index_name: str, table_name: str) -> None:
    """
    Registra criação de índice.

    Args:
        index_name: Nome do índice
        table_name: Tabela onde o índice foi criado
    """
    migration_logger.debug(f"📇 Índice '{index_name}' criado em '{table_name}'")


def log_seed_progress(current: int, total: int, item_type: str) -> None:
    """
    Registra progresso de seed de dados.

    Args:
        current: Quantidade atual inserida
        total: Total a ser inserido
        item_type: Tipo de item (ex: "fragmentos", "parâmetros")
    """
    percentage = (current / total * 100) if total > 0 else 0
    migration_logger.info(f"🌱 Seed: {current}/{total} {item_type} ({percentage:.0f}%)")


def log_error(message: str, exception: Optional[Exception] = None) -> None:
    """
    Registra erro com detalhes opcionais da exceção.

    Args:
        message: Mensagem de erro
        exception: Exceção capturada (opcional)
    """
    migration_logger.error(f"❌ ERRO: {message}")

    if exception:
        migration_logger.error(f"   Tipo: {type(exception).__name__}")
        migration_logger.error(f"   Mensagem: {str(exception)}")

        # Stack trace completo no nível DEBUG
        import traceback
        stack_trace = traceback.format_exc()
        migration_logger.debug(f"   Stack trace:\n{stack_trace}")


def log_warning(message: str) -> None:
    """
    Registra aviso (não crítico).

    Args:
        message: Mensagem de aviso
    """
    migration_logger.warning(f"⚠️  {message}")


def log_migration_complete(name: str, stats: Dict) -> None:
    """
    Registra conclusão bem-sucedida da migration.

    Args:
        name: Nome da migration
        stats: Dicionário com estatísticas (ex: {"tabelas_criadas": 6})
    """
    migration_logger.info("=" * 60)
    migration_logger.info(f"MIGRATION CONCLUÍDA: {name}")
    migration_logger.info("-" * 40)

    for key, value in stats.items():
        key_formatted = key.replace("_", " ").title()
        migration_logger.info(f"  {key_formatted}: {value}")

    migration_logger.info("-" * 40)
    migration_logger.info(f"Log salvo em: {LOG_FILE}")
    migration_logger.info("=" * 60)


def log_rollback(reason: str) -> None:
    """
    Registra início de rollback.

    Args:
        reason: Motivo do rollback
    """
    migration_logger.warning("=" * 60)
    migration_logger.warning("⚠️  ROLLBACK INICIADO")
    migration_logger.warning(f"   Motivo: {reason}")
    migration_logger.warning("=" * 60)


def log_rollback_complete() -> None:
    """Registra conclusão do rollback."""
    migration_logger.warning("⚠️  ROLLBACK CONCLUÍDO")


def log_debug(message: str) -> None:
    """
    Registra mensagem de debug (apenas no arquivo).

    Args:
        message: Mensagem de debug
    """
    migration_logger.debug(f"🔍 {message}")


def log_info(message: str) -> None:
    """
    Registra mensagem informativa.

    Args:
        message: Mensagem informativa
    """
    migration_logger.info(message)


def get_log_file_path() -> Path:
    """Retorna o caminho do arquivo de log atual."""
    return LOG_FILE


# ========================================
# CONTEXTO DE MIGRATION
# ========================================

class MigrationContext:
    """
    Gerenciador de contexto para migrations com logging automático.

    Uso:
        with MigrationContext("TRI System v1.0") as ctx:
            ctx.table_created("irt_fragments", 12)
            ctx.seed_progress(30, 150, "fragmentos")
    """

    def __init__(self, name: str):
        self.name = name
        self.stats = {
            "tabelas_criadas": 0,
            "tabelas_existentes": 0,
            "indices_criados": 0,
            "registros_inseridos": 0,
            "erros": 0
        }
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        log_migration_start(self.name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.stats["erros"] += 1
            log_error(f"Migration falhou: {exc_val}", exc_val)
            log_rollback(str(exc_val))
            return False

        # Calcular duração
        duration = datetime.now() - self.start_time
        self.stats["duracao_segundos"] = duration.total_seconds()

        log_migration_complete(self.name, self.stats)
        return True

    def table_created(self, table_name: str, columns: int) -> None:
        """Registra criação de tabela."""
        log_table_created(table_name, columns)
        self.stats["tabelas_criadas"] += 1

    def table_exists(self, table_name: str) -> None:
        """Registra tabela já existente."""
        log_table_exists(table_name)
        self.stats["tabelas_existentes"] += 1

    def index_created(self, index_name: str, table_name: str) -> None:
        """Registra criação de índice."""
        log_index_created(index_name, table_name)
        self.stats["indices_criados"] += 1

    def seed_progress(self, current: int, total: int, item_type: str) -> None:
        """Registra progresso de seed."""
        log_seed_progress(current, total, item_type)
        self.stats["registros_inseridos"] = current

    def error(self, message: str, exception: Optional[Exception] = None) -> None:
        """Registra erro."""
        log_error(message, exception)
        self.stats["erros"] += 1


# ========================================
# TESTE DO MÓDULO
# ========================================

if __name__ == "__main__":
    # Teste básico do logger
    print(f"Testando migration_logger...")
    print(f"Log será salvo em: {LOG_FILE}")

    with MigrationContext("Teste de Logger") as ctx:
        ctx.table_created("tabela_teste", 5)
        ctx.table_exists("tabela_existente")
        ctx.index_created("idx_teste", "tabela_teste")
        ctx.seed_progress(50, 100, "registros de teste")
        ctx.seed_progress(100, 100, "registros de teste")

    print(f"\n✅ Teste concluído! Verifique o log em: {LOG_FILE}")
