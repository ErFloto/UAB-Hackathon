# EscoltDamm

Prototip per al repte d'Estrella Damm de l'UAB The Hack! 2026. La idea és que RRHH pugui
escriure què vol saber ("com portem els canvis de torn?"), que el sistema proposi una
microconsulta, que una persona la revisi i la publiqui, i que després es vegi un resum
agregat amb algunes accions possibles.

Totes les dades són sintètiques. No hi ha cap dada real de Damm ni de cap treballador, i
això no és una eina per controlar ningú.

## Posar-ho en marxa

Cal Python 3.10 o més nou. Des de l'arrel del repositori, a Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r "Applicación\requirements.txt"
cd "Applicación"
streamlit run app.py
```

S'obre a `http://localhost:8501`. Si ja tens l'entorn virtual creat, només cal activar-lo
i executar l'última comanda.

Perquè el QR funcioni des d'un mòbil (ha d'estar a la mateixa xarxa), arrenca-ho així i
posa la IP de l'ordinador a `PUBLIC_URL`:

```powershell
streamlit run app.py --server.address 0.0.0.0
```

## Configuració

Copia `.env.example` com a `.env` dins d'`Applicación/` i omple'l. El `.env` no es puja
mai al repositori. Les variables:

- `ESCOLTA_MODE`: `mock` (per defecte, no necessita xarxa) o `api`, que fa servir la IA.
- `ESCOLTA_API_URL` i `ESCOLTA_API_KEY`: la passarel·la d'IA, compatible amb OpenAI. Només
  fan falta amb `api`.
- `PRIVACY_THRESHOLD_PCT`: el llindar de privacitat, com a percentatge de la població de
  cada col·lectiu (entre 1 i 10, per defecte 4). Veure l'apartat de privacitat.
- `PUBLIC_URL`: l'adreça que porten el QR i l'enllaç. Per provar des del mòbil, la IP local
  (per exemple `http://192.168.1.35:8501`).
- `ADMIN_PIN`: el PIN del panell de RRHH, només números. Si no n'hi ha, el panell queda
  bloquejat. Després de 5 intents fallats s'espera un minut.
- `TEAMS_WEBHOOK_URL`: opcional. Sense ella, la publicació a Teams és simulada.

Sense configurar res més que el PIN, tot funciona en mode `mock`.

## Què hi ha a l'aplicació

El panell de RRHH té aquestes pàgines: Inici, Nova consulta (de la necessitat a l'enllaç i
el QR, passant per l'aprovació humana), Participació (qui respon i qui no), Anàlisi (temes,
sentiment i evolució), Insights i accions, Privacitat i Guió de demo.

La gent que respon no entra al panell: ho fa des de l'enllaç o el QR, que obre només el
formulari (`?respondre=true`). Hi ha un QR per col·lectiu, i és el QR escanejat el que
decideix a quin col·lectiu va la resposta; ningú s'identifica.

## Fitxers

```
Applicación/
├── app.py          navegació, PIN d'admin, panell i formulari públic
├── Encuesta.py     generació de les consultes
├── ia.py           resums i accions amb IA
├── datos.py        dades sintètiques i classificació per paraules clau
├── analisis.py     llindar de privacitat, representativitat, temes i tendències
├── respostes.py    desa les respostes reals en un CSV local
├── pii.py          treu dades personals dels comentaris
├── qrs.py          codis QR per col·lectiu
├── teams.py        targeta per a Teams
├── Interfaz.py     estils
└── .env.example
```

`entrenament_nb.py` és un experiment amb Naive Bayes que ara no s'utilitza.

## Teams

Teams ha retirat els webhooks antics, i ara es fa amb Workflows (Power Automate). La
publicació genera la targeta que s'enviaria, però en aquesta demo va en mode simulat perquè
no teníem un compte de Microsoft 365 per provar-ho. Amb una URL de Workflows a
`TEAMS_WEBHOOK_URL`, el mateix botó l'envia de veritat.

## Què fa la IA

Proposa preguntes per a la consulta, resumeix els temes i suggereix accions, i opcionalment
ajuda a detectar noms propis als comentaris. No publica res ni decideix: la consulta l'ha
d'aprovar una persona abans de sortir, i les accions també les decideix una persona.

## Privacitat

- Les respostes són anònimes: no es desa nom, IP ni dispositiu, només un identificador
  aleatori, el col·lectiu, el canal i les respostes.
- Abans de desar un comentari se n'eliminen correus, telèfons, usuaris, URL, DNI/NIE, IBAN
  i noms propis.
- Només es mostren resultats agregats. Un col·lectiu amb menys respostes que el llindar
  s'oculta del tot, també dels totals, perquè no es pugui deduir restant. El llindar és un
  percentatge de la població del col·lectiu, però mai baixa de 8 respostes.
- Les respostes caduquen als 90 dies, i el formulari públic ho explica a qui respon.

## Seguretat

El `.env` no es puja al repositori i no hi ha cap clau al codi. El panell de RRHH demana
PIN. Abans de fer públic el repositori cal revisar l'historial de commits.