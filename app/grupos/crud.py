from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from datetime import datetime
import secrets

from .models import Grupo, MiembroGrupo

def create_grupo(db: Session, grupo_data, user_id: int):
    try:
        # Verificar si ya existe un grupo con el mismo nombre creado por el mismo usuario
        existing = db.query(Grupo).filter_by(nombre=grupo_data.nombre, creado_por_id=user_id, is_deleted=False).first()
        if existing:
            raise HTTPException(status_code=400, detail="GROUP_NAME_ALREADY_EXISTS")

        # Generar código de invitación aleatorio (8 caracteres)
        codigo = secrets.token_hex(4).upper()

        new_grupo = Grupo(
            nombre=grupo_data.nombre,
            descripcion=grupo_data.descripcion,
            codigo_invitacion=codigo,
            creado_por_id=user_id,
        )

        db.add(new_grupo)
        db.commit()
        db.refresh(new_grupo)

        # Agregar al creador como admin en MiembroGrupo
        miembro_admin = MiembroGrupo(
            usuario_id=user_id,
            grupo_id=new_grupo.id,
            rol="admin",
            activo=True,
            fecha_union=datetime.utcnow()
        )
        db.add(miembro_admin)
        db.commit()

        return new_grupo

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear grupo: {str(e)}")

def salir_de_grupo(db: Session, grupo_id: int, user_id: int):
    grupo = db.query(Grupo).filter(
        Grupo.id == grupo_id,
        Grupo.is_deleted == False
    ).first()

    if not grupo:
        raise HTTPException(status_code=404, detail="GROUP_NOT_FOUND")

    # El creador no puede salir
    if grupo.creado_por_id == user_id:
        raise HTTPException(status_code=400, detail="CREATOR_CANNOT_LEAVE")

    miembro = db.query(MiembroGrupo).filter_by(
        usuario_id=user_id,
        grupo_id=grupo_id
    ).first()

    if not miembro:
        raise HTTPException(status_code=400, detail="NOT_IN_GROUP")

    if not miembro.activo:
        raise HTTPException(status_code=400, detail="NO_LONGER_MEMBER")

    # 🔹 Solo esta parte cambia: no se borra, se desactiva
    miembro.activo = False
    db.commit()

    # 🔹 Mensaje más natural y limpio
    return {"code": "GROUP_LEFT_SUCCESS"}
