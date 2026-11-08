"""
Dades sintètiques per a la demo d'Escolta Damm.

Genera un conjunt de respostes 100% sintètiques (cap dada real) amb:
- participació desigual per col·lectiu,
- dos períodes per poder comparar tendències,
- biaixos intencionats (torns i descansos emergeixen al segon període),
- comentaris oberts amb soroll, faltes i alguna dada identificativa falsa
  per demostrar la redacció automàtica de PII.

Tot el mòdul és determinista per a un `seed` donat, de manera que la demo
sempre mostra el mateix resultat.
"""

from __future__ import annotations

import random
import re
import unicodedata
from datetime import date, timedelta

import pandas as pd
import hashlib
import os

# ---------------------------------------------------------------------------
# Constants de domini
# ---------------------------------------------------------------------------

COL_LECTIUS = ["General", "Planta", "Logística", "Comercial", "Oficina", "Manager"]

# Població de referència (fictícia, només per calcular representativitat).
POBLACIO = {
    "Planta": 1400,
    "Logística": 800,
    "Comercial": 500,
    "Oficina": 700,
    "Manager": 200,
    "General": 3000,
}

CENTRES = {
    "Planta": "Fàbrica",
    "Logística": "Magatzem",
    "Comercial": "Oficina",
    "Oficina": "Oficina",
    "Manager": "Oficina",
    "General": "Tots"
}

CANALS = ["Mòbil-QR", "Correu", "Teams"]

PERIODES = ["2026-T3", "2026-T4"]

PERIODE_DATA = {
    "2026-T3": (date(2026, 9, 8), date(2026, 9, 30)),
    "2026-T4": (date(2026, 10, 1), date(2026, 10, 26)),
}

TEMES = [
    "Torns i horaris",
    "Descansos i pauses",
    "Càrrega de treball",
    "Comunicació",
    "Lideratge",
    "Reconeixement",
    "Conciliació",
    "Formació i desenvolupament",
    "Eines i processos",
    "Salut i seguretat",
    "Ambient i relacions",
    "Organització i recursos",
]

TEMES_ORDRE = {t: i for i, t in enumerate(TEMES)}

# Pes de cada tema per col·lectiu (es normalitza després).
PESOS_TEMA = {
    "Planta": {
        "Torns i horaris": 21,
        "Descansos i pauses": 12,
        "Càrrega de treball": 14,
        "Comunicació": 10,
        "Lideratge": 6,
        "Reconeixement": 7,
        "Conciliació": 5,
        "Formació i desenvolupament": 4,
        "Eines i processos": 9,
        "Salut i seguretat": 6,
        "Ambient i relacions": 4,
        "Organització i recursos": 2,
    },
    "Logística": {
        "Torns i horaris": 19,
        "Descansos i pauses": 10,
        "Càrrega de treball": 16,
        "Comunicació": 11,
        "Lideratge": 6,
        "Reconeixement": 6,
        "Conciliació": 5,
        "Formació i desenvolupament": 4,
        "Eines i processos": 10,
        "Salut i seguretat": 6,
        "Ambient i relacions": 5,
        "Organització i recursos": 2,
    },
    "Comercial": {
        "Torns i horaris": 7,
        "Descansos i pauses": 5,
        "Càrrega de treball": 17,
        "Comunicació": 13,
        "Lideratge": 9,
        "Reconeixement": 9,
        "Conciliació": 11,
        "Formació i desenvolupament": 7,
        "Eines i processos": 10,
        "Salut i seguretat": 3,
        "Ambient i relacions": 5,
        "Organització i recursos": 4,
    },
    "Oficina": {
        "Torns i horaris": 3,
        "Descansos i pauses": 3,
        "Càrrega de treball": 12,
        "Comunicació": 14,
        "Lideratge": 14,
        "Reconeixement": 10,
        "Conciliació": 12,
        "Formació i desenvolupament": 9,
        "Eines i processos": 9,
        "Salut i seguretat": 2,
        "Ambient i relacions": 6,
        "Organització i recursos": 6,
    },
    "Manager": {
        "Torns i horaris": 7,
        "Descansos i pauses": 3,
        "Càrrega de treball": 12,
        "Comunicació": 13,
        "Lideratge": 16,
        "Reconeixement": 8,
        "Conciliació": 10,
        "Formació i desenvolupament": 9,
        "Eines i processos": 7,
        "Salut i seguretat": 2,
        "Ambient i relacions": 6,
        "Organització i recursos": 7,
    },
        "General": {
        "Torns i horaris": 21,
        "Descansos i pauses": 3,
        "Càrrega de treball": 10,
        "Comunicació": 13,
        "Lideratge": 19,
        "Reconeixement": 8,
        "Conciliació": 10,
        "Formació i desenvolupament": 13,
        "Eines i processos": 7,
        "Salut i seguretat": 9,
        "Ambient i relacions": 6,
        "Organització i recursos": 3,
    },
}

SENTIMENT_BASE = {
    "Torns i horaris": -0.35,
    "Descansos i pauses": -0.40,
    "Càrrega de treball": -0.30,
    "Comunicació": -0.25,
    "Lideratge": -0.20,
    "Reconeixement": -0.35,
    "Conciliació": -0.20,
    "Formació i desenvolupament": 0.00,
    "Eines i processos": -0.25,
    "Salut i seguretat": -0.15,
    "Ambient i relacions": 0.05,
    "Organització i recursos": -0.20,
}

AJUST_COL_LECTIU = {
    "Planta": -0.10,
    "Logística": -0.14,
    "Comercial": 0.05,
    "Oficina": 0.10,
    "Manager": 0.08,
    "General": 0.08,
}

# ---------------------------------------------------------------------------
# Banc de comentaris (català, amb soroll i faltes controlades)
# ---------------------------------------------------------------------------

COMENTARIS = {
    "Torns i horaris": {
        -1: [
            "Els canvis de torn amb pocs dies d'antelació fan molt difícil organitzar-se.",
            "La rotació actual no respecta el descans entre torns.",
            "Porto tres setmanes encadenant tancaments i obertures.",
            "El calendari de torns arriba tard i després no es pot canviar.",
            "Treballar de nit sense previsió desgasta molt i no es compensa.",
            "Cada setmana canvio de torn i no acabo d'adaptar-me mai.",
        ],
        0: [
            "Els torns funcionen, però depèn molt de l'equip on caiguis.",
            "L'horari és correcte, tot i que els canvis puntuals costen.",
            "No tinc queixes greus, però la planificació podria ser més estable.",
        ],
        1: [
            "Aquest trimestre els torns han estat més estables i ho he notat.",
            "La planificació de torns ha millorat respecte de l'any passat.",
            "He pogut canviar un torn sense problemes quan ho he necessitat.",
        ],
    },
    "Descansos i pauses": {
        -1: [
            "Les pauses són massa curtes per dinar amb calma.",
            "Quan hi ha pic de feina no podem fer la pausa que toca.",
            "Moltes vegades menjo dempeus perquè no hi ha relleu.",
            "El descans de quinze minuts no sempre es respecta al torn de nit.",
            "Acabo el dia sense haver pogut desconnectar ni cinc minuts.",
        ],
        0: [
            "Les pauses estan bé, però depèn del volum de feina del dia.",
            "El descans és correcte, tot i que a vegades es fa curt.",
        ],
        1: [
            "Hem pogut fer pauses reals aquest mes i es nota en l'ambient.",
            "El nou protocol de pauses al magatzem ha ajudat molt.",
        ],
    },
    "Càrrega de treball": {
        -1: [
            "La càrrega és assumible, però els pics coincideixen amb baixes i vaig just.",
            "Vaig acumulant tasques perquè no hi ha prou mans.",
            "Faig feina de dues persones i no arribo a tot.",
            "El volum ha pujat i els terminis no s'han mogut.",
            "Sovint em quedo més estona per acabar el que toca.",
        ],
        0: [
            "El volum és exigent, però dins del que és normal en campanya.",
            "Hi ha dies de molta feina i dies més tranquils.",
        ],
        1: [
            "El volum s'ha repartit millor i acabo menys esgotat.",
            "Aquest mes hem tingut reforç i s'ha notat molt.",
        ],
    },
    "Comunicació": {
        -1: [
            "M'assabento dels canvis quan ja estan decidits.",
            "Falten canals clars per explicar per què es fan les coses.",
            "La informació arriba tard i per camins diferents.",
            "No hi ha transparència sobre els criteris de les decisions.",
            "A la planta no arriba la meitat del que es diu a oficines.",
        ],
        0: [
            "La comunicació és correcta, però es podria resumir millor.",
            "Rebem informació, tot i que sovint és massa genèrica.",
        ],
        1: [
            "Les reunions d'equip són més clares i amb menys soroll.",
            "Aquest trimestre han explicat abans els canvis i ho agraeixo.",
        ],
    },
    "Lideratge": {
        -1: [
            "El meu responsable no dona feedback si no el vas a buscar.",
            "Hi ha molt micromanagement i poca autonomia.",
            "Quan hi ha un problema, la resposta és pressionar més.",
            "Els caps de torn no sempre coneixen la feina real.",
        ],
        0: [
            "Tinc un responsable correcte, però el feedback és escàs.",
            "La relació amb el cap és bona, tot i que falta més acompanyament.",
        ],
        1: [
            "Tinc un responsable que escolta i dona espai per provar coses.",
            "El feedback mensual amb el meu cap m'ajuda molt.",
        ],
    },
    "Reconeixement": {
        -1: [
            "La feina ben feta no es reconeix mai.",
            "Els reconeixements sempre van als mateixos.",
            "Quan fas un extra ni tan sols et donen les gràcies.",
            "No hi ha cap incentiu clar per esforçar-se més.",
        ],
        0: [
            "De tant en tant es valora la feina, però no és habitual.",
            "El reconeixement existeix, tot i que és molt informal.",
        ],
        1: [
            "Aquest trimestre sí que s'ha valorat l'esforç de l'equip.",
            "Un petit reconeixement públic ha pujat la moral del grup.",
        ],
    },
    "Conciliació": {
        -1: [
            "La flexibilitat existeix sobre el paper, però depèn del cap.",
            "Les hores de tancament fan impossible la conciliació.",
            "Els canvis d'última hora trenquen qualsevol pla familiar.",
            "Sempre he de triar entre arribar a l'hora o acabar la feina.",
        ],
        0: [
            "La conciliació és acceptable, tot i que depèn de l'època.",
            "Tinc flexibilitat, però no sempre puc fer-la servir.",
        ],
        1: [
            "El teletreball m'ha ajudat molt a conciliar.",
            "Poder ajustar l'entrada i la sortida m'ha canviat el dia a dia.",
        ],
    },
    "Formació i desenvolupament": {
        -1: [
            "La formació és genèrica i no serveix per al meu dia a dia.",
            "No tinc temps per fer els cursos obligatoris.",
            "No veig un pla clar per créixer dins de l'empresa.",
            "Els cursos són els mateixos de fa tres anys.",
        ],
        0: [
            "La formació està bé, però hauria de ser més pràctica.",
            "Hi ha oportunitats, tot i que no sempre se n'informa.",
        ],
        1: [
            "El curs de seguretat em va semblar molt útil i aplicable.",
            "M'han deixat fer una formació que demanava des de fa temps.",
        ],
    },
    "Eines i processos": {
        -1: [
            "El sistema nou és més lent i ningú ens va formar bé.",
            "Fem servir tres eines diferents per a la mateixa tasca.",
            "El procés té massa passes i paperassa innecessària.",
            "Quan falla l'aplicació ho has de fer tot a mà.",
        ],
        0: [
            "Les eines funcionen, però no estan ben integrades.",
            "El procés és correcte, tot i que es podria simplificar.",
        ],
        1: [
            "L'aplicació nova ens ha estalviat molta paperassa.",
            "La integració de les eines ha fet la feina més àgil.",
        ],
    },
    "Salut i seguretat": {
        -1: [
            "Hi ha llocs de treball amb molt de soroll i no tenim protectors còmodes.",
            "Acabo el dia amb molèsties d'esquena per la postura.",
            "La senyalització de seguretat al magatzem és insuficient.",
            "Quan hi ha pressa, les mesures de seguretat es relaxen.",
        ],
        0: [
            "Les mesures de seguretat hi són, però cal recordar-les més.",
            "No he tingut incidents, tot i que hi ha zones millorables.",
        ],
        1: [
            "Les millores ergonòmiques del magatzem es noten.",
            "La formació de seguretat d'enguany ha estat molt clara.",
        ],
    },
    "Ambient i relacions": {
        -1: [
            "Hi ha tensions entre torns i ningú les aborda.",
            "L'ambient ha empitjorat amb els canvis d'equip.",
            "Hi ha comentaris que no ajuden i ningú diu res.",
        ],
        0: [
            "L'ambient és bo en general, amb els alts i baixos normals.",
            "M'emporto bé amb l'equip, tot i que falta més coordinació.",
        ],
        1: [
            "L'equip és molt solidari i ens ajudem quan cal.",
            "El bon ambient fa que les setmanes difícils siguin més portables.",
        ],
    },
    "Organització i recursos": {
        -1: [
            "Es prenen decisions sense explicar els recursos disponibles.",
            "Falten mans i es nota en la planificació.",
            "L'estructura canvia cada poc temps i no s'acaba d'assentar.",
        ],
        0: [
            "L'organització funciona, tot i que hi ha marge de millora.",
            "Els recursos arriben, però sovint tard.",
        ],
        1: [
            "La nova organització de l'equip ha estat un encert.",
            "Aquest trimestre s'han planificat millor els recursos.",
        ],
    },
}

OBERTURES = ["", "", "", "Crec que ", "Sincerament, ", "Des del meu punt de vista, "]
TANCAMENTS = [
    "",
    "",
    "",
    "",
    " Ho comento perquè es pugui millorar.",
    " És només la meva percepció.",
]

# Dades identificatives FALSES per demostrar la redacció automàtica.
PII_FALS = [
    " Si cal, el meu correu és laura.gomez@example.com.",
    " Podeu trucar-me al 699 123 456.",
    " El meu usuari és @lgomez_damm.",
    " Escriviu a miquel.sans@example.org per ampliar-ho.",
]


# ---------------------------------------------------------------------------
# Utilitats de text
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?:\+34[\s.-]?)?[6-9](?:[\s.-]?\d){8}")
HANDLE_RE = re.compile(r"@[A-Za-z0-9_]{2,}")
# Noms propis després de "sóc", "amb", "en/la" (heurística conservadora).
NOM_RE = re.compile(r"\b(?:sóc|amb|parlo amb|ho comenta)\s+(?:la|el|l'|en|na)?\s*([A-ZÀ-Ú][a-zà-ú]{2,})\b")


def normalitza(text: str) -> str:
    """Minúscules i sense accents, per fer coincidir paraules clau."""
    text = text.lower()
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def redacta_pii(text: str) -> tuple[str, list[str]]:
    """Elimina correus, telèfons i usuaris. Retorna (text net, tipus detectats)."""
    if not text:
        return "", []
    detectats: list[str] = []

    def _sub(pattern: re.Pattern, etiqueta: str, value: str) -> str:
        nonlocal detectats
        if pattern.search(value):
            detectats.append(etiqueta)
            return pattern.sub(f"[{etiqueta} eliminat]", value)
        return value

    net = EMAIL_RE.sub("[correu eliminat]", text)
    if net != text:
        detectats.append("correu")
    nou = PHONE_RE.sub("[telèfon eliminat]", net)
    if nou != net:
        detectats.append("telèfon")
    net = nou
    nou = HANDLE_RE.sub("[usuari eliminat]", net)
    if nou != net:
        detectats.append("usuari")
    net = nou
    # Noms propis: només els que apareixen en contextos explícits.
    if NOM_RE.search(net):
        detectats.append("nom")
        net = NOM_RE.sub(lambda m: m.group(0)[: m.start(1) - m.start(0)] + "[nom eliminat]", net)
    return net, sorted(set(detectats))


# ---------------------------------------------------------------------------
# Classificació de comentaris per paraules clau (explicable, sense caixa negra)
# ---------------------------------------------------------------------------

PARAULES_CLAU = {
    "Torns i horaris": ["torn", "torns", "horaris", "rotacio", "nit", "matí", "tarda", "calendari"],
    "Descansos i pauses": ["descans", "descansos", "pausa", "pauses", "esmorzar", "dinar", "menjar", "relleu", "respir", "desconnectar"],
    "Càrrega de treball": ["carrega", "carregues", "volum", "presses", "estres", "sobrecarrega", "extres", "termini", "acumul"],
    "Comunicació": ["comunicacio", "comunicar", "informacio", "avisos", "reunio", "reunions d'equip", "transparencia", "assabento", "explicar", "criteris"],
    "Lideratge": ["caps", "caps de", "lider", "lideratge", "manager", "coordinador", "supervisor", "feedback", "responsable", "autonomia", "micromanagement"],
    "Reconeixement": ["reconeixement", "reconeixements", "reconeix", "valorar", "valorat", "merit", "incentiu", "premi", "esforc"],
    "Conciliació": ["conciliacio", "familia", "flexibilitat", "teletreball", "vida personal", "entrada", "sortida", "hores"],
    "Formació i desenvolupament": ["formacio", "formacions", "formacio de seguretat", "aprendre", "curs", "cursos", "curs de seguretat", "creixer", "desenvolupament", "carrera", "formar"],
    "Eines i processos": ["eina", "eines", "sistema", "erp", "ordinador", "aplicacio", "proces", "processos", "paperassa", "digital", "integracio"],
    "Salut i seguretat": ["salut", "seguretat", "ergonomia", "fatiga", "dolor", "esquena", "epi", "risc", "soroll", "postura", "molesties"],
    "Ambient i relacions": ["ambient", "companys", "relacions", "respecte", "tensions", "solidari", "clima"],
    "Organització i recursos": ["organitzacio", "recursos", "plantilla", "estructura", "decisions"],
}


def classifica_tema(text: str) -> str:
    """Retorna el tema amb més coincidències de paraules clau."""
    if not text or not text.strip():
        return "Altres"
    net = normalitza(text)
    millor, millor_punts = "Altres", 0
    for tema, claus in PARAULES_CLAU.items():
        # Les paraules més llargues són més específiques: pesen més.
        punts = sum(
            (len(c) ** 2) * len(re.findall(r"\b" + re.escape(normalitza(c)) + r"\b", net))
            for c in claus
        )
        if punts > millor_punts:
            millor, millor_punts = tema, punts
    return millor


CUES_NEGATIUS = {
    "no es respecta": 2.0,
    "no es reconeix": 2.0,
    "no respecta": 1.8,
    "no es pot": 1.5,
    "no podem": 1.5,
    "no puc": 1.2,
    "no arribo": 1.5,
    "no acabo": 1.5,
    "no tinc temps": 1.5,
    "no hi ha": 1.5,
    "no serveix": 1.8,
    "no sempre": 1.0,
    "no veig": 1.4,
    "no dona": 1.4,
    "no ajuda": 1.4,
    "no ajuden": 1.5,
    "no arriba": 1.4,
    "no s'acaba": 1.2,
    "no estan": 1.2,
    "no esta": 1.2,
    "sense explicar": 1.2,
    "sense haver pogut": 1.5,
    "sense problemes": -1.5,
    "ningu": 1.3,
    "mai": 1.2,
    "impossible": 2.0,
    "massa": 1.2,
    "tard": 1.1,
    "falta": 1.0,
    "falten": 1.2,
    "fallen": 1.4,
    "falla": 1.4,
    "pitjor": 1.5,
    "tensions": 1.5,
    "estres": 1.4,
    "sobrecarrega": 1.5,
    "acumul": 1.2,
    "esgotat": 1.5,
    "cremat": 1.5,
    "pressionar": 1.5,
    "micromanagement": 2.0,
    "innecessaria": 1.5,
    "insuficient": 1.5,
    "lent": 1.4,
    "soroll": 1.1,
    "dolor": 1.4,
    "molesties": 1.2,
    "queixa": 1.0,
    "queixes greus": -1.0,
    "empitjor": 1.5,
    "dificil": 1.4,
    "dificulta": 1.3,
    "costen": 0.8,
    "cost": 0.8,
    "gens": 1.3,
    "poques": 1.3,
    "pocs": 1.0,
    "manca": 1.3,
    "exigent": 0.7,
    "obligatoris": 1.1,
    "paperassa": 1.1,
    "tres eines diferents": 1.2,
    "els mateixos": 1.0,
    "encadenant": 1.0,
    "desgasta": 1.4,
    "dempeus": 1.0,
    "sobre el paper": 1.4,
    "he de triar": 1.0,
    "a ma": 0.7,
    "es relaxen": 1.1,
    "ni tan sols": 1.2,
    "sempre van als mateixos": 1.5,
    "no tinc queixes": -1.5,
    "menys esgotat": -1.5,
    "baixes": 0.9,
    "vaig just": 1.2,
    "no s'han": 1.2,
    "decidits": 1.0,
}

CUES_POSITIUS = {
    "m'ha ajudat": 2.0,
    "ha ajudat": 1.5,
    "m'ha canviat": 1.5,
    "m'agrada": 1.8,
    "agraeixo": 1.8,
    "content": 1.8,
    "encert": 1.8,
    "ha millorat": 1.8,
    "millorat": 1.3,
    "més clar": 1.4,
    "més clares": 1.4,
    "més estables": 1.4,
    "més àgil": 1.4,
    "molt útil": 2.0,
    "molt clara": 1.4,
    "util": 1.3,
    "solidari": 1.8,
    "bona": 0.9,
    "correcte": 0.4,
    "acceptable": 0.4,
    "funciona": 0.7,
    "tranquil": 1.3,
    "estalviat": 1.4,
    "agil": 1.3,
    "repartit millor": 1.4,
    "planificat millor": 1.4,
    "he pogut": 1.2,
    "m'han deixat": 1.2,
    "ha pujat la moral": 1.5,
    "orgull": 1.8,
    "positiu": 1.8,
    "reconegut": 1.3,
    "valorat": 1.3,
    "s'ha valorat": 1.8,
    "s'ha explicat": 1.8,
    "es noten": 1.0,
    "s'ha notat": 1.2,
    "flexibilitat": 0.4,
    "estable": 0.6,
    "tranquils": 1.0,
    "m'ajuda": 1.5,
    "escolta": 1.0,
    "dona espai": 1.2,
    "bon ambient": 1.8,
    "mes portables": 1.6,
}


def sentiment_de(text: str) -> int:
    """Sentiment per lexicon: -1, 0 o 1. Llindar per evitar falsos positius."""
    if not text or not text.strip():
        return 0
    net = normalitza(text)
    neg = sum(w for cue, w in CUES_NEGATIUS.items() if normalitza(cue) in net)
    pos = sum(w for cue, w in CUES_POSITIUS.items() if normalitza(cue) in net)
    if neg - pos > 0.8:
        return -1
    if pos - neg > 0.8:
        return 1
    return 0

# ---------------------------------------------------------------------------
# Dades Sintètiques
# ---------------------------------------------------------------------------
from faker import Faker 

fake = Faker('es_ES')

def generar_datos_sinteticos(n_muestras=1000):
    """Genera un DataFrame con datos falsos que respetan la estructura original."""
    datos = []
    for _ in range(n_muestras):
        datos.append({
            'id_usuario': fake.uuid4(),
            'edad': random.randint(18, 65),
            'departamento': random.choice(['Ventas', 'IT', 'RRHH', 'Marketing']),
            'satisfaccion': random.uniform(1.0, 5.0),
            'comentario': fake.sentence() # Texto aleatorio
        })
    return pd.DataFrame(datos)

# ---------------------------------------------------------------------------
# Anonimitació i Hash
# ---------------------------------------------------------------------------

def anonimizar_dataset(df, columnas_sensibles):
    """Aplica un hash irreversible a las columnas con PII (Información Personal Identificable)."""
    df_seguro = df.copy()
    
    # Obtener el salt del entorno (NUNCA hardcodear contraseñas)
    # Asegúrate de cargar las variables con dotenv en app.py
    salt = os.getenv("HASH_SALT", "default_hackathon_salt").encode()
    
    for col in columnas_sensibles:
        if col in df_seguro.columns:
            df_seguro[col] = df_seguro[col].apply(
                lambda x: hashlib.sha256(str(x).encode() + salt).hexdigest()
            )
    return df_seguro

# ---------------------------------------------------------------------------
# Generació
# ---------------------------------------------------------------------------

def _normalitza_pesos(pesos: dict[str, float]) -> list[float]:
    total = sum(pesos.values())
    return [v / total for v in pesos.values()]


def _comentari(rng: random.Random, tema: str, sentiment: int, pii: bool) -> str:
    opcions = COMENTARIS[tema][sentiment]
    base = rng.choice(opcions)
    obertura = rng.choice(OBERTURES)
    if obertura:
        base = obertura + base[0].lower() + base[1:]
    base += rng.choice(TANCAMENTS)
    if pii:
        base += rng.choice(PII_FALS)
    return base


def _escala(rng: random.Random, centre: float) -> int:
    valor = rng.gauss(centre, 0.55)
    return int(min(5, max(1, round(valor))))


def generar_respostes(n: int = 640, seed: int = 42) -> pd.DataFrame:
    """Genera el conjunt sintètic complet."""
    rng = random.Random(seed)

    prob_col = [0.18, 0.13, 0.19, 0.31, 0.19, 0.24]  # participació desigual respecte de la població
    registres: list[dict] = []

    for i in range(n):
        collectiu = rng.choices(COL_LECTIUS, weights=prob_col, k=1)[0]
        periode = "2026-T3" if rng.random() < 0.45 else "2026-T4"

        pesos = dict(PESOS_TEMA[collectiu])
        if periode == "2026-T4":
            # Biaix intencionat: torns i descansos pugen; comunicació baixa.
            pesos["Torns i horaris"] += 7
            pesos["Descansos i pauses"] += 6
            pesos["Comunicació"] -= 3

        tema = rng.choices(list(pesos.keys()), weights=_normalitza_pesos(pesos), k=1)[0]

        prior = SENTIMENT_BASE[tema] + AJUST_COL_LECTIU[collectiu]
        if periode == "2026-T4" and tema in ("Torns i horaris", "Descansos i pauses"):
            prior -= 0.18

        r = rng.random()
        if r < 0.50:
            sentiment = -1
        elif r < 0.82:
            sentiment = 0
        else:
            sentiment = 1
        # Si el tema és molt negatiu, augmenta la probabilitat de comentari negatiu.
        if prior < -0.35 and rng.random() < 0.25:
            sentiment = -1

        te_comentari = rng.random() < 0.86
        pii = te_comentari and rng.random() < 0.035
        comentari = _comentari(rng, tema, sentiment, pii) if te_comentari else ""

        if tema == "Comunicació":
            escala_com = _escala(rng, 3.4 + 0.9 * sentiment)
        else:
            escala_com = _escala(rng, 3.2 + AJUST_COL_LECTIU[collectiu] * 2 + rng.gauss(0, 0.3))
        if tema == "Reconeixement":
            escala_rec = _escala(rng, 3.0 + 1.0 * sentiment)
        else:
            escala_rec = _escala(rng, 3.1 + AJUST_COL_LECTIU[collectiu] * 2 + rng.gauss(0, 0.3))

        inici, fi = PERIODE_DATA[periode]
        data = inici + timedelta(days=rng.randint(0, (fi - inici).days))

        # Canal coherent amb el col·lectiu.
        if collectiu in ("Planta", "Logística"):
            canal = rng.choices(["Mòbil-QR", "Correu","NFC"], weights=[0.88, 0.09, 0.03], k=1)[0]
        elif collectiu == "Comercial":
            canal = rng.choices(["Mòbil-QR", "Correu","NFC"], weights=[0.55, 0.35, 0.10], k=1)[0]
        elif collectiu == "Oficina":
            canal = rng.choices(["Mòbil-QR", "Correu","NFC"], weights=[0.18, 0.52, 0.30], k=1)[0]
        else:
            canal = rng.choices(["Mòbil-QR", "Correu","NFC"], weights=[0.10, 0.35, 0.55], k=1)[0]

        registres.append(
            {
                "id_resposta": f"r_{i + 1:05d}",
                "data": data.isoformat(),
                "període": periode,
                "col·lectiu": collectiu,
                "centre_tipus": CENTRES[collectiu],
                "canal": canal,
                "escala_benestar": _escala(rng, 3.3 + 0.9 * sentiment),
                "escala_càrrega": _escala(rng, 3.0 - 0.8 * sentiment),
                "escala_comunicació": escala_com,
                "escala_reconeixement": escala_rec,
                "comentari_obert": comentari,
                "tema_real": tema,
                "sentiment_real": sentiment,
            }
        )

    df = pd.DataFrame(registres)
    df["tema_detectat"] = df["comentari_obert"].map(classifica_tema)
    df["sentiment_detectat"] = df["comentari_obert"].map(sentiment_de)
    df["comentari_net"], df["pii_eliminada"] = zip(
        *(df["comentari_obert"].map(redacta_pii))
    ) if len(df) else ([], [])
    df["pii_eliminada"] = df["pii_eliminada"].map(lambda x: ", ".join(x) if x else "")
    return df


def desa_csv(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, index=False, encoding="utf-8")