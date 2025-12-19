#!/usr/bin/env python3
"""
test_fact_extraction.py - Teste de Extração de Fatos
=====================================================

Testa se o sistema está extraindo e salvando fatos corretamente
das conversas dos usuários.
"""

import logging
from jung_core import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_fact_extraction():
    """
    Testa extração de fatos com mensagens de exemplo
    """

    db = DatabaseManager()

    # Mensagens de teste simulando informações pessoais
    test_messages = [
        "Minha esposa se chama Maria",
        "Tenho dois filhos: João e Pedro",
        "Trabalho como desenvolvedor na Google",
        "Sou introvertido e gosto de ficar sozinho",
        "Meu pai é médico e minha mãe é professora"
    ]

    # User ID de teste
    test_user_id = "test_user_12345"

    logger.info("="*60)
    logger.info("TESTE DE EXTRAÇÃO DE FATOS")
    logger.info("="*60)

    # Criar usuário de teste se não existir
    user = db.get_user(test_user_id)
    if not user:
        logger.info(f"Criando usuário de teste: {test_user_id}")
        db.create_user(
            user_id=test_user_id,
            user_name="Usuário Teste",
            platform="telegram",
            platform_id="123456789"
        )

    # Testar extração para cada mensagem
    for i, message in enumerate(test_messages, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"TESTE {i}: {message}")
        logger.info(f"{'='*60}")

        # Simular conversation_id
        conversation_id = 1000 + i

        # Extrair fatos
        extracted = db.extract_and_save_facts(test_user_id, message, conversation_id)

        logger.info(f"Fatos extraídos: {len(extracted)}")
        for fact in extracted:
            logger.info(f"  - {fact['category']}.{fact['key']}: {fact['value']}")

    # Verificar fatos salvos no banco
    logger.info(f"\n{'='*60}")
    logger.info("FATOS SALVOS NO BANCO")
    logger.info(f"{'='*60}")

    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT fact_category, fact_key, fact_value, version, is_current
        FROM user_facts
        WHERE user_id = ?
        ORDER BY fact_category, fact_key, version
    """, (test_user_id,))

    facts = cursor.fetchall()

    logger.info(f"\nTotal de fatos salvos: {len(facts)}")

    current_category = None
    for fact in facts:
        if fact['fact_category'] != current_category:
            current_category = fact['fact_category']
            logger.info(f"\n{current_category}:")

        status = "✓ ATUAL" if fact['is_current'] else "✗ ANTIGO"
        logger.info(f"  {fact['fact_key']}: {fact['fact_value']} (v{fact['version']}) {status}")

    # Testar build_rich_context
    logger.info(f"\n{'='*60}")
    logger.info("CONTEXTO SEMÂNTICO GERADO")
    logger.info(f"{'='*60}")

    context = db.build_rich_context(
        user_id=test_user_id,
        current_input="Como está minha família?",
        k_memories=3
    )

    logger.info("\n" + context)

    # Análise de problemas
    logger.info(f"\n{'='*60}")
    logger.info("ANÁLISE DE PROBLEMAS")
    logger.info(f"{'='*60}")

    # Verificar se fatos familiares foram extraídos
    cursor.execute("""
        SELECT COUNT(*) as count FROM user_facts
        WHERE user_id = ? AND fact_category = 'RELACIONAMENTO' AND is_current = 1
    """, (test_user_id,))

    relationship_count = cursor.fetchone()['count']

    if relationship_count == 0:
        logger.error("❌ PROBLEMA: Nenhum fato de relacionamento foi extraído!")
        logger.error("   Mensagens com 'esposa' e 'filhos' não foram reconhecidas")
    else:
        logger.info(f"✅ {relationship_count} fatos de relacionamento extraídos")

    # Verificar se nomes próprios foram capturados
    cursor.execute("""
        SELECT fact_value FROM user_facts
        WHERE user_id = ? AND is_current = 1
    """, (test_user_id,))

    all_values = [row['fact_value'] for row in cursor.fetchall()]

    expected_names = ['Maria', 'João', 'Pedro']
    captured_names = [name for name in expected_names if any(name.lower() in v.lower() for v in all_values)]

    if not captured_names:
        logger.error("❌ PROBLEMA: Nenhum nome próprio foi capturado!")
        logger.error("   O sistema detectou 'esposa' e 'filhos' mas não salvou os nomes")
    else:
        logger.info(f"✅ Nomes capturados: {', '.join(captured_names)}")

    logger.info(f"\n{'='*60}")
    logger.info("FIM DO TESTE")
    logger.info(f"{'='*60}")

if __name__ == "__main__":
    test_fact_extraction()
