"""Components visuals reutilitzables per a la interfície Streamlit. Renova"""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Estils
# ---------------------------------------------------------------------------

CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --maroon: #831B1E;
    --maroon-2: #A3262A;
    --gold: #FAB626;
    --gold-soft: #FDEBC0;
    --red: #E32819;
    --cream: #FBF3E4;
    --ink: #241715;
    --muted: #6F5F5A;
    --line: #EADBC4;
    --green: #2F7D5C;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: var(--ink);
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(1200px 600px at 85% -10%, rgba(250,182,38,0.10), transparent 60%),
        radial-gradient(900px 500px at -10% 20%, rgba(131,27,30,0.05), transparent 60%),
        var(--cream);
}

[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }

.block-container {
    padding-top: 2.2rem;
    padding-bottom: 3rem;
    max-width: 1240px;
}

h1, h2, h3, h4 {
    font-family: 'DM Serif Display', Georgia, serif;
    color: var(--maroon);
    letter-spacing: -0.01em;
    font-weight: 400;
}

h1 { font-size: 2.35rem; line-height: 1.1; }
h2 { font-size: 1.65rem; }
h3 { font-size: 1.25rem; }

p, li, label, span, div { font-size: 0.98rem; }

/* ---------------- Sidebar ---------------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #3A0A0D 0%, #5A1216 70%, #831B1E 100%);
    border-right: 1px solid rgba(250,182,38,0.25);
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #F3EEE5;
}
[data-testid="stSidebar"] .stRadio label p { color: #F1E4D8 !important; font-weight: 500; }
[data-testid="stSidebar"] .stRadio [role="radiogroup"] { gap: 0.15rem; }
[data-testid="stSidebar"] .stRadio label:hover p { color: #FFFFFF !important; }
/* Cada opción del menú (Streamlit >= 1.4x: <label data-testid="stRadioOption">) */
[data-testid="stSidebar"] [data-testid="stRadioOption"] {
    padding: 0.38rem 0.65rem;
    border-radius: 9px;
    transition: background 0.15s ease;
}
[data-testid="stSidebar"] [data-testid="stRadioOption"]:hover {
    background: rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked),
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected] {
    background: rgba(250,182,38,0.16);
    box-shadow: inset 3px 0 0 #FAB626;
}
/* Oculta el círculo del radio: es el primer div dentro del contenedor flex de la opción */
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child:not(:last-child) {
    display: none !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: rgba(250,182,38,0.14);
    border: 1px solid rgba(250,182,38,0.55);
    color: #F6E7C4;
    font-weight: 600;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(250,182,38,0.26);
    border-color: #FAB626;
    color: #FFFFFF;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #FAB626, #D99A12);
    border: 1px solid #FAB626;
    color: #831B1E;
    box-shadow: 0 8px 20px rgba(0,0,0,0.25);
}
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #FFC94D, #E8A81A);
    color: #831B1E;
}
[data-testid="stSidebar"] .stButton > button p { color: inherit !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.12); }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] a { color: var(--gold); }

.brand {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.4rem 0 0.9rem 0;
}
.brand-star {
    width: 40px; height: 40px; border-radius: 12px;
    background: linear-gradient(135deg, var(--gold), #D99A12);
    color: #831B1E; display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem; font-weight: 700; line-height: 1;
    box-shadow: 0 6px 18px rgba(250,182,38,0.35);
}
.brand-name {
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 1.35rem; color: #FFFFFF; line-height: 1;
}
.brand-sub {
    font-size: 0.72rem; letter-spacing: 0.14em; text-transform: uppercase;
    color: #D8B7A8; margin-top: 0.18rem;
}

/* ---------------- Hero ---------------- */
.hero {
    position: relative;
    background: linear-gradient(120deg, #4A0F12 0%, #831B1E 58%, #B3262B 100%);
    border-radius: 22px;
    padding: 2.1rem 2.3rem 2rem 2.3rem;
    color: #FBF3E4;
    overflow: hidden;
    box-shadow: 0 18px 50px rgba(131,27,30,0.22);
    margin-bottom: 1.4rem;
}
.hero::after {
    content: "";
    position: absolute; right: -70px; top: -90px;
    width: 320px; height: 320px; border-radius: 50%;
    background: radial-gradient(circle, rgba(250,182,38,0.30), rgba(250,182,38,0) 70%);
}
.hero::before {
    content: "";
    position: absolute; right: 60px; bottom: -60px;
    width: 180px; height: 180px; border-radius: 50%;
    border: 1px solid rgba(250,182,38,0.35);
}
.hero-kicker {
    font-size: 0.72rem; letter-spacing: 0.18em; text-transform: uppercase;
    color: var(--gold); font-weight: 600; margin-bottom: 0.55rem;
}
.hero-title {
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 2.35rem; line-height: 1.08; color: #FFFFFF;
    max-width: 780px; margin-bottom: 0.6rem;
}
.hero-title em { color: var(--gold); font-style: italic; }
.hero-text {
    color: #F0D9CF; max-width: 720px; font-size: 1.02rem; line-height: 1.55;
    margin-bottom: 0.1rem;
}
.hero-badges { margin-top: 1.05rem; display: flex; flex-wrap: wrap; gap: 0.45rem; }
.hero-badge {
    border: 1px solid rgba(250,182,38,0.45);
    background: rgba(250,182,38,0.10);
    color: #F0D9A6; border-radius: 999px;
    padding: 0.28rem 0.72rem; font-size: 0.76rem; letter-spacing: 0.02em;
}

/* ---------------- Mètriques ---------------- */
.metric {
    background: #FFFFFF;
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 1rem 1.1rem 0.95rem 1.1rem;
    height: 100%;
    box-shadow: 0 6px 18px rgba(28,36,48,0.04);
    position: relative;
    overflow: hidden;
}
.metric::before {
    content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
    background: linear-gradient(180deg, var(--gold), #D99A12);
}
.metric-value {
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 1.95rem; color: var(--maroon); line-height: 1.05;
}
.metric-label {
    font-size: 0.73rem; text-transform: uppercase; letter-spacing: 0.10em;
    color: var(--muted); font-weight: 600; margin-top: 0.35rem;
}
.metric-detail { font-size: 0.80rem; color: var(--muted); margin-top: 0.3rem; }

/* ---------------- Seccions ---------------- */
.section-kicker {
    font-size: 0.70rem; letter-spacing: 0.16em; text-transform: uppercase;
    color: var(--gold); font-weight: 700; margin-bottom: 0.25rem;
}
.section-title {
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 1.6rem; color: var(--maroon); margin-bottom: 0.2rem;
}
.section-sub { color: var(--muted); font-size: 0.95rem; margin-bottom: 1rem; }

.pill {
    display: inline-block; padding: 0.18rem 0.6rem; border-radius: 999px;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.02em;
    border: 1px solid transparent; white-space: nowrap;
}
.pill-gold { background: var(--gold-soft); color: #7A4A00; border-color: #F4D68A; }
.pill-green { background: #DFF0E7; color: #1F6046; border-color: #B9DCCB; }
.pill-red { background: #FBE0DC; color: #8A1A12; border-color: #F2B8B0; }
.pill-blue { background: #F3DCDD; color: #6B1519; border-color: #E3B9BB; }
.pill-grey { background: #F0E9DD; color: #5F524C; border-color: #DDD0BC; }

/* ---------------- Cicle ---------------- */
.cycle {
    display: grid; grid-template-columns: repeat(8, minmax(0, 1fr));
    gap: 0.4rem; margin: 0.4rem 0 0.6rem 0;
}
.cycle-step {
    background: #FFFFFF; border: 1px solid var(--line); border-radius: 12px;
    padding: 0.6rem 0.5rem; text-align: center; min-height: 78px;
}
.cycle-num {
    width: 22px; height: 22px; border-radius: 50%; margin: 0 auto 0.35rem auto;
    background: var(--maroon); color: #fff; font-size: 0.7rem; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
}
.cycle-label { font-size: 0.68rem; line-height: 1.2; color: var(--maroon); font-weight: 600; }
@media (max-width: 900px) { .cycle { grid-template-columns: repeat(4, 1fr); } }

/* ---------------- Callouts ---------------- */
.callout {
    border-radius: 14px; padding: 0.9rem 1.05rem; border: 1px solid var(--line);
    background: #FFFFFF; font-size: 0.92rem; line-height: 1.45;
}
.callout-warn { background: #FFF6E3; border-color: #EED9A8; color: #6B4E11; }
.callout-ok { background: #EAF5EF; border-color: #BFDDCD; color: #1F5A42; }
.callout-danger { background: #FDECE9; border-color: #F3C4BD; color: #7F1B14; }
.callout-info { background: #F4EFE8; border-color: #DDD2C2; color: #4A3F38; }
.callout b { color: inherit; }
.callout-title { font-weight: 700; margin-bottom: 0.25rem; }

/* ---------------- Cites ---------------- */
.quote {
    background: #FFFFFF; border: 1px solid var(--line); border-left: 4px solid var(--gold);
    border-radius: 10px; padding: 0.7rem 0.9rem; margin-bottom: 0.55rem;
}
.quote-text { font-size: 0.92rem; color: var(--ink); font-style: italic; line-height: 1.45; }
.quote-meta { font-size: 0.73rem; color: var(--muted); margin-top: 0.35rem; }

/* ---------------- Alertes ---------------- */
.alert-item {
    display: flex; gap: 0.6rem; align-items: flex-start;
    background: #FFF6E3; border: 1px solid #EED9A8; border-radius: 12px;
    padding: 0.7rem 0.9rem; margin-bottom: 0.5rem; color: #6B4E11;
    font-size: 0.9rem;
}
.alert-dot {
    width: 8px; height: 8px; border-radius: 50%; background: var(--red);
    margin-top: 0.45rem; flex: 0 0 auto;
}
.hint { font-size: 0.8rem; color: var(--muted); }

/* ---------------- Streamlit widgets ---------------- */
.stButton > button {
    border-radius: 10px; font-weight: 600; border: 1px solid var(--maroon);
    padding: 0.45rem 1.1rem; transition: all 0.15s ease;
}
.stButton > button[kind="primary"] {
    background: var(--maroon); color: #FFFFFF; border: 1px solid var(--maroon);
    box-shadow: 0 6px 16px rgba(131,27,30,0.18);
}
.stButton > button[kind="primary"]:hover {
    background: #A3262A; border-color: #A3262A; transform: translateY(-1px);
}
.stButton > button[kind="secondary"] {
    background: #FFFFFF; color: var(--maroon); border: 1px solid #D9C9B5;
}
.stButton > button[kind="secondary"]:hover { border-color: var(--gold); color: #7A4A00; }

[data-testid="stForm"] {
    background: #FFFFFF; border: 1px solid var(--line); border-radius: 16px;
    padding: 1rem 1.2rem;
}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
textarea {
    border-radius: 10px !important;
}

[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
    border-radius: 12px; overflow: hidden; border: 1px solid var(--line);
}

[data-testid="stExpander"] {
    border: 1px solid var(--line); border-radius: 12px; background: #FFFFFF;
}

hr { border-color: var(--line); }

/* Amaga Deploy i el menú de Streamlit durant la demo, però NO la barra sencera:
   dins hi ha el botó per tornar a obrir la barra lateral. */
[data-testid="stToolbarActions"],
[data-testid="stAppDeployButton"],
[data-testid="stMainMenu"] { display: none !important; }

/* Botó per reobrir la barra lateral: visible i amb els colors de la marca */
[data-testid="stExpandSidebarButton"] {
    display: flex !important;
    background: var(--maroon);
    border-radius: 10px;
    box-shadow: 0 6px 16px rgba(131,27,30,0.25);
}
[data-testid="stExpandSidebarButton"],
[data-testid="stExpandSidebarButton"] * { color: #FFFFFF !important; fill: #FFFFFF !important; }
[data-testid="stExpandSidebarButton"]:hover { background: #A3262A; }

/* Títols de Streamlit (st.markdown("### ...")): els estils propis de Streamlit
   (Source Sans, pes 600, color de text) guanyaven a la regla global. */
[data-testid="stMain"] [data-testid="stHeadingWithActionElements"] h1,
[data-testid="stMain"] [data-testid="stHeadingWithActionElements"] h2,
[data-testid="stMain"] [data-testid="stHeadingWithActionElements"] h3,
[data-testid="stMain"] [data-testid="stHeadingWithActionElements"] h4,
[data-testid="stMain"] [data-testid="stHeadingWithActionElements"] h5,
[data-testid="stMain"] [data-testid="stHeadingWithActionElements"] h6 {
    font-family: 'DM Serif Display', Georgia, serif;
    color: var(--maroon);
    font-weight: 400;
    letter-spacing: -0.01em;
    line-height: 1.2;
}
/* El text del títol va dins d'un span/div: sense això la regla global
   "span, div { font-size: 0.98rem }" l'encongeix. */
[data-testid="stMain"] [data-testid="stHeadingWithActionElements"] h1 *,
[data-testid="stMain"] [data-testid="stHeadingWithActionElements"] h2 *,
[data-testid="stMain"] [data-testid="stHeadingWithActionElements"] h3 *,
[data-testid="stMain"] [data-testid="stHeadingWithActionElements"] h4 *,
[data-testid="stMain"] [data-testid="stHeadingWithActionElements"] h5 *,
[data-testid="stMain"] [data-testid="stHeadingWithActionElements"] h6 * {
    font-size: inherit; font-family: inherit; color: inherit;
    font-weight: inherit; line-height: inherit; letter-spacing: inherit;
}
[data-testid="stMain"] [data-testid="stHeadingWithActionElements"] h3 { font-size: 1.6rem; }
[data-testid="stMain"] [data-testid="stHeadingWithActionElements"] h4 { font-size: 1.3rem; }
[data-testid="stMain"] [data-testid="stHeadingWithActionElements"] h5 { font-size: 1.12rem; }

/* Botones desactivados (p. ej. publicar sin aprobación humana) */
.stButton > button:disabled {
    opacity: 0.45; cursor: not-allowed; box-shadow: none; transform: none;
}

/* Botón secundario de la barra lateral: el estilo genérico lo dejaba blanco con texto invisible */
[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background: rgba(250,182,38,0.14);
    border: 1px solid rgba(250,182,38,0.55);
    color: #F6E7C4;
}
[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
    background: rgba(250,182,38,0.26);
    border-color: #FAB626;
    color: #FFFFFF;
}
"""


def injecta_css() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------


def marca() -> None:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-star">★</div>
            <div>
                <div class="brand-name">EscoltDamm</div>
                <div class="brand-sub">Damm · UAB The Hack 2026</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(kicker: str, titol: str, text: str, badges: list[str] | None = None) -> None:
    badges_html = ""
    if badges:
        badges_html = (
            '<div class="hero-badges">'
            + "".join(f'<span class="hero-badge">{b}</span>' for b in badges)
            + "</div>"
        )
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-kicker">{kicker}</div>
            <div class="hero-title">{titol}</div>
            <div class="hero-text">{text}</div>
            {badges_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metrica(valor: str, etiqueta: str, detall: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric">
            <div class="metric-value">{valor}</div>
            <div class="metric-label">{etiqueta}</div>
            <div class="metric-detail">{detall}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def seccio(kicker: str, titol: str, subtitol: str = "") -> None:
    st.markdown(
        f"""
        <div>
            <div class="section-kicker">{kicker}</div>
            <div class="section-title">{titol}</div>
            <div class="section-sub">{subtitol}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pill(text: str, kind: str = "grey") -> str:
    return f'<span class="pill pill-{kind}">{text}</span>'


def callout(titol: str, text: str, kind: str = "info") -> None:
    st.markdown(
        f"""
        <div class="callout callout-{kind}">
            <div class="callout-title">{titol}</div>
            <div>{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def cicle_escolta(pas_actiu: int = 0) -> None:
    passos = [
        "Necessitat",
        "Consulta IA",
        "Validació",
        "Publicació",
        "Participació",
        "Anàlisi",
        "Visualització",
        "Acció",
    ]
    html = '<div class="cycle">'
    for i, p in enumerate(passos, start=1):
        actiu = i <= pas_actiu
        estil = "background:#831B1E;color:#fff;border-color:#831B1E;" if actiu else ""
        estil_num = "background:#FAB626;color:#831B1E;" if actiu else ""
        estil_text = "color:#fff;" if actiu else ""
        html += (
            f'<div class="cycle-step" style="{estil}">'
            f'<div class="cycle-num" style="{estil_num}">{i}</div>'
            f'<div class="cycle-label" style="{estil_text}">{p}</div>'
            f"</div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def cita(text: str, meta: str) -> None:
    st.markdown(
        f"""
        <div class="quote">
            <div class="quote-text">“{text}”</div>
            <div class="quote-meta">{meta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def alerta(text: str) -> None:
    st.markdown(
        f'<div class="alert-item"><div class="alert-dot"></div><div>{text}</div></div>',
        unsafe_allow_html=True,
    )