"""
PermissionManager - Sistema RBAC (Role-Based Access Control)

Responsabilidades:
    - Definir permissões por role (master, org_admin)
    - Verificar se admin tem permissão para ação
    - Verificar se admin pode acessar recurso específico (user, org)

Autor: Sistema Multi-Tenant JungAgent
Data: 2025-12-29
"""

import sqlite3
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PermissionManager:
    """
    Gerenciador de permissões baseado em roles.
    """

    # Definição de permissões por role
    PERMISSIONS = {
        'master': [
            '*'  # Wildcard: acesso total ao sistema
        ],
        'org_admin': [
            'view_own_users',           # Ver usuários da própria org
            'view_own_psychometrics',   # Ver psicometria da própria org
            'view_own_dashboard',       # Acessar dashboard da org
            'generate_own_reports',     # Gerar relatórios da org
            'manage_own_team',          # Adicionar/remover colaboradores
            'view_own_jung_lab'         # Ver jung-lab da própria org (se aplicável)
        ]
    }

    def __init__(self, db_manager=None, db_conn: Optional[sqlite3.Connection] = None):
        """
        Inicializa PermissionManager.

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

    def has_permission(self, admin: Dict, permission: str) -> bool:
        """
        Verifica se admin tem permissão específica.

        Args:
            admin: Dict com 'role' e outros dados do admin
            permission: Permissão a verificar (ex: 'view_own_users')

        Returns:
            True se admin tem a permissão

        Examples:
            >>> perm_mgr.has_permission(master_admin, 'view_own_users')
            True  # Master tem tudo

            >>> perm_mgr.has_permission(org_admin, 'view_own_users')
            True  # Org admin pode ver próprios usuários

            >>> perm_mgr.has_permission(org_admin, 'create_organization')
            False  # Org admin não pode criar organizações
        """
        role = admin.get('role')

        if role not in self.PERMISSIONS:
            logger.warning(f"⚠️  Role desconhecido: {role}")
            return False

        permissions = self.PERMISSIONS[role]

        # Master tem wildcard (acesso total)
        if '*' in permissions:
            return True

        # Verificar se permissão está na lista
        return permission in permissions

    def can_access_user(self, admin: Dict, user_id: str) -> bool:
        """
        Verifica se admin pode acessar dados de um usuário.

        Regras:
            - Master: pode acessar qualquer usuário
            - Org Admin: apenas usuários da própria organização

        Args:
            admin: Dict com 'role' e 'org_id'
            user_id: ID do usuário a acessar

        Returns:
            True se pode acessar
        """
        role = admin.get('role')

        # Master pode acessar qualquer usuário
        if role == 'master':
            return True

        # Org Admin: verificar se user pertence à org
        if role == 'org_admin':
            org_id = admin.get('org_id')

            if not org_id:
                logger.error(f"❌ Org Admin sem org_id: {admin.get('admin_id')}")
                return False

            cursor = self.conn.cursor()

            cursor.execute("""
                SELECT 1 FROM user_organization_mapping
                WHERE user_id = ? AND org_id = ? AND status = 'active'
            """, (user_id, org_id))

            has_access = cursor.fetchone() is not None

            if not has_access:
                logger.debug(f"⚠️  Acesso negado: user {user_id} não pertence à org {org_id}")

            return has_access

        # Qualquer outro role: sem acesso
        return False

    def can_access_org(self, admin: Dict, org_id: str) -> bool:
        """
        Verifica se admin pode acessar dados de uma organização.

        Regras:
            - Master: pode acessar qualquer org
            - Org Admin: apenas a própria org

        Args:
            admin: Dict com 'role' e 'org_id'
            org_id: ID da organização a acessar

        Returns:
            True se pode acessar
        """
        role = admin.get('role')

        # Master pode acessar qualquer org
        if role == 'master':
            return True

        # Org Admin: apenas a própria org
        if role == 'org_admin':
            admin_org_id = admin.get('org_id')

            if not admin_org_id:
                logger.error(f"❌ Org Admin sem org_id: {admin.get('admin_id')}")
                return False

            has_access = (admin_org_id == org_id)

            if not has_access:
                logger.debug(f"⚠️  Acesso negado: admin de org {admin_org_id} tentou acessar org {org_id}")

            return has_access

        return False

    def get_accessible_users(self, admin: Dict) -> List[str]:
        """
        Retorna lista de user_ids que o admin pode acessar.

        Args:
            admin: Dict com 'role' e 'org_id'

        Returns:
            Lista de user_ids
        """
        cursor = self.conn.cursor()

        role = admin.get('role')

        if role == 'master':
            # Master: todos os usuários
            cursor.execute("""
                SELECT user_id FROM users
                WHERE platform = 'telegram'
            """)

        elif role == 'org_admin':
            # Org Admin: apenas usuários da org
            org_id = admin.get('org_id')

            if not org_id:
                logger.error(f"❌ Org Admin sem org_id: {admin.get('admin_id')}")
                return []

            cursor.execute("""
                SELECT user_id FROM user_organization_mapping
                WHERE org_id = ? AND status = 'active'
            """, (org_id,))

        else:
            return []

        rows = cursor.fetchall()
        return [row[0] for row in rows]

    def get_accessible_orgs(self, admin: Dict) -> List[str]:
        """
        Retorna lista de org_ids que o admin pode acessar.

        Args:
            admin: Dict com 'role' e 'org_id'

        Returns:
            Lista de org_ids
        """
        cursor = self.conn.cursor()

        role = admin.get('role')

        if role == 'master':
            # Master: todas as organizações
            cursor.execute("""
                SELECT org_id FROM organizations
                WHERE subscription_status = 'active'
            """)

            rows = cursor.fetchall()
            return [row[0] for row in rows]

        elif role == 'org_admin':
            # Org Admin: apenas a própria org
            org_id = admin.get('org_id')

            if not org_id:
                logger.error(f"❌ Org Admin sem org_id: {admin.get('admin_id')}")
                return []

            return [org_id]

        return []

    def filter_users_by_access(self, admin: Dict, user_ids: List[str]) -> List[str]:
        """
        Filtra lista de user_ids, mantendo apenas os que o admin pode acessar.

        Args:
            admin: Dict com dados do admin
            user_ids: Lista de user_ids a filtrar

        Returns:
            Lista filtrada de user_ids
        """
        accessible_users = set(self.get_accessible_users(admin))
        return [uid for uid in user_ids if uid in accessible_users]

    def require_master(self, admin: Dict) -> bool:
        """
        Verifica se admin é master.

        Args:
            admin: Dict com 'role'

        Returns:
            True se é master

        Raises:
            PermissionError se não for master
        """
        if admin.get('role') != 'master':
            logger.warning(f"⚠️  Acesso negado: requer role master (admin={admin.get('email')})")
            raise PermissionError("Master role required")

        return True

    def require_org_admin(self, admin: Dict) -> bool:
        """
        Verifica se admin é org_admin ou master.

        Args:
            admin: Dict com 'role'

        Returns:
            True se é org_admin ou master

        Raises:
            PermissionError se não tiver permissão
        """
        role = admin.get('role')

        if role not in ['master', 'org_admin']:
            logger.warning(f"⚠️  Acesso negado: requer role org_admin ou master (admin={admin.get('email')})")
            raise PermissionError("Organization admin role required")

        return True

    def get_role_permissions(self, role: str) -> List[str]:
        """
        Retorna lista de permissões de um role.

        Args:
            role: 'master' ou 'org_admin'

        Returns:
            Lista de permissões
        """
        return self.PERMISSIONS.get(role, [])

    def has_any_permission(self, admin: Dict, permissions: List[str]) -> bool:
        """
        Verifica se admin tem QUALQUER UMA das permissões listadas.

        Args:
            admin: Dict com dados do admin
            permissions: Lista de permissões a verificar

        Returns:
            True se tem pelo menos uma
        """
        for permission in permissions:
            if self.has_permission(admin, permission):
                return True

        return False

    def has_all_permissions(self, admin: Dict, permissions: List[str]) -> bool:
        """
        Verifica se admin tem TODAS as permissões listadas.

        Args:
            admin: Dict com dados do admin
            permissions: Lista de permissões a verificar

        Returns:
            True se tem todas
        """
        for permission in permissions:
            if not self.has_permission(admin, permission):
                return False

        return True
