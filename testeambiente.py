"""
Script para testar a instalação híbrida
"""
import os
import asyncio
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

async def test_hybrid_setup():
    """Testa se a configuração híbrida está funcionando"""
    print("🔧 TESTANDO CONFIGURAÇÃO HÍBRIDA")
    print("=" * 50)
    
    # 1. Testar importações
    print("📦 Testando importações...")
    try:
        from langchain_openai import OpenAIEmbeddings
        from langchain_anthropic import ChatAnthropic
        from langchain_chroma import Chroma
        print("✅ Todas as bibliotecas importadas com sucesso")
    except ImportError as e:
        print(f"❌ Erro na importação: {e}")
        return False
    
    # 2. Testar chaves de API
    print("\n🔑 Testando chaves de API...")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not openai_key:
        print("❌ OPENAI_API_KEY não encontrada")
        return False
    else:
        print("✅ OPENAI_API_KEY encontrada")
    
    if not anthropic_key:
        print("❌ ANTHROPIC_API_KEY não encontrada")
        return False
    else:
        print("✅ ANTHROPIC_API_KEY encontrada")
    
    # 3. Testar OpenAI Embeddings
    print("\n🔢 Testando OpenAI Embeddings...")
    try:
        embeddings = OpenAIEmbeddings()
        test_embedding = await embeddings.aembed_query("teste")
        print(f"✅ Embedding gerado: {len(test_embedding)} dimensões")
    except Exception as e:
        print(f"❌ Erro no OpenAI Embeddings: {e}")
        return False
    
    # 4. Testar Claude
    print("\n🤖 Testando Claude...")
    try:
        claude = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            anthropic_api_key=anthropic_key,
            max_tokens=100
        )
        
        response = await claude.ainvoke("Diga apenas: 'Claude funcionando!'")
        print(f"✅ Claude respondeu: {response.content}")
    except Exception as e:
        print(f"❌ Erro no Claude: {e}")
        return False
    
    # 5. Testar ChromaDB
    print("\n🗃️ Testando ChromaDB...")
    try:
        vectorstore = Chroma(
            persist_directory="./test_chroma",
            embedding_function=embeddings
        )
        print("✅ ChromaDB inicializado com sucesso")
        
        # Limpar teste
        import shutil
        if os.path.exists("./test_chroma"):
            shutil.rmtree("./test_chroma")
            
    except Exception as e:
        print(f"❌ Erro no ChromaDB: {e}")
        return False
    
    print("\n🎉 TODOS OS TESTES PASSARAM!")
    print("Sistema híbrido pronto para uso:")
    print("  🔢 OpenAI → Embeddings (busca de memórias)")
    print("  🧠 Claude → Respostas (arquétipos e síntese)")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_hybrid_setup())