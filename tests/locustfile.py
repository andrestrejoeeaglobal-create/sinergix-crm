"""Script de Pruebas de Carga y Estrés con Locust para Sinergix CRM.

Escenarios:
  1. Ingesta de telemetría biométrica Banda H7 (POST /api/biometrics/ingest)
  2. Consultas al dashboard analítico MongoDB $facet (GET /api/reports/dashboard)
  3. Publicación de eventos en el bus multimódulo (POST /api/ecosystem/bus/publish)
"""
from locust import HttpUser, task, between
import random


class SinergixLoadUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(3)
    def ingesta_biometrica_h7(self):
        self.client.post("/api/biometrics/ingest", json={
            "lead_id": "lead_fase5_test",
            "hrv_ms": random.randint(30, 90),
            "frecuencia_cardiaca_lpm": random.randint(50, 90),
            "temperatura_basal_delta": round(random.uniform(-0.2, 0.5), 2),
            "minutos_sueno": 480,
            "calidad_sueno_porcentaje": 88.0,
            "dispositivo_id": "LOCUST_H7_TEST"
        })

    @task(2)
    def consulta_dashboard_facet(self):
        self.client.get("/api/reports/dashboard", headers={"X-API-Token": "token-default"})

    @task(1)
    def publicacion_bus_eventos(self):
        self.client.post("/api/ecosystem/bus/publish", json={
            "modulo_origen": "salud",
            "tipo_evento": "biometria.alerta",
            "payload": {"lead_id": "lead_fase5_test", "hrv_baja": True}
        })
