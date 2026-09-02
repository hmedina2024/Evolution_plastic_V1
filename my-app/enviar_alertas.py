"""Envía las alertas de documentos faltantes por proceso en las OP.

Pensado para ejecutarse por cron / tarea programada, una vez al día:

    cd /ruta/al/proyecto/my-app
    /ruta/al/venv/bin/python enviar_alertas.py

Revisa las OPs activas y, por cada proceso configurado con alerta activa
que tras 'dias_limite' no tenga documentos cargados, envía un correo a los
destinatarios del proceso (lista + correos adicionales). Reenvía según
'dias_reenvio' mientras el documento siga faltando.
"""
import sys
from app import app
from controllers.funciones_home import procesar_alertas_documentos

if __name__ == '__main__':
    # Modo simulación: python enviar_alertas.py --dry-run  (no envía, solo reporta)
    dry_run = '--dry-run' in sys.argv
    with app.app_context():
        resultado = procesar_alertas_documentos(dry_run=dry_run)
        print("Resultado alertas documentos:", resultado)
