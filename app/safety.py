"""SafetyEngine COFEPRIS & Meta Opt-In Guard — middleware de compliance para todo mensaje saliente.

Fuente: sinergix-dev/safety_engine.py, adaptado para Sinergix CRM (Sprint 28 / Fase 1).
Regla dura:
1. NINGÚN mensaje sale sin pasar por validate().
2. NINGÚN mensaje saliente por Cloud API/HSM sale si consentimiento_whatsapp == False (Enmienda 3).
"""
import re
from typing import Optional, Dict, Any

# (patrón, severidad, categoría, sustitución segura)
REGLAS = [
    (re.compile(r"\bcura(?:r|s|n)?\b", re.I), "alta", "atribución terapéutica", "apoya el bienestar"),
    (re.compile(r"\btrata(?:r|s|n|miento)\b", re.I), "alta", "vocabulario clínico", "acompaña tu proceso"),
    (re.compile(r"\bpaciente[s]?\b", re.I), "alta", "vocabulario clínico", "Ascendans"),
    (re.compile(r"\benfermedad(?:es)?\b", re.I), "alta", "mención de enfermedad", "desafío de bienestar"),
    (re.compile(r"\bdiagnóstic[oa]s?\b", re.I), "alta", "vocabulario clínico", "evaluación de bienestar"),
    (re.compile(r"\breceta[s]?\b", re.I), "alta", "vocabulario clínico", "plan nutricional"),
    (re.compile(r"\bquema(?:r|s|n)?\s+(la\s+)?grasa\b", re.I), "alta", "promesa de pérdida", "apoya la composición corporal"),
    (re.compile(r"\b(?:pierde|baja|adelgaz)\w*\s+(de\s+)?(peso|kilos)\b", re.I), "alta", "promesa de pérdida", "apoya tus metas de bienestar"),
    (re.compile(r"\belimina\w*\b", re.I), "media", "resultado garantizado", "se reduce"),
    (re.compile(r"\bgarantizamos?\b", re.I), "alta", "garantía de resultados", "buscamos que"),
    (re.compile(r"\b100%\s+(eficaz|garantizado|seguro)\b", re.I), "alta", "garantía de resultados", "con constancia y datos"),
    (re.compile(r"\bdiabetes|hipertensión|cáncer|cancer|colesterol\b", re.I), "alta", "mención de enfermedad", "condición de salud (sin nombrarla)"),
    (re.compile(r"\bantes\s+y\s+después\b", re.I), "media", "imagen antes/después", "comparativa de métricas personales"),
    (re.compile(r"\bdesaparec\w+\b", re.I), "media", "resultado garantizado", "se reduce"),
]


def validate(texto: str) -> dict:
    """Audita un texto. Devuelve {ok, hallazgos, texto_seguro}.

    ok=False → el mensaje NO debe enviarse tal cual; usar texto_seguro.
    """
    hallazgos = []
    texto_seguro = texto
    for patron, severidad, categoria, sustituto in REGLAS:
        m = patron.search(texto_seguro)
        if m:
            hallazgos.append({"termino": m.group(0), "severidad": severidad, "categoria": categoria})
            texto_seguro = patron.sub(sustituto, texto_seguro)
    return {"ok": not hallazgos, "hallazgos": hallazgos, "texto_seguro": texto_seguro}


def assert_seguro(texto: str) -> str:
    """Devuelve el texto seguro o lanza ValueError si tiene hallazgos de severidad alta."""
    r = validate(texto)
    altas = [h for h in r["hallazgos"] if h["severidad"] == "alta"]
    if altas:
        raise ValueError(f"Mensaje bloqueado por SafetyEngine: {altas}")
    return r["texto_seguro"]


def validar_optin_whatsapp(lead_dict_o_obj: Any) -> bool:
    """Valida que el lead cuente con consentimiento explícito de WhatsApp conforme a la política de Meta (Enmienda 3).
    
    Si consentimiento_whatsapp (o optin_whatsapp) es False, bloquea el envío saliente.
    """
    if isinstance(lead_dict_o_obj, dict):
        optin = lead_dict_o_obj.get("consentimiento_whatsapp")
        if optin is None:
            optin = lead_dict_o_obj.get("optin_whatsapp", False)
    else:
        optin = getattr(lead_dict_o_obj, "consentimiento_whatsapp", None)
        if optin is None:
            optin = getattr(lead_dict_o_obj, "optin_whatsapp", False)

    if not optin:
        raise ValueError("Envío de WhatsApp bloqueado: El lead no cuenta con consentimiento explícito (opt-in registrado).")

    return True
