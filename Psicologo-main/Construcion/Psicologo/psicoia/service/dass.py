import os
from openai import OpenAI

ITEMS_DASS = [
    {"num": 1,  "sub": "S", "texto": "Me costó mucho relajarme."},
    {"num": 2,  "sub": "A", "texto": "Me di cuenta de que tenía la boca seca."},
    {"num": 3,  "sub": "D", "texto": "No podía sentir ningún sentimiento positivo."},
    {"num": 4,  "sub": "A", "texto": "Tuve dificultad para respirar (p. ej. respiración excesivamente rápida o falta de aliento sin haber hecho esfuerzo físico)."},
    {"num": 5,  "sub": "D", "texto": "Me resultó difícil tener iniciativa para hacer cosas."},
    {"num": 6,  "sub": "S", "texto": "Tendí a reaccionar de forma exagerada ante las situaciones."},
    {"num": 7,  "sub": "A", "texto": "Experimenté temblores (p. ej. en las manos)."},
    {"num": 8,  "sub": "S", "texto": "Sentí que estaba muy nervioso/a."},
    {"num": 9,  "sub": "A", "texto": "Estaba preocupado/a por situaciones en las que podía entrar en pánico y hacer el ridículo."},
    {"num": 10, "sub": "D", "texto": "Sentí que no tenía nada que esperar del futuro."},
    {"num": 11, "sub": "S", "texto": "Me noté agitado/a."},
    {"num": 12, "sub": "S", "texto": "Me resultó difícil relajarme."},
    {"num": 13, "sub": "D", "texto": "Me sentí triste y deprimido/a."},
    {"num": 14, "sub": "S", "texto": "Fui intolerante con cualquier cosa que me impidiese seguir con lo que estaba haciendo."},
    {"num": 15, "sub": "A", "texto": "Estuve a punto de entrar en pánico."},
    {"num": 16, "sub": "D", "texto": "No fui capaz de entusiasmarme con nada."},
    {"num": 17, "sub": "D", "texto": "Sentí que no valía mucho como persona."},
    {"num": 18, "sub": "S", "texto": "Noté que era muy irritable."},
    {"num": 19, "sub": "A", "texto": "Noté el ritmo de mi corazón a pesar de no haber hecho ningún esfuerzo físico (p. ej. sentir que el corazón se acelera o que da un vuelco)."},
    {"num": 20, "sub": "D", "texto": "Sentí miedo sin motivo."},
    {"num": 21, "sub": "S", "texto": "Sentí que la vida no tenía sentido."},
]

BAREMOS = {
    "D": [("normal", 9), ("leve", 13), ("moderado", 20), ("severo", 27), ("muy_severo", 999)],
    "A": [("normal", 7), ("leve", 9),  ("moderado", 14), ("severo", 19), ("muy_severo", 999)],
    "S": [("normal", 14), ("leve", 18), ("moderado", 25), ("severo", 33), ("muy_severo", 999)],
}

NIVEL_ORDEN = ["normal", "leve", "moderado", "severo", "muy_severo"]

RECOMENDACIONES_POR_TIPO = {
    "respiracion": "Practica respiración diafragmática 4-7-8: inhala 4 s, aguanta 7 s, exhala 8 s. Repite 3 veces cuando sientas tensión.",
    "mindfulness": "Dedica 10 minutos al día a una meditación guiada (app Insight Timer o Calm). Enfócate en el presente sin juzgar.",
    "actividad":   "Camina 30 minutos al aire libre 3 veces por semana. El movimiento reduce el cortisol y mejora el estado de ánimo.",
    "escritura":   "Escribe en un diario cada noche 3 cosas que salieron bien hoy, por pequeñas que sean.",
    "social":      "Planifica al menos una actividad social esta semana: llamar a un amigo, salir a tomar algo, unirte a un grupo.",
    "profesional": "⚠️ Tus resultados sugieren buscar apoyo profesional. Consulta con un psicólogo o médico de cabecera lo antes posible.",
    "psicoeducacion": "Lee sobre el ciclo estrés-pensamiento-emoción. Comprender qué te pasa es el primer paso para manejarlo.",
}


def get_client():
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def nivel_por_puntuacion(subescala: str, puntuacion: int) -> str:
    for nivel, limite in BAREMOS[subescala]:
        if puntuacion <= limite:
            return nivel
    return "muy_severo"


def nivel_mas_alto(*niveles) -> str:
    indices = [NIVEL_ORDEN.index(n) for n in niveles if n in NIVEL_ORDEN]
    return NIVEL_ORDEN[max(indices)] if indices else "normal"


def extraer_respuesta_numerica(texto_usuario: str, pregunta: str) -> int | None:

    client = get_client()
    prompt = f"""
Eres un asistente que convierte respuestas de texto libre al formato DASS-21.
La escala es: 0=nunca/nada, 1=a veces/algo, 2=bastante/frecuentemente, 3=casi siempre/mucho.

Pregunta DASS: "{pregunta}"
Respuesta del usuario: "{texto_usuario}"

Responde SOLO con el número 0, 1, 2 o 3. Sin explicación.
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0,
        )
        valor = int(resp.choices[0].message.content.strip())
        return max(0, min(3, valor))
    except Exception:
        return None


# ── Generar pregunta DASS conversacional ─────────────────────────────
def formular_pregunta_dass(num_item: int, historial_previo: list) -> str:

    item = ITEMS_DASS[num_item - 1]
    client = get_client()

    system = """Eres Empathy AI. Estás administrando el cuestionario DASS-21
de manera conversacional y empática. Formula el ítem como una pregunta natural,
cálida y sin jerga clínica. Añade una frase de transición si corresponde.
Pide que responda con una escala: 0 (nunca), 1 (a veces), 2 (bastante seguido), 3 (casi siempre).
Sé breve (2-3 líneas máximo)."""

    historial = [{"role": "system", "content": system}]
    for m in historial_previo[-6:]:  # solo los últimos 6 para contexto
        historial.append({"role": m.rol, "content": m.contenido})
    historial.append({
        "role": "user",
        "content": f"Formula conversacionalmente el ítem DASS #{num_item}: '{item['texto']}'"
    })

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=historial,
            max_tokens=150,
            temperature=0.6,
        )
        return resp.choices[0].message.content
    except Exception:
        return f"En la última semana, ¿con qué frecuencia: «{item['texto']}»? (0=nunca, 1=a veces, 2=bastante, 3=casi siempre)"


# ── Calcular diagnóstico completo ─────────────────────────────────────
def calcular_diagnostico(respuestas_dass: dict, emociones_nlp: list, emociones_facial: list) -> dict:


    scores = {"D": 0, "A": 0, "S": 0}
    for item in ITEMS_DASS:
        val = respuestas_dass.get(item["num"], 0)
        scores[item["sub"]] += val
    scores = {k: v * 2 for k, v in scores.items()}

    nivel_D = nivel_por_puntuacion("D", scores["D"])
    nivel_A = nivel_por_puntuacion("A", scores["A"])
    nivel_S = nivel_por_puntuacion("S", scores["S"])

    # Ajuste por emociones NLP
    conteo_nlp = {e: emociones_nlp.count(e) for e in set(emociones_nlp)}
    if conteo_nlp.get("tristeza", 0) >= 3:
        nivel_D = nivel_mas_alto(nivel_D, "leve")
    if conteo_nlp.get("ansiedad", 0) >= 3:
        nivel_A = nivel_mas_alto(nivel_A, "leve")
    if conteo_nlp.get("enojo", 0) >= 2:
        nivel_S = nivel_mas_alto(nivel_S, "leve")

    # Ajuste por emociones faciales
    conteo_facial = {e: emociones_facial.count(e) for e in set(emociones_facial)}
    if conteo_facial.get("tristeza", 0) >= 2:
        nivel_D = nivel_mas_alto(nivel_D, "leve")
    if conteo_facial.get("miedo", 0) >= 2:
        nivel_A = nivel_mas_alto(nivel_A, "leve")

    nivel_global = nivel_mas_alto(nivel_D, nivel_A, nivel_S)

    # Confianza: mayor si hay respuestas completas
    completitud = len([v for v in respuestas_dass.values() if v is not None]) / 21
    confianza   = round(0.6 * completitud + 0.2 * min(len(emociones_nlp) / 10, 1) + 0.2 * min(len(emociones_facial) / 5, 1), 2)

    # Recomendaciones según nivel
    tipos_rec = []
    if nivel_A in ["moderado", "severo", "muy_severo"]:
        tipos_rec += ["respiracion", "mindfulness"]
    if nivel_D in ["moderado", "severo", "muy_severo"]:
        tipos_rec += ["actividad", "escritura", "social"]
    if nivel_S in ["moderado", "severo", "muy_severo"]:
        tipos_rec += ["mindfulness", "actividad"]
    if nivel_global in ["moderado", "severo", "muy_severo"]:
        tipos_rec.append("profesional")
    if not tipos_rec:
        tipos_rec = ["respiracion", "psicoeducacion"]
    tipos_rec = list(dict.fromkeys(tipos_rec))  # deduplicar manteniendo orden

    recomendaciones = [
        {"tipo": t, "descripcion": RECOMENDACIONES_POR_TIPO[t], "derivar": t == "profesional"}
        for t in tipos_rec
    ]

    return {
        "puntuacion_D": scores["D"],
        "puntuacion_A": scores["A"],
        "puntuacion_S": scores["S"],
        "nivel_D":      nivel_D,
        "nivel_A":      nivel_A,
        "nivel_S":      nivel_S,
        "nivel_global": nivel_global,
        "confianza_global": confianza,
        "recomendaciones": recomendaciones,
        "derivar_profesional": "profesional" in tipos_rec,
    }


# ── Generar texto de cierre con el diagnóstico ───────────────────────
def generar_resumen_diagnostico(resultado: dict) -> str:
    client = get_client()
    prompt = f"""
Eres Empathy AI. Has completado el cuestionario DASS-21 con el usuario.
Resultados:
  - Depresión:  {resultado['nivel_D']} ({resultado['puntuacion_D']} pts)
  - Ansiedad:   {resultado['nivel_A']} ({resultado['puntuacion_A']} pts)
  - Estrés:     {resultado['nivel_S']} ({resultado['puntuacion_S']} pts)
  - Global:     {resultado['nivel_global']}
  - Derivar a profesional: {resultado['derivar_profesional']}

Escribe un mensaje de cierre empático (5-7 líneas) que:
1. Agradezca al usuario por completar el cuestionario.
2. Explique el resultado de forma clara y sin alarmar.
3. Mencione las recomendaciones principales.
4. Si el nivel es moderado/severo/muy_severo, sugiere buscar ayuda profesional con calidez.
No uses jerga clínica. Habla en segunda persona, tono cálido.
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7,
        )
        return resp.choices[0].message.content
    except Exception:
        return "Gracias por completar el cuestionario. Tus resultados han sido guardados."
