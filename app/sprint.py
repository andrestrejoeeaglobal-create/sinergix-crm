"""Motor del Sprint 28 (Sinergix Eco) — máquina de estados de 28 días con plan adaptativo y renovación a los 90 días.

Nomenclatura (Enmienda 5): Sprint 28 (no PH21). Banda interna: "Eco" (Sinergix Eco).
Renovación (Enmienda 6): Al completar 28 días, el lead pasa al estado "Renovación pendiente" (dentro del ciclo de 90 días).
"""
from dataclasses import dataclass

# Fases del Sprint 28 (Banda Eco)
FASES = [
    (1, 7, "Reset"),
    (8, 14, "Ignicion"),
    (15, 21, "Ingenieria"),
    (22, 28, "Cierre"),
]

# Hitos base del Sprint 28 → plantilla que dispara
HITOS = {
    7: "SPR_02",   # fin de Reset Metabólico (condicional a adherencia)
    14: "SPR_03",  # evaluación intermedia con comparativa real
    21: "SPR_04",  # Ingeniería Tisular — apertura de diálogo
    25: "SPR_05",  # pre-recompra + Re-Auditoría (hito crítico)
    28: "DIA_28",  # Re-Auditoría presencial + transición a Renovación Pendiente (Sprint 28)
}

UMBRAL_ADHERENCIA_DIA7 = 60.0


@dataclass
class EstadoNoche:
    dia_calendario: int
    dia_efectivo: int
    fase: str
    registrado: bool
    reconstruccion: bool
    adherencia_dia: float
    hitos_disparados: list
    estado_renovacion: str  # "al_dia" | "renovacion_pendiente"


def fase_por_dia(dia_efectivo: int) -> str:
    if dia_efectivo <= 0:
        return FASES[0][2]
    for inicio, fin, nombre in FASES:
        if inicio <= dia_efectivo <= fin:
            return nombre
    return "Cierre" if dia_efectivo > 28 else FASES[0][2]


def dia_efectivo(dia_calendario: int, reconstrucciones: int) -> int:
    return max(0, dia_calendario - reconstrucciones)


def hitos_en(dia_efectivo: int) -> list[str]:
    return [nombre for dia_base, nombre in HITOS.items() if dia_base == dia_efectivo]


def evaluar_estado_renovacion(dia_efectivo: int, ciclo_dias: int = 90) -> str:
    """Evalúa el estado de renovación conforme a la Enmienda 6:
    Al completar 28 días del Sprint 28, el lead pasa a 'Renovación pendiente' (dentro del ciclo de 90 días).
    """
    if dia_efectivo >= 28:
        return "renovacion_pendiente"
    return "al_dia"


def procesar_noche(dia_calendario: int, reconstrucciones: int, resumen: dict) -> EstadoNoche:
    """Procesa una noche del Sprint 28 con datos REALES de BiometriaAPI.

    resumen: {registrado: bool, adherencia_dia: float, hrv, fc_reposo, sueno_horas}
    """
    registrado = bool(resumen.get("registrado", False))
    efectivo = dia_efectivo(dia_calendario, reconstrucciones)
    hubo_reconstruccion = not registrado
    if hubo_reconstruccion:
        efectivo = dia_efectivo(dia_calendario, reconstrucciones + 1)

    estado_renovacion = evaluar_estado_renovacion(efectivo)

    return EstadoNoche(
        dia_calendario=dia_calendario,
        dia_efectivo=efectivo,
        fase=fase_por_dia(efectivo),
        registrado=registrado,
        reconstruccion=hubo_reconstruccion,
        adherencia_dia=float(resumen.get("adherencia_dia", 0.0)) * 100,
        hitos_disparados=hitos_en(efectivo),
        estado_renovacion=estado_renovacion
    )
