# Ing. Axel Jesús García Ramírez
# Chat bot CEFOPED V1.0
# APP
from flask import Flask, render_template, request, jsonify
import json, difflib, unicodedata

app = Flask(__name__)

# Cargar FAQs
with open("faqs.json", "r", encoding="utf-8") as f:
    faqs = json.load(f)

def normaliza(txt: str) -> str:
    txt = txt.lower().strip()
    txt = "".join(c for c in unicodedata.normalize("NFD", txt) if unicodedata.category(c) != "Mn")
    return " ".join(txt.split())  # colapsar espacios

# Prepara índice de búsqueda (pregunta + aliases)
buscables = []
for i, faq in enumerate(faqs):
    base = [faq["pregunta"]]
    if "aliases" in faq:
        base += faq["aliases"]
    for frase in base:
        buscables.append({"key": normaliza(frase), "idx": i})

def buscar_respuesta(pregunta_usuario: str):
    q = normaliza(pregunta_usuario)
    universe = [b["key"] for b in buscables]
    # Top 3 coincidencias aproximadas
    matches = difflib.get_close_matches(q, universe, n=3, cutoff=0.35)
    if matches:
        # Regresa la mejor y sugerencias
        best = matches[0]
        idx_best = next(b["idx"] for b in buscables if b["key"] == best)
        sugerencias = []
        for m in matches[1:]:
            idx = next(b["idx"] for b in buscables if b["key"] == m)
            sugerencias.append(faqs[idx]["pregunta"])
        return faqs[idx_best], sugerencias
    return None, []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    faq, sugerencias = buscar_respuesta(user_input)
    if faq:
        return jsonify({
            "respuesta": faq["respuesta"],
            "video": faq.get("video"),
            "sugerencias": sugerencias
        })
    else:
        return jsonify({
            "respuesta": "No encontré una respuesta exacta. ¿Te refieres a alguna de estas?",
            "video": None,
            "sugerencias": [f["pregunta"] for f in faqs[:3]]
        })

if __name__ == "__main__":
    # Para correr localmente
    app.run(host="0.0.0.0", port=5000, debug=True)
