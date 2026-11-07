# Reparto de tareas · Escolta Damm (UAB The Hack! 2026)

**Equipo:** Izan Flores Tortosa · Miguel Simon Ramis · Iker Peña Garcia · Jordi Vivas Sakuta
**Reto:** Estrella Damm — plataforma de escucha activa con IA
**Fecha:** 7–8 de noviembre de 2026 · Escola d'Enginyeria UAB
**Entrega:** domingo antes de las 14:00 · Demo: 3 minutos

---

## 1. Resumen ejecutivo

El objetivo no es hacer «una encuesta más», sino un **ciclo completo**:

> Necesidad → consulta adaptada → participación → respuestas → análisis → visualización → acción → nueva consulta

El frontend se construye **en este dispositivo** (Streamlit + Python) y ya está
funcionando con datos sintéticos y análisis determinista. El resto del equipo
trabaja en paralelo sobre el mismo contrato de datos, de modo que cualquier
módulo se pueda sustituir por el servicio real sin rehacer la interfaz.

**Estado actual del repositorio (hecho):**

- App Streamlit completa en `Applicación/` con las 7 pantallas del ciclo.
- 640 respuestas sintéticas, 2 períodos, 5 colectivos, participación desigual y sesgos intencionados.
- Generación de microconsultas + validación humana + publicación simulada con QR.
- Dashboard de representatividad con margen de error y alertas por colectivo.
- Análisis de temas, sentimiento, evolución, temas emergentes, señales débiles y PII.
- Recomendaciones priorizadas, plan 30/60/90 y microconsulta de seguimiento.
- Documento de contrato API, `.env.example` y `.gitignore`.
- Precisión de la demo: ~99% de temas y ~95% de sentimiento frente a la etiqueta oculta.

---

## 2. Reparto por persona

### Iker Peña — Frontend, integración y demo técnica (este dispositivo)

**Misión:** que la demo sea impecable y que el frontend pueda hablar con el backend real sin cambios de diseño.

| Prioridad | Tarea | Entregable | Archivos |
| --- | --- | --- | --- |
| P0 | Revisar la UI completa (responsive, estados vacíos, textos en catalán, contraste) | App pulida y sin errores en las 7 pantallas | `app.py`, `Interfaz.py` |
| P0 | Crear capa `api_client.py` con `ESCOLTA_MODE=mock/api` | El frontend usa mock por defecto y API si hay URL | `api_client.py` |
| P0 | Integrar publicación real de Typeform (`POST /v1/forms`) | Enlace y QR reales; si falla, fallback mock | `Encuesta.py`, `api_client.py` |
| P0 | Grabar vídeo de seguridad de 2–3 min con el flujo completo | `docs/demo-backup.mp4` (o enlace) | — |
| P1 | Añadir formulario móvil de respuesta simulado para la demo | Pantalla «responder» sin depender de Typeform | `app.py` |
| P1 | Exportar insights a CSV y botón de impresión/PDF | Descarga desde la pantalla de insights | `app.py` |
| P2 | Selector de idioma CA/ES | Bonus de multiidioma | `Interfaz.py` |

**Definición de hecho:** `streamlit run app.py` arranca en limpio, todas las pantallas cargan sin excepción, el flujo necesidad → QR → análisis → recomendación se puede hacer en menos de 3 minutos y existe vídeo de respaldo.

**No hace:** cambiar el esquema de datos ni el motor de análisis sin acordarlo con Izan/Miguel.

---

### Izan Flores — Datos sintéticos, privacidad y QA de datos

**Misión:** que los datos sean creíbles, reproducibles y demuestren que el sistema detecta sesgos sin vulnerar la privacidad.

| Prioridad | Tarea | Entregable | Archivos |
| --- | --- | --- | --- |
| P0 | Congelar el dataset v1: 300–1.000 respuestas, ≥2 períodos, 5 colectivos | CSV reproducible + seed documentada | `datos.py` |
| P0 | Validar el esquema (rangos, nulos, tipos, coherencia de canal/colectivo) | Script `validar_datos.py` con salida OK/KO | `validar_datos.py` |
| P0 | Ampliar la redacción de PII (correos, teléfonos, usuarios, nombres en contexto) | Tests + tabla de casos | `datos.py`, `tests/` |
| P0 | Garantizar el umbral mínimo y la supresión de segmentos pequeños | Comprobación automática por segmento | `analisis.py` (revisión) |
| P1 | Documentar sesgos intencionados y límites del dataset | Sección en `docs/DATOS.md` | `docs/DATOS.md` |
| P1 | QA de los escenarios A, B y C con datos | Checklist firmada | `docs/QA.md` |
| P2 | Generar una segunda versión del dataset para el vídeo | `data/respostes_v2.csv` (ignorado por git) | — |

**Definición de hecho:** cualquier persona puede regenerar los datos con la misma seed, ninguna respuesta es identificable, ningún segmento por debajo del umbral se muestra y los tres escenarios se pueden explicar con los datos.

---

### Miguel Simon — Motor de IA, análisis e insights

**Misión:** convertir comentarios en temas, tendencias y recomendaciones explicables, con límites claros y sin caja negra.

| Prioridad | Tarea | Entregable | Archivos |
| --- | --- | --- | --- |
| P0 | Revisar clasificación de temas y sentimiento; mantener precisión >90% | Métricas y matriz de confusión | `analisis.py`, `datos.py` |
| P0 | Temas emergentes, señales débiles y evolución entre períodos | Tarjetas y umbrales documentados | `analisis.py` |
| P0 | Recomendaciones priorizadas + propuesta de seguimiento | Reglas con impacto/esfuerzo/responsable | `analisis.py` |
| P0 | Diseñar el prompt y el JSON schema para el LLM real (generación y resumen) | `docs/PROMPTS.md` + ejemplos | `docs/PROMPTS.md` |
| P1 | Guardrails: la IA nunca publica, nunca decide, nunca infiere personas | Lista de comprobación | `docs/PROMPTS.md` |
| P1 | Evaluación: cobertura, precisión, sesgos, límites y causalidad | Informe corto para el jurado | `docs/EVALUACION.md` |
| P2 | Embeddings o clustering real (si sobra tiempo); fallback Ollama local | Servicio opcional | `analisis.py` |

**Definición de hecho:** el jurado puede preguntar «¿por qué este tema?» y la respuesta está en la pantalla (palabras clave, conteo, sentimiento y límites). Las recomendaciones son propuestas, no decisiones automáticas.

---

### Jordi Vivas — Producto, Typeform/M365, representatividad y pitch

**Misión:** que la solución hable el idioma de People/RRHH y que la demo convenza en 3 minutos.

| Prioridad | Tarea | Entregable | Archivos |
| --- | --- | --- | --- |
| P0 | Validar la narrativa con mentores de People: problema, usuarios, criterios de éxito | Guion de producto de 1 página | `docs/PRODUCTO.md` |
| P0 | Configurar el workspace de Typeform y el token (solo en `.env`) | Formulario real + límites de API | `.env.example` |
| P0 | Definir la estrategia de representatividad (población, tasas, alertas) | Tabla de referencia y mensajes | `docs/PRODUCTO.md` |
| P0 | Preparar el pitch de 3 minutos y las diapositivas | `docs/PITCH.md` + slides | `docs/` |
| P0 | Checklist de entrega y ética | `docs/CHECKLIST.md` | `docs/CHECKLIST.md` |
| P1 | Historia de integración M365/Teams (bonus) | 3 diapositivas + alcance MVP | `docs/M365.md` |
| P1 | Grabar el vídeo de respaldo con Iker | Vídeo de 2–3 min | `docs/demo-backup.mp4` |
| P2 | Revisar README y `.env.example` | Documentación final | raíz |

**Definición de hecho:** el pitch cabe en 3 minutos, cada persona sabe qué decir, existe vídeo de respaldo y el checklist está completo.

---

## 3. Cronograma de 32 horas

| Franja | Iker (frontend) | Izan (datos/privacidad) | Miguel (IA/análisis) | Jordi (producto/pitch) |
| --- | --- | --- | --- | --- |
| Sáb 09:00–10:30 | Entender reto + mentorías | Entender reto + mentorías | Entender reto + mentorías | Entender reto + mentorías |
| Sáb 10:30–12:00 | Wireframes + contrato API | Esquema + dataset v1 | Motor de temas v1 | Narrativa + Typeform |
| Sáb 12:00–14:00 | UI del flujo | Generador + sesgos | Clasificación + sentimiento | Representatividad |
| Sáb 14:00–15:00 | Comida + demo interna de 10 min | Comida | Comida | Comida |
| Sáb 15:00–19:00 | Pantallas de participación/análisis | PII + validación | Emergentes + señales débiles | Typeform real + M365 |
| Sáb 19:00–20:00 | **Checkpoint 1: flujo completo con mocks** | **Checkpoint 1** | **Checkpoint 1** | **Checkpoint 1** |
| Sáb 20:00–00:00 | Integración API + QR | QA escenarios A/B/C | Recomendaciones + límites | Pitch v1 + vídeo |
| Dom 00:00–06:00 | **Dormir** | **Dormir** | **Dormir** | **Dormir** |
| Dom 06:00–09:00 | Integración final + bugs | Dataset final congelado | Métricas finales | Ensayo + slides |
| Dom 09:00–10:00 | **Checkpoint 2: demo congelada** | **Checkpoint 2** | **Checkpoint 2** | **Checkpoint 2** |
| Dom 10:00–12:00 | Vídeo de respaldo | Revisión de privacidad | Revisión de límites | Ensayo completo |
| Dom 12:00–13:30 | Correcciones menores | Checklist datos | Checklist análisis | Checklist entrega |
| Dom 13:30–14:00 | **Entrega** | **Entrega** | **Entrega** | **Entrega** |

**Regla de oro:** a las 10:00 del domingo se congela la demo. A partir de ahí solo se corrigen fallos, no se añaden funcionalidades.

---

## 4. Puntos de sincronización y contrato de integración

| Hito | Hora | Criterio de aceptación | Responsable |
| --- | --- | --- | --- |
| Contrato API cerrado | Sáb 12:00 | `docs/CONTRATO_API.md` revisado por los 4 | Iker + Miguel |
| Dataset v1 | Sáb 12:00 | 300+ respuestas, 2 períodos, 5 colectivos, seed fija | Izan |
| Flujo completo con mocks | Sáb 19:00 | Necesidad → propuesta → aprobación → QR → dashboard | Iker |
| Typeform real | Sáb 22:00 | Formulario creado por API y respuestas recuperadas | Jordi + Iker |
| Demo congelada | Dom 10:00 | Sin errores en las 7 pantallas + vídeo grabado | Todos |
| Ensayo final | Dom 12:00 | Pitch de 3:00 ±10 s, sin leer | Jordi |

**Propiedad de archivos (evitar conflictos):**

| Archivo | Dueño | Revisores |
| --- | --- | --- |
| `Applicación/app.py` | Iker | Jordi |
| `Applicación/Interfaz.py` | Iker | Jordi |
| `Applicación/Encuesta.py` | Iker | Miguel |
| `Applicación/datos.py` | Izan | Miguel |
| `Applicación/analisis.py` | Miguel | Izan |
| `docs/` y `README.md` | Jordi | Todos |

Si alguien necesita tocar un archivo de otro, lo pide en el grupo y hace un cambio pequeño; nada de reescribir el módulo entero a última hora.

---

## 5. Reglas del equipo

1. **No datos reales.** Todo sintético. Ni nombres, ni correos, ni centros identificables.
2. **Ningún secreto en el repo.** `.env` fuera de git; `.env.example` sin valores.
3. **La IA nunca publica ni decide.** Validación humana visible en la demo.
4. **Siempre agregado.** Umbral mínimo de 5–10 respuestas por segmento.
5. **Nada de ML si no es necesario.** Reglas explicables > caja negra.
6. **Dormir.** Una demo rota el domingo vale menos que una demo sencilla que funciona.
7. **Vídeo de respaldo.** Si falla internet o el proyector, se reproduce el vídeo.
8. **Español/catalán:** la app está en catalán (jurado y Damm); la documentación interna en español.

---

## 6. Reparto de la demo (3 minutos)

| Tiempo | Persona | Qué dice | Qué muestra |
| --- | --- | --- | --- |
| 0:00–0:25 | Jordi | El problema: no llega a todos, una encuesta no encaja con todos, el análisis llega tarde | Inicio |
| 0:25–0:55 | Iker | RRHH describe la necesidad; la IA propone 4 preguntas | Nova consulta |
| 0:55–1:15 | Iker | Edición y aprobación humana; QR para planta | Validación + QR |
| 1:15–1:45 | Izan | Representatividad: planta y logística por debajo; alertas honestas | Participació |
| 1:45–2:25 | Miguel | Temas, evolución, emergentes, señales débiles y límites | Anàlisi |
| 2:25–2:45 | Jordi | Dos acciones y nueva microconsulta; el ciclo se cierra | Insights |
| 2:45–3:00 | Todos | Privacidad: agregado, umbral, PII, control humano | Privacitat |

**Frase de cierre:** «La IA propone; las personas deciden. Y cada respuesta genera la siguiente pregunta.»

---

## 7. Riesgos y plan B

| Riesgo | Probabilidad | Plan B |
| --- | --- | --- |
| Typeform falla o limita la API | Media | Modo mock + vídeo + capturas |
| El LLM no responde o tarda | Media | Generación por plantillas (ya implementada) |
| La app se rompe en directo | Baja | Vídeo de respaldo y app local ya cargada |
| El jurado cuestiona la representatividad | Alta | Mostrar margen de error, tasas por colectivo y alertas |
| El jurado cuestiona la privacidad | Alta | Enseñar umbral, PII y pantalla de privacidad |
| Alguien no duerme | Media | Turnos y congelación a las 10:00 |

---

## 8. Checklist final

- [ ] El flujo funciona de la necesidad a la recomendación.
- [ ] Hay validación humana antes de publicar.
- [ ] Las datos son 100% sintéticos.
- [ ] Hay umbral mínimo y resultados solo agregados.
- [ ] Ningún token ni secreto en el código o la presentación.
- [ ] README y `.env.example` incluidos.
- [ ] Demo de seguridad (vídeo o capturas) preparada.
- [ ] El pitch dura 3 minutos y lo ha ensayado todo el equipo.
- [ ] Las 7 pantallas cargan sin errores en el portátil de la demo.
