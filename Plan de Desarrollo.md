**PLAN DE IMPLEMENTACIÓN**

Producto: Criteria ServiceDesk Copilot – Módulo de Calidad de
Experiencia de Atención  
Versión: 1.0 – Válido para desarrollo de V1

**1. Objetivo del Plan**

Definir el **orden de construcción, pruebas y despliegue** del Criteria
ServiceDesk Copilot – V1, de forma que el equipo de desarrollo pueda
avanzar por **hitos claros**, verificando en cada paso:

1.  Se implementa una capacidad concreta.

2.  Se prueba.

3.  Si funciona → se pasa al siguiente hito.

4.  Si no funciona → se corrige antes de continuar.

Este plan se apoya en:

- el **Diseño Funcional** aprobado, y

- el **Documento Técnico** V1,

y no los reemplaza: los complementa con un **“cómo y en qué orden”**
llevarlos a código.

**2. Alcance resumido de la V1 (recordatorio)**

La V1 del Copilot debe entregar, al finalizar el plan:

1.  **Consola web para técnicos** con:

    - bandeja “Mis tickets”,

    - información de estado, prioridad y servicio,

    - **tiempo desde la última comunicación al usuario**,

    - indicador de **ticket silencioso** según un **SLA de
      comunicación** configurable por servicio/prioridad.

2.  **Vista detalle de ticket** con:

    - contexto del ticket (asunto, descripción, solicitante),

    - contexto del servicio (si existe service_code),

    - timeline de conversación (usuario/técnico) y notas internas.

3.  **Panel IA** para:

    - primera respuesta,

    - actualizaciones,

    - mensajes de cierre.

4.  **Integración con SDP** vía SDP_API_GW_OP:

    - lectura de tickets,

    - lectura de historial,

    - cambio de estado,

    - registro de notas internas (para la solicitud de revisión).

5.  **Integración con Microsoft Graph**:

    - envío de correos al usuario,

    - BCC al buzón de SDP, con ID entre \## para asociar al ticket.

6.  **Flujo de “Solicitud de revisión de la atención”**:

    - link en correos de actualización/cierre,

    - formulario simple para el usuario,

    - registro de la solicitud como nota interna en SDP,

    - flag en el Copilot para ese ticket.

**3. Supuestos y dependencias**

Para ejecutar este plan, se asume que:

1.  **Gateway SDP_API_GW_OP**:

    - expone los endpoints definidos en el Documento Técnico (assigned,
      detail, history, status, note_internal),

    - está accesible desde el backend del Copilot.

2.  **Infraestructura básica disponible**:

    - cuenta en Render para:

      - copilot-api,

      - copilot-db (PostgreSQL),

      - copilot-web.

    - suscripción / cuenta para IA (OpenAI u otro proveedor),

    - tenant de Azure AD con:

      - aplicación registrada para Microsoft Graph,

      - credenciales (client_id, secret, tenant_id),

      - buzón emisor y buzón de SDP.

3.  **Datos mínimos iniciales en BD**:

    - al menos un registro en technician_mapping para pruebas,

    - configuración básica en settings (por ejemplo
      COMM_SLA_DEFAULT_HOURS),

    - al menos 1 registro en org_profile, persona_config y
      services_catalog para escenarios de prueba.

4.  **Acceso a un entorno de SDP de pruebas**, con:

    - algunos tickets reales o simulados,

    - un técnico al que se le asignen tickets.

**4. Hitos de implementación**

Los hitos están pensados para construirse **en orden secuencial**.  
La regla es:

No avanzar al siguiente hito sin que el actual cumpla sus criterios de
aceptación.

**Hito 1 – Esqueleto API + conexión a BD**

**Objetivo**  
Dejar operativo el esqueleto del backend con FastAPI y la conexión a
PostgreSQL.

**Tareas técnicas**

1.  Crear estructura base del proyecto (app/, main.py, etc.).

2.  Implementar:

    - GET /health → devuelve {"status": "ok"}.

3.  Configurar DATABASE_URL e infraestructura DB (local o Render).

4.  Implementar:

    - models/base.py,

    - db/session.py.

5.  Configurar Alembic y ejecutar una migración inicial vacía.

**Criterios de aceptación**

- GET /health responde 200 con {"status": "ok"}.

- La API se conecta correctamente a la BD (no hay errores de conexión en
  logs).

**Hito 2 – Modelos de datos y migraciones**

**Objetivo**  
Crear todas las tablas necesarias para la V1 y tenerlas migradas en la
BD.

**Tareas técnicas**

1.  Implementar modelos SQLAlchemy y migraciones Alembic para:

    - technician_mapping

    - services_catalog

    - org_profile

    - persona_config

    - settings

    - ticket_flags

    - ia_logs

2.  Ejecutar migraciones en la BD de desarrollo.

**Criterios de aceptación**

- Todas las tablas existen en la BD.

- Se pueden insertar registros de prueba mediante scripts o herramientas
  de administración (ej. technician_mapping, settings).

**Hito 3 – Autenticación y /api/me**

**Objetivo**  
Autenticar usuarios y mapearlos a técnicos SDP, para que cualquier
operación posterior sepa “quién es el técnico”.

**Tareas técnicas**

1.  Implementar core/auth.py:

    - validación del token de usuario (mock o integración real con Azure
      AD, según decisión).

2.  Implementar endpoint GET /api/me:

    - extrae user_upn del token,

    - busca en technician_mapping,

    - devuelve user_upn, display_name, technician_id_sdp.

3.  Cargar al menos un registro de prueba en technician_mapping.

**Criterios de aceptación**

- Para un usuario con entrada en technician_mapping, GET /api/me
  devuelve sus datos correctamente.

- Si el user_upn no existe en technician_mapping, el endpoint devuelve
  **403** o error equivalente de “usuario no configurado”.

**Hito 4 – Integración SDP básica y bandeja “Mis tickets”**

**Objetivo**  
Poder listar los tickets asignados a un técnico y calcular la
información de comunicación (último contacto, SLA, silencioso).

**Tareas técnicas**

1.  Implementar core/sdp_client.py con funciones:

    - get_assigned_requests(technician_id, ...)

2.  Implementar GET /api/tickets:

    - Resuelve user_upn → technician_id_sdp.

    - Llama a get_assigned_requests.

    - Para cada ticket:

      - toma last_public_reply_time desde el gateway (o campo
        equivalente),

      - calcula last_user_contact_at,

      - calcula hours_since_last_user_contact,

      - determina communication_sla_hours usando:

        - services_catalog por service_code + prioridad, o

        - COMM_SLA_DEFAULT_HOURS desde settings,

      - determina is_silent según reglas del Documento Técnico,

      - actualiza/inserta ticket_flags.

3.  Devolver en la respuesta de /api/tickets:

    - datos básicos del ticket,

    - last_user_contact_at,

    - hours_since_last_user_contact,

    - communication_sla_hours,

    - is_silent,

    - experience_review_requested.

**Criterios de aceptación**

- Se puede llamar a /api/tickets con un usuario autenticado y obtener la
  lista de sus tickets.

- Al menos se prueban 2 casos:

  - ticket con comunicación reciente → is_silent = false,

  - ticket con comunicación muy antigua → is_silent = true.

- Los registros correspondientes aparecen en ticket_flags actualizados.

**Hito 5 – Detalle de ticket + historial**

**Objetivo**  
Tener el detalle completo del ticket y su timeline para mostrarlos en la
UI.

**Tareas técnicas**

1.  Ampliar core/sdp_client.py con:

    - get_request_detail(ticket_id)

    - get_request_history(ticket_id)

2.  Implementar:

    - GET /api/tickets/{ticket_id}:

      - llama a get_request_detail,

      - consulta services_catalog (por service_code),

      - consulta ticket_flags,

      - devuelve combinación de toda la información.

    - GET /api/tickets/{ticket_id}/history:

      - llama a get_request_history,

      - devuelve lista cronológica de eventos.

**Criterios de aceptación**

- GET /api/tickets/{ticket_id} devuelve:

  - datos del ticket,

  - nombre del servicio (si hay service_code),

  - datos de comunicación (last_user_contact_at, is_silent, etc.).

- GET /api/tickets/{ticket_id}/history devuelve el timeline con:

  - mensajes del usuario,

  - mensajes del técnico,

  - notas internas.

**Hito 6 – IA: generación de mensajes**

**Objetivo**  
Permitir que el técnico obtenga mensajes generados por IA para primera
respuesta, actualizaciones y cierre.

**Tareas técnicas**

1.  Implementar core/ia_client.py:

    - generate_reply(contexto)

    - interpret_conversation(contexto) (se usará en el siguiente hito).

2.  Implementar POST /api/ia/generate_reply:

    - recibe ticket_id, message_type, draft,

    - arma contexto con:

      - ticket,

      - historial (limitado),

      - servicio (services_catalog),

      - organización (org_profile),

      - persona IA (persona_config),

      - notas internas recientes (según settings),

      - borrador del técnico (opcional),

    - llama a ia_client.generate_reply,

    - guarda registro en ia_logs,

    - devuelve suggested_message.

**Criterios de aceptación**

- Enviando al menos 1 ticket de prueba con message_type =
  primera_respuesta se obtiene un suggested_message razonable.

- Se registra una fila en ia_logs por cada llamada.

- Los errores del proveedor IA se manejan devolviendo mensaje claro al
  frontend (no se cae la API).

**Hito 7 – IA: interpretar conversación**

**Objetivo**  
Permitir al técnico usar el botón “Interpretar conversación” y recibir
una guía sobre intención y brecha de expectativas.

**Tareas técnicas**

1.  Implementar POST /api/ia/interpret_conversation:

    - recibe ticket_id,

    - obtiene últimos N mensajes del historial,

    - (opcional) incluye notas internas recientes según configuración,

    - arma el prompt,

    - llama a ia_client.interpret_conversation,

    - guarda en ia_logs,

    - devuelve:

      - user_intention,

      - expectation_gap,

      - suggested_approach.

**Criterios de aceptación**

- Para un ticket con varias idas y venidas, el endpoint:

  - responde 200,

  - devuelve los 3 campos con texto.

- Se registra una entrada en ia_logs por cada llamada.

**Hito 8 – Envío de correo y actualización de flags / estado**

**Objetivo**  
Cerrar el ciclo: enviar el mensaje al usuario vía correo, vincularlo a
SDP y actualizar los indicadores de comunicación.

**Tareas técnicas**

1.  Implementar core/graph_client.py con:

    - autenticación contra Graph (client credentials),

    - función send_mail(from, to, bcc, subject, body).

2.  Implementar POST /api/tickets/{ticket_id}/send_reply:

    - recibe:

      - message,

      - message_type,

      - change_status_to.

    - obtiene detalle del ticket (para display_id, subject,
      requester_email),

    - construye subject con \##display_id##,

    - envía correo mediante Graph:

      - To: solicitante,

      - Bcc: buzón SDP,

    - si change_status_to != "NONE":

      - llama a set_request_status en el gateway,

    - actualiza ticket_flags:

      - last_user_contact_at = now(),

      - hours_since_last_user_contact = 0,

      - recálculo de communication_sla_hours,

      - is_silent = false.

**Criterios de aceptación**

- Los correos de prueba llegan al solicitante y al buzón de SDP.

- En ticket_flags:

  - se actualiza last_user_contact_at tras una llamada exitosa,

  - el ticket deja de aparecer como silencioso.

- Si Graph falla:

  - la API devuelve error,

  - no se cambia el estado en SDP,

  - no se actualizan ticket_flags.

**Hito 9 – Flujo de “Solicitud de revisión de la atención”**

**Objetivo**  
Permitir que el usuario final, desde un correo de actualización/cierre,
pueda solicitar revisión de la atención.

**Tareas técnicas**

1.  Implementar utils/tokens.py:

    - generación y validación de tokens JWT para revisión (contienen
      ticket_id y expiración).

2.  Ajustar generación de correo (Hito 8):

    - en mensajes de **actualización** y **cierre** incluir link:  
      https://\<dominio\>/experience/review?token=\<...\>  
      solo si habilitar_solicitud_revision es true en settings.

3.  Implementar endpoint para servir la página de revisión:

    - GET /experience/review?token=...:

      - valida token,

      - si es válido → sirve SPA con formulario,

      - si no → mensaje de enlace inválido/expirado.

4.  Implementar POST /api/experience/review/submit:

    - recibe token, reason, comment,

    - valida token (firma y expiración),

    - extrae ticket_id,

    - llama a note_internal en el gateway con texto estándar,

    - actualiza ticket_flags:

      - experience_review_requested = true,

      - last_review_request_at = now().

**Criterios de aceptación**

- Desde un correo de prueba, el enlace de revisión abre la página
  correspondiente.

- Enviando el formulario:

  - se registra una nota interna en SDP,

  - se actualiza el flag experience_review_requested en ticket_flags.

**Hito 10 – Frontend completo (bandeja, detalle, panel IA y revisión)**

**Objetivo**  
Conectar toda la lógica de backend en una UI usable por los técnicos y
por el usuario final (revisión).

**Tareas técnicas**

1.  Implementar en React:

    - Layout principal con:

      - barra de encabezado (usuario, logout),

      - columna “Mis tickets”:

        - buscador,

        - filtros básicos,

        - indicador de is_silent y experience_review_requested,

      - columna de detalle:

        - cabecera de ticket,

        - contexto de servicio/organización,

        - timeline de conversación,

        - botón “Interpretar conversación” (usa
          /api/ia/interpret_conversation),

        - panel IA con:

          - tipo de mensaje,

          - borrador,

          - botón “Generar con IA”,

          - textarea editable,

          - check de cambio de estado,

          - botón “Enviar al usuario” (usa
            /api/tickets/{ticket_id}/send_reply).

2.  Implementar SPA de revisión:

    - vista simple para /experience/review?token=...,

    - formulario de motivo + comentario,

    - POST a /api/experience/review/submit,

    - mensaje de confirmación.

**Criterios de aceptación**

- Un técnico puede:

  - autenticarse,

  - ver su lista de tickets,

  - filtrar por silenciosos,

  - abrir un ticket,

  - ver timeline,

  - generar un mensaje con IA,

  - enviarlo al usuario,

  - ver cómo varía el tiempo desde la última comunicación.

- Un usuario puede:

  - recibir correo de actualización/cierre,

  - hacer clic en “Solicitar revisión de mi caso”,

  - enviar el formulario,

  - disparar la nota interna en SDP.

**5. Plan de pruebas (alto nivel)**

**5.1. Pruebas unitarias y de integración técnica**

- Pruebas unitarias:

  - lógica de cálculo de hours_since_last_user_contact,

  - lógica de communication_sla_hours por servicio/prioridad,

  - generación y validación de tokens de revisión.

- Pruebas de integración:

  - llamadas al gateway SDP (con datos de prueba),

  - llamadas a IA (escenarios normales y de error),

  - envío de correos con Graph (correo de pruebas).

**5.2. Pruebas funcionales clave**

- Escenario 1: Primera respuesta con IA + cambio de estado a “En
  Proceso”.

- Escenario 2: Ticket que se vuelve silencioso por falta de
  comunicación.

- Escenario 3: Actualización intermedia con IA.

- Escenario 4: Cierre con IA + solicitud explícita de conformidad.

- Escenario 5: Solicitud de revisión de la atención desde correo.

**5.3. UAT (Pruebas de usuario)**

- 2–3 técnicos usando el Copilot en entorno de pruebas con tickets
  reales.

- Validar:

  - utilidad de los mensajes sugeridos por IA,

  - claridad de los indicadores de silencio,

  - facilidad de uso del flujo de revisión.

**6. Plan de despliegue inicial**

1.  Crear servicios en Render:

    - copilot-api,

    - copilot-db,

    - copilot-web.

2.  Configurar variables de entorno según Documento Técnico.

3.  Ejecutar migraciones Alembic en copilot-db.

4.  Cargar datos iniciales:

    - technician_mapping,

    - services_catalog (servicios clave),

    - org_profile,

    - persona_config,

    - settings básicos (incluyendo COMM_SLA_DEFAULT_HOURS).

5.  Probar en entorno de pruebas:

    - GET /health,

    - /api/me,

    - /api/tickets,

    - un flujo completo de:

      - generar mensaje con IA,

      - enviar al usuario,

      - verificar en SDP el correo BCC adjunto al ticket.

6.  Una vez validado en pruebas:

    - replicar configuración en entorno productivo,

    - iniciar con grupo piloto de técnicos.
