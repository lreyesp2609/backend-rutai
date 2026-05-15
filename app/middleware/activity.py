"""
Middleware liviano para actualizar last_active_at en cada request autenticado.

Diseño:
  - Solo actúa en requests que llevan un JWT válido (header Authorization: Bearer).
  - Usa un cache en memoria para throttle: solo hace UPDATE en la DB si han pasado
    más de 5 minutos desde el último update para ese usuario.
  - Esto evita saturar Supabase/PostgreSQL en Render free tier.
  - El UPDATE es fire-and-forget: si falla, no afecta la respuesta del endpoint.

Flujo:
  Request → Middleware extrae user_id del JWT (sin validar expiración completa,
  eso lo hace el endpoint) → Revisa cache → Si pasaron >5 min → UPDATE → Responde

Rendimiento:
  - 0 queries extra en el 99% de requests (cache hit)
  - 1 UPDATE liviano cada 5 min por usuario activo
  - Cache en memoria, sin dependencias externas (Redis no necesario para <1000 usuarios)
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from datetime import datetime, timezone
from sqlalchemy import update
import os
import time
import logging

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# Configuración
# ══════════════════════════════════════════════════════════════

# Throttle: mínimo 5 minutos entre UPDATEs por usuario
ACTIVITY_THROTTLE_SECONDS = 5 * 60  # 300 segundos

# JWT config (misma que en security.py)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# Cache en memoria: { user_id: timestamp_del_ultimo_update }
_last_update_cache: dict[int, float] = {}


# ══════════════════════════════════════════════════════════════
# Middleware
# ══════════════════════════════════════════════════════════════

class ActivityTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que actualiza usuarios.last_active_at para requests autenticados.
    
    - No bloquea la respuesta si el UPDATE falla.
    - Throttle de 5 minutos por usuario para no saturar la DB.
    - Solo procesa requests con header Authorization: Bearer <token>.
    """

    async def dispatch(self, request: Request, call_next):
        # 1. Extraer user_id del JWT (si existe)
        user_id = self._extract_user_id(request)

        # 2. Procesar el request normalmente
        response = await call_next(request)

        # 3. Actualizar actividad si corresponde (post-response, fire-and-forget)
        if user_id is not None:
            self._maybe_update_activity(user_id)

        return response

    def _extract_user_id(self, request: Request) -> int | None:
        """
        Extrae id_usuario del JWT sin validar expiración.
        
        ¿Por qué no validar expiración aquí?
        Porque el endpoint ya lo hace con Depends(decodificar_token).
        Si validáramos aquí, un token expirado no actualizaría actividad,
        lo cual es correcto — pero el decode ya ocurre en el endpoint.
        Aquí solo necesitamos saber QUIÉN es, no si su token es válido.
        
        Nota: Usamos options={"verify_exp": False} para no rechazar tokens
        que están a segundos de expirar. El endpoint se encarga de eso.
        """
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1]

        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"verify_exp": False}
            )
            return payload.get("id_usuario")
        except JWTError:
            return None

    def _maybe_update_activity(self, user_id: int) -> None:
        """
        Actualiza last_active_at solo si han pasado más de 5 minutos
        desde el último update para este usuario.
        
        Usa un UPDATE directo con SQLAlchemy Core (no ORM) para ser
        lo más liviano posible — no carga el objeto Usuario completo.
        """
        now = time.time()
        last_update = _last_update_cache.get(user_id, 0)

        if (now - last_update) < ACTIVITY_THROTTLE_SECONDS:
            return  # Throttled — no hacer nada

        # Actualizar cache ANTES del query (previene race conditions)
        _last_update_cache[user_id] = now

        try:
            # Import aquí para evitar circular imports
            from ..database.database import SessionLocal
            from ..usuarios.models import Usuario

            db = SessionLocal()
            try:
                db.execute(
                    update(Usuario)
                    .where(Usuario.id == user_id)
                    .values(last_active_at=datetime.now(timezone.utc))
                )
                db.commit()
            finally:
                db.close()

        except Exception as e:
            # Fire-and-forget: loguear pero NO romper el request
            logger.warning(f"⚠️ Error actualizando last_active_at para usuario {user_id}: {e}")
            # Revertir cache para reintentar en el próximo request
            _last_update_cache.pop(user_id, None)
