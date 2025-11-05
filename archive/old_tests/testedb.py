import agent_development_db as dev_db
import os

print("🔍 Testando criação do banco de dados...")
print(f"📁 Diretório atual: {os.getcwd()}")
print(f"📄 Arquivo DB esperado: {dev_db.DB_PATH}")

# Verificar se arquivo existe ANTES
if os.path.exists(dev_db.DB_PATH):
    print(f"✅ Arquivo {dev_db.DB_PATH} já existe")
else:
    print(f"❌ Arquivo {dev_db.DB_PATH} NÃO existe ainda")

# Tentar inicializar
print("\n🚀 Inicializando banco de dados...")
try:
    dev_db.init_database()
    print("✅ init_database() executado com sucesso")
except Exception as e:
    print(f"❌ ERRO ao inicializar: {e}")
    import traceback
    traceback.print_exc()

# Verificar se arquivo existe DEPOIS
print("\n🔍 Verificando criação...")
if os.path.exists(dev_db.DB_PATH):
    size = os.path.getsize(dev_db.DB_PATH)
    print(f"✅ Arquivo {dev_db.DB_PATH} CRIADO com sucesso! ({size} bytes)")
else:
    print(f"❌ Arquivo {dev_db.DB_PATH} ainda NÃO existe!")

# Testar leitura do estado
print("\n📊 Testando leitura do estado...")
try:
    state = dev_db.get_agent_state()
    print(f"✅ Estado lido com sucesso:")
    print(f"   Fase: {state['phase']}")
    print(f"   Interações: {state['total_interactions']}")
    print(f"   Auto-consciência: {state['self_awareness_score']}")
except Exception as e:
    print(f"❌ ERRO ao ler estado: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Teste concluído!")