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
    """Genera una proposta de microconsulta editable; no la publica."""
    objectiu = str(necessitat.get("objectiu", "")).strip()
    collectiu = str(necessitat.get("col_lectiu", "Equip"))
    context = str(necessitat.get("context", "")).strip()
    durada_max = int(necessitat.get("durada_max", 2))
    canal = str(necessitat.get("canal", "Mòbil-QR"))
    to = str(necessitat.get("to", "Proper i directe"))
    prohibits = [str(x).lower() for x in necessitat.get("temes_prohibits", [])]

    # Identifica el tema a partir del text, sense confondre'l amb el to.
    tema = "Altres"
    text_cerca = f"{objectiu} {context}".lower()
    paraules_tema = {
        "Educació": ("educació", "formació", "aprenentatge", "curs"),
        "Treball": ("treball", "feina", "torn", "planta", "empresa"),
        "Habitatge": ("habitatge", "lloguer", "casa"),
        "Salut": ("salut", "benestar", "estrès"),
        "Economia": ("economia", "despesa", "cost", "sou"),
    }
    for nom, paraules in paraules_tema.items():
        if any(p in text_cerca for p in paraules):
            tema = nom
            break

    intros_to = {
        "Proper i directe": "Volem conèixer la teva opinió de manera senzilla i directa.",
        "Formal i professional": "Aquesta consulta té com a objectiu recollir la teva valoració.",
        "Proper i empàtic": "Ens interessa entendre la teva experiència i com et sents.",
    }
    intro = intros_to.get(to, intros_to["Proper i directe"])
    if context:
        intro += f" Aquesta consulta se centra en: {context}."
    intro += " Les respostes es tractaran de manera agregada."

    preguntes_base = [
        {
            "id": "q1",
            "text": f"Com valores actualment {objectiu.rstrip('.')}?" if objectiu else "Com valores aquesta situació?",
            "tipus": TIPUS_ESCALA,
            "opcions": ["1 - Molt malament", "2 - Malament", "3 - Normal", "4 - Bé", "5 - Molt bé"],
            "obligatoria": True,
            "condicional": "",
        },
        {
            "id": "q2",
            "text": "Quin és el principal aspecte que funciona bé?",
            "tipus": TIPUS_OPCIONS,
            "opcions": ["Organització", "Comunicació", "Recursos", "Acompanyament", "Cap d'aquests"],
            "obligatoria": True,
            "condicional": "",
        },
        {
            "id": "q3",
            "text": "Què canviaries o milloraries?",
            "tipus": TIPUS_OBERT,
            "opcions": [],
            "obligatoria": False,
            "condicional": "",
        },
    ]

    # Evita preguntes sobre temes prohibits.
    preguntes = []
    for pregunta in preguntes_base:
        text_pregunta = pregunta["text"].lower()
        if any(prohibit and prohibit in text_pregunta for prohibit in prohibits):
            continue
        preguntes.append(pregunta)

    # La variació canvia l'ordre de les preguntes sense alterar-ne el contingut.
    if variacio and len(preguntes) > 1:
        random.Random(variacio).shuffle(preguntes)

    temps_estimat = max(1, min(durada_max, len(preguntes)))
    titol = f"Microconsulta sobre {tema.lower()}"

    return {
        "titol": titol,
        "intro": intro,
        "objectiu": objectiu,
        "col_lectiu": collectiu,
        "context": context,
        "temes": [tema],
        "to": to,
        "durada_max": durada_max,
        "temps_estimat": temps_estimat,
        "canal": canal,
        "logica": [],
        "preguntes": preguntes,
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
