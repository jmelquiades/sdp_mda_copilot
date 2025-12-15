# Criteria ServiceDesk Copilot – API (V1)

FastAPI + Alembic. Incluye:
- Hito 1: `/health` y conexión a Postgres (schema `copilot`).
- Hito 4: `/api/tickets` (listado asignado) con servicio, último contacto y flags locales.
- Hito 5: `/api/tickets/{id}` (detalle) y `/api/tickets/{id}/history` (historial) con servicio resuelto y timestamps normalizados.

## Configuración rápida
1) Copia `.env.example` a `.env` y ajusta si es necesario.
2) Usa la URL de Render en formato async (`postgresql+asyncpg://...`). Si tu URL trae `?sslmode=require`, no pasa nada: el backend la limpia y fuerza SSL con contexto por defecto. El `DB_SCHEMA` por defecto es `copilot` (minúsculas para evitar problemas de schema).

## Ejecutar local
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health check:
```bash
curl -v http://localhost:8000/health
```

## Migraciones
```bash
alembic upgrade head
```
- La migración inicial crea el esquema `Copilot` (no toca otras tablas).
- El versionado de Alembic se almacena en el mismo esquema `Copilot`.

## Endpoints relevantes
- `GET /health` → estado básico.
- `GET /api/tickets` → tickets asignados al técnico autenticado (bearer UPN). Campos: `service_code` (nombre), último contacto, flags de silencio/SLA.
- `GET /api/tickets/{id}` → detalle del ticket (servicio, SLA, requester, created_time, último contacto, flags).
- `GET /api/tickets/{id}/history` → eventos cronológicos (notas y conversaciones) con autor, visibilidad y timestamp ISO.
- `POST /api/ia/generate_reply` → (Hito 6) genera un mensaje sugerido con IA. Requiere tablas pobladas: `org_profile`, `persona_config`, `services_catalog`, `settings` y mapeo en `technician_mapping`.
- `POST /api/ia/interpret_conversation` → (Hito 6) sugiere enfoque a partir del historial reciente.

## Variables de entorno IA (Azure OpenAI)
- `AZURE_OPENAI_ENDPOINT` (ej. `https://criteria-nlu.openai.azure.com`)
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_API_VERSION` (ej. `2024-06-01`)
- `AZURE_OPENAI_DEPLOYMENT_GPT` (ej. `nlu-41mini`)

## Datos mínimos en BD para probar IA
- `org_profile`: 1 fila con industria, contexto y tone_notes.
- `persona_config`: 1 fila activa con role_description, tone_attributes, rules, max_reply_length o system_prompt_template.
- `services_catalog`: códigos/nombres de servicio usados en tickets (ej. 307 → “Otros”).
- `settings`: claves JSON `max_history_messages_in_prompt`, `max_internal_notes_in_prompt`, `temperature`, `max_tokens`, `azure_openai_deployment`, `azure_openai_api_version`.
- `settings` (reviews): `review_token_secret` (clave HMAC) y opcional `review_token_ttl_hours` (por defecto 24).
- `technician_mapping`: user_upn ↔ technician_id_sdp para el bearer que uses en las pruebas.

## Pruebas manuales (curl)
> Usamos un “token” dummy: `Authorization: Bearer <UPN>` donde el UPN debe existir en `technician_mapping`.

### Hito 1 – Health
```bash
curl -v http://localhost:8000/health
```

### Hito 4 – Listado de tickets asignados
```bash
curl -H "Authorization: Bearer mds_jrojas@chinalco.com.pe" \
  http://localhost:8000/api/tickets
```
Validar: `service_code` viene como nombre (no id), `last_user_contact_at` en ISO UTC, flags `is_silent`/`communication_sla_hours`.

### Hito 5 – Detalle e historial
Detalle:
```bash
curl -H "Authorization: Bearer mds_jrojas@chinalco.com.pe" \
  http://localhost:8000/api/tickets/162385
```
Validar: `created_time` no nulo, requester (nombre/email), servicio resuelto, SLA y último contacto.

Historial:
```bash
curl -H "Authorization: Bearer mds_jrojas@chinalco.com.pe" \
  http://localhost:8000/api/tickets/162385/history
```
Validar: eventos en orden cronológico con `type`, `author_type`, `visibility` y `timestamp` ISO.

### Hito 6/7 – IA (OpenAI) y envío de respuestas
Generar sugerencia:
```bash
curl -X POST http://localhost:8000/api/ia/generate_reply \
  -H "Authorization: Bearer mds_jrojas@chinalco.com.pe" \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"162385","message_type":"primera_respuesta","draft":""}'
```

Interpretar conversación:
```bash
curl -X POST http://localhost:8000/api/ia/interpret_conversation \
  -H "Authorization: Bearer mds_jrojas@chinalco.com.pe" \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"162385"}'
```

Enviar respuesta (Graph con app-only):
```bash
curl -X POST "http://localhost:8000/api/tickets/162385/send_reply" \
  -H "Authorization: Bearer mds_jrojas@chinalco.com.pe" \
  -H "Content-Type: application/json" \
  -d '{"message":"Texto de prueba via Graph"}'
```
Requisitos previos: claves `graph_tenant_id`, `graph_client_id`, `graph_client_secret`, `graph_sender` en `copilot.settings` y ApplicationAccessPolicy concedida al buzón (comprobar con `Test-ApplicationAccessPolicy`). Respuesta esperada: `{"ok":true}` y correo recibido desde `graph_sender`.

### Hito 9 – Flujo de review de experiencia
Validar token (público):
```bash
curl "http://localhost:8000/api/experience/review/validate?token=<TOKEN>"
```
Respuesta esperada: `{"valid":true,"ticket_id":"<id>"}` o error `invalid_token/token_expired`.

Registrar solicitud de revisión (público):
```bash
curl -X POST "http://localhost:8000/api/experience/review/submit" \
  -H "Content-Type: application/json" \
  -d '{"token":"<TOKEN>","reason":"No quedó conforme","comment":"Ejemplo"}'
```
Efectos: crea nota interna en SDP con el motivo, marca `experience_review_requested=true` y setea `last_review_request_at` en `ticket_flags`.

Generar un token (usar la misma `review_token_secret` y TTL `experience_review_token_ttl_hours`, 24h por defecto):
```bash
python - <<'PY'
from app.core.review_tokens import generate_token
secret = "mi-clave-larga-super-segura"  # la misma guardada en copilot.settings
token = generate_token(ticket_id="162385", secret=secret, ttl_hours=24)
print(token)
PY
```

Validar manualmente un token:
```bash
curl "http://localhost:8000/api/experience/review/validate?token=<TOKEN>"
```
