"""
Motor d'anàlisi de la demo (determinista i explicable).

No és un model de ML: és un conjunt de regles transparents que permeten
ensenyar a la demo com es passaria del feedback a insights i accions.
L'objectiu és que qualsevol persona del jurat pugui entendre per què el
sistema diu el que diu.
"""

from __future__ import annotations

import math

import pandas as pd

from datos import POBLACIO, TEMES, TEMES_ORDRE


# ---------------------------------------------------------------------------
# Representativitat
# ---------------------------------------------------------------------------


def marge_error(n: int, poblacio: int, z: float = 1.96) -> float:
    """Marge d'error al 95% per a una proporció, amb correcció de població finita."""
    if n <= 0 or poblacio <= 0:
        return 0.0
    moe = z * math.sqrt(0.25 / n) * math.sqrt(max(0.0, (poblacio - n) / max(1, poblacio - 1)))
    return round(moe * 100, 1)


# Mínim absolut per protegir l'anonimat (cites, senyals febles i talls filtrats).
ANONIMAT_MIN = 8
# Objectiu de resposta per col·lectiu, com a % de la seva població.
# Per sota de l'objectiu el col·lectiu es mostra amb avís; només s'oculta
# si té menys de ANONIMAT_MIN respostes (privacitat).
LLINDAR_PCT_DEFECTE = 15


def llindar_colectiu(col: str, llindar_pct: float = LLINDAR_PCT_DEFECTE) -> int:
    """Respostes objectiu d'un col·lectiu: llindar_pct % de la seva població."""
    return math.ceil(POBLACIO[col] * llindar_pct / 100)


def taula_participacio(df: pd.DataFrame, llindar_pct: float = LLINDAR_PCT_DEFECTE) -> pd.DataFrame:
    total_mostra = len(df)
    total_poblacio = sum(POBLACIO.values())
    files = []
    for col in POBLACIO:
        sub = df[df["col·lectiu"] == col]
        n = len(sub)
        poblacio = POBLACIO[col]
        taxa = (n / poblacio * 100) if poblacio else 0.0
        pes_mostra = (n / total_mostra * 100) if total_mostra else 0.0
        pes_poblacio = poblacio / total_poblacio * 100
        desviacio = pes_mostra - pes_poblacio
        minim = llindar_colectiu(col, llindar_pct)
        if n < ANONIMAT_MIN:
            estat = "Ocult (llindar)"
        elif n < minim or desviacio <= -5:
            estat = "Infrarepresentat"
        elif desviacio >= 5:
            estat = "Sobre-representat"
        else:
            estat = "Adequat"
        files.append(
            {
                "Col·lectiu": col,
                "Respostes": n,
                "Mínim": minim,
                "Població": poblacio,
                "Taxa resposta": round(taxa, 1),
                "Pes mostra": round(pes_mostra, 1),
                "Pes població": round(pes_poblacio, 1),
                "Desviació (pp)": round(desviacio, 1),
                "Marge error": marge_error(n, poblacio),
                "Estat": estat,
            }
        )
    return pd.DataFrame(files)


def alertes_representativitat(taula: pd.DataFrame) -> list[str]:
    alertes = []
    for _, row in taula.iterrows():
        if row["Estat"] == "Infrarepresentat":
            alertes.append(
                f"{row['Col·lectiu']}: {row['Respostes']} respostes "
                f"({row['Taxa resposta']}% de resposta; l'objectiu són {row['Mínim']})."
            )
        elif row["Estat"] == "Ocult (llindar)":
            alertes.append(
                f"{row['Col·lectiu']}: només {row['Respostes']} respostes; el segment no es mostra."
            )
    return alertes


# ---------------------------------------------------------------------------
# Temes i tendències
# ---------------------------------------------------------------------------


def resum_temes(df: pd.DataFrame) -> pd.DataFrame:
    files = []
    for tema, sub in df.groupby("tema_detectat"):
        if tema == "Altres":
            continue
        files.append(
            {
                "Tema": tema,
                "Respostes": len(sub),
                "%": round(len(sub) / max(1, len(df)) * 100, 1),
                "Sentiment mitjà": round(sub["sentiment_detectat"].mean(), 2),
                "Benestar mitjà": round(sub["escala_benestar"].mean(), 2),
            }
        )
    out = pd.DataFrame(files)
    if out.empty:
        return out
    out["_ordre"] = out["Tema"].map(TEMES_ORDRE).fillna(99)
    return out.sort_values(["Respostes", "_ordre"], ascending=[False, True]).drop(columns="_ordre")


def evolucio_temes(df: pd.DataFrame) -> pd.DataFrame:
    """Compara el pes de cada tema entre períodes (en punts percentuals)."""
    pivot = (
        df.groupby(["tema_detectat", "període"]).size().unstack(fill_value=0)
    )
    for p in ("2026-T3", "2026-T4"):
        if p not in pivot.columns:
            pivot[p] = 0
    totals = pivot.sum()
    share = pivot.div(totals.replace(0, 1), axis=1) * 100
    out = pd.DataFrame(
        {
            "Tema": share.index,
            "T3 (%)": share["2026-T3"].round(1).values,
            "T4 (%)": share["2026-T4"].round(1).values,
        }
    )
    out["Delta (pp)"] = (out["T4 (%)"] - out["T3 (%)"]).round(1)
    out = out[out["Tema"] != "Altres"]
    out["_ordre"] = out["Tema"].map(TEMES_ORDRE).fillna(99)
    return out.sort_values("Delta (pp)", ascending=False).drop(columns="_ordre")


def temes_emergents(evolucio: pd.DataFrame, minim_pp: float = 2.5) -> pd.DataFrame:
    return evolucio[evolucio["Delta (pp)"] >= minim_pp].copy()


def senyals_febles(df: pd.DataFrame, evolucio: pd.DataFrame, llindar_mostra: int = ANONIMAT_MIN) -> pd.DataFrame:
    """Temes poc freqüents però molt negatius i amb tendència a l'alça."""
    resum = resum_temes(df)
    if resum.empty:
        return resum
    resum = resum.merge(evolucio[["Tema", "Delta (pp)"]], on="Tema", how="left")
    resum["Delta (pp)"] = resum["Delta (pp)"].fillna(0)
    out = resum[
        (resum["Respostes"] >= llindar_mostra)
        & (resum["%"] <= 10)
        & (resum["Sentiment mitjà"] <= -0.25)
        & (resum["Delta (pp)"] >= 1.0)
    ].copy()
    out["Senyal"] = "Poc freqüent, negatiu i a l'alça"
    return out.sort_values("Delta (pp)", ascending=False)


# ---------------------------------------------------------------------------
# Cites anonimitzades
# ---------------------------------------------------------------------------


def cites_per_tema(df: pd.DataFrame, llindar: int = ANONIMAT_MIN, max_cites: int = 3) -> dict[str, list[str]]:
    """Retorna cites netes només per a segments que superen el llindar."""
    resultat: dict[str, list[str]] = {}
    if len(df) < llindar:
        return resultat
    amb_text = df[df["comentari_net"].astype(str).str.strip() != ""]
    for tema, sub in amb_text.groupby("tema_detectat"):
        if tema == "Altres" or len(sub) < llindar:
            continue
        negatius = sub[sub["sentiment_detectat"] < 0]["comentari_net"].dropna().unique().tolist()
        positius = sub[sub["sentiment_detectat"] > 0]["comentari_net"].dropna().unique().tolist()
        cites: list[str] = []
        for text in negatius[:max_cites]:
            if text not in cites:
                cites.append(text)
        for text in positius[:1]:
            if text not in cites:
                cites.append(text)
        resultat[tema] = cites[: max_cites + 1]
    return resultat


# ---------------------------------------------------------------------------
# Recomanacions i tancament de cicle
# ---------------------------------------------------------------------------

RECOMANACIONS_BASE = {
    "Torns i horaris": {
        "accio": "Revisar la planificació de torns amb 2 setmanes d'antelació i limitar els canvis d'última hora.",
        "responsable": "People + Caps de planta",
        "impacte": "Alt",
        "esforc": "Mitjà",
    },
    "Descansos i pauses": {
        "accio": "Garantir relleus per fer la pausa completa, especialment al torn de nit.",
        "responsable": "Operacions",
        "impacte": "Alt",
        "esforc": "Mitjà",
    },
    "Càrrega de treball": {
        "accio": "Revisar el volum per equip i reforçar els pics amb suport temporal.",
        "responsable": "Direcció d'operacions",
        "impacte": "Alt",
        "esforc": "Alt",
    },
    "Comunicació": {
        "accio": "Crear un butlletí breu per col·lectiu amb decisions, motius i properes passes.",
        "responsable": "Comunicació interna",
        "impacte": "Mitjà",
        "esforc": "Baix",
    },
    "Lideratge": {
        "accio": "Formar els caps d'equip en feedback setmanal i escolta activa.",
        "responsable": "People",
        "impacte": "Alt",
        "esforc": "Mitjà",
    },
    "Reconeixement": {
        "accio": "Establir un reconeixement trimestral per equip, no només individual.",
        "responsable": "People",
        "impacte": "Mitjà",
        "esforc": "Baix",
    },
    "Conciliació": {
        "accio": "Fer explícits els criteris de flexibilitat i garantir que tots els caps els apliquen igual.",
        "responsable": "People + Direcció",
        "impacte": "Mitjà",
        "esforc": "Baix",
    },
    "Formació i desenvolupament": {
        "accio": "Publicar un pla de formació per col·lectiu amb temps protegit per fer-lo.",
        "responsable": "Desenvolupament de persones",
        "impacte": "Mitjà",
        "esforc": "Mitjà",
    },
    "Eines i processos": {
        "accio": "Simplificar el procés amb més passes i formar les persones abans de desplegar canvis.",
        "responsable": "Data & IA + Operacions",
        "impacte": "Mitjà",
        "esforc": "Alt",
    },
    "Salut i seguretat": {
        "accio": "Revisar ergonomia i equips de protecció a les zones amb més queixes.",
        "responsable": "Prevenció",
        "impacte": "Alt",
        "esforc": "Mitjà",
    },
    "Ambient i relacions": {
        "accio": "Facilitar espais de coordinació entre torns per reduir tensions.",
        "responsable": "Caps d'equip",
        "impacte": "Mitjà",
        "esforc": "Baix",
    },
    "Organització i recursos": {
        "accio": "Explicar les decisions organitzatives amb els recursos i terminis previstos.",
        "responsable": "Direcció",
        "impacte": "Mitjà",
        "esforc": "Mitjà",
    },
}


def recomanacions(df: pd.DataFrame, maxim: int = 4) -> pd.DataFrame:
    """Prioritza accions a partir de volum, sentiment i tendència."""
    resum = resum_temes(df)
    if resum.empty:
        return pd.DataFrame()
    evolucio = evolucio_temes(df)
    resum = resum.merge(evolucio[["Tema", "Delta (pp)"]], on="Tema", how="left")
    resum["Delta (pp)"] = resum["Delta (pp)"].fillna(0)
    # Puntuació: volum + negativitat + creixement.
    resum["_score"] = (
        resum["%"] * 0.5
        + (-resum["Sentiment mitjà"]).clip(lower=0) * 40
        + resum["Delta (pp)"].clip(lower=0) * 2
    )
    resum = resum.sort_values("_score", ascending=False).head(maxim)

    files = []
    for _, row in resum.iterrows():
        base = RECOMANACIONS_BASE.get(row["Tema"], {})
        files.append(
            {
                "Prioritat": len(files) + 1,
                "Tema": row["Tema"],
                "Acció proposada": base.get("accio", "Analitzar el tema amb més profunditat."),
                "Responsable": base.get("responsable", "People"),
                "Impacte": base.get("impacte", "Mitjà"),
                "Esforç": base.get("esforc", "Mitjà"),
                "Suport": f"{row['Respostes']} respostes · {row['%']}% · sentiment {row['Sentiment mitjà']:+.2f}",
                "_score": row["_score"],
            }
        )
    return pd.DataFrame(files).drop(columns="_score")


def proposta_seguiment(df: pd.DataFrame) -> dict:
    """Proposa la propera microconsulta a partir del tema més emergent."""
    evolucio = evolucio_temes(df)
    if evolucio.empty:
        return {
            "titol": "Microconsulta de seguiment",
            "preguntes": ["Com ha evolucionat la teva percepció aquesta setmana?"],
            "motiu": "No hi ha prou dades per prioritzar un tema.",
        }
    top = evolucio.sort_values("Delta (pp)", ascending=False).iloc[0]
    tema = top["Tema"]
    preguntes = {
        "Torns i horaris": [
            "Els canvis de torn d'aquest mes s'han comunicat amb prou antelació?",
            "Quin aspecte del calendari et dificulta més la setmana?",
        ],
        "Descansos i pauses": [
            "Has pogut fer la pausa completa en almenys 4 de 5 dies?",
            "Què et caldria per poder descansar de veritat?",
        ],
        "Comunicació": [
            "La informació sobre els canvis ha arribat a temps?",
            "Quin canal prefereixes per rebre les novetats del teu col·lectiu?",
        ],
    }.get(
        tema,
        [
            f"Com valores ara el tema «{tema}» (1-5)?",
            "Quina acció concreta ajudaria més el teu equip?",
        ],
    )
    return {
        "titol": f"Seguiment: {tema}",
        "preguntes": preguntes,
        "motiu": (
            f"«{tema}» ha passat del {top['T3 (%)']}% al {top['T4 (%)']}% "
            f"de les respostes ({top['Delta (pp)']:+.1f} pp)."
        ),
        "tema": tema,
    }


# ---------------------------------------------------------------------------
# Qualitat del model
# ---------------------------------------------------------------------------


def precisio_classificacio(df: pd.DataFrame) -> dict[str, float]:
    no_buida = df[df["comentari_obert"].astype(str).str.strip() != ""]
    amb_text = no_buida[no_buida["tema_detectat"] != "Altres"]
    # Només es valida contra l'etiqueta oculta on n'hi ha (les respostes en directe no en tenen).
    amb_text = amb_text[amb_text["tema_real"].notna()]
    if amb_text.empty:
        return {"temes": 0.0, "sentiment": 0.0, "cobertura": 0.0}
    temes = (amb_text["tema_detectat"] == amb_text["tema_real"]).mean() * 100
    sentiments = (amb_text["sentiment_detectat"] == amb_text["sentiment_real"]).mean() * 100
    cobertura = (no_buida["tema_detectat"] != "Altres").mean() * 100
    return {
        "temes": round(temes, 1),
        "sentiment": round(sentiments, 1),
        "cobertura": round(cobertura, 1),
    }


def kpis(df: pd.DataFrame, llindar_pct: float = LLINDAR_PCT_DEFECTE) -> dict[str, float]:
    taula = taula_participacio(df, llindar_pct)
    total_poblacio = sum(POBLACIO.values())
    return {
        "respostes": len(df),
        "taxa_resposta": round(len(df) / total_poblacio * 100, 1),
        "marge_error": marge_error(len(df), total_poblacio),
        "col_lectius_coberts": int((taula["Respostes"] >= taula["Mínim"]).sum()),  # han assolit l'objectiu
        "alertes": int((taula["Estat"] == "Infrarepresentat").sum()),
    }