from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from collections import defaultdict

from ..database.database import get_db

from .models import LatenciaMetrica, ConsumoEnergetico
from .schemas import (
    LatenciaCreate,
    LatenciaBatchCreate,
    LatenciaResponse,
    ConsumoEnergeticoCreate,
    ConsumoEnergeticoResponse,
    LatenciaEstadisticasResponse,
    EstadisticaEndpoint,
    EstadisticaDispositivo,
    EstadisticaRed,
    EnergiaEstadisticasResponse,
    EstadisticaModo,
    EstadisticaDispositivoEnergia,
)
from . import crud

router = APIRouter()


# ───────────────────────────────────────────────
# Utilidad: cálculo de percentiles (Python puro)
# ───────────────────────────────────────────────

def percentil(valores: list, p: float) -> float:
    """Calcula el percentil p de una lista de valores, sin pandas."""
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    idx = (len(ordenados) - 1) * p / 100
    inferior = int(idx)
    superior = min(inferior + 1, len(ordenados) - 1)
    fraccion = idx - inferior
    return round(ordenados[inferior] + fraccion * (ordenados[superior] - ordenados[inferior]), 2)


# ═══════════════════════════════════════════════
# LATENCIA
# ═══════════════════════════════════════════════

@router.post("/latencia", response_model=LatenciaResponse)
def crear_latencia(
    data: LatenciaCreate,
    db: Session = Depends(get_db),
):
    """Registra una medición de latencia desde el dispositivo."""
    return crud.crear_latencia(db, data)


@router.post("/latencia/batch", response_model=List[LatenciaResponse])
def crear_latencia_batch(
    data: LatenciaBatchCreate,
    db: Session = Depends(get_db),
):
    """Registra hasta 50 mediciones de latencia en un solo lote."""
    return crud.crear_latencia_batch(db, data.registros)


@router.get("/latencia", response_model=List[LatenciaResponse])
def listar_latencias(
    dispositivo_id: Optional[str] = Query(None, description="Filtrar por dispositivo"),
    endpoint: Optional[str] = Query(None, description="Filtrar por endpoint"),
    red: Optional[str] = Query(None, description="Filtrar por tipo de red"),
    sesion_id: Optional[int] = Query(None, description="Filtrar por sesión"),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha inicio (UTC)"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha fin (UTC)"),
    db: Session = Depends(get_db),
):
    """Lista registros de latencia con filtros opcionales."""
    return crud.listar_latencias(
        db,
        dispositivo_id=dispositivo_id,
        endpoint=endpoint,
        red=red,
        sesion_id=sesion_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


@router.get("/latencia/estadisticas", response_model=LatenciaEstadisticasResponse)
def estadisticas_latencia(
    dispositivo_id: Optional[str] = Query(None, description="Filtrar por dispositivo"),
    endpoint: Optional[str] = Query(None, description="Filtrar por endpoint"),
    red: Optional[str] = Query(None, description="Filtrar por tipo de red"),
    sesion_id: Optional[int] = Query(None, description="Filtrar por sesión"),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha inicio (UTC)"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha fin (UTC)"),
    db: Session = Depends(get_db),
):
    """
    Calcula estadísticas de latencia: percentiles p50/p95/p99,
    promedio, min y max — agrupado por endpoint, dispositivo y red.
    """
    registros = crud.listar_latencias(
        db,
        dispositivo_id=dispositivo_id,
        endpoint=endpoint,
        red=red,
        sesion_id=sesion_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )

    # ── Agrupar por endpoint+metodo ─────────────────────────
    por_endpoint_dict: dict = defaultdict(list)
    for r in registros:
        key = (r.endpoint, r.metodo_http)
        por_endpoint_dict[key].append(r.latencia_ms)

    por_endpoint = []
    for (ep, metodo), latencias in por_endpoint_dict.items():
        por_endpoint.append(EstadisticaEndpoint(
            endpoint=ep,
            metodo_http=metodo,
            total=len(latencias),
            p50_ms=percentil(latencias, 50),
            p95_ms=percentil(latencias, 95),
            p99_ms=percentil(latencias, 99),
            promedio_ms=round(sum(latencias) / len(latencias), 2),
            min_ms=round(min(latencias), 2),
            max_ms=round(max(latencias), 2),
        ))

    # ── Agrupar por dispositivo ─────────────────────────────
    por_dispositivo_dict: dict = defaultdict(lambda: {"latencias": [], "modelo": None})
    for r in registros:
        por_dispositivo_dict[r.dispositivo_id]["latencias"].append(r.latencia_ms)
        if r.modelo_dispositivo:
            por_dispositivo_dict[r.dispositivo_id]["modelo"] = r.modelo_dispositivo

    por_dispositivo = []
    for disp_id, info in por_dispositivo_dict.items():
        lats = info["latencias"]
        por_dispositivo.append(EstadisticaDispositivo(
            dispositivo_id=disp_id,
            modelo_dispositivo=info["modelo"],
            total=len(lats),
            p50_ms=percentil(lats, 50),
            p95_ms=percentil(lats, 95),
            p99_ms=percentil(lats, 99),
        ))

    # ── Agrupar por red ─────────────────────────────────────
    por_red_dict: dict = defaultdict(list)
    for r in registros:
        red_tipo = r.red or "desconocida"
        por_red_dict[red_tipo].append(r.latencia_ms)

    por_red = {}
    for red_tipo, latencias in por_red_dict.items():
        por_red[red_tipo] = EstadisticaRed(
            total=len(latencias),
            p50_ms=percentil(latencias, 50),
            p95_ms=percentil(latencias, 95),
            p99_ms=percentil(latencias, 99),
        )

    return LatenciaEstadisticasResponse(
        total_requests=len(registros),
        por_endpoint=por_endpoint,
        por_dispositivo=por_dispositivo,
        por_red=por_red,
    )


# ═══════════════════════════════════════════════
# CONSUMO ENERGÉTICO
# ═══════════════════════════════════════════════

@router.post("/energia", response_model=ConsumoEnergeticoResponse)
def crear_consumo(
    data: ConsumoEnergeticoCreate,
    db: Session = Depends(get_db),
):
    """Registra una sesión de consumo energético desde el dispositivo."""
    return crud.crear_consumo(db, data)


@router.get("/energia", response_model=List[ConsumoEnergeticoResponse])
def listar_consumos(
    dispositivo_id: Optional[str] = Query(None, description="Filtrar por dispositivo"),
    modo_ubicacion: Optional[str] = Query(None, description="Filtrar por modo de ubicación"),
    sesion_id: Optional[int] = Query(None, description="Filtrar por sesión"),
    db: Session = Depends(get_db),
):
    """Lista registros de consumo energético con filtros opcionales."""
    return crud.listar_consumos(
        db,
        dispositivo_id=dispositivo_id,
        modo_ubicacion=modo_ubicacion,
        sesion_id=sesion_id,
    )


@router.get("/energia/estadisticas", response_model=EnergiaEstadisticasResponse)
def estadisticas_energia(
    dispositivo_id: Optional[str] = Query(None, description="Filtrar por dispositivo"),
    modo_ubicacion: Optional[str] = Query(None, description="Filtrar por modo de ubicación"),
    db: Session = Depends(get_db),
):
    """
    Calcula estadísticas de consumo energético agrupadas por modo
    de ubicación y por dispositivo.
    consumo_por_hora_pct = (consumo_pct / duracion_minutos) * 60
    """
    registros = crud.listar_consumos(
        db,
        dispositivo_id=dispositivo_id,
        modo_ubicacion=modo_ubicacion,
    )

    # ── Agrupar por modo de ubicación ───────────────────────
    por_modo_dict: dict = defaultdict(lambda: {
        "consumos": [], "duraciones": [], "temperaturas": [], "dispositivos": set()
    })
    for r in registros:
        grupo = por_modo_dict[r.modo_ubicacion]
        grupo["consumos"].append(r.consumo_pct)
        grupo["duraciones"].append(r.duracion_minutos)
        if r.temperatura_promedio_c is not None:
            grupo["temperaturas"].append(r.temperatura_promedio_c)
        grupo["dispositivos"].add(r.dispositivo_id)

    por_modo = {}
    for modo, info in por_modo_dict.items():
        consumo_promedio = sum(info["consumos"]) / len(info["consumos"])
        duracion_promedio = sum(info["duraciones"]) / len(info["duraciones"])
        consumo_por_hora = (consumo_promedio / duracion_promedio) * 60 if duracion_promedio > 0 else 0.0
        temperatura = (
            round(sum(info["temperaturas"]) / len(info["temperaturas"]), 2)
            if info["temperaturas"] else None
        )
        por_modo[modo] = EstadisticaModo(
            total_sesiones=len(info["consumos"]),
            consumo_promedio_pct=round(consumo_promedio, 2),
            consumo_por_hora_pct=round(consumo_por_hora, 2),
            temperatura_promedio_c=temperatura,
            dispositivos=len(info["dispositivos"]),
        )

    # ── Agrupar por dispositivo + modo ──────────────────────
    por_disp_dict: dict = defaultdict(lambda: {
        "modelo": None, "consumos": [], "duraciones": []
    })
    for r in registros:
        key = (r.dispositivo_id, r.modo_ubicacion)
        grupo = por_disp_dict[key]
        grupo["consumos"].append(r.consumo_pct)
        grupo["duraciones"].append(r.duracion_minutos)
        if r.modelo_dispositivo:
            grupo["modelo"] = r.modelo_dispositivo

    por_dispositivo = []
    for (disp_id, modo), info in por_disp_dict.items():
        consumo_promedio = sum(info["consumos"]) / len(info["consumos"])
        duracion_promedio = sum(info["duraciones"]) / len(info["duraciones"])
        consumo_por_hora = (consumo_promedio / duracion_promedio) * 60 if duracion_promedio > 0 else 0.0
        por_dispositivo.append(EstadisticaDispositivoEnergia(
            dispositivo_id=disp_id,
            modelo_dispositivo=info["modelo"],
            modo_ubicacion=modo,
            sesiones=len(info["consumos"]),
            consumo_promedio_pct=round(consumo_promedio, 2),
            consumo_por_hora_pct=round(consumo_por_hora, 2),
        ))

    return EnergiaEstadisticasResponse(
        por_modo=por_modo,
        por_dispositivo=por_dispositivo,
    )
