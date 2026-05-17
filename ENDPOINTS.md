# 📚 ENDPOINTS Documentation for **rutai** API

> This document groups all public REST endpoints by module, providing a quick reference for developers and integrators.

---

## 🔐 Module: **login**

| Method | URL | Description | Parameters | Example Request | Example Response |
|---|---|---|---|---|---|
| **POST** | `/login/` | Authenticate a user and obtain access/refresh tokens. | **Body** (`application/x-www-form-urlencoded`): `correo` (string), `contrasenia` (string), optional `dispositivo`, `version_app`, `ip`. | ```bash
curl -X POST "http://localhost:8000/login/" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "correo=john@example.com&contrasenia=Secret123&ip=127.0.0.1"
``` | ```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "d2f3...",
  "token_type": "bearer",
  "sesion_id": "1"
}
``` |
| **POST** | `/login/refresh` | Refresh an **access** token using a valid **refresh** token. | **Body** (`application/x-www-form-urlencoded`): `refresh_token` (string). | ```bash
curl -X POST "http://localhost:8000/login/refresh" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "refresh_token=d2f3..."
``` | ```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "new_refresh_token",
  "token_type": "bearer",
  "sesion_id": "1"
}
``` |
| **POST** | `/login/logout` | Invalidate a **refresh** token (log out). | **Body**: `refresh_token`. | ```bash
curl -X POST "http://localhost:8000/login/logout" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "refresh_token=d2f3..."
``` | ```json
{ "detail": "SESION_CERRADA" }
``` |
| **GET** | `/login/decodificar` | Decode the current JWT and return basic user info. | **Header**: `Authorization: Bearer <access_token>` | ```bash
curl -H "Authorization: Bearer <access_token>" \
     http://localhost:8000/login/decodificar
``` | ```json
{
  "id": 1,
  "nombre": "John",
  "apellido": "Doe",
  "activo": true,
  "id_rol": 2,
  "rol": "usuario",
  "correo": "john@example.com"
}
``` |

**How to modify behaviour**
- Change token expiration by editing `constants.py` (`ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`).
- Replace `create_access_token`/`create_refresh_token` implementations in `app/usuarios/security.py` to use a different signing algorithm or add custom claims.

---

## 🛡️ Module: **seguridad**

| Method | URL | Description | Parameters | Example Request | Example Response |
|---|---|---|---|---|---|
| **POST** | `/seguridad/marcar-zona` | Create a **dangerous zone** for the authenticated user. | **Body** (`application/json`): `ZonaPeligrosaCreate` (lat, lon, radio_metros, nombre, nivel_peligro, tipo, notas). | ```bash
curl -X POST "http://localhost:8000/seguridad/marcar-zona" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"lat": -2.2, "lon": -79.9, "radio_metros": 100, "nombre": "Callejón", "nivel_peligro": 3, "tipo": "shortest", "notas": "Oscuro"}'
``` | ```json
{
  "id": 5,
  "nombre": "Callejón",
  "poligono": [{"lat": -2.2, "lon": -79.9}, ...],
  "nivel_peligro": 3,
  "tipo": "shortest",
  "notas": "Oscuro",
  "radio_metros": 100,
  "activa": true,
  "fecha_creacion": "2026-05-17T15:20:00Z"
}
``` |
| **GET** | `/seguridad/mis-zonas` | Retrieve the authenticated user's dangerous zones. | Query: `activas_solo` (bool, default `true`). | ```bash
curl -H "Authorization: Bearer <token>" \
     "http://localhost:8000/seguridad/mis-zonas?activas_solo=true"
``` | ```json
[ {"id":5,"nombre":"Callejón",...}, {"id":6,"nombre":"Parque"} ]
``` |
| **POST** | `/seguridad/validar-rutas` | Validate a batch of routes against **personal** and **public** danger zones, returning safety flags and ML recommendation. | **Body** (`application/json`): `ValidarRutasRequest` (ubicacion_id, rutas: list of `Ruta`). | ```bash
curl -X POST "http://localhost:8000/seguridad/validar-rutas" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"ubicacion_id":10,"rutas":[{"geometry":"encoded_polyline","tipo":"shortest","distance":1200,"duration":300}]}'
``` | ```json
{
  "rutas_validadas": [
    {
      "tipo": "shortest",
      "es_segura": false,
      "nivel_riesgo": 4,
      "zonas_detectadas": [ {"zona_id":5,"nombre":"Callejón","nivel_peligro":4,"tipo":"shortest","porcentaje_ruta":0.75} ],
      "mensaje": "ALL_ROUTES_HIGH_RISK",
      "distancia": 1200,
      "duracion": 300,
      "zonas_publicas_detectadas": null
    }
  ],
  "tipo_ml_recomendado": "fastest",
  "todas_seguras": false,
  "mejor_ruta_segura": "fastest",
  "advertencia_general": "ALL_ROUTES_HIGH_RISK",
  "total_zonas_usuario": 3,
  "zonas_publicas_encontradas": 5
}
``` |
| **PATCH** | `/seguridad/zona/{zona_id}` | Update a personal dangerous zone (owner only). | **Path**: `zona_id` (int). **Body**: `ZonaPeligrosaUpdate` (any mutable fields). | ```bash
curl -X PATCH "http://localhost:8000/seguridad/zona/5" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Callejón 2","nivel_peligro":2}'
``` | ```json
{ "id":5, "nombre":"Callejón 2", "nivel_peligro":2, ... }
``` |
| **DELETE** | `/seguridad/zona/{zona_id}` | Delete a personal dangerous zone. | **Path**: `zona_id`. | ```bash
curl -X DELETE "http://localhost:8000/seguridad/zona/5" \
  -H "Authorization: Bearer <token>"
``` | **204 No Content** |
| **GET** | `/seguridad/estadisticas` | Get user‑specific security statistics (counts of own zones, public zones found, etc.). | No parameters. | ```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/seguridad/estadisticas
``` | ```json
{ "total_zonas":3, "zonas_publicas_encontradas":5, "rutas_validas":0 }
``` |
| **POST** | `/seguridad/zona/{zona_id}/toggle` | Activate / deactivate a zone without deleting it. | **Path**: `zona_id`. | ```bash
curl -X POST "http://localhost:8000/seguridad/zona/5/toggle" \
  -H "Authorization: Bearer <token>"
``` | ```json
{ "zona_id":5, "activa":false, "code":"ZONE_STATUS_UPDATED" }
``` |
| **POST** | `/seguridad/verificar-ubicacion-actual` | Real‑time check if the user is inside any of their active zones. | **Body**: `VerificarUbicacionRequest` (lat, lon). | ```bash
curl -X POST "http://localhost:8000/seguridad/verificar-ubicacion-actual" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"lat":-2.2,"lon":-79.9}'
``` | ```json
{ "hay_peligro": true, "zonas_detectadas":[{...}], "mensaje_alerta":"HIGH_RISK_ZONE" }
``` |
| **GET** | `/seguridad/zonas-sugeridas` | Get **public** zones near a coordinate, excluding zones the user already owns. | Query: `lat` (float), `lon` (float), optional `radio_km` (float, default 10). | ```bash
curl -H "Authorization: Bearer <token>" \
     "http://localhost:8000/seguridad/zonas-sugeridas?lat=-2.2&lon=-79.9"
``` | ```json
[ {"id":12,"nombre":"Puente","poligono":[...],"nivel_peligro":2,...} ]
``` |
| **POST** | `/seguridad/adoptar-zona/{zona_id}` | Copy a **public** zone into the user's personal collection. | **Path**: `zona_id`. | ```bash
curl -X POST "http://localhost:8000/seguridad/adoptar-zona/12" \
  -H "Authorization: Bearer <token>"
``` | ```json
{ "id":15, "nombre":"Puente", "activa":true, ... }
``` |

**How to modify behaviour**
- Adjust validation distance (`radio_busqueda_metros`) inside `validar_rutas` (line ~197). 
- Change ML recommendation model by editing `services/ucb_service.py`.
- To alter the public‑zone filter radius, modify `radio_km` default in the query endpoint.

---

## 📈 Module: **mediciones**

| Method | URL | Description | Parameters | Example Request | Example Response |
|---|---|---|---|---|---|
| **POST** | `/latencia/` | Record a single latency measurement. | **Body**: `LatenciaCreate`. | ```bash
curl -X POST "http://localhost:8000/latencia/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"endpoint":"/login/","latencia_ms":120,"dispositivo_id":"android-01","red":"wifi","sesion_id":3}'
``` | ```json
{ "id": 23, "endpoint": "/login/", "latencia_ms": 120, "timestamp": "2026-05-17T12:00:00Z" }
``` |
| **POST** | `/latencia/batch` | Record up to 50 latency measurements in one call. | **Body**: `LatenciaBatchCreate` (list of `LatenciaCreate`). | ```bash
curl -X POST "http://localhost:8000/latencia/batch" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"mediciones":[{"endpoint":"/login/","latencia_ms":110},{"endpoint":"/seguridad/marcar-zona","latencia_ms":250}]}'
``` | ```json
[ {"id":24,...}, {"id":25,...} ]
``` |
| **GET** | `/latencia/` | List latency records with optional filters. | Query: `dispositivo_id`, `endpoint`, `red`, `sesion_id`, `fecha_desde`, `fecha_hasta`. | ```bash
curl -H "Authorization: Bearer <token>" "http://localhost:8000/latencia/?endpoint=/login/"
``` | ```json
[ {"id":23,"endpoint":"/login/","latencia_ms":120,...} ]
``` |
| **GET** | `/latencia/estadisticas` | Compute percentile (p50/p95/p99) and avg/min/max latencies grouped by endpoint, device, and network. | Same query filters as list endpoint. | ```bash
curl -H "Authorization: Bearer <token>" "http://localhost:8000/latencia/estadisticas"
``` | ```json
{
  "total_requests": 152,
  "por_endpoint": [ {"endpoint":"/login/","metodo_http":"POST","p50_ms":115,"p95_ms":210,"p99_ms":250,"promedio_ms":130,"min_ms":80,"max_ms":300,"total":78} ],
  "por_dispositivo": [...],
  "por_red": {"wifi": {...}, "cellular": {...}}
}
``` |
| **POST** | `/energia/` | Record a single energy‑consumption session. | **Body**: `ConsumoEnergeticoCreate`. | ```bash
curl -X POST "http://localhost:8000/energia/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"dispositivo_id":"android-01","modo_ubicacion":"movil","consumo_pct":12.5,"duracion_minutos":30}'
``` | ```json
{ "id": 7, "dispositivo_id":"android-01", "consumo_pct":12.5, "duracion_minutos":30 }
``` |
| **GET** | `/energia/` | List energy sessions with optional filters. | Query: `dispositivo_id`, `modo_ubicacion`, `sesion_id`. | ```bash
curl -H "Authorization: Bearer <token>" "http://localhost:8000/energia/?modo_ubicacion=movil"
``` | ```json
[ {"id":7,"dispositivo_id":"android-01",...} ]
``` |
| **GET** | `/energia/estadisticas` | Aggregate energy consumption statistics per device and per location mode. | Same filters as list. | ```bash
curl -H "Authorization: Bearer <token>" "http://localhost:8000/energia/estadisticas"
``` | ```json
{
  "por_modo": {
    "movil": {"total_sesiones":12,"consumo_promedio_pct":10.2,"consumo_por_hora_pct":20.4,"temperatura_promedio_c":22.5,"dispositivos":3}
  },
  "por_dispositivo": [
    {"dispositivo_id":"android-01","modelo_dispositivo":"Pixel","modo_ubicacion":"movil","sesiones":5,"consumo_promedio_pct":11.0,"consumo_por_hora_pct":22.0}
  ]
}
``` |

**How to modify behaviour**
- Change the batch size limit in `crear_latencia_batch` (currently 50). Adjust the `percentil` function if a different rounding is required.
- Update energy‑metric aggregation windows by editing the queries in `estadisticas_energia`.

---

## 📍 Module: **tracking** (Passive GPS Tracking)

| Method | URL | Description | Parameters | Example Request | Example Response |
|---|---|---|---|---|---|
| **POST** | `/tracking/gps/punto` | Store a single GPS point sent from the mobile client. | **Body**: `PuntoGPSRequest` (lat, lon, precision, velocidad). | ```bash
curl -X POST "http://localhost:8000/tracking/gps/punto" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"lat":-2.2,"lon":-79.9,"precision":5,"velocidad":0.0}'
``` | ```json
{ "success": true, "message": "Punto GPS guardado correctamente" }
``` |
| **POST** | `/tracking/gps/lote` | Store a batch of GPS points (more efficient). | **Body**: `LotePuntosGPSRequest` (list of points). | ```bash
curl -X POST "http://localhost:8000/tracking/gps/lote" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"puntos":[{"lat":-2.2,"lon":-79.9,"precision":5,"velocidad":0},{"lat":-2.201,"lon":-79.902,"precision":5,"velocidad":0.2}]}'
``` | ```json
{ "success": true, "puntos_guardados": 2, "message": "2 puntos GPS guardados correctamente" }
``` |
| **GET** | `/tracking/viajes` | Retrieve detected trips for the current user (pagination). | Query: `skip`, `limit`, optional `ubicacion_id`. | ```bash
curl -H "Authorization: Bearer <token>" "http://localhost:8000/tracking/viajes?limit=20"
``` | ```json
[ {"id":3,"fecha_inicio":"2026-05-15T08:00:00Z","distancia_metros":12000,...}, ... ]
``` |
| **GET** | `/tracking/patrones` | List predictability patterns detected for the user. | No parameters. | ```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/tracking/patrones
``` | ```json
[ {"id":4,"predictibilidad":0.92,"es_predecible":true,...} ]
``` |
| **GET** | `/tracking/estadisticas` | General stats: total trips, trips this month, total distance, patterns, GPS points this month. | No parameters. | ```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/tracking/estadisticas
``` | ```json
{ "total_viajes": 42, "viajes_este_mes": 5, "distancia_total_km": 350.7, "total_patrones": 12, "patrones_predecibles": 8, "puntos_gps_este_mes": 145 }
``` |
| **DELETE** | `/tracking/viaje/{viaje_id}` | Delete a previously detected trip (owner only). | **Path**: `viaje_id`. | ```bash
curl -X DELETE "http://localhost:8000/tracking/viaje/3" -H "Authorization: Bearer <token>"
``` | ```json
{ "message": "Viaje eliminado correctamente" }
``` |
| **POST** | `/tracking/patron/{patron_id}/resetear-notificacion` | Reset the notification flag for a pattern (useful after the user changes routes). | **Path**: `patron_id`. | ```bash
curl -X POST "http://localhost:8000/tracking/patron/4/resetear-notificacion" -H "Authorization: Bearer <token>"
``` | ```json
{ "message": "Notificación reseteada, se volverá a analizar" }
``` |
| **POST** | `/tracking/debug/reanalizar-patron/{usuario_id}/{ubicacion_destino_id}` | Debug endpoint to force re‑analysis of a pattern with the latest algorithm. | **Path**: `usuario_id`, `ubicacion_destino_id`. | ```bash
curl -X POST "http://localhost:8000/tracking/debug/reanalizar-patron/1/10" -H "Authorization: Bearer <token>"
``` | ```json
{ "success": true, "predictibilidad": 0.95, "es_predecible": true, "viajes_similares": 3, "total_viajes": 12 }
``` |
| **POST** | `/tracking/debug/forzar-notificacion/{usuario_id}/{ubicacion_destino_id}` | Force‑send a push notification for a pattern regardless of cooldown. | **Path**: `usuario_id`, `ubicacion_destino_id`. | ```bash
curl -X POST "http://localhost:8000/tracking/debug/forzar-notificacion/1/10" -H "Authorization: Bearer <token>"
``` | ```json
{ "success": true, "message": "Notificación enviada (forzada)", "patron_creado": false, "predictibilidad": 0.95, "resultado_fcm": "sent" }
``` |

**How to modify behaviour**
- Change the points‑per‑batch limit by editing `guardar_lote_puntos_gps` in `services/passive_tracking_service.py`.
- Adjust the trip‑detection sensitivity by modifying the `_analizar_predictibilidad_destino` algorithm.
- To change the debug endpoints' visibility, wrap them with a `settings.DEBUG` guard.

---

## ⏰ Module: **reminders**

| Method | URL | Description | Parameters | Example Request | Example Response |
|---|---|---|---|---|---|
| **POST** | `/reminders/crear` | Create a new reminder. | **Body**: `ReminderCreate`. | ```bash
curl -X POST "http://localhost:8000/reminders/crear" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Tomar medicinas","fecha":"2026-05-18T09:00:00Z"}'
``` | ```json
{ "id": 9, "title": "Tomar medicinas", "fecha": "2026-05-18T09:00:00Z", "is_active": true }
``` |
| **GET** | `/reminders/listar` | List all reminders for the authenticated user. | No parameters. | ```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/reminders/listar
``` | ```json
[ {"id":9,"title":"Tomar medicinas",...}, {"id":10,"title":"Cita médico",...} ]
``` |
| **PATCH** | `/reminders/{reminder_id}/toggle` | Enable/disable a reminder. | **Path**: `reminder_id`. | ```bash
curl -X PATCH "http://localhost:8000/reminders/9/toggle" -H "Authorization: Bearer <token>"
``` | ```json
{ "id":9, "is_active": false, ... }
``` |
| **DELETE** | `/reminders/{reminder_id}/delete` | Soft‑delete a reminder (`is_deleted` flag). | **Path**: `reminder_id`. | ```bash
curl -X DELETE "http://localhost:8000/reminders/9/delete" -H "Authorization: Bearer <token>"
``` | ```json
{ "code": "REMINDER_DELETED_SUCCESS" }
``` |
| **PUT** | `/reminders/{reminder_id}/editar` | Update reminder fields. | **Path**: `reminder_id`. **Body**: `ReminderUpdate`. | ```bash
curl -X PUT "http://localhost:8000/reminders/9/editar" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Tomar vitaminas"}'
``` | ```json
{ "id":9, "title":"Tomar vitaminas", ... }
``` |
| **POST** | `/reminders/geofence-trigger` | Create a geofence trigger linked to a reminder (used for real‑time alerts). | **Body**: `GeofenceTriggerCreate`. | ```bash
curl -X POST "http://localhost:8000/reminders/geofence-trigger" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"reminder_id":9,"radio_m":100,"gps_lat":-2.2,"gps_lon":-79.9}'
``` | ```json
{ "id":3,"reminder_id":9,"radio_m":100,"gps_lat":-2.2,"gps_lon":-79.9 }
``` |

**How to modify behaviour**
- Change soft‑delete behaviour (currently just a flag) by editing `delete_reminder` in `app/recordatorios/crud.py`.
- Adjust geofence radius validation in `create_geofence_trigger` (line 45 of `seguridad.py` contains a generic check – you can add min/max limits).

---

## 👥 Module: **grupos** (Groups & Messaging)

| Method | URL | Description | Parameters | Example Request | Example Response |
|---|---|---|---|---|---|
| **POST** | `/grupos/crear` | Create a new group (owner becomes creator). | **Body**: `GrupoCreate`. | ```bash
curl -X POST "http://localhost:8000/grupos/crear" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Equipo Viajeros","descripcion":"Grupo de viajes"}'
``` | ```json
{ "id":4, "nombre":"Equipo Viajeros", "codigo_invitacion":"AB12CD", "creado_por_id":1 }
``` |
| **GET** | `/grupos/listar` | List groups the user created or is a member of. | No parameters. | ```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/grupos/listar
``` | ```json
[ {"id":4,"nombre":"Equipo Viajeros"}, {"id":7,"nombre":"Familia"} ]
``` |
| **POST** | `/grupos/unirse/{codigo}` | Join a group using an invitation code. | **Path**: `codigo`. | ```bash
curl -X POST "http://localhost:8000/grupos/unirse/AB12CD" -H "Authorization: Bearer <token>"
``` | ```json
{ "id":4, "nombre":"Equipo Viajeros", ... }
``` |
| **GET** | `/grupos/{grupo_id}/mensajes` | Retrieve latest messages of a group (default 50). | **Path**: `grupo_id`. Query: `limit`. | ```bash
curl -H "Authorization: Bearer <token>" "http://localhost:8000/grupos/4/mensajes?limit=20"
``` | ```json
[ {"id":12,"remitente_id":2,"remitente_nombre":"Ana Pérez","contenido":"Hola!","entregado":true,"leido":false,"leido_por":3}, ... ]
``` |
| **POST** | `/grupos/{grupo_id}/mensajes/{mensaje_id}/marcar-leido` | Mark a specific message as read (cannot be the sender). | **Path**: `grupo_id`, `mensaje_id`. | ```bash
curl -X POST "http://localhost:8000/grupos/4/mensajes/12/marcar-leido" -H "Authorization: Bearer <token>"
``` | ```json
{ "code": "MESSAGE_MARKED_READ", "leido": true }
``` |
| **GET** | `/grupos/{grupo_id}/integrantes` | List members of a group with roles and join dates. | **Path**: `grupo_id`. | ```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/grupos/4/integrantes
``` | ```json
{ "grupo_id":4, "grupo_nombre":"Equipo Viajeros", "total_integrantes":3, "integrantes":[ {"usuario_id":1,"nombre_completo":"Juan Pérez","rol":"creador","activo":true,"fecha_union":"2026-01-10T12:00:00Z","es_creador":true}, ... ] }
``` |
| **POST** | `/grupos/{grupo_id}/salir` | Leave a group (deactivate membership). | **Path**: `grupo_id`. | ```bash
curl -X POST "http://localhost:8000/grupos/4/salir" -H "Authorization: Bearer <token>"
``` | ```json
{ "code": "LEFT_GROUP_SUCCESS" }
``` |
| **DELETE** | `/grupos/eliminar/{grupo_id}` | Delete a group (creator only). | **Path**: `grupo_id`. | ```bash
curl -X DELETE "http://localhost:8000/grupos/eliminar/4" -H "Authorization: Bearer <token>"
``` | ```json
{ "code": "GROUP_DELETED_SUCCESS" }
``` |
| **POST** | `/grupos/{grupo_id}/mensajes/marcar-entregados` | Mark all messages in the group (that are not sent by the user) as delivered. | **Path**: `grupo_id`. | ```bash
curl -X POST "http://localhost:8000/grupos/4/mensajes/marcar-entregados" -H "Authorization: Bearer <token>"
``` | ```json
{ "message": "5 mensajes marcados como entregados", "mensajes_marcados":5, "mensaje_ids":[12,13,14,15,16] }
``` |

**How to modify behaviour**
- Change the maximum number of messages returned by editing the `limit` default in `obtener_mensajes_grupo` (currently 50).
- To switch from soft‑delete to hard‑delete for groups, modify `eliminar_grupo` implementation.
- Adjust the WebSocket broadcast logic in `marcar_mensajes_entregados` if you want asynchronous pushes via a background task instead of awaiting each broadcast.

---

## 📍 Module: **ubicaciones** (User Locations)

| Method | URL | Description | Parameters | Example Request | Example Response |
|---|---|---|---|---|---|
| **POST** | `/ubicaciones/` | Create a new user location (e.g., *Home*, *Work*). | **Body**: `UbicacionUsuarioCreate`. | ```bash
curl -X POST "http://localhost:8000/ubicaciones/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Casa","latitud":-2.2,"longitud":-79.9}'
``` | ```json
{ "id":3, "nombre":"Casa", "latitud":-2.2, "longitud":-79.9 }
``` |
| **GET** | `/ubicaciones/` | List all locations for the current user. | No parameters. | ```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/ubicaciones/
``` | ```json
[ {"id":3,"nombre":"Casa",...}, {"id":4,"nombre":"Trabajo",...} ]
``` |
| **GET** | `/ubicaciones/{ubicacion_id}` | Retrieve a single location by id. | **Path**: `ubicacion_id`. | ```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/ubicaciones/3
``` | ```json
{ "id":3, "nombre":"Casa", "latitud":-2.2, "longitud":-79.9 }
``` |
| **PUT** | `/ubicaciones/{ubicacion_id}` | Update a location (name change, coordinates). | **Path**: `ubicacion_id`. **Body**: `UbicacionUsuarioUpdate`. | ```bash
curl -X PUT "http://localhost:8000/ubicaciones/3" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Casa Nueva"}'
``` | ```json
{ "id":3, "nombre":"Casa Nueva", ... }
``` |
| **DELETE** | `/ubicaciones/{ubicacion_id}` | Delete a location (hard delete). | **Path**: `ubicacion_id`. | ```bash
curl -X DELETE "http://localhost:8000/ubicaciones/3" -H "Authorization: Bearer <token>"
``` | **200 OK** with the deleted object returned. |

**How to modify behaviour**
- Enforce unique location names per user by adjusting the `crear_ubicacion` CRUD function (currently returns `None` on duplicate). 
- Change the delete strategy (soft vs hard) by modifying `eliminar_ubicacion` in `app/ubicaciones/crud.py`.

---

> **Tip**: All endpoints require a valid JWT (`Authorization: Bearer <token>`) unless stated otherwise. Use the `/login/` endpoints to obtain tokens.

*Generated with love by **Antigravity** – your premium AI coding assistant.*
