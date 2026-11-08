"""
Capa d'IA sobre l'anàlisi (Insights i accions).

L'anàlisi NO es toca: continua sent `analisis.py` (determinista i explicable).
Aquest mòdul només agafa els resultats que ja calcula l'app, els envia
agregats a la IA de la UAB (la mateixa passarel·la que fa servir
`Encuesta.generar_consulta`) i en retorna:

  1. un text breu que explica què diuen les dades,
  2. les solucions detallades (accions, passos, responsable, indicador),
  3. el pla 30/60/90 dies i la proposta de microconsulta de seguiment.

Privacitat: a la IA només hi arriben xifres agregades per tema i col·lectiu.
Mai comentaris individuals, ni cites, ni cap dada identificativa.
"""

from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests
from dotenv import load_dotenv

import analisis

# Mateixa càrrega de .env que a Encuesta.py
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

ESCOLTA_MODE = os.getenv("ESCOLTA_MODE", "mock").strip()
API_URL = os.getenv("ESCOLTA_API_URL", "").strip()
API_KEY = os.getenv("ESCOLTA_API_KEY", "").strip()
MODEL = "ornith"  # mateix model que a Encuesta.py


# ---------------------------------------------------------------------------
# 1. Context: el que ja ha calculat l'anàlisi, en format compacte
# ---------------------------------------------------------------------------


def _registres(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []
    return json.loads(df.to_json(orient="records", force_ascii=False))


def construeix_context(df: pd.DataFrame, llindar_pct: float) -> dict:
    """Recull les sortides d'`analisis.py` (sense modificar-les) per passar-les a la IA."""
    taula = analisis.taula_participacio(df, llindar_pct)
    resum = analisis.resum_temes(df)
    evolucio = analisis.evolucio_temes(df)
    emergents = analisis.temes_emergents(evolucio)
    febles = analisis.senyals_febles(df, evolucio)
    precisio = analisis.precisio_classificacio(df)
    indicadors = analisis.kpis(df, llindar_pct)

    # Només els col·lectius amb dades visibles (els ocults per privacitat no surten).
    taula_visible = taula[taula["Estat"] != "Ocult (llindar)"]

    return {
        "indicadors_globals": indicadors,
        "participacio_per_collectiu": _registres(taula_visible),
        "alertes_representativitat": analisis.alertes_representativitat(taula),
        "temes_principals": _registres(resum),
        "evolucio_temes_T3_a_T4": _registres(evolucio),
        "temes_emergents": _registres(emergents),
        "senyals_febles": _registres(febles),
        "qualitat_classificacio": precisio,
    }


def _empremta(context: dict) -> str:
    brut = json.dumps(context, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(brut.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# 2. Crida a la IA
# ---------------------------------------------------------------------------

REGLES = """Ets un analista expert en clima laboral i recursos humans que assessora l'equip de People d'Estrella Damm.
Rebràs els resultats ja calculats d'una anàlisi de microconsultes (participació per col·lectiu, temes, sentiment, evolució entre períodes, temes emergents i senyals febles). Totes les dades són agregades i sintètiques.

Regles:
- Escriu en català i sigues concís.
- Basa't NOMÉS en les dades rebudes. No t'inventis xifres ni temes.
- No afirmis causalitat: les dades mostren associacions, no causes.
- Si algun col·lectiu està infrarepresentat, inclou una acció per millorar la seva participació (no per decidir sobre els seus resultats).
- No proposis res sobre salaris, acomiadaments ni dades mèdiques individuals.
- No facis inferències sobre persones concretes.
- Tot són propostes: les validen i decideixen les persones de People.
- Retorna EXCLUSIVAMENT un objecte JSON net, sense markdown ni text addicional."""

PROMPT_RESUM = REGLES + """

Retorna aquest JSON:
{
  "resum": "text BREU (3 a 5 frases, un sol paràgraf) que expliqui en llenguatge planer què diuen les dades: participació i representativitat, temes que pesen més i amb quin sentiment, què creix o baixa i quin senyal feble cal vigilar. Cita xifres concretes.",
  "seguiment": {
    "titol": "títol de la propera microconsulta",
    "motiu": "per què es proposa, amb una dada",
    "preguntes": ["pregunta 1", "pregunta 2"]
  }
}"""

PROMPT_SOLUCIONS = REGLES + """

Proposa entre 3 i 4 solucions CONCRETES i accionables (no frases genèriques), ordenades per prioritat, cadascuna lligada explícitament a una dada de l'anàlisi. Retorna aquest JSON:
{
  "solucions": [
    {
      "prioritat": 1,
      "tema": "tema o col·lectiu al qual respon",
      "titol": "títol curt",
      "diagnostic": "què diuen les dades que ho justifica (amb xifres), 1 frase",
      "descripcio": "explicació de la solució, 2 a 4 frases",
      "passos": ["pas concret 1", "pas concret 2", "pas concret 3"],
      "responsable": "àrea o rol",
      "impacte": "Alt | Mitjà | Baix",
      "esforc": "Alt | Mitjà | Baix",
      "indicador": "com sabrem si ha funcionat"
    }
  ],
  "pla": [
    {"horitzo": "0-30 dies", "accio": "...", "responsable": "...", "indicador": "..."},
    {"horitzo": "30-60 dies", "accio": "...", "responsable": "...", "indicador": "..."},
    {"horitzo": "60-90 dies", "accio": "...", "responsable": "...", "indicador": "..."}
  ]
}"""

# La pasarela pot tardar: marge ampli per crida (les dues van en paral·lel).
TIMEOUT_S = 240


def _extreu_json(contingut: str) -> dict:
    """Neteja possibles blocs markdown o text addicional al voltant del JSON."""
    text = contingut.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    ini, fi = text.find("{"), text.rfind("}")
    if ini != -1 and fi > ini:
        text = text[ini : fi + 1]
    return json.loads(text)


def _normalitza(parsed: dict) -> dict:
    """Garanteix que l'estructura té tot el que la interfície necessita (admet parts buides)."""
    solucions = []
    for i, s in enumerate(parsed.get("solucions", []) or []):
        if not isinstance(s, dict):
            continue
        passos = s.get("passos", [])
        if isinstance(passos, str):
            passos = [passos]
        solucions.append(
            {
                "prioritat": s.get("prioritat", i + 1),
                "tema": str(s.get("tema", "")),
                "titol": str(s.get("titol", f"Solució {i + 1}")),
                "diagnostic": str(s.get("diagnostic", "")),
                "descripcio": str(s.get("descripcio", "")),
                "passos": [str(p) for p in passos],
                "responsable": str(s.get("responsable", "People")),
                "impacte": str(s.get("impacte", "Mitjà")),
                "esforc": str(s.get("esforc", "Mitjà")),
                "indicador": str(s.get("indicador", "")),
            }
        )
    seg = parsed.get("seguiment")
    seg = seg if isinstance(seg, dict) else {}
    pregs = seg.get("preguntes", []) or []
    return {
        "resum": str(parsed.get("resum", "") or "").strip(),
        "solucions": solucions,
        "pla": [p for p in (parsed.get("pla") or []) if isinstance(p, dict)],
        "seguiment": {
            "titol": str(seg.get("titol", "Microconsulta de seguiment")),
            "motiu": str(seg.get("motiu", "")),
            "preguntes": [str(p) for p in pregs],
        },
    }


def _crida(prompt_sistema: str, context: dict) -> tuple[dict | None, str | None]:
    """Una crida a la IA. Retorna (JSON, error). Reintenta un cop en errors temporals (429/5xx)."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": prompt_sistema},
            {
                "role": "user",
                "content": "Resultats de l'anàlisi (JSON agregat):\n" + json.dumps(context, ensure_ascii=False),
            },
        ],
        "temperature": 0.4,
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    ultim_error = None
    for _ in range(2):
        try:
            resp = requests.post(f"{API_URL}/chat/completions", headers=headers, json=payload, timeout=TIMEOUT_S)
            if resp.status_code == 200:
                return _extreu_json(resp.json()["choices"][0]["message"]["content"]), None
            ultim_error = f"HTTP {resp.status_code}: {resp.text[:300]}"
            if resp.status_code != 429 and resp.status_code < 500:
                break
        except requests.exceptions.Timeout:
            return None, f"La IA ha trigat més de {TIMEOUT_S} s a respondre."
        except Exception as e:  # xarxa, JSON mal format, etc.
            return None, str(e)
    return None, ultim_error


def genera_informe(context: dict) -> tuple[dict | None, str | None]:
    """
    Fa dues crides en paral·lel (resum+seguiment i solucions+pla) perquè cadascuna sigui curta.
    Si una falla, es retorna l'altra part i la resta queda buida (la interfície usa l'anàlisi base).
    Retorna (informe, error). Només és None si fallen totes dues.
    """
    if ESCOLTA_MODE != "api" or not API_KEY or not API_URL:
        return None, "La IA no està configurada (cal ESCOLTA_MODE=api, ESCOLTA_API_URL i ESCOLTA_API_KEY al .env)."

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_resum = pool.submit(_crida, PROMPT_RESUM, context)
        f_sol = pool.submit(_crida, PROMPT_SOLUCIONS, context)
        (j_resum, e_resum), (j_sol, e_sol) = f_resum.result(), f_sol.result()

    if j_resum is None and j_sol is None:
        return None, e_resum or e_sol or "Error desconegut"

    informe = _normalitza({**(j_resum or {}), **(j_sol or {})})
    avisos = []
    if j_resum is None:
        avisos.append(f"Resum no disponible ({e_resum})")
    if j_sol is None:
        avisos.append(f"Solucions no disponibles ({e_sol})")
    if j_resum is not None and not informe["resum"]:
        avisos.append("La IA no ha retornat el resum")
    if j_sol is not None and not informe["solucions"]:
        avisos.append("La IA no ha retornat solucions")
    informe["avisos"] = avisos
    return informe, None


def informe_amb_cache(estat, df: pd.DataFrame, llindar_pct: float, forca: bool = False):
    """
    Evita tornar a cridar la IA a cada interacció de Streamlit.
    `estat` és st.session_state. Només es torna a generar si canvien les dades
    de l'anàlisi o si es demana explícitament (botó «Regenerar»).
    """
    context = construeix_context(df, llindar_pct)
    clau = _empremta(context)
    cache = estat.get("informe_ia")
    if not forca and cache and cache.get("clau") == clau:
        return cache["informe"], cache["error"]

    informe, error = genera_informe(context)
    estat["informe_ia"] = {"clau": clau, "informe": informe, "error": error}
    return informe, error