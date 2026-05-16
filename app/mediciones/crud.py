from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from .models import LatenciaMetrica, ConsumoEnergetico
from .schemas import LatenciaCreate, ConsumoEnergeticoCreate


# ───────────────────────────────────────────────
# Latencia CRUD
# ───────────────────────────────────────────────

def crear_latencia(db: Session, data: LatenciaCreate) -> LatenciaMetrica:
    """Crea un registro de latencia."""
    registro = LatenciaMetrica(
        sesion_id=data.sesion_id,
        dispositivo_id=data.dispositivo_id,
        modelo_dispositivo=data.modelo_dispositivo,
        so_version=data.so_version,
        endpoint=data.endpoint,
        metodo_http=data.metodo_http,
        latencia_ms=data.latencia_ms,
        codigo_respuesta=data.codigo_respuesta,
        latitud=data.latitud,
        longitud=data.longitud,
        red=data.red,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


def crear_latencia_batch(db: Session, registros: List[LatenciaCreate]) -> List[LatenciaMetrica]:
    """Crea múltiples registros de latencia en un solo commit."""
    objetos = []
    for data in registros:
        obj = LatenciaMetrica(
            sesion_id=data.sesion_id,
            dispositivo_id=data.dispositivo_id,
            modelo_dispositivo=data.modelo_dispositivo,
            so_version=data.so_version,
            endpoint=data.endpoint,
            metodo_http=data.metodo_http,
            latencia_ms=data.latencia_ms,
            codigo_respuesta=data.codigo_respuesta,
            latitud=data.latitud,
            longitud=data.longitud,
            red=data.red,
        )
        objetos.append(obj)
    db.add_all(objetos)
    db.commit()
    for obj in objetos:
        db.refresh(obj)
    return objetos


def listar_latencias(
    db: Session,
    dispositivo_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    red: Optional[str] = None,
    sesion_id: Optional[int] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
) -> List[LatenciaMetrica]:
    """Lista registros de latencia con filtros opcionales."""
    query = db.query(LatenciaMetrica)
    if dispositivo_id is not None:
        query = query.filter(LatenciaMetrica.dispositivo_id == dispositivo_id)
    if endpoint is not None:
        query = query.filter(LatenciaMetrica.endpoint == endpoint)
    if red is not None:
        query = query.filter(LatenciaMetrica.red == red)
    if sesion_id is not None:
        query = query.filter(LatenciaMetrica.sesion_id == sesion_id)
    if fecha_desde is not None:
        query = query.filter(LatenciaMetrica.timestamp >= fecha_desde)
    if fecha_hasta is not None:
        query = query.filter(LatenciaMetrica.timestamp <= fecha_hasta)
    return query.order_by(LatenciaMetrica.timestamp).all()


# ───────────────────────────────────────────────
# Consumo energético CRUD
# ───────────────────────────────────────────────

def crear_consumo(db: Session, data: ConsumoEnergeticoCreate) -> ConsumoEnergetico:
    """Crea un registro de consumo energético. consumo_pct se calcula automáticamente."""
    consumo_pct = data.bateria_inicio_pct - data.bateria_fin_pct
    registro = ConsumoEnergetico(
        sesion_id=data.sesion_id,
        dispositivo_id=data.dispositivo_id,
        modelo_dispositivo=data.modelo_dispositivo,
        so_version=data.so_version,
        modo_ubicacion=data.modo_ubicacion,
        bateria_inicio_pct=data.bateria_inicio_pct,
        bateria_fin_pct=data.bateria_fin_pct,
        consumo_pct=consumo_pct,
        duracion_minutos=data.duracion_minutos,
        temperatura_promedio_c=data.temperatura_promedio_c,
        pantalla_encendida=data.pantalla_encendida,
        timestamp_inicio=data.timestamp_inicio,
        timestamp_fin=data.timestamp_fin,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


def listar_consumos(
    db: Session,
    dispositivo_id: Optional[str] = None,
    modo_ubicacion: Optional[str] = None,
    sesion_id: Optional[int] = None,
) -> List[ConsumoEnergetico]:
    """Lista registros de consumo energético con filtros opcionales."""
    query = db.query(ConsumoEnergetico)
    if dispositivo_id is not None:
        query = query.filter(ConsumoEnergetico.dispositivo_id == dispositivo_id)
    if modo_ubicacion is not None:
        query = query.filter(ConsumoEnergetico.modo_ubicacion == modo_ubicacion)
    if sesion_id is not None:
        query = query.filter(ConsumoEnergetico.sesion_id == sesion_id)
    return query.order_by(ConsumoEnergetico.timestamp_inicio).all()
