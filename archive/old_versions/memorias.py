# explore_memories.py
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

def explore_chromadb():
    """Explorer completo do ChromaDB"""
    print("🔍 EXPLORADOR DE MEMÓRIAS DO CHROMADB")
    print("=" * 50)
    
    # Conectar ao ChromaDB
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )
    
    try:
        collection = vectorstore._collection
        # Garante que estamos buscando os IDs para a função de exclusão
        all_docs = collection.get(include=["metadatas", "documents"])
        
        if not all_docs or not all_docs.get('documents'):
            print("📭 ChromaDB vazio - nenhuma memória encontrada")
            return
        
        # Extrai todos os dados necessários
        ids = all_docs['ids']
        documents = all_docs['documents']
        metadatas = all_docs['metadatas']
        
        print(f"📊 Total de memórias: {len(documents)}")
        print()
        
        # Organizar por usuário
        users = {}
        for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
            user_id = metadata.get('user_id', 'unknown')
            user_name = metadata.get('user_name', 'Desconhecido')
            
            if user_id not in users:
                users[user_id] = {
                    'name': user_name,
                    'memories': []
                }
            
            # Adiciona o ID do documento, que será essencial para a exclusão
            users[user_id]['memories'].append({
                'id': ids[i],
                'document': doc,
                'metadata': metadata
            })
        
        # Mostrar resumo por usuário
        print("👥 USUÁRIOS NO CHROMADB:")
        for user_id, user_data in users.items():
            print(f"\n🔸 {user_data['name']} ({user_id})")
            print(f"   Memórias: {len(user_data['memories'])}")
            
            # Última interação
            last_memory = user_data['memories'][-1]
            last_timestamp = last_memory['metadata'].get('timestamp', 'N/A')
            print(f"   Última: {last_timestamp}")
        
        print("\n" + "=" * 50)
        
        # Menu interativo
        while True:
            print("\nOpções:")
            print("1. Ver todas as memórias")
            print("2. Ver memórias de um usuário")
            print("3. Buscar por palavra-chave")
            print("4. Estatísticas detalhadas")
            print("5. Exportar para JSON")
            print("6. Limpar memórias de um usuário") # Nova opção
            print("0. Sair")
            
            choice = input("\nEscolha uma opção: ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                show_all_memories(users)
            elif choice == "2":
                show_user_memories(users)
            elif choice == "3":
                search_memories(users)
            elif choice == "4":
                show_detailed_stats(users)
            elif choice == "5":
                export_to_json(users)
            elif choice == "6":
                # A função de exclusão precisa do vectorstore para executar a ação
                data_deleted = delete_user_memories(users, vectorstore)
                if data_deleted:
                    print("\n🔄 Dados alterados. Por favor, reinicie o script para carregar o estado atualizado.")
                    break # Encerra o loop para forçar a reinicialização
            else:
                print("❌ Opção inválida")
    
    except Exception as e:
        print(f"❌ Erro ao acessar ChromaDB: {e}")

def show_all_memories(users):
    """Mostra todas as memórias"""
    print("\n🧠 TODAS AS MEMÓRIAS:")
    print("=" * 70)
    
    for user_id, user_data in users.items():
        print(f"\n👤 {user_data['name']}:")
        
        for i, memory in enumerate(user_data['memories'], 1):
            metadata = memory['metadata']
            doc = memory['document']
            
            timestamp = metadata.get('timestamp', 'N/A')[:16]
            intensity = metadata.get('intensity_level', 'N/A')
            tension = metadata.get('tension_level', 'N/A')
            
            print(f"\n   {i}. [{timestamp}] Int: {intensity} | Tensão: {tension}")
            print(f"      {doc[:150]}...")
            
        print("-" * 70)

def show_user_memories(users):
    """Mostra memórias de usuário específico"""
    print("\n👥 Usuários disponíveis:")
    user_list = list(users.items())
    
    for i, (user_id, user_data) in enumerate(user_list, 1):
        print(f"{i}. {user_data['name']} ({len(user_data['memories'])} memórias)")
    
    try:
        choice = int(input("\nEscolha um usuário (número): ")) - 1
        if 0 <= choice < len(user_list):
            user_id, user_data = user_list[choice]
            
            print(f"\n🧠 MEMÓRIAS DE {user_data['name']}:")
            print("=" * 50)
            
            for i, memory in enumerate(user_data['memories'], 1):
                metadata = memory['metadata']
                doc = memory['document']
                
                print(f"\n{i}. MEMÓRIA [{metadata.get('timestamp', 'N/A')[:16]}]")
                print(f"   Intensidade: {metadata.get('intensity_level', 'N/A')}")
                print(f"   Tensão: {metadata.get('tension_level', 'N/A')}")
                print(f"   Arquétipo dominante: {metadata.get('dominant_archetype', 'N/A')}")
                print(f"   Carga afetiva: {metadata.get('affective_charge', 'N/A')}")
                print(f"   Profundidade existencial: {metadata.get('existential_depth', 'N/A')}")
                print(f"   Palavras-chave: {metadata.get('keywords', 'N/A')}")
                print(f"\n   CONTEÚDO:")
                print(f"   {doc}")
                print("-" * 50)
        else:
            print("❌ Escolha inválida")
    except ValueError:
        print("❌ Digite um número válido")

def delete_user_memories(users, vectorstore):
    """Permite selecionar e deletar todas as memórias de um usuário."""
    print("\n🗑️ DELETAR MEMÓRIAS DE UM USUÁRIO")
    print("=" * 50)
    
    user_list = list(users.items())
    
    if not user_list:
        print("Nenhum usuário para deletar.")
        return False

    for i, (user_id, user_data) in enumerate(user_list, 1):
        print(f"{i}. {user_data['name']} ({user_id}) - {len(user_data['memories'])} memórias")
    
    try:
        choice = int(input("\nEscolha o usuário para DELETAR (número) ou 0 para cancelar: "))
        
        if choice == 0:
            print("🚫 Operação cancelada.")
            return False

        user_index = choice - 1
        if 0 <= user_index < len(user_list):
            user_id_to_delete, user_data = user_list[user_index]
            
            confirm = input(
                f"\n‼️  ATENÇÃO: Você está prestes a deletar TODAS as {len(user_data['memories'])} memórias de {user_data['name']}.\n"
                "    Esta ação não pode ser desfeita.\n\n"
                "    Digite 'sim' para confirmar a exclusão: "
            ).lower().strip()
            
            if confirm == 'sim':
                # Coletar todos os IDs dos documentos associados a este usuário
                ids_to_delete = [mem['id'] for mem in user_data['memories']]
                
                if not ids_to_delete:
                    print("🧐 Nenhuma memória encontrada para este usuário.")
                    return False
                
                # Deletar do ChromaDB
                collection = vectorstore._collection
                collection.delete(ids=ids_to_delete)
                
                print(f"\n✅ Sucesso! {len(ids_to_delete)} memórias do usuário {user_data['name']} foram deletadas.")
                return True
            else:
                print("🚫 Exclusão cancelada pelo usuário.")
                return False
        else:
            print("❌ Escolha inválida.")
            return False
            
    except ValueError:
        print("❌ Entrada inválida. Por favor, digite um número.")
        return False
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado durante a exclusão: {e}")
        return False

def search_memories(users):
    """Busca memórias por palavra-chave"""
    keyword = input("\n🔍 Digite a palavra-chave: ").lower()
    
    print(f"\n🔍 RESULTADOS PARA '{keyword}':")
    print("=" * 50)
    
    found = False
    for user_id, user_data in users.items():
        user_results = []
        
        for memory in user_data['memories']:
            if keyword in memory['document'].lower():
                user_results.append(memory)
        
        if user_results:
            found = True
            print(f"\n👤 {user_data['name']} ({len(user_results)} resultados):")
            
            for memory in user_results:
                timestamp = memory['metadata'].get('timestamp', 'N/A')[:16]
                # Destacar palavra-chave
                content = memory['document']
                highlighted = content.replace(keyword, f"**{keyword.upper()}**")
                print(f"   [{timestamp}] {highlighted[:200]}...")
    
    if not found:
        print("❌ Nenhuma memória encontrada com essa palavra-chave")

def show_detailed_stats(users):
    """Mostra estatísticas detalhadas"""
    print("\n📊 ESTATÍSTICAS DETALHADAS:")
    print("=" * 50)
    
    total_memories = sum(len(user_data['memories']) for user_data in users.values())
    
    if len(users) == 0:
        print("Nenhum dado para exibir.")
        return

    print(f"Total de usuários: {len(users)}")
    print(f"Total de memórias: {total_memories}")
    print(f"Média de memórias por usuário: {total_memories / len(users):.1f}")
    
    # Estatísticas por usuário
    print(f"\n📈 Por usuário:")
    for user_id, user_data in users.items():
        memories = user_data['memories']
        
        # Calcular médias
        intensities = []
        tensions = []
        depths = []
        
        for memory in memories:
            metadata = memory['metadata']
            try:
                if 'intensity_level' in metadata and metadata['intensity_level'] is not None:
                    intensities.append(float(metadata['intensity_level']))
                if 'tension_level' in metadata and metadata['tension_level'] is not None:
                    tensions.append(float(metadata['tension_level']))
                if 'existential_depth' in metadata and metadata['existential_depth'] is not None:
                    depths.append(float(metadata['existential_depth']))
            except (ValueError, TypeError):
                pass
        
        avg_intensity = sum(intensities) / len(intensities) if intensities else 0
        avg_tension = sum(tensions) / len(tensions) if tensions else 0
        avg_depth = sum(depths) / len(depths) if depths else 0
        
        print(f"\n  {user_data['name']}:")
        print(f"    Memórias: {len(memories)}")
        print(f"    Intensidade média: {avg_intensity:.1f}")
        print(f"    Tensão média: {avg_tension:.1f}")
        print(f"    Profundidade média: {avg_depth:.1f}")

def export_to_json(users):
    """Exporta memórias para JSON"""
    filename = f"memories_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    export_data = {}
    for user_id, user_data in users.items():
        export_data[user_id] = {
            'user_name': user_data['name'],
            'total_memories': len(user_data['memories']),
            'memories': []
        }
        
        for memory in user_data['memories']:
            export_data[user_id]['memories'].append({
                'document': memory['document'],
                'metadata': memory['metadata']
            })
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Memórias exportadas para: {filename}")
    except Exception as e:
        print(f"❌ Erro ao exportar: {e}")

if __name__ == "__main__":
    explore_chromadb()