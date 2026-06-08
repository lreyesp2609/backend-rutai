import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import TokenRecuperacion


def crear_token_recuperacion(db: Session, usuario_id: int):
    token = secrets.token_urlsafe(64)
    expiracion = datetime.utcnow() + timedelta(minutes=30)
    token_obj = TokenRecuperacion(
        usuario_id=usuario_id,
        token=token,
        expiracion=expiracion,
        usado=False
    )
    db.add(token_obj)
    db.commit()
    db.refresh(token_obj)
    return token_obj


def obtener_token_valido(db: Session, token: str):
    return db.query(TokenRecuperacion).filter(
        TokenRecuperacion.token == token,
        TokenRecuperacion.usado == False,
        TokenRecuperacion.expiracion >= datetime.utcnow()
    ).first()


def marcar_token_usado(db: Session, token_obj: TokenRecuperacion):
    token_obj.usado = True
    db.commit()
    db.refresh(token_obj)
    return token_obj
