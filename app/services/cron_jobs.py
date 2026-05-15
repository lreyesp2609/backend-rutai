"""
Cron Job: Silent FCM Ping para mantener sesiones Android activas.

Ejecuta cada 10 minutos:
  1. Consulta usuarios con last_active_at en las últimas 2 horas
     que tengan al menos un fcm_token registrado
  2. Envía un FCM Data Message silencioso a TODOS sus tokens
  3. Limpia automáticamente tokens inválidos (via fcm_service)
  4. Loguea resumen de la ejecución

Restricciones (Render free tier):
  - Batches de máximo 50 usuarios por ejecución
  - Sin concurrencia: si una ejecución anterior no terminó, se salta
  - Queries livianas con JOIN explícito (no lazy loading)

Dependencia: apscheduler >= 3.10
  pip install apscheduler
  (o agregar 'APScheduler==3.10.4' a requirements.txt)
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# Configuración
# ══════════════════════════════════════════════════════════════

PING_INTERVAL_MINUTES = 10        # Cada cuánto corre el cron
ACTIVE_WINDOW_HOURS = 2           # Usuarios activos en las últimas N horas
MAX_USERS_PER_BATCH = 50          # Límite por batch (Render free tier)

# Scheduler global
scheduler = AsyncIOScheduler()


# ══════════════════════════════════════════════════════════════
# Job principal
# ══════════════════════════════════════════════════════════════

async def silent_ping_job():
    """
    Job que envía FCM silent pings a usuarios con actividad reciente.
    
    Query: usuarios WHERE last_active_at > NOW() - 2h
           AND tiene al menos 1 fcm_token
    Batch: máximo 50 usuarios por ejecución
    """
    from app.database.database import SessionLocal
    from app.usuarios.models import Usuario, FCMToken
    from app.services.fcm_service import fcm_service

    logger.info("⏰ Silent ping job iniciado")

    db = SessionLocal()
    try:
        # Ventana de actividad: últimas 2 horas
        cutoff = datetime.now(timezone.utc) - timedelta(hours=ACTIVE_WINDOW_HOURS)

        # Query: usuarios activos con tokens FCM
        # Usamos joinedload para cargar fcm_tokens en la misma query (1 round-trip)
        usuarios = (
            db.query(Usuario)
            .options(joinedload(Usuario.fcm_tokens))
            .filter(
                and_(
                    Usuario.last_active_at.isnot(None),
                    Usuario.last_active_at > cutoff,
                    Usuario.activo == True
                )
            )
            .limit(MAX_USERS_PER_BATCH)
            .all()
        )

        # Filtrar usuarios que efectivamente tienen tokens
        usuarios_con_tokens = [
            u for u in usuarios if u.fcm_tokens and len(u.fcm_tokens) > 0
        ]

        if not usuarios_con_tokens:
            logger.info("📭 Silent ping: 0 usuarios activos con tokens FCM")
            return

        # Contadores
        total_sent = 0
        total_cleaned = 0
        total_errors = 0
        total_tokens = 0

        # Enviar pings
        for usuario in usuarios_con_tokens:
            for fcm_token_obj in usuario.fcm_tokens:
                total_tokens += 1
                result = await fcm_service.send_silent_refresh_ping(fcm_token_obj.token)

                if result == "sent":
                    total_sent += 1
                elif result == "invalid_token":
                    total_cleaned += 1
                elif result == "error":
                    total_errors += 1

        # Resumen
        logger.info(
            f"📊 Ping batch: {total_sent} sent, {total_cleaned} cleaned, "
            f"{total_errors} errors | "
            f"{len(usuarios_con_tokens)} usuarios, {total_tokens} tokens"
        )

    except Exception as e:
        logger.error(f"❌ Error en silent ping job: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════
# Inicialización del scheduler
# ══════════════════════════════════════════════════════════════

def start_scheduler():
    """
    Inicia el scheduler con el job de silent ping.
    Llamar desde main.py en el evento startup.
    
    - max_instances=1: si la ejecución anterior no terminó, se salta
    - misfire_grace_time=60: si se retrasa hasta 60s, ejecutar igual
    """
    scheduler.add_job(
        silent_ping_job,
        trigger=IntervalTrigger(minutes=PING_INTERVAL_MINUTES),
        id="silent_fcm_ping",
        name="Silent FCM Ping - Keep Android sessions alive",
        max_instances=1,
        misfire_grace_time=60,
        replace_existing=True
    )

    scheduler.start()
    logger.info(f"🕐 Scheduler iniciado: silent ping cada {PING_INTERVAL_MINUTES} minutos")


def stop_scheduler():
    """
    Detiene el scheduler limpiamente.
    Llamar desde main.py en el evento shutdown.
    """
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("🛑 Scheduler detenido")
