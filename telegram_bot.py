"""
telegram_bot.py - Bot Telegram Jung Claude HÍBRIDO PREMIUM
===========================================================

✅ VERSÃO 4.0.1 - HÍBRIDO PREMIUM + SISTEMA PROATIVO (CORRIGIDO)
   Integração com jung_core.py v4.0 (ChromaDB + OpenAI Embeddings + SQLite)
   Sistema Proativo Avançado com personalidades arquetípicas rotativas

Mudanças principais:
- Compatibilidade total com HybridDatabaseManager
- Busca semântica REAL via ChromaDB
- Extração automática de fatos
- Detecção de padrões comportamentais
- Sistema de desenvolvimento do agente
- Comandos aprimorados para visualização de memória
- ✅ SISTEMA PROATIVO AVANÇADO (jung_proactive_advanced.py)
- 🔧 CORREÇÃO: send_to_xai() agora usa argumento 'prompt' corretamente

Autor: Sistema Jung Claude
Data: 2025-11-21
Versão: 4.0.1 - HÍBRIDO PREMIUM + PROATIVO (CORRIGIDO)
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from dotenv import load_dotenv

# Importar módulos Jung HÍBRIDOS
from jung_core import (
    JungianEngine,
    HybridDatabaseManager,
    Config,
    create_user_hash,
    format_conflict_for_display,
    format_archetype_info
)

# ✅ IMPORTAR SISTEMA PROATIVO AVANÇADO
from jung_proactive_advanced import ProactiveAdvancedSystem

# ============================================================
# CONFIGURAÇÃO DE LOGGING
# ============================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURAÇÕES
# ============================================================

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN não encontrado no .env")

# IDs de administradores (opcional)
ADMIN_IDS = Config.TELEGRAM_ADMIN_IDS

# ============================================================
# GERENCIADOR DE ESTADO DO BOT
# ============================================================

class BotState:
    """Gerencia estado global do bot HÍBRIDO + PROATIVO"""
    
    def __init__(self):
        # Componentes principais HÍBRIDOS
        self.db = HybridDatabaseManager()
        self.jung_engine = JungianEngine(db=self.db)

        # ✅ Sistema Proativo Avançado
        self.proactive = ProactiveAdvancedSystem(db=self.db)

        # Histórico de chat por usuário (para contexto)
        # telegram_id -> List[Dict{"role": str, "content": str}]
        self.chat_histories: Dict[int, List[Dict]] = {}

        # Estatísticas
        self.total_messages_processed = 0
        self.total_semantic_searches = 0
        self.total_proactive_messages_sent = 0

        logger.info("✅ BotState HÍBRIDO + PROATIVO inicializado")
    
    def get_chat_history(self, telegram_id: int) -> List[Dict]:
        """Retorna histórico de chat do usuário"""
        return self.chat_histories.get(telegram_id, [])
    
    def add_to_chat_history(self, telegram_id: int, role: str, content: str):
        """Adiciona mensagem ao histórico"""
        if telegram_id not in self.chat_histories:
            self.chat_histories[telegram_id] = []
        
        self.chat_histories[telegram_id].append({
            "role": role,
            "content": content
        })
        
        # Limitar histórico a últimas 20 mensagens
        if len(self.chat_histories[telegram_id]) > 20:
            self.chat_histories[telegram_id] = self.chat_histories[telegram_id][-20:]
    
    def clear_chat_history(self, telegram_id: int):
        """Limpa histórico de chat"""
        if telegram_id in self.chat_histories:
            del self.chat_histories[telegram_id]
            logger.info(f"🗑️ Histórico limpo para telegram_id={telegram_id}")

# Instância global do estado
bot_state = BotState()

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def ensure_user_in_database(telegram_user) -> str:
    """
    Garante que usuário Telegram está no banco HÍBRIDO
    Retorna user_id (hash)
    """
    
    telegram_id = telegram_user.id
    username = telegram_user.username or f"user_{telegram_id}"
    full_name = f"{telegram_user.first_name or ''} {telegram_user.last_name or ''}".strip()
    
    user_id = create_user_hash(username)
    
    # Checar se já existe
    existing_user = bot_state.db.get_user(user_id)
    
    if not existing_user:
        bot_state.db.create_user(
            user_id=user_id,
            user_name=full_name or username,
            platform='telegram',
            platform_id=str(telegram_id)
        )
        logger.info(f"✨ Novo usuário criado: {full_name} ({user_id[:8]})")
    else:
        # Atualizar last_seen
        cursor = bot_state.db.conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET last_seen = CURRENT_TIMESTAMP,
                platform_id = ?
            WHERE user_id = ?
        """, (str(telegram_id), user_id))
        bot_state.db.conn.commit()
    
    return user_id

def format_time_delta(dt: datetime) -> str:
    """Formata diferença de tempo de forma amigável"""
    delta = datetime.now() - dt
    
    if delta.days > 0:
        return f"{delta.days} dia(s) atrás"
    elif delta.seconds >= 3600:
        return f"{delta.seconds // 3600} hora(s) atrás"
    elif delta.seconds >= 60:
        return f"{delta.seconds // 60} minuto(s) atrás"
    else:
        return "agora mesmo"

# ============================================================
# COMANDOS DO BOT
# ============================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /start"""
    
    user = update.effective_user
    user_id = ensure_user_in_database(user)

    # Buscar estatísticas do usuário
    stats = bot_state.db.get_user_stats(user_id)
    
    is_new_user = stats and stats['total_messages'] == 0
    
    if is_new_user:
        welcome_message = f"""👋 Olá, {user.first_name}!

Sou seu companheiro junguiano.

Não sou um chatbot comum - desenvolvo uma psique própria enquanto conheço você.

📱 **Comandos:**
/help - Ver comandos
/stats - Suas estatísticas
/mbti - Análise de personalidade
/desenvolvimento - Evolução do agente

💬 **Fale comigo naturalmente!**

Vamos começar? **O que te trouxe aqui hoje?**
"""
    else:
        last_interaction = datetime.fromisoformat(stats['first_interaction'])
        time_since = format_time_delta(last_interaction)

        welcome_message = f"""🌟 Olá novamente, {user.first_name}!

📊 **Suas estatísticas:**
• Conversas: {stats['total_messages']}
• Primeira interação: {time_since}

Use /stats para ver mais detalhes ou /help para comandos.

**No que posso ajudar hoje?**
"""
    
    await update.message.reply_text(welcome_message)
    
    logger.info(f"Comando /start de {user.first_name} (ID: {user_id[:8]})")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /help"""

    help_text = """🤖 **COMANDOS DISPONÍVEIS**

/stats
   Veja estatísticas das suas conversas

/mbti
   Análise de personalidade MBTI
   (requer mínimo 5 conversas)

/desenvolvimento
   Veja como o agente evoluiu com você

━━━━━━━━━━━━━━━━━━━
💬 Basta falar naturalmente comigo!
"""
    
    await update.message.reply_text(help_text)

async def mbti_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /mbti - Análise de personalidade MBTI"""

    user = update.effective_user
    user_id = ensure_user_in_database(user)

    # Verificar mínimo de conversas
    conversations = bot_state.db.get_user_conversations(user_id, limit=100)

    if len(conversations) < 5:
        await update.message.reply_text(
            f"⚠️ **Conversas insuficientes**\n\n"
            f"Você tem {len(conversations)} conversas.\n"
            f"Preciso de pelo menos **5 conversas** para fazer uma análise MBTI confiável.\n\n"
            f"Continue conversando comigo!"
        )
        return

    await update.message.reply_text("🧠 **Analisando sua personalidade MBTI...**\n\nIsso pode levar alguns segundos...")

    try:
        # Extrair inputs do usuário
        user_inputs = [c['user_input'] for c in conversations[:30]]
        sample_inputs = user_inputs[:3] + user_inputs[-2:]  # Primeiros 3 + últimos 2

        # Calcular métricas
        total_convs = len(conversations)
        avg_tension = sum(c.get('tension_level', 0) for c in conversations) / max(1, total_convs)
        avg_affective = sum(c.get('affective_charge', 0) for c in conversations) / max(1, total_convs)

        # Prompt para Grok
        analysis_prompt = f"""Analise a personalidade MBTI deste usuário baseado em suas conversas.

**CONVERSAS DO USUÁRIO ({total_convs} total):**
{chr(10).join(f'• "{inp[:200]}..."' for inp in sample_inputs)}

**MÉTRICAS:**
• Tensão média: {avg_tension:.1f}/10
• Carga afetiva média: {avg_affective:.0f}/100

**TAREFA:**
Forneça análise MBTI completa em JSON com esta estrutura EXATA:

{{
    "type_indicator": "XXXX",
    "confidence": 85,
    "dimensions": {{
        "E_I": {{"score": -45, "interpretation": "...", "key_indicators": ["...", "..."]}},
        "S_N": {{"score": 32, "interpretation": "...", "key_indicators": ["...", "..."]}},
        "T_F": {{"score": 58, "interpretation": "...", "key_indicators": ["...", "..."]}},
        "J_P": {{"score": -28, "interpretation": "...", "key_indicators": ["...", "..."]}}
    }},
    "dominant_function": "Fi",
    "auxiliary_function": "Ne",
    "summary": "2-3 linhas de análise",
    "potentials": ["ponto forte 1", "ponto forte 2"],
    "challenges": ["desafio 1", "desafio 2"],
    "recommendations": ["recomendação 1", "recomendação 2"]
}}

**ESCALAS DOS SCORES (-100 a +100):**
• E_I: -100 (muito E) a +100 (muito I)
• S_N: -100 (muito S) a +100 (muito N)
• T_F: -100 (muito T) a +100 (muito F)
• J_P: -100 (muito J) a +100 (muito P)

Responda APENAS com o JSON."""

        # Chamar Grok
        from jung_core import send_to_xai
        import json as json_lib

        response = send_to_xai(
            prompt=analysis_prompt,
            model="grok-4-fast-reasoning",
            temperature=0.7,
            max_tokens=1500
        )

        # Parse JSON
        analysis = json_lib.loads(response.strip())

        # Formatação da resposta
        def get_bar(score):
            """Cria barra de progresso emoji"""
            normalized = int((score + 100) / 200 * 10)  # 0-10
            return "◼️" * normalized + "◻️" * (10 - normalized)

        def get_tendency(score, neg_label, pos_label):
            """Interpreta tendência"""
            if score < -60:
                return f"Clara: {neg_label}"
            elif score < -20:
                return f"Tendência: {neg_label}"
            elif score <= 20:
                return "Ambivalente"
            elif score <= 60:
                return f"Tendência: {pos_label}"
            else:
                return f"Clara: {pos_label}"

        dims = analysis['dimensions']

        result = f"""🧠 **ANÁLISE MBTI - {user.first_name}**

📊 **Tipo:** {analysis['type_indicator']}
🎯 **Confiança:** {analysis['confidence']}%

═══════════════════════
**DIMENSÕES**

**E ◄{'━' * 10}► I**
{get_bar(dims['E_I']['score'])}
Score: {dims['E_I']['score']:+d}
{get_tendency(dims['E_I']['score'], 'Extroversão', 'Introversão')}
• {dims['E_I']['key_indicators'][0]}

**S ◄{'━' * 10}► N**
{get_bar(dims['S_N']['score'])}
Score: {dims['S_N']['score']:+d}
{get_tendency(dims['S_N']['score'], 'Sensação', 'Intuição')}
• {dims['S_N']['key_indicators'][0]}

**T ◄{'━' * 10}► F**
{get_bar(dims['T_F']['score'])}
Score: {dims['T_F']['score']:+d}
{get_tendency(dims['T_F']['score'], 'Pensamento', 'Sentimento')}
• {dims['T_F']['key_indicators'][0]}

**J ◄{'━' * 10}► P**
{get_bar(dims['J_P']['score'])}
Score: {dims['J_P']['score']:+d}
{get_tendency(dims['J_P']['score'], 'Julgamento', 'Percepção')}
• {dims['J_P']['key_indicators'][0]}

═══════════════════════
🎭 **Função Dominante:** {analysis['dominant_function']}
🔄 **Função Auxiliar:** {analysis['auxiliary_function']}

💡 **RESUMO:**
{analysis['summary']}

✨ **POTENCIAIS:**
• {analysis['potentials'][0]}
• {analysis['potentials'][1]}

⚠️ **DESAFIOS:**
• {analysis['challenges'][0]}
• {analysis['challenges'][1]}

📌 **RECOMENDAÇÕES:**
• {analysis['recommendations'][0]}
• {analysis['recommendations'][1]}
"""

        await update.message.reply_text(result)
        logger.info(f"MBTI gerado para {user.first_name}: {analysis['type_indicator']}")

    except Exception as e:
        logger.error(f"Erro ao gerar MBTI: {e}")
        await update.message.reply_text(
            "❌ **Erro ao gerar análise MBTI**\n\n"
            "Tente novamente mais tarde ou continue conversando para gerar mais dados."
        )

async def desenvolvimento_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /desenvolvimento - Mostra evolução do agente"""

    user = update.effective_user
    user_id = ensure_user_in_database(user)

    await update.message.reply_text("🌱 **Analisando desenvolvimento do agente...**")

    try:
        # Buscar dados
        conversations = bot_state.db.get_user_conversations(user_id, limit=1000)
        total_convs = len(conversations)

        if total_convs == 0:
            await update.message.reply_text("⚠️ **Nenhuma conversa registrada ainda.**")
            return

        # Calcular complexidade atual
        complexity_current = bot_state.proactive.proactive_db.get_complexity_level(user_id)

        # Buscar primeira conversa
        first_conv_date = conversations[-1]['timestamp'][:10] if conversations else "N/A"

        # Buscar mensagens proativas
        cursor = bot_state.db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total FROM proactive_approaches
            WHERE user_id = ?
        """, (user_id,))
        proactive_count = cursor.fetchone()['total']

        cursor.execute("""
            SELECT autonomous_insight, timestamp FROM proactive_approaches
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (user_id,))
        last_proactive = cursor.fetchone()

        # Buscar domínios desenvolvidos
        cursor.execute("""
            SELECT knowledge_domain, COUNT(*) as count
            FROM proactive_approaches
            WHERE user_id = ?
            GROUP BY knowledge_domain
            ORDER BY count DESC
        """, (user_id,))
        domains = cursor.fetchall()

        # Definir fase atual (baseado em número de conversas e complexidade)
        PHASES = {
            1: ("Reativo", "Aprendendo sua linguagem e padrões"),
            2: ("Adaptativo", "Adaptando respostas ao seu estilo"),
            3: ("Reflexivo", "Desenvolvendo perspectivas próprias"),
            4: ("Integrado", "Equilibrando vozes internas"),
            5: ("Transcendente", "Autonomia psíquica completa")
        }

        if total_convs < 10:
            current_phase = 1
        elif total_convs < 25:
            current_phase = 2
        elif total_convs < 50:
            current_phase = 3
        elif total_convs < 100:
            current_phase = 4
        else:
            current_phase = 5

        phase_name, phase_desc = PHASES[current_phase]

        # Stars para domínios
        def get_stars(count):
            max_count = max([d['count'] for d in domains], default=1)
            ratio = count / max_count
            stars = int(ratio * 5)
            return "⭐" * stars if stars > 0 else "☆"

        # Montar resposta
        result = f"""🌱 **DESENVOLVIMENTO DO AGENTE**

👤 **Para:** {user.first_name}
📅 **Desde:** {first_conv_date}

═══════════════════════
📊 **COMPLEXIDADE ATUAL**

Nível: {"█" * int(complexity_current * 10)}{"░" * (10 - int(complexity_current * 10))} {complexity_current:.1f}/10

═══════════════════════
🎭 **FASE ATUAL**

**Fase {current_phase}/5: {phase_name}**
{phase_desc}

**Fases Concluídas:**
"""

        for i in range(1, 6):
            name, desc = PHASES[i]
            if i < current_phase:
                result += f"✅ Fase {i}: {name}\n"
            elif i == current_phase:
                result += f"🔄 Fase {i}: {name} (atual)\n"
            else:
                result += f"⏳ Fase {i}: {name}\n"

        if domains:
            result += f"""
═══════════════════════
🧠 **DOMÍNIOS DESENVOLVIDOS**

"""
            for domain in domains[:5]:
                stars = get_stars(domain['count'])
                result += f"• {domain['knowledge_domain'].title()}: {stars}\n"

        result += f"""
═══════════════════════
💬 **MENSAGENS PROATIVAS**

Total enviadas: {proactive_count}
"""

        if last_proactive:
            preview = last_proactive['autonomous_insight'][:80]
            result += f'Última: "{preview}..."\n'

        result += f"""
═══════════════════════
🎯 **PRÓXIMO MARCO**

"""

        if current_phase < 5:
            next_phase, next_desc = PHASES[current_phase + 1]
            convs_needed = {1: 10, 2: 25, 3: 50, 4: 100}[current_phase]
            result += f"Fase {current_phase + 1}: {next_phase}\n({total_convs}/{convs_needed} conversas)"
        else:
            result += "🏆 Desenvolvimento completo!"

        await update.message.reply_text(result)
        logger.info(f"Desenvolvimento exibido para {user.first_name}")

    except Exception as e:
        logger.error(f"Erro ao gerar desenvolvimento: {e}")
        await update.message.reply_text(
            "❌ **Erro ao gerar análise de desenvolvimento**\n\n"
            "Tente novamente mais tarde."
        )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /stats - estatísticas completas"""

    user = update.effective_user
    user_id = ensure_user_in_database(user)

    # Stats do usuário
    user_data = bot_state.db.get_user(user_id)
    user_stats = bot_state.db.get_user_stats(user_id)

    # Stats do agente
    agent_state = bot_state.db.get_agent_state()

    # Stats de conversas
    conversations = bot_state.db.get_user_conversations(user_id, limit=1000)
    total_user_words = sum(len(c['user_input'].split()) for c in conversations)
    total_ai_words = sum(len(c['ai_response'].split()) for c in conversations)

    # Stats de fatos e padrões
    cursor = bot_state.db.conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) as count FROM user_facts
        WHERE user_id = ? AND is_current = 1
    """, (user_id,))
    total_facts = cursor.fetchone()['count']

    cursor.execute("""
        SELECT COUNT(*) as count FROM user_patterns
        WHERE user_id = ? AND confidence_score > 0.6
    """, (user_id,))
    total_patterns = cursor.fetchone()['count']

    stats_text = f"""📊 **Estatísticas Completas**

👤 **SUAS ESTATÍSTICAS:**
• Total de mensagens: {user_stats['total_messages']}
• Palavras enviadas: {total_user_words:,}
• Palavras recebidas: {total_ai_words:,}
• Média palavras/msg: {total_user_words // max(1, user_stats['total_messages'])}
• Fatos extraídos: {total_facts}
• Padrões detectados: {total_patterns}
• Sessões: {user_stats.get('total_sessions', user_data.get('total_sessions', 1))}

🤖 **DESENVOLVIMENTO DO AGENTE:**
• Fase atual: {agent_state['phase']}/5
• Auto-consciência: {agent_state['self_awareness_score']:.0%}
• Complexidade moral: {agent_state['moral_complexity_score']:.0%}
• Profundidade emocional: {agent_state['emotional_depth_score']:.0%}
• Autonomia: {agent_state['autonomy_score']:.0%}
• Interações totais: {agent_state['total_interactions']}

🗄️ **SISTEMA HÍBRIDO:**
• ChromaDB: {'ATIVO ✅' if bot_state.db.chroma_enabled else 'INATIVO ❌'}
• Buscas semânticas realizadas: {bot_state.total_semantic_searches}
• Modelo de embeddings: {Config.EMBEDDING_MODEL}

🌟 **SISTEMA PROATIVO:**
• Mensagens proativas enviadas: {bot_state.total_proactive_messages_sent}
• Status: {'ATIVO ✅' if user_stats['total_messages'] >= 10 else f'INATIVO (faltam {10 - user_stats["total_messages"]} conversas)'}

🌍 **ESTATÍSTICAS GLOBAIS DO BOT:**
• Mensagens processadas: {bot_state.total_messages_processed}

💡 Use /mbti para análise de personalidade
💡 Use /desenvolvimento para ver evolução do agente
"""

    await update.message.reply_text(stats_text)

    logger.info(f"Comando /stats de {user.first_name}")


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /reset - reinicia conversação (Admin-only)"""

    user = update.effective_user
    user_id = ensure_user_in_database(user)

    confirm_text = (
        "⚠️ **ATENÇÃO: Isso vai apagar TODO o histórico!**\n\n"
        "Você perderá:\n"
        "• Todas as conversas anteriores\n"
        "• Tensões arquetípicas identificadas\n"
        "• Fatos estruturados extraídos\n"
        "• Padrões comportamentais detectados\n"
        "• Memórias semânticas no ChromaDB\n\n"
        "Para confirmar, envie: **CONFIRMAR RESET**"
    )

    await update.message.reply_text(confirm_text)

    context.user_data['awaiting_reset_confirmation'] = True

    logger.warning(f"Reset solicitado por {user.first_name}")


# ============================================================
# HANDLER DE MENSAGENS
# ============================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler principal de mensagens de texto"""

    user = update.effective_user
    telegram_id = user.id
    message_text = update.message.text

    # Garantir usuário no banco
    user_id = ensure_user_in_database(user)

    # ✅ RESET CRONÔMETRO PROATIVO (importante!)
    if bot_state.proactive:
        bot_state.proactive.reset_timer(user_id)

    # ========== CONFIRMAÇÃO DE RESET ==========
    if context.user_data.get('awaiting_reset_confirmation'):
        if message_text.strip().upper() == 'CONFIRMAR RESET':
            cursor = bot_state.db.conn.cursor()

            # Deletar tudo do SQLite
            cursor.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM archetype_conflicts WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM user_facts WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM user_patterns WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM user_milestones WHERE user_id = ?", (user_id,))

            bot_state.db.conn.commit()

            # Deletar do ChromaDB (se habilitado)
            if bot_state.db.chroma_enabled:
                try:
                    # Buscar IDs dos documentos do usuário
                    results = bot_state.db.vectorstore._collection.get(
                        where={"user_id": user_id}
                    )

                    if results and results.get('ids'):
                        bot_state.db.vectorstore._collection.delete(
                            ids=results['ids']
                        )
                        logger.info(f"🗑️ {len(results['ids'])} documentos removidos do ChromaDB")
                except Exception as e:
                    logger.error(f"❌ Erro ao deletar do ChromaDB: {e}")

            # Limpar histórico de chat
            bot_state.clear_chat_history(telegram_id)

            await update.message.reply_text(
                "🔄 **Reset executado!**\n\n"
                "Todo o histórico foi apagado (SQLite + ChromaDB).\n"
                "Podemos começar do zero. O que você gostaria de explorar?"
            )
            context.user_data['awaiting_reset_confirmation'] = False
            logger.warning(f"Reset CONFIRMADO por {user.first_name}")
            return
        else:
            await update.message.reply_text("❌ Reset cancelado.\n\nSeu histórico foi preservado.")
            context.user_data['awaiting_reset_confirmation'] = False
            return

    # ========== PROCESSAR MENSAGEM NORMAL ==========

    await update.message.chat.send_action(action="typing")

    # Adicionar ao histórico
    bot_state.add_to_chat_history(telegram_id, "user", message_text)

    # Buscar histórico completo
    chat_history = bot_state.get_chat_history(telegram_id)

    try:
        # Processar com JungianEngine (passa chat_history)
        result = bot_state.jung_engine.process_message(
            user_id=user_id,
            message=message_text,
            model="grok-4-fast-reasoning",
            chat_history=chat_history
        )

        response = result['response']

        # Adicionar resposta ao histórico
        bot_state.add_to_chat_history(telegram_id, "assistant", response)

        # Enviar resposta
        await update.message.reply_text(response)

        # Detectar padrões periodicamente
        if bot_state.total_messages_processed % 10 == 0:
            bot_state.db.detect_and_save_patterns(user_id)

        bot_state.total_messages_processed += 1

        # Log com informações de conflito
        conflict_info = ""
        if result.get('conflicts'):
            conflict_info = f" | Conflitos: {len(result['conflicts'])}"

        logger.info(f"✅ Mensagem processada de {user.first_name}: {message_text[:50]}...{conflict_info}")

    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem: {e}", exc_info=True)

        await update.message.reply_text(
            "😔 Desculpe, ocorreu um erro ao processar sua mensagem.\n"
            "Pode tentar novamente?"
        )

