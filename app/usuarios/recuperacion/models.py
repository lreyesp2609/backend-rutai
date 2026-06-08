from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from ...database.database import Base


class TokenRecuperacion(Base):
    __tablename__ = "tokens_recuperacion"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    token = Column(String(128), nullable=False, unique=True)
    expiracion = Column(DateTime(timezone=True), nullable=False)
    usado = Column(Boolean, default=False, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    usuario = relationship("Usuario")
