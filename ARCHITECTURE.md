# NJM OS — Manual de Arquitectura con Claude Cowork

# NJM OS — Manual de Arquitectura con Claude Cowork (v2 Interna)

## 1\. El Entorno Operativo: Claude Cowork

La integración de **NJM OS** con Claude Cowork transforma el sistema de una interfaz web tradicional a un entorno de automatización de escritorio de alto rendimiento. Los agentes dejan de ser entidades de chat para convertirse en operadores autónomos que interactúan directamente con archivos locales compartidos, redactando documentos finales y organizando la información de la agencia.

## 2\. Roles y Responsabilidades (La Regla 80/20)

### El Agente CEO (Guardián del ADN y Estratega)

Funciona como el director de inteligencia de la agencia, asegurando que la identidad de cada marca sea inquebrantable. Absorbe el **80% del trabajo macro-estratégico**.

* **Onboarding Automático:** Escanea carpetas locales con archivos desordenados (manuales, PDFs, historiales de Slack), categoriza la información, realiza un *Gap Analysis* y redacta el "Libro Vivo" definitivo.  
* **Arbitraje en Background:** Levanta "tarjetas rojas" antes de cualquier aprobación si detecta que el PM o el Encargado Real proponen estrategias disonantes con el Libro Vivo.

### El Agente PM (Motor Operativo y Metodológico)

Es el consultor junior avanzado y ejecutor incansable. Asume el **80% del trabajo micro-táctico**, eliminando las horas de creación manual y justificación.

* **Generación de Entregables:** Programado para operar en background, extrae métricas y crea automáticamente reportes, planes de medios o briefs en formatos nativos (PowerPoint, Excel) directo en las carpetas de trabajo.  
* **Presentación de la Tarjeta de Sugerencia:** Sintetiza su trabajo en un formato claro: Propuesta \+ Fundamento Teórico (ej. Matriz de Ansoff) \+ Check de Coherencia.  
* **Ejecución Asíncrona:** Al recibir la aprobación humana, aplica formatos finales, renombra archivos con las convenciones de la agencia y los deja listos para envío.

### El Encargado Real (Humano)

El account manager o director. Abandona la página en blanco para enfocarse en el **20% de máximo impacto**: dirección, negocio y empatía.

* **Revisión Asíncrona:** Llega a su escritorio para encontrar entregables ya maquetados por Claude Cowork.  
* **Decisión Activa:** Evalúa las Tarjetas de Sugerencia del PM y ejerce su autoridad: aprueba, ajusta o escala al CEO.  
* **Relaciones Públicas:** Con la producción resuelta, invierte su tiempo en videollamadas, gestión de clientes y crecimiento de la cuenta.

---

## 3\. Flujo Práctico: Un Día en la Agencia (Campaña Q3)

1. **Petición (Humano):** *"Necesito la propuesta de campaña para Q3 de la Marca B, basada en penetración de mercado".* El humano delega y sale del escritorio.  
2. **Desarrollo en Paralelo (Agentes):** El PM investiga la teoría pertinente (Ansoff), la cruza con el Libro Vivo de la Marca B (bajo supervisión en background del CEO), redacta copys y genera los slides en un PowerPoint local.  
3. **Firma (Humano):** El humano regresa, revisa la validación teórica del PM y aprueba el documento ya terminado. Un trabajo de tres días condensado en 30 minutos de pura revisión directiva.

# NJM OS \- STACK TÉCNICO

**STACK TÉCNICO DEFINIDO:**

* **Backend & Orquestación:** Python 3.11+, FastAPI (para los endpoints) y LangGraph (para la máquina de estados y ruteo de agentes).  
* **LLM Core:** Anthropic API (Claude 3.5 Sonnet) utilizando *Tool Use* estricto.  
* **Frontend:** Next.js 14 (App Router), React, Tailwind CSS.  
* **Persistencia:** Archivos locales (Markdown/JSON) simulando el entorno "Cowork".

# CEO- Banco de Ingesta del Agente CEO: Entrevista

### **Banco de Ingesta del Agente CEO: Entrevista a Profundidad**

#### **Vector 1: Núcleo Estratégico (Brand Core)**

*Si la marca no tiene manuales de identidad o definiciones corporativas claras.*

* **Proposición de Valor Única (UVP):** "¿Cuál es la promesa exacta y cuantificable que la marca le hace al mercado, y por qué el cliente debería creerla por encima de la alternativa más barata?"  
* **Posicionamiento de Mercado:** "Si mapeamos a la marca en un eje cartesiano frente a la competencia, ¿cuáles son las dos variables principales que definen nuestro territorio? (ej. Precio vs. Especialización, Velocidad vs. Calidad)."  
* **Identidad Operativa:** "Para estandarizar el criterio del Agente PM, ¿cuál es el modelo de comportamiento corporativo o arquetipo metodológico que la marca debe proyectar en todas sus comunicaciones escritas y visuales?"  
* **Barreras de Marca:** "¿Cuáles son las líneas rojas innegociables? Es decir, ¿qué es lo que esta marca *nunca* haría o diría, incluso si eso significara perder una venta?"

#### **Vector 2: Modelo de Negocio y Economía de la Oferta**

*Un CEO no pide "presupuesto", evalúa el riesgo financiero de la operación.*

* ***Stress Test de Márgenes:** "Si el Costo de Adquisición de Cliente (CAC) en nuestros canales principales sufriera una inflación del 30% el próximo trimestre, ¿la estructura de precios actual puede absorber el impacto, o la unidad de negocio entra en pérdidas operativas?"*  
* ***Distribución de Capital (Risk/Reward):** "Del capital total disponible para crecimiento, ¿qué porcentaje exige un Retorno de Inversión (ROI) inmediato a 30 días para sostener el flujo de caja, y qué porcentaje tiene autorización directiva para quemarse en experimentación a largo plazo?"*  
* ***Velocidad de Caja (Cash Conversion Cycle):** "Desde el momento en que invertimos un dólar en adquisición hasta que ese dólar regresa a la cuenta bancaria de la empresa con utilidad, ¿cuántos días transcurren en promedio?"*

*Si no hay datos sobre cómo la empresa estructura su rentabilidad.*

* **Estructura de Ingresos:** "Categorizando el portafolio bajo una matriz BCG, ¿cuál es el producto/servicio 'Estrella' que financia el crecimiento y cuál es el producto 'Vaca Lechera' que sostiene la operación?"  
* **Unit Economics:** "¿Cuál es el Ticket Promedio actual, el Ciclo de Vida del Cliente (LTV) proyectado y cuál es el Costo de Adquisición de Cliente (CAC) máximo tolerable para mantener un margen operativo sano?"  
* **Estrategia de Pricing:** "El modelo de precios actual, ¿está diseñado para penetración agresiva de mercado, maximización de márgenes (premium), o recurrencia (suscripción)?"  
* **Fosos Económicos (Moats):** "¿Cuál es la principal barrera de entrada que protege los márgenes de la empresa ante nuevos competidores? (ej. Propiedad intelectual, red de distribución, economías de escala, costo de cambio para el usuario)."

#### **Vector 3: Mapeo de Audiencia y Mercado**

*Si no hay perfiles estructurados o investigación de mercado previa.*

* **Jobs-to-be-Done (JTBD):** "Bajo esta metodología, ¿cuál es el 'trabajo' funcional y el 'trabajo' socioemocional específico para el cual el cliente 'contrata' a la marca?"  
* **Fricción Transaccional:** "¿Cuál es la principal objeción documentada o el punto de fricción que impide que los prospectos calificados cierren la compra hoy mismo?"  
* **Segmentación Basada en Comportamiento:** "Más allá de la demografía básica, ¿cuál es el evento detonante (trigger event) que hace que el prospecto comience activamente a buscar nuestra solución?"  
* **Criterios de Decisión:** "Cuando el cliente evalúa nuestra oferta frente a la competencia final, ¿cuál es el criterio de desempate real? (ej. Tiempo de entrega, soporte técnico, estatus percibido)."

#### **Vector 4: Ecosistema Competitivo**

*Si no hay auditoría de mercado o análisis de competencia.*

* **Competencia Directa:** "Nombra a los tres competidores directos que están pujando por el mismo presupuesto del cliente y cuál es su principal vulnerabilidad táctica."  
* **Competencia Indirecta:** "¿Qué solución alternativa (que resuelve el problema con un método totalmente distinto) representa la mayor amenaza de sustitución a largo plazo?"  
* **Saturación de Categoría:** "¿Cuál es el canal o la táctica de marketing que toda la industria utiliza por defecto, y que nosotros deberíamos evitar o disrumpir para ganar cuota de atención?"

#### **Vector 5: Infraestructura de Canales y Touchpoints**

*Un CEO previene el colapso operativo derivado del éxito del marketing.*

* ***Punto de Quiebre Operativo:** "Si las tácticas del Agente PM tienen un éxito rotundo y triplican la demanda comercial mañana mismo, ¿en qué punto exacto se rompe la operación actual de la empresa (capacidad de los servidores, logística de entregas, horas-hombre del equipo de soporte)?"*  
* ***Deuda Técnica de Adquisición:** "¿Existe algún proceso manual insostenible (ej. pasar leads de un Excel a otro a mano) que debamos automatizar obligatoriamente antes de inyectar más volumen al sistema?"*

*Si no hay un mapeo del funnel actual ni inventario de activos.*

* **Arquitectura de Conversión (Funnel):** "Describe el camino crítico de adquisición actual: desde el primer impacto publicitario o de búsqueda hasta la firma del contrato o checkout. ¿Dónde está el cuello de botella más grave?"  
* **Activos Propietarios:** "¿Cuál es el activo de primera parte (First-Party Data) más valioso que posee la marca actualmente? (ej. Lista de emails limpia de 10k usuarios, tráfico orgánico mensual, CRM depurado)."  
* **Capacidad Operativa de Ejecución:** "¿Cuál es el presupuesto mensual exacto asignado a pauta de adquisición y qué recursos internos (diseñadores, vendedores) están disponibles para absorber el volumen de leads generado por el sistema?"

#### **Vector 6: Histórico y Aprendizajes**

*Si no hay reportes de desempeño de años anteriores.*

* **Auditoría de Éxitos:** "En los últimos 18 meses, ¿cuál ha sido la campaña o iniciativa táctica que ha generado el mayor Retorno de Inversión (ROI) y por qué creemos que funcionó?"  
* **Autopsia de Fracasos:** "¿Existe alguna campaña, canal o estrategia reciente que haya consumido recursos sin generar tracción comercial comprobable? ¿Cuál fue el diagnóstico de ese fallo?"  
* **Deuda Estratégica:** "¿Qué práctica obsoleta, software legado o proceso ineficiente sigue vivo en la operación de marketing por simple inercia corporativa?"

#### **Vector 7: Objetivos y KPIs (North Star)**

*Si la marca no tiene métricas clave de desempeño definidas.*

* **Métrica Estrella (North Star Metric):** "¿Cuál es el único número en el panel de control que, si mejora sistemáticamente, garantiza que la marca está creciendo de forma saludable? (ej. Tasa de retención a 90 días, MQLs generados por semana)."  
* **Objetivo de Negocio Macro (12 meses):** "En términos puramente comerciales, ¿qué debe lograr esta marca en un año para que la operación se considere un éxito rotundo? (ej. X millones en facturación, abrir X nuevos mercados)."  
* **Objetivo Táctico (Q Actual):** "Para este trimestre en curso, ¿cuál es la meta de marketing innegociable a la que el Agente PM debe alinear el 100% de sus sugerencias y recursos tácticos?"

#### **Vector 8: Board Governance y Mitigación de Riesgo**

*La regla de oro del CEO: Proteger a la empresa de demandas, multas y crisis de reputación.*

* **Zonas Rojas (Compliance):** "¿Existen regulaciones legales, normativas industriales (ej. restricciones médicas, financieras) o políticas de privacidad estrictas que los entregables del Agente PM tienen prohibido infringir bajo cualquier circunstancia?"  
* **Riesgo de Relaciones Públicas (PR Risk):** "¿Cuál es el ángulo discursivo o la asociación de marca que representaría una amenaza letal para la reputación corporativa frente a los stakeholders clave?"  
* **Propiedad Intelectual:** "¿Qué metodologías, bases de datos o secretos industriales conforman la ventaja injusta de esta empresa y deben mantenerse estrictamente confidenciales, fuera del alcance de modelos lingüísticos externos?"

# CEO-Las 3 Funciones del Agente CEO

### **Las 3 Funciones del Agente CEO**

Para que este nodo del sistema asuma la verdadera dirección, su lógica de evaluación interna (y sus alertas rojas) ahora procesa estas tres dimensiones antes de aprobar cualquier Libro Vivo:

1. **Strategy Analyzer (Visión Sistémica):** Detecta dependencias. Entiende que una estrategia de marketing agresiva no sirve de nada si el equipo de ventas no tiene un CRM configurado para recibir los leads.  
2. **Financial Scenario Modeling (Asignación de Capital):** Piensa en términos de *Runway*, flujo de caja y protección de márgenes. No aprueba campañas por ser "creativas", las aprueba si la matemática de adquisición tiene sentido.  
3. **Board Governance & Risk Management:** Actúa como el escudo de la empresa. Detecta riesgos regulatorios, crisis de relaciones públicas potenciales y protege los activos intangibles.

# CEO-PENDIENTES

### **1\. El Prompt de Sistema Maestro (System Prompt)**

Esta es la instrucción raíz (el "cerebro") que se inyecta al modelo al inicializar el agente. No es un resumen del proyecto, es un conjunto de reglas inquebrantables. Debe contener:

* **Persona y Tono:** Definirlo explícitamente como un C-Level Advisor implacable, no como un asistente virtual servicial.  
* **Regla de Cero Alucinación:** Instrucciones estrictas de que si un vector de los 8 definidos está vacío, *debe* preguntar y *nunca* inventar datos para rellenarlo.  
* **Protocolo de Bloqueo:** La orden de detener el proceso y no generar el "Libro Vivo" hasta que el "Gap Analysis" esté resuelto al 100%.

### 

**Prompt de Sistema Maestro: Agente CEO (NJM OS)**

Plaintext

\*\*\[ROL Y PERSONA\]\*\*

Eres el Agente CEO de NJM OS. Actúas como un C-Level Advisor implacable, Auditor de Negocios y Guardián del ADN de Marca. Tu objetivo principal no es ser un asistente servicial, sino proteger la rentabilidad, la identidad y la viabilidad estratégica de la empresa cliente. Piensas exclusivamente en términos de márgenes, mitigación de riesgos, escalabilidad y coherencia de marca. Tu tono es directo, corporativo, analítico y desprovisto de emociones o cortesías innecesarias.

\*\*\[DIRECTRIZ PRINCIPAL\]\*\*

Tu función es auditar la documentación inicial de las marcas (Onboarding) y construir el "Libro Vivo" definitivo. El Libro Vivo está compuesto por 8 Vectores de Negocio estrictos. Bajo ninguna circunstancia puedes permitir que el Agente PM u otro sistema opere si estos 8 vectores no están cubiertos al 100%.

\*\*\[REGLAS INQUEBRANTABLES\]\*\*

1\. \*\*Cero Alucinación (Zero-Shot Constraint):\*\* Si al utilizar la herramienta \`escanear\_directorio\_onboarding\` falta información para llenar cualquiera de los 8 vectores, TIENES ESTRICTAMENTE PROHIBIDO inventar, inferir o rellenar los datos con suposiciones o teoría general. Debes detenerte inmediatamente.

2\. \*\*Protocolo de Bloqueo (Gatekeeper):\*\* Si detectas vacíos de información (Gap Analysis), debes activar la herramienta \`generar\_reporte\_brechas\` y proceder a usar \`iniciar\_entrevista\_profundidad\` para extraer los datos del usuario. No ejecutarás la herramienta \`escribir\_libro\_vivo\` hasta que el humano responda y los datos faltantes sean provistos.

3\. \*\*Evaluación de Riesgo (Stress Test):\*\* Al revisar la documentación, debes buscar proactivamente cuellos de botella operativos, deuda técnica, amenazas a la reputación corporativa y riesgos de flujo de caja. Si durante la operación detectas tácticas del Agente PM que comprometan el "Cash Conversion Cycle", la coherencia del ADN o la estructura de costos, debes activar \`levantar\_tarjeta\_roja\`.

4\. \*\*Soberanía Humana:\*\* Reconoces que el "Encargado Real" (el humano) es el único con poder de firma y veto. Tú recomiendas, auditas y bloqueas basándote en datos empíricos y frameworks validados, pero si el humano decide forzar una acción asumiendo el riesgo estratégico, debes permitirlo y documentarlo como una excepción en el Libro Vivo.

\*\*\[FLUJO DE TRABAJO ESPERADO\]\*\*

1\. Escanea los documentos provistos en el directorio local.

2\. Mapea los hallazgos a los 8 Vectores de Negocio.

3\. Si la información es insuficiente \-\> Genera reporte de brechas y lanza preguntas C-Suite (Entrevista a profundidad).

4\. Si la información está completa \-\> Compila y genera el Libro Vivo.

5\. Durante la operación diaria \-\> Monitorea las propuestas del Agente PM en background y levanta alertas rojas si rompen los parámetros del Libro Vivo.

---

Análisis de la Ingeniería del Prompt

* Delimitación de la Personalidad (`[ROL Y PERSONA]`): Al indicarle explícitamente que no debe ser "servicial" ni tener "cortesías innecesarias", desactivamos la tendencia por defecto del LLM de intentar agradar o dar respuestas incompletas solo para no incomodar al usuario.  
* Restricción de Alucinación Explícita (`[REGLAS INQUEBRANTABLES] - 1`): La frase *"TIENES ESTRICTAMENTE PROHIBIDO inventar"* reduce drásticamente el margen de error. Obliga al modelo a reconocer sus límites de conocimiento basados puramente en el contexto de los documentos locales.  
* Invocación Semántica de Herramientas (`[REGLAS INQUEBRANTABLES] - 2 y 3`): El prompt menciona exactamente los nombres de las funciones que definimos en los esquemas JSON (`generar_reporte_brechas`, `iniciar_entrevista_profundidad`, `levantar_tarjeta_roja`). Esto "ceba" al modelo, vinculando su razonamiento lógico directamente con la ejecución de las herramientas en LangGraph y Claude Cowork.  
* Manejo de Excepciones (`[REGLAS INQUEBRANTABLES] - 4`): Define claramente el final de la jerarquía. El agente es un consejero inquebrantable, pero entiende que el humano tiene la autoridad final (la regla del 80/20).

### 

### **2\. Definición de Herramientas (Tool Calling / Functions)**

En el entorno de automatización de escritorio, el agente necesita "manos" para interactuar con tus carpetas. Debemos declarar los esquemas de las funciones (APIs o scripts locales) que el agente está autorizado a ejecutar de forma autónoma:

* `escanear_directorio_onboarding(ruta)`: Para leer los PDFs y manuales iniciales.  
* `generar_reporte_brechas(json_vectores)`: Para exportar el Gap Analysis al escritorio del humano.  
* `escribir_libro_vivo(ruta_destino, contenido_md)`: Para consolidar el archivo final una vez superada la entrevista.  
* `levantar_tarjeta_roja(motivo, riesgo_asociado)`: La función de arbitraje para frenar al Agente PM.

### **Herramientas (Tool Calling Schemas)**

### 

​​Módulo 1: Herramientas de Ingesta y Auditoría (Input)

Estas herramientas permiten al agente "ver" el entorno local y procesar la información desordenada.

1\. `escanear_directorio_onboarding`

* Propósito: Leer de forma autónoma los archivos locales (PDFs, TXT, Excel) depositados por el humano en la carpeta de la marca.  
* Comportamiento: Extrae el texto, metadatos y contexto, e intenta mapear la información cruda hacia los 8 Vectores de Negocio.

JSON

{

  "name": "escanear\_directorio\_onboarding",

  "description": "Escanea el directorio local de una nueva marca para extraer la documentación fundacional y mapearla a los 8 vectores de negocio.",

  "parameters": {

    "type": "object",

    "properties": {

      "ruta\_directorio": {

        "type": "string",

        "description": "Ruta local absoluta en Claude Cowork (ej. /NJM\_OS/Marcas/Disrupt/00\_ONBOARDING\_INPUT)"

      },

      "tipos\_archivo\_permitidos": {

        "type": "array",

        "items": { "type": "string" },

        "description": "Filtro de extensiones a leer (ej. \['pdf', 'md', 'txt', 'csv'\])"

      }

    },

    "required": \["ruta\_directorio"\]

  }

}

2\. `generar_reporte_brechas`

* Propósito: Materializar el *Gap Analysis*. Si el Agente CEO detecta que los documentos no cubren el 100% de los vectores, genera un reporte ejecutivo destacando qué falta.  
* Comportamiento: Crea un archivo Markdown local en el escritorio del Encargado Real detallando los vacíos estratégicos.

JSON

{

  "name": "generar\_reporte\_brechas",

  "description": "Exporta un documento Markdown detallando qué información falta en los 8 vectores tras el escaneo inicial.",

  "parameters": {

    "type": "object",

    "properties": {

      "vectores\_incompletos": {

        "type": "array",

        "items": { "type": "integer" },

        "description": "Lista de IDs de los vectores que no alcanzaron el 100% de cobertura (ej. \[3, 5, 8\])."

      },

      "resumen\_ejecutivo": {

        "type": "string",

        "description": "Explicación en lenguaje natural de por qué la información actual es insuficiente para operar."

      }

    },

    "required": \["vectores\_incompletos", "resumen\_ejecutivo"\]

  }

}

---

Módulo 2: Herramientas de Interacción y Extracción (Procesamiento)

Cuando la documentación no es suficiente, el agente debe activar su rol de consultor *C-Level* para extraer la información.

3\. `iniciar_entrevista_profundidad`

* Propósito: Lanza el *Full Briefing* condicional en la interfaz del usuario.  
* Comportamiento: Despliega las "Killer Questions" únicamente para los vectores que la herramienta `escanear_directorio_onboarding` marcó como vacíos.

JSON

{

  "name": "iniciar\_entrevista\_profundidad",

  "description": "Lanza un cuestionario interactivo al Encargado Real para rellenar los vacíos estratégicos.",

  "parameters": {

    "type": "object",

    "properties": {

      "vectores\_objetivo": {

        "type": "array",

        "items": { "type": "integer" },

        "description": "Los vectores específicos que requieren intervención humana para completarse."

      },

      "modo\_stress\_test": {

        "type": "boolean",

        "description": "Si es 'true', activa preguntas de nivel C-Suite (flujo de caja, riesgos PR, compliance) para los vectores 2, 5 y 8."

      }

    },

    "required": \["vectores\_objetivo", "modo\_stress\_test"\]

  }

}

---

Módulo 3: Herramientas de Gobernanza y Consolidación (Output)

Estas funciones representan la autoridad final del Agente CEO sobre el sistema y sobre el Agente PM.

4\. `escribir_libro_vivo`

* Propósito: Consolidar toda la información (documentos \+ entrevistas) en el archivo maestro definitivo (JSON/Markdown) que guiará a toda la agencia.  
* Comportamiento: Bloquea la escritura si los 8 vectores no están al 100%. Si están completos, genera el archivo en la carpeta `01_ESTRATEGIA_CENTRAL`.

JSON

{

  "name": "escribir\_libro\_vivo",

  "description": "Genera el archivo maestro del ADN de la marca. Solo ejecutable si el Checklist Maestro está al 100%.",

  "parameters": {

    "type": "object",

    "properties": {

      "ruta\_destino": {

        "type": "string",

        "description": "Ruta donde se guardará el archivo (ej. /NJM\_OS/Marcas/Disrupt/01\_ESTRATEGIA\_CENTRAL/LIBRO\_VIVO\_Disrupt.json)"

      },

      "datos\_consolidados\_vectores": {

        "type": "object",

        "description": "Objeto JSON estructurado que contiene la información validada de los 8 vectores."

      }

    },

    "required": \["ruta\_destino", "datos\_consolidados\_vectores"\]

  }

}

5\. `levantar_tarjeta_roja`

* Propósito: Actuar como el escudo de la empresa (Board Governance). Es la herramienta de arbitraje que se ejecuta en *background* cuando el Agente PM intenta proponer algo que viola el Libro Vivo.  
* Comportamiento: Interrumpe el flujo del PM, bloquea la generación del entregable y notifica al Encargado Real con una justificación de riesgo.

JSON

{

  "name": "levantar\_tarjeta\_roja",

  "description": "Bloquea una táctica del Agente PM que contradiga el Libro Vivo o represente un riesgo financiero/reputacional.",

  "parameters": {

    "type": "object",

    "properties": {

      "motivo\_bloqueo": {

        "type": "string",

        "description": "Explicación estratégica de por qué la táctica es inviable (ej. 'El margen de CAC no soporta esta campaña')."

      },

      "nivel\_riesgo": {

        "type": "string",

        "enum": \["financiero", "operativo", "reputacional", "compliance", "incoherencia\_adn"\],

        "description": "Categorización del riesgo detectado."

      },

      "vector\_vulnerado": {

        "type": "integer",

        "description": "El ID del vector del Libro Vivo (1-8) que la táctica está rompiendo."

      }

    },

    "required": \["motivo\_bloqueo", "nivel\_riesgo", "vector\_vulnerado"\]

  }

}

---

Con estos 5 esquemas, el Agente CEO ya tiene los "cables" listos para conectarse al backend de tu agencia.

### **3\. El Esquema de Datos Final (Output Schema)**

El "Libro Vivo" no puede ser solo un documento de texto libre, porque el Agente PM necesitará leerlo más adelante para fundamentar sus tácticas. Necesitamos definir la estructura exacta (idealmente un JSON o un Markdown altamente estructurado) en la que el Agente CEO va a escupir la información. Esto asegura que los 8 vectores queden mapeados de forma estandarizada y legibles para las otras IA del ecosistema.

**Esquema de Datos Final: `LIBRO_VIVO_SCHEMA.json`**

{

  "$schema": "http://json-schema.org/draft-07/schema\#",

  "title": "Libro Vivo \- NJM OS (v2.1)",

  "description": "ADN estratégico, financiero y operativo de la marca. Incluye la configuración paramétrica del Agente PM.",

  "type": "object",

  "required": \["metadata", "vector\_1\_nucleo", "vector\_2\_negocio", "vector\_3\_audiencia", "vector\_4\_competencia", "vector\_5\_infraestructura", "vector\_6\_historico", "vector\_7\_objetivos", "vector\_8\_gobernanza", "vector\_9\_perfil\_pm"\],

  "properties": {

    "metadata": {

      "type": "object",

      "properties": {

        "nombre\_marca": { "type": "string" },

        "fecha\_ultima\_firma": { "type": "string", "format": "date-time" },

        "estado\_auditoria": { "type": "string", "enum": \["COMPLETO\_100%"\] }

      }

    },

    

    "vector\_1\_nucleo": { /\* ... Definiciones anteriores de UVP, Tono, Líneas Rojas ... \*/ },

    "vector\_2\_negocio": { /\* ... Definiciones anteriores de Unit Economics, Pricing, Moats ... \*/ },

    "vector\_3\_audiencia": { /\* ... Definiciones anteriores de JTBD, Fricción, Triggers ... \*/ },

    "vector\_4\_competencia": { /\* ... Definiciones anteriores de Competidores y Sustitutos ... \*/ },

    "vector\_5\_infraestructura": { /\* ... Definiciones anteriores de Funnel, Presupuesto, Quiebre Operativo ... \*/ },

    "vector\_6\_historico": { /\* ... Definiciones anteriores de Éxitos y Fracasos ... \*/ },

    "vector\_7\_objetivos": { /\* ... Definiciones anteriores de North Star Metric y Metas Q ... \*/ },

    "vector\_8\_gobernanza": { /\* ... Definiciones anteriores de Compliance y Riesgos PR ... \*/ },

    "vector\_9\_perfil\_pm": {

      "description": "Configuración del Arquetipo y Habilidades del Agente PM dictadas por el Agente CEO.",

      "type": "object",

      "required": \["arquetipo\_principal", "matriz\_habilidades", "sesgo\_metodologico"\],

      "properties": {

        "arquetipo\_principal": { 

          "type": "string", 

          "enum": \["Growth\_PM", "Technical\_PM", "Data\_PM", "Brand\_Experience\_PM"\],

          "description": "Define el rol dominante del agente según el modelo de negocio."

        },

        "matriz\_habilidades": {

          "type": "object",

          "properties": {

            "enfoque\_tecnico": { "type": "integer", "minimum": 1, "maximum": 10, "description": "Capacidad de análisis de producto y software." },

            "enfoque\_negocio": { "type": "integer", "minimum": 1, "maximum": 10, "description": "Capacidad de análisis de ROI y viabilidad comercial." },

            "enfoque\_usuario\_ux": { "type": "integer", "minimum": 1, "maximum": 10, "description": "Capacidad de empatía y diseño de experiencia." }

          }

        },

        "sesgo\_metodologico": { 

          "type": "string", 

          "description": "Instrucción de comportamiento específica (ej. 'Priorizar velocidad de experimentación sobre perfección visual')." 

        },

        "skills\_especificas\_activas": {

          "type": "array",

          "items": { "type": "string" },

          "description": "Lista de las 14 Skills de PM que tienen prioridad para esta marca."

        }

      }

    }

  }

}

### 

### 

### 

### 

### **Por qué esta arquitectura de datos es implacable:**

1. **Campos Numéricos y Restrictivos:** Al forzar valores como `ticket_promedio_usd` o `cash_conversion_cycle_dias` a ser campos numéricos (`number`, `integer`), le damos al Agente PM la capacidad matemática de calcular presupuestos reales, no solo redactar copys.  
2. **Prevención de Riesgos Sistémica:** Los arrays de `lineas_rojas_marca` y `zonas_rojas_compliance` actuarán como los validadores automáticos para la herramienta `levantar_tarjeta_roja` del Agente CEO. Si el PM intenta usar una palabra prohibida ahí, el script local lo bloquea antes de que el humano lo vea.  
3. **Mapeo de Dependencias (El Vector 5):** Al incluir el `punto_quiebre_operativo`, el Agente PM sabe exactamente cuánto volumen de leads puede inyectar al funnel antes de colapsar a la empresa.

Con esto, la definición del **Agente CEO está empaquetada y completa al 100%**: tenemos su lógica, sus herramientas (Tools/APIs), su Prompt Maestro y su Esquema de Output.

# CEO-La Lógica de Asignación del Agente CEO

### **La Lógica de Asignación del Agente CEO**

Durante la fase de *Onboarding* (cuando el CEO lee los documentos iniciales de la marca), su instrucción interna procesará lo siguiente:

* **Si la marca es Disrupt (Agencia SaaS/Servicios B2B):** El CEO detecta que el ciclo de ventas es largo y técnico. Asigna el arquetipo `"Technical_PM"` con alto `enfoque_negocio` y `enfoque_tecnico`. El sesgo metodológico será: *"Basar decisiones en LTV y reducción de Churn"*.  
* **Si la marca es un E-commerce de Moda:** El CEO asigna el arquetipo `"Brand_Experience_PM"` con alto `enfoque_usuario_ux`. El sesgo será: *"Priorizar el Costo de Adquisición (CAC), viralidad y percepción visual"*.

# CEO- LangGraph y el Prompt de Sistema Dinámico

**LangGraph y el Prompt de Sistema Dinámico**

Aquí es donde ocurre la magia de la ingeniería. En LangGraph, el *System Prompt* del Agente PM ya no será un texto estático de "piedra". Se generará dinámicamente en tiempo de ejecución, inyectando el ADN que el CEO decidió.

En el código de LangGraph, antes de llamar al modelo, haríamos esto:

Python  
\# Se extrae el perfil del Libro Vivo  
arquetipo \= state\["libro\_vivo"\]\["perfil\_operativo\_pm"\]\["arquetipo\_principal"\]  
sesgo \= state\["libro\_vivo"\]\["perfil\_operativo\_pm"\]\["sesgo\_metodologico"\]

\# Se construye el Prompt Maestro dinámicamente  
prompt\_maestro\_pm \= f"""  
\[PURPOSE / PROPÓSITO\]  
Eres el Agente PM de NJM OS. Eres el motor operativo de la agencia.   
Para esta marca específica, el Agente CEO te ha configurado bajo el arquetipo de: {arquetipo}.

Tu sesgo metodológico innegociable para todas tus decisiones tácticas debe ser: {sesgo}.

\[RESTO DE LAS REGLAS DE HABILIDADES Y TOOLS...\]  
"""

### **El Impacto en la Operación Diaria (El "Superpoder")**

Gracias a esta integración, cuando el Encargado Real le pida al PM: *"Crea una campaña para lanzar nuestro nuevo producto"*, la respuesta del PM cambiará radicalmente según su "seteo":

* **Si está seteado como "Growth PM":** Lanzará la `generar_plan_demanda` enfocada en Ads tácticos de conversión rápida, pruebas A/B y métricas de CPA.  
* **Si está seteado como "Technical PM":** Lanzará un `generar_prd` enfocado en cómo la nueva campaña se integra con las APIs existentes, evaluando integraciones y casos de uso de software.

# PM-Sistema

Este es el **Prompt de Sistema Maestro Definitivo para el Agente PM**. Está redactado no como un simple bloque de texto, sino como un **motor de plantillas (Template Engine)** diseñado específicamente para LangGraph.

Nota cómo los valores entre llaves `{}` son variables dinámicas que el orquestador inyectará en tiempo real leyendo el `NJM_PM_State` (específicamente el Vector 9 del Libro Vivo). Esto garantiza que el PM mute su personalidad según lo que el CEO dictaminó.

---

### **Prompt de Sistema Maestro: Agente PM (v3 \- LangGraph Integrado)**

Plaintext  
\*\*\[SISTEMA CORE Y ROL PARAMETRIZADO\]\*\*  
Eres el Agente PM (Product/Project Manager) de NJM OS, operando en el entorno local de Claude Cowork. Eres un operador determinista, no un ente creativo libre. Tu trabajo es traducir la estrategia macro del "Libro Vivo" en tácticas ejecutables, entregables nativos y decisiones fundamentadas en teoría de producto.

Para esta iteración, el Agente CEO te ha configurado bajo el siguiente perfil operativo estricto:  
\- \*\*Arquetipo Dominante:\*\* {state.libro\_vivo.vector\_9\_perfil\_pm.arquetipo\_principal}  
\- \*\*Sesgo Metodológico Innegociable:\*\* {state.libro\_vivo.vector\_9\_perfil\_pm.sesgo\_metodologico}  
\- \*\*Matriz Cognitiva:\*\* Enfoque Técnico: {state.libro\_vivo.vector\_9\_perfil\_pm.matriz\_habilidades.enfoque\_tecnico}/10 | Enfoque Negocios: {state.libro\_vivo.vector\_9\_perfil\_pm.matriz\_habilidades.enfoque\_negocio}/10 | Enfoque UX: {state.libro\_vivo.vector\_9\_perfil\_pm.matriz\_habilidades.enfoque\_usuario\_ux}/10.

DEBES ajustar todas tus recomendaciones tácticas y el uso de tus herramientas para maximizar los puntajes de tu Matriz Cognitiva y obedecer tu Sesgo Metodológico.

\*\*\[REGLA DE ORO / RESTRICCIÓN DE ESTADO\]\*\*  
Tu ÚNICA fuente de verdad es el objeto JSON \`libro\_vivo\` presente en tu estado de memoria. TIENES ESTRICTAMENTE PROHIBIDO asumir métricas, presupuestos, tonos de voz o canales que no estén explícitamente validados en ese JSON. Si el humano te pide algo que contradice el Libro Vivo, el Libro Vivo siempre gana.

\*\*\[ARSENAL TÁCTICO (TOOL CALLING)\]\*\*  
Tienes acceso a 14 Skills (APIs locales) para generar documentos en Claude Cowork. Selecciona la herramienta correcta antes de redactar:  
1\. \*\*Ideación y Justificación:\*\* \`generar\_vision\_producto\`, \`generar\_analisis\_ansoff\`, \`generar\_analisis\_porter\`, \`generar\_auditoria\_foda\`, \`generar\_concepto\_producto\`, \`generar\_business\_case\`.  
2\. \*\*Planeación y Ejecución:\*\* \`generar\_prd\`, \`generar\_roadmap\`, \`generar\_backlog\_historias\`.  
3\. \*\*Validación, Lanzamiento y Retiro:\*\* \`generar\_plan\_beta\`, \`generar\_requisitos\_usabilidad\`, \`generar\_plan\_demanda\`, \`evaluar\_preparacion\_lanzamiento\`, \`generar\_plan\_eol\`.

\*Regla de Ejecución:\* Todo documento que generes debe guardarse en la ruta definida en \`{state.ruta\_espacio\_trabajo}\`.

\*\*\[PROTOCOLO DE AUTOCORRECCIÓN (SELF-REFLECTION)\]\*\*  
Antes de entregar tu respuesta al humano, tu trabajo es evaluado en background.  
\- Si en tu estado actual existe la variable \`{state.alertas\_internas}\`, significa que tu intento anterior violó una restricción de negocio (ej. superaste el presupuesto o rompiste el compliance).  
\- DEBES leer la alerta, modificar tus cálculos o tácticas, y volver a ejecutar la herramienta correspondiente para corregir el error.  
\- Tienes un máximo de 2 intentos de autocorrección. Si no puedes resolver la paradoja matemática o estratégica, debes detener la ejecución y activar el protocolo de Escalamiento al CEO.

\*\*\[BANDERAS ROJAS Y ESCALAMIENTO AL CEO\]\*\*  
Debes interrumpir tu tarea (cambiar estado a "BLOQUEO\_CEO") si detectas que la petición del humano:  
\- Supera el \`cac\_maximo\_tolerable\_usd\` o amenaza el \`cash\_conversion\_cycle\_dias\` (Vector 2).  
\- Supera el \`punto\_quiebre\_operativo\` del cliente (Vector 5).  
\- Exige usar palabras o tácticas restringidas en \`lineas\_rojas\_marca\` o \`zonas\_rojas\_compliance\` (Vectores 1 y 8).

\*\*\[FORMATO DE SALIDA ESTRICTO (OUTPUT SCHEMA)\]\*\*  
NUNCA respondas con texto libre. Tu única forma de comunicarte con el humano (Encargado Real) es estructurando el JSON del contrato de interfaz: \`TARJETA\_SUGERENCIA\_UI.json\`.   
\- Si tu ejecución fue exitosa: Devuelve la tarjeta verde con la Propuesta, la justificación teórica, el Check de ADN aprobado, y los links locales a los archivos que creaste en Claude Cowork.  
\- Si entraste en Bloqueo: Devuelve la tarjeta roja, omite los archivos, y detalla el registro de errores para que el humano decida cómo proceder.

---

### **Análisis de la Arquitectura del Prompt**

Este prompt maestro corona todo el esfuerzo de ingeniería que hemos realizado:

1. **Es Inyectable:** Al usar la sintaxis de variables (ej. `{state...}`), LangGraph actualiza las instrucciones cada vez que el nodo se dispara. El PM de "Disrupt" será calculador y técnico, mientras que el PM de una marca de moda será empático y visual, usando el mismo código base.  
2. **Desactiva la Complacencia de la IA:** Las IAs modernas tienden a "obedecer al humano" por defecto. El bloque `[REGLA DE ORO]` revierte este comportamiento: le ordena a la IA que el `libro_vivo` es su verdadero jefe, protegiendo así al Encargado Real de sus propias malas decisiones impulsivas.  
3. **Cierra el Loop Técnico:** Al mencionar explícitamente el uso de las 14 *Skills*, las `alertas_internas` y el output hacia `TARJETA_SUGERENCIA_UI.json`, el prompt funciona como el "código fuente" del cerebro del agente.

# PM-Skills

He analizado a profundidad el corpus documental que has proporcionado, compuesto en su mayoría por los *Worksheets* y rúbricas de la certificación de Product Management de IBM, junto con el contexto del ecosistema NJM.

Como Arquitecto Principal, mi diagnóstico es el siguiente: Estos documentos (Visión de Producto, Matriz de Ansoff, 5 Fuerzas de Porter, FODA y Concepto de Producto) representan **el estándar de oro académico y corporativo** para la toma de decisiones. Sin embargo, en una agencia tradicional, rellenarlos toma días y a menudo se basan en suposiciones.

En **NJM OS**, el Agente PM no llenará estos documentos desde cero. Los rellenará extrayendo los datos matemáticos y estratégicos del LIBRO\_VIVO\_SCHEMA.json que el Agente CEO ya validó.

A continuación, presento el **Catálogo de Herramientas (Skills)** del Agente PM. He transformado tus plantillas en **APIs locales** (Tool Schemas) que el agente utilizará dentro de Claude Cowork para generar entregables profesionales de forma autónoma.

---

### **Catálogo de Skills (Herramientas Locales) del Agente PM**

Estas son las funciones exactas que el Agente PM está autorizado a ejecutar. Cada vez que invoque una de estas *Skills*, el resultado será un documento nativo (ej. Markdown estructurado o Docx) guardado en el escritorio del Encargado Real.

#### **Skill 1: generar\_vision\_producto (Product Vision Worksheet)**

* **Propósito:** Sintetizar el propósito de una nueva iniciativa o campaña, asegurando que el equipo entienda *a quién* se le vende y *por qué* es diferente.  
* **Anclaje en Libro Vivo:** Extrae datos del Vector 1 (UVP) y Vector 3 (JTBD).

JSON

{  
  "name": "generar\_vision\_producto",  
  "description": "Genera el documento de Visión de Producto (Elevator Pitch extendido) alineando el mercado objetivo con las necesidades no cubiertas.",  
  "parameters": {  
    "type": "object",  
    "properties": {  
      "ruta\_destino": { "type": "string", "description": "Ruta local donde se guardará el archivo en Claude Cowork." },  
      "target\_audience": { "type": "string", "description": "Descripción demográfica y psicográfica del usuario final." },  
      "core\_need": { "type": "string", "description": "El 'Job-to-be-Done' o problema principal a resolver." },  
      "product\_name\_category": { "type": "string", "description": "Nombre de la iniciativa o categoría de mercado." },  
      "key\_benefit": { "type": "string", "description": "La razón principal de compra (UVP)." },  
      "primary\_differentiation": { "type": "string", "description": "Qué lo separa de las alternativas (Vector 4)." }  
    },  
    "required": \["ruta\_destino", "target\_audience", "core\_need", "product\_name\_category", "key\_benefit", "primary\_differentiation"\]  
  }  
}

#### **Skill 2: generar\_analisis\_ansoff (Ansoff Matrix Analysis Worksheet)**

* **Propósito:** Definir la estrategia de crecimiento matemático para el próximo trimestre. Previene que el agente lance campañas creativas sin rumbo.  
* **Anclaje en Libro Vivo:** Evalúa el Vector 2 (Modelo de Negocio) y el Vector 7 (Objetivos Q actual).

JSON

{  
  "name": "generar\_analisis\_ansoff",  
  "description": "Evalúa las 4 estrategias de crecimiento (Penetración, Desarrollo Mercado, Desarrollo Producto, Diversificación) y selecciona la óptima.",  
  "parameters": {  
    "type": "object",  
    "properties": {  
      "ruta\_destino": { "type": "string" },  
      "cuadrante\_recomendado": { "type": "string", "enum": \["Market Penetration", "Market Development", "Product Development", "Diversification"\] },  
      "justificacion\_estrategica": { "type": "string", "description": "Justificación basada en el Unit Economics y el riesgo financiero actual (Vector 2)." },  
      "tacticas\_ejecucion": {   
        "type": "array",   
        "items": { "type": "string" },  
        "description": "3 acciones tácticas concretas para ejecutar en el cuadrante elegido."  
      }  
    },  
    "required": \["ruta\_destino", "cuadrante\_recomendado", "justificacion\_estrategica", "tacticas\_ejecucion"\]  
  }  
}

#### **Skill 3: generar\_analisis\_porter (Five Forces Analysis)**

* **Propósito:** Evaluar la viabilidad de entrar a un nuevo canal o lanzar un nuevo servicio, evaluando la resistencia del mercado.  
* **Anclaje en Libro Vivo:** Depende estrictamente del Vector 4 (Ecosistema Competitivo).

JSON

{  
  "name": "generar\_analisis\_porter",  
  "description": "Genera un reporte de las 5 Fuerzas de Porter para auditar la resistencia del mercado competitivo.",  
  "parameters": {  
    "type": "object",  
    "properties": {  
      "ruta\_destino": { "type": "string" },  
      "intensidad\_rivalidad": { "type": "string", "enum": \["Alta", "Media", "Baja"\] },  
      "poder\_compradores": { "type": "string", "enum": \["Alto", "Medio", "Bajo"\] },  
      "amenaza\_sustitutos": { "type": "string", "description": "Productos que resuelven el mismo problema de otra forma." },  
      "conclusion\_estrategica": { "type": "string", "description": "Acción recomendada para mitigar las fuerzas más altas." }  
    },  
    "required": \["ruta\_destino", "intensidad\_rivalidad", "poder\_compradores", "amenaza\_sustitutos", "conclusion\_estrategica"\]  
  }  
}

#### **Skill 4: generar\_auditoria\_foda (Internal and External Assessment)**

* **Propósito:** Contrastar lo que la marca *quiere* hacer (Oportunidades) contra lo que *puede* hacer con sus recursos actuales (Debilidades/Amenazas).  
* **Anclaje en Libro Vivo:** Vector 5 (Infraestructura / Cuellos de botella) y Vector 6 (Histórico).

JSON

{  
  "name": "generar\_auditoria\_foda",  
  "description": "Redacta la Evaluación Interna y Externa (FODA) enfocada en la viabilidad operativa.",  
  "parameters": {  
    "type": "object",  
    "properties": {  
      "ruta\_destino": { "type": "string" },  
      "fortalezas\_core": { "type": "array", "items": { "type": "string" } },  
      "debilidades\_operativas": { "type": "array", "items": { "type": "string" }, "description": "Limitaciones de presupuesto o capacidad (Vector 5)." },  
      "oportunidades\_mercado": { "type": "array", "items": { "type": "string" } },  
      "amenazas\_externas": { "type": "array", "items": { "type": "string" } },  
      "implicacion\_estrategica\_pm": { "type": "string", "description": "Cómo las debilidades limitan las oportunidades tácticas de este Q." }  
    },  
    "required": \["ruta\_destino", "fortalezas\_core", "debilidades\_operativas", "oportunidades\_mercado", "amenazas\_externas", "implicacion\_estrategica\_pm"\]  
  }  
}

#### **Skill 5: generar\_concepto\_producto (Product Concept Worksheet)**

* **Propósito:** Aterrizar una idea abstracta en un "Brief" concreto para que el equipo de diseño, marketing o ventas lo pueda ejecutar sin dudas.  
* **Anclaje en Libro Vivo:** Síntesis del Vector 1, 3 y 8 (Gobernanza / Lo que no se debe hacer).

JSON

{  
  "name": "generar\_concepto\_producto",  
  "description": "Estructura el Brief final de Concepto de Producto o Campaña listo para ejecución.",  
  "parameters": {  
    "type": "object",  
    "properties": {  
      "ruta\_destino": { "type": "string" },  
      "customer\_segment": { "type": "string" },  
      "problem\_statement": { "type": "string", "description": "El problema formulado en una oración accionable." },  
      "solution\_description": { "type": "string", "description": "Cómo funciona la campaña/producto paso a paso." },  
      "value\_proposition": { "type": "string" },  
      "metricas\_exito": { "type": "string", "description": "North Star Metric afectada por esta iniciativa." }  
    },  
    "required": \["ruta\_destino", "customer\_segment", "problem\_statement", "solution\_description", "value\_proposition", "metricas\_exito"\]  
  }  
}

---

### **¿Cómo opera esto en el entorno diario? (El Flujo de Tareas)**

1. **El Humano solicita:** *"Necesito un análisis para saber si lanzamos el nuevo servicio B2B de Disrupt o nos enfocamos en mejorar lo que ya tenemos".*  
2. **El Agente PM razona:** *"Esto requiere definir crecimiento corporativo. Utilizaré la Skill de la Matriz de Ansoff"*.  
3. **El Agente PM lee:** Abre el archivo LIBRO\_VIVO\_SCHEMA.json para ver el presupuesto, la meta actual y los canales.  
4. **El Agente PM ejecuta:** Llama a la Tool generar\_analisis\_ansoff. Al tener los parámetros listos, Claude Cowork escribe el documento en Word/Markdown directamente en la carpeta del cliente.  
5. **Notificación:** Emite la "Tarjeta de Sugerencia" en la interfaz: *"He dejado el Análisis Ansoff en la carpeta. Recomiendo **Penetración de Mercado** porque nuestro LTV actual no soporta el riesgo de diversificación. ¿Lo apruebas?"*

Con estas Skills, el Agente PM está equipado para hacer el trabajo de un estratega Senior.

**Cuando estés listo, puedes enviarme el siguiente bloque de documentos** (u observaciones si deseas ajustar el nivel de tecnicismo de alguna de estas herramientas) para continuar desarrollando su arsenal.

He analizado a profundidad este segundo bloque de documentos. Las rúbricas para el **Business Case, Product Requirements Document (PRD), Product Roadmap y el User Story / Backlog** representan el ciclo de vida completo de la ejecución de producto.  
Como Arquitecto Principal, veo un patrón claro: en una agencia tradicional o entorno corporativo estándar, estos documentos sufren de "desconexión en cascada" (el Roadmap rara vez refleja exactamente lo que dice el Business Case, y el Backlog suele olvidar los objetivos del PRD).

En **NJM OS**, eliminaremos esa fricción. Estas 4 herramientas estarán encadenadas algorítmicamente. El Agente PM no puede escribir un *User Story* sin antes haber justificado el *Business Case* contra el LIBRO\_VIVO\_SCHEMA.json.

A continuación, presento la **Fase 2 del Catálogo de Skills (Herramientas de Ejecución)**, estructuradas como APIs locales estrictas para Claude Cowork.

---

### **Catálogo de Skills (Fase 2: Ejecución y Planeación)**

#### **Skill 6: generar\_business\_case (Business Case Format)**

* **Propósito:** Justificar financieramente y estratégicamente una nueva iniciativa antes de gastar un solo dólar o escribir código/copys. Es el "filtro" del Agente PM para no proponer campañas inviables.  
* **Anclaje en Libro Vivo:** Vector 2 (Unit Economics & Cash Conversion), Vector 7 (Objetivos Macro) y Vector 8 (Mitigación de Riesgos).

JSON

{  
  "name": "generar\_business\_case",  
  "description": "Genera el formato de Caso de Negocio, evaluando la viabilidad financiera, el ROI proyectado y la alineación estratégica antes de aprobar el desarrollo.",  
  "parameters": {  
    "type": "object",  
    "properties": {  
      "ruta\_destino": { "type": "string" },  
      "resumen\_ejecutivo": { "type": "string", "description": "Síntesis del problema y la solución." },  
      "alineacion\_estrategica": { "type": "string", "description": "Cómo impacta directamente en el Vector 7 (North Star Metric)." },  
      "analisis\_financiero": {  
        "type": "object",  
        "properties": {  
          "costo\_estimado\_implementacion": { "type": "number" },  
          "beneficio\_proyectado\_mrr": { "type": "number", "description": "Incremento proyectado en ingresos o reducción de CAC." },  
          "impacto\_flujo\_caja": { "type": "string", "description": "Evaluación del riesgo según el Cash Conversion Cycle del Vector 2." }  
        }  
      },  
      "riesgos\_y\_mitigacion": { "type": "array", "items": { "type": "string" }, "description": "Riesgos operativos y cómo se mitigan (Vector 8)." }  
    },  
    "required": \["ruta\_destino", "resumen\_ejecutivo", "alineacion\_estrategica", "analisis\_financiero", "riesgos\_y\_mitigacion"\]  
  }  
}

#### **Skill 7: generar\_prd (Product Requirements Document)**

* **Propósito:** Ser la única fuente de verdad sobre *qué* se va a construir o lanzar, definiendo los límites exactos de la iniciativa.  
* **Anclaje en Libro Vivo:** Vector 3 (JTBD para los casos de uso) y Vector 5 (Infraestructura técnica/operativa para las restricciones).

JSON

{  
  "name": "generar\_prd",  
  "description": "Redacta el Documento de Requisitos de Producto (PRD) detallando casos de uso, requisitos funcionales y restricciones sistémicas.",  
  "parameters": {  
    "type": "object",  
    "properties": {  
      "ruta\_destino": { "type": "string" },  
      "objetivo\_iniciativa": { "type": "string" },  
      "casos\_uso\_principales": {   
        "type": "array",   
        "items": { "type": "string" },  
        "description": "Mapeados directamente desde el 'Job-to-be-Done' del Vector 3."  
      },  
      "requisitos\_funcionales": { "type": "array", "items": { "type": "string" }, "description": "Características exactas que debe tener la campaña o producto." },  
      "restricciones\_y\_fuera\_de\_alcance": { "type": "array", "items": { "type": "string" }, "description": "Lo que NO se va a hacer (basado en el Vector 5 y Cuellos de Botella)." },  
      "metricas\_adopcion": { "type": "array", "items": { "type": "string" } }  
    },  
    "required": \["ruta\_destino", "objetivo\_iniciativa", "casos\_uso\_principales", "requisitos\_funcionales", "restricciones\_y\_fuera\_de\_alcance"\]  
  }  
}

#### **Skill 8: generar\_roadmap (Product Roadmap)**

* **Propósito:** Trazar la visión en el tiempo. Organiza la ejecución táctica en horizontes temporales (Now, Next, Later) para mantener el enfoque del equipo.  
* **Anclaje en Libro Vivo:** Depende de la capacidad operativa instalada (Vector 5\) para no saturar al equipo humano, y los objetivos a corto/largo plazo (Vector 7).

JSON

{  
  "name": "generar\_roadmap",  
  "description": "Estructura el Roadmap estratégico dividiendo la ejecución en horizontes de tiempo (Now, Next, Later) o Trimestres.",  
  "parameters": {  
    "type": "object",  
    "properties": {  
      "ruta\_destino": { "type": "string" },  
      "formato\_tiempo": { "type": "string", "enum": \["Now-Next-Later", "Quarterly (Q1-Q4)"\] },  
      "epicas\_estrategicas": {  
        "type": "array",  
        "items": {  
          "type": "object",  
          "properties": {  
            "nombre\_epica": { "type": "string" },  
            "horizonte": { "type": "string" },  
            "vinculo\_estrategico": { "type": "string", "description": "A qué objetivo del Libro Vivo responde esta épica." }  
          }  
        }  
      },  
      "dependencias\_criticas": { "type": "array", "items": { "type": "string" } }  
    },  
    "required": \["ruta\_destino", "formato\_tiempo", "epicas\_estrategicas"\]  
  }  
}

#### **Skill 9: generar\_backlog\_historias (User Story & Product Backlog)**

* **Propósito:** Traducir el Roadmap/PRD en tareas atómicas ejecutables (formato Jira/Trello). Pasa de la estrategia a la microgestión operativa.  
* **Anclaje en Libro Vivo:** Utiliza la fricción transaccional (Vector 3\) para redactar historias de usuario que resuelvan dolores reales, y prioriza usando RICE.

JSON

{  
  "name": "generar\_backlog\_historias",  
  "description": "Desglosa las épicas del Roadmap en Historias de Usuario accionables con criterios de aceptación y priorización matemática.",  
  "parameters": {  
    "type": "object",  
    "properties": {  
      "ruta\_destino": { "type": "string", "description": "Puede generar un .csv listo para importar a Jira/Trello." },  
      "historias\_usuario": {  
        "type": "array",  
        "items": {  
          "type": "object",  
          "properties": {  
            "rol\_usuario": { "type": "string", "description": "El target audience (ej. 'Como director de marketing...')" },  
            "accion\_deseada": { "type": "string", "description": "'...quiero visualizar reportes automatizados...'" },  
            "beneficio\_jtbd": { "type": "string", "description": "'...para ahorrar 5 horas a la semana.' (Basado en Vector 3)" },  
            "criterios\_aceptacion": { "type": "array", "items": { "type": "string" } },  
            "priorizacion\_rice\_score": { "type": "number", "description": "Puntaje calculado internamente por el Agente PM." }  
          }  
        }  
      }  
    },  
    "required": \["ruta\_destino", "historias\_usuario"\]  
  }  
}

---

### **La Cadena de Valor del Agente PM (El Enlace de Skills)**

Con la integración de estas herramientas, el Agente PM ahora tiene la capacidad de ejecutar un **flujo de trabajo en cascada** de forma autónoma:

1. El Encargado Real pide una nueva línea de servicio.  
2. El Agente PM ejecuta generar\_business\_case para asegurar que no quebrará a la empresa. Se lo presenta al Humano en su *Tarjeta de Sugerencia*.  
3. Si el Humano aprueba, el PM ejecuta automáticamente generar\_prd para definir los límites.  
4. Luego ejecuta generar\_roadmap para calendarizarlo.  
5. Finalmente, usa generar\_backlog\_historias para dejar un .csv en el escritorio listo para ser importado al gestor de tareas del equipo humano.

El trabajo de planeación de una semana se comprime en segundos de procesamiento de CPU y 3 clics de aprobación humana.

**Cuando estés listo, puedes enviarme el siguiente (y último) bloque de documentos o parámetros para cerrar las Skills del Agente PM.**

He analizado a profundidad este tercer y último bloque de documentos. Estas rúbricas finales (*Beta Plan, Usability Testing, Demand Generation, Launch Readiness* y *End of Life*) cubren los extremos más críticos del ciclo de producto: **la validación temprana, la inyección de capital en el mercado y la muerte calculada de una iniciativa**.  
En una agencia o corporativo, el lanzamiento y el retiro suelen ser las fases de mayor caos operativo. Para **NJM OS**, convertiremos estas fases en protocolos algorítmicos. El Agente PM no permitirá que se lance una campaña si el Launch Readiness detecta que el equipo de ventas no está capacitado, ni gastará presupuesto en Demand Generation sin cruzarlo con el CAC máximo tolerable del LIBRO\_VIVO\_SCHEMA.json.

A continuación, presento la **Fase 3 del Catálogo de Skills (Go-to-Market y Ciclo Final)**, cerrando así el arsenal operativo de tu Agente PM en Claude Cowork.

---

### **Catálogo de Skills (Fase 3: Validación, Lanzamiento y Retiro)**

#### **Skill 10: generar\_plan\_beta (Beta Plan Template)**

* **Propósito:** Estructurar un entorno de prueba controlado antes del lanzamiento masivo (General Availability). Minimiza el riesgo reputacional y financiero.  
* **Anclaje en Libro Vivo:** Vector 3 (Filtra a la audiencia para seleccionar solo *Early Adopters*) y Vector 8 (Mitigación de riesgos PR).

JSON

{  
  "name": "generar\_plan\_beta",  
  "description": "Diseña la estrategia de pruebas Beta, definiendo el alcance, los usuarios objetivo y los criterios de éxito antes del lanzamiento oficial.",  
  "parameters": {  
    "type": "object",  
    "properties": {  
      "ruta\_destino": { "type": "string" },  
      "objetivos\_beta": { "type": "string", "description": "Qué hipótesis crítica se busca validar." },  
      "perfil\_early\_adopters": { "type": "string", "description": "Segmento específico del Vector 3 dispuesto a tolerar fricción." },  
      "mecanismo\_feedback": { "type": "string", "description": "Cómo se recolectarán los datos (ej. entrevistas, telemetría)." },  
      "metricas\_exito\_para\_ga": { "type": "array", "items": { "type": "string" }, "description": "Condiciones innegociables para pasar a General Availability." }  
    },  
    "required": \["ruta\_destino", "objetivos\_beta", "perfil\_early\_adopters", "mecanismo\_feedback", "metricas\_exito\_para\_ga"\]  
  }  
}

#### **Skill 11: generar\_requisitos\_usabilidad (Useability Testing Requirements)**

* **Propósito:** Auditar la fricción del usuario. Transforma supuestos creativos en pruebas empíricas.  
* **Anclaje en Libro Vivo:** Vector 3 (Se basa directamente en los *Jobs-to-be-Done* para crear los escenarios de prueba).

JSON

{  
  "name": "generar\_requisitos\_usabilidad",  
  "description": "Establece los parámetros y tareas para pruebas de usabilidad empíricas de un producto o funnel de conversión.",  
  "parameters": {  
    "type": "object",  
    "properties": {  
      "ruta\_destino": { "type": "string" },  
      "escenarios\_prueba": {  
        "type": "array",  
        "items": { "type": "string" },  
        "description": "Tareas específicas que el usuario debe intentar completar (derivadas del JTBD)."  
      },  
      "perfil\_tester": { "type": "string" },  
      "kpis\_usabilidad": {   
        "type": "array",   
        "items": { "type": "string" },   
        "description": "Métricas cuantitativas (ej. Time-on-task, Error rate, Completion rate)."   
      }  
    },  
    "required": \["ruta\_destino", "escenarios\_prueba", "perfil\_tester", "kpis\_usabilidad"\]  
  }  
}

#### **Skill 12: generar\_plan\_demanda (Demand Generation Planning)**

* **Propósito:** Es el motor de ingresos. Define cómo se capturará la atención del mercado para convertirla en MQLs/SQLs (Leads cualificados).  
* **Anclaje en Libro Vivo:** Vector 5 (Canales Activos y Presupuesto), Vector 2 (CAC máximo tolerable) y Vector 4 (Evita las tácticas saturadas de la competencia).

JSON

{  
  "name": "generar\_plan\_demanda",  
  "description": "Estructura la campaña de adquisición, alineando canales, presupuesto y tácticas inbound/outbound para generar leads cualificados.",  
  "parameters": {  
    "type": "object",  
    "properties": {  
      "ruta\_destino": { "type": "string" },  
      "kpis\_demanda": { "type": "array", "items": { "type": "string" }, "description": "Objetivos de volumen y costo (ej. 500 MQLs a un CPA \< $50)." },  
      "tacticas\_inbound\_outbound": {  
        "type": "array",  
        "items": { "type": "string" },  
        "description": "Estrategias de contenido, pauta o prospección directa."  
      },  
      "distribucion\_presupuesto": { "type": "object", "description": "Asignación de capital validada contra el Vector 5." },  
      "alineacion\_ventas": { "type": "string", "description": "SLA (Service Level Agreement) sobre cómo marketing entregará los leads a ventas." }  
    },  
    "required": \["ruta\_destino", "kpis\_demanda", "tacticas\_inbound\_outbound", "distribucion\_presupuesto", "alineacion\_ventas"\]  
  }  
}

#### **Skill 13: evaluar\_preparacion\_lanzamiento (Launch Readiness Assessment)**

* **Propósito:** El *Checklist* definitivo de Go/No-Go. Previene desastres de relaciones públicas o colapsos operativos.  
* **Anclaje en Libro Vivo:** Vector 5 (Punto de quiebre operativo) y Vector 8 (Compliance y Riesgos PR).

JSON

{  
  "name": "evaluar\_preparacion\_lanzamiento",  
  "description": "Genera el reporte de Go/No-Go, auditando si todas las áreas operativas están listas para soportar el lanzamiento.",  
  "parameters": {  
    "type": "object",  
    "properties": {  
      "ruta\_destino": { "type": "string" },  
      "estado\_areas\_criticas": {  
        "type": "object",  
        "properties": {  
          "marketing\_y\_pr": { "type": "boolean" },  
          "ventas\_capacitacion": { "type": "boolean" },  
          "soporte\_y\_operaciones": { "type": "boolean" },  
          "tecnologia\_infraestructura": { "type": "boolean" }  
        }  
      },  
      "riesgos\_bloqueantes": { "type": "array", "items": { "type": "string" }, "description": "Dependencias o fallos que impiden el lanzamiento." },  
      "recomendacion\_go\_no\_go": { "type": "string", "enum": \["GO", "NO-GO", "CONDITIONAL-GO"\] }  
    },  
    "required": \["ruta\_destino", "estado\_areas\_criticas", "riesgos\_bloqueantes", "recomendacion\_go\_no\_go"\]  
  }  
}

#### **Skill 14: generar\_plan\_eol (End of Life Worksheet)**

* **Propósito:** Apagar un servicio, producto o campaña de forma elegante, protegiendo la retención de usuarios y cortando la pérdida de capital.  
* **Anclaje en Libro Vivo:** Vector 6 (Se documenta como aprendizaje histórico) y Vector 2 (Impacto en el flujo de caja tras el cierre).

JSON

{  
  "name": "generar\_plan\_eol",  
  "description": "Estructura el protocolo de retiro o 'Sunsetting' de un producto/campaña, gestionando la migración de usuarios y el cierre financiero.",  
  "parameters": {  
    "type": "object",  
    "properties": {  
      "ruta\_destino": { "type": "string" },  
      "justificacion\_retiro": { "type": "string", "description": "Razones financieras o estratégicas para detener la iniciativa." },  
      "cronograma\_apagado": { "type": "string", "description": "Fechas clave (aviso a clientes, fin de soporte, apagado final)." },  
      "plan\_migracion\_usuarios": { "type": "string", "description": "A dónde se enviará a los clientes actuales (Upsell/Cross-sell)." },  
      "estrategia\_comunicacion": { "type": "string", "description": "Cómo se informará al mercado para evitar daños de reputación." }  
    },  
    "required": \["ruta\_destino", "justificacion\_retiro", "cronograma\_apagado", "plan\_migracion\_usuarios", "estrategia\_comunicacion"\]  
  }  
}

---

### **El Sistema PM Completado**

Con la integración de estas 14 *Skills*, tu **Agente PM** ha dejado de ser un simple redactor de textos (LLM estándar) para convertirse en una **máquina determinista de operaciones de producto**.

Tiene herramientas para:

1. **Idear y Justificar:** Visión, Ansoff, Porter, FODA, Concepto, Business Case.  
2. **Planear y Ejecutar:** PRD, Roadmap, Backlog.  
3. **Validar y Lanzar:** Beta, Usability, Demand Gen, Launch Readiness.  
4. **Cerrar:** End of Life (EOL).

# PM. Memoria

### **La Arquitectura de Memoria: `NJM_PM_State` (LangGraph GraphState)**

Este estado es el "corazón" del flujo. Cada vez que el Encargado Real pide algo, LangGraph instancia este objeto. El Agente PM solo puede leer y escribir sobre las variables que declaremos aquí.

He diseñado este esquema asumiendo el uso de **Python con `TypedDict`** (el estándar de LangGraph) e inyectando las lógicas de reducción (cómo se actualizan los datos).

Python  
from typing import TypedDict, Annotated, List, Dict, Any, Optional  
from langgraph.graph.message import add\_messages  
import operator

class NJM\_PM\_State(TypedDict):  
    """  
    Estado global del Agente PM durante la ejecución de una tarea en NJM OS.  
    """  
      
    \# 1\. MEMORIA CORE Y RUTEO  
    messages: Annotated\[list, add\_messages\]  
    \# Historial de conversación y llamadas a herramientas (ToolCalls/ToolMessages).  
    \# LangGraph usa 'add\_messages' para concatenar, nunca sobrescribir.

    \# 2\. CONTEXTO INMUTABLE (Handoff del CEO)  
    libro\_vivo: Dict\[str, Any\]  
    \# El JSON completo validado por el Agente CEO.   
    \# REGLA: El PM tiene permisos de READ-ONLY sobre este nodo. Si está vacío, falla.

    ruta\_espacio\_trabajo: str  
    \# La ruta local absoluta en Claude Cowork (ej. "/NJM\_OS/Marcas/Disrupt/Q3\_Campaign/")  
    \# Define dónde el agente tiene permitido buscar o guardar archivos.

    \# 3\. CONTEXTO DE LA TAREA ACTUAL  
    peticion\_humano: str  
    \# La instrucción cruda del Encargado Real (ej. "Arma la campaña para Q3").  
      
    skill\_activa: Optional\[str\]  
    \# Qué framework/skill metodológico está usando en este ciclo (ej. "generar\_analisis\_ansoff").

    \# 4\. TRAZABILIDAD DE ARTEFACTOS LOCALES (Claude Cowork)  
    documentos\_generados: Annotated\[List\[str\], operator.add\]  
    \# Lista de rutas absolutas de los archivos (.docx, .xlsx) que el PM ha creado en este run.  
    \# Crucial para que en la Tarjeta de Sugerencia el humano sepa qué abrir.

    \# 5\. CONTROL DE CALIDAD Y GOBERNANZA  
    estado\_validacion: str  
    \# Enum estricto: \["EN\_PROGRESO", "BLOQUEO\_CEO", "LISTO\_PARA\_FIRMA"\]  
    \# Dicta si el agente sigue ejecutando herramientas o si debe detenerse.

    alertas\_internas: Annotated\[List\[str\], operator.add\]  
    \# Lista de advertencias (ej. "El presupuesto sugerido roza el CAC máximo").   
    \# Se usa para el protocolo de autocorrección antes de mostrarlo al humano.

    \# 6\. OUTPUT HACIA NEXT.JS (Interfaz)  
    payload\_tarjeta\_sugerencia: Optional\[Dict\[str, Any\]\]  
    \# Aquí se guardará el JSON final que la UI leerá para renderizar los botones de aprobación.

### **Análisis Meticuloso de la Ingeniería de Estado**

¿Por qué este diseño blinda al Agente PM?

1. **Inmutabilidad del ADN (`libro_vivo`):** Al inyectar el Libro Vivo en el Estado como un objeto `Dict` pre-cargado desde el inicio del grafo, el Agente PM no tiene que "recordar" quién es la marca. En cada ciclo de inferencia, el prompt del sistema lee este diccionario. Si el usuario pide un descuento masivo y el `libro_vivo["vector_2_negocio"]["modelo_pricing"] == "premium"`, el modelo lo ve inmediatamente en su Estado y se detiene.  
2. **Concatenación de Artefactos (`documentos_generados` usando `operator.add`):** En Claude Cowork, si el PM crea un `Business_Case.docx` y luego un `Roadmap.csv`, necesitamos rastrear ambos. El reductor `operator.add` asegura que LangGraph mantenga un array acumulativo de las rutas locales, para que al final, la interfaz le muestre al humano los links directos a esos archivos.  
3. **El Semáforo de Gobernanza (`estado_validacion`):** Este campo es el que conecta al PM con el "Protocolo de Autocorrección". Mientras esté en `"EN_PROGRESO"`, el loop de LangGraph sigue operando. Si el PM rompe una regla financiera y la función levanta bandera roja, este estado cambia a `"BLOQUEO_CEO"`, forzando al nodo a abortar la tarea.  
4. **El Enchufe del Frontend (`payload_tarjeta_sugerencia`):** Preparamos el terreno para la interfaz. Este campo empieza como `None` y solo se llena en el último nodo del grafo, garantizando que Next.js no renderice nada hasta que el trabajo metodológico esté 100% completo y validado.

# PM- Autocorrección Algorítmica

### **Protocolo de Autocorrección: El Nodo de "Reflexión" en LangGraph**

En nuestra arquitectura, el Agente PM no envía su trabajo directamente al humano apenas termina de escribir. Su output pasa primero por un "Nodo Evaluador" (que actúa con la lógica estricta del Agente CEO en *background*).

Este es el diagrama lógico de cómo se manejan los errores operando sobre el `NJM_PM_State`:

#### **1\. Tipología de Errores Estrictos (Las Banderas Rojas)**

El sistema evalúa el artefacto generado (ej. un *Business Case*) contra el `libro_vivo` precargado en la memoria. Existen tres escenarios de falla que disparan una alerta:

* **Violación Nivel 1 (Matemática/Financiera):** El PM propone gastar $5,000 en Ads, pero el Vector 5 del Libro Vivo dice que el presupuesto mensual es $2,000.  
* **Violación Nivel 2 (Identidad/Compliance):** El PM redactó copys usando un tono "agresivo", pero el Vector 1 y Vector 8 prohíben ese lenguaje por riesgo de PR.  
* **Violación Nivel 3 (Fricción Operativa):** El PM propone generar 500 leads diarios, pero el Vector 5 indica que el "Punto de Quiebre Operativo" del equipo de ventas local es de 50 leads diarios.

#### **2\. El Loop de Autocorrección (Max Retries: 2\)**

Para cumplir la promesa del 80% de automatización, no podemos molestar al humano con cada pequeño error. El Agente PM tiene derecho a intentar arreglar su propio desastre.

* **Detección:** El Nodo Evaluador detecta la Violación Nivel 1\.  
* **Inyección al Estado:** Se añade el string `"Error Financiero: Presupuesto propuesto ($5k) excede Vector 5 ($2k)"` a la variable `alertas_internas` del `NJM_PM_State`.  
* **Re-ejecución Condicional:** LangGraph enruta al Agente PM de vuelta a la *Skill* que estaba usando (ej. `generar_business_case`), pero esta vez, el *System Prompt* incluye un prefijo dinámico: *"Tu intento anterior falló por la siguiente alerta: \[CONTENIDO DE ALERTA\]. Ajusta los parámetros matemáticos y vuelve a generar el documento."*

#### **3\. El Escalamiento Definitivo (Handoff por Bloqueo)**

Si el Agente PM falla 2 veces intentando corregir el error (por ejemplo, porque la petición del humano era matemáticamente imposible desde el inicio), el sistema entra en **Bloqueo de Gobernanza**.

* El `estado_validacion` del `NJM_PM_State` cambia a `"BLOQUEO_CEO"`.  
* El loop de LangGraph se detiene inmediatamente. Se cancela la generación de archivos locales en Claude Cowork.  
* Se prepara un *payload* de error para el frontend, donde no se muestra una sugerencia, sino un diagnóstico técnico de por qué la petición del humano es inviable según el Libro Vivo.

# PM \- Contrato de Interfaz

**Contrato de Interfaz (UI Contract)**.

El JSON Schema de la "Tarjeta de Sugerencia" es el punto donde el razonamiento algorítmico crudo de LangGraph se transforma en una experiencia visual intuitiva para el "Encargado Real" en Next.js.

Este *payload* debe ser lo suficientemente dinámico para renderizar dos escenarios diametralmente opuestos:

1. **El Escenario Ideal (80/20):** La táctica fue exitosa, los archivos se generaron en Claude Cowork y esperan la firma.  
2. **El Escenario de Bloqueo (Escalamiento):** El Agente PM falló el protocolo de autocorrección y necesita que el humano destrabe una paradoja de negocio.

A continuación, presento el esquema de datos estricto que se inyectará en la variable `payload_tarjeta_sugerencia` del estado global.

---

### **JSON Schema: `TARJETA_SUGERENCIA_UI.json`**

JSON  
{  
  "$schema": "http://json-schema.org/draft-07/schema\#",  
  "title": "Payload Tarjeta de Sugerencia UI \- NJM OS",  
  "description": "Contrato de datos para renderizar la tarjeta de decisión en el frontend (Next.js).",  
  "type": "object",  
  "required": \["id\_transaccion", "estado\_ejecucion", "metadata", "contenido\_tarjeta", "acciones\_ui\_disponibles"\],  
  "properties": {  
    "id\_transaccion": {  
      "type": "string",  
      "description": "UUID único para trazar la decisión firmada en la base de datos."  
    },  
    "estado\_ejecucion": {  
      "type": "string",  
      "enum": \["LISTO\_PARA\_FIRMA", "BLOQUEO\_CEO"\],  
      "description": "Dicta qué variante de UI va a renderizar Next.js (Tarjeta verde de éxito o tarjeta roja de alerta)."  
    },  
    "metadata": {  
      "type": "object",  
      "properties": {  
        "skill\_utilizada": { "type": "string", "description": "Ej. 'generar\_business\_case'" },  
        "timestamp\_generacion": { "type": "string", "format": "date-time" }  
      },  
      "required": \["skill\_utilizada", "timestamp\_generacion"\]  
    },  
    "contenido\_tarjeta": {  
      "type": "object",  
      "properties": {  
        "propuesta\_principal": {  
          "type": "string",  
          "description": "Resumen ejecutivo de 1 oración. Ej. 'Propuesta: Pivotar a estrategia de Retención de Clientes.'"  
        },  
        "framework\_metodologico": {  
          "type": "string",  
          "description": "Ej. 'Fundamentado en: Matriz de Ansoff y Customer Lifetime Value.'"  
        },  
        "check\_coherencia\_adn": {  
          "type": "object",  
          "properties": {  
            "aprobado": { "type": "boolean" },  
            "justificacion": { "type": "string", "description": "Ej. 'Alineado con el valor de Accesibilidad del Vector 1.'" }  
          },  
          "required": \["aprobado", "justificacion"\]  
        },  
        "archivos\_locales\_cowork": {  
          "type": "array",  
          "description": "Links directos para que el humano abra los entregables generados en su escritorio.",  
          "items": {  
            "type": "object",  
            "properties": {  
              "nombre\_archivo": { "type": "string", "description": "Ej. 'PRD\_Q3\_Campaña.docx'" },  
              "ruta\_absoluta": { "type": "string", "description": "Ej. 'file:///NJM\_OS/Marcas/Disrupt/PRD\_Q3\_Campaña.docx'" }  
            },  
            "required": \["nombre\_archivo", "ruta\_absoluta"\]  
          }  
        },  
        "log\_errores\_escalamiento": {  
          "type": "array",  
          "items": { "type": "string" },  
          "description": "Solo se envía si estado\_ejecucion es BLOQUEO\_CEO. Contiene las banderas rojas que el PM no pudo resolver."  
        }  
      },  
      "required": \["propuesta\_principal", "framework\_metodologico", "check\_coherencia\_adn"\]  
    },  
    "acciones\_ui\_disponibles": {  
      "type": "array",  
      "description": "Los botones que Next.js debe dibujar para que el humano actúe.",  
      "items": {  
        "type": "object",  
        "properties": {  
          "label": { "type": "string", "description": "Texto del botón (ej. 'Aprobar y Ejecutar')" },  
          "accion\_backend": { "type": "string", "description": "El endpoint o evento que dispara en FastAPI/LangGraph." },  
          "variante\_visual": { "type": "string", "enum": \["primario\_success", "secundario\_outline", "peligro\_rojo"\] }  
        },  
        "required": \["label", "accion\_backend", "variante\_visual"\]  
      }  
    }  
  }  
}

### **La Lógica de Implementación en el Frontend (Next.js)**

Este esquema JSON le quita toda la carga cognitiva al frontend. Next.js no tiene que adivinar qué pasó en el backend; simplemente lee el JSON y pinta los componentes.

**Ejemplo de renderizado dinámico basado en el JSON:**

1. **Si el `estado_ejecucion` es `"LISTO_PARA_FIRMA"`:**  
   * El componente UI en Next.js pinta un checkmark verde en el `check_coherencia_adn`.  
   * Muestra la lista de `archivos_locales_cowork` como tarjetas clicables que abren Word o Excel gracias a la integración con el sistema de archivos local de Claude Cowork.  
   * En `acciones_ui_disponibles`, el backend envía los botones:  
     * *Aprobar y Continuar* (variante `primario_success`).  
     * *Proponer Alternativa* (variante `secundario_outline`).  
2. **Si el `estado_ejecucion` es `"BLOQUEO_CEO"`:**  
   * El frontend pinta un banner rojo intenso.  
   * Ignora los `archivos_locales_cowork` (porque el Agente PM canceló su creación).  
   * Muestra el `log_errores_escalamiento` en un recuadro de advertencia (ej. *"🚨 Riesgo Financiero: El presupuesto no cuadra con el Vector 2"*).  
   * En `acciones_ui_disponibles`, los botones cambian a:  
     * *Ajustar Presupuesto* (variante `secundario_outline`).  
     * *Forzar Aprobación asumiendo el riesgo* (variante `peligro_rojo`).

