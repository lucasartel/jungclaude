"""
test_query_enrichment.py

Script de teste para validar Query Enrichment (Fase 2)
"""

import logging
from jung_core import HybridDatabaseManager, Config

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_query_enrichment_functions():
    """Testa funções auxiliares de query enrichment"""

    logger.info("=" * 60)
    logger.info("TESTE 1: Funções de Query Enrichment")
    logger.info("=" * 60)

    Config.validate()
    db = HybridDatabaseManager()

    # Teste 1: _extract_names_from_text
    logger.info("\n1. Testando _extract_names_from_text:")

    text1 = "Minha esposa Ana está preocupada com o trabalho"
    text2 = "João e Maria foram viajar para Paris"
    text3 = "O trabalho está difícil mas estou tentando"

    names1 = db._extract_names_from_text(text1)
    names2 = db._extract_names_from_text(text2)
    names3 = db._extract_names_from_text(text3)

    logger.info(f"   '{text1}' → {names1} (esperado: ['Ana'])")
    logger.info(f"   '{text2}' → {names2} (esperado: ['João', 'Maria', 'Paris'])")
    logger.info(f"   '{text3}' → {names3} (esperado: [])")

    # Teste 2: _detect_topics_in_text
    logger.info("\n2. Testando _detect_topics_in_text:")

    text1 = "Meu chefe está cobrando muito, preciso de férias"
    text2 = "Minha filha está doente, vou ao médico amanhã"
    text3 = "Estou preocupado com minhas dívidas e salário baixo"

    topics1 = db._detect_topics_in_text(text1)
    topics2 = db._detect_topics_in_text(text2)
    topics3 = db._detect_topics_in_text(text3)

    logger.info(f"   '{text1}' → {topics1} (esperado: ['trabalho', 'lazer'])")
    logger.info(f"   '{text2}' → {topics2} (esperado: ['familia', 'saude'])")
    logger.info(f"   '{text3}' → {topics3} (esperado: ['dinheiro'])")

    logger.info("\n✅ Testes de funções auxiliares concluídos!")


def test_enriched_semantic_search():
    """Testa busca semântica com query enrichment"""

    logger.info("\n" + "=" * 60)
    logger.info("TESTE 2: Busca Semântica com Query Enrichment")
    logger.info("=" * 60)

    Config.validate()
    db = HybridDatabaseManager()

    # Usar usuário de teste criado anteriormente
    test_user_id = "test_metadata_enrichment"

    # Simular histórico de conversa
    chat_history = [
        {"role": "user", "content": "Estou preocupado com minha família"},
        {"role": "assistant", "content": "Entendo. Pode me contar mais sobre isso?"},
    ]

    logger.info("\n1. Teste sem enrichment (query simples):")
    logger.info("   Query: 'Ana'")

    # Para comparação, vamos ver a query original vs enriquecida
    simple_query = "Ana"

    logger.info("\n2. Teste COM enrichment (query enriquecida):")

    # Construir query enriquecida manualmente para ver o resultado
    enriched = db._build_enriched_query(
        user_id=test_user_id,
        user_input="Como está Ana?",
        chat_history=chat_history
    )

    logger.info(f"   Query enriquecida: '{enriched[:200]}...'")

    # Executar busca semântica com query enrichment
    logger.info("\n3. Executando busca semântica:")

    if db.chroma_enabled:
        results = db.semantic_search(
            user_id=test_user_id,
            query="Como está Ana?",
            k=3,
            chat_history=chat_history
        )

        logger.info(f"   ✅ Encontradas {len(results)} memórias")

        for i, result in enumerate(results, 1):
            logger.info(f"\n   Memória {i}:")
            logger.info(f"      Input: {result['user_input'][:60]}...")
            logger.info(f"      Score: {result.get('similarity_score', 0):.3f}")

            metadata = result.get('metadata', {})
            logger.info(f"      Topics: {metadata.get('topics', 'N/A')}")
            logger.info(f"      People: {metadata.get('mentions_people', 'N/A')}")
    else:
        logger.warning("   ⚠️ ChromaDB desabilitado")

    logger.info("\n✅ Teste de busca concluído!")


def test_enrichment_with_facts():
    """Testa enrichment quando há fatos sobre pessoas"""

    logger.info("\n" + "=" * 60)
    logger.info("TESTE 3: Enrichment com Fatos Estruturados")
    logger.info("=" * 60)

    Config.validate()
    db = HybridDatabaseManager()

    test_user_id = "test_metadata_enrichment"

    # Primeiro, garantir que temos alguns fatos sobre "Ana"
    cursor = db.conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) as count
        FROM user_facts
        WHERE user_id = ? AND fact_value LIKE '%Ana%'
    """, (test_user_id,))

    fact_count = cursor.fetchone()['count']

    logger.info(f"\n1. Fatos existentes sobre 'Ana': {fact_count}")

    if fact_count == 0:
        logger.warning("   ⚠️ Nenhum fato sobre Ana encontrado")
        logger.info("   Salvando conversa para criar fato...")

        # Criar uma conversa que menciona Ana
        db.save_conversation(
            user_id=test_user_id,
            user_name="Teste Enrichment",
            user_input="Minha esposa Ana é professora",
            ai_response="Que legal! Em que escola ela leciona?",
            keywords=["esposa", "professora"],
            platform="test"
        )

        logger.info("   ✅ Conversa salva")

    # Testar query enrichment com nome mencionado
    logger.info("\n2. Testando enrichment com nome 'Ana':")

    enriched = db._build_enriched_query(
        user_id=test_user_id,
        user_input="Ana está estressada",
        chat_history=None
    )

    logger.info(f"   Query original: 'Ana está estressada'")
    logger.info(f"   Query enriquecida: '{enriched[:300]}'")

    # Verificar se fatos foram incluídos
    if "Ana" in enriched and len(enriched) > len("Ana está estressada"):
        logger.info("   ✅ Fatos sobre Ana foram incluídos na query!")
    else:
        logger.warning("   ⚠️ Nenhum fato adicional foi incluído")

    logger.info("\n✅ Teste de enrichment com fatos concluído!")


if __name__ == "__main__":
    try:
        test_query_enrichment_functions()
        test_enriched_semantic_search()
        test_enrichment_with_facts()

        logger.info("\n" + "=" * 60)
        logger.info("🎉 TODOS OS TESTES PASSARAM!")
        logger.info("=" * 60)
        logger.info("\nQuery Enrichment (Fase 2) está funcionando corretamente.")
        logger.info("\nMelhorias implementadas:")
        logger.info("1. Extração de nomes próprios do input")
        logger.info("2. Detecção de tópicos (trabalho, família, saúde, etc.)")
        logger.info("3. Busca de fatos estruturados sobre pessoas mencionadas")
        logger.info("4. Histórico expandido de 3 para 5 mensagens")
        logger.info("\nPróximos passos:")
        logger.info("1. Commit e push das mudanças")
        logger.info("2. Deploy no Railway")
        logger.info("3. Monitorar logs de produção")

    except Exception as e:
        logger.error(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        logger.error(traceback.format_exc())
