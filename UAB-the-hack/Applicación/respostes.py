"""
Respostes reals del formulari (QR / enllaç) — emmagatzematge local en CSV.

Privacitat per disseny:
  - Només es desen els camps necessaris per a l'anàlisi (minimització).
  - El text lliure passa per `redacta_pii` ABANS de desar-se: el text original mai toca el disc.
  - L'identificador és aleatori; no es desa IP, user-agent ni cap dada de la persona.
  - Les respostes caduquen: es descarten les anteriors a DIES_MAX dies (caducitat).
Les respostes de prova són sintètiques (les introdueix l'equip).
"""

from __future__ import annotations

import csv
import os
import threading
import uuid
from datetime import date, timedelta

import pandas as pd

import datos

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "respostes_reals.csv")
DIES_MAX = 90
PERIODE_ACTUAL = "2026-T4"

ESCALES = ["escala_benestar", "escala_càrrega", "escala_comunicació", "escala_reconeixement"]
COLS = [
    "id_resposta", "data", "període", "col·lectiu", "centre_tipus", "canal",
    *ESCALES, "comentari_obert", "pii_eliminada",
]
_LOCK = threading.Lock()


def desa_resposta(consulta: dict, respostes: dict, col: str | None, canal: str | None) -> None:
    """Desa una resposta anònima. `respostes` és {id_pregunta: valor}."""
    col = col if col in datos.COL_LECTIUS else "General"
    canal = canal if canal in datos.CANALS else "Mòbil-QR"
    pregs = consulta.get("preguntes", [])

    escales = [
        str(respostes.get(q["id"], "")).strip()
        for q in pregs
        if q.get("tipus") == "Escala (1-5)"
    ]
    escales = [e for e in escales if e.isdigit()]
    obert = " ".join(
        str(respostes.get(q["id"], "")).strip()
        for q in pregs
        if q.get("tipus") == "Text obert" and str(respostes.get(q["id"], "")).strip()
    )
    net, detectats = datos.redacta_pii(obert)  # PII fora ABANS de desar

    fila = {
        "id_resposta": f"live_{uuid.uuid4().hex[:8]}",
        "data": date.today().isoformat(),
        "període": PERIODE_ACTUAL,
        "col·lectiu": col,
        "centre_tipus": datos.CENTRES.get(col, "Tots"),
        "canal": canal,
        "comentari_obert": net,
        "pii_eliminada": ", ".join(detectats),
    }
    for nom, valor in zip(ESCALES, escales + [""] * len(ESCALES)):
        fila[nom] = valor

    with _LOCK:
        nou = not os.path.exists(RUTA)
        with open(RUTA, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLS)
            if nou:
                w.writeheader()
            w.writerow(fila)


def carrega_reals(dies_max: int = DIES_MAX) -> pd.DataFrame:
    """Llegeix les respostes desades i les deixa amb el mateix esquema que el dataset sintètic."""
    if not os.path.exists(RUTA):
        return pd.DataFrame()
    try:
        df = pd.read_csv(RUTA, keep_default_na=False)
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df
    limit = pd.Timestamp(date.today() - timedelta(days=dies_max))
    df = df[pd.to_datetime(df["data"], errors="coerce") >= limit].copy()  # caducitat
    if df.empty:
        return df
    for c in ESCALES:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["comentari_obert"] = df["comentari_obert"].astype(str)
    df["comentari_net"] = df["comentari_obert"]
    df["tema_detectat"] = df["comentari_obert"].map(datos.classifica_tema)
    df["sentiment_detectat"] = df["comentari_obert"].map(datos.sentiment_de)
    df["tema_real"] = None        # no hi ha etiqueta oculta a les respostes en directe
    df["sentiment_real"] = None
    df["pii_eliminada"] = df["pii_eliminada"].astype(str)
    return df.reset_index(drop=True)