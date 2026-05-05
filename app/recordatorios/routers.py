from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .schemas import GeofenceTriggerCreate, GeofenceTriggerOut, ReminderCreate, ReminderOut, ReminderUpdate
from .crud import *
from .models import GeofenceTrigger
from ..database.database import get_db
from ..usuarios.security import get_current_user

router = APIRouter(prefix="/reminders", tags=["Reminders"])

@router.post("/crear", response_model=ReminderOut)
def create_new_reminder(
    reminder: ReminderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        new_reminder = create_reminder(db, reminder, current_user.id)
        return new_reminder
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating reminder: {str(e)}")

@router.get("/listar", response_model=list[ReminderOut])
def get_user_reminders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return list_reminders(db, current_user.id)

@router.patch("/{reminder_id}/toggle")
def toggle_reminder(reminder_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    reminder = db.query(Reminder).filter_by(id=reminder_id, user_id=current_user.id, is_deleted=False).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="REMINDER_NOT_FOUND")
    
    reminder.is_active = not reminder.is_active
    db.commit()
    db.refresh(reminder)
    return reminder

@router.delete("/{reminder_id}/delete")
def delete_reminder(reminder_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    reminder = db.query(Reminder).filter_by(id=reminder_id, user_id=current_user.id, is_deleted=False).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="REMINDER_NOT_FOUND")
    
    reminder.is_deleted = True
    db.commit()
    return {"code": "REMINDER_DELETED_SUCCESS"}

@router.put("/{reminder_id}/editar", response_model=ReminderOut)
def edit_reminder(
    reminder_id: int,
    reminder_update: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Convertir a dict y filtrar valores None
    update_data = reminder_update.dict(exclude_unset=True)
    
    # 🔵 LOGS AGREGADOS
    print(f"🔵 REQUEST BODY RECIBIDO: {update_data}")
    print(f"🔵 reminder_type = {update_data.get('reminder_type')}")
    print(f"🔵 Editando reminder_id = {reminder_id}")
    
    updated_reminder = update_reminder(db, reminder_id, current_user.id, update_data)
    return updated_reminder

@router.post("/geofence-trigger", response_model=GeofenceTriggerOut)
def create_geofence_trigger(
    trigger_data: GeofenceTriggerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    geofence_trigger = GeofenceTrigger(
        reminder_id=trigger_data.reminder_id,
        user_id=current_user.id,
        radio_m=trigger_data.radio_m,
        gps_lat=trigger_data.gps_lat,
        gps_lon=trigger_data.gps_lon,
    )
    db.add(geofence_trigger)
    db.commit()
    db.refresh(geofence_trigger)
    return geofence_trigger
