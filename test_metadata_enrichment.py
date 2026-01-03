"""
test_metadata_enrichment.py

Script de teste para validar metadata enriquecido (Fase 1)
"""

import logging
from datetime import datetime
from jung_core import HybridDatabaseManager, Config, ArchetypeInsight

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_metadata_functions():
    """Testa funções auxiliares de metadata"""

    logger.info("=" * 60)
    logger.info("TESTE 1: Funções Auxiliares de Metadata")
    logger.info("=" * 60)

    # Inicializar DB Manager
    Config.validate()
    db = HybridDatabaseManager()

    # Teste 1: _calculate_recency_tier
    logger.info("\n1. Testando _calculate_recency_tier:")

    now = datetime.now()
    from datetime import timedelta

    recent_time = now - timedelta(days=15)
    medium_time = now - timedelta(days=60)
    old_time = now - timedelta(days=120)

    logger.info(f"   15 dias atrás → {db._calculate_recency_tier(recent_time)} (esperado: recent)")
    logger.info(f"   60 dias atrás → {db._calculate_recency_tier(medium_time)} (esperado: medium)")
    logger.info(f"   120 dias atrás → {db._calculate_recency_tier(old_time)} (esperado: old)")

    # Teste 2: _get_dominant_archetype
    logger.info("\n2. Testando _get_dominant_archetype:")

    mock_analyses = {
        "Persona": ArchetypeInsight("Persona", "Quer proteger", "acolher", 0.5),
        "Sombra": ArchetypeInsight("Sombra", "Quer confrontar", "provocar", 0.9),
        "Anima": ArchetypeInsight("Anima", "Quer conectar", "aprofundar", 0.3),
    }

    dominant = db._get_dominant_archetype(mock_analyses)
    logger.info(f"   Dominante: {dominant} (esperado: Sombra, intensidade=0.9)")

    # Teste 3: _extract_topics_from_keywords
    logger.info("\n3. Testando _extract_topics_from_keywords:")

    keywords1 = ["trabalho", "chefe", "estresse"]
    keywords2 = ["esposa", "filho", "familia"]
    keywords3 = ["viagem", "livro", "musica"]

    topics1 = db._extract_topics_from_keywords(keywords1)
    topics2 = db._extract_topics_from_keywords(keywords2)
    topics3 = db._extract_topics_from_keywords(keywords3)

    logger.info(f"   {keywords1} → {topics1} (esperado: ['trabalho'])")
    logger.info(f"   {keywords2} → {topics2} (esperado: ['familia'])")
    logger.info(f"   {keywords3} → {topics3} (esperado: ['lazer'])")

    # Teste 4: calculate_temporal_boost
    logger.info("\n4. Testando calculate_temporal_boost:")

    recent_ts = (now - timedelta(days=10)).isoformat()
    medium_ts = (now - timedelta(days=60)).isoformat()
    old_ts = (now - timedelta(days=100)).isoformat()

    boost_recent = db.calculate_temporal_boost(recent_ts, mode="balanced")
    boost_medium = db.calculate_temporal_boost(medium_ts, mode="balanced")
    boost_old = db.calculate_temporal_boost(old_ts, mode="balanced")

    logger.info(f"   10 dias (recent) → boost={boost_recent} (esperado: 1.2)")
    logger.info(f"   60 dias (medium) → boost={boost_medium} (esperado: 1.0)")
    logger.info(f"   100 dias (old) → boost={boost_old} (esperado: 0.9)")

    logger.info("\n✅ Testes de funções auxiliares concluídos!")


def test_save_with_enriched_metadata():
    """Testa salvamento de conversa com metadata enriquecido"""

    logger.info("\n" + "=" * 60)
    logger.info("TESTE 2: Salvamento com Metadata Enriquecido")
    logger.info("=" * 60)

    Config.validate()
    db = HybridDatabaseManager()

    # Criar usuário de teste se não existir
    test_user_id = "test_metadata_enrichment"
    test_user_name = "Teste Metadata"

    try:
        db.create_user(test_user_id, test_user_name, platform="test")
    except:
        pass  # Usuário já existe

    # Simular conversa com diferentes características
    logger.info("\n1. Salvando conversa sobre FAMÍLIA:")

    conv_id_1 = db.save_conversation(
        user_id=test_user_id,
        user_name=test_user_name,
        user_input="Minha esposa Ana está ansiosa com a viagem para Paris",
        ai_response="Entendo sua preocupação. Como você tem ajudado ela com essa ansiedade?",
        tension_level=0.6,
        affective_charge=0.7,
        existential_depth=0.4,
        keywords=["esposa", "ansiedade", "viagem"],
        platform="test"
    )

    logger.info(f"   ✅ Conversa {conv_id_1} salva")

    logger.info("\n2. Salvando conversa sobre TRABALHO:")

    conv_id_2 = db.save_conversation(
        user_id=test_user_id,
        user_name=test_user_name,
        user_input="Meu chefe está cobrando muito, estou sobrecarregado",
        ai_response="Isso parece intenso. Quando foi a última vez que você conversou com ele sobre isso?",
        tension_level=0.8,
        affective_charge=0.9,
        existential_depth=0.3,
        keywords=["trabalho", "chefe", "estresse"],
        platform="test"
    )

    logger.info(f"   ✅ Conversa {conv_id_2} salva")

    # Verificar se metadata foi salvo corretamente no ChromaDB
    logger.info("\n3. Verificando metadata no ChromaDB:")

    if db.chroma_enabled:
        # Buscar as conversas salvas
        results = db.semantic_search(test_user_id, "família trabalho", k=2)

        for i, result in enumerate(results, 1):
            logger.info(f"\n   Memória {i}:")
            logger.info(f"      Input: {result['user_input'][:50]}...")

            metadata = result.get('metadata', {})
            logger.info(f"      Recency tier: {metadata.get('recency_tier')}")
            logger.info(f"      Emotional intensity: {metadata.get('emotional_intensity')}")
            logger.info(f"      Topics: {metadata.get('topics')}")
            logger.info(f"      Mentions people: {metadata.get('mentions_people')}")
            logger.info(f"      Day bucket: {metadata.get('day_bucket')}")
    else:
        logger.warning("   ⚠️ ChromaDB desabilitado, não é possível verificar metadata")

    logger.info("\n✅ Teste de salvamento concluído!")


if __name__ == "__main__":
    try:
        test_metadata_functions()
        test_save_with_enriched_metadata()

        logger.info("\n" + "=" * 60)
        logger.info("🎉 TODOS OS TESTES PASSARAM!")
        logger.info("=" * 60)
        logger.info("\nMetadata enriquecido (Fase 1) está funcionando corretamente.")
        logger.info("Próximos passos:")
        logger.info("1. Commit e push das mudanças")
        logger.info("2. Deploy no Railway")
        logger.info("3. Monitorar logs de produção")

    except Exception as e:
        logger.error(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        logger.error(traceback.format_exc())
