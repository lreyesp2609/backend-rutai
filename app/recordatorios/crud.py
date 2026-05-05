from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from .models import Reminder
from .schemas import ReminderCreate
from fastapi import HTTPException
import locale

try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except locale.Error:
        pass

def create_reminder(db: Session, reminder_data: ReminderCreate, user_id: int):
    try:
        # Verificar si ya existe
        existing = db.query(Reminder).filter_by(
            user_id=user_id, 
            title=reminder_data.title
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="REMINDER_TITLE_DUPLICATE"
            )

        reminder_dict = reminder_data.dict()
        
        print(f"🔍 DEBUG CREATE REMINDER:")
        print(f"   days tipo: {type(reminder_dict.get('days'))}")
        print(f"   days valor: {reminder_dict.get('days')}")

        new_reminder = Reminder(
            **reminder_dict,
            user_id=user_id
        )

        db.add(new_reminder)
        db.commit()
        db.refresh(new_reminder)
        
        print(f"✅ Recordatorio guardado en BD:")
        print(f"   ID: {new_reminder.id}")
        print(f"   days en BD: {new_reminder.days}")
        
        return new_reminder

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail="REMINDER_CREATE_ERROR"
        )
    
def list_reminders(db: Session, user_id: int):
    try:
        reminders = db.query(Reminder).filter_by(
            user_id=user_id,
            is_deleted=False
        ).all()
        return reminders
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="REMINDERS_FETCH_ERROR")
    
def update_reminder(db: Session, reminder_id: int, user_id: int, reminder_data: dict):
    try:
        # 🔵 LOG AGREGADO
        print(f"🔵 Buscando reminder_id={reminder_id} para user_id={user_id}")
        
        reminder = db.query(Reminder).filter_by(
            id=reminder_id, 
            user_id=user_id, 
            is_deleted=False
        ).first()
        
        if not reminder:
            raise HTTPException(
                status_code=404, 
                detail="REMINDER_NOT_FOUND"
            )
        
        # 🔵 LOG AGREGADO
        print(f"🔵 reminder_type ANTES del update: {reminder.reminder_type}")
        
        # Actualizar solo los campos proporcionados
        for key, value in reminder_data.items():
            if value is not None:
                # 🔵 LOG AGREGADO
                print(f"🔵 Actualizando {key} = {value}")
                setattr(reminder, key, value)
        
        # 🔵 LOG AGREGADO
        print(f"🔵 reminder_type DESPUÉS del setattr: {reminder.reminder_type}")
        print(f"🔵 Ejecutando db.commit()...")
        
        db.commit()
        db.refresh(reminder)
        
        # 🔵 LOG AGREGADO
        print(f"🔵 reminder_type DESPUÉS del commit: {reminder.reminder_type}")
        print(f"✅ Reminder actualizado exitosamente")
        
        return reminder
        
    except HTTPException:
        db.rollback()
        print(f"❌ HTTPException - Rollback ejecutado")
        raise
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ SQLAlchemyError - Rollback ejecutado: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="REMINDER_UPDATE_ERROR"
        )