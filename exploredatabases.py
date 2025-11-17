# explore_databases.py
"""
Explorador de Bases de Dados - Jung Claude
Analisa ChromaDB e SQLite para documentar estrutura real
"""

import sqlite3
import chromadb
from pathlib import Path
import json
from datetime import datetime

print("=" * 80)
print("🔍 EXPLORADOR DE BASES DE DADOS - JUNG CLAUDE")
print("=" * 80)

# ============================================================================
# 1. EXPLORAR SQLITE (agent_development.db)
# ============================================================================

print("\n📊 EXPLORANDO SQLite: agent_development.db")
print("-" * 80)

sqlite_path = Path("agent_development.db")

if not sqlite_path.exists():
    print("❌ Arquivo agent_development.db NÃO ENCONTRADO")
else:
    print(f"✅ Arquivo encontrado: {sqlite_path.absolute()}")
    
    conn = sqlite3.connect(str(sqlite_path))
    cursor = conn.cursor()
    
    # Listar todas as tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"\n📋 Total de tabelas: {len(tables)}")
    print("\nTABELAS ENCONTRADAS:")
    for table in tables:
        print(f"  • {table[0]}")
    
    print("\n" + "=" * 80)
    
    # Para cada tabela, mostrar estrutura completa
    for table in tables:
        table_name = table[0]
        
        print(f"\n📊 TABELA: {table_name}")
        print("-" * 80)
        
        # Estrutura (colunas)
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        print("\n🔹 ESTRUTURA (Colunas):")
        for col in columns:
            col_id, col_name, col_type, not_null, default, pk = col
            nullable = "NOT NULL" if not_null else "NULL"
            primary = "PRIMARY KEY" if pk else ""
            print(f"  {col_id}. {col_name:25} {col_type:15} {nullable:10} {primary}")
        
        # Total de registros
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"\n📈 Total de registros: {count}")
        
        # Amostra de dados (primeiros 3 registros)
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            rows = cursor.fetchall()
            
            print(f"\n🔍 AMOSTRA DE DADOS (primeiros {len(rows)} registros):")
            
            col_names = [col[1] for col in columns]
            
            for i, row in enumerate(rows, 1):
                print(f"\n  Registro {i}:")
                for col_name, value in zip(col_names, row):
                    # Truncar valores muito longos
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"    {col_name}: {value}")
        
        print("\n" + "=" * 80)
    
    conn.close()

# ============================================================================
# 2. EXPLORAR CHROMADB (chroma_db/)
# ============================================================================

print("\n\n🗄️ EXPLORANDO ChromaDB: chroma_db/")
print("-" * 80)

chroma_dir = Path("chroma_db")

if not chroma_dir.exists():
    print("❌ Diretório chroma_db/ NÃO ENCONTRADO")
else:
    print(f"✅ Diretório encontrado: {chroma_dir.absolute()}")
    
    try:
        client = chromadb.PersistentClient(path=str(chroma_dir))
        
        # Listar coleções
        collections = client.list_collections()
        
        print(f"\n📚 Total de coleções: {len(collections)}")
        
        for collection_obj in collections:
            print(f"\n📦 COLEÇÃO: {collection_obj.name}")
            print("-" * 80)
            
            collection = client.get_collection(name=collection_obj.name)
            
            # Total de documentos
            total_docs = collection.count()
            print(f"📈 Total de documentos: {total_docs}")
            
            if total_docs > 0:
                # Buscar todos os documentos (limitado a 10 para análise)
                sample_size = min(10, total_docs)
                results = collection.get(limit=sample_size, include=["documents", "metadatas"])
                
                print(f"\n🔍 AMOSTRA DE DOCUMENTOS (primeiros {sample_size}):")
                
                # Analisar metadados para descobrir estrutura
                if results['metadatas']:
                    print("\n🔹 ESTRUTURA DE METADADOS:")
                    
                    # Coletar todas as chaves de metadados
                    all_keys = set()
                    for metadata in results['metadatas']:
                        all_keys.update(metadata.keys())
                    
                    print(f"  Campos disponíveis: {sorted(all_keys)}")
                    
                    # Mostrar exemplos de metadados
                    print("\n🔹 EXEMPLOS DE METADADOS:")
                    for i, metadata in enumerate(results['metadatas'][:3], 1):
                        print(f"\n  Documento {i}:")
                        for key, value in metadata.items():
                            if isinstance(value, str) and len(value) > 100:
                                value = value[:100] + "..."
                            print(f"    {key}: {value}")
                
                # Mostrar exemplos de documentos
                print("\n🔹 EXEMPLOS DE CONTEÚDO:")
                for i, doc in enumerate(results['documents'][:2], 1):
                    print(f"\n  Documento {i}:")
                    # Mostrar apenas primeiros 300 caracteres
                    preview = doc[:300] + "..." if len(doc) > 300 else doc
                    print(f"    {preview}")
                
                print("\n" + "=" * 80)
                
                # Estatísticas extras
                print("\n📊 ESTATÍSTICAS:")
                
                # Usuários únicos
                user_ids = set()
                for metadata in results['metadatas']:
                    if 'user_id' in metadata:
                        user_ids.add(metadata['user_id'])
                
                print(f"  Usuários únicos (amostra): {len(user_ids)}")
                
                # Tipos de campos
                print("\n  Tipos de campos nos metadados:")
                if results['metadatas']:
                    first_metadata = results['metadatas'][0]
                    for key, value in first_metadata.items():
                        print(f"    {key}: {type(value).__name__}")
        
    except Exception as e:
        print(f"❌ ERRO ao acessar ChromaDB: {e}")

# ============================================================================
# 3. RESUMO E RECOMENDAÇÕES
# ============================================================================

print("\n\n" + "=" * 80)
print("📝 RESUMO DA EXPLORAÇÃO")
print("=" * 80)

print("""
Com base na exploração acima, agora sabemos:

1. **SQLite - Tabelas disponíveis:**
   - Listar todas as tabelas encontradas
   - Estrutura exata de cada tabela (colunas, tipos)
   - Quantidade de dados em cada tabela

2. **ChromaDB - Estrutura de dados:**
   - Campos disponíveis nos metadados
   - Formato dos documentos armazenados
   - Informações de usuários

3. **Próximos passos:**
   - Use essas informações para construir admin.py corretamente
   - Adapte queries SQL para os nomes de colunas reais
   - Configure filtros ChromaDB baseados nos metadados reais
""")

print("\n" + "=" * 80)
print("✅ Exploração concluída!")
print("=" * 80)