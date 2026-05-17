# 🗂️ rutai

## 📖 Descripción del proyecto

`rutai` es una API **RESTful** basada en **FastAPI** que sirve como backend para la aplicación *RutAI*. Proporciona servicios de autenticación, gestión de usuarios, almacenamiento de datos y funcionalidades en tiempo real mediante **Redis**. La API está diseñada para ser altamente escalable, segura y fácil de desplegar en plataformas como **Render**.

---

## 🛠️ Tecnologías usadas

| Categoría      | Tecnologías |
|----------------|-------------|
| Framework      | FastAPI (Python 3.11) |
| Base de datos  | PostgreSQL (a través de Supabase) |
| BaaS / Auth    | Supabase (para gestión de usuarios y OAuth) |
| Cache / Mensajería | Redis |
| Deploy         | Render (servicio de hosting) |
| Otros          | Pydantic, SQLAlchemy, Alembic, python‑dotenv |

---

## 📦 Requisitos previos

- **Python ≥ 3.11**
- **Node.js (opcional)** – Solo si deseas generar tipos TypeScript para el cliente.
- **Docker** (opcional, recomendado) – Para levantar una base de datos PostgreSQL y Redis locales.
- **Cuenta en Supabase** (para obtener `SUPABASE_URL` y `SUPABASE_KEY`).
- **Cuenta en Render** (para despliegue). 

---

## 🚀 Instalación y ejecución local

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/recuerdago-api.git
   cd recuerdago-api
   ```

2. **Crear y activar un entorno virtual**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate   # Windows
   # source .venv/bin/activate   # macOS/Linux
   ```

3. **Instalar dependencias**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Crear archivo de variables de entorno**
   Copia el ejemplo y rellena los valores:
   ```bash
   cp .env.example .env
   ```
   Edita `.env` con tus credenciales (ver sección *Variables de entorno*).

5. **Inicializar la base de datos**
   ```bash
   alembic upgrade head   # aplica migraciones
   ```

6. **Ejecutar la API**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   La documentación interactiva estará disponible en `http://localhost:8000/docs`.

---

## 🔑 Variables de entorno necesarias (`.env.example`)

```dotenv
# ---------------------------------------------------
# FastAPI / Uvicorn
# ---------------------------------------------------
HOST=0.0.0.0
PORT=8000
DEBUG=True

# ---------------------------------------------------
# PostgreSQL (Supabase) 
# ---------------------------------------------------
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=recuerdago
POSTGRES_HOST=your_supabase_host
POSTGRES_PORT=5432

# ---------------------------------------------------
# Supabase (Auth + Storage)
# ---------------------------------------------------
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_or_service_key

# ---------------------------------------------------
# Redis (Cache / PubSub)
# ---------------------------------------------------
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=optional_password

# ---------------------------------------------------
# Seguridad / JWT
# ---------------------------------------------------
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ---------------------------------------------------
# Render (solo para CI/CD, opcional)
# ---------------------------------------------------
RENDER_SERVICE_ID=your_render_service_id
```

Guarda este archivo como `.env` antes de iniciar la aplicación.

---

## 🌐 Despliegue en Render

1. **Crear una nueva Web Service** en Render y conectar tu repositorio de GitHub.
2. **Configurar el entorno**:
   - En la sección *Environment*, añade todas las variables definidas en `.env.example`.
   - Selecciona *Python* como runtime y especifica la versión (≥3.11).
3. **Build Command** (comando de construcción):
   ```bash
   pip install -r requirements.txt && alembic upgrade head
   ```
4. **Start Command** (comando de arranque):
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
5. **Persistencia**: Render provee una base de datos PostgreSQL y Redis gestionados; si utilizas Supabase, simplemente mantiene las variables de conexión.
6. **Deploy automático**: Cada push a la rama `main` disparará una nueva compilación y despliegue.

---

## 📂 Estructura de carpetas

```
recuerdago-api/
├─ app/                     # Código fuente de la API
│   ├─ api/                 # Routers (endpoints) organizados por dominio
│   │   ├─ v1/              # Versión 1 de la API
│   │   │   ├─ usuarios.py
│   │   │   ├─ auth.py
│   │   │   └─ ...
│   ├─ core/                # Configuración y utilidades generales
│   │   ├─ config.py        # Carga de .env y settings de Pydantic
│   │   ├─ security.py      # JWT, hashing, etc.
│   │   └─ ...
│   ├─ db/                  # Gestión de base de datos
│   │   ├─ models/          # Modelos SQLAlchemy
│   │   ├─ schemas/         # Schemas Pydantic
│   │   ├─ session.py       # Session y engine
│   │   └─ migrations/      # Alembic migrations
│   ├─ services/            # Lógica de negocio (p.ej., envío de correos)
│   └─ main.py              # Punto de entrada de FastAPI
├─ tests/                   # Tests unitarios y de integración
│   └─ ...
├─ .env.example            # Plantilla de variables de entorno
├─ requirements.txt         # Dependencias Python
├─ alembic.ini              # Configuración de Alembic
├─ Dockerfile               # (opcional) Imagen Docker para Render
├─ docker-compose.yml       # (opcional) Levantar PostgreSQL + Redis localmente
└─ README.md                # <-- Este archivo
```

---

> **¡Listo!** Ahora tienes toda la información necesaria para desarrollar, probar y desplegar `rutai`.
