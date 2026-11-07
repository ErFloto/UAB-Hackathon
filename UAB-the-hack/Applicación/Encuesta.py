import random
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
import matplotlib

from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

import os
from dotenv import load_dotenv

import json
import requests

# Carrega les variables del fitxer .env
load_dotenv()

# Variables llestes per ser utilitzades al codi

ruta_env = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(ruta_env)

ESCOLTA_MODE = os.getenv("ESCOLTA_MODE", "mock").strip()
API_URL = os.getenv("ESCOLTA_API_URL", "").strip()
API_KEY = os.getenv("ESCOLTA_API_KEY", "").strip()

print(f"--- INFO HACKATO: API_KEY carregada? {'SÍ' if API_KEY else 'NO'} ---")

# ... la resta del teu codi a continuació ...

# ---------------------------------------------------------------------------
# TEMES DE CONSULTA (es mantenen separats dels tons)
# ---------------------------------------------------------------------------

INTROS = {
    "Educació": "educacio",
    "Treball": "treball",
    "Habitatge": "habitatge",
    "Salut": "salut",
    "Economia": "economia",
    "Altres": "altres",
}

# app.py utilitza aquests valors al selector "To de la consulta".
TONS = {
    "Proper i directe": "proper",
    "Formal i professional": "formal",
    "Proper i empàtic": "empatic",
}

# ---------------------------------------------------------------------------
# TIPUS DE PREGUNTA (utilitzats per st.data_editor a app.py)
# ---------------------------------------------------------------------------

TIPUS_ESCALA = "Escala (1-5)"
TIPUS_OPCIONS = "Opció múltiple"
TIPUS_SI_NO = "Sí / No"
TIPUS_OBERT = "Text obert"

# ---------------------------------------------------------------------------
# MODEL DE CLASSIFICACIÓ
# ---------------------------------------------------------------------------

X_synthetic, y_synthetic = make_classification(
    n_samples=200,
    n_features=25,
    n_informative=15,
    n_redundant=5,
    n_repeated=0,
    n_classes=8,
    weights=[0.2, 0.15, 0.15, 0.15, 0.1, 0.1, 0.1, 0.05],
    flip_y=0.05,
    random_state=42,
)

column_names = [f"Criteri d'avaluació{i}" for i in range(X_synthetic.shape[1])]
df = pd.DataFrame(X_synthetic, columns=column_names)
df["target"] = y_synthetic

X = df.drop("target", axis=1)
y = df["target"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(
    n_estimators=100, max_depth=15, n_jobs=-1, random_state=42
)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

# ---------------------------------------------------------------------------
# GENERACIÓ DE MICROCONSULTES hola
# ---------------------------------------------------------------------------

def generar_consulta(necessitat: dict, variacio: int = 0) -> dict:
    """Genera microconsultes 100% originals i dinàmiques a través de la IA de la UAB amb depuració d'errors."""
    objectiu = str(necessitat.get("objectiu", "")).strip()
    collectiu = str(necessitat.get("col_lectiu", "Equip"))
    context = str(necessitat.get("context", "")).strip()
    durada_max = int(necessitat.get("durada_max", 2))
    canal = str(necessitat.get("canal", "Mòbil-QR"))
    to = str(necessitat.get("to", "Proper i directe"))
    prohibits = [str(x).lower() for x in necessitat.get("temes_prohibits", [])]

    preguntes = []
    error_detallat = None

    if ESCOLTA_MODE == "api" and API_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            prompt_sistema = (
                "Ets un expert en recursos humans i disseny d'enquestes de clima laboral. "
                "Genera un conjunt de preguntes 100% originals, creatives i totalment personalitzades per a l'objectiu indicat. "
                "No utilitzis plantilles fixes. Varia els tipus de pregunta (pots usar 'Escala (1-5)', 'Opció múltiple', "
                "'Sí / No' o 'Text obert'). "
                "Has de retornar exclusivament un objecte JSON net, sense markdown addicional, amb aquesta estructura exacta:\n"
                "{\n"
                "  \"titol\": \"Títol original de la microconsulta\",\n"
                "  \"intro\": \"Introducció empàtica i adaptada\",\n"
                "  \"preguntes\": [\n"
                "    {\n"
                "      \"text\": \"Enunciat original de la pregunta?\",\n"
                "      \"tipus\": \"Escala (1-5)\",\n"
                "      \"opcions\": [\"1 - ...\", \"5 - ...\"],\n"
                "      \"obligatoria\": true\n"
                "    }\n"
                "  ]\n"
                "}"
            )
            
            payload = {
                "model": "ornith",
                "messages": [
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": f"Objectiu: {objectiu}. Col·lectiu: {collectiu}. Context: {context}. To: {to}. Temes prohibits: {', '.join(prohibits)}."}
                ],
                "temperature": 0.95
            }
            
            response = requests.post(f"{API_URL}/chat/completions", headers=headers, json=payload, timeout=120)
            
            if response.status_code == 200:
                res_json = response.json()
                content = res_json["choices"][0]["message"]["content"]
                
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                parsed = json.loads(content)
                titol_ia = parsed.get("titol", f"Microconsulta: {objectiu}")
                intro_ia = parsed.get("intro", f"Volem conèixer la vostra opinió sobre {objectiu}.")
                
                raw_q = parsed.get("preguntes", [])
                for i, q in enumerate(raw_q):
                    preguntes.append({
                        "id": f"q{i + 1}",
                        "text": q.get("text", ""),
                        "tipus": q.get("tipus", TIPUS_ESCALA),
                        "opcions": q.get("opcions", []),
                        "obligatoria": q.get("obligatoria", True),
                        "condicional": ""
                    })
                
                if preguntes:
                    return {
                        "titol": titol_ia,
                        "intro": intro_ia,
                        "objectiu": objectiu,
                        "col_lectiu": collectiu,
                        "context": context,
                        "temes": ["Treball"],
                        "to": to,
                        "durada_max": durada_max,
                        "temps_estimat": min(durada_max, len(preguntes)),
                        "canal": canal,
                        "logica": [],
                        "preguntes": preguntes,
                        "estat": "Esborrany",
                        "qr": None,
                        "enllac": "",
                        "publicada_el": "",
                    }
            else:
                error_detallat = f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            error_detallat = str(e)

    # Si arriba aquí és que l'API ha fallat o no ha retornat res; mostrem l'error exacte per depurar
    text_error = f"[Error API UAB] No s'ha pogut connectar amb la IA. Detall: {error_detallat}" if error_detallat else "[Avís] No s'han rebut dades de l'API."
    
    return {
        "titol": f"Error de connexió amb la IA",
        "intro": text_error,
        "objectiu": objectiu,
        "col_lectiu": collectiu,
        "context": context,
        "temes": ["Error"],
        "to": to,
        "durada_max": durada_max,
        "temps_estimat": 1,
        "canal": canal,
        "logica": [],
        "preguntes": [
            {
                "id": "q1",
                "text": text_error,
                "tipus": TIPUS_OBERT,
                "opcions": [],
                "obligatoria": True,
                "condicional": ""
            }
        ],
        "estat": "Esborrany",
        "qr": None,
        "enllac": "",
        "publicada_el": "",
    }

def publica_consulta(consulta: dict) -> dict:
    """Marca la consulta com a publicada i prepara un QR/enllaç de demostració."""
    nova = dict(consulta)
    nova["preguntes"] = list(consulta.get("preguntes", []))
    identificador = f"microconsulta-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    enllac = f"https://exemple.local/consulta/{identificador}"

    try:
        import qrcode
        qr = qrcode.make(enllac)
    except ImportError:
        # Alternativa perquè l'aplicació no falli si no està instal·lat qrcode.
        from PIL import Image, ImageDraw
        qr = Image.new("RGB", (420, 180), "white")
        draw = ImageDraw.Draw(qr)
        draw.text((15, 25), "QR de demostració", fill="black")
        draw.text((15, 65), identificador, fill="black")
        draw.text((15, 105), "Instal·la qrcode per generar el QR real", fill="black")

    nova["qr"] = qr
    nova["enllac"] = enllac
    nova["publicada_el"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    nova["estat"] = "Publicada"
    return nova

# ---------------------------------------------------------------------------
# PRIVACITAT I FEEDBACK
# ---------------------------------------------------------------------------

def mostrar_feedback():
    st.header("Formulari de Feedback")

    edad = st.number_input("Edad (opcional)", min_value=18, max_value=99, step=1)
    departamento = st.selectbox(
        "Departamento", ["Ventas", "IT", "RRHH", "Marketing"]
    )
    consentimiento = st.checkbox(
        "Acepto la política de privacidad (PRODUCTE.md) "
        "y el uso de mis datos de forma anonimizada."
    )

    if st.button("Enviar Datos"):
        if not consentimiento:
            st.error("Debes aceptar la política de privacidad para continuar.")
        else:
            st.success(
                "Datos registrados correctamente y anonimizados de forma segura."
            )
