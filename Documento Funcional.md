**DISEÑO FUNCIONAL**

Producto: Criteria ServiceDesk Copilot – Módulo de Calidad de
Experiencia de Atención

**1. Objetivo del documento**

Definir el comportamiento funcional del Criteria ServiceDesk Copilot
como capa complementaria a ServiceDesk Plus (SDP), enfocada en:

- Mejorar la experiencia de atención del usuario (no solo los tiempos de
  SLA).

- Asistir al técnico en la redacción y enfoque de sus comunicaciones
  mediante IA.

- Aprovechar:

  - los datos operativos de SDP,

  - un catálogo de servicios,

  - un perfil de organización,

  - y una persona IA predefinida (analista virtual de mesa de
    servicios).

Este documento será la base para el diseño técnico / arquitectura y para
las pruebas de aceptación de la versión 1 (V1).

**2. Alcance de la Versión 1 (V1)**

**2.1. Funcionalidades incluidas**

1.  **Consola Web del Técnico (Copilot UI)**

    - Autenticación (SSO o equivalente).

    - Bandeja “Mis tickets”.

    - Vista detalle de ticket.

    - Panel IA para:

      - Primera respuesta al usuario.

      - Actualizaciones de estado hacia el usuario.

      - Mensaje de cierre con pedido de conformidad.

2.  **Integración con ServiceDesk Plus (SDP)**

    - Lectura de tickets asignados al técnico.

    - Lectura de detalle de ticket (campos principales).

    - Lectura del hilo de conversación del ticket (a través de reporte
      expuesto por API o mecanismo equivalente definido en el diseño
      técnico).

    - Registro de respuestas al usuario como parte del ticket.

    - Cambio básico de estado del ticket (ej. Nuevo → En Proceso, En
      Proceso → Resuelto/Cerrado).

3.  **Uso de Catálogo de Servicios**

    - Asociación de un ticket a un código de servicio (service_code)
      cuando exista mapeo desde campos de SDP (categoría, plantilla,
      UDF, etc.).

    - Lectura de:

      - nombre del servicio,

      - descripción corta orientada al usuario,

      - requisitos clave del solicitante (autorizaciones,
        precondiciones),

      - notas clave para mensajes de:

        - primera respuesta,

        - actualización,

        - cierre,

      - parámetros de política de comunicación recomendada (frecuencia
        máxima sin comunicación al usuario, por prioridad del ticket,
        cuando se definan).

4.  **Perfil de organización (contexto general)**

    - Información configurable sobre la organización:

      - rubro/industria (ej. minería),

      - contexto operativo relevante (ej. operación en mina, seguridad
        como prioridad),

      - servicios críticos para el negocio.

    - Este perfil se usa como contexto general para la IA (tono,
      prioridades).

5.  **Persona del Copilot IA**

    - Rol fijo: analista virtual de Mesa de Servicios.

    - Tono: respetuoso, empático, profesional, claro.

    - Reglas de comunicación (no inventar plazos, no inventar procesos,
      pedir acuerdo al cerrar, etc.).

6.  **Funcionalidad “Interpretar conversación”**

    - Dado el hilo reciente del ticket:

      - resumir qué está buscando el usuario actualmente,

      - identificar posibles brechas de expectativa,

      - sugerir un enfoque para la siguiente respuesta del técnico.

7.  **Soporte a técnicos con credenciales compartidas en SDP**

    - Autenticación en Copilot por usuario corporativo real (ej. cuenta
      O365).

    - Tabla de mapeo usuario_copilot → technician_id_SDP.

    - Uso de una cuenta técnica/API para acceder a SDP, manteniendo
      trazabilidad interna de qué usuario Copilot ejecuta cada acción.

8.  **Base de datos propia del Copilot**

    - Para:

      - configuración (catálogo de servicios, persona IA, perfil de
        organización, mapeos),

      - logs de uso y trazabilidad.

    - No se almacena de forma masiva todo el histórico de conversaciones
      de SDP; el contenido de las conversaciones se obtiene on-demand al
      atender cada ticket.

**2.2. Hipótesis de volumen**

La versión 1 se diseña pensando en organizaciones con:

- Mínimo recomendado: ~200–300 tickets/mes (para que el Copilot tenga
  impacto apreciable).

- Rango objetivo de diseño: hasta ~3,000–5,000 tickets/mes por instancia
  SDP, con picos diarios razonables.

La bandeja del técnico mostrará siempre un subconjunto limitado (sus
tickets), y las consultas de historial se realizarán por ticket, no de
forma masiva sobre todo el universo de tickets.

**3. Actores y Perfiles**

1.  **Técnico de Mesa / Soporte**

    - Usuario principal del Copilot.

    - Ve sus tickets asignados.

    - Utiliza IA para redactar respuestas y cierres.

    - Puede usar “Interpretar conversación” cuando lo necesite.

2.  **Administrador del Copilot**

    - Mantiene:

      - catálogo de servicios (en BD/archivo),

      - configuración de persona IA,

      - perfil de organización,

      - parámetros de umbrales de comunicación (p. ej. “ticket
        silencioso”, por servicio y prioridad),

      - mapeo usuario_copilot → technician_id_SDP.

El rol de supervisor se reconoce como potencial usuario futuro, pero no
forma parte del alcance funcional de V1 (ver sección de roadmap).

**4. Descripción General de la Solución**

El Criteria ServiceDesk Copilot es una aplicación web que se apoya en
tres fuentes principales:

1.  **ServiceDesk Plus (SDP)**  
    Fuente de verdad operativa del ticket:

    - ID, asunto, descripción,

    - requester, estado, prioridad,

    - conversaciones (usuario/técnico) mediante reporte/API,

    - técnico asignado, fechas clave.

2.  **Catálogo de Servicios**  
    Contexto de negocio:

    - qué servicio se está atendiendo (ej. Radios, BI, PC nueva),

    - qué incluye y qué requisitos tiene,

    - mensajes clave según etapa (inicio, seguimiento, cierre),

    - política de comunicación recomendada con el usuario según
      prioridad para ese servicio (cuando exista configuración).

3.  **Perfil de Organización + Persona IA**

    - Perfil de organización:

      - giro del negocio, sensibilidades, servicios críticos.

    - Persona IA:

      - rol, tono, reglas de comunicación.

El técnico trabaja en el Copilot para:

- ver sus tickets,

- entender el contexto (ticket + servicio + organización),

- generar con IA respuestas claras, empáticas y alineadas al servicio,

- registrar esas respuestas en SDP, y

- solicitar o confirmar el cierre con el usuario.

SDP sigue siendo el sistema de registro; el Copilot es la consola
inteligente de atención.

**5. Flujos Funcionales**

**5.1. Autenticación**

**Objetivo:** identificar al técnico y restringir el acceso a los
tickets que le corresponden.

**Flujo:**

1.  El usuario abre la URL del Copilot.

2.  El sistema redirige al proveedor de identidad (SSO/IdP corporativo,
    ej. Azure AD).

3.  Tras autenticarse, el Copilot recibe un token (ej. JWT) con:

    - correo / UPN del usuario.

4.  El backend consulta la tabla de mapeo interna:

    - usuario_copilot → technician_id_SDP.

5.  Si el mapeo existe:

    - se muestra la bandeja “Mis tickets”.

6.  Si NO existe:

    - se muestra un mensaje de error indicando que su usuario no está
      configurado como técnico válido para el Copilot.

El login corporativo del técnico no tiene por qué ser el mismo usuario
de SDP; la relación se controla mediante el mapeo interno y una cuenta
técnica/API para SDP.

**5.2. Bandeja “Mis Tickets”**

**Objetivo:** permitir al técnico gestionar su carga de trabajo con foco
en experiencia de atención.

**Elementos funcionales:**

- **Buscador por:**

  - ID de ticket,

  - asunto,

  - nombre del requester.

- **Filtros rápidos:**

  - Prioridad (P1, P2, P3, etc.),

  - Estado (Nuevo, Asignado, En Proceso, Resuelto, etc.),

  - “Silenciosos”: tickets sin actualización al usuario más allá del
    umbral de tiempo definido por la política de comunicación (ver
    reglas de negocio), según su servicio/prioridad o el valor por
    defecto global.

- **Lista de tickets del técnico, mostrando al menos:**

  - ID,

  - Asunto,

  - Requester,

  - Prioridad,

  - Estado,

  - Tiempo desde la última respuesta del técnico al usuario,

  - Indicador visual si el ticket ha superado el umbral de “SLA de
    comunicación” para su servicio/prioridad (ej. icono de “Necesita
    actualización”),

  - Nombre del servicio asociado (cuando existe service_code).

**Flujo:**

1.  El frontend llama a GET /api/tickets?scope=mine.

2.  El backend:

    - obtiene el technician_id_SDP desde el mapeo,

    - consulta a SDP por tickets asignados a ese técnico (usando
      API/consulta eficiente),

    - para cada ticket:

      - determina la última comunicación pública del técnico al usuario
        (ver abajo),

      - calcula el tiempo transcurrido desde esa comunicación,

      - determina si se ha superado el umbral de comunicación
        correspondiente a su servicio/prioridad (o el valor por
        defecto),

    - aplica filtros,

    - devuelve la lista en formato estándar.

3.  Al seleccionar un ticket, se abre la vista detalle.

**Definición funcional de “tiempo desde la última respuesta al usuario”
y “silenciosos”:**

- El Copilot considera como **“respuesta al usuario”** cualquier evento
  en el historial del ticket que cumpla:

  - proviene de un técnico (incluyendo mensajes enviados a través del
    Copilot), y

  - es una respuesta pública (no una nota interna).

- A partir del historial entregado por SDP (vía reporte/API/gateway), el
  sistema identifica el último evento que cumple estos criterios y
  registra su fecha/hora como **última comunicación del técnico al
  usuario**.

- El tiempo desde la última respuesta al usuario es la diferencia entre
  la fecha/hora actual y esa última comunicación.

- Un ticket se considera **“silencioso”** cuando:

  - se encuentra en un estado activo (Nuevo, Asignado, En Proceso u
    otros que defina el cliente), y

  - el tiempo desde la última respuesta al usuario **supera el umbral
    máximo de silencio** definido por la política de comunicación para:

    - su service_code y prioridad, si el servicio tiene una
      configuración específica, o

    - el valor global por defecto, si no existe una configuración por
      servicio.

**5.3. Vista Detalle de Ticket**

**Objetivo:** brindar contexto suficiente para atender al usuario sin
abrir la interfaz de SDP.

**Elementos:**

- **Cabecera del ticket:**

  - ID,

  - Asunto,

  - Requester (nombre, correo),

  - Prioridad,

  - Estado,

  - SLA (si está disponible),

  - Campo informativo: “Última comunicación al usuario: hace X
    horas/días”, calculado según la definición anterior,

  - Mensaje de recomendación cuando se ha superado el umbral de
    comunicación para el servicio/prioridad, por ejemplo:  
    “Para este tipo de servicio se recomienda actualizar al usuario cada
    N horas. Han pasado M horas desde la última comunicación.”,

  - Botón “Abrir en SDP” (link directo a la ficha en SDP).

- **Información de servicio (cuando el ticket tiene service_code):**

  - Nombre del servicio,

  - Descripción corta orientada al usuario,

  - Requisitos / notas relevantes (resumen desde catálogo),

  - Información resumida de la política de comunicación recomendada para
    ese servicio/prioridad.

- **Descripción inicial del ticket.**

- **Timeline de conversaciones:**

  - Mensajes del usuario (respuestas públicas),

  - Respuestas de técnicos (respuestas públicas),

  - Notas internas en pestaña separada,

  - Cada mensaje con:

    - autor,

    - fecha/hora,

    - tipo (usuario / técnico, público / interno).

**Fuente de datos para el timeline:**

- Las conversaciones se obtienen desde SDP mediante:

  - un reporte expuesto vía API, o

  - otro mecanismo de lectura definido en el diseño técnico (ej. lectura
    de tablas request + history con acceso de solo lectura).

El Copilot no almacena de forma permanente todo el contenido de las
conversaciones; las trae bajo demanda cuando se abre el ticket.

**5.4. Panel IA – Estructura General**

**Objetivo:** centralizar la interacción del técnico con la IA para
redactar mensajes de calidad.

**Elementos:**

- Selector de tipo de mensaje:

  - Primera respuesta.

  - Actualización.

  - Cierre.

- Campo “Borrador del técnico”:

  - texto corto donde el técnico puede escribir su idea inicial, para
    que la IA la refine o complete.

- Campo “Mensaje sugerido por IA”:

  - área de texto grande donde aparece el mensaje generado/mejorado por
    la IA,

  - siempre editable por el técnico.

- Botones:

  - “Generar con IA”:

    - usa el borrador (si existe) y el contexto (ticket + servicio +
      organización + historial).

  - “Regenerar”:

    - genera una nueva propuesta.

  - “Enviar al usuario”:

    - registra el mensaje en SDP y dispara la notificación al usuario
      según el modelo definido.

- Opciones de estado:

  - “Cambiar estado a En Proceso” (para primera respuesta).

  - “Marcar como Resuelto/Cerrado” (para cierre).

**5.5. Flujo: Primera Respuesta**

**Objetivo funcional:** dar una primera respuesta rápida, clara y
empática al usuario.

**Flujo:**

1.  El técnico abre un ticket en estado “Nuevo” o equivalente.

2.  En el panel IA selecciona “Primera respuesta”.

3.  Escribe un borrador breve o deja el campo vacío para que la IA
    proponga desde cero.

4.  Presiona “Generar con IA”.

5.  El backend:

    - obtiene datos de SDP (asunto, descripción, requester, prioridad,
      estado),

    - intenta derivar service_code y consulta el catálogo (si existe),

    - lee el perfil de organización,

    - obtiene la configuración de la persona IA,

    - construye el prompt con:

      - contexto del ticket,

      - contexto del servicio,

      - contexto de la organización,

      - rol/tono/reglas de la persona IA,

      - tipo de mensaje (primera respuesta),

      - borrador del técnico (si existe),

    - llama al modelo de IA.

6.  El mensaje sugerido aparece en el campo “Mensaje sugerido por IA”.

7.  El técnico revisa y ajusta si lo considera necesario.

8.  Al presionar “Enviar al usuario”:

    - se registra la comunicación en SDP,

    - se envía notificación al usuario por correo (según modelo definido
      en 5.10),

    - cuando corresponda, se cambia el estado a “En Proceso”.

**Reglas de contenido:**

- La IA debe:

  - agradecer el contacto,

  - demostrar que se entendió la solicitud (resumen claro),

  - indicar que se está trabajando en el caso y qué se puede esperar
    (sin inventar plazos concretos),

  - utilizar, cuando corresponda, fragmentos del catálogo (ej. breve
    explicación del servicio o requisitos).

**5.6. Flujo: Actualización**

**Objetivo funcional:** evitar silencios prolongados y mantener al
usuario informado sobre el progreso.

**Flujo:**

1.  El técnico abre un ticket ya atendido previamente.

2.  En el panel IA selecciona “Actualización”.

3.  Escribe un borrador breve (por ejemplo, “Pendiente de proveedor”) o
    deja que la IA sugiera con base en el historial.

4.  Presiona “Generar con IA”.

5.  El backend:

    - consulta las últimas interacciones del ticket (timeline),

    - consulta el catálogo de servicios (si aplica),

    - toma en cuenta la persona IA y el perfil de organización,

    - genera un mensaje que explique el estado actual en lenguaje
      simple.

6.  El técnico revisa, edita y presiona “Enviar al usuario”.

7.  El backend:

    - registra la comunicación en SDP,

    - dispara la notificación al usuario según el modelo 5.10.

**Reglas de contenido:**

- Evitar tecnicismos innecesarios.

- No prometer fechas si no están definidas por el servicio o el
  contexto.

- Puede indicar:

  - qué se está haciendo,

  - qué se está esperando (respuesta de otra área, proveedor),

  - cuál es el próximo paso lógico.

La decisión de cuándo hacer una actualización se apoya en los
indicadores de “tiempo desde la última respuesta al usuario” y en la
política de comunicación por servicio/prioridad (tickets “silenciosos”).

**5.7. Flujo: Cierre**

**Objetivo funcional:** cerrar el caso con una explicación clara y un
pedido de conformidad al usuario.

**Flujo:**

1.  El técnico considera que el ticket está resuelto.

2.  En el panel IA selecciona “Cierre”.

3.  Escribe un breve resumen técnico de lo que hizo o deja que la IA
    proponga con el contexto existente.

4.  Presiona “Generar con IA”.

5.  El backend:

    - usa el contexto del ticket (acciones pasadas),

    - usa el catálogo de servicios (para recordar alcances y
      responsabilidades),

    - usa la persona IA y el perfil de organización,

    - genera un mensaje con estructura:

      - qué problema se identificó (en lenguaje usuario),

      - qué acciones se realizaron,

      - cuál es el estado actual del servicio/equipo,

      - recordatorios relevantes (según catálogo),

      - pregunta explícita de conformidad:

        - “¿Estarías de acuerdo en que demos por cerrado el caso?”

6.  El técnico revisa y envía.

7.  Cuando corresponda, el backend cambia el estado en SDP a
    “Resuelto/Cerrado”.

**Reglas:**

- Siempre dejar la puerta abierta a que el usuario pida aclaraciones o
  indique que el problema persiste.

- No cerrar tickets sin un mensaje final claro (ese es parte del valor
  del Copilot).

**5.8. Funcionalidad “Interpretar conversación”**

**Objetivo:** ayudar al técnico a entender qué está buscando el usuario
y si hay brechas de expectativa, especialmente en tickets con muchas
idas y vueltas o mensajes confusos.

**UI:**

- Botón en la vista detalle, cercano al timeline:

  - “Interpretar conversación” / “¿Qué está pasando en este ticket?”

**Flujo:**

1.  El técnico percibe que la conversación es confusa o que hay
    malentendidos.

2.  Presiona el botón “Interpretar conversación”.

3.  El frontend llama a POST /api/ia/interpretar_conversacion con:

    - ticket_id.

4.  El backend:

    - obtiene los últimos N mensajes del historial (usuario y técnico),

    - obtiene las últimas N notas internas según la configuración de uso
      de notas en IA,

    - usa IA para:

      - identificar la intención actual del usuario,

      - detectar posibles brechas de expectativa (ej. usuario piensa que
        falta X cuando en realidad falta Y),

      - generar una sugerencia de enfoque para la siguiente respuesta.

5.  El resultado se muestra en un panel de solo lectura para el técnico,
    por ejemplo:

    - “Intención actual del usuario:”  
      “…”

    - “Brecha de expectativa detectada:”  
      “…”

    - “Sugerencia de enfoque para tu próxima respuesta:”  
      “…”

**Reglas:**

- Esta función es asistencial interna:

  - el texto no se envía al usuario,

  - no cambia estados ni ejecuta acciones automáticas.

- Debe servir como guía para que el técnico entienda mejor el caso y
  luego use el Panel IA para generar el mensaje adecuado.

**5.9. Registro de respuesta en SDP**

**Objetivo:** asegurar que toda comunicación generada desde el Copilot
quede reflejada correctamente en el ticket de SDP.

**Flujo:**

1.  Al presionar “Enviar al usuario”, el frontend envía al backend:

    - ticket_id,

    - mensaje_final (texto revisado por el técnico),

    - tipo_mensaje (primera_respuesta, actualizacion, cierre),

    - accion_estado (si debe cambiar estado: En Proceso, Resuelto,
      etc.).

2.  El backend:

    - envía la comunicación al usuario por correo según el modelo
      definido en 5.10, incluyendo la referencia al ID del ticket que
      permite a SDP asociar el mensaje,

    - aplica el cambio de estado si se ha solicitado.

3.  Si la operación es exitosa:

    - el mensaje aparece en el hilo del ticket en SDP,

    - se actualiza el timeline en la vista detalle,

    - se muestra confirmación al técnico.

4.  Si falla:

    - se informa del error,

    - el texto del mensaje no se pierde (el técnico puede copiar/pegar
      manualmente si fuera necesario).

**5.10. Modelo de envío de mensajes al usuario**

Cuando el técnico presiona “Enviar al usuario”, el Copilot debe cumplir
simultáneamente:

1.  **Registrar la comunicación en SDP**, de forma que:

    - el mensaje quede ligado al ticket,

    - sea visible en el hilo de conversaciones del ticket.

2.  **Notificar al usuario por correo electrónico**, utilizando:

    - la misma dirección de remitente que el cliente usa en SDP para
      notificaciones de mesa (o la cuenta que se defina para el
      Copilot),

    - el contenido del mensaje aprobado por el técnico.

**Modelo funcional elegido para V1:**

- El Copilot enviará un correo al solicitante del ticket:

  - desde la cuenta de Mesa de Servicios (o cuenta designada),

  - incluyendo en el asunto o en el cuerpo el ID del ticket entre \##
    (ej. \##INC-123##),

  - con copia oculta (BCC) al buzón de correo que SDP utiliza para
    registrar respuestas (buzón de entrada de SDP).

- SDP, al recibir este correo con el ID entre \##, adjuntará el mensaje
  automáticamente al hilo del ticket correspondiente.

- Desde el punto de vista del técnico:

  - “Enviar al usuario” siempre implica:

    - que el usuario reciba un correo con la actualización, y

    - que la actualización quede registrada en el ticket de SDP mediante
      el mecanismo de correo con ID y BCC.

No se contemplan rutas alternativas para V1; el mecanismo descrito es el
camino estándar para registrar la comunicación y notificar al usuario.

**5.11. Solicitud de revisión de la atención por parte del usuario**

**Objetivo**  
Permitir que el usuario pueda indicar, durante la vida del ticket, que
no está conforme con la atención o que la situación se ha vuelto más
sensible, sin esperar al cierre del caso.

**Alcance**

- Esta funcionalidad forma parte de la versión 1 del producto.

- Debe implementarse con un parámetro de configuración por organización
  que permita mostrar u ocultar la opción al usuario final, sin eliminar
  la lógica del lado del servidor.

**Reglas de visibilidad**

- El enlace o texto de acción (por ejemplo “Solicitar revisión de mi
  caso”):

  - No se muestra en la primera respuesta al usuario.

  - Se incluye en:

    - correos de actualización, y

    - correos de cierre generados por el Copilot,

  - siempre que la organización tenga habilitada esta opción en su
    configuración.

**Flujo para el usuario**

1.  El usuario recibe un correo del Copilot (actualización o cierre) que
    incluye una frase del tipo:  
    “Si consideras que esta atención no está respondiendo a tu
    necesidad, puedes solicitar una revisión de tu caso haciendo clic
    aquí.”

2.  Al hacer clic, se abre una página del Copilot asociada al ticket.

3.  La página muestra:

    - una pregunta breve (ej. “¿Qué deseas indicarnos?”),

    - opciones predefinidas (ej. “No estoy de acuerdo con esta
      respuesta”, “La situación se ha vuelto más urgente”, “Otro”),

    - un campo de comentario corto (texto libre).

4.  El usuario envía el formulario.

**Comportamiento interno del Copilot**

Al recibir una solicitud de revisión, el sistema debe:

1.  Registrar una nota interna asociada al ticket en SDP, con:

    - el tipo de solicitud seleccionada,

    - el comentario del usuario (si lo hay).

2.  Marcar en la BD interna del Copilot un indicador:

    - experience_review_requested = true para ese ticket.

**Reglas de negocio**

- La “Solicitud de revisión” es una señal de experiencia, no una orden
  automática de cambio de prioridad:

  - no cambia automáticamente la prioridad,

  - no modifica el SLA,

  - no escala jerárquicamente por sí misma.

- Su objetivo es:

  - advertir al técnico de que el usuario no está conforme,

  - permitir que el Copilot y el técnico revisen con mayor cuidado el
    caso,

  - servir de insumo futuro para vistas de supervisión y análisis de
    experiencia.

La notificación automática a supervisores, jefes u otros canales (ej.
Teams) cuando hay una solicitud de revisión se considera parte del
roadmap y no se implementa en V1.

**6. Datos y Fuentes de Contexto para la IA**

**6.1. Datos provenientes de SDP**

- **Ticket:**

  - ID,

  - Asunto,

  - Descripción inicial,

  - Requester (nombre, correo),

  - Estado,

  - Prioridad,

  - Grupo de soporte, técnico asignado,

  - Fechas (creación, última actualización),

  - SLA (si aplica).

- **Historial:**

  - Mensajes públicos (texto, autor, fecha/hora),

  - Notas internas (texto, autor, fecha/hora).

**6.2. Catálogo de Servicios**

Por service_code:

- Nombre del servicio.

- Descripción corta orientada al usuario.

- Requisitos clave del solicitante (autorizaciones, condiciones).

- Notas sugeridas para:

  - primera respuesta,

  - actualizaciones,

  - cierre (recordatorios de responsabilidades, recomendaciones).

- Parámetros de política de comunicación recomendada:

  - tiempos máximos de silencio permitidos antes de volver a comunicarse
    con el usuario, por prioridad del ticket (ej. P1, P2, P3).

  - Si un servicio no define estos parámetros, se utilizará la política
    global por defecto de la organización.

**6.3. Perfil de Organización**

Configuración general:

- Rubro / industria (ej. minería).

- Contexto operativo relevante (ej. operación en mina, foco en
  seguridad, continuidad de operación).

- Servicios más críticos para el negocio (informativo).

- Cualquier sensibilidad que deba cuidar la IA en el tono de los
  mensajes.

**6.4. Persona IA**

- **Rol:**

  - Analista virtual de Mesa de Servicios, orientado a asegurar que el
    usuario se siente informado, respetado y acompañado.

- **Tono:**

  - respetuoso,

  - empático,

  - profesional,

  - claro.

- **Reglas:**

  - no inventar procesos ni requisitos que no estén en
    catálogo/realidad,

  - no prometer plazos concretos si no están definidos,

  - explicar en lenguaje simple qué se hizo y qué sigue,

  - en cierre, pedir confirmación antes de dar el caso por concluido.

**6.5. Uso de notas internas**

- Las notas internas se utilizan como contexto adicional para la IA (ej.
  horarios en que el usuario suele atender, intentos previos de
  contacto).

- No deben citarse literalmente en los mensajes al usuario.

- No deben exponer comentarios negativos o sensibles sobre el usuario.

- El sistema limitará el uso de notas internas a las últimas N notas
  configuradas (por ejemplo, 3–5) y un parámetro de configuración
  permitirá activar o desactivar el uso de notas internas como contexto
  para IA según las políticas del cliente.

**7. Reglas de Negocio Globales**

1.  **Control humano obligatorio**

    - La IA nunca envía mensajes de forma automática; el técnico siempre
      revisa y aprueba.

2.  **Modo genérico vs. modo con catálogo**

    - Si hay service_code: se enriquece el mensaje con contexto del
      servicio.

    - Si no hay: se opera solo con datos de SDP + persona IA + perfil de
      organización.

3.  **Persona IA centralizada**

    - No modificable por el técnico; se gestiona centralmente por el
      administrador del Copilot.

4.  **Privacidad**

    - No se envían a la IA datos sensibles que no aporten valor a la
      comunicación.

    - El almacenamiento interno se limita a configuración y logs, no a
      replicar masivamente el texto de todas las conversaciones.

5.  **Soporte a credenciales compartidas de SDP**

    - El mapeo usuario_copilot → technician_id_SDP permite:

      - escenarios en los que varios usuarios reales compartan un
        técnico SDP,

      - sin perder trazabilidad en el Copilot.

6.  **Política de comunicación hacia el usuario (SLA de comunicación por
    servicio/prioridad)**

    - Además del SLA técnico de SDP (respuesta/resolución), el Copilot
      maneja un “SLA de comunicación” que define el tiempo máximo que
      debería pasar sin que el técnico vuelva a comunicarse con el
      usuario mientras el ticket está en un estado activo.

    - Esta política se define en dos niveles:

      1.  Valor global por defecto (configurable por organización):

          - Ejemplo: “no más de 24 horas sin comunicación al usuario en
            tickets activos”.

      2.  Overrides por servicio y prioridad, definidos en el catálogo
          de servicios:

          - Para cada service_code se pueden configurar tiempos máximos
            de silencio permitidos según la prioridad del ticket.

    - Si un servicio no tiene configuración específica, se aplica el
      valor global por defecto.

    - El Copilot:

      - calcula, para cada ticket, el tiempo transcurrido desde la
        última respuesta pública del técnico al usuario,

      - compara ese tiempo con el umbral de comunicación correspondiente
        a su servicio/prioridad (o al valor global),

      - marca como “silencioso” y resalta en la UI aquellos tickets
        activos que hayan superado dicho umbral.

    - El objetivo es:

      - ayudar al técnico a priorizar a quién debe “decirle algo hoy”,

      - diferenciar entre servicios donde se espera comunicación muy
        frecuente (incidente crítico) y servicios donde la comunicación
        puede ser más espaciada (compras, trámites),

      - reforzar la calidad de experiencia de atención más allá del mero
        cumplimiento de SLA técnicos.

**8. Casos Especiales**

**8.1. Técnicos con credenciales compartidas en SDP**

- Varios técnicos reales pueden usar un mismo login de SDP.

- El Copilot:

  - autentica a cada persona con su usuario corporativo,

  - mapea a un technician_id_SDP,

  - usa una cuenta técnica/API para SDP.

- La trazabilidad real se mantiene en los logs del Copilot (quién envió
  qué mensaje y cuándo).

**8.2. Tickets sin servicio identificado**

- Si no se puede derivar un service_code:

  - el Copilot omite el contexto de catálogo,

  - opera solo con ticket + persona IA + perfil de organización.

- En estos casos se utiliza la política global por defecto de
  comunicación (sin overrides específicos por servicio).

**8.3. Caída de IA o de SDP (modo degradado)**

- Si IA no responde:

  - se informa al técnico,

  - se permite redactar manualmente en el campo de mensaje sin perder
    texto.

- Si SDP no responde:

  - no se registra la nota,

  - el texto se conserva en el UI para que el técnico pueda copiar/pegar
    en SDP si fuera necesario.

**9. Fuera de Alcance V1 y Roadmap (No forma parte del desarrollo
actual)**

1.  Gestión del catálogo de servicios desde interfaz gráfica

    - CRUD de servicios, requisitos y mensajes clave desde la UI del
      Copilot.

2.  Módulos de calidad de documentación interna

    - Evaluación automática de causa raíz, solución técnica,
      verificación, etc.

3.  Módulos de calidad de clasificación / data quality

    - Reglas para categorías, subcategorías y UDFs de SDP.

4.  Dashboards y KPIs avanzados para supervisores

    - métricas de experiencia, tickets silenciosos, análisis por
      servicio/área, etc.

5.  Uso explícito de sentimiento / clima emocional como indicador visual

    - semáforos de sentimiento por ticket, tendencias emocionales, etc.

6.  Integraciones adicionales (Teams, paneles para supervisores,
    notificaciones de revisión, etc.)

    - notificaciones proactivas en Teams o correo a supervisores cuando
      hay solicitudes de revisión,

    - resúmenes automáticos para jefaturas.
