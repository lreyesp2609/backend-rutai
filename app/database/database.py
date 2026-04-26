from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from .config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ⚠️ CONFIGURACIÓN CRÍTICA PARA WEBSOCKETS
engine = create_engine(
    settings.database_url,
    pool_size=3,
    max_overflow=7,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug,
    connect_args={
        "sslmode": "require",
        "connect_timeout": 10,
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
metadata = MetaData()

def get_db():
    """
    Dependency para FastAPI endpoints normales.
    La sesión se cierra automáticamente al terminar el request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            logger.info(f"✅ Conexión exitosa a PostgreSQL: {version}")
            return True
    except SQLAlchemyError as e:
        logger.error(f"❌ Error probando la conexión: {e}")
        return False

def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas creadas exitosamente")
    except SQLAlchemyError as e:
        logger.error(f"❌ Error creando las tablas: {e}")
        raise
