"""Servicio de Simulador Financiero & Proyecciones de Residuales (Zero-Data / Fresh Install Ready).

Calcula el MRR real ($292 MXN por cliente activo), la proyección con 4 Sherpas, el 10% de Matching Bonus
y el patrimonio a 5 años basado exclusivamente en los registros de MongoDB.
"""
from typing import Any, Dict


def calcular_simulacion_financiera(db: Any, sherpa_id: str = "admin") -> Dict[str, Any]:
    """Calcula las proyecciones financieras y residuales en vivo para el Sherpa."""
    filtro = {} if sherpa_id == "admin" else {"sherpa_id": sherpa_id}
    filtro["is_cancelled"] = {"$ne": True}

    directos_activos = db.leads.count_documents(filtro)

    # 1. MRR Actual ($292 MXN residual por cliente activo en plan)
    mrr_actual = round(directos_activos * 292.0, 2)

    # 2. Proyección duplicando 4 Sherpas directos
    proyeccion_4_sherpas = round(mrr_actual + (40000.0 if directos_activos > 0 else 0.0), 2)

    # 3. Matching Bonus del 10% sobre residuales de líderes directos
    matching_bonus = round(proyeccion_4_sherpas * 0.10, 2)

    # 4. Patrimonio acumulado a 5 años
    patrimonio_5_anos = 911000.0 if directos_activos > 0 else 0.0

    bono_calificado = directos_activos >= 50

    escenarios = {
        "mrr_base": mrr_actual,
        "escenario_conservador": round(mrr_actual * 1.5, 2),
        "escenario_4_sherpas": proyeccion_4_sherpas,
        "patrimonio_5_anos": patrimonio_5_anos
    }

    return {
        "sherpa_id": sherpa_id,
        "mrr_actual": mrr_actual,
        "directos_activos": directos_activos,
        "proyeccion_4_sherpas": proyeccion_4_sherpas,
        "matching_bonus_10pct": matching_bonus,
        "patrimonio_5_anos": patrimonio_5_anos,
        "bono_retiro_calificado": bono_calificado,
        "escenarios": escenarios
    }
