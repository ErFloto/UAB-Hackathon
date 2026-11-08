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
import json
import os
import threading
import uuid
from datetime import date, timedelta
import pii

import pandas as pd

import datos

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "respostes_reals.csv")
DIES_MAX = 90
PERIODE_ACTUAL = "2026-T4"

ESCALES = ["escala_benestar", "escala_càrrega", "escala_comunicació", "escala_reconeixement"]
COLS = [
    "id_resposta", "data", "període", "col·lectiu", "centre_tipus", "canal",
    *ESCALES, "comentari_obert", "pii_eliminada", "tancades",
]

# Si una pregunta d'escala no declara dimensió (consulta antiga o editada a mà), la deduïm del text.
_PISTES = {
    "càrrega": ("càrrega", "carrega", "pressió", "estrès", "estres", "ritme", "volum de feina"),
    "comunicació": ("comunic", "informa", "coordinaci", "feedback"),
    "reconeixement": ("reconeix", "agraï", "agrai", "t'apreci", "et valoren"),
}


def _dimensio(q: dict) -> str:
    d = q.get("dimensio")
    if d in ("benestar", "càrrega", "comunicació", "reconeixement"):
        return d
    text = str(q.get("text", "")).lower()
    for dim, pistes in _PISTES.items():
        if any(p in text for p in pistes):
            return dim
    return "benestar"

_LOCK = threading.Lock()


def desa_resposta(consulta: dict, respostes: dict, col: str | None, canal: str | None) -> None:
    """Desa una resposta anònima. `respostes` és {id_pregunta: valor}."""
    col = col if col in datos.COL_LECTIUS else "General"
    canal = canal if canal in datos.CANALS else "Mòbil-QR"
    pregs = consulta.get("preguntes", [])

    # Cada escala va a la columna de la seva dimensió (no per ordre d'aparició).
    escales: dict[str, str] = {}
    tancades: dict[str, str] = {}
    for q in pregs:
        v = str(respostes.get(q["id"], "") or "").strip()
        if not v:
            continue
        if q.get("tipus") == "Escala (1-5)":
            col_esc = f"escala_{_dimensio(q)}"
            if v.isdigit() and 1 <= int(v) <= 5 and col_esc not in escales:
                escales[col_esc] = v
        elif q.get("tipus") in ("Sí / No", "Opció múltiple"):
            tancades[q["id"]] = v   # clau = id de pregunta; el text queda a consulta_activa.json
    obert = " ".join(
        str(respostes.get(q["id"], "")).strip()
        for q in pregs
        if q.get("tipus") == "Text obert" and str(respostes.get(q["id"], "")).strip()
    )
    net, detectats = pii.redacta_pii(obert, usa_ia=True)   # antes: datos.redacta_pii(obert)
    
    fila = {
        "id_resposta": f"live_{uuid.uuid4().hex[:8]}",
        "data": date.today().isoformat(),
        "període": PERIODE_ACTUAL,
        "col·lectiu": col,
        "centre_tipus": datos.CENTRES.get(col, "Tots"),
        "canal": canal,
        "comentari_obert": net,
        "pii_eliminada": ", ".join(detectats),
        "tancades": json.dumps(tancades, ensure_ascii=False),
    }
    for nom in ESCALES:
        fila[nom] = escales.get(nom, "")

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