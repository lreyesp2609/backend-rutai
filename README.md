# 🗂️ RutAI Backend

## 📖 Descripción del proyecto

`rutai` es una API **RESTful** basada en **FastAPI** que sirve como backend para la aplicación *RutAI*. Proporciona servicios de autenticación, gestión de usuarios, tracking de ubicación, zonas de seguridad, grupos, recordatorios, notificaciones push (Firebase FCM) y métricas de experimentos de geofencing.

---

## 🛠️ Tecnologías usadas

| Categoría            | Tecnologías                                         |
|----------------------|-----------------------------------------------------|
| Framework            | FastAPI (Python 3.12)                               |
| Base de datos        | PostgreSQL vía Supabase (Transaction Pooler)        |
| ORM                  | SQLAlchemy 2.0                                      |
| Validación           | Pydantic v2 + pydantic-settings                     |
| Autenticación        | JWT (python-jose / PyJWT) + bcrypt                  |
| Notificaciones push  | Firebase Admin SDK (FCM)                            |
| Tiempo real          | WebSockets nativos de FastAPI                       |
| Deploy               | Render (Web Service)                                |
| Contenedores         | Docker (multi-stage build) + Docker Compose         |

---

## 📦 Requisitos previos

- **Python ≥ 3.12**
- **Docker Desktop** (para levantar localmente con contenedor)
- **Cuenta en Supabase** (base de datos PostgreSQL gestionada)
- **Proyecto Firebase** con FCM habilitado (solo para notificaciones push)

---

## 🚀 Ejecución local

### Opción A — Con Docker (recomendado)

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/backend-rutai.git
   cd backend-rutai
   ```

2. **Crear archivo de variables de entorno**
   ```bash
   cp .env.example .env
   ```
   Edita `.env` y rellena al menos las 4 variables obligatorias (ver sección *Variables de entorno*).

3. **Build y levantar**
   ```bash
   docker build -t rutai-backend:local .
   docker compose up
   ```
   La API estará disponible en `http://localhost:8000`.  
   Documentación interactiva: `http://localhost:8000/docs`.

### Opción B — Sin Docker (entorno virtual)

1. **Crear y activar un entorno virtual**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate        # Windows
   # source .venv/bin/activate     # macOS/Linux
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   # Solo para desarrollo (hot-reload, tests):
   pip install -r requirements-dev.txt
   ```

3. **Crear archivo `.env`** (igual que Opción A, paso 2)

4. **Ejecutar la API**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## 🔑 Variables de entorno

Copia `.env.example` como `.env` y rellena los valores. Consulta el propio `.env.example` para la descripción detallada de cada variable.

### Obligatorias — la app NO arranca sin estas

| Variable      | Descripción                                              |
|---------------|----------------------------------------------------------|
| `DB_USER`     | Usuario de la base de datos (ej: `postgres.xxxxxxxxxxx`) |
| `DB_PASSWORD` | Contraseña de la base de datos                           |
| `DB_HOST`     | Host de Supabase Transaction Pooler                      |
| `SECRET_KEY`  | Clave para firmar JWTs. Generar: `openssl rand -hex 32`  |

### Opcionales — tienen valores por defecto funcionales

| Variable                        | Default                              | Descripción                               |
|---------------------------------|--------------------------------------|-------------------------------------------|
| `APP_NAME`                      | `"Mi API Backend"`                   | Nombre visible en `/docs` y `/health`     |
| `DEBUG`                         | `False`                              | Modo debug de FastAPI                     |
| `DB_PORT`                       | `6543`                               | Puerto de Supabase Transaction Pooler     |
| `DB_NAME`                       | `postgres`                           | Nombre de la base de datos                |
| `ALGORITHM`                     | `HS256`                              | Algoritmo de firma JWT                    |
| `ACCESS_TOKEN_EXPIRE_MINUTES`   | `30`                                 | Duración del access token en minutos      |
| `API_BASE_URL`                  | `http://localhost:8000`              | URL base de la API                        |
| `ALLOWED_ORIGINS`               | `http://localhost:3000,...`          | Orígenes CORS permitidos (coma-separated) |
| `GEOFENCE_MATCH_WINDOW_SECONDS` | `30`                                 | Ventana de coincidencia para geofencing   |
| `FIREBASE_CREDENTIALS`          | _(vacío)_                            | JSON de credenciales Firebase (una línea). Sin esto, FCM no funciona pero la app arranca. |

---

## 🌐 Despliegue en Render

1. **Crear un nuevo Web Service** en Render y conectar el repositorio de GitHub.
2. **Configurar entorno** en *Environment*:
   - Añadir las 4 variables obligatorias y cualquier opcional que necesites.
   - Para `FIREBASE_CREDENTIALS`: pegar el JSON completo en una sola línea directamente en el campo de Render (no usar archivo).
3. **Build Command**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Start Command**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
5. **Deploy automático**: cada push a `main` dispara un nuevo deploy.

> **Alternativa con Docker en Render:** Render detecta el `Dockerfile` automáticamente si seleccionas *Docker* como runtime. El multi-stage build producirá una imagen más pequeña y segura.

---

## 📂 Estructura del proyecto

```
backend-rutai/
├── app/
│   ├── database/
│   │   ├── config.py              # Settings (Pydantic) — carga .env
│   │   ├── database.py            # Engine y SessionLocal de SQLAlchemy
│   │   └── seed.py                # Datos iniciales (roles, admin)
│   ├── usuarios/                  # Auth, JWT, modelos de usuario
│   ├── login/                     # Endpoints de login
│   ├── ubicaciones/               # Gestión de ubicaciones e historial
│   ├── grupos/                    # Grupos de usuarios + WebSockets
│   ├── seguridad/                 # Zonas de seguridad / riesgo
│   ├── tracking/                  # Tracking en tiempo real
│   ├── recordatorios/             # Recordatorios con APScheduler
│   ├── services/                  # FCM, cron jobs
│   ├── experimento/               # Métricas de geofencing
│   ├── mediciones/                # Latencia y métricas de rendimiento
│   ├── middleware/                # Activity tracking
│   └── main.py                    # Punto de entrada FastAPI
├── .env.example                   # Plantilla de variables de entorno
├── requirements.txt               # Dependencias de producción
├── requirements-dev.txt           # Dependencias de desarrollo (watchfiles, pytest)
├── Dockerfile                     # Multi-stage build (builder + runtime)
├── docker-compose.yml             # Configuración local con healthcheck y límites
├── .dockerignore                  # Excluye .env, .git, __pycache__, etc.
└── README.md                      # Este archivo
```

---

## 🏥 Health Check

La API expone un endpoint de salud que verifica la conectividad con la base de datos:

```
GET /health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "app": "RutAI Backend",
  "version": "1.0.0",
  "database": "connected"
}
```

---

> **¡Listo!** Con Docker, solo necesitas las 4 variables obligatorias en tu `.env` y la API levanta completa.
