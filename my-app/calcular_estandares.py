"""Recalcula los estándares de tiempo por proceso/actividad.

Analiza el histórico de operaciones de los últimos 30 días y actualiza
tbl_estandares_proceso_actividad (tiempo promedio, desviación, dificultad...).

Estos estándares alimentan:
  - El Planificador de Personal
  - La sección "Eficiencia real vs. estándar" del Dashboard de Operaciones

Conviene ejecutarlo periódicamente (semanal) por cron:
    cd /ruta/al/my-app && /ruta/al/venv/bin/python calcular_estandares.py
"""
from app import app
from controllers.funciones_home import actualizar_estandares_procesos

if __name__ == '__main__':
    with app.app_context():
        print("Recalculando estándares desde el histórico (últimos 30 días)...")
        resultado = actualizar_estandares_procesos()
        print("Resultado:", resultado)
