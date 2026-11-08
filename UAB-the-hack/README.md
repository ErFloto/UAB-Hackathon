# UAB The Hack! 2026 · Repte Estrella Damm

**EscoltDamm** — una plataforma d'escolta activa amb IA per mesurar el clima laboral
de manera àgil, contínua i representativa. Del problema a l'acció en un sol cicle.

> Prototip de demo. Totes les dades són **100% sintètiques**. No és una eina de
> vigilància ni avalua persones.

## Equip

| Persona | Rol |
| --- | --- |
| Izan Flores Tortosa | Dades sintètiques, privacitat i QA |
| Miguel Simon Ramis | IA, anàlisi i insights |
| Iker Peña Garcia | Frontend, integració i demo tècnica |
| Jordi Vivas Sakuta | Producte, Typeform/M365 i pitch |

## En aquest repositori

- [`docs/CONTRATO_API.md`](docs/CONTRATO_API.md) — contracte entre frontend i backend.
- [`Applicación/`](Applicación/) — prototip Streamlit executable.
- [`.env.example`](.env.example) — variables necessàries (sense valors).

## Executar la demo

```powershell
.\.venv\Scripts\Activate.ps1
cd "Applicación"
streamlit run app.py
```

Més detalls a [`Applicación/README.md`](Applicación/README.md).

## El cicle

Necessitat → consulta adaptada → participació → respostes → anàlisi →
visualització → acció → nova consulta.

## Regles no negociables

- Només dades sintètiques.
- Resultats sempre agregats i amb llindar mínim.
- Eliminació automàtica de dades identificatives.
- La IA proposa; les persones validen i decideixen.
- Cap token ni secret al repositori.
