#!/usr/bin/env python3
"""
test_memoria_profunda.py - Teste do Sistema de Memória Profunda V2
==================================================================

Testa extração inteligente com Claude nas 6 categorias:
1. RELACIONAMENTO (expandido)
2. TRABALHO (expandido)
3. PERSONALIDADE (expandido)
4. DESAFIOS (novo)
5. PREFERENCIAS (novo)
6. MOMENTOS (novo)

Autor: Sistema Jung
Data: 2025-12-20
"""

import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_extraction():
    """Testa extração de fatos nas 6 categorias"""

    # Importar LLM Fact Extractor
    try:
        import anthropic
        from llm_fact_extractor import LLMFactExtractor

        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            logger.error("❌ ANTHROPIC_API_KEY não configurada")
            return False

        # Inicializar Claude
        client = anthropic.Anthropic(api_key=anthropic_key)
        extractor = LLMFactExtractor(
            llm_client=client,
            model="claude-sonnet-4-5-20250929"
        )

        logger.info("✅ LLM Fact Extractor inicializado (Claude Sonnet 4.5)")

    except Exception as e:
        logger.error(f"❌ Erro ao inicializar: {e}")
        return False

    # ========================================
    # CASOS DE TESTE - 6 CATEGORIAS
    # ========================================

    test_cases = [
        {
            "categoria": "RELACIONAMENTO (expandido)",
            "mensagem": "Minha esposa Jucinei faz aniversário dia 15 de março, ela é professora e é meu porto seguro",
            "esperado": ["esposa.nome=Jucinei", "esposa.aniversario=15/03", "esposa.profissao=professora", "esposa.dinamica"]
        },
        {
            "categoria": "TRABALHO (expandido)",
            "mensagem": "Trabalho como designer na Google há 3 anos, gosto mas é muito estressante, quero virar senior logo",
            "esperado": ["profissao=designer", "empresa=Google", "tempo=3 anos", "satisfacao=estressante", "objetivo=senior"]
        },
        {
            "categoria": "PERSONALIDADE (expandido)",
            "mensagem": "Sou muito introvertido, família é tudo para mim, acredito bastante em terapia e faço acompanhamento",
            "esperado": ["traço=introvertido", "valor=familia", "crenca=terapia"]
        },
        {
            "categoria": "DESAFIOS (novo)",
            "mensagem": "Tenho insônia há 3 meses por causa do estresse no trabalho, já tentei meditação mas não ajudou muito",
            "esperado": ["insonia.tipo=saude_mental", "insonia.inicio=3 meses", "insonia.gatilho=estresse", "tentativa_solucao=meditação"]
        },
        {
            "categoria": "PREFERENCIAS (novo)",
            "mensagem": "Adoro ler ficção científica antes de dormir, Isaac Asimov é meu favorito, me ajuda a relaxar e desligar da rotina",
            "esperado": ["leitura.genero=ficção científica", "frequencia=antes de dormir", "autor_favorito=Asimov", "beneficio=relaxar"]
        },
        {
            "categoria": "MOMENTOS (novo)",
            "mensagem": "Vou viajar para Paris em janeiro, primeira vez na Europa, estou muito ansioso mas empolgado!",
            "esperado": ["viagem.data=janeiro", "tipo=lazer", "planejamento=primeira vez", "sentimento=ansioso"]
        },
        {
            "categoria": "MÚLTIPLAS CATEGORIAS (integração)",
            "mensagem": "Meu filho João de 12 anos está com dificuldade na escola, isso me deixa ansioso. Tento ajudar nas lições mas fico frustrado às vezes.",
            "esperado": ["filho.nome=João", "filho.idade=12", "DESAFIOS", "PERSONALIDADE"]
        }
    ]

    # ========================================
    # EXECUTAR TESTES
    # ========================================

    print("="*80)
    print("TESTE DO SISTEMA DE MEMÓRIA PROFUNDA V2")
    print("="*80)
    print(f"Total de casos de teste: {len(test_cases)}\n")

    success_count = 0
    total_facts_extracted = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TESTE {i}/{len(test_cases)}: {test_case['categoria']}")
        print(f"{'='*80}")
        print(f"Mensagem: \"{test_case['mensagem']}\"")
        print(f"Esperado extrair: {', '.join(test_case['esperado'])}")
        print()

        try:
            # Extrair fatos
            facts = extractor.extract_facts(test_case["mensagem"])

            if facts:
                print(f"[OK] Extraidos {len(facts)} fatos:")
                total_facts_extracted += len(facts)

                for j, fact in enumerate(facts, 1):
                    print(f"   {j}. {fact.category}.{fact.fact_type}.{fact.attribute} = \"{fact.value}\"")
                    print(f"      Confianca: {fact.confidence:.2f} | Metodo: LLM")
                    print(f"      Contexto: \"{fact.context[:60]}...\"" if len(fact.context) > 60 else f"      Contexto: \"{fact.context}\"")

                success_count += 1
                print(f"\n[OK] TESTE {i} PASSOU")
            else:
                print(f"[ERRO] Nenhum fato extraido!")
                print(f"[ERRO] TESTE {i} FALHOU")

        except Exception as e:
            print(f"[ERRO] Erro na extracao: {e}")
            print(f"[ERRO] TESTE {i} FALHOU")
            import traceback
            print(traceback.format_exc())

    # ========================================
    # RESUMO FINAL
    # ========================================

    print(f"\n{'='*80}")
    print("RESUMO DO TESTE")
    print(f"{'='*80}")
    print(f"Testes executados: {len(test_cases)}")
    print(f"Testes bem-sucedidos: {success_count}")
    print(f"Taxa de sucesso: {(success_count/len(test_cases)*100):.1f}%")
    print(f"Total de fatos extraídos: {total_facts_extracted}")
    print(f"Média de fatos por mensagem: {(total_facts_extracted/len(test_cases)):.1f}")

    if success_count == len(test_cases):
        print(f"\n🎉 TODOS OS TESTES PASSARAM!")
        print(f"✅ Sistema de Memória Profunda V2 está funcionando corretamente")
        return True
    else:
        print(f"\n⚠️ Alguns testes falharam ({len(test_cases) - success_count}/{len(test_cases)})")
        print(f"Revisar casos de falha acima")
        return False


if __name__ == "__main__":
    success = test_extraction()
    exit(0 if success else 1)
