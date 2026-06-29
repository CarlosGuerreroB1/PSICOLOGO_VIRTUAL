
import base64
import numpy as np
import cv2
from deepface import DeepFace


def decodificar_frame(frame_base64: str) -> np.ndarray:
    if "," in frame_base64:
        frame_base64 = frame_base64.split(",")[1]
    datos = base64.b64decode(frame_base64)
    arreglo = np.frombuffer(datos, dtype=np.uint8)
    return cv2.imdecode(arreglo, cv2.IMREAD_COLOR)


def analizar_emocion_facial(frame_base64: str) -> dict:

    respuesta_default = {
        "emocion": "neutral",
        "confianza": 0.0,
        "rostro_detectado": False,
    }

    try:
        imagen = decodificar_frame(frame_base64)

        if imagen is None:
            return respuesta_default

        # FIX: enforce_detection=False → no lanza FaceNotDetected,
        # devuelve neutral cuando no hay rostro en el frame.
        resultado = DeepFace.analyze(
            img_path=imagen,
            actions=["emotion"],
            enforce_detection=False,
            silent=True,
        )

        if isinstance(resultado, list):
            resultado = resultado[0]

        emociones         = resultado.get("emotion", {})
        emocion_dominante = resultado.get("dominant_emotion", "neutral")

        if not emociones or not emocion_dominante:
            return respuesta_default
        confianza = float(emociones.get(emocion_dominante, 0.0)) / 100.0

        return {
            "emocion":          traducir_emocion(emocion_dominante),
            "confianza":        round(confianza, 2),
            "rostro_detectado": confianza > 0.0,
        }

    except Exception:

        return respuesta_default


def traducir_emocion(emocion_en: str) -> str:
    mapa = {
        "happy":    "alegria",
        "sad":      "tristeza",
        "angry":    "enojo",
        "fear":     "miedo",
        "surprise": "sorpresa",
        "disgust":  "apatia",
        "neutral":  "neutral",
    }
    return mapa.get(emocion_en, "neutral")
