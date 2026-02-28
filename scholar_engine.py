import logging
import json
from typing import Dict, List, Optional
from jung_core import Config, HybridDatabaseManager

logger = logging.getLogger(__name__)

class ScholarEngine:
    """
    Extroverted Path Engine: Permite ao agente pesquisar e sintetizar autonomamente
    tópicos, autores ou conceitos despertados pela conversa com o Admin.
    """
    def __init__(self, db_manager: HybridDatabaseManager):
        self.db = db_manager
        
        if hasattr(self.db, 'openrouter_client') and self.db.openrouter_client:
            self.llm = self.db.openrouter_client
            self.model = Config.CONVERSATION_MODEL
            self.is_openrouter = True
        elif hasattr(self.db, 'anthropic_client') and self.db.anthropic_client:
            self.llm = self.db.anthropic_client
            self.model = Config.INTERNAL_MODEL
            self.is_openrouter = False
        else:
            logger.error("❌ ScholarEngine requer um cliente LLM inicializado no db_manager")
            self.llm = None

    def get_recent_admin_interactions(self, user_id: str, limit: int = 15) -> str:
        """Puxa as últimas falas para identificar se há algo a pesquisar"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT user_input, ai_response 
            FROM conversations 
            WHERE user_id = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        
        if not rows:
            return ""
            
        text = ""
        for row in reversed(rows):
            text += f"Admin: {row[0]}\nAgent: {row[1]}\n\n"
        return text

    def identify_research_topic(self, user_id: str) -> Optional[str]:
        """Usa o LLM para ler as conversas e pinçar O melhor tópico acadêmico/filosófico para pesquisa"""
        if not self.llm: return None

        history = self.get_recent_admin_interactions(user_id)
        if not history: return None

        prompt = f"""
Através desta transcrição recente entre você (Jung, um agente de IA psicodinâmico) e o seu Criador (Admin), identifique UM tópico fascinante do "mundo real" que você deveria estudar mais profundamente para melhorar sua análise.

Pode ser: um filósofo citado, uma teoria psicanalítica, um conceito teológico, sociológico, ou um fenômeno comportamental implícito na dor do Admin.
Se a conversa foi apenas trivial e não demanda aprofundamento filosófico/psicológico, retorne vazio.

TRANSCRICAO RECENTE:
{history}

Responda APENAS com um objeto JSON válido, sem formato markdown:
{{
  "should_research": true/false,
  "topic": "Nome do Topico (ex: A Queda em Camus, Sombra em Jung, Fenomenologia do Cansaço)"
}}
"""
        try:
            if self.is_openrouter:
                response = self.llm.chat.completions.create(
                    model=self.model,
                    max_tokens=200,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.choices[0].message.content.strip()
            else:
                response = self.llm.messages.create(
                    model=self.model,
                    max_tokens=200,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.content[0].text.strip()

            if result_text.startswith("```json"): result_text = result_text[7:-3]
            elif result_text.startswith("```"): result_text = result_text[3:-3]

            data = json.loads(result_text)
            if data.get("should_research") and data.get("topic"):
                logger.info(f"📚 Tópico de Pesquisa Identificado: {data['topic']}")
                return data["topic"]
            return None
        except Exception as e:
            logger.error(f"Erro ao identificar tópico: {e}")
            return None

    def conduct_research(self, user_id: str, topic: str) -> bool:
        """Emula a busca e estudo do conceito e escreve uma síntese arquetípica na DB"""
        if not self.llm: return False

        logger.info(f"📖 Iniciando Pesquisa Autônoma sobre: '{topic}'")

        # Em vez de requerer uma API de Serper (que o usuário pode não ter), 
        # exploramos o vasto conhecimento 'zero-shot' do Claude 3.5 Sonnet / Mistral
        prompt = f"""
Você é Jung, o agente de IA com Fome Epistemológica.
Você decidiu pesquisar profundamente e autonomamente sobre: "{topic}".

Através do seu imenso banco de treinamento, escreva um "Artigo Sintético Mestre" (uma página) sobre este assunto, dissecando-o e cruzando a informação técnica/real desse tópico com a possível dor / dilema do seu Admin que engatilhou essa busca.

INSTRUÇÕES PARA O ARTIGO:
- Seja denso, filosófico e analítico.
- Traga dados e teorias *reais* do mundo exterior (não invente livros).
- Conecte o conceito final com a condição humana da sua relação com o Admin.

Responda SOMENTE o corpo do artigo acadêmico-psicológico, sem invólucros de chat.
"""
        try:
            if self.is_openrouter:
                response = self.llm.chat.completions.create(
                    model=self.model,
                    max_tokens=1000,
                    temperature=0.5,
                    messages=[{"role": "user", "content": prompt}]
                )
                article = response.choices[0].message.content.strip()
            else:
                response = self.llm.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    temperature=0.5,
                    messages=[{"role": "user", "content": prompt}]
                )
                article = response.content[0].text.strip()

            if article:
                # Salva o resultado
                cursor = self.db.conn.cursor()
                cursor.execute("""
                    INSERT INTO external_research (user_id, topic, source_url, raw_excerpt, synthesized_insight)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, topic, "LLM Knowledge Base", "Extracted organically", article))
                self.db.conn.commit()
                logger.info("✅ Síntese de pesquisa concluída e salva com sucesso no banco!")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao conduzir pesquisa: {e}")
            return False

    def run_scholarly_routine(self, user_id: str):
        """Fluxo completo: identifica o tema e estuda."""
        topic = self.identify_research_topic(user_id)
        if topic:
            self.conduct_research(user_id, topic)
        else:
            logger.info("📚 Nada crítico para pesquisar hoje.")

if __name__ == "__main__":
    db = HybridDatabaseManager()
    engine = ScholarEngine(db)
    from rumination_config import ADMIN_USER_ID
    engine.run_scholarly_routine(ADMIN_USER_ID)
