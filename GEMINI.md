# DIRECTIVA OBLIGATORIA: INTEGRIDAD DE DATOS Y PROHIBICIÓN TOTAL DE HARDCODING

**Nivel de Cumplimiento:** Estricto / Crítico  
**Alcance:** Modelado de datos, interfaces de usuario, scripts de backend, integraciones API y lógica de negocio.

---

### 1. Prohibición Absoluta de Hardcoding y Mock Data
* **Cero Datos Falsos en Producción o Staging:** Queda estrictamente prohibido el uso de colecciones ficticias, arrays de prueba incrustados (*dummy/mock arrays*), IDs simulados o literales estáticos para emular respuestas de base de datos o APIs.
* **Prohibición de Valores "Quemados":** No se admiten configuraciones de conexión, URLs base, enlaces de redirección fijos, identificadores personales, claves criptográficas ni parámetros de negocio escritos directamente en el código fuente. Todo parámetro debe provenir de variables de entorno (`.env`), esquemas de configuración validados, sesión activa o colecciones maestras.

---

### 2. Consumo Dinámico y Esquemas Reales
* **Fuente Única de Verdad:** Toda vista, reporte o proceso reactivo debe consumir datos reales directamente desde las fuentes vivas (MongoDB, Firebase, APIs REST o llamadas a endpoints autorizados).
* **Manejo de Estados Vacíos (*Empty States*):** Si una colección o consulta no devuelve registros, la interfaz y el controlador deben manejar explícitamente el estado nulo o vacío (`[]` o `null`) mediante componentes de carga o mensajes de "sin registros", sin inventar registros temporales para llenar la pantalla.

---

### 3. Validación y Fallos Tempranos (*Fail-Fast*)
* **Cero Fallbacks Ficticios:** Si una variable requerida o una conexión a la base de datos no está presente o falla, el sistema debe emitir un error explícito en consola/logs y detener la operación. Queda prohibido enmascarar errores inyectando datos de respaldo estáticos (*fallbacks dummy*).
* **Aislamiento de Pruebas:** Cualquier script de testing o prueba unitaria debe estar estrictamente confinado a su entorno (`*.test.*` o fixtures dedicados) y jamás acoplarse ni filtrarse al código de compilación o runtime del aplicativo.
