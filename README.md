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
- `technician_mapping`: user_upn ↔ technician_id_sdp para el bearer que uses en las pruebas.
