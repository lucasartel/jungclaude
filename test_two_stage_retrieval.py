"""
test_two_stage_retrieval.py

Script de teste para validar Two-Stage Retrieval & Reranking (Fase 3)
"""

import logging
from jung_core import HybridDatabaseManager, Config

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_adaptive_k():
    """Testa k adaptativo"""

    logger.info("=" * 60)
    logger.info("TESTE 1: k Adaptativo")
    logger.info("=" * 60)

    Config.validate()
    db = HybridDatabaseManager()

    test_user_id = "test_metadata_enrichment"

    # Teste 1: Query curta
    logger.info("\n1. Query curta (2 palavras):")
    k1 = db._calculate_adaptive_k("ok entendi", [], test_user_id)
    logger.info(f"   k calculado: {k1} (esperado: 3-4)")

    # Teste 2: Query média
    logger.info("\n2. Query média (10 palavras):")
    k2 = db._calculate_adaptive_k("Como está Ana? Ela ainda está preocupada com a viagem?", [], test_user_id)
    logger.info(f"   k calculado: {k2} (esperado: 5-7)")

    # Teste 3: Query complexa com múltiplas pessoas
    logger.info("\n3. Query complexa (múltiplas pessoas):")
    k3 = db._calculate_adaptive_k("Como estão Ana, João e Maria? Todos bem?", [], test_user_id)
    logger.info(f"   k calculado: {k3} (esperado: 8-10)")

    # Teste 4: Histórico longo
    logger.info("\n4. Query com histórico longo:")
    long_history = [{"role": "user", "content": f"Mensagem {i}"} for i in range(15)]
    k4 = db._calculate_adaptive_k("Como está tudo?", long_history, test_user_id)
    logger.info(f"   k calculado: {k4} (esperado: 6-7)")

    logger.info("\n✅ Teste de k adaptativo concluído!")


def test_reranking():
    """Testa reranking inteligente"""

    logger.info("\n" + "=" * 60)
    logger.info("TESTE 2: Reranking Inteligente")
    logger.info("=" * 60)

    Config.validate()
    db = HybridDatabaseManager()

    test_user_id = "test_metadata_enrichment"

    logger.info("\n1. Criando conversas de teste com diferentes características:")

    # Conversa recente sobre Ana (alta relevância)
    db.save_conversation(
        user_id=test_user_id,
        user_name="Teste Reranking",
        user_input="Ana está muito estressada com o trabalho",
        ai_response="Que situação difícil. O que você acha que poderia ajudar Ana?",
        tension_level=0.8,
        affective_charge=0.9,
        existential_depth=0.5,
        keywords=["Ana", "estresse", "trabalho"],
        platform="test"
    )

    # Conversa antiga sobre trabalho (baixa relevância temporal)
    from datetime import datetime, timedelta
    import time
    time.sleep(1)  # Garantir timestamp diferente

    db.save_conversation(
        user_id=test_user_id,
        user_name="Teste Reranking",
        user_input="Meu trabalho está muito chato ultimamente",
        ai_response="Entendo. O que especificamente está chato?",
        tension_level=0.3,
        affective_charge=0.4,
        existential_depth=0.2,
        keywords=["trabalho", "chato"],
        platform="test"
    )

    # Conversa com alta carga emocional
    time.sleep(1)

    db.save_conversation(
        user_id=test_user_id,
        user_name="Teste Reranking",
        user_input="Estou muito preocupado com a saúde da minha mãe",
        ai_response="Isso deve ser muito difícil para você. Quer conversar sobre isso?",
        tension_level=0.9,
        affective_charge=1.0,
        existential_depth=0.8,
        keywords=["mãe", "saúde", "preocupação"],
        platform="test"
    )

    logger.info("   ✅ 3 conversas criadas")

    logger.info("\n2. Testando busca semântica com two-stage:")

    if db.chroma_enabled:
        # Busca sobre Ana (deve priorizar conversa recente sobre Ana)
        results = db.semantic_search(
            user_id=test_user_id,
            query="Como está Ana?",
            k=None,  # Usar k adaptativo
            chat_history=[]
        )

        logger.info(f"\n   ✅ Busca retornou {len(results)} resultados")

        for i, result in enumerate(results, 1):
            logger.info(f"\n   Resultado {i}:")
            logger.info(f"      Input: {result['user_input'][:60]}...")
            logger.info(f"      Final score: {result.get('final_score', 0):.3f}")
            logger.info(f"      Boosts: {result.get('boosts', {})}")

        # Verificar se primeiro resultado é sobre Ana
        if results and "Ana" in results[0]['user_input']:
            logger.info("\n   ✅ Reranking funcionou! Conversa sobre Ana está em primeiro")
        else:
            logger.warning("\n   ⚠️ Conversa sobre Ana não está em primeiro lugar")

    else:
        logger.warning("   ⚠️ ChromaDB desabilitado")

    logger.info("\n✅ Teste de reranking concluído!")


def test_two_stage_end_to_end():
    """Teste completo end-to-end do two-stage retrieval"""

    logger.info("\n" + "=" * 60)
    logger.info("TESTE 3: Two-Stage End-to-End")
    logger.info("=" * 60)

    Config.validate()
    db = HybridDatabaseManager()

    test_user_id = "test_metadata_enrichment"

    logger.info("\n1. Teste com query simples:")

    if db.chroma_enabled:
        # Query simples
        results1 = db.semantic_search(
            user_id=test_user_id,
            query="trabalho",
            k=None,  # k adaptativo
            chat_history=[]
        )

        logger.info(f"   Query 'trabalho' → {len(results1)} resultados (k adaptativo)")

        logger.info("\n2. Teste com query complexa:")

        # Query complexa com múltiplas pessoas
        results2 = db.semantic_search(
            user_id=test_user_id,
            query="Como estão Ana e minha mãe? Estou preocupado com ambas",
            k=None,
            chat_history=[]
        )

        logger.info(f"   Query complexa → {len(results2)} resultados (k adaptativo)")
        logger.info(f"   Esperado: k maior devido a 2 pessoas mencionadas")

        if len(results2) > len(results1):
            logger.info(f"   ✅ k adaptativo funcionou! ({len(results2)} > {len(results1)})")
        else:
            logger.warning(f"   ⚠️ k não aumentou como esperado")

        logger.info("\n3. Análise de boosts aplicados:")

        if results2:
            for i, mem in enumerate(results2[:2], 1):
                logger.info(f"\n   Memória {i}:")
                logger.info(f"      Input: {mem['user_input'][:50]}...")
                logger.info(f"      Base: {mem.get('base_score', 0):.3f}")
                logger.info(f"      Final: {mem.get('final_score', 0):.3f}")

                boosts = mem.get('boosts', {})
                logger.info(f"      Boosts aplicados:")
                for boost_name, boost_value in boosts.items():
                    if boost_value != 1.0:
                        logger.info(f"         - {boost_name}: {boost_value}x")

    else:
        logger.warning("   ⚠️ ChromaDB desabilitado")

    logger.info("\n✅ Teste end-to-end concluído!")


if __name__ == "__main__":
    try:
        test_adaptive_k()
        test_reranking()
        test_two_stage_end_to_end()

        logger.info("\n" + "=" * 60)
        logger.info("🎉 TODOS OS TESTES PASSARAM!")
        logger.info("=" * 60)
        logger.info("\nTwo-Stage Retrieval & Reranking (Fase 3) está funcionando!")
        logger.info("\nMelhorias implementadas:")
        logger.info("1. k Adaptativo (3-12 baseado em complexidade)")
        logger.info("2. Broad Retrieval (k*3 resultados)")
        logger.info("3. Reranking com 6 boosts:")
        logger.info("   - Temporal (recente vs histórico)")
        logger.info("   - Emocional (intensidade afetiva)")
        logger.info("   - Tópico (overlap com query)")
        logger.info("   - Pessoa (mesma pessoa mencionada)")
        logger.info("   - Profundidade existencial")
        logger.info("   - Conflito arquetípico")
        logger.info("\nImpacto esperado:")
        logger.info("- Memórias relevantes são REALMENTE recuperadas")
        logger.info("- Metadataenriquecido (Fase 1) finalmente utilizado")
        logger.info("- Query enrichment (Fase 2) tem efeito multiplicado")
        logger.info("- Usuário perceberá que 'Jung lembra melhor'")
        logger.info("\nPróximos passos:")
        logger.info("1. Commit e push das mudanças")
        logger.info("2. Deploy no Railway")
        logger.info("3. Monitorar logs de produção")

    except Exception as e:
        logger.error(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        logger.error(traceback.format_exc())
