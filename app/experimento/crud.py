from sqlalchemy.orm import Session
from typing import Optional, List, Tuple

from .models import GroundTruth
from .schemas import GroundTruthCreate


def crear_ground_truth(db: Session, data: GroundTruthCreate) -> GroundTruth:
    """Crea un nuevo registro de ground truth."""
    registro = GroundTruth(
        zona_id=data.zona_id,
        sesion_id=data.sesion_id,
        tipo_evento=data.tipo_evento,
        timestamp_real=data.timestamp_real,
        metodo_verificacion=data.metodo_verificacion,
        velocidad_kmh=data.velocidad_kmh,
        notas=data.notas,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


def crear_ground_truth_batch(
    db: Session,
    registros: List[GroundTruthCreate],
) -> Tuple[List[GroundTruth], List[dict]]:
    """Crea múltiples registros de ground truth en una sola transacción."""
    insertados = []
    errores = []

    for idx, data in enumerate(registros):
        try:
            obj = GroundTruth(
                zona_id=data.zona_id,
                sesion_id=data.sesion_id,
                tipo_evento=data.tipo_evento,
                timestamp_real=data.timestamp_real,
                metodo_verificacion=data.metodo_verificacion,
                velocidad_kmh=data.velocidad_kmh,
                notas=data.notas,
            )
            db.add(obj)
            db.flush()
            insertados.append(obj)
        except Exception as e:
            db.rollback()
            errores.append({"indice": idx, "error": str(e)})
            return insertados, errores

    db.commit()
    for obj in insertados:
        db.refresh(obj)
    return insertados, errores


def listar_ground_truth(
    db: Session,
    zona_id: Optional[int] = None,
    sesion_id: Optional[int] = None,
) -> List[GroundTruth]:
    """Lista registros de ground truth con filtros opcionales."""
    query = db.query(GroundTruth)
    if zona_id is not None:
        query = query.filter(GroundTruth.zona_id == zona_id)
    if sesion_id is not None:
        query = query.filter(GroundTruth.sesion_id == sesion_id)
    return query.order_by(GroundTruth.timestamp_real).all()
