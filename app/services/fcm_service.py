import firebase_admin
from firebase_admin import credentials, messaging
from typing import List, Optional, Dict
import os
import json
import logging
import time

logger = logging.getLogger(__name__)

class FCMService:
    """
    Servicio singleton para enviar notificaciones push mediante Firebase Cloud Messaging.
    Se inicializa automáticamente al importarse.
    """
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FCMService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not FCMService._initialized:
            self._initialize_firebase()
            FCMService._initialized = True
    
    def _initialize_firebase(self):
        """Inicializa Firebase Admin SDK una sola vez"""
        try:
            # ✅ PRIORIDAD 1: Variable de entorno (RENDER/PRODUCCIÓN)
            firebase_creds = os.getenv('FIREBASE_CREDENTIALS')
            
            if firebase_creds:
                logger.info("🔥 Inicializando Firebase desde variable de entorno")
                try:
                    # Parsear JSON desde string
                    cred_dict = json.loads(firebase_creds)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                    logger.info("✅ Firebase inicializado correctamente desde variable de entorno")
                    return
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Error parseando FIREBASE_CREDENTIALS: {e}")
                    logger.error("   Asegúrate de que sea un JSON válido")
                except Exception as e:
                    logger.error(f"❌ Error con variable de entorno: {e}")
            
            # ✅ PRIORIDAD 2: Archivo local (DESARROLLO)
            current_dir = os.path.dirname(__file__)
            cred_path = os.path.abspath(os.path.join(current_dir, "..", "..", "firebase-credentials.json"))
            
            if os.path.exists(cred_path):
                logger.info(f"🔥 Inicializando Firebase desde archivo: {cred_path}")
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                logger.info("✅ Firebase inicializado correctamente desde archivo")
                return
            
            # ❌ No se encontró ninguna configuración
            logger.warning("⚠️ No se encontraron credenciales de Firebase")
            logger.warning(f"   Archivo buscado en: {cred_path}")
            logger.warning(f"   Variable FIREBASE_CREDENTIALS: {'Configurada' if firebase_creds else 'No configurada'}")
            logger.warning("   Las notificaciones FCM NO funcionarán")
            
        except ValueError as e:
            # Ya está inicializado (puede pasar en hot-reload)
            if "already exists" in str(e).lower():
                logger.info("ℹ️ Firebase ya estaba inicializado")
            else:
                logger.error(f"❌ ValueError inicializando Firebase: {e}")
        except Exception as e:
            logger.error(f"❌ Error inicializando Firebase: {e}")
            import traceback
            traceback.print_exc()
    
    async def enviar_notificacion_mensaje(
        self,
        token: str,
        grupo_id: int,
        grupo_nombre: str,
        remitente_nombre: str,
        mensaje: str,
        timestamp: Optional[int] = None
    ) -> bool:
        """
        ✅ NUEVO: Envía notificación de MENSAJE con todos los datos necesarios
        para acumulación
        
        Args:
            token: Token FCM del dispositivo
            grupo_id: ID del grupo
            grupo_nombre: Nombre del grupo
            remitente_nombre: Nombre de quien envió el mensaje
            mensaje: Contenido del mensaje
            timestamp: Timestamp del mensaje (opcional)
        
        Returns:
            bool: True si se envió correctamente
        
        Example:
            await fcm_service.enviar_notificacion_mensaje(
                token="dispositivo_token_123",
                grupo_id=123,
                grupo_nombre="Familia",
                remitente_nombre="Juan",
                mensaje="Hola, ¿cómo están?",
                timestamp=1730000000000
            )
        """
        try:
            # ✅ DATOS COMPLETOS para acumulación
            notification_data = {
                "type": "nuevo_mensaje",
                "grupo_id": str(grupo_id),
                "grupo_nombre": grupo_nombre,
                "remitente_nombre": remitente_nombre,  # ✅ CRÍTICO
                "cuerpo": mensaje,
                "timestamp": str(timestamp or int(time.time() * 1000))
            }
            
            # Título para la notificación
            titulo = f"💬 {grupo_nombre}"
            
            # Construir mensaje FCM
            message = messaging.Message(
                notification=messaging.Notification(
                    title=titulo,
                    body=f"{remitente_nombre}: {mensaje[:50]}..."  # Preview
                ),
                data=notification_data,
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='recuerdago_mensajes',  # ✅ Debe coincidir con Android
                        click_action='FLUTTER_NOTIFICATION_CLICK'
                    )
                )
            )
            
            # Enviar
            response = messaging.send(message)
            logger.info(f"✅ FCM mensaje enviado: {response}")
            logger.info(f"   Grupo: {grupo_nombre} | Remitente: {remitente_nombre}")
            return True
            
        except messaging.UnregisteredError:
            logger.warning(f"⚠️ Token FCM no registrado: {token[:20]}...")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error enviando FCM mensaje: {e}")
            return False
    
    async def enviar_notificacion(
        self,
        token: str,
        titulo: str,
        cuerpo: str,
        data: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        ⚠️ DEPRECATED: Usar enviar_notificacion_mensaje() para mensajes
        
        Envía una notificación FCM genérica a un dispositivo específico
        """
        try:
            notification_data = {}
            if data:
                notification_data = {k: str(v) for k, v in data.items()}
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=titulo,
                    body=cuerpo[:100]
                ),
                data=notification_data,
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='recuerdago_mensajes',
                        click_action='FLUTTER_NOTIFICATION_CLICK'
                    )
                )
            )
            
            response = messaging.send(message)
            logger.info(f"✅ FCM enviado correctamente: {response}")
            return True
            
        except messaging.UnregisteredError:
            logger.warning(f"⚠️ Token FCM no registrado o expirado: {token[:20]}...")
            return False
            
        except firebase_admin.exceptions.InvalidArgumentError as e:
            logger.error(f"❌ Argumento inválido en FCM: {e}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error enviando FCM: {e}")
            return False
    
    async def enviar_mensaje_a_grupo(
        self,
        tokens: List[str],
        grupo_id: int,
        grupo_nombre: str,
        remitente_nombre: str,
        mensaje: str,
        timestamp: Optional[int] = None
    ) -> Dict[str, any]:
        """
        ✅ FALLBACK: Enviar uno por uno si send_multicast no está disponible
        """
        if not tokens:
            logger.warning("⚠️ No hay tokens para enviar")
            return {"exitosos": 0, "fallidos": 0, "tokens_invalidos": []}
        
        try:
            notification_data = {
                "type": "nuevo_mensaje",
                "grupo_id": str(grupo_id),
                "grupo_nombre": grupo_nombre,
                "remitente_nombre": remitente_nombre,
                "cuerpo": mensaje,
                "timestamp": str(timestamp or int(time.time() * 1000)),
                "titulo": f"💬 {grupo_nombre}"
            }
            
            # ✅ INTENTAR send_multicast primero
            try:
                message = messaging.MulticastMessage(
                    data=notification_data,
                    tokens=tokens,
                    android=messaging.AndroidConfig(priority='high')
                )
                
                response = messaging.send_multicast(message)
                
                tokens_invalidos = []
                if response.failure_count > 0:
                    for idx, resp in enumerate(response.responses):
                        if not resp.success:
                            tokens_invalidos.append(tokens[idx])
                            logger.warning(f"⚠️ Token inválido: {tokens[idx][:20]}...")
                
                logger.info(f"📊 FCM grupo: {response.success_count} exitosos, {response.failure_count} fallidos")
                
                return {
                    "exitosos": response.success_count,
                    "fallidos": response.failure_count,
                    "tokens_invalidos": tokens_invalidos
                }
            
            except AttributeError:
                # ⚠️ FALLBACK: send_multicast no disponible, enviar uno por uno
                logger.warning("⚠️ send_multicast no disponible, usando send() individual")
                
                exitosos = 0
                fallidos = 0
                tokens_invalidos = []
                
                for token in tokens:
                    try:
                        message = messaging.Message(
                            data=notification_data,
                            token=token,
                            android=messaging.AndroidConfig(priority='high')
                        )
                        
                        response = messaging.send(message)
                        exitosos += 1
                        logger.info(f"✅ FCM enviado a token: {token[:20]}...")
                        
                    except messaging.UnregisteredError:
                        fallidos += 1
                        tokens_invalidos.append(token)
                        logger.warning(f"⚠️ Token no registrado: {token[:20]}...")
                    
                    except Exception as e:
                        fallidos += 1
                        logger.error(f"❌ Error enviando a token {token[:20]}...: {e}")
                
                logger.info(f"📊 FCM individual: {exitosos} exitosos, {fallidos} fallidos")
                
                return {
                    "exitosos": exitosos,
                    "fallidos": fallidos,
                    "tokens_invalidos": tokens_invalidos
                }
                
        except Exception as e:
            logger.error(f"❌ Error en envío: {e}")
            import traceback
            traceback.print_exc()
            return {
                "exitosos": 0,
                "fallidos": len(tokens),
                "tokens_invalidos": []  # ❌ NO marcar como inválidos si fue error del SDK
            }
    
    async def enviar_a_multiples(
        self,
        tokens: List[str],
        titulo: str,
        cuerpo: str,
        data: Optional[Dict[str, str]] = None
    ) -> Dict[str, any]:
        """
        ⚠️ DEPRECATED: Usar enviar_mensaje_a_grupo() para mensajes
        
        Envía notificación genérica a múltiples dispositivos
        """
        if not tokens:
            logger.warning("⚠️ No se proporcionaron tokens")
            return {"exitosos": 0, "fallidos": 0, "tokens_invalidos": []}
        
        try:
            notification_data = {}
            if data:
                notification_data = {k: str(v) for k, v in data.items()}
            
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=titulo,
                    body=cuerpo[:100]
                ),
                data=notification_data,
                tokens=tokens,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='recuerdago_mensajes'
                    )
                )
            )
            
            response = messaging.send_multicast(message)
            
            tokens_invalidos = []
            if response.failure_count > 0:
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        tokens_invalidos.append(tokens[idx])
            
            logger.info(f"📊 FCM multicast: {response.success_count} exitosos, {response.failure_count} fallidos")
            
            return {
                "exitosos": response.success_count,
                "fallidos": response.failure_count,
                "tokens_invalidos": tokens_invalidos
            }
            
        except Exception as e:
            logger.error(f"❌ Error en envío multicast: {e}")
            return {
                "exitosos": 0,
                "fallidos": len(tokens),
                "tokens_invalidos": tokens
            }
    
    async def verificar_token_valido(self, token: str) -> bool:
        """
        Verifica si un token FCM es válido
        """
        try:
            message = messaging.Message(
                data={"tipo": "validacion"},
                token=token,
                android=messaging.AndroidConfig(priority='normal')
            )
            
            messaging.send(message, dry_run=True)
            return True
            
        except messaging.UnregisteredError:
            return False
        except Exception as e:
            logger.error(f"❌ Error verificando token: {e}")
            return False

    async def send_silent_refresh_ping(self, fcm_token: str) -> str:
        """
        Envía un FCM Data Message silencioso para despertar la app Android
        y que refresque el access_token sin intervención del usuario.

        Características:
          - SIN campo notification:{} → no genera notificación visible
          - android.priority='high' → rompe Doze mode / App Standby
          - data.type='SILENT_TOKEN_REFRESH' → Android identifica el intent

        Args:
            fcm_token: Token FCM del dispositivo destino

        Returns:
            str: Estado del envío:
              - 'sent'          → Mensaje enviado correctamente
              - 'invalid_token' → Token inválido, eliminado de la DB
              - 'error'         → Error inesperado, token NO eliminado
        """
        try:
            message = messaging.Message(
                # ✅ SOLO data, SIN notification — completamente silencioso
                data={
                    "type": "SILENT_TOKEN_REFRESH"
                },
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority='high'  # Rompe Doze mode
                )
            )

            response = messaging.send(message)
            logger.debug(f"📡 Silent ping enviado: {response}")
            return "sent"

        except messaging.UnregisteredError:
            # Token fue válido pero el dispositivo ya no está registrado
            logger.warning(f"⚠️ Token FCM no registrado, limpiando: {fcm_token[:20]}...")
            self._cleanup_invalid_token(fcm_token)
            return "invalid_token"

        except firebase_admin.exceptions.InvalidArgumentError:
            # Token con formato inválido o corrupto
            logger.warning(f"⚠️ Token FCM inválido, limpiando: {fcm_token[:20]}...")
            self._cleanup_invalid_token(fcm_token)
            return "invalid_token"

        except Exception as e:
            # Error del SDK o de red — NO eliminar el token (puede ser temporal)
            logger.error(f"❌ Error enviando silent ping: {e}")
            return "error"

    def _cleanup_invalid_token(self, fcm_token: str) -> None:
        """
        Elimina un token FCM inválido de la tabla fcm_tokens.
        
        Usa SQLAlchemy Core (DELETE directo) en lugar de ORM para
        ser lo más liviano posible — no carga el objeto FCMToken.
        """
        try:
            from ..usuarios.models import FCMToken
            from ..database.database import SessionLocal
            from sqlalchemy import delete

            db = SessionLocal()
            try:
                result = db.execute(
                    delete(FCMToken).where(FCMToken.token == fcm_token)
                )
                db.commit()
                deleted = result.rowcount
                if deleted:
                    logger.info(f"🗑️ Token FCM inválido eliminado de la DB ({deleted} fila(s))")
                else:
                    logger.warning(f"⚠️ Token FCM no encontrado en DB para limpiar: {fcm_token[:20]}...")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"❌ Error limpiando token FCM de la DB: {e}")


# ✅ Instancia única global (singleton)
fcm_service = FCMService()