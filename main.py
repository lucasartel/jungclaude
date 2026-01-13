import asyncio
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import logging
import os
import sys
import sqlite3
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
# MEMORY CONSOLIDATION SCHEDULER
# ============================================================================

async def consolidation_scheduler():
    """
    Background task que roda consolidação todo dia 1º às 03:00 UTC

    Usa asyncio.sleep() para calcular próxima execução, sem dependências externas
    """
    from jung_memory_consolidation import run_consolidation_job_async
    from datetime import datetime, timedelta
    import calendar

    logger.info("📦 Consolidation scheduler iniciado")

    # Aguardar 1 minuto para garantir inicialização completa
    await asyncio.sleep(60)

    while True:
        try:
            now = datetime.utcnow()

            # Calcular próximo dia 1º às 03:00 UTC
            if now.day == 1 and now.hour < 3:
                # Hoje é dia 1 e ainda não passou das 03:00
                next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
            else:
                # Próximo mês
                if now.month == 12:
                    next_month = 1
                    next_year = now.year + 1
                else:
                    next_month = now.month + 1
                    next_year = now.year

                next_run = datetime(next_year, next_month, 1, 3, 0, 0)

            # Calcular tempo de espera
            wait_seconds = (next_run - now).total_seconds()

            logger.info(f"📅 Próxima consolidação: {next_run.strftime('%Y-%m-%d %H:%M')} UTC (em {wait_seconds/3600:.1f}h)")

            # Esperar até o momento
            await asyncio.sleep(wait_seconds)

            # Executar consolidação
            logger.info("🔄 Iniciando consolidação automática mensal...")
            try:
                await run_consolidation_job_async(bot_state.db)
                logger.info("✅ Consolidação automática concluída")
            except Exception as e:
                logger.error(f"❌ Erro na consolidação automática: {e}")
                import traceback
                logger.error(traceback.format_exc())

        except Exception as e:
            logger.error(f"❌ Erro crítico no consolidation scheduler: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Em caso de erro, aguardar 1 hora e tentar novamente
            await asyncio.sleep(3600)


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

    # 0. Aplicar migrations pendentes
    logger.info("=" * 70)
    logger.info("🔧 SISTEMA DE MIGRATIONS")
    logger.info("=" * 70)
    try:
        from database_migrations import run_migrations_on_startup
        migrations_ok = run_migrations_on_startup()
        if not migrations_ok:
            logger.error("❌ ERRO: Migrations falharam - servidor pode não funcionar corretamente")
    except Exception as e:
        logger.error(f"❌ ERRO ao executar migrations: {e}")
        import traceback
        logger.error(traceback.format_exc())

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

    # ✨ Iniciar scheduler de consolidação de memórias (Fase 4)
    consolidation_task = asyncio.create_task(consolidation_scheduler())
    logger.info("✅ Scheduler de consolidação de memórias ativado (mensal: dia 1 às 03:00 UTC)")

    # ✨ Iniciar scheduler de identidade do agente (Fase 2)
    try:
        from agent_identity_consolidation_job import identity_consolidation_scheduler
        from identity_config import IDENTITY_CONSOLIDATION_INTERVAL_HOURS
        identity_task = asyncio.create_task(identity_consolidation_scheduler())
        logger.info(f"✅ Scheduler de identidade do agente ativado (a cada {IDENTITY_CONSOLIDATION_INTERVAL_HOURS}h)")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar scheduler de identidade: {e}")

    # ✨ Iniciar scheduler de bridge identidade-ruminação (Fase 3)
    try:
        from identity_rumination_bridge import identity_rumination_sync_scheduler
        bridge_task = asyncio.create_task(identity_rumination_sync_scheduler())
        logger.info("✅ Scheduler de bridge identidade-ruminação ativado (a cada 6h)")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar scheduler de bridge: {e}")

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

    # Parar scheduler de consolidação
    consolidation_task.cancel()
    try:
        await consolidation_task
    except asyncio.CancelledError:
        logger.info("✅ Scheduler de consolidação cancelado")

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
async def facts_v2_list(user_id: str = None):
    """
    Lista todos os fatos da tabela user_facts_v2 com análise completa

    Acesse: GET https://seu-railway-url/admin/facts-v2/list
    Filtrar por usuário: GET https://seu-railway-url/admin/facts-v2/list?user_id=USER_ID
    """

    try:
        cursor = bot_state.db.conn.cursor()
        cursor.row_factory = sqlite3.Row

        # Buscar fatos (com filtro opcional de user_id)
        if user_id:
            cursor.execute("""
                SELECT id, user_id, fact_category, fact_type, fact_attribute,
                       fact_value, confidence, extraction_method, context, created_at
                FROM user_facts_v2
                WHERE is_current = 1 AND user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT id, user_id, fact_category, fact_type, fact_attribute,
                       fact_value, confidence, extraction_method, context, created_at
                FROM user_facts_v2
                WHERE is_current = 1
                ORDER BY created_at DESC
            """)

        facts = cursor.fetchall()

        # Organizar por categoria
        by_category = {}
        by_user = {}

        for fact in facts:
            cat = fact['fact_category']
            uid = fact['user_id']

            # Por categoria
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append({
                "id": fact['id'],
                "user_id": fact['user_id'],
                "type": fact['fact_type'],
                "attribute": fact['fact_attribute'],
                "value": fact['fact_value'],
                "confidence": fact['confidence'],
                "method": fact['extraction_method'],
                "context": fact['context'][:80] + "..." if fact['context'] and len(fact['context']) > 80 else fact['context'],
                "created_at": fact['created_at']
            })

            # Por usuário
            if uid not in by_user:
                by_user[uid] = {
                    "total": 0,
                    "by_category": {}
                }
            by_user[uid]["total"] += 1
            if cat not in by_user[uid]["by_category"]:
                by_user[uid]["by_category"][cat] = 0
            by_user[uid]["by_category"][cat] += 1

        # Estatísticas por categoria
        category_stats = {}
        for cat, items in by_category.items():
            category_stats[cat] = {
                "total": len(items),
                "avg_confidence": sum(f['confidence'] for f in items) / len(items) if items else 0,
                "methods": {}
            }

            # Contar métodos de extração
            for item in items:
                method = item['method']
                if method not in category_stats[cat]["methods"]:
                    category_stats[cat]["methods"][method] = 0
                category_stats[cat]["methods"][method] += 1

        return {
            "status": "success",
            "summary": {
                "total_facts": len(facts),
                "total_users": len(by_user),
                "categories": list(by_category.keys()),
                "category_breakdown": {cat: len(items) for cat, items in by_category.items()}
            },
            "category_stats": category_stats,
            "users": by_user,
            "facts_by_category": by_category,
            "all_facts": [dict(f) for f in facts]  # Lista completa no final
        }

    except Exception as e:
        import traceback
        logger.error(f"Erro ao listar fatos: {e}")
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.api_route("/admin/test-consolidation", methods=["GET", "POST"])
async def test_consolidation(user_id: str = None):
    """
    ENDPOINT DE TESTE: Consolidação de Memórias

    Acesse: GET https://seu-railway-url/admin/test-consolidation

    Testa o sistema de consolidação de memórias (Fase 4):
    - Executa consolidação para um usuário específico ou todos
    - Mostra clusters criados
    - Exibe memórias consolidadas
    - Retorna estatísticas

    Parâmetros:
    - user_id (opcional): ID do usuário para consolidar (se vazio, consolida todos)
    """

    try:
        from jung_memory_consolidation import MemoryConsolidator
        from datetime import datetime
        import sqlite3

        results = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "consolidation_results": []
        }

        consolidator = MemoryConsolidator(bot_state.db)

        # Se user_id especificado, consolidar apenas esse usuário
        if user_id:
            logger.info(f"📦 Consolidando memórias para user_id={user_id}")

            try:
                consolidator.consolidate_user_memories(user_id, lookback_days=365)

                # Buscar memórias consolidadas criadas
                if bot_state.db.chroma_enabled:
                    consolidated_docs = bot_state.db.vectorstore._collection.get(
                        where={
                            "$and": [
                                {"user_id": {"$eq": user_id}},
                                {"type": {"$eq": "consolidated"}}
                            ]
                        }
                    )

                    consolidated_count = len(consolidated_docs.get('ids', []))

                    results["consolidation_results"].append({
                        "user_id": user_id[:8] + "...",
                        "status": "success",
                        "consolidated_memories_created": consolidated_count,
                        "documents": []
                    })

                    # Adicionar detalhes das memórias consolidadas
                    if consolidated_count > 0:
                        for i, doc_id in enumerate(consolidated_docs['ids']):
                            metadata = consolidated_docs['metadatas'][i]
                            doc_content = consolidated_docs['documents'][i]

                            results["consolidation_results"][-1]["documents"].append({
                                "id": doc_id,
                                "topic": metadata.get('topic'),
                                "period": f"{metadata.get('period_start')} a {metadata.get('period_end')}",
                                "conversations_count": metadata.get('count'),
                                "avg_tension": metadata.get('avg_tension'),
                                "avg_affective": metadata.get('avg_affective'),
                                "summary_preview": doc_content[:300] + "..." if len(doc_content) > 300 else doc_content
                            })
                else:
                    results["consolidation_results"].append({
                        "user_id": user_id[:8] + "...",
                        "status": "success_no_chroma",
                        "message": "ChromaDB desabilitado, consolidação não criou documentos"
                    })

            except Exception as e:
                results["consolidation_results"].append({
                    "user_id": user_id[:8] + "...",
                    "status": "error",
                    "error": str(e)
                })

        # Se não especificou user_id, consolidar todos os usuários
        else:
            logger.info("📦 Consolidando memórias para TODOS os usuários")

            cursor = bot_state.db.conn.cursor()
            cursor.execute("SELECT DISTINCT user_id FROM conversations")
            all_user_ids = [row[0] for row in cursor.fetchall()]

            results["total_users"] = len(all_user_ids)

            for uid in all_user_ids[:10]:  # Limitar a 10 para não travar
                try:
                    consolidator.consolidate_user_memories(uid, lookback_days=90)

                    # Contar consolidadas criadas
                    if bot_state.db.chroma_enabled:
                        consolidated_docs = bot_state.db.vectorstore._collection.get(
                            where={
                                "$and": [
                                    {"user_id": {"$eq": uid}},
                                    {"type": {"$eq": "consolidated"}}
                                ]
                            }
                        )
                        consolidated_count = len(consolidated_docs.get('ids', []))
                    else:
                        consolidated_count = 0

                    results["consolidation_results"].append({
                        "user_id": uid[:8] + "...",
                        "status": "success",
                        "consolidated_memories": consolidated_count
                    })

                except Exception as e:
                    results["consolidation_results"].append({
                        "user_id": uid[:8] + "...",
                        "status": "error",
                        "error": str(e)
                    })

            if len(all_user_ids) > 10:
                results["note"] = f"Processados apenas os primeiros 10 de {len(all_user_ids)} usuários para evitar timeout"

        # Estatísticas globais de consolidação
        if bot_state.db.chroma_enabled:
            try:
                all_consolidated = bot_state.db.vectorstore._collection.get(
                    where={"type": {"$eq": "consolidated"}}
                )

                results["global_stats"] = {
                    "total_consolidated_memories": len(all_consolidated.get('ids', [])),
                    "topics": {}
                }

                # Contar por tópico
                for metadata in all_consolidated.get('metadatas', []):
                    topic = metadata.get('topic', 'unknown')
                    if topic not in results["global_stats"]["topics"]:
                        results["global_stats"]["topics"][topic] = 0
                    results["global_stats"]["topics"][topic] += 1

            except Exception as e:
                results["global_stats"] = {"error": str(e)}

        return results

    except Exception as e:
        logger.error(f"Erro no endpoint de teste de consolidação: {e}")
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.api_route("/admin/api/memory-metrics", methods=["GET", "POST"])
async def memory_metrics(user_id: str = None, format: str = "json"):
    """
    ENDPOINT DE MÉTRICAS: Monitoramento de Qualidade de Memória (Fase 6)

    Acesse: GET https://seu-railway-url/admin/api/memory-metrics

    Fornece métricas de qualidade do sistema de memória:
    - Cobertura (% conversas embedadas)
    - Gaps (períodos sem memórias)
    - Estatísticas de retrieval
    - Métricas globais do sistema

    Parâmetros:
    - user_id (opcional): ID do usuário para relatório individual
    - format (opcional): "json" (padrão) ou "text" (relatório formatado)

    Retorna:
    - Se user_id fornecido: relatório individual
    - Se user_id omitido: métricas globais do sistema
    """

    try:
        from jung_memory_metrics import MemoryQualityMetrics, generate_formatted_system_report

        metrics = MemoryQualityMetrics(bot_state.db)

        # Relatório individual
        if user_id:
            if format == "text":
                report = metrics.generate_user_report(user_id)
                return {"user_id": user_id[:12] + "...", "report": report}
            else:
                coverage = metrics.calculate_coverage(user_id)
                gaps = metrics.detect_memory_gaps(user_id, gap_threshold_days=7)
                retrieval_stats = metrics.calculate_retrieval_stats(user_id)

                return {
                    "user_id": user_id[:12] + "...",
                    "coverage": coverage,
                    "gaps": gaps,
                    "retrieval_stats": retrieval_stats
                }

        # Métricas globais
        else:
            if format == "text":
                report = generate_formatted_system_report(bot_state.db)
                return {"system_report": report}
            else:
                system_metrics = metrics.generate_system_metrics()
                return system_metrics

    except Exception as e:
        logger.error(f"Erro no endpoint de métricas: {e}")
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.api_route("/admin/test-extraction", methods=["GET", "POST"])
async def test_extraction(request: Request = None, message: str = None):
    """
    Endpoint de diagnóstico para testar extração de fatos diretamente

    Uso GET: https://seu-railway-url/admin/test-extraction?message=Sua+mensagem
    Uso POST: Body: {"message": "Sua mensagem de teste aqui"}

    Retorna:
    - O que o LLM extraiu (raw)
    - Se os fatos foram salvos
    - Possíveis erros
    """

    try:
        # Aceitar tanto GET quanto POST
        if request and request.method == "POST":
            body = await request.json()
            message = body.get("message")

        if not message:
            return {
                "status": "error",
                "error": "Campo 'message' obrigatório",
                "usage": {
                    "GET": "/admin/test-extraction?message=Sua+mensagem",
                    "POST": "Body: {\"message\": \"Sua mensagem\"}"
                }
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

# Rotas de análise Jung (protegidas com session-based auth - apenas Master Admin)
# MIGRADO: Agora usa require_master ao invés de HTTP Basic Auth
try:
    from admin_web.routes import router as admin_router
    app.include_router(admin_router)
    logger.info("✅ Rotas de análise Jung carregadas (protegidas - Master Admin only)")
except Exception as e:
    import traceback
    logger.error(f"❌ Erro ao carregar rotas de análise: {e}")
    logger.error(f"Traceback completo:\n{traceback.format_exc()}")
    logger.warning("⚠️  Rotas de análise não disponíveis")

# Rotas de autenticação multi-tenant
try:
    from admin_web.routes.auth_routes import router as auth_router, init_auth_routes
    from admin_web.auth.middleware import init_middleware

    # Inicializar sistemas de autenticação no startup
    # Usar bot_state.db que é o DatabaseManager já inicializado
    if hasattr(bot_state, 'db') and bot_state.db:
        init_middleware(bot_state.db)
        init_auth_routes(bot_state.db)
        app.include_router(auth_router)
        logger.info("✅ Rotas de autenticação multi-tenant carregadas")
    else:
        logger.warning("⚠️  DatabaseManager não disponível - auth routes não carregadas")
except Exception as e:
    import traceback
    logger.error(f"❌ Erro ao carregar auth routes: {e}")
    logger.error(traceback.format_exc())

# Rotas de dashboards multi-tenant
try:
    from admin_web.routes.dashboard_routes import router as dashboard_router, init_dashboard_routes

    # Inicializar dashboards
    if hasattr(bot_state, 'db') and bot_state.db:
        init_dashboard_routes(bot_state.db)
        app.include_router(dashboard_router)
        logger.info("✅ Rotas de dashboards multi-tenant carregadas")
    else:
        logger.warning("⚠️  DatabaseManager não disponível - dashboard routes não carregadas")
except Exception as e:
    import traceback
    logger.error(f"❌ Erro ao carregar dashboard routes: {e}")
    logger.error(traceback.format_exc())

# Rotas de gestão de organizações
try:
    from admin_web.routes.organization_routes import router as org_router, init_organization_routes

    if hasattr(bot_state, 'db') and bot_state.db:
        init_organization_routes(bot_state.db)
        app.include_router(org_router)
        logger.info("✅ Rotas de gestão de organizações carregadas")
    else:
        logger.warning("⚠️  DatabaseManager não disponível - organization routes não carregadas")
except Exception as e:
    import traceback
    logger.error(f"❌ Erro ao carregar organization routes: {e}")
    logger.error(traceback.format_exc())

# Rotas de gestão de admin users
try:
    from admin_web.routes.admin_user_routes import router as admin_user_router, init_admin_user_routes

    if hasattr(bot_state, 'db') and bot_state.db:
        init_admin_user_routes(bot_state.db)
        app.include_router(admin_user_router)
        logger.info("✅ Rotas de gestão de admin users carregadas")
    else:
        logger.warning("⚠️  DatabaseManager não disponível - admin user routes não carregadas")
except Exception as e:
    import traceback
    logger.error(f"❌ Erro ao carregar admin user routes: {e}")
    logger.error(traceback.format_exc())

# ⚠️ ROTA DE MIGRAÇÃO REMOVIDA - Migração já foi executada com sucesso
# A rota de migração foi comentada por segurança após a execução bem-sucedida
# Se precisar executar novamente, descomente temporariamente as linhas abaixo:
# try:
#     from admin_web.routes.migration_route import router as migration_router
#     app.include_router(migration_router)
#     logger.info("✅ Rota de migração multi-tenant carregada")
#     logger.warning("⚠️  LEMBRETE: Remover migration_route após executar a migração!")
# except Exception as e:
#     logger.warning(f"⚠️  Rota de migração não disponível: {e}")

# ✅ DEBUG CONCLUÍDO - Endpoint removido por segurança
# O sistema de invite links está funcionando corretamente

# ============================================================================
# ROTAS DE IDENTIDADE DO AGENTE (Fase 5) - MOVIDAS PARA MODULE
# ============================================================================
try:
    from admin_web.routes.agent_identity_routes import router as agent_identity_router
    app.include_router(agent_identity_router)
    logger.info("✅ Rotas de identidade do agente carregadas (protegidas - Master Admin only)")
except Exception as e:
    logger.warning(f"⚠️  Rotas de identidade do agente não disponíveis: {e}")


# ============================================================================
# ENDPOINT TEMPORÁRIO: FORÇAR MIGRATION DE IDENTIDADE
# ============================================================================
@app.post("/admin/force-identity-migration")
async def force_identity_migration(request: Request):
    """
    TEMPORÁRIO: Força aplicação da migration de identidade do agente

    Remover após uso!
    """
    try:
        from force_apply_identity_migration import apply_identity_migration, find_database

        db_path = find_database()
        logger.info(f"🔧 Forçando migration de identidade em: {db_path}")

        apply_identity_migration(db_path)

        return {
            "success": True,
            "message": "Migration aplicada com sucesso",
            "database": str(db_path)
        }
    except Exception as e:
        logger.error(f"❌ Erro ao forçar migration: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Rodar com uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
