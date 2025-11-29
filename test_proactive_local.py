#!/usr/bin/env python3
"""
Script de teste local do sistema proativo.
Simula exatamente o que o scheduler faz no Railway.
"""

import sys
import os
from pathlib import Path

# Adicionar diretório ao path
sys.path.insert(0, str(Path(__file__).parent))

from jung_core import HybridDatabaseManager
from jung_proactive_advanced import ProactiveAdvancedSystem
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_proactive_system():
    """Testa o sistema proativo passo a passo"""

    print("="*80)
    print("TESTE DO SISTEMA PROATIVO")
    print("="*80)

    # 1. Inicializar componentes
    print("\n[1] Inicializando componentes...")
    try:
        db = HybridDatabaseManager()
        proactive = ProactiveAdvancedSystem(db=db)
        print("   OK Componentes inicializados")
    except Exception as e:
        print(f"   ERR Erro ao inicializar: {e}")
        return

    # 2. Buscar usuários
    print("\n[2] Buscando usuários...")
    try:
        users = db.get_all_users()
        print(f"   OK Total de usuários: {len(users)}")

        if not users:
            print("   WARN  Nenhum usuário cadastrado!")
            return

        for user in users:
            print(f"\n   USER: {user.get('user_name')}:")
            print(f"      - user_id: {user.get('user_id')}")
            print(f"      - platform_id: {user.get('platform_id')}")
            print(f"      - last_seen: {user.get('last_seen')}")
            print(f"      - total_messages: {user.get('total_messages', 0)}")
    except Exception as e:
        print(f"   ERR Erro ao buscar usuários: {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. Testar elegibilidade de cada usuário
    print("\n[3] Testando elegibilidade...")

    for user in users:
        user_id = user.get('user_id')
        user_name = user.get('user_name', 'Usuário')
        platform_id = user.get('platform_id')

        print(f"\n   {'='*60}")
        print(f"   Testando: {user_name}")
        print(f"   {'='*60}")

        if not user_id:
            print(f"   ERR user_id ausente")
            continue

        if not platform_id:
            print(f"   ERR platform_id ausente")
            continue

        # Tentar gerar mensagem
        try:
            message = proactive.check_and_generate_advanced_message(
                user_id=user_id,
                user_name=user_name
            )

            if message:
                print(f"\n   OK - MENSAGEM GERADA:")
                print(f"   {'-'*60}")
                print(f"   {message[:200]}...")
                print(f"   {'-'*60}")
                print(f"\n   Enviaria para telegram_id: {platform_id}")
            else:
                print(f"   NAO ELEGIVEL (veja logs acima)")

        except Exception as e:
            print(f"   ERR Erro ao gerar mensagem: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("TESTE COMPLETO")
    print("="*80)

if __name__ == "__main__":
    test_proactive_system()
