# Escolta · prototip de demo (Streamlit)

Plataforma d'escolta activa per al repte **Estrella Damm · UAB The Hack! 2026**.
Converteix una necessitat de RRHH en una microconsulta adaptada, en participació
representativa i en insights i accions, amb anonimat i control humà.

> Totes les dades són **100% sintètiques**. No hi ha cap dada real de Damm ni de
> persones treballadores. Aquest prototip no és una eina de vigilància.

## Executar-ho en aquest dispositiu (Windows)

Ja hi ha un entorn virtual creat a l'arrel del repositori.

```powershell
# Des de l'arrel del repositori
.\.venv\Scripts\Activate.ps1
cd "Applicación"
streamlit run app.py
```

Si l'entorn no existeix:

```powershell
python -m venv .venv
.\.venv\Scripts\pip.exe install -r "Applicación\requirements.txt"
```

S'obre a `http://localhost:8501`.

## Pàgines

| Pàgina | Què demostra |
| --- | --- |
| Inici | El problema, el cicle de 8 passos i els tres escenaris de demo |
| Nova consulta | Necessitat en llenguatge natural → proposta IA → edició → aprovació humana → QR/enllaç |
| Participació | Representativitat per col·lectiu, canals, marge d'error i alertes |
| Anàlisi | Temes, sentiment, evolució, temes emergents, senyals febles i PII |
| Insights i accions | Recomanacions prioritzades, pla 30/60/90 i microconsulta de seguiment |
| Privacitat | Llindar mínim, esquema de dades, checklist i bones pràctiques |
| Guió de demo | Repartiment dels 3 minuts, pla B i preguntes del jurat |

## Estructura

```
Applicación/
├── app.py             # entrada Streamlit i navegació
├── Interfaz.py        # CSS i components visuals
├── Encuesta.py        # generació de consultes + publicació simulada (QR)
├── datos.py           # dades sintètiques, PII, classificació per paraules clau
├── analisis.py        # representativitat, temes, tendències, recomanacions
├── requirements.txt
└── .streamlit/config.toml
```

## Mode mock vs. mode API

Ara mateix tot funciona en **mode mock** (determinista, sense xarxa). El
contracte per connectar el frontend amb el backend real és a
[`../docs/CONTRATO_API.md`](../docs/CONTRATO_API.md).

Punts de substitució:

- `Encuesta.generar_consulta()` → crida al servei de generació (LLM + regles).
- `Encuesta.publica_consulta()` → `POST /v1/forms` de Typeform.
- `datos.generar_respostes()` → lectura de respostes reals de Typeform.
- `analisis.*` → servei d'anàlisi (el mateix contracte de sortida).

## Privacitat implementada a la demo

- Llindar mínim configurable (5-10 respostes per segment).
- Només resultats agregats; mai respostes individuals.
- Redacció automàtica de correus, telèfons, usuaris i noms en contextos explícits.
- Cap perfil individual ni inferència sobre persones.
- Control humà obligatori abans de publicar i abans d'actuar.

## Seguretat

- `.env` i `.env.example` (sense valors) al `.gitignore`.
- Cap token al codi, al repositori ni a les diapositives.
- Si es publica el repositori, revisar l'historial de commits.
