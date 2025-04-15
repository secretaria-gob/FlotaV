import os

# Módulo de mensajería - versión sin Twilio
# Esta versión solo registra los mensajes en la consola y no envía SMS reales

# Variables de entorno (siempre serán None o no configuradas)
TWILIO_ACCOUNT_SID = None
TWILIO_AUTH_TOKEN = None
TWILIO_PHONE_NUMBER = None


def send_twilio_message(to_phone_number: str, message: str) -> bool:
    """
    Función simulada de envío de mensajes (sin usar Twilio).
    Solo registra el intento de envío en la consola.
    
    Args:
        to_phone_number: Número de teléfono del destinatario (con código de país)
        message: Texto del mensaje a enviar
    
    Returns:
        bool: True para simular éxito en el envío
    """
    print("\n===== MENSAJE SMS SIMULADO =====")
    print(f"Para: {to_phone_number}")
    print(f"Mensaje: {message}")
    print("===============================\n")
    
    # Siempre retorna True como si el mensaje se hubiera enviado
    return True


def send_maintenance_reminder(to_phone_number: str, patente: str, marca: str, modelo: str, 
                             fecha_service: str = None, km: int = None) -> bool:
    """
    Simula el envío de un recordatorio de mantenimiento.
    
    Args:
        to_phone_number: Número de teléfono del destinatario
        patente: Patente del vehículo
        marca: Marca del vehículo
        modelo: Modelo del vehículo
        fecha_service: Fecha programada para el servicio (opcional)
        km: Kilometraje para el próximo servicio (opcional)
    
    Returns:
        bool: True para simular éxito en el envío
    """
    # Construir el mensaje de recordatorio
    mensaje = f"RECORDATORIO: El vehículo {patente} ({marca} {modelo}) "
    
    if fecha_service:
        mensaje += f"tiene programado un servicio para el día {fecha_service}. "
    
    if km:
        mensaje += f"Debe realizarse un servicio al alcanzar {km} km. "
    
    mensaje += "Sistema de Gestión de Flota Vehicular."
    
    # Simular el envío
    return send_twilio_message(to_phone_number, mensaje)


def send_vtv_expiration_alert(to_phone_number: str, patente: str, marca: str, modelo: str,
                             fecha_vencimiento: str, dias_restantes: int) -> bool:
    """
    Simula el envío de una alerta de vencimiento próximo de VTV.
    
    Args:
        to_phone_number: Número de teléfono del destinatario
        patente: Patente del vehículo
        marca: Marca del vehículo
        modelo: Modelo del vehículo
        fecha_vencimiento: Fecha de vencimiento de la VTV
        dias_restantes: Días restantes hasta el vencimiento
    
    Returns:
        bool: True para simular éxito en el envío
    """
    # Construir el mensaje de alerta
    mensaje = f"ALERTA: La VTV del vehículo {patente} ({marca} {modelo}) "
    
    if dias_restantes <= 0:
        mensaje += f"venció el {fecha_vencimiento}. "
    else:
        mensaje += f"vence el {fecha_vencimiento} (en {dias_restantes} días). "
    
    mensaje += "Por favor, programe la renovación a la brevedad. "
    mensaje += "Sistema de Gestión de Flota Vehicular."
    
    # Simular el envío
    return send_twilio_message(to_phone_number, mensaje)