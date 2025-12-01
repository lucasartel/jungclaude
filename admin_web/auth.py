"""
auth.py - Sistema de Autenticação Segura para Admin Web
========================================================

Sistema de autenticação com:
- Hash bcrypt de senhas
- Comparação timing-safe
- Suporte a múltiplos usuários
- Senhas via variáveis de ambiente

Autor: Sistema Jung
Data: 2025-11-29
"""

import os
import bcrypt
import secrets
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

logger = logging.getLogger(__name__)

# Instância de segurança HTTP Basic
security = HTTPBasic()


class AuthManager:
    """Gerenciador de autenticação com suporte a múltiplos usuários"""

    def __init__(self):
        self.users = self._load_users_from_env()
        logger.info(f"🔐 AuthManager inicializado com {len(self.users)} usuário(s)")

    def _load_users_from_env(self) -> dict:
        """
        Carrega usuários e senhas hashadas das variáveis de ambiente

        Formato esperado:
        ADMIN_USER=usuario1
        ADMIN_PASSWORD=senha_hash_bcrypt_aqui

        OU múltiplos usuários:
        ADMIN_USERS=user1:hash1,user2:hash2,user3:hash3
        """
        users = {}

        # Método 1: Variável única (compatibilidade com versão antiga)
        single_user = os.getenv("ADMIN_USER")
        single_pass = os.getenv("ADMIN_PASSWORD")

        if single_user and single_pass:
            # Se a senha não for um hash bcrypt, criar hash
            if single_pass.startswith("$2b$") or single_pass.startswith("$2a$"):
                # Já é um hash bcrypt
                users[single_user] = single_pass.encode('utf-8')
            else:
                # Senha em texto plano (modo desenvolvimento)
                logger.warning(f"⚠️ Senha em texto plano detectada para {single_user}. Use hash bcrypt em produção!")
                users[single_user] = bcrypt.hashpw(single_pass.encode('utf-8'), bcrypt.gensalt())

        # Método 2: Múltiplos usuários (formato: user1:hash1,user2:hash2)
        multi_users = os.getenv("ADMIN_USERS")
        if multi_users:
            for user_entry in multi_users.split(","):
                try:
                    username, password_hash = user_entry.split(":")
                    username = username.strip()
                    password_hash = password_hash.strip()

                    if password_hash.startswith("$2b$") or password_hash.startswith("$2a$"):
                        users[username] = password_hash.encode('utf-8')
                    else:
                        logger.warning(f"⚠️ Hash inválido para {username}")
                except ValueError:
                    logger.error(f"❌ Formato inválido em ADMIN_USERS: {user_entry}")

        # Fallback para desenvolvimento (admin/admin)
        if not users:
            logger.warning("⚠️ Nenhum usuário configurado! Usando admin/admin (SOMENTE DESENVOLVIMENTO)")
            default_password = "admin"
            users["admin"] = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt())

        return users

    def verify_password(self, username: str, password: str) -> bool:
        """
        Verifica se a senha está correta para o usuário

        Args:
            username: Nome do usuário
            password: Senha em texto plano

        Returns:
            True se credenciais corretas, False caso contrário
        """
        if username not in self.users:
            # Executar bcrypt mesmo assim para evitar timing attack
            bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            return False

        stored_hash = self.users[username]

        try:
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
        except Exception as e:
            logger.error(f"❌ Erro ao verificar senha: {e}")
            return False

    def authenticate(self, credentials: HTTPBasicCredentials) -> str:
        """
        Autentica credenciais HTTP Basic

        Args:
            credentials: Credenciais HTTP Basic

        Returns:
            Username se autenticado

        Raises:
            HTTPException: Se credenciais inválidas
        """
        # Verificar usando comparação timing-safe
        username = credentials.username
        password = credentials.password

        # Log de tentativa (sem senha)
        logger.info(f"🔑 Tentativa de login: {username}")

        if not self.verify_password(username, password):
            logger.warning(f"❌ Falha de autenticação para: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas",
                headers={"WWW-Authenticate": "Basic"},
            )

        logger.info(f"✅ Login bem-sucedido: {username}")
        return username


# Instância global do gerenciador de autenticação
auth_manager = AuthManager()


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    Dependency para verificar credenciais em rotas protegidas

    Usage:
        @router.get("/protected")
        async def protected_route(username: str = Depends(verify_credentials)):
            # username contém o usuário autenticado
            return {"message": f"Olá, {username}"}
    """
    return auth_manager.authenticate(credentials)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_password_hash(password: str) -> str:
    """
    Gera hash bcrypt de uma senha

    Usage:
        >>> hash = generate_password_hash("minha_senha_forte")
        >>> print(hash)
        $2b$12$xyz...

    Para configurar no Railway:
        ADMIN_USER=admin
        ADMIN_PASSWORD=$2b$12$xyz...
    """
    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')


def verify_password_hash(password: str, hash_str: str) -> bool:
    """
    Verifica se uma senha corresponde a um hash

    Usage:
        >>> hash = generate_password_hash("senha123")
        >>> verify_password_hash("senha123", hash)
        True
        >>> verify_password_hash("errada", hash)
        False
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hash_str.encode('utf-8'))
    except Exception:
        return False


# ============================================================================
# CLI HELPER (para gerar hashes de senha)
# ============================================================================

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("🔐 GERADOR DE HASH DE SENHA BCRYPT")
    print("=" * 60)
    print()

    if len(sys.argv) > 1:
        # Modo não-interativo (para scripts)
        password = sys.argv[1]
    else:
        # Modo interativo
        import getpass
        password = getpass.getpass("Digite a senha para gerar hash: ")

    if not password:
        print("❌ Senha vazia!")
        sys.exit(1)

    hash_result = generate_password_hash(password)

    print()
    print("✅ Hash gerado com sucesso!")
    print()
    print("📋 CONFIGURAÇÃO PARA RAILWAY:")
    print("-" * 60)
    print(f"ADMIN_USER=admin")
    print(f"ADMIN_PASSWORD={hash_result}")
    print("-" * 60)
    print()
    print("💡 DICA: Copie o hash acima e adicione como variável de ambiente")
    print("         no Railway ou no seu arquivo .env")
    print()

    # Teste de verificação
    print("🧪 Testando hash...")
    if verify_password_hash(password, hash_result):
        print("✅ Hash válido e funcionando!")
    else:
        print("❌ Erro na verificação do hash!")
        sys.exit(1)
