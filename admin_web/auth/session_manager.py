"""
SessionManager - Gerenciamento de Sessões

Responsabilidades:
    - Criar sessões após login bem-sucedido
    - Validar sessões em cada request
    - Invalidar sessões no logout
    - Limpar sessões expiradas (background task)

Autor: Sistema Multi-Tenant JungAgent
Data: 2025-12-29
"""

import uuid
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Gerenciador de sessões para admins.
    """

    def __init__(self, db_manager=None, db_conn: Optional[sqlite3.Connection] = None):
        """
        Inicializa SessionManager.

        Args:
            db_manager: DatabaseManager do jung_core (opcional)
            db_conn: Conexão SQLite direta (opcional)
        """
        if db_manager:
            self.conn = db_manager.conn
        elif db_conn:
            self.conn = db_conn
        else:
            raise ValueError("Forneça db_manager ou db_conn")

    def create(
        self,
        admin_id: str,
        ip_address: str,
        user_agent: str,
        expiry_hours: int = 24
    ) -> str:
        """
        Cria nova sessão para admin.

        Args:
            admin_id: UUID do admin
            ip_address: IP do request
            user_agent: User-Agent do navegador
            expiry_hours: Horas até expiração (padrão: 24h)

        Returns:
            session_id (UUID) para armazenar em cookie
        """
        session_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(hours=expiry_hours)

        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO admin_sessions (
                    session_id,
                    admin_id,
                    ip_address,
                    user_agent,
                    expires_at,
                    is_active
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                admin_id,
                ip_address,
                user_agent,
                expires_at.isoformat(),
                True
            ))

            self.conn.commit()

            logger.info(f"✅ Sessão criada: {session_id[:8]}... (admin={admin_id[:8]}..., expires={expires_at})")
            return session_id

        except Exception as e:
            logger.error(f"❌ Erro ao criar sessão: {e}")
            self.conn.rollback()
            raise

    def validate(self, session_id: str) -> Optional[Dict]:
        """
        Valida sessão e retorna dados do admin se válida.

        Args:
            session_id: UUID da sessão

        Returns:
            Dict com dados do admin ou None se inválida/expirada

            Retorna:
                - admin_id
                - email
                - full_name
                - role
                - org_id
        """
        cursor = self.conn.cursor()

        # Buscar sessão e fazer JOIN com admin_users
        cursor.execute("""
            SELECT
                s.admin_id,
                s.expires_at,
                s.is_active,
                a.email,
                a.full_name,
                a.role,
                a.org_id,
                a.is_active as admin_is_active
            FROM admin_sessions s
            JOIN admin_users a ON s.admin_id = a.admin_id
            WHERE s.session_id = ?
        """, (session_id,))

        row = cursor.fetchone()

        if not row:
            logger.debug(f"⚠️  Sessão não encontrada: {session_id[:8]}...")
            return None

        admin_id, expires_at, is_active, email, full_name, role, org_id, admin_is_active = row

        # Verificar se sessão está ativa
        if not is_active:
            logger.debug(f"⚠️  Sessão inativa: {session_id[:8]}...")
            return None

        # Verificar se admin está ativo
        if not admin_is_active:
            logger.warning(f"⚠️  Admin desativado: {email}")
            return None

        # Verificar expiração
        expires_dt = datetime.fromisoformat(expires_at)
        if datetime.now() > expires_dt:
            logger.info(f"⚠️  Sessão expirada: {session_id[:8]}...")
            # Invalidar sessão expirada
            self.invalidate(session_id)
            return None

        # Sessão válida!
        return {
            'admin_id': admin_id,
            'email': email,
            'full_name': full_name,
            'role': role,
            'org_id': org_id
        }

    def invalidate(self, session_id: str) -> bool:
        """
        Invalida sessão (logout).

        Args:
            session_id: UUID da sessão

        Returns:
            True se sucesso
        """
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                UPDATE admin_sessions
                SET is_active = FALSE
                WHERE session_id = ?
            """, (session_id,))

            self.conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"✅ Sessão invalidada: {session_id[:8]}...")
                return True
            else:
                logger.debug(f"⚠️  Sessão não encontrada para invalidar: {session_id[:8]}...")
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao invalidar sessão: {e}")
            self.conn.rollback()
            return False

    def invalidate_all_user_sessions(self, admin_id: str) -> int:
        """
        Invalida todas as sessões de um admin.

        Útil para:
            - Forçar logout em todos os dispositivos
            - Após alteração de senha
            - Desativação de admin

        Args:
            admin_id: UUID do admin

        Returns:
            Número de sessões invalidadas
        """
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                UPDATE admin_sessions
                SET is_active = FALSE
                WHERE admin_id = ? AND is_active = TRUE
            """, (admin_id,))

            self.conn.commit()
            count = cursor.rowcount

            logger.info(f"✅ {count} sessões invalidadas para admin {admin_id[:8]}...")
            return count

        except Exception as e:
            logger.error(f"❌ Erro ao invalidar sessões: {e}")
            self.conn.rollback()
            return 0

    def refresh(self, session_id: str, expiry_hours: int = 24) -> bool:
        """
        Renova expiração de uma sessão.

        Args:
            session_id: UUID da sessão
            expiry_hours: Novas horas até expiração

        Returns:
            True se sucesso
        """
        cursor = self.conn.cursor()

        new_expires_at = datetime.now() + timedelta(hours=expiry_hours)

        try:
            cursor.execute("""
                UPDATE admin_sessions
                SET expires_at = ?
                WHERE session_id = ? AND is_active = TRUE
            """, (new_expires_at.isoformat(), session_id))

            self.conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"✅ Sessão renovada: {session_id[:8]}... (expires={new_expires_at})")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao renovar sessão: {e}")
            self.conn.rollback()
            return False

    def cleanup_expired(self) -> int:
        """
        Remove sessões expiradas e inativas do banco.

        Deve ser executado periodicamente (ex: cronjob diário).

        Returns:
            Número de sessões removidas
        """
        cursor = self.conn.cursor()

        try:
            # Deletar sessões expiradas ou inativas
            cursor.execute("""
                DELETE FROM admin_sessions
                WHERE expires_at < CURRENT_TIMESTAMP
                   OR is_active = FALSE
            """)

            self.conn.commit()
            count = cursor.rowcount

            logger.info(f"✅ Limpeza de sessões: {count} sessões removidas")
            return count

        except Exception as e:
            logger.error(f"❌ Erro ao limpar sessões: {e}")
            self.conn.rollback()
            return 0

    def get_active_sessions(self, admin_id: str) -> list:
        """
        Lista sessões ativas de um admin.

        Args:
            admin_id: UUID do admin

        Returns:
            Lista de dicts com dados das sessões
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                session_id,
                ip_address,
                user_agent,
                created_at,
                expires_at
            FROM admin_sessions
            WHERE admin_id = ?
              AND is_active = TRUE
              AND expires_at > CURRENT_TIMESTAMP
            ORDER BY created_at DESC
        """, (admin_id,))

        rows = cursor.fetchall()

        sessions = []
        for row in rows:
            sessions.append({
                'session_id': row[0],
                'ip_address': row[1],
                'user_agent': row[2],
                'created_at': row[3],
                'expires_at': row[4]
            })

        return sessions

    def get_session_count(self, admin_id: Optional[str] = None) -> int:
        """
        Conta sessões ativas.

        Args:
            admin_id: Se fornecido, conta apenas sessões deste admin

        Returns:
            Número de sessões ativas
        """
        cursor = self.conn.cursor()

        if admin_id:
            cursor.execute("""
                SELECT COUNT(*)
                FROM admin_sessions
                WHERE admin_id = ?
                  AND is_active = TRUE
                  AND expires_at > CURRENT_TIMESTAMP
            """, (admin_id,))
        else:
            cursor.execute("""
                SELECT COUNT(*)
                FROM admin_sessions
                WHERE is_active = TRUE
                  AND expires_at > CURRENT_TIMESTAMP
            """)

        return cursor.fetchone()[0]
