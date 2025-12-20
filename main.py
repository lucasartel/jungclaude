import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import logging
import os
import sys
from dotenv import load_dotenv

# Adicionar diretório atual ao PYTHONPATH para garantir que admin_web seja encontrado
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar o bot
from telegram_bot import bot_state, start_command, help_command, stats_command, mbti_command, desenvolvimento_command, reset_command
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Importar rotas do admin (serão criadas)
# from admin_web.routes import router as admin_router

load_dotenv()

# Configuração de Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================================
# PROACTIVE MESSAGE SCHEDULER
# ============================================================================

async def proactive_message_scheduler(telegram_app):
    """
    Loop contínuo que verifica e envia mensagens proativas a cada 30 minutos.

    Funcionalidades:
    - Verifica todos os usuários cadastrados
    - Identifica usuários inativos (>3h sem enviar mensagem)
    - Gera mensagens proativas personalizadas usando Jung Proactive Advanced
    - Envia via Telegram
    - Respeita cooldown de 6h entre mensagens proativas
    """

    logger.info("🔄 Scheduler de mensagens proativas iniciado!")

    # Aguardar 1 minuto para garantir que o bot está completamente inicializado
    await asyncio.sleep(60)

    while True:
        try:
            logger.info("🔍 [PROATIVO] Verificando usuários elegíveis para mensagens proativas...")

            # Buscar todos os usuários
            try:
                users = bot_state.db.get_all_users()
                logger.info(f"   📊 Total de usuários cadastrados: {len(users)}")
            except Exception as e:
                logger.error(f"   ❌ Erro ao buscar usuários: {e}")
                await asyncio.sleep(30 * 60)  # Aguardar 30 min e tentar novamente
                continue

            proactive_sent_count = 0

            for user in users:
                try:
                    user_id = user.get('user_id')
                    user_name = user.get('user_name', 'Usuário')
                    platform_id = user.get('platform_id')  # ✅ CRÍTICO: Telegram ID real

                    if not user_id or not platform_id:
                        logger.warning(f"   ⚠️  [PROATIVO] Usuário sem user_id ou platform_id: {user_name}")
                        continue

                    # Verificar e gerar mensagem proativa (sistema já faz todas as validações internas)
                    message = bot_state.proactive.check_and_generate_advanced_message(
                        user_id=user_id,
                        user_name=user_name
                    )

                    if message:
                        # ✅ FIX: Usar platform_id (telegram_id) como chat_id, não user_id (hash)
                        try:
                            telegram_id = int(platform_id)  # Converter para inteiro

                            await telegram_app.bot.send_message(
                                chat_id=telegram_id,  # ✅ CORRIGIDO: usa telegram_id real
                                text=message,
                                parse_mode='Markdown'
                            )
                            logger.info(f"   ✅ [PROATIVO] Mensagem enviada para {user_name} (telegram_id={telegram_id})")
                            proactive_sent_count += 1

                            # Pequeno delay entre envios para evitar rate limit
                            await asyncio.sleep(2)

                        except ValueError as e:
                            logger.error(f"   ❌ [PROATIVO] platform_id inválido para {user_name}: {platform_id} - {e}")
                        except Exception as e:
                            logger.error(f"   ❌ [PROATIVO] Erro ao enviar para {user_name} (telegram_id={platform_id}): {e}")

                except Exception as e:
                    logger.error(f"   ❌ [PROATIVO] Erro ao processar usuário: {e}")
                    continue

            logger.info(f"✅ [PROATIVO] Ciclo completo. Mensagens enviadas: {proactive_sent_count}")
            logger.info(f"⏰ [PROATIVO] Próxima verificação em 30 minutos...")

            # Aguardar 30 minutos antes de próxima verificação
            await asyncio.sleep(30 * 60)

        except Exception as e:
            logger.error(f"❌ [PROATIVO] Erro crítico no scheduler: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Em caso de erro, aguardar 5 minutos e tentar novamente
            await asyncio.sleep(5 * 60)

# ============================================================================
# LIFECYCLE MANAGER
# ============================================================================

async def setup_bot_commands(telegram_app):
    """
    Configura os comandos do bot que aparecem no menu do Telegram.
    Remove comandos antigos e define apenas os comandos atuais.
    """
    from telegram import BotCommand

    commands = [
        BotCommand("start", "Iniciar conversa com Jung"),
        BotCommand("help", "Ver comandos disponíveis"),
        BotCommand("stats", "Ver estatísticas do agente"),
        BotCommand("mbti", "Ver análise MBTI de personalidade"),
        BotCommand("desenvolvimento", "Ver estado de desenvolvimento do agente"),
        BotCommand("reset", "Resetar conversa (apaga todo histórico)")
    ]

    await telegram_app.bot.set_my_commands(commands)
    logger.info(f"✅ Comandos do bot configurados: {[cmd.command for cmd in commands]}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação (Bot + API)"""

    # 1. Iniciar Bot Telegram
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN não encontrado!")
        yield
        return

    logger.info("🤖 Inicializando Bot Telegram...")
    telegram_app = Application.builder().token(telegram_token).build()

    # Registrar handlers (apenas comandos essenciais)
    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("stats", stats_command))
    telegram_app.add_handler(CommandHandler("mbti", mbti_command))
    telegram_app.add_handler(CommandHandler("desenvolvimento", desenvolvimento_command))
    telegram_app.add_handler(CommandHandler("reset", reset_command))

    # Handler de mensagens (precisamos importar a função handle_message se ela existir,
    # ou definir aqui se estiver dentro do main no original.
    # Vou assumir que precisamos mover a lógica de main() do telegram_bot.py para cá ou expor o handler)
    from telegram_bot import handle_message
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Iniciar bot em modo assíncrono
    await telegram_app.initialize()
    await telegram_app.start()

    # Configurar comandos visíveis no menu do Telegram
    await setup_bot_commands(telegram_app)

    # Iniciar polling (em background task para não bloquear o FastAPI)
    # Nota: Em produção com webhook seria diferente, mas para polling:
    asyncio.create_task(telegram_app.updater.start_polling())

    logger.info("✅ Bot Telegram iniciado e rodando!")

    # ✨ Iniciar scheduler de mensagens proativas
    proactive_task = asyncio.create_task(proactive_message_scheduler(telegram_app))
    logger.info("✅ Scheduler de mensagens proativas ativado!")

    # ✨ Iniciar scheduler de ruminação (Jung Lab)
    rumination_scheduler_process = None
    try:
        import subprocess
        import sys
        pid_file = "rumination_scheduler.pid"

        # Remover PID file antigo se existir (de sessões anteriores)
        if os.path.exists(pid_file):
            try:
                with open(pid_file, "r") as f:
                    old_pid = int(f.read().strip())
                try:
                    os.kill(old_pid, 0)  # Verifica se processo ainda existe
                    logger.info(f"⚠️  Scheduler de ruminação já rodando (PID: {old_pid})")
                except OSError:
                    # Processo não existe, remover PID file obsoleto
                    os.remove(pid_file)
                    logger.info("🗑️  PID file obsoleto removido")
            except:
                os.remove(pid_file)

        # Iniciar novo processo de scheduler
        if not os.path.exists(pid_file):
            python_exe = sys.executable
            rumination_scheduler_process = subprocess.Popen(
                [python_exe, "rumination_scheduler.py"],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Salvar PID
            with open(pid_file, "w") as f:
                f.write(str(rumination_scheduler_process.pid))

            logger.info(f"✅ Scheduler de ruminação iniciado (PID: {rumination_scheduler_process.pid})")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar scheduler de ruminação: {e}")
        logger.warning("⚠️  Jung Lab rodará apenas com digestão manual")

    yield

    # Shutdown
    logger.info("🛑 Parando aplicação...")

    # Parar scheduler proativo
    proactive_task.cancel()
    try:
        await proactive_task
    except asyncio.CancelledError:
        logger.info("✅ Scheduler proativo cancelado")

    # Parar scheduler de ruminação
    if rumination_scheduler_process:
        try:
            import signal
            rumination_scheduler_process.send_signal(signal.SIGTERM)
            rumination_scheduler_process.wait(timeout=5)
            logger.info("✅ Scheduler de ruminação parado")
        except Exception as e:
            logger.warning(f"⚠️  Erro ao parar scheduler de ruminação: {e}")
            try:
                rumination_scheduler_process.kill()
            except:
                pass

        # Remover PID file
        pid_file = "rumination_scheduler.pid"
        if os.path.exists(pid_file):
            os.remove(pid_file)

    # Parar bot Telegram
    logger.info("🛑 Parando Bot Telegram...")
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="Jung Claude Admin", lifespan=lifespan)

# ============================================================================
# ROTAS BÁSICAS
# ============================================================================

@app.get("/")
async def root():
    """Rota raiz - redireciona para o admin"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/admin")

@app.get("/health")
async def health_check():
    """Health check endpoint para monitoramento"""
    return {
        "status": "healthy",
        "service": "Jung Claude Bot + Admin",
        "bot_running": True
    }

@app.get("/test/proactive")
async def test_proactive():
    """
    ENDPOINT DE DIAGNÓSTICO DO SISTEMA PROATIVO

    Acesse: https://seu-railway-url/test/proactive

    Retorna informações detalhadas sobre:
    - Usuários cadastrados
    - Elegibilidade para mensagens proativas
    - Mensagens geradas (sem enviar)
    - Erros encontrados
    - Timezone e cálculos de tempo
    """

    results = []
    from datetime import datetime

    try:
        # Informações de timezone
        now_local = datetime.now()
        now_utc = datetime.utcnow()

        timezone_info = {
            "server_time_local": now_local.strftime("%Y-%m-%d %H:%M:%S"),
            "server_time_utc": now_utc.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone_offset_hours": round((now_local - now_utc).total_seconds() / 3600, 1)
        }

        # Buscar todos os usuários
        users = bot_state.db.get_all_users()

        results.append({
            "step": "get_users",
            "status": "success",
            "total_users": len(users)
        })

        # Testar cada usuário
        for user in users:
            user_id = user.get('user_id')
            user_name = user.get('user_name', 'Usuário')
            platform_id = user.get('platform_id')
            last_seen_str = user.get('last_seen')

            # Calcular tempo de inatividade MANUALMENTE
            hours_inactive = None
            if last_seen_str:
                try:
                    last_seen_dt = datetime.fromisoformat(last_seen_str)
                    # SQLite retorna UTC, comparar com UTC
                    delta = now_utc - last_seen_dt
                    hours_inactive = round(delta.total_seconds() / 3600, 2)
                except Exception as e:
                    logger.error(f"Error parsing last_seen for {user_name}: {e}")

            user_result = {
                "user_name": user_name,
                "user_id": user_id[:8] if user_id else None,
                "platform_id": platform_id,
                "last_seen_utc": last_seen_str,
                "hours_inactive": hours_inactive,
                "total_messages": user.get('total_messages', 0),
                "requirements": {
                    "min_conversations": 3,
                    "min_inactivity_hours": 3,
                    "cooldown_hours": 6
                }
            }

            # Verificar campos obrigatórios
            if not user_id or not platform_id:
                user_result["error"] = "Missing user_id or platform_id"
                results.append(user_result)
                continue

            # Verificar elegibilidade MANUALMENTE
            # (sem chamar check_and_generate para evitar logs confusos)

            # 1. Conversas suficientes?
            total_convs = len(bot_state.db.get_user_conversations(user_id, limit=1000))
            user_result["total_conversations"] = total_convs
            user_result["has_enough_conversations"] = total_convs >= 3

            # 2. Inatividade suficiente?
            user_result["has_enough_inactivity"] = hours_inactive and hours_inactive >= 3

            # 3. Cooldown OK?
            cursor = bot_state.db.conn.cursor()
            cursor.execute("""
                SELECT timestamp FROM proactive_approaches
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (user_id,))
            last_proactive = cursor.fetchone()

            if last_proactive:
                last_proactive_dt = datetime.fromisoformat(last_proactive['timestamp'])
                hours_since_proactive = round((now_utc - last_proactive_dt).total_seconds() / 3600, 2)
                user_result["hours_since_last_proactive"] = hours_since_proactive
                user_result["cooldown_ok"] = hours_since_proactive >= 6
            else:
                user_result["hours_since_last_proactive"] = None
                user_result["cooldown_ok"] = True  # Nunca recebeu = OK

            # Resultado final
            is_eligible = (
                user_result["has_enough_conversations"] and
                user_result["has_enough_inactivity"] and
                user_result["cooldown_ok"]
            )
            user_result["eligible"] = is_eligible

            if is_eligible:
                user_result["status"] = "ELIGIBLE - Ready to receive proactive message"
            else:
                blockers = []
                if not user_result["has_enough_conversations"]:
                    blockers.append(f"Only {total_convs}/3 conversations")
                if not user_result["has_enough_inactivity"]:
                    blockers.append(f"Only {hours_inactive:.1f}h/3h inactive")
                if not user_result["cooldown_ok"]:
                    blockers.append(f"Cooldown {user_result['hours_since_last_proactive']:.1f}h/6h")
                user_result["status"] = f"NOT ELIGIBLE: {', '.join(blockers)}"

            results.append(user_result)

        return {
            "status": "success",
            "timezone": timezone_info,
            "results": results
        }

    except Exception as e:
        logger.error(f"Error in test_proactive endpoint: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "results": results
        }

@app.get("/test/consent")
async def test_consent():
    """
    ENDPOINT DE DIAGNÓSTICO DO SISTEMA DE CONSENTIMENTO

    Acesse: https://seu-railway-url/test/consent

    Verifica:
    - Se as colunas de consentimento existem no banco
    - Estado do consentimento de cada usuário
    - Última atividade de cada usuário
    """

    try:
        from datetime import datetime
        import sqlite3

        cursor = bot_state.db.conn.cursor()

        # Verificar se as colunas existem
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]

        columns_exist = {
            "consent_given": "consent_given" in columns,
            "consent_timestamp": "consent_timestamp" in columns
        }

        # Buscar todos os usuários
        if columns_exist["consent_given"] and columns_exist["consent_timestamp"]:
            cursor.execute("""
                SELECT
                    user_id,
                    user_name,
                    platform_id,
                    registration_date,
                    last_seen,
                    consent_given,
                    consent_timestamp
                FROM users
                ORDER BY last_seen DESC
            """)
        else:
            cursor.execute("""
                SELECT
                    user_id,
                    user_name,
                    platform_id,
                    registration_date,
                    last_seen
                FROM users
                ORDER BY last_seen DESC
            """)

        users = []
        for row in cursor.fetchall():
            user_data = {
                "user_id": row[0][:8] + "...",
                "user_name": row[1],
                "telegram_id": row[2],
                "registration_date": row[3],
                "last_seen": row[4]
            }

            if columns_exist["consent_given"] and columns_exist["consent_timestamp"]:
                user_data["consent_given"] = bool(row[5]) if row[5] is not None else None
                user_data["consent_timestamp"] = row[6]
            else:
                user_data["consent_given"] = "COLUMN_MISSING"
                user_data["consent_timestamp"] = "COLUMN_MISSING"

            # Buscar total de mensagens
            stats = bot_state.db.get_user_stats(row[0])
            user_data["total_messages"] = stats.get("total_messages", 0) if stats else 0

            users.append(user_data)

        return {
            "status": "success",
            "database_columns": columns_exist,
            "migration_needed": not all(columns_exist.values()),
            "migration_command": "python migrate_add_consent.py",
            "total_users": len(users),
            "users": users
        }

    except Exception as e:
        logger.error(f"Error in test_consent endpoint: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }

@app.post("/admin/migrate/consent")
async def migrate_consent():
    """
    ENDPOINT PARA EXECUTAR A MIGRAÇÃO DE CONSENTIMENTO

    Acesse: POST https://seu-railway-url/admin/migrate/consent

    Adiciona as colunas consent_given e consent_timestamp ao banco
    e marca usuários existentes como tendo consentido (grandfathering).
    """

    try:
        cursor = bot_state.db.conn.cursor()

        # Verificar se as colunas já existem
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'consent_given' in columns and 'consent_timestamp' in columns:
            return {
                "status": "success",
                "message": "Colunas de consentimento já existem. Nada a fazer.",
                "migration_executed": False
            }

        logger.info("🔧 Executando migração de consentimento...")

        changes_made = []

        # Adicionar consent_given
        if 'consent_given' not in columns:
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN consent_given INTEGER DEFAULT 0
            """)
            changes_made.append("consent_given column added")
            logger.info("  ✓ Coluna 'consent_given' adicionada")

        # Adicionar consent_timestamp
        if 'consent_timestamp' not in columns:
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN consent_timestamp DATETIME
            """)
            changes_made.append("consent_timestamp column added")
            logger.info("  ✓ Coluna 'consent_timestamp' adicionada")

        # Marcar usuários existentes como tendo consentido (grandfathering)
        cursor.execute("""
            UPDATE users
            SET consent_given = 1,
                consent_timestamp = registration_date
            WHERE consent_given = 0
        """)

        updated = cursor.rowcount
        changes_made.append(f"{updated} existing users marked as consented (grandfathering)")
        logger.info(f"  ✓ {updated} usuários existentes marcados como tendo consentido")

        bot_state.db.conn.commit()
        logger.info("✅ Migração de consentimento concluída com sucesso!")

        return {
            "status": "success",
            "message": "Migration executed successfully",
            "migration_executed": True,
            "changes": changes_made,
            "users_updated": updated
        }

    except Exception as e:
        logger.error(f"Error in migrate_consent endpoint: {e}", exc_info=True)
        bot_state.db.conn.rollback()
        return {
            "status": "error",
            "error": str(e),
            "message": "Migration failed - database rolled back"
        }

@app.api_route("/admin/migrate/evidence", methods=["GET", "POST"])
async def migrate_evidence():
    """
    ENDPOINT PARA EXECUTAR A MIGRAÇÃO DO SISTEMA DE EVIDÊNCIAS 2.0

    Acesse via GET ou POST: https://seu-railway-url/admin/migrate/evidence

    Cria a tabela psychometric_evidence e adiciona colunas em user_psychometrics
    para rastreabilidade de evidências.
    """

    try:
        cursor = bot_state.db.conn.cursor()

        # Verificar se tabela já existe
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='psychometric_evidence'
        """)

        if cursor.fetchone():
            return {
                "status": "success",
                "message": "Tabela 'psychometric_evidence' já existe. Nada a fazer.",
                "migration_executed": False
            }

        logger.info("🔧 Executando migração do Sistema de Evidências 2.0...")

        changes_made = []

        # Criar tabela de evidências
        cursor.execute("""
            CREATE TABLE psychometric_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- Relacionamentos
                user_id TEXT NOT NULL,
                psychometric_version INTEGER NOT NULL,
                conversation_id INTEGER NOT NULL,

                -- Tipo de evidência
                dimension TEXT NOT NULL,
                trait_indicator TEXT,

                -- A evidência em si
                quote TEXT NOT NULL,
                context_before TEXT,
                context_after TEXT,

                -- Scoring
                relevance_score REAL DEFAULT 0.5,
                direction TEXT CHECK(direction IN ('positive', 'negative', 'neutral')),
                weight REAL DEFAULT 1.0,

                -- Metadados
                conversation_timestamp DATETIME,
                extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Qualidade
                confidence REAL DEFAULT 0.5,
                is_ambiguous BOOLEAN DEFAULT 0,
                extraction_method TEXT DEFAULT 'claude',

                -- Explicação
                explanation TEXT,

                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)
        changes_made.append("psychometric_evidence table created")
        logger.info("  ✓ Tabela 'psychometric_evidence' criada")

        # Criar índices
        cursor.execute("""
            CREATE INDEX idx_evidence_user_dimension
            ON psychometric_evidence(user_id, dimension)
        """)
        changes_made.append("idx_evidence_user_dimension index created")
        logger.info("  ✓ Índice: idx_evidence_user_dimension")

        cursor.execute("""
            CREATE INDEX idx_evidence_conversation
            ON psychometric_evidence(conversation_id)
        """)
        changes_made.append("idx_evidence_conversation index created")
        logger.info("  ✓ Índice: idx_evidence_conversation")

        cursor.execute("""
            CREATE INDEX idx_evidence_version
            ON psychometric_evidence(psychometric_version)
        """)
        changes_made.append("idx_evidence_version index created")
        logger.info("  ✓ Índice: idx_evidence_version")

        cursor.execute("""
            CREATE INDEX idx_evidence_direction
            ON psychometric_evidence(direction)
        """)
        changes_made.append("idx_evidence_direction index created")
        logger.info("  ✓ Índice: idx_evidence_direction")

        # Adicionar colunas à tabela user_psychometrics
        cursor.execute("PRAGMA table_info(user_psychometrics)")
        existing_columns = {col[1] for col in cursor.fetchall()}

        columns_to_add = {
            'conversations_used': 'TEXT',
            'evidence_extracted': 'BOOLEAN DEFAULT 0',
            'evidence_extraction_date': 'DATETIME',
            'red_flags': 'TEXT'
        }

        for column_name, column_type in columns_to_add.items():
            if column_name not in existing_columns:
                cursor.execute(f"""
                    ALTER TABLE user_psychometrics
                    ADD COLUMN {column_name} {column_type}
                """)
                changes_made.append(f"{column_name} column added to user_psychometrics")
                logger.info(f"  ✓ Coluna '{column_name}' adicionada")

        bot_state.db.conn.commit()
        logger.info("✅ Migração do Sistema de Evidências 2.0 concluída com sucesso!")

        return {
            "status": "success",
            "message": "Evidence System 2.0 migration executed successfully",
            "migration_executed": True,
            "changes": changes_made,
            "next_steps": [
                "1. Sistema de evidências está pronto",
                "2. Evidências serão extraídas on-demand quando visualizadas",
                "3. Cache automático para visualizações futuras"
            ]
        }

    except Exception as e:
        logger.error(f"Error in migrate_evidence endpoint: {e}", exc_info=True)
        bot_state.db.conn.rollback()
        return {
            "status": "error",
            "error": str(e),
            "message": "Migration failed - database rolled back"
        }

@app.api_route("/admin/migrate/facts-v2", methods=["GET", "POST"])
async def migrate_facts_v2_endpoint():
    """
    ENDPOINT TEMPORÁRIO: Migrar para Sistema de Fatos V2

    Acesse: GET ou POST https://seu-railway-url/admin/migrate/facts-v2

    Cria tabela user_facts_v2 com schema melhorado e migra dados antigos.
    """

    try:
        logger.info("🚀 Iniciando migração para user_facts_v2...")

        from migrate_facts_v2 import migrate_to_v2

        success = migrate_to_v2()

        if success:
            logger.info("✅ Migração concluída com sucesso!")
            return {
                "status": "success",
                "message": "Migração para user_facts_v2 concluída com sucesso",
                "next_steps": [
                    "1. Verificar logs do Railway",
                    "2. Integrar código no jung_core.py",
                    "3. Testar com mensagem: 'Minha esposa se chama [nome]'",
                    "4. Remover este endpoint depois dos testes"
                ]
            }
        else:
            logger.error("❌ Migração falhou")
            return {
                "status": "error",
                "message": "Migração falhou, verificar logs do Railway"
            }

    except Exception as e:
        logger.error(f"❌ Erro na migração: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/admin/facts-v2/status")
async def facts_v2_status():
    """
    Verifica status da migração para user_facts_v2

    Acesse: GET https://seu-railway-url/admin/facts-v2/status
    """

    try:
        cursor = bot_state.db.conn.cursor()

        # Verificar se tabela existe
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='user_facts_v2'
        """)

        v2_exists = cursor.fetchone() is not None

        result = {
            "user_facts_v2_exists": v2_exists
        }

        if v2_exists:
            # Estatísticas
            cursor.execute("SELECT COUNT(*) as count FROM user_facts_v2 WHERE is_current = 1")
            total_facts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT user_id) as count FROM user_facts_v2")
            users_with_facts = cursor.fetchone()[0]

            cursor.execute("""
                SELECT fact_category, COUNT(*) as count
                FROM user_facts_v2
                WHERE is_current = 1
                GROUP BY fact_category
            """)

            by_category = {row[0]: row[1] for row in cursor.fetchall()}

            result.update({
                "total_facts": total_facts,
                "users_with_facts": users_with_facts,
                "by_category": by_category,
                "status": "migrated"
            })
        else:
            result["status"] = "not_migrated"
            result["action"] = "Execute POST /admin/migrate/facts-v2"

        return result

    except Exception as e:
        logger.error(f"Erro ao verificar status: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/admin/facts-v2/list")
async def facts_v2_list():
    """
    Lista todos os fatos da tabela user_facts_v2

    Acesse: GET https://seu-railway-url/admin/facts-v2/list
    """

    try:
        cursor = bot_state.db.conn.cursor()
        cursor.row_factory = lambda cursor, row: {
            "id": row[0],
            "user_id": row[1],
            "category": row[2],
            "type": row[3],
            "attribute": row[4],
            "value": row[5],
            "confidence": row[6],
            "method": row[7],
            "created_at": row[8]
        }

        cursor.execute("""
            SELECT id, user_id, fact_category, fact_type, fact_attribute,
                   fact_value, confidence, extraction_method, created_at
            FROM user_facts_v2
            WHERE is_current = 1
            ORDER BY created_at DESC
        """)

        facts = cursor.fetchall()

        return {
            "status": "success",
            "total": len(facts),
            "facts": facts
        }

    except Exception as e:
        logger.error(f"Erro ao listar fatos: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.post("/admin/test-extraction")
async def test_extraction(request: dict):
    """
    Endpoint de diagnóstico para testar extração de fatos diretamente

    Uso:
    POST https://seu-railway-url/admin/test-extraction
    Body: {"message": "Sua mensagem de teste aqui"}

    Retorna:
    - O que o LLM extraiu (raw)
    - Se os fatos foram salvos
    - Possíveis erros
    """

    try:
        message = request.get("message")
        if not message:
            return {
                "status": "error",
                "error": "Campo 'message' obrigatório"
            }

        # Verificar se extractor está disponível
        if not hasattr(bot_state.db, 'fact_extractor') or not bot_state.db.fact_extractor:
            return {
                "status": "error",
                "error": "LLMFactExtractor não está inicializado",
                "hint": "Verifique se ANTHROPIC_API_KEY está configurada"
            }

        # Testar extração
        logger.info(f"[TEST] Testando extração com mensagem: {message}")

        try:
            facts = bot_state.db.fact_extractor.extract_facts(message)

            result = {
                "status": "success",
                "message": message,
                "facts_extracted": len(facts),
                "facts": []
            }

            for fact in facts:
                fact_dict = {
                    "category": fact.category,
                    "type": fact.fact_type,
                    "attribute": fact.attribute,
                    "value": fact.value,
                    "confidence": fact.confidence,
                    "context": fact.context[:100] + "..." if len(fact.context) > 100 else fact.context
                }
                result["facts"].append(fact_dict)

            logger.info(f"[TEST] Extraídos {len(facts)} fatos: {result['facts']}")

            return result

        except Exception as extraction_error:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"[TEST] Erro na extração: {extraction_error}")
            logger.error(f"[TEST] Traceback: {error_trace}")

            return {
                "status": "error",
                "error": "Erro durante extração",
                "details": str(extraction_error),
                "traceback": error_trace
            }

    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# Montar arquivos estáticos (apenas se o diretório existir)
static_dir = "admin_web/static"
if os.path.exists(static_dir) and os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"✅ Diretório static montado: {static_dir}")
else:
    logger.warning(f"⚠️  Diretório static não encontrado: {static_dir} - Continuando sem arquivos estáticos")

# Importar e incluir rotas do admin (opcional)
try:
    from admin_web.routes import router as admin_router
    app.include_router(admin_router)
    logger.info("✅ Rotas do admin web carregadas")
except Exception as e:
    import traceback
    logger.error(f"❌ Erro ao carregar admin web: {e}")
    logger.error(f"Traceback completo:\n{traceback.format_exc()}")
    logger.warning("⚠️  Admin web não disponível - Apenas bot Telegram funcionará")


if __name__ == "__main__":
    # Rodar com uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
