
"""
service/chat.py
───────────────
Conversación con OpenAI integrada con flujo DASS-21.
FIX: una vez completado el DASS, el estado se marca como "completado=True"
y el bot vuelve a conversación normal sin volver a proponer el cuestionario.
"""

import os
from openai import OpenAI
from . import dass as dass_service


def get_client():
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


SYSTEM_PROMPT = """
Eres Empathy AI, un asistente de apoyo emocional entrenado para administrar
el cuestionario DASS-21 de forma conversacional.

Flujo de la sesión:
1. Saluda y escucha al usuario 2-3 turnos para generar rapport.
2. Cuando el usuario haya expresado cómo se siente, di algo como:
   "Para entenderte mejor, me gustaría hacerte algunas preguntas breves
    sobre cómo te has sentido esta semana. ¿Estás de acuerdo?"
3. Administra las 21 preguntas DASS una por una, de forma empática.
4. Al terminar las 21 preguntas, el sistema calculará el diagnóstico
   automáticamente y tú presentarás los resultados.
5. Después del diagnóstico, vuelve a ser un compañero de conversación normal,
   empático y de apoyo. NO vuelvas a proponer el cuestionario.

Reglas generales:
- Nunca diagnostiques formalmente; acompañas y orientas.
- Si detectas ideación suicida, recomienda inmediatamente líneas de ayuda.
- Tono cálido, sin jerga clínica.
- Respuestas breves (3-5 líneas).
"""

SYSTEM_PROMPT_POST_DASS = """
Eres Empathy AI, un asistente de apoyo emocional.
Ya completaste el cuestionario DASS-21 con este usuario y tienes sus resultados.
Ahora tu rol es acompañar, escuchar y apoyar emocionalmente en base a esos resultados.
NO vuelvas a proponer el cuestionario. Simplemente conversa con calidez y empatía.
Si el usuario pregunta por sus resultados, dile que puede verlos en el botón "Ver diagnóstico".
Tono cálido, respuestas breves (3-5 líneas).
"""

PALABRAS_RIESGO = [
    "quiero morir", "suicidio", "no quiero vivir", "acabar con todo",
    "hacerme daño", "lastimarme", "no vale la pena vivir",
]


def detectar_riesgo_critico(texto: str) -> bool:
    return any(frase in texto.lower() for frase in PALABRAS_RIESGO)


# ── Detectar intención de reiniciar sesión ────────────────────────────
FRASES_NUEVA_SESION = [
    "nueva sesión", "nueva sesion", "empezar de nuevo", "comenzar de nuevo",
    "reiniciar", "borrar conversación", "borrar conversacion",
    "quiero empezar otra vez", "nueva conversación", "nueva conversacion",
    "iniciar de nuevo", "quiero una nueva sesión", "quiero una nueva sesion",
]

def quiere_nueva_sesion(texto: str) -> bool:
    return any(frase in texto.lower() for frase in FRASES_NUEVA_SESION)


def clasificar_emocion(texto: str) -> str:
    texto_lower = texto.lower()
    mapa = {
        "tristeza": ["triste", "llorar", "vacío", "solo", "soledad", "deprimido"],
        "ansiedad": ["ansioso", "ansiedad", "nervios", "preocupa", "pánico", "angustia"],
        "miedo":    ["miedo", "temor", "asustado", "terror"],
        "enojo":    ["enojado", "furioso", "rabia", "molesto", "irritado"],
        "alegria":  ["feliz", "bien", "contento", "alegre", "tranquilo"],
    }
    for emocion, palabras in mapa.items():
        if any(p in texto_lower for p in palabras):
            return emocion
    return "neutral"


def construir_historial(mensajes_previos, system_prompt=None):
    prompt = system_prompt or SYSTEM_PROMPT
    historial = [{"role": "system", "content": prompt}]
    for m in mensajes_previos:
        historial.append({"role": m.rol, "content": m.contenido})
    return historial


def generar_respuesta(mensajes_previos, mensaje_nuevo: str, sesion=None) -> dict:
    client = get_client()
    estado_dass = {}

    if sesion:
        estado_dass = sesion.estado_dass or {}

    modo_dass       = estado_dass.get("activo", False)
    dass_completado = estado_dass.get("completado", False)
    item_actual     = estado_dass.get("item_actual", 0)
    respuestas      = estado_dass.get("respuestas", {})
    rapport_turnos  = estado_dass.get("rapport_turnos", 0)

    # ── FIX: si el DASS ya se completó → conversación normal post-DASS ─
    if dass_completado:
        historial = construir_historial(mensajes_previos, SYSTEM_PROMPT_POST_DASS)
        historial.append({"role": "user", "content": mensaje_nuevo})
        resp = client.chat.completions.create(
            model="gpt-4o-mini", messages=historial, temperature=0.7, max_tokens=300,
        )
        return {
            "respuesta":         resp.choices[0].message.content,
            "emocion_detectada": clasificar_emocion(mensaje_nuevo),
            "tokens":            resp.usage.total_tokens,
            "riesgo_critico":    detectar_riesgo_critico(mensaje_nuevo),
        }

    # ── Flujo DASS activo ─────────────────────────────────────────────
    if modo_dass and item_actual > 0 and item_actual <= 21:
        item_info = dass_service.ITEMS_DASS[item_actual - 1]
        valor = dass_service.extraer_respuesta_numerica(mensaje_nuevo, item_info["texto"])
        if valor is not None:
            respuestas[str(item_actual)] = valor

        item_actual += 1
        estado_dass["item_actual"] = item_actual
        estado_dass["respuestas"]  = respuestas

        if item_actual > 21:
            # DASS completo → calcular diagnóstico
            emociones_nlp    = [m.emocion_nlp for m in mensajes_previos if m.emocion_nlp != "neutral"]
            emociones_facial = list(
                sesion.analisis_faciales.values_list("emocion_predominante", flat=True)
            ) if sesion else []

            respuestas_int = {int(k): v for k, v in respuestas.items()}
            resultado_dass = dass_service.calcular_diagnostico(respuestas_int, emociones_nlp, emociones_facial)
            resumen_dass   = dass_service.generar_resumen_diagnostico(resultado_dass)

            # ✅ FIX: limpiar estado y marcar como completado para siempre
            if sesion:
                sesion.estado_dass = {"activo": False, "completado": True, "rapport_turnos": rapport_turnos}
                sesion.save(update_fields=["estado_dass"])

            return {
                "respuesta":             resumen_dass,
                "emocion_detectada":     "neutral",
                "tokens":                0,
                "riesgo_critico":        False,
                "resultado_dass":        resultado_dass,
                "diagnostico_calculado": True,
            }

        # Siguiente pregunta DASS
        if sesion:
            sesion.estado_dass = estado_dass
            sesion.save(update_fields=["estado_dass"])

        pregunta = dass_service.formular_pregunta_dass(item_actual, mensajes_previos)
        return {
            "respuesta":         pregunta,
            "emocion_detectada": clasificar_emocion(mensaje_nuevo),
            "tokens":            0,
            "riesgo_critico":    detectar_riesgo_critico(mensaje_nuevo),
            "item_dass":         item_actual,
            "total_dass":        21,
        }

    # ── Conversación normal con GPT ───────────────────────────────────
    historial = construir_historial(mensajes_previos)
    historial.append({"role": "user", "content": mensaje_nuevo})

    respuesta_gpt = client.chat.completions.create(
        model="gpt-4o-mini", messages=historial, temperature=0.7, max_tokens=300,
    )
    texto_respuesta = respuesta_gpt.choices[0].message.content
    tokens_usados   = respuesta_gpt.usage.total_tokens
    emocion         = clasificar_emocion(mensaje_nuevo)

    # Detectar si el bot propuso el DASS y el usuario acepta
    ultima_bot = mensajes_previos[-1].contenido.lower() if mensajes_previos else ""
    acepta_dass  = any(p in mensaje_nuevo.lower() for p in ["sí", "si", "claro", "adelante", "ok", "de acuerdo", "está bien", "bueno"])
    propuso_dass = any(p in ultima_bot for p in ["algunas preguntas", "cuestionario", "dass", "hacerte preguntas", "preguntas breves"])

    if propuso_dass and acepta_dass and sesion and not modo_dass and not dass_completado:
        sesion.estado_dass = {"activo": True, "item_actual": 1, "respuestas": {}, "rapport_turnos": rapport_turnos, "completado": False}
        sesion.save(update_fields=["estado_dass"])
        primera_pregunta = dass_service.formular_pregunta_dass(1, mensajes_previos)
        return {
            "respuesta":         primera_pregunta,
            "emocion_detectada": emocion,
            "tokens":            tokens_usados,
            "riesgo_critico":    detectar_riesgo_critico(mensaje_nuevo),
            "item_dass":         1,
            "total_dass":        21,
        }

    # Contar turnos de rapport
    rapport_turnos += 1
    if sesion:
        estado_dass["rapport_turnos"] = rapport_turnos
        sesion.estado_dass = estado_dass
        sesion.save(update_fields=["estado_dass"])

    return {
        "respuesta":         texto_respuesta,
        "emocion_detectada": emocion,
        "tokens":            tokens_usados,
        "riesgo_critico":    detectar_riesgo_critico(mensaje_nuevo),
    }