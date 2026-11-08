# Contrato API · Escolta Damm

Este documento define cómo se conecta el **frontend** (Streamlit, en este
dispositivo) con el **backend** (generación con IA, Typeform, análisis y datos).
El frontend funciona ahora en **modo mock**; cuando exista backend, solo cambia
la implementación de `api_client.py`, no la interfaz.

---

## 1. Convenciones

- Base URL: `${ESCOLTA_API_URL}/v1`
- Autenticación: `Authorization: Bearer ${ESCOLTA_API_KEY}` (nunca en el código).
- Formato: JSON UTF-8.
- Fechas: ISO 8601 (`2026-11-07T18:30:00Z`).
- Idioma de los textos generados: catalán (configurable).
- Modo: `ESCOLTA_MODE=mock|api` en `.env`.
- Paginación: `?limit=50&cursor=...` cuando aplique.
- Idempotencia: cabecera `Idempotency-Key` en POST de publicación.

### Enumeraciones

| Campo | Valores |
| --- | --- |
| `collective` | `plant`, `logistics`, `commercial`, `office`, `manager` |
| `channel` | `mobile_qr`, `email`, `nfc` |
| `tone` | `close_direct`, `neutral_formal`, `motivating` |
| `question.type` | `scale_1_5`, `single_choice`, `yes_no`, `open_text` |
| `status` | `draft`, `approved`, `published`, `closed` |
| `segment.status` | `adequate`, `overrepresented`, `underrepresented`, `suppressed` |
| `impact` / `effort` | `low`, `medium`, `high` |

---

## 2. Flujo completo

```
RRHH                Frontend (Streamlit)              Backend / IA                 Typeform
 │                        │                               │                           │
 │ define necesidad ─────►│ POST /consultations/draft ───►│ genera propuesta          │
 │                        │◄──────────── draft ───────────│                           │
 │ edita y aprueba ──────►│ POST /{id}/approve ──────────►│ valida + versiona         │
 │                        │ POST /{id}/publish ──────────►│ crea formulario ─────────►│
 │                        │◄──── url + qr + form_id ──────│                           │
 │ responde (QR/móvil) ──────────────────────────────────────────────────────────────►│
 │                        │                               │◄──── webhook respuesta ───│
 │                        │ GET /{id}/participation ─────►│ agrega + umbral           │
 │                        │ GET /{id}/analysis ──────────►│ temas + sentimiento       │
 │                        │ GET /{id}/insights ──────────►│ recomendaciones           │
 │ decide y actúa ◄───────│ dashboard + plan              │                           │
 └ nueva microconsulta ──►│ POST /consultations/draft ...  │                           │
```

---

## 3. Endpoints

### 3.1. Crear borrador de consulta

`POST /consultations/draft`

```json
{
  "objective": "Vull entendre com està afectant el nou sistema de torns a planta.",
  "collective": "plant",
  "context": "Nou sistema de torns · octubre 2026",
  "max_minutes": 2,
  "forbidden_topics": ["salary", "health"],
  "tone": "close_direct",
  "channel": "mobile_qr",
  "language": "ca"
}
```

Respuesta `201`:

```json
{
  "id": "cns_8c6899",
  "status": "draft",
  "created_at": "2026-11-07T16:20:00Z",
  "title": "Com vius els torns?",
  "intro": "Volem saber com ho estàs vivint de veritat...",
  "collective": "plant",
  "channel": "mobile_qr",
  "tone": "close_direct",
  "estimated_minutes": 2,
  "questions": [
    {
      "id": "q1",
      "text": "Com et sents de benestar general a la feina aquestes últimes setmanes?",
      "type": "scale_1_5",
      "options": [],
      "required": true,
      "logic": null
    },
    {
      "id": "q2",
      "text": "Quin canvi concret en els torns t'ajudaria més?",
      "type": "open_text",
      "options": [],
      "required": false,
      "logic": "shown_if(q1 <= 2)"
    }
  ],
  "trace": {
    "model": "gpt-4o-mini",
    "rules": ["forbidden_topics_filtered", "max_questions_by_duration"],
    "forbidden_topics": ["salary", "health"]
  }
}
```

**Guardrails:** la respuesta es siempre `draft`; el backend no publica en este paso.

---

### 3.2. Aprobar con control humano

`POST /consultations/{id}/approve`

```json
{
  "questions": [
    {
      "id": "q1",
      "text": "Com et sents de benestar general aquestes últimes setmanes?",
      "type": "scale_1_5",
      "options": [],
      "required": true,
      "logic": null
    }
  ],
  "approved_by": "human_izan",
  "approved_at": "2026-11-07T16:35:00Z",
  "changes_summary": "S'ha eliminat una pregunta i s'ha reescrit la introducció."
}
```

Respuesta `200`:

```json
{
  "id": "cns_8c6899",
  "status": "approved",
  "version": 2,
  "approved_by": "human_izan",
  "approved_at": "2026-11-07T16:35:00Z"
}
```

Regla: sin `approved_by` humano, `publish` devuelve `409 human_approval_required`.

---

### 3.3. Publicar en Typeform

`POST /consultations/{id}/publish`

```json
{
  "provider": "typeform",
  "channel": "mobile_qr",
  "expires_at": "2026-11-21T23:59:59Z"
}
```

Respuesta `201`:

```json
{
  "id": "cns_8c6899",
  "status": "published",
  "provider": "typeform",
  "form_id": "abc123XYZ",
  "url": "https://form.typeform.com/to/abc123XYZ",
  "qr_url": "https://api.escolta.local/v1/qr/cns_8c6899.png",
  "published_at": "2026-11-07T16:40:00Z",
  "expires_at": "2026-11-21T23:59:59Z"
}
```

Errores: `502 typeform_unavailable` → el frontend ofrece modo mock y QR local.

---

### 3.4. Participación y representatividad

`GET /consultations/{id}/participation?period=2026-T4&threshold=8`

```json
{
  "period": "2026-T4",
  "threshold": 8,
  "overall": {
    "responses": 640,
    "population": 3600,
    "response_rate_pct": 17.8,
    "margin_error_pp": 3.5,
    "confidence": 0.95
  },
  "segments": [
    {
      "collective": "plant",
      "responses": 126,
      "population": 1400,
      "response_rate_pct": 9.0,
      "sample_share_pct": 19.7,
      "population_share_pct": 38.9,
      "deviation_pp": -19.2,
      "margin_error_pp": 8.3,
      "status": "underrepresented",
      "visible": true
    },
    {
      "collective": "manager",
      "responses": 135,
      "population": 200,
      "response_rate_pct": 67.5,
      "sample_share_pct": 21.1,
      "population_share_pct": 5.6,
      "deviation_pp": 15.5,
      "margin_error_pp": 3.2,
      "status": "overrepresented",
      "visible": true
    }
  ],
  "channels": [
    { "channel": "mobile_qr", "responses": 402 },
    { "channel": "email", "responses": 168 },
    { "channel": "nfc", "responses": 70 }
  ],
  "alerts": [
    "Planta: 126 respostes (9.0% de resposta, 19.2 pp per sota).",
    "Logística: 69 respostes (8.6% de resposta, 15.2 pp per sota)."
  ],
  "privacy": {
    "aggregated": true,
    "suppressed_segments": [],
    "individual_responses_exposed": false
  }
}
```

---

### 3.5. Análisis

`GET /consultations/{id}/analysis?period=2026-T4&collectives=plant,logistics&min_segment=8`

```json
{
  "period": "2026-T4",
  "filters": { "collectives": ["plant", "logistics"], "min_segment": 8 },
  "themes": [
    {
      "theme": "shifts",
      "label": "Torns i horaris",
      "responses": 60,
      "share_pct": 9.4,
      "avg_sentiment": -0.42,
      "avg_wellbeing": 2.6,
      "keywords": ["torn", "torns", "rotacio", "calendari"]
    }
  ],
  "evolution": [
    { "theme": "shifts", "t3_share_pct": 7.7, "t4_share_pct": 11.1, "delta_pp": 3.4 }
  ],
  "emerging": [
    { "theme": "shifts", "label": "Torns i horaris", "delta_pp": 3.4, "direction": "up" }
  ],
  "weak_signals": [
    {
      "theme": "wellbeing",
      "label": "Salut i seguretat",
      "responses": 12,
      "share_pct": 3.0,
      "avg_sentiment": -0.35,
      "delta_pp": 1.9
    }
  ],
  "quotes": [
    {
      "theme": "shifts",
      "text": "Els canvis de torn amb pocs dies d'antelació fan molt difícil organitzar-se.",
      "sentiment": -1,
      "pii_redacted": true
    }
  ],
  "quality": {
    "theme_accuracy_pct": 99.1,
    "sentiment_accuracy_pct": 94.4,
    "coverage_pct": 77.3,
    "method": "keyword_rules_v1"
  },
  "privacy": {
    "aggregated": true,
    "threshold": 8,
    "suppressed_segments": [],
    "pii_redaction": true
  },
  "limits": [
    "La classificació és per paraules clau; no infereix causalitat.",
    "Els segments per sota del llindar no es mostren.",
    "El marge d'error és orientatiu i depèn de la mostra sintètica."
  ]
}
```

**Invariantes de privacidad (obligatorias en todas las respuestas):**

1. `aggregated: true` siempre.
2. Ningún `response_id` ni texto de una respuesta individual.
3. Los segmentos con `n < threshold` no aparecen o aparecen como `suppressed` sin datos.
4. `pii_redaction: true` en cualquier texto libre.
5. No se devuelven campos que permitan inferir personas concretas.

---

### 3.6. Insights y recomendaciones

`GET /consultations/{id}/insights`

```json
{
  "recommendations": [
    {
      "priority": 1,
      "theme": "shifts",
      "label": "Torns i horaris",
      "action": "Revisar la planificació de torns amb 2 setmanes d'antelació i limitar els canvis d'última hora.",
      "owner": "People + Caps de planta",
      "impact": "high",
      "effort": "medium",
      "support": "60 respostes · 9.4% · sentiment -0.42",
      "human_validation_required": true
    }
  ],
  "follow_up": {
    "title": "Seguiment: Torns i horaris",
    "reason": "«Torns i horaris» ha passat del 7.7% al 11.1% de les respostes (+3.4 pp).",
    "questions": [
      "Els canvis de torn d'aquest mes s'han comunicat amb prou antelació?",
      "Quin aspecte del calendari et dificulta més la setmana?"
    ]
  },
  "action_plan": [
    {
      "horizon": "0-30 days",
      "action": "Revisar la planificació de torns...",
      "owner": "People + Caps de planta",
      "indicator": "Taxa de resposta i valoració del tema"
    }
  ]
}
```

---

### 3.7. Webhook de Typeform

`POST /webhooks/typeform` (servidor a servidor, sin Bearer de usuario)

```json
{
  "event_id": "evt_123",
  "form_id": "abc123XYZ",
  "response_id": "resp_456",
  "submitted_at": "2026-11-08T09:12:00Z",
  "answers": [
    { "field": "q1", "type": "scale_1_5", "value": 2 },
    { "field": "q2", "type": "open_text", "value": "Els canvis arriben tard..." }
  ],
  "metadata": { "channel": "mobile_qr", "period": "2026-T4" }
}
```

Procesamiento:

1. Verificar firma/secreto del webhook.
2. Deduplicar por `response_id` (idempotencia).
3. Redactar PII del texto libre **antes** de persistir.
4. Guardar solo campos agregables (sin identificar a la persona).
5. Responder `202 Accepted`.

---

### 3.8. Salud del servicio

`GET /health`

```json
{ "status": "ok", "mode": "api", "typeform": "ok", "llm": "ok", "version": "1.0.0" }
```

---

## 4. Mapeo con el prototipo actual

| Contrato (inglés) | `Applicación/` (catalán) | Módulo |
| --- | --- | --- |
| `title` | `titol` | `Encuesta.generar_consulta` |
| `intro` | `intro` | `Encuesta.generar_consulta` |
| `estimated_minutes` | `temps_estimat` | `Encuesta.generar_consulta` |
| `questions[].text` | `preguntes[].text` | `Encuesta.generar_consulta` |
| `questions[].type` | `preguntes[].tipus` | `Encuesta.generar_consulta` |
| `questions[].logic` | `preguntes[].condicional` | `Encuesta.generar_consulta` |
| `form_id`, `url`, `qr_url` | `enllac`, `qr` | `Encuesta.publica_consulta` |
| `segments[]` | `taula_participacio()` | `analisis.py` |
| `themes[]`, `evolution[]` | `resum_temes()`, `evolucio_temes()` | `analisis.py` |
| `emerging[]`, `weak_signals[]` | `temes_emergents()`, `senyals_febles()` | `analisis.py` |
| `recommendations[]`, `follow_up` | `recomanacions()`, `proposta_seguiment()` | `analisis.py` |
| `quality` | `precisio_classificacio()` | `analisis.py` |
| `privacy.threshold` | `st.session_state.llindar` | `app.py` |

`api_client.py` (pendiente, tarea de Iker) traducirá entre ambos mundos y
elegirá mock o API según `ESCOLTA_MODE`.

---

## 5. Errores

| Código | `error` | Cuándo |
| --- | --- | --- |
| 400 | `invalid_request` | Falta un campo o tipo incorrecto |
| 401 | `unauthorized` | Token ausente o inválido |
| 403 | `forbidden` | El token no tiene permiso sobre la consulta |
| 404 | `not_found` | Consulta o formulario inexistente |
| 409 | `human_approval_required` | Se intenta publicar sin aprobación humana |
| 422 | `privacy_violation` | Se pide un segmento por debajo del umbral |
| 429 | `rate_limited` | Límite de API (respetar `Retry-After`) |
| 502 | `typeform_unavailable` | Typeform no responde |
| 503 | `llm_unavailable` | Modelo no disponible; usar fallback determinista |

Formato de error:

```json
{
  "error": "privacy_violation",
  "message": "El segment 'plant/night' té 3 respostes, per sota del llindar de 8.",
  "request_id": "req_abc123"
}
```

---

## 6. Límites y buenas prácticas

- Typeform: respetar los límites del plan; usar `Retry-After` y backoff exponencial.
- LLM: cachear propuestas por `hash(objective + collective + context)`.
- Respuestas: procesar el webhook en cola, no en la petición HTTP.
- Secretos: solo en `.env`; rotar el token si se filtra.
- Datos: nunca enviar datos reales al LLM; solo sintéticos o anonimizados.
- Logs: no registrar textos libres completos ni tokens.
