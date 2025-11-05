#!/usr/bin/env python3
"""
Teste rápido das dependências instaladas
"""

def test_imports():
    """Testa todos os imports necessários"""
    tests = [
        ("streamlit", "Interface web"),
        ("yaml", "Configuração YAML"),
        ("pydantic", "Validação de dados"),
        ("pandas", "Manipulação de dados"),
        ("numpy", "Computação numérica"),
        ("aiofiles", "Operações assíncronas"),
        ("tenacity", "Retry automático"),
    ]
    
    print("🧪 Testando imports das novas dependências...")
    
    success_count = 0
    for module, description in tests:
        try:
            if module == "yaml":
                import yaml
            else:
                __import__(module)
            print(f"✅ {module} ({description}) - OK")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module} ({description}) - ERRO: {e}")
    
    print(f"\n📊 Resultado: {success_count}/{len(tests)} imports funcionaram")
    
    if success_count == len(tests):
        print("🎉 Todas as dependências estão funcionando!")
        return True
    else:
        print("⚠️ Algumas dependências têm problemas")
        return False

if __name__ == "__main__":
    if test_imports():
        print("\n🚀 Sistema pronto para uso!")
        print("Execute: python main.py --interface web")
    else:
        print("\n💡 Execute o script de instalação novamente")
