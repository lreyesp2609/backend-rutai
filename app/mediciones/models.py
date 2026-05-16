from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..database.database import Base


class LatenciaMetrica(Base):
    """
    ⏱️ LATENCIA — Cada request que hace la app, el móvil mide el tiempo
    de ida y vuelta y lo reporta al backend.
    Permite comparar rendimiento entre dispositivos, redes y endpoints.
    """
    __tablename__ = "latencia_metricas"

    id = Column(Integer, primary_key=True, index=True)
    sesion_id = Column(Integer, ForeignKey("sesiones_app_usuario.id"), nullable=True)
    dispositivo_id = Column(String(100), nullable=False, index=True)
    modelo_dispositivo = Column(String(100), nullable=True)
    so_version = Column(String(50), nullable=True)
    endpoint = Column(String(200), nullable=False, index=True)
    metodo_http = Column(String(10), nullable=False)  # "GET", "POST", "WS"
    latencia_ms = Column(Float, nullable=False)
    codigo_respuesta = Column(Integer, nullable=True)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    red = Column(String(20), nullable=True)  # "wifi", "4g", "3g"
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class ConsumoEnergetico(Base):
    """
    🔋 CONSUMO ENERGÉTICO — El dispositivo reporta el consumo de batería
    por sesión de prueba. Permite comparar modos de ubicación
    (continua vs pasiva vs apagada) entre dispositivos.
    """
    __tablename__ = "consumo_energetico"

    id = Column(Integer, primary_key=True, index=True)
    sesion_id = Column(Integer, ForeignKey("sesiones_app_usuario.id"), nullable=True)
    dispositivo_id = Column(String(100), nullable=False, index=True)
    modelo_dispositivo = Column(String(100), nullable=True)
    so_version = Column(String(50), nullable=True)
    modo_ubicacion = Column(String(20), nullable=False)  # "continua", "pasiva", "apagada"
    bateria_inicio_pct = Column(Integer, nullable=False)
    bateria_fin_pct = Column(Integer, nullable=False)
    consumo_pct = Column(Float, nullable=False)  # calculado: inicio - fin
    duracion_minutos = Column(Float, nullable=False)
    temperatura_promedio_c = Column(Float, nullable=True)
    pantalla_encendida = Column(Boolean, default=False)
    timestamp_inicio = Column(DateTime(timezone=True), nullable=False)
    timestamp_fin = Column(DateTime(timezone=True), nullable=False)

    # Datos físicos de corriente y voltaje
    corriente_promedio_ma = Column(Float, nullable=True)
    voltaje_promedio_mv = Column(Float, nullable=True)

    # Energía calculada
    energia_consumida_joules = Column(Float, nullable=True)

    # Carga en mAh (más preciso que porcentaje)
    carga_inicio_mah = Column(Float, nullable=True)
    carga_fin_mah = Column(Float, nullable=True)
    consumo_mah = Column(Float, nullable=True)
