"""
Un QR per col·lectiu.

Cada QR du al formulari públic amb el col·lectiu i el canal a la URL
(?respondre=true&col=Planta&canal=Mòbil-QR). Així la persona no s'identifica mai:
el col·lectiu el decideix el QR que escaneja, i RRHH pot saber quin col·lectiu respon
i quin no (control de representativitat) sense preguntar res personal.

Aquest mòdul no depèn de Streamlit, de manera que es pot provar a part.
"""

from __future__ import annotations

import io
import unicodedata
import zipfile
from urllib.parse import urlencode

import qrcode
from PIL import Image, ImageDraw, ImageFont

import datos

CANAL_QR = "Mòbil-QR"  # un QR sempre és el canal «Mòbil-QR» (no barregem amb Correu)


def colectius_qr() -> list[str]:
    """Col·lectius amb QR propi: tots menys «General» (que és només el cub per defecte)."""
    return [c for c in datos.COL_LECTIUS if c != "General"]


def url_resposta(base_url: str, col: str, canal: str = CANAL_QR) -> str:
    base = base_url.strip().rstrip("/") or "http://localhost:8501"
    return base + "/?" + urlencode({"respondre": "true", "col": col, "canal": canal})


def _sense_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def _fitxer(col: str) -> str:
    return "qr_" + _sense_accents(col).lower().replace(" ", "_") + ".png"


def nom_fitxer(col: str) -> str:
    """Nom de fitxer del PNG d'un col·lectiu (sense accents)."""
    return _fitxer(col)


def _font(mida: int = 30) -> tuple[ImageFont.ImageFont, bool]:
    """Retorna (font, només_ascii). Si només tenim la font per defecte antiga, evitem accents."""
    for nom in ("arial.ttf", "DejaVuSans.ttf", "Arial.ttf", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(nom, mida), False
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=mida), False  # Pillow >= 10.1 (inclou accents)
    except TypeError:
        return ImageFont.load_default(), True


def qr_png(url: str, etiqueta: str = "") -> bytes:
    """PNG del QR amb una franja inferior amb el nom del col·lectiu (llest per imprimir)."""
    qr = qrcode.QRCode(box_size=10, border=4, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    if etiqueta:
        font, nomes_ascii = _font()
        text = _sense_accents(etiqueta) if nomes_ascii else etiqueta
        franja = 70
        sortida = Image.new("RGB", (img.width, img.height + franja), "white")
        sortida.paste(img, (0, 0))
        d = ImageDraw.Draw(sortida)
        bbox = d.textbbox((0, 0), text, font=font)
        x = (sortida.width - (bbox[2] - bbox[0])) // 2 - bbox[0]
        y = img.height + (franja - (bbox[3] - bbox[1])) // 2 - bbox[1] - 6
        d.text((x, y), text, fill="black", font=font)
        img = sortida

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def qrs_per_colectiu(base_url: str) -> list[dict]:
    """Una entrada per col·lectiu: nom, tipus de centre, URL, bytes del PNG i nom del fitxer."""
    sortida = []
    for col in colectius_qr():
        url = url_resposta(base_url, col)
        sortida.append(
            {
                "col": col,
                "centre": datos.CENTRES.get(col, ""),
                "url": url,
                "png": qr_png(url, col),
                "fitxer": _fitxer(col),
            }
        )
    return sortida


def zip_qrs(qrs: list[dict]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for q in qrs:
            z.writestr(q["fitxer"], q["png"])
    return buf.getvalue()