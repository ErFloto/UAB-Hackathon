"""
Integració amb Microsoft Teams (publicació de la microconsulta en un canal).

Com funciona:
  - Teams ja no admet els webhooks antics (connectors d'Office 365, retirats el maig de 2026).
    La via vigent és l'app Workflows (Power Automate): plantilla
    «Post to a channel when a webhook request is received». Dona una URL on es fa un POST
    amb una Adaptive Card i Teams la publica al canal.
  - La URL és un SECRET: viu a TEAMS_WEBHOOK_URL del .env i mai es mostra ni es puja al repositori.
  - Si TEAMS_WEBHOOK_URL no està definida, el mode és SIMULAT: es construeix exactament la mateixa
    targeta i es mostra com quedaria, però no s'envia res. Cap dada surt de l'ordinador.
  - L'enviament sempre el decideix una persona (botó explícit), després d'haver validat i publicat la consulta.
  - La targeta només porta el títol, la introducció i l'enllaç anònim. Cap dada personal ni resultat.
"""

from __future__ import annotations

import os

import requests


def url_configurada() -> bool:
    return bool(os.getenv("TEAMS_WEBHOOK_URL", "").strip())


def construeix_payload(consulta: dict, enllac: str, colectiu: str) -> dict:
    """Missatge en el format que espera el webhook de Workflows (Adaptive Card dins d'un attachment)."""
    n = len(consulta.get("preguntes", []))
    minuts = consulta.get("temps_estimat", 1)
    targeta = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {"type": "TextBlock", "text": consulta.get("titol", "Microconsulta"), "weight": "Bolder", "size": "Medium", "wrap": True},
            {"type": "TextBlock", "text": consulta.get("intro", ""), "wrap": True},
            {
                "type": "TextBlock",
                "text": f"Col·lectiu: {colectiu} · {n} preguntes · ~{minuts} min · 100% anònima",
                "isSubtle": True,
                "wrap": True,
            },
        ],
        "actions": [{"type": "Action.OpenUrl", "title": "Respondre ara", "url": enllac}],
    }
    return {
        "type": "message",
        "attachments": [
            {"contentType": "application/vnd.microsoft.card.adaptive", "contentUrl": None, "content": targeta}
        ],
    }


def envia(payload: dict) -> tuple[bool, str]:
    """Envia la targeta si hi ha URL; si no, mode simulat. Retorna (enviat, missatge)."""
    url = os.getenv("TEAMS_WEBHOOK_URL", "").strip()
    if not url:
        return False, "Mode simulat: no hi ha TEAMS_WEBHOOK_URL al .env, no s'ha enviat res."
    try:
        r = requests.post(url, json=payload, timeout=15)
    except requests.RequestException as e:
        return False, f"No s'ha pogut connectar amb Teams ({type(e).__name__})."
    if r.status_code in (200, 201, 202):
        return True, "Publicat al canal de Teams."
    return False, f"Teams ha respost amb error HTTP {r.status_code}."