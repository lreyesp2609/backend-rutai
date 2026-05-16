from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from ..database.database import Base


class GroundTruth(Base):
    """
    📍 GROUND TRUTH — Registro de eventos reales verificados por el investigador.
    Cada entrada marca el momento exacto en que un sujeto entró/salió
    de una zona peligrosa, verificado por un método externo (DGPS, marcador fijo, video).
    """
    __tablename__ = "ground_truth"

    id = Column(Integer, primary_key=True, index=True)
    zona_id = Column(Integer, ForeignKey("zonas_peligrosas_usuario.id"), nullable=False)
    sesion_id = Column(Integer, ForeignKey("sesiones_app_usuario.id"), nullable=True)
    tipo_evento = Column(String(10), nullable=False)  # "entrada" o "salida"
    timestamp_real = Column(DateTime(timezone=True), nullable=False)
    metodo_verificacion = Column(String(20), nullable=False)  # "dgps", "marcador_fijo", "video"
    velocidad_kmh = Column(Float, nullable=True)
    notas = Column(String(500), nullable=True)
