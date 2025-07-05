#!/usr/bin/env python3
"""
Script de instalação automática das dependências do Jung Claude System v1.0
VERSÃO CORRIGIDA - sem problemas de aspas
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Executa comando e trata erros"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Sucesso")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Erro:")
        print(f"   Comando: {command}")
        print(f"   Stderr: {e.stderr}")
        return False

def check_python_version():
    """Verifica versão do Python"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ é necessário!")
        print(f"   Versão atual: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} - OK")
    return True

def install_package(package_name, description=None):
    """Instala um pacote específico"""
    if description is None:
        description = f"Instalando {package_name}"
    
    # Comando sem aspas problemáticas
    command = f"pip install {package_name}"
    return run_command(command, description)

def check_package_installed(package_name):
    """Verifica se um pacote está instalado"""
    try:
        if package_name == "yaml":
            import yaml
        elif package_name == "streamlit":
            import streamlit
        elif package_name == "pydantic":
            import pydantic
        elif package_name == "pandas":
            import pandas
        elif package_name == "numpy":
            import numpy
        elif package_name == "aiofiles":
            import aiofiles
        elif package_name == "tenacity":
            import tenacity
        else:
            __import__(package_name.replace("-", "_"))
        return True
    except ImportError:
        return False

def install_dependencies():
    """Instala todas as dependências"""
    print("🧠 Jung Claude System v1.0 - Instalação de Dependências")
    print("=" * 60)
    
    # 1. Verificar Python
    if not check_python_version():
        return False
    
    # 2. Atualizar pip
    print("\n🔧 Atualizando pip...")
    if not run_command("python -m pip install --upgrade pip", "Atualizando pip"):
        print("⚠️ Falha ao atualizar pip - continuando...")
    
    # 3. Lista de pacotes essenciais com versões específicas
    essential_packages = [
        # Interface Web
        ("streamlit>=1.28.0", "streamlit", "Interface web principal"),
        ("pyyaml>=6.0", "yaml", "Processamento de arquivos YAML"),
        ("pydantic>=2.0.0", "pydantic", "Validação de dados"),
        
        # Dados
        ("pandas>=2.0.0", "pandas", "Manipulação de dados"),
        ("numpy>=1.24.0", "numpy", "Computação numérica"),
        
        # Performance
        ("aiofiles>=23.0.0", "aiofiles", "Operações de arquivo assíncronas"),
        ("tenacity>=8.0.0", "tenacity", "Retry automático"),
    ]
    
    # 4. Verificar e instalar pacotes essenciais
    print("\n📦 Instalando pacotes essenciais...")
    failed_packages = []
    
    for package_spec, import_name, description in essential_packages:
        package_name = package_spec.split(">=")[0]
        
        print(f"\n🔍 Verificando {package_name}...")
        
        if check_package_installed(import_name):
            print(f"✅ {package_name} - Já instalado")
        else:
            print(f"📦 Instalando {package_name}...")
            if install_package(package_spec, description):
                print(f"✅ {package_name} - Instalado com sucesso")
            else:
                print(f"❌ {package_name} - Falha na instalação")
                failed_packages.append(package_name)
    
    # 5. Pacotes opcionais (desenvolvimento)
    optional_packages = [
        ("pytest>=7.0.0", "pytest", "Framework de testes"),
        ("pytest-asyncio>=0.21.0", "pytest_asyncio", "Testes assíncronos"),
        ("black>=23.0.0", "black", "Formatação de código"),
        ("isort>=5.12.0", "isort", "Organização de imports"),
    ]
    
    print("\n🧪 Instalando pacotes opcionais...")
    for package_spec, import_name, description in optional_packages:
        package_name = package_spec.split(">=")[0]
        
        if not check_package_installed(import_name):
            print(f"📦 Instalando {package_name} (opcional)...")
            install_package(package_spec, description)
        else:
            print(f"✅ {package_name} - Já instalado")
    
    # 6. Verificar core packages (que já devemos ter)
    core_packages = [
        ("anthropic", "anthropic"),
        ("openai", "openai"),
        ("langchain", "langchain"),
        ("chromadb", "chromadb"),
        ("python-dotenv", "dotenv"),
    ]
    
    print("\n🔧 Verificando bibliotecas principais...")
    missing_core = []
    
    for package_name, import_name in core_packages:
        if check_package_installed(import_name):
            print(f"✅ {package_name} - OK")
        else:
            print(f"⚠️ {package_name} - AUSENTE")
            missing_core.append(package_name)
    
    if missing_core:
        print(f"\n⚠️ Bibliotecas principais ausentes: {', '.join(missing_core)}")
        print("💡 Instale-as manualmente se necessário")
    
    # 7. Resumo
    print("\n" + "=" * 60)
    if failed_packages:
        print(f"⚠️ Alguns pacotes falharam: {', '.join(failed_packages)}")
        return False
    else:
        print("✅ Todas as novas dependências foram instaladas!")
        return True

def verify_streamlit():
    """Testa especificamente o Streamlit"""
    print("\n🌐 Testando Streamlit...")
    try:
        import streamlit as st
        print(f"✅ Streamlit {st.__version__} - OK")
        
        # Teste adicional
        test_command = "streamlit --version"
        result = subprocess.run(test_command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Streamlit CLI - OK")
            print(f"   Versão: {result.stdout.strip()}")
        else:
            print("⚠️ Streamlit CLI pode ter problemas")
        
        return True
    except ImportError as e:
        print(f"❌ Streamlit - ERRO: {e}")
        return False

def create_quick_test():
    """Cria script de teste rápido"""
    test_script = '''#!/usr/bin/env python3
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
    
    print(f"\\n📊 Resultado: {success_count}/{len(tests)} imports funcionaram")
    
    if success_count == len(tests):
        print("🎉 Todas as dependências estão funcionando!")
        return True
    else:
        print("⚠️ Algumas dependências têm problemas")
        return False

if __name__ == "__main__":
    if test_imports():
        print("\\n🚀 Sistema pronto para uso!")
        print("Execute: python main.py --interface web")
    else:
        print("\\n💡 Execute o script de instalação novamente")
'''
    
    with open("test_installation.py", "w", encoding="utf-8") as f:
        f.write(test_script)
    
    print("📄 Script de teste criado: test_installation.py")

def main():
    """Função principal"""
    success = install_dependencies()
    
    # Teste específico do Streamlit
    streamlit_ok = verify_streamlit()
    
    # Criar script de teste
    create_quick_test()
    
    print("\n" + "=" * 60)
    if success and streamlit_ok:
        print("🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
        print("\n✅ Todas as dependências estão instaladas")
        print("✅ Streamlit está funcionando")
        print("✅ Sistema pronto para uso")
        
        print("\n🧪 Para testar:")
        print("   python test_installation.py")
        
        print("\n🚀 Para iniciar o sistema:")
        print("   python main.py --interface web")
        
    else:
        print("⚠️ PROBLEMAS NA INSTALAÇÃO")
        print("\n💡 Tente as instalações manuais abaixo:")
        print("   pip install streamlit")
        print("   pip install pyyaml")
        print("   pip install pydantic")
        print("   pip install pandas")
        print("   pip install numpy")
        print("   pip install aiofiles")
        print("   pip install tenacity")

if __name__ == "__main__":
    main()