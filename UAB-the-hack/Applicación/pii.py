"""
Eliminació de dades identificatives (PII) als comentaris oberts.

Capes (de més barata/segura a més flexible):
  1. Patrons: correus, telèfons, usuaris (@), URLs, DNI/NIE, IBAN.
  2. Noms amb pista: «sóc Pere», «soy Iker», «me llamo Laura García», «my name is Anna»...
  3. Diccionari de noms propis (Faker es_ES/es_CA/en_US + extres en català).
  4. (Opcional) IA: només DETECTA noms que les capes anteriors no han vist.
     La IA mai reescriu el text: retorna una llista de cadenes i el codi les
     substitueix després d'haver comprovat que existeixen al text.

Privacitat:
  - La capa 4 rep el text JA netejat per les capes 1-3 (correus i telèfons no surten).
  - Si la IA falla o no està configurada, es retorna el resultat de les capes 1-3.
  - Usa la MATEIXA IA que Encuesta.py i ia.py (ESCOLTA_MODE/ESCOLTA_API_URL/ESCOLTA_API_KEY, model «ornith»).
  - En producció, apunta ESCOLTA_API_URL a un model local (p. ex. Ollama:
    http://localhost:11434/v1) perquè el text original no surti de la màquina.

Ús (substitueix datos.redacta_pii a respostes.py):
    from pii import redacta_pii
    net, detectats = redacta_pii(text, usa_ia=True)
"""

from __future__ import annotations

import json
import os
import re
from typing import Callable

from dotenv import load_dotenv

# Mateixa càrrega de .env que a Encuesta.py i ia.py
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# Mateixa passarel·la i mateix model que la generació de consultes (Encuesta.py) i ia.py
MODEL = "ornith"

# ---------------------------------------------------------------------------
# 1. Patrons
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?:\+34[\s.-]?)?[6-9](?:[\s.-]?\d){8}")
HANDLE_RE = re.compile(r"(?<![\w.])@[A-Za-z0-9_]{2,}")
URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
DNI_RE = re.compile(r"\b(?:\d{8}|[XYZxyz]\d{7})[\s-]?[A-Za-z]\b")
IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}(?:[\s-]?\d{4}){4,6}\b", re.IGNORECASE)

PATRONS = [
    (EMAIL_RE, "correu"),
    (URL_RE, "enllaç"),
    (IBAN_RE, "iban"),
    (DNI_RE, "document"),
    (PHONE_RE, "telèfon"),
    (HANDLE_RE, "usuari"),
]

# ---------------------------------------------------------------------------
# 2. Noms amb pista (català, castellà, anglès)
# ---------------------------------------------------------------------------

_NOM = r"[A-ZÀ-ÚÑ][a-zà-úñ'·-]{1,}(?:\s+(?:de\s+|del\s+|de\s+la\s+|i\s+)?[A-ZÀ-ÚÑ][a-zà-úñ'·-]{1,}){0,2}"
_PISTES = (
    r"s[oó]c|soy|em\s+dic|me\s+llamo|me\s+llaman|em\s+diuen|"
    r"el\s+meu\s+nom\s+[eé]s|mi\s+nombre\s+es|my\s+name\s+is|i\s+am|i'm|"
    r"parlo\s+amb|hablo\s+con|ho\s+comenta|lo\s+dice|diu|dice|"
    r"amb|con|with|"
    r"el\s+meu\s+cap\s+[eé]s|mi\s+jefe\s+es|mi\s+jefa\s+es"
)
# (?i:...) fa la pista insensible a majúscules, però el nom ha de començar en majúscula.
NOM_PISTA_RE = re.compile(rf"\b(?i:{_PISTES})\s+(?i:la\s+|el\s+|l'|en\s+|na\s+|don\s+|doña\s+)?({_NOM})")

# ---------------------------------------------------------------------------
# 3. Diccionari de noms propis
# ---------------------------------------------------------------------------

_EXTRES_CA = {
    "Pere", "Jordi", "Marc", "Pau", "Jaume", "Quim", "Joan", "Narcís", "Oriol", "Arnau", "Biel",
    "Roger", "Genís", "Aleix", "Ferran", "Xavi", "Albert", "Magí", "Montserrat", "Núria", "Mercè",
    "Montse", "Roser", "Laia", "Marta", "Anna", "Berta", "Queralt", "Aina", "Ona", "Neus", "Griselda",
}

# Paraules comunes que també són noms (evitem sobre-censurar).
_NO_NOMS = {
    "Mar", "Sol", "Luz", "Pilar", "Rosa", "Paz", "Pau", "Angel", "Ángel", "Cruz", "Consuelo", "Dolores",
    "Amparo", "Esperanza", "Victoria", "Gloria", "Carmen", "Mercè", "Llum", "Estel", "Nuria", "Iris",
    "Abril", "Marina", "Salud", "Fe", "Lucas", "Max", "Rey", "Santos", "Jesus", "Jesús", "Domingo",
}


def _carrega_noms() -> frozenset[str]:
    noms: set[str] = set(_EXTRES_CA)
    try:  # Faker ja és a requirements.txt
        from faker.providers.person import en_US, es_CA, es_ES

        for prov in (es_ES, es_CA, en_US):
            p = prov.Provider
            for attr in ("first_names_male", "first_names_female", "first_names"):
                lst = getattr(p, attr, None)
                if lst:
                    noms.update(lst if not isinstance(lst, dict) else lst.keys())
    except Exception:
        pass
    return frozenset(n for n in noms if len(n) >= 3 and n not in _NO_NOMS)


NOMS = _carrega_noms()
PARAULA_RE = re.compile(r"[A-ZÀ-ÚÑ][a-zà-úñ'·-]{2,}")


# ---------------------------------------------------------------------------
# 4. Detecció amb IA (opcional, només retorna cadenes)
# ---------------------------------------------------------------------------

PROMPT_NOMS = (
    "Ets un detector de dades personals. Del text següent, extreu NOMÉS els noms i cognoms de "
    "persones (empleats, caps, companys), tal com apareixen escrits. No incloguis empreses, "
    "llocs, càrrecs ni marcadors com [nom eliminat]. Retorna EXCLUSIVAMENT un JSON amb aquesta "
    'forma: {"noms": ["...", "..."]}. Si no n\'hi ha, retorna {"noms": []}. No reescriguis el text.'
)


def _llista_noms_ia(text: str) -> list[str]:
    """Crida la passarel·la d'IA. Qualsevol error → llista buida (fallback segur a les capes 1-3)."""
    mode = os.getenv("ESCOLTA_MODE", "mock").strip()
    url = os.getenv("ESCOLTA_API_URL", "").strip()
    key = os.getenv("ESCOLTA_API_KEY", "").strip()
    if mode != "api" or not url or not key:
        return []
    try:
        import requests

        resp = requests.post(
            f"{url}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": MODEL,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": PROMPT_NOMS},
                    {"role": "user", "content": text},
                ],
            },
            timeout=int(os.getenv("PII_TIMEOUT_S", "10")),
        )
        if resp.status_code != 200:
            return []
        contingut = resp.json()["choices"][0]["message"]["content"]
        ini, fi = contingut.find("{"), contingut.rfind("}")
        dades = json.loads(contingut[ini : fi + 1])
        return [str(n) for n in dades.get("noms", []) if isinstance(n, str)]
    except Exception:
        return []


def _aplica_noms_ia(text: str, detector: Callable[[str], list[str]]) -> tuple[str, bool]:
    """Substitueix només les cadenes que la IA retorna I que existeixen literalment al text."""
    canvi = False
    for nom in sorted(set(detector(text)), key=len, reverse=True):  # primer els més llargs
        nom = nom.strip()
        if not (2 <= len(nom) <= 40) or "[" in nom or "]" in nom:
            continue
        patro = re.compile(rf"(?<!\w){re.escape(nom)}(?!\w)")
        if patro.search(text):
            text = patro.sub("[nom eliminat]", text)
            canvi = True
    return text, canvi


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------


def redacta_pii(
    text: str,
    usa_ia: bool = False,
    detector_ia: Callable[[str], list[str]] | None = None,
) -> tuple[str, list[str]]:
    """Retorna (text net, tipus detectats). Mateixa signatura que datos.redacta_pii + usa_ia."""
    if not text or not str(text).strip():
        return "", []
    net = str(text)
    detectats: set[str] = set()

    # 1. Patrons
    for patro, etiqueta in PATRONS:
        nou = patro.sub(f"[{etiqueta} eliminat]", net)
        if nou != net:
            detectats.add(etiqueta)
            net = nou

    # 2. Noms amb pista (conservem la pista, substituïm el nom)
    nou = NOM_PISTA_RE.sub(lambda m: m.group(0)[: m.start(1) - m.start(0)] + "[nom eliminat]", net)
    if nou != net:
        detectats.add("nom")
        net = nou

    # 3. Diccionari de noms propis
    def _sub_nom(m: re.Match) -> str:
        return "[nom eliminat]" if m.group(0) in NOMS else m.group(0)

    nou = PARAULA_RE.sub(_sub_nom, net)
    if nou != net:
        detectats.add("nom")
        net = nou

    # 4. IA (rep el text ja net de correus/telèfons)
    if usa_ia:
        net, canvi = _aplica_noms_ia(net, detector_ia or _llista_noms_ia)
        if canvi:
            detectats.add("nom")

    # Cap resta de marcadors duplicats consecutius («[nom eliminat] [nom eliminat]»)
    net = re.sub(r"(\[nom eliminat\])(?:\s+\[nom eliminat\])+", r"\1", net)
    return net, sorted(detectats)