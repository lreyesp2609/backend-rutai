from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import timedelta
from collections import defaultdict

from ..database.database import get_db
from ..database.config import settings
from ..seguridad.models import ZonaPeligrosaUsuario
from ..seguridad.geometria import calcular_distancia_haversine
from ..recordatorios.models import GeofenceTrigger

from .models import GroundTruth
from .schemas import (
    GroundTruthCreate,
    GroundTruthResponse,
    MetricasResponse,
    ResumenGlobal,
    MetricasBase,
    MetricasZona,
)
from . import crud

router = APIRouter()


# ───────────────────────────────────────────────
# Ground Truth endpoints
# ───────────────────────────────────────────────

@router.post("/ground-truth", response_model=GroundTruthResponse)
def crear_ground_truth(
    data: GroundTruthCreate,
    db: Session = Depends(get_db),
):
    """Registra un evento de ground truth verificado por el investigador."""
    return crud.crear_ground_truth(db, data)


@router.get("/ground-truth", response_model=List[GroundTruthResponse])
def listar_ground_truth(
    zona_id: Optional[int] = Query(None, description="Filtrar por zona"),
    sesion_id: Optional[int] = Query(None, description="Filtrar por sesión"),
    db: Session = Depends(get_db),
):
    """Lista registros de ground truth con filtros opcionales."""
    return crud.listar_ground_truth(db, zona_id=zona_id, sesion_id=sesion_id)


# ───────────────────────────────────────────────
# Métricas endpoint
# ───────────────────────────────────────────────

def _calcular_tp_fp_fn(
    triggers: list,
    ground_truths: list,
    ventana: timedelta,
) -> dict:
    """
    Calcula TP, FP, FN comparando triggers contra ground truths
    usando una ventana de tiempo.

    TP: trigger con GT dentro de la ventana (misma zona).
    FP: trigger sin GT correspondiente.
    FN: GT sin trigger correspondiente.
    """
    gt_usados = set()
    trigger_emparejados = set()

    # Para cada trigger, buscar un GT dentro de la ventana
    for t in triggers:
        if t.triggered_at is None:
            continue
        for gt in ground_truths:
            if gt.id in gt_usados:
                continue
            diff = abs((t.triggered_at - gt.timestamp_real).total_seconds())
            if diff <= ventana.total_seconds():
                trigger_emparejados.add(t.id)
                gt_usados.add(gt.id)
                break

    tp = len(trigger_emparejados)
    fp = len(triggers) - tp
    fn = len(ground_truths) - len(gt_usados)

    return {"TP": tp, "FP": fp, "FN": fn}


def _calcular_precision_recall_f1(tp: int, fp: int, fn: int) -> dict:
    """Calcula precision, recall y F1 a partir de TP, FP, FN."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


@router.get("/metricas", response_model=MetricasResponse)
def obtener_metricas(
    radio_metros: Optional[int] = Query(None, description="Filtrar zonas por radio"),
    velocidad_min: Optional[float] = Query(None, description="Velocidad mínima del GT"),
    velocidad_max: Optional[float] = Query(None, description="Velocidad máxima del GT"),
    sesion_id: Optional[int] = Query(None, description="Filtrar por sesión"),
    usuario_id: Optional[int] = Query(None, description="Filtrar por usuario"),
    db: Session = Depends(get_db),
):
    """
    Calcula precision, recall y F1 del geofencing comparando
    GeofenceTrigger (eventos del dispositivo) contra GroundTruth
    (eventos verificados por el investigador).
    """
    ventana = timedelta(seconds=settings.geofence_match_window_seconds)

    # ── 1. Obtener zonas activas ────────────────────────────
    zonas_query = db.query(ZonaPeligrosaUsuario).filter(
        ZonaPeligrosaUsuario.activa == True
    )
    if radio_metros is not None:
        zonas_query = zonas_query.filter(
            ZonaPeligrosaUsuario.radio_metros == radio_metros
        )
    if usuario_id is not None:
        zonas_query = zonas_query.filter(
            ZonaPeligrosaUsuario.usuario_id == usuario_id
        )
    zonas = zonas_query.all()

    # ── 2. Obtener todos los triggers ───────────────────────
    triggers_query = db.query(GeofenceTrigger)
    if sesion_id is not None:
        # GeofenceTrigger no tiene sesion_id directo,
        # pero filtramos por usuario si viene sesion_id
        pass
    if usuario_id is not None:
        triggers_query = triggers_query.filter(
            GeofenceTrigger.user_id == usuario_id
        )
    todos_los_triggers = triggers_query.all()

    # ── 3. Por cada zona, asignar triggers y GTs ────────────
    resultados_por_zona: List[MetricasZona] = []
    acumulador_por_radio: dict = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0})

    global_tp = 0
    global_fp = 0
    global_fn = 0
    global_triggers = 0
    global_gt = 0

    for zona in zonas:
        # Centro de la zona = primer punto del polígono
        centro = zona.poligono[0] if zona.poligono else None
        if centro is None:
            continue

        radio = zona.radio_metros or 200

        # Triggers que caen dentro de esta zona
        triggers_zona = []
        for t in todos_los_triggers:
            if t.gps_lat is None or t.gps_lon is None:
                continue
            distancia = calcular_distancia_haversine(
                t.gps_lat, t.gps_lon,
                centro["lat"], centro["lon"],
            )
            if distancia <= radio:
                triggers_zona.append(t)

        # Ground truths de esta zona
        gt_query = db.query(GroundTruth).filter(GroundTruth.zona_id == zona.id)
        if sesion_id is not None:
            gt_query = gt_query.filter(GroundTruth.sesion_id == sesion_id)
        if velocidad_min is not None:
            gt_query = gt_query.filter(GroundTruth.velocidad_kmh >= velocidad_min)
        if velocidad_max is not None:
            gt_query = gt_query.filter(GroundTruth.velocidad_kmh <= velocidad_max)
        gts_zona = gt_query.all()

        # Calcular TP / FP / FN
        resultado = _calcular_tp_fp_fn(triggers_zona, gts_zona, ventana)
        metricas = _calcular_precision_recall_f1(resultado["TP"], resultado["FP"], resultado["FN"])

        # Acumular globales
        global_tp += resultado["TP"]
        global_fp += resultado["FP"]
        global_fn += resultado["FN"]
        global_triggers += len(triggers_zona)
        global_gt += len(gts_zona)

        # Acumular por radio
        radio_key = str(radio)
        acumulador_por_radio[radio_key]["TP"] += resultado["TP"]
        acumulador_por_radio[radio_key]["FP"] += resultado["FP"]
        acumulador_por_radio[radio_key]["FN"] += resultado["FN"]

        resultados_por_zona.append(MetricasZona(
            zona_id=zona.id,
            nombre=zona.nombre,
            radio_metros=radio,
            TP=resultado["TP"],
            FP=resultado["FP"],
            FN=resultado["FN"],
            precision=metricas["precision"],
            recall=metricas["recall"],
            f1=metricas["f1"],
            total_triggers=len(triggers_zona),
            total_ground_truth=len(gts_zona),
        ))

    # ── 4. Resumen global ───────────────────────────────────
    global_metricas = _calcular_precision_recall_f1(global_tp, global_fp, global_fn)

    resumen_global = ResumenGlobal(
        TP=global_tp,
        FP=global_fp,
        FN=global_fn,
        precision=global_metricas["precision"],
        recall=global_metricas["recall"],
        f1=global_metricas["f1"],
        total_zonas_analizadas=len(zonas),
        total_triggers=global_triggers,
        total_ground_truth=global_gt,
    )

    # ── 5. Métricas por radio ───────────────────────────────
    por_radio = {}
    for r_key, acum in acumulador_por_radio.items():
        r_metricas = _calcular_precision_recall_f1(acum["TP"], acum["FP"], acum["FN"])
        por_radio[r_key] = MetricasBase(
            TP=acum["TP"],
            FP=acum["FP"],
            FN=acum["FN"],
            precision=r_metricas["precision"],
            recall=r_metricas["recall"],
            f1=r_metricas["f1"],
        )

    return MetricasResponse(
        resumen_global=resumen_global,
        por_radio=por_radio,
        por_zona=resultados_por_zona,
    )
