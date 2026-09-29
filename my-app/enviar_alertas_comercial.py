"""Envia las alertas de control comercial (inactividad y cuota semanal
incumplida) por vendedor.

Pensado para ejecutarse por cron / tarea programada, una vez al dia:

    cd /ruta/al/proyecto/my-app
    /ruta/al/venv/bin/python enviar_alertas_comercial.py

Revisa los vendedores con una meta activa (ver /admin/metas-vendedores) y:
- Alerta si un vendedor lleva N dias sin registrar actividad comercial.
- Alerta (una vez por semana) si la semana anterior no cumplio la cuota
  minima de actividades configurada.
"""
import sys
from app import app
from controllers.funciones_home import procesar_alertas_comercial

if __name__ == '__main__':
    # Modo simulacion: python enviar_alertas_comercial.py --dry-run  (no envia, solo reporta)
    dry_run = '--dry-run' in sys.argv
    with app.app_context():
        resultado = procesar_alertas_comercial(dry_run=dry_run)
        print("Resultado alertas comerciales:", resultado)
