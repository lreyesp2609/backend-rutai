import logging

from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..database.config import settings
from ..usuarios.security import *
from ..usuarios.models import Usuario
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse, HTMLResponse
from ..usuarios.sesiones.crud import (
    crear_sesion,
    obtener_sesion,
    inhabilitar_sesion,
    inhabilitar_sesiones_usuario,
)
from ..usuarios.recuperacion.crud import (
    crear_token_recuperacion,
    obtener_token_valido,
    marcar_token_usado,
)
from ..usuarios.recuperacion.email_service import enviar_email_recuperacion
from .schemas import ForgotPasswordRequest, ResetPasswordRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/login", tags=["Login"])

# 🔹 Login
@router.post("/")
def login(
    correo: str = Form(...),
    contrasenia: str = Form(...),
    dispositivo: str = Form(None),
    version_app: str = Form(None),
    ip: str = Form(None),
    db: Session = Depends(get_db)
):
    usuario = db.query(Usuario).filter(Usuario.usuario==correo, Usuario.activo==True).first()
    if not usuario or not verify_password(contrasenia, usuario.contrasenia):
        raise HTTPException(
        status_code=401,
        detail="INVALID_CREDENTIALS"
        )

    access_token = create_access_token(
        {"sub": correo, "id_usuario": usuario.id, "rol": usuario.rol.nombre}
    )
    refresh_token = create_refresh_token()
    expiracion = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    nueva_sesion = crear_sesion(db, usuario.id, refresh_token, expiracion, dispositivo, version_app, ip)

    return JSONResponse({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "sesion_id": str(nueva_sesion.id)
    })

# 🔹 Forgot password
@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    return {
        "mensaje": "Para restablecer tu contraseña, usa el endpoint /login/reset-directo"
    }

class ResetDirectoRequest(BaseModel):
    correo: str
    nueva_contrasenia: str

@router.post("/reset-directo")
def reset_directo(
    request: ResetDirectoRequest,
    db: Session = Depends(get_db)
):
    if len(request.nueva_contrasenia) < 8:
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener al menos 8 caracteres"
        )
    
    usuario = db.query(Usuario).filter(
        Usuario.usuario == request.correo,
        Usuario.activo == True
    ).first()
    
    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="USUARIO_NO_ENCONTRADO"
        )
    
    usuario.contrasenia = get_password_hash(request.nueva_contrasenia)
    db.commit()
    
    return {"mensaje": "Contraseña actualizada correctamente"}

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page():
    with open("static/reset-password.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    api_base = settings.frontend_url
    if api_base.endswith("/static"):
        api_base = api_base[:-7]
    
    html = html.replace(
        'const API_BASE = "PLACEHOLDER_API_BASE"',
        f'const API_BASE = "{api_base}"'
    )
    return HTMLResponse(content=html)

# 🔹 Reset password
@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    if len(request.nueva_contrasenia or "") < 8:
        raise HTTPException(
            status_code=400,
            detail="La nueva contraseña debe tener al menos 8 caracteres"
        )

    token_obj = obtener_token_valido(db, request.token)
    if not token_obj:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    usuario = db.query(Usuario).filter(Usuario.id == token_obj.usuario_id, Usuario.activo == True).first()
    if not usuario:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    usuario.contrasenia = get_password_hash(request.nueva_contrasenia)
    marcar_token_usado(db, token_obj)
    inhabilitar_sesiones_usuario(db, usuario.id)

    return {"mensaje": "Contraseña actualizada correctamente"}

# 🔹 Refresh token
@router.post("/refresh")
def refresh_token(refresh_token: str = Form(...), db: Session = Depends(get_db)):
    sesion = obtener_sesion(db, refresh_token)
    if not sesion:
        raise HTTPException(status_code=401, detail="REFRESH_INVALIDO")
    
    # Verificar que el refresh token no haya expirado
    if sesion.expiracion < datetime.utcnow():
        inhabilitar_sesion(db, refresh_token)
        raise HTTPException(status_code=401, detail="REFRESH_EXPIRADO")

    # Renovar access token
    nuevo_access = create_access_token(
        {"sub": sesion.usuario.usuario, "id_usuario": sesion.usuario.id, "rol": sesion.usuario.rol.nombre}
    )

    # 🆕 CLAVE: Renovar refresh token si está cerca de expirar
    tiempo_restante = sesion.expiracion - datetime.utcnow()
    
    # Si le quedan menos de 7 días, renovar el refresh token
    if tiempo_restante.days < 7:
        nuevo_refresh = create_refresh_token()
        nueva_expiracion = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        sesion.refresh_token = nuevo_refresh
        sesion.expiracion = nueva_expiracion
        
        print(f"🔄 Refresh token renovado. Nueva expiración: {nueva_expiracion}")
    else:
        nuevo_refresh = refresh_token  # Mantener el mismo

    db.commit()

    return {
        "access_token": nuevo_access,
        "refresh_token": nuevo_refresh,
        "token_type": "bearer",
        "sesion_id": str(sesion.id)
    }

# 🔹 Logout
@router.post("/logout")
def logout(refresh_token: str = Form(...), db: Session = Depends(get_db)):
    sesion = inhabilitar_sesion(db, refresh_token)
    if not sesion:
        raise HTTPException(status_code=404, detail="SESION_NO_ENCONTRADA")
    return {"detail": "SESION_CERRADA"}

# 🔹 Decodificar token
@router.get("/decodificar")
def decodificar(
    payload: dict = Depends(decodificar_token),
    db: Session = Depends(get_db)
):
    correo = payload.get("sub")
    usuario = db.query(Usuario).filter(Usuario.usuario==correo, Usuario.activo==True).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="USUARIO_NO_ENCONTRADO")
    return JSONResponse({
        "id": usuario.id,
        "nombre": usuario.datos_personales.nombre,
        "apellido": usuario.datos_personales.apellido,
        "activo": usuario.activo,
        "id_rol": usuario.rol.id,
        "rol": usuario.rol.nombre,
        "correo": usuario.usuario,
    })
