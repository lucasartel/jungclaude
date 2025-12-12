"""
Script para baixar dados do Railway para análise local
"""
import requests
import json
from getpass import getpass

# URL do Railway
RAILWAY_URL = input("Digite a URL do Railway (ex: https://seu-projeto.railway.app): ").strip()
if not RAILWAY_URL.startswith('http'):
    RAILWAY_URL = f"https://{RAILWAY_URL}"

# Credenciais admin
print("\n🔐 Autenticação Admin")
username = input("Username: ")
password = getpass("Password: ")

auth = (username, password)

# Criar sessão
session = requests.Session()
session.auth = auth

print("\n📥 Baixando dados do Railway...\n")

# 1. Baixar fragmentos
print("1️⃣ Baixando fragmentos...")
try:
    response = session.get(f"{RAILWAY_URL}/admin/api/jung-lab/export-fragments")
    response.raise_for_status()
    fragments_data = response.json()

    with open("railway_fragments.json", "w", encoding="utf-8") as f:
        json.dump(fragments_data, f, indent=2, ensure_ascii=False)

    print(f"   ✅ {fragments_data['total']} fragmentos baixados → railway_fragments.json")
except Exception as e:
    print(f"   ❌ Erro ao baixar fragmentos: {e}")

# 2. Baixar tensões
print("\n2️⃣ Baixando tensões...")
try:
    response = session.get(f"{RAILWAY_URL}/admin/api/jung-lab/export-tensions")
    response.raise_for_status()
    tensions_data = response.json()

    with open("railway_tensions.json", "w", encoding="utf-8") as f:
        json.dump(tensions_data, f, indent=2, ensure_ascii=False)

    print(f"   ✅ {tensions_data['total']} tensões baixadas → railway_tensions.json")
except Exception as e:
    print(f"   ❌ Erro ao baixar tensões: {e}")

# 3. Baixar insights
print("\n3️⃣ Baixando insights...")
try:
    response = session.get(f"{RAILWAY_URL}/admin/api/jung-lab/export-insights")
    response.raise_for_status()
    insights_data = response.json()

    with open("railway_insights.json", "w", encoding="utf-8") as f:
        json.dump(insights_data, f, indent=2, ensure_ascii=False)

    print(f"   ✅ {insights_data['total']} insights baixados → railway_insights.json")
except Exception as e:
    print(f"   ❌ Erro ao baixar insights: {e}")

# 4. Baixar diagnóstico
print("\n4️⃣ Baixando diagnóstico completo...")
try:
    response = session.get(f"{RAILWAY_URL}/admin/api/jung-lab/why-no-insights")
    response.raise_for_status()
    diagnosis_data = response.json()

    with open("railway_diagnosis.json", "w", encoding="utf-8") as f:
        json.dump(diagnosis_data, f, indent=2, ensure_ascii=False)

    print(f"   ✅ Diagnóstico baixado → railway_diagnosis.json")

    # Mostrar resumo do diagnóstico
    print("\n" + "="*80)
    print("📊 RESUMO DO DIAGNÓSTICO")
    print("="*80)

    if "problem_identified" in diagnosis_data and diagnosis_data["problem_identified"]:
        print(f"\n🐛 PROBLEMA: {diagnosis_data['problem_identified']}")

    if "tensions" in diagnosis_data and len(diagnosis_data["tensions"]) > 0:
        print(f"\n⚡ TENSÕES ENCONTRADAS: {len(diagnosis_data['tensions'])}")
        for idx, t in enumerate(diagnosis_data["tensions"][:3], 1):
            print(f"\n   Tensão #{idx}:")
            print(f"   - Tipo: {t.get('type')}")
            print(f"   - Status: {t.get('status')}")
            print(f"   - Maturidade: {t.get('maturity', {}).get('score', 0):.2f} / {t.get('maturity', {}).get('needed', 0):.2f}")
            print(f"   - Evidências: {t.get('evidence', {}).get('count', 0)} / {t.get('evidence', {}).get('needed', 0)}")
            print(f"   - Idade: {t.get('days_old', 0)} dias")

            if "blocking_factors" in t and len(t["blocking_factors"]) > 0:
                print(f"   - Bloqueios:")
                for block in t["blocking_factors"]:
                    print(f"     • {block}")

    print("\n" + "="*80)

except Exception as e:
    print(f"   ❌ Erro ao baixar diagnóstico: {e}")

print("\n✅ Download concluído!")
print("\nArquivos gerados:")
print("  - railway_fragments.json")
print("  - railway_tensions.json")
print("  - railway_insights.json")
print("  - railway_diagnosis.json")
