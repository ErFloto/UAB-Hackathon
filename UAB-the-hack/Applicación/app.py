"""
Escolta · Damm — prototip de plataforma d'escolta activa.

Aquest fitxer és el punt d'entrada de la demo (Streamlit).
Tota la interfície es pot executar en aquest dispositiu:

    streamlit run app.py

Les dades són 100% sintètiques i l'anàlisi és determinista i explicable.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from io import BytesIO

import Encuesta
import Interfaz as ui
import analisis
import datos
import qrcode

params = st.query_params
MODO_RESPOTA = "respondre" in params

if MODO_RESPOTA:
    import json
    st.markdown("<div style='max-width: 600px; margin: auto; padding-top: 2rem;'>", unsafe_allow_html=True)
    
    # Comprovem si ja ha respost en aquesta sessió
    if "enquesta_enviada" not in st.session_state:
        st.session_state.enquesta_enviada = False

    consulta_activa = None
    try:
        with open("consulta_activa.json", "r", encoding="utf-8") as f:
            consulta_activa = json.load(f)
    except Exception:
        consulta_activa = None

    if not consulta_activa:
        consulta_activa = {
            "titol": "Microconsulta UAB The Hack",
            "intro": "Respon amb total sinceritat de forma anònima.",
            "preguntes": [
                {"id": "q1", "text": "Com valores el teu grau de benestar actual?", "tipus": "Escala (1-5)", "obligatoria": True}
            ]
        }

    st.title(consulta_activa.get("titol", "Enquesta"))
    st.info(consulta_activa.get("intro", "T'agraïm la participació."))

    # Si JA ha respost, mostrem només el missatge d'èxit i blockejem un altre enviament
    if st.session_state.enquesta_enviada:
        st.success("✅ Ja has respost aquesta consulta anteriorment. Moltes gràcies per la teva participació anònima!")
        st.balloons()
    else:
        # Si NO ha respost, mostrem el formulari
        with st.form("formulari_public_exterior", clear_on_submit=True):
            respostes_usuari = {}
            preguntes = consulta_activa.get("preguntes", [])
            
            for i, q in enumerate(preguntes):
                obligatoria = "*(Obligatòria)*" if q.get("obligatoria") else ""
                st.markdown(f"**{i+1}. {q.get('text')}** {obligatoria}")
                
                tipus = q.get("tipus", "Text obert")
                q_id = q.get("id", f"q_{i}")
                
                if tipus == Encuesta.TIPUS_ESCALA:
                    respostes_usuari[q_id] = st.radio("Escala", ["1", "2", "3", "4", "5"], horizontal=True, key=f"ext_{q_id}_{i}")
                elif tipus == Encuesta.TIPUS_SI_NO:
                    respostes_usuari[q_id] = st.radio("Sí/No", ["Sí", "No"], horizontal=True, key=f"ext_{q_id}_{i}")
                elif tipus == Encuesta.TIPUS_OPCIONS:
                    opcions = q.get("opcions", ["Opció 1", "Opció 2"])
                    if not opcions:
                        opcions = ["Opció 1", "Opció 2"]
                    respostes_usuari[q_id] = st.radio("Tria una opció", opcions, key=f"ext_{q_id}_{i}")
                else:
                    respostes_usuari[q_id] = st.text_area("Escriu la teva resposta...", key=f"ext_{q_id}_{i}")
                
                st.write("---")
                
            enviat = st.form_submit_button("Enviar respostes", type="primary", use_container_width=True)
            if enviat:
                # Canviem l'estat a True i recarreguem la pàgina
                st.session_state.enquesta_enviada = True
                st.rerun()
                
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()
        
# ---------------------------------------------------------------------------
# Configuració i estat
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="EscoltDamm",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded",
)
ui.injecta_css()

PAGINES = [
    "Inici",
    "Nova consulta",
    "Participació",
    "Anàlisi",
    "Insights i accions",
    "Privacitat",
]

COLORS = ["#831B1E", "#FAB626", "#2F7D5C", "#E32819", "#6F5F5A", "#C9A66B"]
STATUS_COLORS = {
    "Adequat": "#2F7D5C",
    "Sobre-representat": "#FAB626",
    "Infrarepresentat": "#E32819",
    "Ocult (llindar)": "#6F5F5A",
}


# ---------------------------------------------------------------------------
# Comprovació de Mode Resposta Extern (QR / URL / NFC)
# ---------------------------------------------------------------------------


def init_state() -> None:
    valors = {
        "seed": 42,
        "n_respostes": 640,
        "llindar": analisis.LLINDAR_PCT_DEFECTE,
        "nav": "Inici",
        "necessitat": None,
        "consulta": None,
        "variacio": 0,
        "aprovada": False,
    }
    for k, v in valors.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


@st.cache_data(show_spinner="Generant dades sintètiques…")
def carrega_dades(seed: int, n: int) -> pd.DataFrame:
    return datos.generar_respostes(n=n, seed=seed)


df_global = carrega_dades(st.session_state.seed, st.session_state.n_respostes)
llindar = st.session_state.llindar


def colectius_amagats() -> list[str]:
    """Col·lectius per sota de l'objectiu que l'usuari ha decidit no representar.

    Es calculen sobre tot el conjunt de dades, perquè siguin els mateixos a totes les pàgines.
    """
    if st.session_state.get("mostra_sota", True):
        return []
    taula = analisis.taula_participacio(df_global, st.session_state.llindar)
    return taula.loc[taula["Estat"].isin(["Infrarepresentat", "Ocult (llindar)"]), "Col·lectiu"].tolist()


def ves(pagina: str) -> None:
    st.session_state.nav = pagina


def estil_fig(fig: go.Figure, height: int = 340, marge_esq: int = 10) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=10, t=28, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#241715", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
        hoverlabel=dict(bgcolor="#831B1E", font_color="#FFFFFF", bordercolor="#831B1E"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#EFE2CC", zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    ui.marca()
    st.button(
        "＋ Nova consulta",
        width="stretch",
        type="primary",
        on_click=ves,
        args=("Nova consulta",),
    )
    st.markdown("<div style='height:0.35rem'></div>", unsafe_allow_html=True)
    st.radio("Navegació", PAGINES, key="nav", label_visibility="collapsed")

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.68rem;letter-spacing:0.15em;text-transform:uppercase;"
        "color:#D8B7A8;font-weight:700;margin-bottom:0.4rem'>Dades de demo</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-size:0.85rem;color:#F1E4D8'>{len(df_global):,} respostes sintètiques<br>"
        f"2 períodes · seed {st.session_state.seed}</div>",
        unsafe_allow_html=True,
    )
    st.slider("Objectiu de resposta per col·lectiu (% de la població)", 5, 25, key="llindar", format="%d%%")
    st.toggle(
        "Mostrar col·lectius per sota de l'objectiu",
        value=True,
        key="mostra_sota",
        help="Si el desactives, Participació i Anàlisi deixen de representar els col·lectius "
        "que no assoleixen l'objectiu de resposta. Les alertes es mantenen.",
    )
    if st.button("Regenerar dades", width="stretch"):
        st.session_state.seed += 1
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.74rem;color:#D8B7A8;line-height:1.5'>"
        "Prototip de demo.<br>Cap dada real de Damm ni de persones treballadores.<br>"
        "No és una eina de vigilància.</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Pàgina: Inici
# ---------------------------------------------------------------------------

def panel_distribucion_encuesta(consulta: dict) -> None:
    ip_local = "localhost" 
    url_publica = f"http://{ip_local}:8501/?respondre=true"  # <--- Canvi clau aquí
    
    st.subheader("Consulta llesta per distribuir")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("###  Enllaç Web")
        st.code(url_publica, language="text")
        st.markdown(f"[Obrir pàgina de votació]({url_publica})")
        st.caption("Clica l'enllaç per provar la pàgina exclusiva.")

    with c2:
        st.markdown("###  Codi QR")
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url_publica)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buf = BytesIO()
        img.save(buf, format="PNG")
        qr_bytes = buf.getvalue()
        
        st.image(qr_bytes, use_container_width=True)
        st.download_button("⬇️ Descarregar QR", data=qr_bytes, file_name="qr_enquesta.png", mime="image/png", use_container_width=True)

    with c3:
        st.markdown("###  Etiqueta NFC")
        st.info("Per activar físicament el punt d'enquesta:")
        st.write("1. Obre **NFC Tools** al teu mòbil.")
        st.write("2. Tria **Escriure > Afegir registre > URL**.")
        st.write("3. Enganxa l'enllaç web.")
        st.write("4. Apropa el mòbil a l'etiqueta.")

def mostrar_formulario_final(consulta: dict) -> None:
    st.subheader("Vista prèvia interactiva del formulari")
    st.caption("Així és exactament com ho veurà la persona treballadora al seu mòbil quan escanegi el QR.")
    
    with st.form("formulari_enquesta", clear_on_submit=True):
        st.markdown(f"### {consulta.get('titol', 'Enquesta')}")
        st.info(consulta.get("intro", "Ens agradaria saber què en penses."))
        
        respuestas = {}
        for i, q in enumerate(consulta.get("preguntes", [])):
            obligatoria = "*(Obligatòria)*" if q.get("obligatoria") else ""
            st.markdown(f"**{i+1}. {q['text']}** {obligatoria}")
            
            tipus = q.get("tipus", "")
            q_id = q.get("id", f"q_{i}")
            
            if tipus == Encuesta.TIPUS_ESCALA:
                respuestas[q_id] = st.radio("Escala", ["1", "2", "3", "4", "5"], horizontal=True, label_visibility="collapsed", key=f"form_{q_id}")
            elif tipus == Encuesta.TIPUS_SI_NO:
                respuestas[q_id] = st.radio("Sí/No", ["Sí", "No"], horizontal=True, label_visibility="collapsed", key=f"form_{q_id}")
            elif tipus == Encuesta.TIPUS_OPCIONS:
                opcions = q.get("opcions", ["Opció 1", "Opció 2"])
                respuestas[q_id] = st.radio("Tria una opció", opcions, label_visibility="collapsed", key=f"form_{q_id}")
            else:
                respuestas[q_id] = st.text_area("La teva resposta...", label_visibility="collapsed", key=f"form_{q_id}")
            
            st.write("---")
            
        enviat = st.form_submit_button("Enviar respostes", type="primary", use_container_width=True)
        if enviat:
            st.success("🎉 Respostes enviades correctament! (Dades processades localment per a la demo)")


def pagina_inici() -> None:
    ui.hero(
        "UAB The Hack! 2026 · Repte Estrella Damm",
        "Escoltar millor,<br><em>actuar abans.</em>",
        "Una plataforma d'escolta activa que crea microconsultes adaptades a cada "
        "col·lectiu, aconsegueix participació representativa i converteix les respostes "
        "en insights i accions, sempre amb anonimat i control humà.",
        [
            "Anonimat per disseny",
            "La IA proposa, les persones decideixen",
            "NFC + QR + Correu",
        ],
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        st.button(
            "Crear una microconsulta",
            type="primary",
            width="stretch",
            on_click=ves,
            args=("Nova consulta",),
        )
    with c2:
        st.button(
            "Veure participació",
            width="stretch",
            on_click=ves,
            args=("Participació",),
        )

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    k = analisis.kpis(df_global, llindar)
    cols = st.columns(5)
    with cols[0]:
        ui.metrica(f"{k['respostes']:,}", "Respostes sintètiques", "2 períodes comparables")
    with cols[1]:
        ui.metrica(f"{k['taxa_resposta']}%", "Taxa de resposta", "sobre població simulada")
    with cols[2]:
        ui.metrica(f"±{k['marge_error']} pp", "Marge d'error", "95% de confiança")
    with cols[3]:
        ui.metrica(f"{k['col_lectius_coberts']}/5", "Col·lectius coberts", f"han assolit el {llindar}% de resposta")
    with cols[4]:
        ui.metrica(f"{k['alertes']}", "Alertes de mostra", "segments infrarepresentats")

    st.markdown("<div style='height:1.3rem'></div>", unsafe_allow_html=True)

    ui.seccio(
        "El cicle",
        "De la necessitat a l'acció, en un sol flux",
        "Cada part del cicle alimenta la següent. La demo recorre les vuit etapes.",
    )
    ui.cicle_escolta(8)

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

    ui.seccio("Tres tensions", "Un sol problema, tres cares", "")
    t1, t2, t3 = st.columns(3)
    with t1:
        ui.callout(
            "Participació",
            "Volem obtenir un feedback actiu sense saturar al personal. Amb facilitats QR i mòbil ",
            "info",
        )
    with t2:
        ui.callout(
            "Personalització",
            "Consultes rellevants per a cada realitat (planta, logística, comercial, oficina, "
            "manager) sense dissenyar desenes d'enquestes a mà.",
            "warn",
        )
    with t3:
        ui.callout(
            "Anàlisi i acció",
            "Els comentaris es converteixen en temes, tendències i senyals febles; les "
            "recomanacions són propostes que RRHH valida.",
            "ok",
        )

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    ui.callout(
        "Privacitat des del primer moment",
        "Hem dissenyat el sistema posant la protecció de dades al centre de tot · visió global amb resultats "
        "agrupats i mínim de persones per grup · esborrat automàtic de dades identificatives · "
        "cap perfil personal · un equip humà valida la informació abans de publicar o actuar.",
        "ok",
    )


# ---------------------------------------------------------------------------
# Pàgina: Nova consulta
# ---------------------------------------------------------------------------


def _preguntes_a_df(preguntes: list[dict]) -> pd.DataFrame:
    files = []
    for p in preguntes:
        # Agafem les opcions (pot ser que la IA no hagi posat la clau)
        opcions = p.get("opcions", [])
        
        # Si la IA ha retornat 'null'
        if opcions is None:
            opcions_str = ""
        # Si la IA s'ha equivocat i ha retornat un text en lloc d'una llista
        elif isinstance(opcions, str):
            opcions_str = opcions
        # Si és una llista (el comportament esperat)
        elif isinstance(opcions, list):
            # Ens assegurem que tot el que hi ha dins es converteixi a text (str) abans d'unir-ho
            opcions_str = " · ".join([str(opt) for opt in opcions])
        else:
            opcions_str = ""

        files.append({
            "Pregunta": p.get("text", "Pregunta sense text"),
            "Tipus": p.get("tipus", "Text obert"),
            "Opcions": opcions_str,
            "Obligatòria": bool(p.get("obligatoria", True)),
        })
        
    return pd.DataFrame(files)


def _df_a_preguntes(editat: pd.DataFrame, originals: list[dict]) -> list[dict]:
    preguntes = []
    for i, row in editat.iterrows():
        text = str(row.get("Pregunta", "")).strip()
        if not text:
            continue
        opcions_raw = str(row.get("Opcions", "") or "")
        opcions = [o.strip() for o in opcions_raw.split("·") if o.strip()] if opcions_raw.strip() else []
        preguntes.append(
            {
                "id": f"q{i + 1}",
                "text": text,
                "tipus": str(row.get("Tipus", "Text obert")),
                "opcions": opcions,
                "obligatoria": bool(row.get("Obligatòria", True)),
                "condicional": "",
            }
        )
    return preguntes


def pagina_nova_consulta() -> None:
    ui.seccio(
        "Validació humana",
        "Nova microconsulta",
        "La IA proposa. RRHH edita, reordena, elimina i aprova abans de publicar.",
    )

    consulta = st.session_state.consulta

    if consulta is None:
        st.markdown(
            f"{ui.pill('Definir la necessitat', 'blue')}",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        with st.form("form_necessitat"):
            objectiu = st.text_area(
                "Què vols entendre?",
                value="Escriu de que vols que sigui l'enquesta.",
                height=92,
                help="Descriu l'objectiu en llenguatge natural. La IA el convertirà en preguntes.",
            )
            col1, col2 = st.columns(2)
            with col1:
                collectiu = st.selectbox("Col·lectiu", datos.COL_LECTIUS, index=0)
                durada = st.select_slider("Durada màxima", options=["Curt", "Moderat", "Llarg"])
                canal = st.selectbox("Canal principal", datos.CANALS, index=0)
            with col2:
                context = st.text_input("Context (opcional)", value="")
                to = st.radio("To de la consulta", list(Encuesta.TONS.keys()), horizontal=False)
                prohibits = st.multiselect(
                    "Temes que NO s'han de preguntar",
                    ["Salari", "Salut", "Torns", "Lideratge", "Conciliació", "Formació", "Eines"],
                    default=["Salari"],
                )

            enviar = st.form_submit_button("Generar consulta amb IA", type="primary", width="stretch")

        if enviar:
            if not objectiu.strip():
                st.error("Escriu un objectiu abans de generar la consulta.")
            else:
                necessitat = {
                    "objectiu": objectiu.strip(),
                    "col_lectiu": collectiu,
                    "context": context.strip(),
                    "durada_max": durada,
                    "temes_prohibits": [p.lower() for p in prohibits],
                    "to": to,
                    "canal": canal,
                }
                st.session_state.necessitat = necessitat
                st.session_state.variacio = 0
                st.session_state.consulta = Encuesta.generar_consulta(necessitat, 0)
                st.session_state.aprovada = False
                st.rerun()
        return

    # ---- Proposta generada -------------------------------------------------
    publicada = consulta.get("estat") == "Publicada"
    estat_pill = "green" if publicada else "gold"
    pas_pill = "Publicació" if publicada else "Revisar i validar"
    pills = " ".join(
        [
            ui.pill(pas_pill, "blue"),
            ui.pill(consulta["estat"], estat_pill),
            ui.pill(f"Temps estimat: {consulta['temps_estimat']} min", "grey"),
            ui.pill(f"Canal: {consulta['canal']}", "grey"),
        ]
    )
    st.markdown(pills, unsafe_allow_html=True)
    st.markdown("<div style='height:0.7rem'></div>", unsafe_allow_html=True)

    st.markdown(f"### {consulta['titol']}")
    st.markdown(f"<div style='color:#6F5F5A;max-width:820px'>{consulta['intro']}</div>", unsafe_allow_html=True)

    with st.expander("Per què aquesta proposta? (traçabilitat)", expanded=False):
        st.markdown(
            f"- **Objectiu introduït:** {consulta['objectiu']}\n"
            f"- **Col·lectiu:** {consulta['col_lectiu']} · **Context:** {consulta['context'] or '—'}\n"
            f"- **Temes prioritzats:** {', '.join(consulta['temes']) or '—'}\n"
            f"- **To:** {consulta['to']} · **Durada objectiu:** {consulta['durada_max']} min\n"
            f"- **Regla de seguretat:** les preguntes sobre temes prohibits s'han exclòs abans de generar."
        )
        if consulta["logica"]:
            st.markdown("**Lògica condicional proposada:**")
            for l in consulta["logica"]:
                st.markdown(f"- {l}")

    st.markdown("#### Preguntes proposades")
    st.caption("Pots editar el text, canviar el tipus, afegir o eliminar files. La IA no publica mai sense la teva aprovació.")

    editat = st.data_editor(
        _preguntes_a_df(consulta["preguntes"]),
        key="editor_preguntes",
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Pregunta": st.column_config.TextColumn("Pregunta", width="large", required=True),
            "Tipus": st.column_config.SelectboxColumn(
                "Tipus",
                options=[Encuesta.TIPUS_ESCALA, Encuesta.TIPUS_OPCIONS, Encuesta.TIPUS_SI_NO, Encuesta.TIPUS_OBERT],
                width="medium",
            ),
            "Opcions": st.column_config.TextColumn("Opcions (separades per ·)", width="medium"),
            "Obligatòria": st.column_config.CheckboxColumn("Obligatòria", width="small"),
        },
        disabled=publicada,
    )

    if not publicada:
        # Afegim una columna extra al principi (b0) i ajustem una mica les mides
        b0, b1, b2, b3 = st.columns([1, 1.2, 1.2, 2])
        
        with b0:
            # Botó per descartar-ho tot i fer una enquesta des de zero
            if st.button("Nova consulta", width="stretch", type="primary"):
                # Esborrem les dades clau que mantenen l'usuari en aquesta pantalla
                st.session_state.pop("consulta", None)
                st.session_state.pop("necessitat", None)
                st.session_state.pop("editor_preguntes", None)
                st.session_state.variacio = 0
                st.rerun() # Això recarrega la pàgina i el torna al formulari inicial

        with b1:
            if st.button("Tornar a generar", width="stretch"):
                st.session_state.variacio += 1
                st.session_state.consulta = Encuesta.generar_consulta(
                    st.session_state.necessitat, st.session_state.variacio
                )
                st.session_state.pop("editor_preguntes", None)
                st.rerun()
                
        with b2:
            if st.button("Desar esborrany", width="stretch"):
                nova = dict(consulta)
                nova["preguntes"] = _df_a_preguntes(editat, consulta["preguntes"])
                st.session_state.consulta = nova
                st.toast("Esborrany desat")
                
        with b3:
            aprovacio = st.checkbox(
                "He revisat les preguntes i aprovo la publicació (control humà obligatori)."
            )

        # Nou botó de publicar (sense dependre de Typeform)
      # Nou botó de publicar amb la persistència JSON per al QR/NFC
        if st.button("🚀 Aprovar i publicar l'enquesta (QR / NFC)", type="primary", disabled=not aprovacio):
            import json
            nova = dict(consulta)
            nova["preguntes"] = _df_a_preguntes(editat, consulta["preguntes"])
            nova["estat"] = "Publicada"
            
            # Guardem a fitxer local perquè l'enllaç extern ho llegeixi sempre
            with open("consulta_activa.json", "w", encoding="utf-8") as f:
                json.dump(nova, f, ensure_ascii=False, indent=4)
                
            st.session_state.consulta = nova
            st.session_state.aprovada = True
            st.session_state.pop("editor_preguntes", None)
            st.rerun()
            
    else: # Quan l'estat és 'Publicada'
        st.success("✅ Consulta publicada amb aprovació humana. L'enquesta ja és activa.")
        
        # 1. Mostrem el panell per obtenir els codis de distribució
        panel_distribucion_encuesta(consulta)
        
        st.divider()
        
        # 2. Mostrem l'enquesta funcional on es pot respondre
        mostrar_formulario_final(consulta)
        
        st.divider()
        
        # 3. Botons de navegació per continuar la presentació de la demo
        c1, c2, c3 = st.columns(3)
        with c1:
            st.button("Veure participació", type="primary", width="stretch", on_click=ves, args=("Participació",))
        with c2:
            st.button("Veure anàlisi", width="stretch", on_click=ves, args=("Anàlisi",))
        with c3:
            if st.button("Crear una altra consulta", width="stretch"):
                st.session_state.consulta = None
                st.session_state.necessitat = None
                st.session_state.variacio = 0
                st.rerun()

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    with st.expander("Com es connecta amb Typeform (contracte tècnic)"):
        st.markdown(
            "1. `POST /v1/forms` amb títol, introducció i camps → retorna `form_id` i `url`.\n"
            "2. `GET /v1/forms/{form_id}/responses` per recollir respostes (paginat, respectant límits).\n"
            "3. La nostra capa de privacitat elimina PII abans de desar el comentari.\n"
            "4. El token de Typeform viu al `.env`, mai al codi ni al repositori."
        )


# ---------------------------------------------------------------------------
# Pàgina: Participació
# ---------------------------------------------------------------------------


def pagina_participacio() -> None:
    ui.seccio(
        "Participació",
        "Qui ha respost i qui falta",
        "La representativitat es mesura per col·lectiu, no només en global.",
    )

    f1, f2 = st.columns([1, 2])
    with f1:
        periode = st.selectbox("Període", ["Tots"] + datos.PERIODES, index=0)
    with f2:
        col_sel = st.multiselect("Col·lectius", datos.COL_LECTIUS, default=datos.COL_LECTIUS)

    df = df_global.copy()
    if periode != "Tots":
        df = df[df["període"] == periode]
    if col_sel:
        df = df[df["col·lectiu"].isin(col_sel)]

    if len(df) < analisis.ANONIMAT_MIN:
        ui.callout(
            "Segment ocult per privacitat",
            f"Aquesta combinació té només {len(df)} respostes. Per sota del llindar de {analisis.ANONIMAT_MIN} "
            "no es mostren resultats: mai no es poden inferir respostes individuals.",
            "danger",
        )
        return

    k = analisis.kpis(df, llindar)
    taula = analisis.taula_participacio(df, llindar)
    alertes = analisis.alertes_representativitat(taula)

    cols = st.columns(4)
    with cols[0]:
        ui.metrica(f"{len(df):,}", "Respostes al tall", f"període: {periode}")
    with cols[1]:
        ui.metrica(f"{k['taxa_resposta']}%", "Taxa de resposta", "sobre població simulada")
    with cols[2]:
        ui.metrica(f"±{k['marge_error']} pp", "Marge d'error global", "95% de confiança")
    with cols[3]:
        ui.metrica(f"{len(alertes)}", "Segments a vigilar", f"objectiu: {llindar}% per col·lectiu")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # Els col·lectius per sota de l'objectiu es poden amagar de la vista amb el botó de la
    # barra lateral. Les alertes de sota se segueixen mostrant sempre: no s'amaga que falten.
    amagats = colectius_amagats()
    taula_vista = taula[~taula["Col·lectiu"].isin(amagats)]
    df_vista = df[~df["col·lectiu"].isin(amagats)]
    if amagats:
        st.caption(f"Vista sense: {', '.join(amagats)}. Segueixen comptant als totals i a les alertes.")
    if taula_vista.empty:
        st.info("Cap col·lectiu ha assolit l'objectiu de resposta. Activa el botó de la barra lateral per veure'ls tots.")

    g1, g2 = st.columns([1.55, 1])
    with g1:
        st.markdown("##### Població vs. mostra")
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                y=taula_vista["Col·lectiu"],
                x=taula_vista["Pes població"],
                name="Pes a la població",
                orientation="h",
                marker_color="#D9C9B5",
                text=taula_vista["Pes població"].astype(str) + "%",
                textposition="outside",
            )
        )
        fig.add_trace(
            go.Bar(
                y=taula_vista["Col·lectiu"],
                x=taula_vista["Pes mostra"],
                name="Pes a la mostra",
                orientation="h",
                marker_color="#831B1E",
                text=taula_vista["Pes mostra"].astype(str) + "%",
                textposition="outside",
            )
        )
        fig.update_layout(barmode="group")
        fig.update_xaxes(ticksuffix="%", range=[0, max(65, (taula_vista["Pes mostra"].max() if not taula_vista.empty else 0) + 12)])
        st.plotly_chart(estil_fig(fig, height=330), width="stretch")

    with g2:
        st.markdown("##### Canal de participació")
        canal = df_vista.groupby("canal").size().reset_index(name="Respostes")
        fig = px.pie(
            canal,
            names="canal",
            values="Respostes",
            hole=0.62,
            color_discrete_sequence=["#831B1E", "#FAB626", "#2F7D5C"],
        )
        fig.update_traces(textinfo="percent", textfont_size=12)
        fig.update_layout(showlegend=True)
        st.plotly_chart(estil_fig(fig, height=330), width="stretch")

    st.markdown("##### Detall per col·lectiu")
    st.dataframe(
        taula_vista,
        width="stretch",
        hide_index=True,
        column_config={
            "Col·lectiu": st.column_config.TextColumn("Col·lectiu", width="medium"),
            "Respostes": st.column_config.NumberColumn("Respostes", format="%d"),
            "Població": st.column_config.NumberColumn("Població", format="%d"),
            "Taxa resposta": st.column_config.ProgressColumn(
                "Taxa resposta", min_value=0, max_value=100, format="%.1f%%"
            ),
            "Pes mostra": st.column_config.NumberColumn("Pes mostra", format="%.1f%%"),
            "Pes població": st.column_config.NumberColumn("Pes població", format="%.1f%%"),
            "Desviació (pp)": st.column_config.NumberColumn("Desviació", format="%+.1f pp"),
            "Marge error": st.column_config.NumberColumn("Marge error", format="±%.1f pp"),
            "Estat": st.column_config.TextColumn("Estat", width="medium"),
        },
    )

    if alertes:
        st.markdown("##### Alertes de representativitat")
        for a in alertes:
            ui.alerta(a)
        ui.callout(
            "Què fem amb aquesta alerta?",
            "El sistema no amaga el problema: l'explica i proposa accions. A la demo, planta i "
            "logística queden per sota perquè responen menys; la recomanació és reforçar el canal "
            "QR i els recordatoris presencials, no augmentar la pressió.",
            "warn",
        )
    else:
        ui.callout("Mostra equilibrada", "Tots els col·lectius superen el llindar i la desviació és inferior a 5 pp.", "ok")

    with st.expander("Com es calcula el marge d'error?"):
        st.markdown(
            "Per a una proporció, amb z = 1,96 (95% de confiança) i correcció de població finita:\n\n"
            "`marge = z · √(0,25 / n) · √((N − n) / (N − 1))`\n\n"
            "El marge és orientatiu: la mostra sintètica té biaixos intencionats per demostrar "
            "que el sistema els detecta."
        )


# ---------------------------------------------------------------------------
# Pàgina: Anàlisi
# ---------------------------------------------------------------------------


def pagina_analisi() -> None:
    ui.seccio(
        "Anàlisi",
        "Del comentari al tema, del tema a la tendència",
        "Anàlisi explicable: cada etiqueta es pot justificar amb les paraules que l'han activada.",
    )

    amagats = colectius_amagats()
    col_visibles = [c for c in datos.COL_LECTIUS if c not in amagats]
    # Les dades de base d'aquesta pàgina no inclouen els col·lectius que s'han decidit no representar.
    df_base = df_global[~df_global["col·lectiu"].isin(amagats)]

    f1, f2, f3 = st.columns([1, 1.2, 1.2])
    with f1:
        periode = st.selectbox("Període", ["Tots"] + datos.PERIODES, index=0, key="an_periode")
    with f2:
        col_sel = st.multiselect("Col·lectiu", col_visibles, default=col_visibles, key="an_col_" + "_".join(col_visibles))
    with f3:
        nomes_amb_text = st.checkbox("Només comentaris amb text", value=True)

    if amagats:
        st.caption(f"Anàlisi sense: {', '.join(amagats)} (per sota de l'objectiu de resposta; botó de la barra lateral).")

    df = df_base.copy()
    if periode != "Tots":
        df = df[df["període"] == periode]
    if col_sel:
        df = df[df["col·lectiu"].isin(col_sel)]
    if nomes_amb_text:
        df = df[df["comentari_net"].astype(str).str.strip() != ""]

    if len(df) < analisis.ANONIMAT_MIN:
        ui.callout(
            "Segment ocult per privacitat",
            f"Només {len(df)} respostes amb els filtres actuals. Per sota de {analisis.ANONIMAT_MIN} no es mostra cap anàlisi.",
            "danger",
        )
        return

    resum = analisis.resum_temes(df)
    evolucio = analisis.evolucio_temes(df_base.copy()) if periode == "Tots" else pd.DataFrame()
    precisio = analisis.precisio_classificacio(df_base)
    n_pii = int((df_base["pii_eliminada"].astype(str).str.strip() != "").sum())

    cols = st.columns(4)
    with cols[0]:
        ui.metrica(f"{len(df):,}", "Respostes analitzades", "només text lliure" if nomes_amb_text else "totes")
    with cols[1]:
        ui.metrica(f"{len(resum)}", "Temes detectats", "classificació per paraules clau")
    with cols[2]:
        ui.metrica(f"{precisio['temes']}%", "Coincidència amb etiqueta oculta", "validació de la demo")
    with cols[3]:
        ui.metrica(f"{n_pii}", "Comentaris amb PII redactada", "correu, telèfon o usuari")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    g1, g2 = st.columns([1.5, 1])
    with g1:
        st.markdown("##### Temes principals")
        if not resum.empty:
            r = resum.sort_values("Respostes", ascending=True)
            fig = px.bar(
                r,
                x="Respostes",
                y="Tema",
                orientation="h",
                color="Sentiment mitjà",
                color_continuous_scale=["#E32819", "#E8D9B5", "#2F7D5C"],
                range_color=[-1, 1],
                text="Respostes",
            )
            fig.update_traces(textposition="outside")
            fig.update_coloraxes(colorbar_title="Sentiment")
            st.plotly_chart(estil_fig(fig, height=380), width="stretch")
    with g2:
        st.markdown("##### Sentiment mitjà per tema")
        if not resum.empty:
            r = resum.sort_values("Sentiment mitjà")
            colors = ["#E32819" if v < 0 else "#2F7D5C" for v in r["Sentiment mitjà"]]
            fig = go.Figure(
                go.Bar(
                    x=r["Sentiment mitjà"],
                    y=r["Tema"],
                    orientation="h",
                    marker_color=colors,
                    text=[f"{v:+.2f}" for v in r["Sentiment mitjà"]],
                    textposition="outside",
                )
            )
            fig.update_xaxes(range=[-1, 1])
            st.plotly_chart(estil_fig(fig, height=380), width="stretch")

    if not evolucio.empty:
        st.markdown("##### Evolució entre períodes")
        ui.callout(
            "Biaix intencionat de la demo",
            "El dataset sintètic fa créixer «Torns i horaris» i «Descansos i pauses» al segon període "
            "i baixar «Comunicació». El sistema ho ha de detectar sense saber-ho d'entrada.",
            "info",
        )
        fig = go.Figure()
        fig.add_trace(go.Bar(x=evolucio["Tema"], y=evolucio["T3 (%)"], name="2026-T3", marker_color="#D9C9B5"))
        fig.add_trace(go.Bar(x=evolucio["Tema"], y=evolucio["T4 (%)"], name="2026-T4", marker_color="#831B1E"))
        fig.update_layout(barmode="group")
        fig.update_xaxes(tickangle=-30)
        fig.update_yaxes(ticksuffix="%")
        st.plotly_chart(estil_fig(fig, height=370), width="stretch")

        e1, e2 = st.columns(2)
        with e1:
            st.markdown("##### Temes emergents")
            emergents = analisis.temes_emergents(evolucio)
            if emergents.empty:
                st.caption("Cap tema supera el llindar de +2,5 pp.")
            for _, row in emergents.iterrows():
                delta_pill = ui.pill(f"{row['Delta (pp)']:+.1f} pp", "red")
                st.markdown(
                    f"<div class='callout callout-warn' style='margin-bottom:0.45rem'>"
                    f"<b>{row['Tema']}</b> {delta_pill}<br>"
                    f"<span style='font-size:0.85rem'>Passa del {row['T3 (%)']}% al {row['T4 (%)']}% de les respostes.</span></div>",
                    unsafe_allow_html=True,
                )
        with e2:
            st.markdown("##### Senyals febles")
            febles = analisis.senyals_febles(df, evolucio)
            if febles.empty:
                st.caption("No s'han detectat senyals febles amb els criteris actuals.")
            for _, row in febles.iterrows():
                sent_pill = ui.pill(f"sentiment {row['Sentiment mitjà']:+.2f}", "red")
                st.markdown(
                    f"<div class='callout callout-danger' style='margin-bottom:0.45rem'>"
                    f"<b>{row['Tema']}</b> {sent_pill}<br>"
                    f"<span style='font-size:0.85rem'>{row['Respostes']} respostes ({row['%']}%), "
                    f"tendència {row['Delta (pp)']:+.1f} pp.</span></div>",
                    unsafe_allow_html=True,
                )

    st.markdown("##### Comentaris agrupats per tema")
    cites = analisis.cites_per_tema(df)
    if not cites:
        st.caption("No hi ha prou comentaris per tema per mostrar cites amb garanties.")
    for tema, llista in cites.items():
        with st.expander(f"{tema} · {len(llista)} cites anonimitzades"):
            for text in llista:
                ui.cita(text, "Comentari anonimitzat · cap dada identificativa")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    with st.expander("Redacció automàtica de dades identificatives (prova interactiva)", expanded=False):
        st.caption("Prova un comentari amb un correu, un telèfon o un usuari. El text es neteja abans d'analitzar-lo.")
        exemple = st.text_area(
            "Comentari original",
            value="Sóc la Laura i el meu correu és laura.gomez@example.com. Podeu trucar-me al 699 123 456 o escriure a @lgomez.",
            height=80,
        )
        net, detectats = datos.redacta_pii(exemple)
        st.markdown("**Text net que arriba al motor d'anàlisi:**")
        st.success(net)
        if detectats:
            st.markdown("**Dades eliminades:** " + ", ".join(ui.pill(d, "red") for d in detectats), unsafe_allow_html=True)
        else:
            st.caption("No s'ha detectat cap dada identificativa.")

    ui.callout(
        "Límits de l'anàlisi (explícits a la demo)",
        f"Classificació per paraules clau: la coincidència amb l'etiqueta oculta és del "
        f"{precisio['temes']}% i el sentiment coincideix en un {precisio['sentiment']}% dels casos. "
        "Una relació entre variables no demostra causalitat. La mida de la mostra i el marge d'error "
        "es mostren sempre; no es fan inferències sobre persones concretes.",
        "warn",
    )


# ---------------------------------------------------------------------------
# Pàgina: Insights i accions
# ---------------------------------------------------------------------------


def pagina_insights() -> None:
    ui.seccio(
        "Visualització i acció",
        "Insights que acaben en una decisió",
        "Les recomanacions són propostes prioritzades. RRHH decideix què es fa i quan.",
    )

    df = df_global
    recs = analisis.recomanacions(df, maxim=4)
    proposta = analisis.proposta_seguiment(df)

    if recs.empty:
        ui.callout("Sense dades suficients", "Calen més respostes per generar recomanacions.", "warn")
        return

    st.markdown("##### Accions proposades")
    for _, row in recs.iterrows():
        st.markdown(
            f"<div class='callout' style='margin-bottom:0.6rem;border-left:4px solid #FAB626'>"
            f"<div style='display:flex;justify-content:space-between;gap:1rem;align-items:center'>"
            f"<div><b>{row['Prioritat']}. {row['Tema']}</b><br>"
            f"<span style='font-size:0.92rem'>{row['Acció proposada']}</span><br>"
            f"<span class='hint'>{row['Suport']}</span></div>"
            f"<div style='text-align:right;min-width:170px'>"
            f"{ui.pill('Impacte ' + row['Impacte'], 'green' if row['Impacte'] == 'Alt' else 'gold')}<br>"
            f"{ui.pill('Esforç ' + row['Esforç'], 'grey')}<br>"
            f"<span class='hint'>{row['Responsable']}</span></div></div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("##### Tancament del cicle")
    s1, s2 = st.columns([1.4, 1])
    with s1:
        st.markdown(
            f"<div class='callout callout-info'>"
            f"<div class='callout-title'>Propera microconsulta proposada</div>"
            f"<div style='font-size:1.05rem;font-weight:600;margin:0.25rem 0'>{proposta['titol']}</div>"
            f"<div class='hint'>{proposta['motiu']}</div>"
            + "".join(f"<div style='margin-top:0.35rem'>· {p}</div>" for p in proposta["preguntes"])
            + "</div>",
            unsafe_allow_html=True,
        )
    with s2:
        def _crear_seguiment(prop: dict) -> None:
            need = {
                "objectiu": prop["motiu"] + " " + " ".join(prop["preguntes"]),
                "col_lectiu": "Planta",
                "context": "Seguiment del cicle",
                "durada_max": 1,
                "temes_prohibits": ["salari"],
                "to": "Proper i directe",
                "canal": "Mòbil-QR",
            }
            st.session_state.necessitat = need
            st.session_state.variacio = 0
            st.session_state.consulta = Encuesta.generar_consulta(need, 0)
            st.session_state.aprovada = False
            st.session_state.nav = "Nova consulta"

        st.button(
            "Crear la microconsulta de seguiment",
            type="primary",
            width="stretch",
            on_click=_crear_seguiment,
            args=(proposta,),
        )
        st.caption("S'obre el mateix flux de validació humana. Res es publica automàticament.")

    st.markdown("##### Pla d'acció i seguiment")
    pla = pd.DataFrame(
        [
            {"Horitzó": "0-30 dies", "Acció": recs.iloc[0]["Acció proposada"], "Responsable": recs.iloc[0]["Responsable"], "Indicador": "Taxa de resposta i valoració del tema"},
            {"Horitzó": "30-60 dies", "Acció": recs.iloc[1]["Acció proposada"] if len(recs) > 1 else "—", "Responsable": recs.iloc[1]["Responsable"] if len(recs) > 1 else "—", "Indicador": "Evolució del sentiment al tema"},
            {"Horitzó": "60-90 dies", "Acció": "Nova microconsulta de seguiment i comparació amb el període anterior", "Responsable": "People", "Indicador": "Delta de participació per col·lectiu"},
        ]
    )
    st.dataframe(pla, width="stretch", hide_index=True)

    ui.callout(
        "Control humà",
        "Cap recomanació s'executa automàticament. Cada acció té un responsable humà i un indicador "
        "per comprovar si realment ha millorat la percepció del col·lectiu.",
        "ok",
    )


# ---------------------------------------------------------------------------
# Pàgina: Privacitat
# ---------------------------------------------------------------------------


def pagina_privacitat() -> None:
    ui.seccio(
        "Principis no negociables",
        "Privacitat, anonimat i ús responsable",
        "Una solució que no genera confiança no farà que la gent respongui.",
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        ui.callout("Resultats 100% anònims i contextualitzats",
    "Mai mostrem respostes individuals i afegim un avís quan no s'arriba a l'objectiu de participació.", "ok")
    with c2:
        ui.callout("Minimització", "Només es recullen els camps necessaris.", "ok")
    with c3:
        ui.callout("Control humà", "La IA proposa consultes i recomanacions; les persones validen abans de publicar i actuar.", "ok")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    ui.seccio("Configuració", "Llindar mínim de mostra", "Prova com canvien els avisos en moure l'objectiu de resposta (% de la població de cada col·lectiu).")

    if "llindar_privacy" not in st.session_state:
        st.session_state.llindar_privacy = st.session_state.llindar

    def _canvia_llindar() -> None:
        st.session_state.llindar = int(st.session_state.llindar_privacy)

    st.slider(
        "Objectiu de taxa de resposta per col·lectiu (% de la població)",
        5,
        25,
        key="llindar_privacy",
        on_change=_canvia_llindar,
        format="%d%%",
    )

    taula = analisis.taula_participacio(df_global, st.session_state.llindar)
    sota = taula[taula["Respostes"] < taula["Mínim"]]
    ocults = taula[taula["Respostes"] < analisis.ANONIMAT_MIN]
    st.markdown(
        f"Amb l'objectiu actual, **{len(sota)} col·lectius** quedarien per sota i es mostrarien amb avís. "
        f"Ocults per privacitat (menys de {analisis.ANONIMAT_MIN} respostes): **{len(ocults)}**."
    )

    st.markdown("##### Esquema de dades (orientatiu)")
    esquema = pd.DataFrame(
        [
            {"Camp": "id_resposta", "Exemple": "r_00123", "Nota": "Aleatori, mai vinculat a una persona"},
            {"Camp": "data", "Exemple": "2026-10-15", "Nota": "Permet comparar períodes"},
            {"Camp": "col·lectiu", "Exemple": "Planta", "Nota": "Categoria àmplia, no equip petit"},
            {"Camp": "centre_tipus", "Exemple": "Fàbrica", "Nota": "Evita centres identificables"},
            {"Camp": "canal", "Exemple": "Mòbil-QR", "Nota": "Participació per canal"},
            {"Camp": "escala_*", "Exemple": "1-5", "Nota": "Benestar, càrrega, comunicació, reconeixement"},
            {"Camp": "comentari_obert", "Exemple": "text lliure", "Nota": "Variat, amb soroll i faltes"},
            {"Camp": "tema_real", "Exemple": "Torns", "Nota": "Etiqueta oculta per validar la classificació"},
        ]
    )
    st.dataframe(esquema, width="stretch", hide_index=True)

    ui.callout(
        "Prohibit",
        "Pujar tokens o claus al repositori, compartir el token de Typeform fora de l'equip, carregar "
        "dades reals de Damm a qualsevol eina (LLMs inclosos) o intentar accedir a workspaces d'altres equips.",
        "danger",
    )


# ---------------------------------------------------------------------------
# Pàgina: Guió de demo
# ---------------------------------------------------------------------------


def pagina_guio() -> None:
    ui.seccio(
        "Suport per a l'equip",
        "Guió de demo (3 minuts)",
        "La demo ha de funcionar encara que falli internet: aquesta app corre en local.",
    )

    guio = pd.DataFrame(
        [
            {"Temps": "0:00-0:25", "Qui": "Jordi", "Què es diu": "El problema: escoltem, però no sempre sentim a tothom. Planta i logística responen menys i els comentaris s'analitzen tard.", "Què es mostra": "Inici"},
            {"Temps": "0:25-0:55", "Qui": "Iker", "Què es mostra": "Nova consulta", "Què es diu": "RRHH descriu la necessitat en llenguatge natural. La IA proposa 4 preguntes en 2 minuts."},
            {"Temps": "0:55-1:15", "Qui": "Iker", "Què es mostra": "Validació + QR", "Què es diu": "RRHH edita i aprova. Res es publica sense control humà. El QR arriba a planta."},
            {"Temps": "1:15-1:45", "Qui": "Izan", "Què es mostra": "Participació", "Què es diu": "Aquesta és la clau: no amaguem qui falta. El sistema avisa que planta i logística estan per sota."},
            {"Temps": "1:45-2:25", "Qui": "Miguel", "Què es mostra": "Anàlisi", "Què es diu": "Els comentaris es converteixen en temes. Torns i descansos emergeixen al segon període. Senyals febles i límits explicats."},
            {"Temps": "2:25-2:45", "Qui": "Jordi", "Què es mostra": "Insights", "Què es diu": "Dues accions concretes i una nova microconsulta de seguiment. El cicle es tanca."},
            {"Temps": "2:45-3:00", "Qui": "Tothom", "Què es mostra": "Privacitat", "Què es diu": "Sempre agregat, llindar mínim, PII eliminada, cap perfil individual. La IA proposa, les persones decideixen."},
        ]
    )
    st.dataframe(guio, width="stretch", hide_index=True)

    st.markdown("##### Pla B si falla la demo")
    ui.callout(
        "Sempre tenir un vídeo",
        "Enregistreu un vídeo de 2-3 minuts amb el flux complet abans de diumenge al matí. Si falla "
        "internet o el projector, es reprodueix el vídeo i es continua el relat.",
        "warn",
    )

    st.markdown("##### Preguntes probables del jurat")
    with st.expander("Com eviteu que la IA publiqui preguntes inadequades?"):
        st.markdown(
            "La IA només proposa. Hi ha una pantalla de validació humana obligatòria i una llista de "
            "temes prohibits que s'aplica abans de generar. Sense la casella d'aprovació, el botó de "
            "publicar està desactivat."
        )
    with st.expander("Com garantiu l'anonimat si mostreu cites?"):
        st.markdown(
            "Les cites passen per un filtre de PII i només es mostren si el segment supera el llindar. "
            "No es mostra mai el text d'una resposta individual associada a una persona."
        )
    with st.expander("Això és només una enquesta?"):
        st.markdown(
            "No: és un cicle. Necessitat → consulta adaptada → participació → anàlisi → visualització → "
            "acció → nova consulta. La diferència és que la consulta següent neix de la resposta anterior."
        )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

PAGINA_FN = {
    "Inici": pagina_inici,
    "Nova consulta": pagina_nova_consulta,
    "Participació": pagina_participacio,
    "Anàlisi": pagina_analisi,
    "Insights i accions": pagina_insights,
    "Privacitat": pagina_privacitat,
    "Guió de demo": pagina_guio,
}

PAGINA_FN[st.session_state.nav]()

st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#9A8A82;font-size:0.75rem'>"
    "EscoltDamm · prototip de demo "
    "</div>",
    unsafe_allow_html=True,
)