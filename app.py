# Ing. Axel Jesús García Ramírez
# Chat bot CEFOPED V1.1
#03/09/2025
# APP
from flask import Flask, render_template, request, jsonify, session
import json, difflib, unicodedata

app = Flask(__name__)
app.secret_key = "clave-super-secreta"

# Cargar FAQs
with open("faqs.json", "r", encoding="utf-8") as f:
    faqs = json.load(f)

def normaliza(txt: str) -> str:
    txt = txt.lower().strip()
    txt = "".join(c for c in unicodedata.normalize("NFD", txt) if unicodedata.category(c) != "Mn")
    return " ".join(txt.split())

# Respuestas directas con sugerencias incluidas
respuestas_directas = {
    "hola": {
        "respuesta": "¡Hola! Soy tu asistente virtual, dime tu duda.",
        "sugerencias": ["¿Cómo ingresar usuario?", "¿Cómo recuperar contraseña?"]
    },
    "ayuda": {
        "respuesta": "Claro, dime qué problema tienes (ej. 'no puedo iniciar sesión').",
        "sugerencias": ["¿Cómo ingresar usuario?", "¿Dónde encuentro mi usuario?"]
    },
    "contraseña": {
        "respuesta": "Si tu contraseña no funciona, revisa que no copies espacios en blanco.",
        "sugerencias": ["¿Olvidé mi contraseña?", "¿Cómo recuperar contraseña?"]
    },
    "usuario": {
        "respuesta": "Tu usuario fue enviado en el correo, revisa bandeja de entrada o spam.",
        "sugerencias": ["¿Dónde encuentro mi usuario?", "¿Cómo ingresar usuario?"]
    }
}

# Prepara índice de búsqueda
buscables = []
for i, faq in enumerate(faqs):
    base = [faq["pregunta"]]
    if "aliases" in faq:
        base += faq["aliases"]
    for frase in base:
        buscables.append({"key": normaliza(frase), "idx": i})

def buscar_respuesta(pregunta_usuario: str):
    q = normaliza(pregunta_usuario)

    # Primero: respuestas directas
    if q in respuestas_directas:
        return {
            "respuesta": respuestas_directas[q]["respuesta"],
            "video": None
        }, respuestas_directas[q]["sugerencias"]

    # Si no es directa, buscar en faqs
    universe = [b["key"] for b in buscables]
    matches = difflib.get_close_matches(q, universe, n=3, cutoff=0.6)  # cutoff más alto
    if matches:
        best = matches[0]
        idx_best = next(b["idx"] for b in buscables if b["key"] == best)
        sugerencias = []
        for m in matches[1:]:
            idx = next(b["idx"] for b in buscables if b["key"] == m)
            sugerencias.append(faqs[idx]["pregunta"])

        # Eliminar duplicados de sugerencias
        sugerencias = list(dict.fromkeys(sugerencias))
        return faqs[idx_best], sugerencias

    return None, []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    faq, sugerencias = buscar_respuesta(user_input)

    if "fails" not in session:
        session["fails"] = 0

    if faq:
        session["fails"] = 0
        return jsonify({
            "respuesta": faq["respuesta"],
            "video": faq.get("video"),
            "sugerencias": sugerencias
        })
    else:
        session["fails"] += 1
        if session["fails"] >= 2:
            return jsonify({
                "respuesta": "No entiendo lo que dices 😅. ¿Puedes explicarlo con más detalle?",
                "video": None,
                "sugerencias": []
            })
        else:
            return jsonify({
                "respuesta": "No encontré una respuesta exacta. ¿Te refieres a alguna de estas?",
                "video": None,
                "sugerencias": [f["pregunta"] for f in faqs[:3]]
            })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
