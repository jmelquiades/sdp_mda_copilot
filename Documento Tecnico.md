**DOCUMENTO TÉCNICO – CRITERIA SERVICEDESK COPILOT**

Versión: 1.0 – Cerrado para desarrollo  
Producto: Criteria ServiceDesk Copilot – Módulo de Calidad de
Experiencia de Atención

**Stack oficial:**

- Backend: Python + FastAPI (Render)

- BD: PostgreSQL (Render)

- Frontend: React SPA

- Integración SDP: SDP_API_GW_OP (único camino)

- Correo: Microsoft Graph (Office 365)

- IA: Proveedor LLM (ej. OpenAI) encapsulado en módulo propio

**1. Objetivo del documento**

Definir la **arquitectura técnica, componentes, modelos de datos,
endpoints y requisitos no funcionales** necesarios para implementar la
V1 del Criteria ServiceDesk Copilot, alineado al Diseño Funcional
aprobado y específicamente orientado a:

- Mejorar la **experiencia de atención** técnico–usuario.

- Implementar una **consola web** para técnicos con:

  - bandeja “Mis tickets”,

  - cálculo de **tiempo desde la última comunicación al usuario**,

  - detección de **tickets silenciosos** según un **SLA de
    comunicación** por servicio/prioridad,

  - redacción asistida por IA para primera respuesta, actualizaciones y
    cierre,

  - registro de la comunicación en SDP vía correo (Graph + BCC).

- Implementar el flujo de **Solicitud de revisión de la atención** por
  parte del usuario.

Este documento:

- Elimina caminos alternativos y ambigüedades.

- Está pensado para que el equipo de desarrollo pueda construir sin
  “rellenar huecos”.

- Asume la forma de trabajo habitual del proyecto:

  - Render.com para servicios y BD.

  - Python en todos los servicios.

  - Gateway SDP_API_GW_OP como único punto de integración con
    ServiceDesk Plus.

  - Office365/Microsoft Graph para envío de correos.

**2. Componentes y Servicios**

**2.1. Servicios en Render**

1.  **copilot-api**

    - Tipo: Web Service.

    - Lenguaje: Python 3.x.

    - Framework: FastAPI.

    - Expone API REST JSON.

    - Responsabilidades:

      - autenticación/mapeo de técnico,

      - consumo de SDP_API_GW_OP,

      - cálculo de **SLA de comunicación** y **tickets silenciosos**,

      - integración con IA,

      - integración con Graph,

      - persistencia en copilot-db.

2.  **copilot-db**

    - Tipo: PostgreSQL (servicio gestionado en Render).

    - Usado exclusivamente por el Copilot para:

      - configuración,

      - mapeos,

      - SLA de comunicación por servicio/prioridad,

      - flags de ticket (silencioso, solicitud de revisión, última
        comunicación),

      - logs de IA.

3.  **copilot-web**

    - Tipo: Static Site (build de React).

    - Se conecta a copilot-api vía HTTPS.

Alternativa válida: servir el frontend desde FastAPI (rutas estáticas).
Se mantiene el mismo contrato API.

**2.2. Servicios externos**

1.  **SDP_API_GW_OP**

    - API Gateway existente para ServiceDesk Plus.

    - El Copilot **no** habla directamente con SDP (ni BD ni API
      nativa); solo con este gateway.

2.  **Microsoft Graph (Office 365)**

    - Para enviar correos en nombre de la cuenta de Mesa de Servicios.

    - Ruta única de notificación al usuario y registro en SDP (vía BCC).

3.  **Proveedor de IA (LLM)**

    - API de modelo de lenguaje (ej. OpenAI) para:

      - generar mensajes (primera respuesta, actualización, cierre),

      - interpretar conversaciones confusas.

**3. Backend – FastAPI**

**3.1. Librerías recomendadas**

- fastapi

- uvicorn

- pydantic / pydantic-core

- sqlalchemy

- asyncpg o psycopg2

- alembic (migraciones)

- httpx (cliente HTTP)

- msal o azure-identity (autenticación Microsoft Graph)

- python-jose o similar (JWT para “solicitud de revisión”)

- cliente IA (ej. openai)

**3.2. Estructura del proyecto**

app/

main.py

config.py

dependencies.py

api/

\_\_init\_\_.py

routes_me.py

routes_tickets.py

routes_ia.py

routes_experience.py

core/

auth.py \# validación de tokens de usuario

sdp_client.py \# cliente para SDP_API_GW_OP

graph_client.py \# cliente para Microsoft Graph

ia_client.py \# cliente para LLM

models/

\_\_init\_\_.py

base.py

technician_mapping.py

services_catalog.py

org_profile.py

persona_config.py

settings.py

ticket_flags.py

ia_logs.py

schemas/

\_\_init\_\_.py

common.py

tickets.py

ia.py

experience.py

db/

session.py

init_db.py

utils/

tokens.py \# generación/validación de tokens de revisión

logging.py

**4. Integración con SDP vía SDP_API_GW_OP**

**4.1. Configuración**

Variables de entorno para copilot-api:

- SDP_GW_BASE_URL  
  Ej: https://criteria-sdp-api-gw-op.onrender.com

- SDP_GW_CLIENT_NAME  
  Para header X-Cliente

- SDP_GW_API_KEY  
  Para header X-Api-Key

Todos los requests al gateway incluirán:

- X-Cliente: \<SDP_GW_CLIENT_NAME\>

- X-Api-Key: \<SDP_GW_API_KEY\>

**4.2. Contrato esperado del Gateway**

Internamente, el gateway resolverá cómo hablar con SDP (reportes, BD,
etc.). El Copilot solo ve estos endpoints.

**4.2.1. Listar tickets asignados a un técnico**

GET {SDP_GW_BASE_URL}/request/assigned

Query params:

- technician_id (obligatorio)

- status (opcional, coma separado)

- priority (opcional)

- from_date (opcional)

Respuesta ejemplo:

\[

{

"id": 123,

"display_id": "INC-123",

"subject": "Problema con BI",

"requester": {

"name": "Juan Pérez",

"email": "juan.perez@cliente.com"

},

"status": "En Proceso",

"priority": "Alta",

"last_public_reply_time": "2025-12-08T10:00:00Z",

"service_code": "BI_DUPLICADOS"

}

\]

- last_public_reply_time representa la última respuesta pública de un
  técnico al usuario.

- Si en alguna instancia no se implementara este campo, el backend
  podría derivarlo a partir del historial (/history).

**4.2.2. Detalle de ticket**

GET {SDP_GW_BASE_URL}/request/{ticket_id}

Respuesta:

{

"id": 123,

"display_id": "INC-123",

"subject": "Problema con BI",

"description": "Texto inicial del ticket...",

"requester": {

"name": "Juan Pérez",

"email": "juan.perez@cliente.com"

},

"status": "En Proceso",

"priority": "Alta",

"site": "UMO",

"group": "Mesa TI",

"technician_id": 24,

"created_time": "2025-12-05T09:00:00Z",

"sla": {

"response_due_by": "...",

"resolution_due_by": "..."

},

"service_code": "BI_DUPLICADOS",

"udf": {

"campo1": "valor",

"campo2": "valor"

}

}

**4.2.3. Historial / timeline del ticket**

GET {SDP_GW_BASE_URL}/request/{ticket_id}/history

Respuesta:

\[

{

"event_id": 1,

"type": "public_reply_user",

"author_name": "Juan Pérez",

"author_type": "usuario",

"visibility": "publico",

"timestamp": "2025-12-05T09:30:00Z",

"text": "Mensaje del usuario",

"old_value": null,

"new_value": null

},

{

"event_id": 2,

"type": "public_reply_tech",

"author_name": "Técnico X",

"author_type": "tecnico",

"visibility": "publico",

"timestamp": "2025-12-05T10:00:00Z",

"text": "Respuesta del técnico",

"old_value": null,

"new_value": null

},

{

"event_id": 3,

"type": "internal_note",

"author_name": "Técnico X",

"author_type": "tecnico",

"visibility": "interno",

"timestamp": "2025-12-05T10:15:00Z",

"text": "El usuario no contesta en las mañanas",

"old_value": null,

"new_value": null

}

\]

Este historial se usa para:

- construir el timeline,

- identificar la **última comunicación del técnico al usuario** → último
  evento type = public_reply_tech con visibility = publico.

**4.2.4. Cambio de estado**

POST {SDP_GW_BASE_URL}/request/{ticket_id}/status

Body:

{

"technician_id": 24,

"new_status": "En Proceso"

}

**4.2.5. Nota interna (para “solicitud de revisión”)**

POST {SDP_GW_BASE_URL}/request/{ticket_id}/note_internal

Body:

{

"technician_id": 24,

"text": "Usuario solicitó revisión: \[motivo\] - \[comentario
opcional\]"

}

**5. Envío de correos – Microsoft Graph (camino único)**

**5.1. Configuración**

Variables de entorno:

- AZURE_TENANT_ID

- AZURE_CLIENT_ID

- AZURE_CLIENT_SECRET

- GRAPH_SENDER_ADDRESS

  - Ej: mesadeservicios@cliente.com

- SDP_INBOUND_EMAIL

  - Ej: sdp@cliente.com

- TICKET_ID_TAG_PATTERN

  - Ej: "##{display_id}##"

**5.2. Flujo “Enviar al usuario”**

1.  Frontend llama a:

> POST /api/tickets/{ticket_id}/send_reply
>
> {
>
> "message": "texto final aprobado",
>
> "message_type": "primera_respuesta\|actualizacion\|cierre",
>
> "change_status_to": "EN_PROCESO\|RESUELTO\|NONE"
>
> }

2.  Backend (copilot-api):

    - Obtiene detalle del ticket desde el gateway:

      - GET /request/{ticket_id} → display_id, subject, requester.email.

    - Construye subject, por ejemplo:

      - "\[Mesa de Servicios\] {display_id} - {subject}
        \##{display_id}##"

    - Construye body HTML:

      - contenido de message,

      - footer estándar de Mesa,

      - texto con enlace para “Solicitar revisión de mi caso” en
        **correos de actualización y cierre**, cuando la organización lo
        tenga habilitado.

    - Llama a Microsoft Graph:

    - POST
      https://graph.microsoft.com/v1.0/users/{GRAPH_SENDER_ADDRESS}/sendMail

    - 

    - {

    - "message": {

    - "subject": "Asunto con \##INC-123##",

    - "body": {

    - "contentType": "HTML",

    - "content": "\<p\>mensaje...\</p\>"

    - },

    - "toRecipients": \[

    - { "emailAddress": { "address": "usuario@cliente.com" } }

    - \],

    - "bccRecipients": \[

    - { "emailAddress": { "address": "sdp@cliente.com" } }

    - \]

    - }

    - }

    - Si change_status_to != "NONE":

      - llama al gateway:

        - POST /request/{ticket_id}/status con {"technician_id": ...,
          "new_status": ...}.

    - Actualiza ticket_flags para ese ticket_id:

      - last_user_contact_at = now()

      - hours_since_last_user_contact = 0

      - recalcula communication_sla_hours (ver sección 7.7),

      - is_silent = false.

3.  SDP, al recibir el correo BCC con \##display_id##, lo adjunta al
    hilo del ticket.

**5.3. Manejo de errores**

- Si Graph falla:

  - Devuelve error al frontend.

  - No cambia estado en SDP.

  - No actualiza ticket_flags.

  - El frontend mantiene el texto del mensaje para que el técnico no lo
    pierda.

**6. Base de Datos – PostgreSQL**

**6.1. Tablas**

**1. technician_mapping**

Mapea usuario O365 ↔ técnico SDP.

CREATE TABLE technician_mapping (

id SERIAL PRIMARY KEY,

user_upn TEXT NOT NULL UNIQUE,

technician_id_sdp TEXT NOT NULL,

active BOOLEAN NOT NULL DEFAULT TRUE,

created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

**2. services_catalog**

Catálogo de servicios para contexto de IA **y configuración de SLA de
comunicación por servicio/prioridad**.

CREATE TABLE services_catalog (

id SERIAL PRIMARY KEY,

service_code TEXT NOT NULL UNIQUE,

name TEXT NOT NULL,

short_description TEXT,

requirements TEXT,

first_response_notes TEXT,

update_notes TEXT,

closure_notes TEXT,

-- SLA de comunicación por prioridad (horas). Si es NULL, se usa valor
global.

comm_sla_p1_hours NUMERIC,

comm_sla_p2_hours NUMERIC,

comm_sla_p3_hours NUMERIC,

comm_sla_p4_hours NUMERIC,

sdp_mapping_info JSONB,

created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

**3. org_profile**

Perfil de organización (1 registro por instancia).

CREATE TABLE org_profile (

id SERIAL PRIMARY KEY,

industry TEXT,

context TEXT,

critical_services JSONB,

tone_notes TEXT,

created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

**4. persona_config**

Configuración de la persona IA.

CREATE TABLE persona_config (

id SERIAL PRIMARY KEY,

role_description TEXT,

tone_attributes JSONB,

rules JSONB,

max_reply_length INT,

system_prompt_template TEXT,

active BOOLEAN NOT NULL DEFAULT TRUE,

created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

**5. settings**

Parámetros generales.

CREATE TABLE settings (

id SERIAL PRIMARY KEY,

key TEXT NOT NULL UNIQUE,

value JSONB NOT NULL,

created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

Claves recomendadas:

- habilitar_solicitud_revision → true/false

- usar_notas_internas_en_ia → true/false

- max_internal_notes_in_prompt → número

- max_history_messages_in_prompt → número

- COMM_SLA_DEFAULT_HOURS → horas máximas sin comunicación al usuario
  cuando no hay configuración por servicio

- EXPERIENCE_REVIEW_TOKEN_TTL_HOURS → horas de validez del token de
  revisión

- LLM_MODEL → nombre del modelo IA a usar

**6. ticket_flags**

Flags por ticket, incluyendo **solicitud de revisión** y **SLA de
comunicación**.

CREATE TABLE ticket_flags (

id SERIAL PRIMARY KEY,

ticket_id TEXT NOT NULL,

display_id TEXT,

service_code TEXT,

priority TEXT,

status TEXT,

-- Comunicación con el usuario

last_user_contact_at TIMESTAMPTZ,

hours_since_last_user_contact NUMERIC,

communication_sla_hours NUMERIC,

is_silent BOOLEAN NOT NULL DEFAULT FALSE,

-- Revisión de experiencia

experience_review_requested BOOLEAN NOT NULL DEFAULT FALSE,

last_review_request_at TIMESTAMPTZ,

updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

CREATE UNIQUE INDEX ux_ticket_flags_ticket_id

ON ticket_flags(ticket_id);

**7. ia_logs**

Registra uso de IA.

CREATE TABLE ia_logs (

id SERIAL PRIMARY KEY,

timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

user_upn TEXT,

ticket_id TEXT,

operation TEXT, -- generate_reply / interpret_conversation

message_type TEXT, -- primera_respuesta / actualizacion / cierre /
interpretacion

model TEXT,

success BOOLEAN,

latency_ms INT,

prompt_chars INT,

response_chars INT,

error_message TEXT

);

**7. Endpoints del backend (API pública para frontend)**

**7.1. /api/me**

- GET /api/me

- Requiere autenticación (token OIDC de Azure AD).

- Devuelve:

{

"user_upn": "juan.melquiades@criteria.pe",

"display_name": "Juan Carlos Melquiades",

"technician_id_sdp": "24"

}

Si el user_upn no existe en technician_mapping, se responde error 403.

**7.2. Tickets**

**7.2.1. Listado “Mis tickets”**

GET /api/tickets?status=...&priority=...&silent_only=...

- Resuelve user_upn → technician_id_sdp.

- Llama a GET /request/assigned del gateway.

- Para cada ticket:

  1.  Determina la **última comunicación del técnico al usuario**:

      - si viene last_public_reply_time desde el gateway, la usa.

      - si no, podría obtenerse desde /history (si se define así), pero
        la V1 asume last_public_reply_time.

  2.  Calcula:

      - last_user_contact_at = last_public_reply_time

      - hours_since_last_user_contact = now() - last_user_contact_at

  3.  Obtiene el SLA de comunicación efectivo:

      - si hay service_code + priority:

        - usa comm_sla_px_hours de services_catalog,

      - si no:

        - usa COMM_SLA_DEFAULT_HOURS de settings.

  4.  Determina is_silent:

      - is_silent = (ticket en estado activo) AND
        (hours_since_last_user_contact \> communication_sla_hours).

  5.  Actualiza/crea registro en ticket_flags.

- Aplica filtros:

  - status: filtra por estado,

  - priority: filtra por prioridad,

  - silent_only=true: devuelve solo is_silent = true.

**Respuesta**: lista de TicketSummary:

\[

{

"ticket_id": "123",

"display_id": "INC-123",

"subject": "Problema con BI",

"requester_name": "Juan Pérez",

"requester_email": "juan.perez@cliente.com",

"status": "En Proceso",

"priority": "Alta",

"service_code": "BI_DUPLICADOS",

"service_name": "Servicio BI – Duplicados",

"last_user_contact_at": "2025-12-08T10:00:00Z",

"hours_since_last_user_contact": 26.5,

"communication_sla_hours": 24,

"is_silent": true,

"experience_review_requested": false

}

\]

**7.2.2. Detalle de ticket**

GET /api/tickets/{ticket_id}

- Llama a GET /request/{ticket_id} en gateway.

- Enriquecer con:

  - datos de services_catalog (service_code),

  - datos de ticket_flags:

    - last_user_contact_at,

    - hours_since_last_user_contact,

    - communication_sla_hours,

    - is_silent,

    - experience_review_requested.

Devuelve TicketDetails con toda esta información.

**7.2.3. Historial del ticket**

GET /api/tickets/{ticket_id}/history

- Llama a GET /request/{ticket_id}/history en gateway.

- Devuelve lista de TicketEvent tal cual, mapeada a estructura interna.

**7.3. IA – generar mensaje**

POST /api/ia/generate_reply

**Request:**

{

"ticket_id": 123,

"message_type": "primera_respuesta\|actualizacion\|cierre",

"draft": "texto opcional"

}

**Backend:**

- Carga:

  - TicketDetails y TicketEvents (gateway),

  - services_catalog (si hay service_code),

  - org_profile,

  - persona_config,

  - settings (uso de notas internas, número de mensajes, etc.).

- Construye prompt con:

  - persona IA (rol, tono, reglas),

  - perfil de organización (industria, contexto, sensibilidades),

  - datos del ticket (asunto, descripción, requester, prioridad, estado,
    SLA de comunicación si es útil para el enfoque del mensaje),

  - historial limitado (últimos N mensajes),

  - últimas N notas internas (si usar_notas_internas_en_ia = true, con
    instrucción explícita de no citarlas literalmente),

  - información de servicio (nombre, descripción, requisitos, notas por
    tipo de mensaje),

  - borrador del técnico (si viene).

- Llama a ia_client.generate_reply(...).

- Registra en ia_logs.

**Respuesta:**

{

"suggested_message": "texto sugerido",

"model": "LLM_MODEL",

"prompt_chars": 1234,

"response_chars": 567

}

**7.4. IA – interpretar conversación**

POST /api/ia/interpret_conversation

**Request:**

{

"ticket_id": 123

}

**Backend:**

- Obtiene últimos N eventos usuario/técnico del historial.

- Obtiene últimas N notas internas (según configuración).

- Construye prompt pidiendo:

  - intención actual del usuario,

  - brecha de expectativa,

  - sugerencia de enfoque para la siguiente respuesta.

- Llama a ia_client.interpret_conversation(...).

- Registra en ia_logs.

**Respuesta:**

{

"user_intention": "texto",

"expectation_gap": "texto",

"suggested_approach": "texto"

}

**7.5. Enviar mensaje al usuario**

POST /api/tickets/{ticket_id}/send_reply

**Request:**

{

"message": "texto final aprobado",

"message_type": "primera_respuesta\|actualizacion\|cierre",

"change_status_to": "EN_PROCESO\|RESUELTO\|NONE"

}

**Backend:**

1.  Llama a GET /request/{ticket_id} en gateway para obtener display_id,
    subject, requester_email.

2.  Envía correo vía Microsoft Graph (To, BCC, \##display_id##).

3.  Si change_status_to ≠ NONE, llama POST /request/{ticket_id}/status.

4.  Actualiza ticket_flags:

    - last_user_contact_at = now(),

    - hours_since_last_user_contact = 0,

    - recalcula communication_sla_hours,

    - is_silent = false,

    - status actualizado.

**Respuesta:**

{

"status": "ok"

}

Si Graph falla, se devuelve error y no se actualizan ticket_flags ni
estado en SDP.

**7.6. Solicitud de revisión (usuario final)**

El footer del correo de **actualización** y **cierre** incluirá un link:

https://copilot.criteria.pe/experience/review?token=...

**7.6.1. Página de formulario**

GET /experience/review?token=...

- Backend valida/decodifica el token (firma + expiración + ticket_id).

- Si es válido, sirve la página React con formulario:

  - motivo,

  - comentario opcional.

**7.6.2. API para registrar la solicitud**

POST /api/experience/review/submit

**Request:**

{

"token": "token recibido",

"reason": "no_acuerdo_respuesta\|se_volvio_urgente\|otro",

"comment": "texto opcional"

}

**Backend:**

1.  Valida token (firma y expiración) → obtiene ticket_id.

2.  Llama a POST /request/{ticket_id}/note_internal en gateway con texto
    estándar.

3.  Marca en ticket_flags:

    - experience_review_requested = true,

    - last_review_request_at = now(),

    - updated_at = now().

4.  Devuelve:

{

"status": "ok"

}

**7.7. Lógica de SLA de comunicación (comunicación con el usuario)**

La lógica se implementa en backend (no en frontend).

**Definiciones:**

- last_user_contact_at:  
  última respuesta pública del técnico al usuario (primera_respuesta,
  actualización o cierre) registrada en el timeline.

- communication_sla_hours:  
  tiempo máximo que se considera aceptable sin comunicación al usuario,
  calculado así:

  - si el ticket tiene service_code y priority, se toma de
    services_catalog.comm_sla_pX_hours,

  - si no hay valor para esa prioridad/servicio, se usa
    COMM_SLA_DEFAULT_HOURS desde settings.

- hours_since_last_user_contact:  
  diferencia entre now() y last_user_contact_at en horas.

- is_silent:  
  true si el ticket está en estado activo y
  hours_since_last_user_contact \> communication_sla_hours.

Esta lógica se ejecuta:

- cuando se consulta /api/tickets (para poblar la bandeja “Mis
  tickets”),

- cuando se envía una respuesta al usuario (send_reply),

- cuando se actualizan estados desde SDP (si se añade más adelante).

**8. IA – Cliente y Prompts**

**8.1. Cliente IA (ia_client)**

Responsabilidades:

- generate_reply(ticket_context) -\> str

- interpret_conversation(ticket_context) -\> dict

Usa configuración:

- LLM_API_KEY

- LLM_MODEL

**8.2. generate_reply – contexto usado**

Prompt incluye:

- **Persona IA (persona_config)**:

  - rol,

  - tono,

  - reglas (no inventar plazos, pedir confirmación en cierre, etc.).

- **Perfil de organización (org_profile)**:

  - industria,

  - contexto (ej. operación minera, seguridad crítica).

- **Datos del ticket**:

  - asunto,

  - descripción,

  - requester (nombre, correo),

  - prioridad,

  - estado,

  - información de SLA de comunicación solo si ayuda al tono (ej.
    explicar que se hará seguimiento).

- **Historial (limitado)**:

  - últimos N mensajes públicos usuario/técnico (según
    max_history_messages_in_prompt).

- **Notas internas** (si usar_notas_internas_en_ia = true):

  - últimas N notas (max_internal_notes_in_prompt),

  - siempre con instrucción clara: *no citarlas literalmente ni exponer
    comentarios negativos*.

- **Servicio (si service_code existe)**:

  - nombre del servicio,

  - descripción corta en lenguaje usuario,

  - requisitos clave,

  - notas para primera respuesta / actualización / cierre según
    message_type.

- **Borrador del técnico** (si existe).

**8.3. interpret_conversation – contexto usado**

- Últimos N eventos de historial (mensajes usuario/técnico).

- Notas internas recientes (si se habilita su uso).

- Preguntas al modelo:

  - ¿Qué está buscando realmente el usuario ahora?

  - ¿Qué cree que falta?

  - ¿Qué brecha de expectativa hay?

  - ¿Qué enfoque recomiendas para la siguiente respuesta?

Salida:

{

"user_intention": "...",

"expectation_gap": "...",

"suggested_approach": "..."

}

**9. Seguridad**

**9.1. Autenticación de usuarios**

- Basada en Azure AD / OIDC.

- Cada request a /api/\* debe:

  - incluir un token de acceso válido,

  - ser validado en auth.py (firma, audiencia, expiración).

**9.2. Autorización y acceso a tickets**

- user_upn se resuelve a technician_id_sdp mediante technician_mapping.

- El backend solo:

  - lista tickets del técnico autenticado llamando al gateway por
    technician_id,

  - permite ver/operar sobre tickets individuales que provienen de ese
    universo (no sobre cualquier ticket_id arbitrario).

**9.3. Gestión de secretos**

- SDP_GW_API_KEY, AZURE_CLIENT_SECRET, LLM_API_KEY, etc.:

  - solo en variables de entorno,

  - no se guardan en código ni en repositorios.

**9.4. Tokens para “solicitud de revisión”**

- Usar JWT HMAC con secreto REVIEW_TOKEN_SECRET.

- Payload:

{

"ticket_id": "INC-123",

"exp": 1733700000

}

- El backend rechaza tokens caducados o con firma inválida.

**10. Rendimiento y Escalabilidad**

- API stateless:

  - copilot-api no guarda estado de sesión en memoria.

  - Se puede escalar horizontalmente en Render (más instancias).

- Uso de gateway SDP:

  - consultas por technician_id o ticket_id puntual.

- IA:

  - limitar N mensajes de historial y notas internas en el prompt.

  - controlar tamaño de prompt y tiempo de respuesta.

- BD:

  - índices en:

    - technician_mapping.user_upn,

    - ticket_flags.ticket_id,

    - ia_logs.ticket_id,

    - ia_logs.user_upn.

**11. Requisitos No Funcionales (NFR)**

**11.1. Confiabilidad y resiliencia**

- Idempotencia al enviar mensajes:

  - cada llamada a send_reply debe ser visible en logs.

  - no hacer reintentos automáticos silenciosos de correo.

- Timeouts:

  - llamadas a SDP_API_GW_OP, IA y Graph con timeout definido (5–10 s).

- Manejo de errores:

  - middleware global en FastAPI para:

    - capturar excepciones,

    - registrar stacktrace internamente,

    - devolver respuesta genérica al frontend.

**11.2. Monitoreo y observabilidad**

- Logging estructurado:

  - endpoint,

  - usuario (user_upn),

  - ticket_id (si aplica),

  - código HTTP,

  - tiempo de respuesta.

- Trazabilidad de IA:

  - ia_logs permite medir:

    - quién pidió qué,

    - latencias,

    - volumen de uso,

    - tasa de errores.

- Healthcheck:

  - GET /health → {"status": "ok"} si API y BD responden.

**11.3. Seguridad (resumen)**

- Autenticación basada en IdP corporativo.

- Autorización por técnico y ticket.

- Protección de datos personales:

  - el texto de conversaciones vive principalmente en SDP,

  - Copilot solo usa lo necesario para contexto de IA.

**11.4. Escalabilidad**

- Frontend → API → Gateway → SDP en capas.

- Fácil cambiar modelo IA o ampliar endpoints del gateway sin romper
  frontend.

**12. Ejemplo de pantallas – Vista principal del técnico y revisión**

**12.1. Vista “Detalle de Ticket + Copilot IA”**

**Objetivo de la pantalla:**

Permitir que el técnico:

- vea el contexto del ticket (datos clave + conversación),

- vea **tiempo desde la última comunicación** y si el ticket es
  “silencioso”,

- use la IA para redactar respuestas,

- envíe el mensaje al usuario,

- acceda a “Interpretar conversación”.

**Layout a dos columnas:**

- **Zona superior (barra de encabezado):**

  - Logo / nombre: “Criteria ServiceDesk Copilot”.

  - Nombre del usuario autenticado.

  - Botón \[Salir\].

- **Columna izquierda (30–40%): “Mis tickets”**

  - Buscador (ID, asunto, solicitante).

  - Filtros rápidos:

    - Estado,

    - Prioridad,

    - “Solo silenciosos” (usa silent_only=true en la API).

  - Lista de tickets:

    - ID / Display ID,

    - Asunto,

    - Solicitante,

    - Estado,

    - Prioridad,

    - **“Hace X horas” desde última respuesta al usuario**,

    - Icono si is_silent = true (ej. ⚠),

    - Icono si experience_review_requested = true.

- **Columna derecha (60–70%): Detalle de ticket + Copilot**

> \(a\) **Cabecera de ticket**

- ID y Display ID, estado, prioridad.

- Solicitante (nombre + correo).

- Link “Abrir en ServiceDesk Plus”.

- Nombre del servicio (si hay service_code).

- Texto informativo:

  - “Última comunicación al usuario: hace X horas.”

  - Si is_silent = true, mensaje tipo:  
    “Para este tipo de servicio se recomienda actualizar al usuario cada
    N horas. Han pasado M horas desde la última comunicación.”

> \(b\) **Información de contexto**

- Descripción inicial del ticket.

- Bloque “Servicio” (si aplica):

  - nombre del servicio,

  - descripción corta orientada al usuario.

- Bloque “Organización” (texto corto de perfil).

> \(c\) **Timeline de conversación**

- Pestañas:

  - “Conversación”: lista cronológica de mensajes públicos.

  - “Notas internas”: lista de notas internas.

- Botón “Interpretar conversación”:

  - abre panel con:

    - intención actual del usuario,

    - brecha de expectativa,

    - sugerencia de enfoque.

> \(d\) **Panel IA – Redacción asistida**

- Selector de tipo:

  - Primera respuesta,

  - Actualización,

  - Cierre.

- Campo “Borrador del técnico”.

- Botón “Generar con IA”.

- Campo “Mensaje sugerido por IA” (editable).

- Opciones de estado:

  - “Cambiar estado a En Proceso”,

  - “Cambiar estado a Resuelto/Cerrado”.

- Botón “Enviar al usuario”:

  - llama a /api/tickets/{ticket_id}/send_reply.

**12.2. Pantalla “Solicitud de revisión de la atención” (usuario
final)**

URL ejemplo:

https://copilot.criteria.pe/experience/review?token=...

Elementos mínimos:

- Encabezado:

  - “Solicitud de revisión de atención”.

  - Mensaje corto explicando el propósito.

- Formulario:

  - Pregunta: “Motivo de la solicitud”.

  - Opciones:

    - “No estoy de acuerdo con la respuesta que recibí.”

    - “La situación se ha vuelto más urgente.”

    - “Otro.”

  - Campo “Comentario (opcional)” (textarea).

  - Botón “Enviar solicitud de revisión”.

- Mensaje de confirmación:

  - “Hemos registrado tu solicitud de revisión. Un técnico revisará tu
    caso.”
