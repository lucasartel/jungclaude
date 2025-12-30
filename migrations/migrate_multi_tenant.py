#!/usr/bin/env python3
"""
Script de Migração Multi-Tenant para JungAgent Admin

Este script migra o banco de dados de single-user para multi-tenant,
criando backup automático e permitindo rollback em caso de erro.

Uso:
    python migrate_multi_tenant.py --db-path /caminho/para/banco.db \\
        --master-email admin@example.com \\
        --master-password SenhaSegura123

Autor: Sistema Multi-Tenant JungAgent
Data: 2025-12-29
"""

import sqlite3
import sys
import os
import shutil
import argparse
import bcrypt
import uuid
from datetime import datetime
from pathlib import Path


class Colors:
    """Cores para output no terminal"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.END}\n")


def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")


def create_password_hash(password: str) -> str:
    """
    Gera hash bcrypt da senha.

    Args:
        password: Senha em texto plano

    Returns:
        Hash bcrypt da senha
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def backup_database(db_path: str) -> str:
    """
    Cria backup do banco de dados.

    Args:
        db_path: Caminho para o banco original

    Returns:
        Caminho do arquivo de backup

    Raises:
        Exception se falhar ao criar backup
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"

    print_info(f"Criando backup em: {backup_path}")

    try:
        shutil.copy2(db_path, backup_path)
        file_size = os.path.getsize(backup_path) / 1024  # KB

        print_success(f"Backup criado com sucesso ({file_size:.2f} KB)")
        return backup_path

    except Exception as e:
        print_error(f"Falha ao criar backup: {e}")
        raise


def verify_database(db_path: str) -> bool:
    """
    Verifica se o banco de dados é válido.

    Args:
        db_path: Caminho para o banco

    Returns:
        True se válido
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verificar se tabela users existe (banco JungAgent válido)
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='users'
        """)

        if not cursor.fetchone():
            print_error("Tabela 'users' não encontrada. Este não parece ser um banco JungAgent válido.")
            conn.close()
            return False

        conn.close()
        return True

    except Exception as e:
        print_error(f"Erro ao verificar banco: {e}")
        return False


def run_migration_sql(conn: sqlite3.Connection, sql_path: str) -> bool:
    """
    Executa script SQL de migração.

    Args:
        conn: Conexão SQLite
        sql_path: Caminho para o arquivo .sql

    Returns:
        True se sucesso
    """
    try:
        with open(sql_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        cursor = conn.cursor()
        cursor.executescript(migration_sql)
        conn.commit()

        print_success("Script SQL executado com sucesso")
        return True

    except Exception as e:
        print_error(f"Erro ao executar SQL: {e}")
        conn.rollback()
        return False


def create_master_user(
    conn: sqlite3.Connection,
    email: str,
    password: str,
    full_name: str = "Master Admin"
) -> bool:
    """
    Cria usuário master com senha criptografada.

    Args:
        conn: Conexão SQLite
        email: Email do master
        password: Senha em texto plano
        full_name: Nome completo

    Returns:
        True se sucesso
    """
    try:
        cursor = conn.cursor()

        # Verificar se já existe
        cursor.execute("SELECT admin_id FROM admin_users WHERE email = ?", (email,))
        if cursor.fetchone():
            print_warning(f"Usuário master com email '{email}' já existe. Pulando criação.")
            return True

        # Gerar hash da senha
        print_info("Gerando hash bcrypt da senha...")
        password_hash = create_password_hash(password)

        admin_id = f"master-admin-{uuid.uuid4().hex[:8]}"

        # Inserir master
        cursor.execute("""
            INSERT INTO admin_users (
                admin_id,
                email,
                password_hash,
                full_name,
                role,
                org_id,
                is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (admin_id, email, password_hash, full_name, 'master', None, True))

        conn.commit()
        print_success(f"Usuário master criado: {email} (ID: {admin_id})")
        return True

    except Exception as e:
        print_error(f"Erro ao criar usuário master: {e}")
        conn.rollback()
        return False


def verify_migration(conn: sqlite3.Connection) -> dict:
    """
    Verifica resultado da migração.

    Args:
        conn: Conexão SQLite

    Returns:
        Dict com estatísticas
    """
    cursor = conn.cursor()
    stats = {}

    try:
        # Contar organizações
        cursor.execute("SELECT COUNT(*) FROM organizations")
        stats['organizations'] = cursor.fetchone()[0]

        # Contar admins
        cursor.execute("SELECT COUNT(*) FROM admin_users")
        stats['admin_users'] = cursor.fetchone()[0]

        # Contar masters
        cursor.execute("SELECT COUNT(*) FROM admin_users WHERE role = 'master'")
        stats['master_admins'] = cursor.fetchone()[0]

        # Contar mapeamentos
        cursor.execute("SELECT COUNT(*) FROM user_organization_mapping")
        stats['user_mappings'] = cursor.fetchone()[0]

        # Contar usuários totais (para comparar)
        cursor.execute("SELECT COUNT(*) FROM users WHERE platform = 'telegram'")
        stats['total_users'] = cursor.fetchone()[0]

        return stats

    except Exception as e:
        print_error(f"Erro ao verificar migração: {e}")
        return {}


def run_migration(
    db_path: str,
    master_email: str,
    master_password: str,
    master_name: str = "Master Admin"
) -> bool:
    """
    Executa migração completa.

    Args:
        db_path: Caminho para o banco de dados
        master_email: Email do usuário master
        master_password: Senha do usuário master
        master_name: Nome completo do master

    Returns:
        True se sucesso
    """
    # 1. Verificar banco
    print_header("VERIFICANDO BANCO DE DADOS")

    if not os.path.exists(db_path):
        print_error(f"Banco de dados não encontrado: {db_path}")
        return False

    if not verify_database(db_path):
        return False

    print_success("Banco de dados válido")

    # 2. Criar backup
    print_header("CRIANDO BACKUP")

    try:
        backup_path = backup_database(db_path)
    except Exception:
        print_error("Migração abortada: falha ao criar backup")
        return False

    # 3. Executar migração
    print_header("EXECUTANDO MIGRAÇÃO")

    conn = None
    try:
        conn = sqlite3.connect(db_path)

        # Executar SQL de migração
        script_dir = Path(__file__).parent
        sql_path = script_dir / 'multi_tenant_migration.sql'

        if not sql_path.exists():
            print_error(f"Script SQL não encontrado: {sql_path}")
            return False

        print_info(f"Executando: {sql_path}")

        if not run_migration_sql(conn, str(sql_path)):
            raise Exception("Falha ao executar SQL de migração")

        # Criar usuário master
        print_info("Criando usuário master...")

        if not create_master_user(conn, master_email, master_password, master_name):
            raise Exception("Falha ao criar usuário master")

        # 4. Verificar migração
        print_header("VERIFICANDO RESULTADO")

        stats = verify_migration(conn)

        if not stats:
            raise Exception("Falha ao verificar migração")

        print_info("Estatísticas da migração:")
        print(f"   • Organizações: {stats.get('organizations', 0)}")
        print(f"   • Admins totais: {stats.get('admin_users', 0)}")
        print(f"   • Masters: {stats.get('master_admins', 0)}")
        print(f"   • Usuários migrados: {stats.get('user_mappings', 0)}")
        print(f"   • Usuários totais: {stats.get('total_users', 0)}")

        # Validar
        if stats.get('master_admins', 0) < 1:
            raise Exception("Nenhum usuário master criado!")

        if stats.get('user_mappings', 0) != stats.get('total_users', 0):
            print_warning(
                f"Nem todos os usuários foram migrados! "
                f"({stats.get('user_mappings', 0)}/{stats.get('total_users', 0)})"
            )

        # 5. Sucesso!
        print_header("MIGRAÇÃO CONCLUÍDA")

        print_success("Migração multi-tenant concluída com sucesso!")
        print_info(f"Backup salvo em: {backup_path}")
        print_info(f"Email master: {master_email}")
        print_warning("IMPORTANTE: Guarde a senha do master em local seguro!")

        return True

    except Exception as e:
        print_header("ERRO NA MIGRAÇÃO")
        print_error(f"Erro: {e}")
        print_warning("Restaurando backup...")

        # Restaurar backup
        try:
            if conn:
                conn.close()

            shutil.copy2(backup_path, db_path)
            print_success("Backup restaurado. Banco de dados inalterado.")

        except Exception as restore_error:
            print_error(f"ERRO CRÍTICO ao restaurar backup: {restore_error}")
            print_error(f"Backup manual disponível em: {backup_path}")

        return False

    finally:
        if conn:
            conn.close()


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Migração Multi-Tenant para JungAgent Admin',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Migração básica
  python migrate_multi_tenant.py \\
      --db-path ./jung_memory.db \\
      --master-email admin@example.com \\
      --master-password SenhaSegura123

  # Com nome customizado
  python migrate_multi_tenant.py \\
      --db-path ./jung_memory.db \\
      --master-email lucas@jungagent.com \\
      --master-password MinhaSenha! \\
      --master-name "Lucas (Master)"
        """
    )

    parser.add_argument(
        '--db-path',
        required=True,
        help='Caminho para o banco de dados SQLite'
    )

    parser.add_argument(
        '--master-email',
        required=True,
        help='Email do usuário master (login)'
    )

    parser.add_argument(
        '--master-password',
        required=True,
        help='Senha do usuário master (mínimo 8 caracteres)'
    )

    parser.add_argument(
        '--master-name',
        default='Master Admin',
        help='Nome completo do usuário master (padrão: "Master Admin")'
    )

    parser.add_argument(
        '--no-confirm',
        action='store_true',
        help='Pular confirmação (use com cuidado!)'
    )

    args = parser.parse_args()

    # Validar senha
    if len(args.master_password) < 8:
        print_error("Senha deve ter no mínimo 8 caracteres")
        sys.exit(1)

    # Banner
    print_header("MIGRAÇÃO MULTI-TENANT JUNGAGENT")

    print(f"{Colors.BOLD}Configuração:{Colors.END}")
    print(f"   • Banco: {args.db_path}")
    print(f"   • Master email: {args.master_email}")
    print(f"   • Master nome: {args.master_name}")
    print(f"   • Senha: {'*' * len(args.master_password)}")

    # Confirmação
    if not args.no_confirm:
        print(f"\n{Colors.BOLD}{Colors.YELLOW}⚠️  ATENÇÃO:{Colors.END}")
        print("   Esta operação vai modificar o banco de dados.")
        print("   Um backup será criado automaticamente.")
        print()

        confirm = input(f"{Colors.BOLD}Continuar? (yes/no): {Colors.END}").strip().lower()

        if confirm != 'yes':
            print_warning("Migração cancelada pelo usuário")
            sys.exit(0)

    # Executar migração
    success = run_migration(
        args.db_path,
        args.master_email,
        args.master_password,
        args.master_name
    )

    if success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 SUCESSO!{Colors.END}\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}💥 FALHA NA MIGRAÇÃO{Colors.END}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
