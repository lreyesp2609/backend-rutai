from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ───────────────────────────────────────────────
# Ground Truth — Request / Response
# ───────────────────────────────────────────────

class GroundTruthCreate(BaseModel):
    zona_id: int
    sesion_id: Optional[int] = None
    tipo_evento: str = Field(..., pattern="^(entrada|salida)$", description="'entrada' o 'salida'")
    timestamp_real: datetime
    metodo_verificacion: str = Field(..., pattern="^(dgps|marcador_fijo|video)$")
    velocidad_kmh: Optional[float] = None
    notas: Optional[str] = Field(None, max_length=500)


class GroundTruthResponse(BaseModel):
    id: int
    zona_id: int
    sesion_id: Optional[int] = None
    tipo_evento: str
    timestamp_real: datetime
    metodo_verificacion: str
    velocidad_kmh: Optional[float] = None
    notas: Optional[str] = None

    class Config:
        from_attributes = True


# ───────────────────────────────────────────────
# Métricas — Response schemas
# ───────────────────────────────────────────────

class MetricasBase(BaseModel):
    TP: int = 0
    FP: int = 0
    FN: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0


class MetricasZona(MetricasBase):
    zona_id: int
    nombre: str
    radio_metros: int
    total_triggers: int = 0
    total_ground_truth: int = 0


class ResumenGlobal(MetricasBase):
    total_zonas_analizadas: int = 0
    total_triggers: int = 0
    total_ground_truth: int = 0


class MetricasResponse(BaseModel):
    resumen_global: ResumenGlobal
    por_radio: dict  # {"50": MetricasBase, "100": ..., "200": ...}
    por_zona: List[MetricasZona]
