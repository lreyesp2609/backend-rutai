from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


# ───────────────────────────────────────────────
# Latencia — Request / Response
# ───────────────────────────────────────────────

class LatenciaCreate(BaseModel):
    sesion_id: Optional[str] = None
    dispositivo_id: str = Field(..., max_length=100)
    modelo_dispositivo: Optional[str] = Field(None, max_length=100)
    so_version: Optional[str] = Field(None, max_length=50)
    endpoint: str = Field(..., max_length=200)
    metodo_http: str = Field(..., pattern="^(GET|POST|PUT|PATCH|DELETE|WS)$")
    latencia_ms: float = Field(..., ge=0)
    codigo_respuesta: Optional[int] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    red: Optional[str] = Field(None, pattern="^(wifi|4g|3g|5g|ethernet)$")
    timestamp: Optional[datetime] = None


class LatenciaBatchCreate(BaseModel):
    mediciones: List[LatenciaCreate] = Field(..., max_length=50)

    @field_validator("mediciones")
    @classmethod
    def validar_maximo(cls, v):
        if len(v) > 50:
            raise ValueError("Máximo 50 mediciones por lote")
        return v


class LatenciaResponse(BaseModel):
    id: int
    sesion_id: Optional[int] = None
    dispositivo_id: str
    modelo_dispositivo: Optional[str] = None
    so_version: Optional[str] = None
    endpoint: str
    metodo_http: str
    latencia_ms: float
    codigo_respuesta: Optional[int] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    red: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# ───────────────────────────────────────────────
# Consumo energético — Request / Response
# ───────────────────────────────────────────────

class ConsumoEnergeticoCreate(BaseModel):
    sesion_id: Optional[str] = None
    dispositivo_id: str = Field(..., max_length=100)
    modelo_dispositivo: Optional[str] = Field(None, max_length=100)
    so_version: Optional[str] = Field(None, max_length=50)
    modo_ubicacion: str = Field(..., pattern="^(continua|pasiva|apagada)$")
    bateria_inicio_pct: int = Field(..., ge=0, le=100)
    bateria_fin_pct: int = Field(..., ge=0, le=100)
    duracion_minutos: float = Field(..., gt=0)
    temperatura_promedio_c: Optional[float] = None
    pantalla_encendida: bool = False
    timestamp_inicio: datetime
    timestamp_fin: datetime
    # Datos físicos de batería (opcionales)
    corriente_promedio_ma: Optional[float] = None
    voltaje_promedio_mv: Optional[float] = None
    energia_consumida_joules: Optional[float] = None
    carga_inicio_mah: Optional[float] = None
    carga_fin_mah: Optional[float] = None


class ConsumoEnergeticoResponse(BaseModel):
    id: int
    sesion_id: Optional[int] = None
    dispositivo_id: str
    modelo_dispositivo: Optional[str] = None
    so_version: Optional[str] = None
    modo_ubicacion: str
    bateria_inicio_pct: int
    bateria_fin_pct: int
    consumo_pct: float
    duracion_minutos: float
    temperatura_promedio_c: Optional[float] = None
    pantalla_encendida: bool
    timestamp_inicio: datetime
    timestamp_fin: datetime
    # Datos físicos de batería
    corriente_promedio_ma: Optional[float] = None
    voltaje_promedio_mv: Optional[float] = None
    energia_consumida_joules: Optional[float] = None
    carga_inicio_mah: Optional[float] = None
    carga_fin_mah: Optional[float] = None
    consumo_mah: Optional[float] = None

    class Config:
        from_attributes = True


# ───────────────────────────────────────────────
# Estadísticas de latencia — Response
# ───────────────────────────────────────────────

class EstadisticaEndpoint(BaseModel):
    endpoint: str
    metodo_http: str
    total: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    promedio_ms: float
    min_ms: float
    max_ms: float


class EstadisticaDispositivo(BaseModel):
    dispositivo_id: str
    modelo_dispositivo: Optional[str] = None
    total: int
    p50_ms: float
    p95_ms: float
    p99_ms: float


class EstadisticaRed(BaseModel):
    total: int
    p50_ms: float
    p95_ms: float
    p99_ms: float


class LatenciaEstadisticasResponse(BaseModel):
    total_requests: int
    por_endpoint: List[EstadisticaEndpoint]
    por_dispositivo: List[EstadisticaDispositivo]
    por_red: dict  # {"wifi": EstadisticaRed, "4g": ..., ...}


# ───────────────────────────────────────────────
# Estadísticas de energía — Response
# ───────────────────────────────────────────────

class EstadisticaModo(BaseModel):
    total_sesiones: int
    consumo_promedio_pct: float
    consumo_por_hora_pct: float
    temperatura_promedio_c: Optional[float] = None
    dispositivos: int


class EstadisticaDispositivoEnergia(BaseModel):
    dispositivo_id: str
    modelo_dispositivo: Optional[str] = None
    modo_ubicacion: str
    sesiones: int
    consumo_promedio_pct: float
    consumo_por_hora_pct: float


class EnergiaEstadisticasResponse(BaseModel):
    por_modo: dict  # {"continua": EstadisticaModo, ...}
    por_dispositivo: List[EstadisticaDispositivoEnergia]
