"""
Sistema de Autenticação Multi-Tenant

Módulos:
    - auth_manager: Criação e validação de usuários admin
    - session_manager: Gestão de sessões
    - permissions: RBAC (Role-Based Access Control)
    - middleware: Decorators de proteção de rotas
"""

from .auth_manager import AuthManager
from .session_manager import SessionManager
from .permissions import PermissionManager

__all__ = ['AuthManager', 'SessionManager', 'PermissionManager']
