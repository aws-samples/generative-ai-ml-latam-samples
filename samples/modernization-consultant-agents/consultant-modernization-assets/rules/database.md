# Reglas de origen: Base de datos (schema + procedimientos) → destino evaluado por ADR

Reglas específicas del stack **base de datos** cuando el repositorio de origen es el script o
dump de una base de datos (schema + lógica de negocio embebida), analizado como caso EXCLUSIVO e
independiente de la aplicación. Se inyectan como contexto a los agentes modernizadores (`modernization-assessment-*`)
durante las tres fases. Complementan (no reemplazan) las instrucciones del prompt de cada fase.
Los prompts definen QUÉ analizar; este archivo define CÓMO se aplica a una base de datos.

## Detección (orquestador)
- Repositorio predominante de artefactos de base de datos: `.sql`, `.pks`/`.pkb`, `.prc`, `.fnc`,
  `.trg`, `.ddl`, `.vw`; sentencias `CREATE TABLE`, `CREATE OR REPLACE
  PACKAGE|PROCEDURE|FUNCTION|TRIGGER|VIEW`; migraciones Flyway/Liquibase; dumps
  (`expdp`/`mysqldump`/`pg_dump`).
- El "lenguaje" es SQL y su dialecto procedural (PL/SQL, T-SQL, PL/pgSQL, SQL/PSM).
- Caso EXCLUSIVO: el stack es `database` y el análisis cubre solo la BD. Si existe una aplicación
  que la usa, se analiza en su propia corrida con su regla de lenguaje.

## Reglas de los prompts que no aplican a este stack
Las reglas de interfaz web (sesión de navegador, cookies, cabeceras, proxies, XHR, egresos del
navegador) y las de frontend/CDN no aplican salvo que la propia BD exponga un endpoint HTTP
(p. ej. ORDS, APEX). Omítelas y decláralo; no fuerces secciones vacías.

## Agnóstico al motor (regla central)
El agente NO asume un motor. DETECTA el motor y su dialecto procedural a partir de la sintaxis del
script y adapta todo el análisis y las recomendaciones a las buenas prácticas de ESE proveedor más
las de la comunidad. Debe funcionar igual para Oracle (PL/SQL), Microsoft SQL Server (T-SQL),
PostgreSQL (PL/pgSQL), MySQL/MariaDB (procedimientos SQL/PSM) y otros motores relacionales.

Señales para detectar el motor (no exhaustivo):
| Motor | Señales típicas en el script |
|---|---|
| Oracle | `CREATE OR REPLACE PACKAGE`, `.pks/.pkb`, `VARCHAR2`, `NUMBER`, `DUAL`, `CONNECT BY`, `DBMS_*`, `NVL`, secuencias `.NEXTVAL` |
| SQL Server (T-SQL) | `CREATE PROCEDURE ... AS BEGIN`, `[dbo].`, `NVARCHAR`, `IDENTITY`, `GETDATE()`, `@variables`, `MERGE`, `TOP` |
| PostgreSQL | `CREATE FUNCTION ... LANGUAGE plpgsql`, `$$`, `SERIAL`/`GENERATED`, `RETURNS TABLE`, extensiones (`CREATE EXTENSION`) |
| MySQL / MariaDB | `DELIMITER //`, `AUTO_INCREMENT`, `ENGINE=InnoDB`, backticks `` `col` ``, `NOW()` |
Si el dialecto es ambiguo o mixto, decláralo y trata cada objeto según su sintaxis real. Nunca
fuerces una recomendación de un motor a otro sin verificarla.

## Fuente de verdad para recomendaciones
Toda recomendación se apoya en, y cita, buenas prácticas actuales de tres fuentes, en este orden:
1. **Documentación oficial del proveedor del motor** detectado (versión, EOL, features deprecadas,
   ruta de upgrade certificada, herramientas de pre-check).
2. **AWS**, vía el MCP de AWS Knowledge, para todo lo relativo al destino en AWS (RDS/Aurora,
   DynamoDB, DMS, SCT/DMS Schema Conversion): versiones soportadas, límites, disponibilidad
   regional, patrones prescriptivos. Nunca afirmes cifras de AWS de memoria.
3. **Consenso de la comunidad** (patrones ampliamente aceptados) cuando complementa a lo anterior.
Distingue siempre lo verificado en documentación de lo que es criterio propio de diseño.

## Descubrimiento de objetos (Fase 1 · Discovery)
Inventaría los objetos como el equivalente al inventario de componentes. Mide con comandos
(`grep -c`, `grep -rn`), no leyendo todo el script:
- **Estructura**: tablas, vistas, vistas materializadas, secuencias/`AUTO_INCREMENT`/`IDENTITY`,
  sinónimos, tipos, índices, constraints (PK/FK/UNIQUE/CHECK).
- **Lógica de negocio embebida**: procedures, functions, packages (Oracle), triggers, jobs/
  schedulers. Cuenta LOC procedural por objeto: es el "código propio a migrar" y el hallazgo de
  mayor impacto.
- **Seguridad y acceso**: usuarios/roles, `GRANT`/privilegios, enlaces entre bases (`DBLINK`,
  linked servers, `dblink`/FDW), `DIRECTORY`/acceso a archivos.
- **Datos**: volumen estimado por tabla si hay `INSERT`/dumps; tablas transaccionales vs. de
  catálogo/paramétricas.
Separa SIEMPRE dos cifras: (a) volumen total del script y (b) lógica de negocio propia real a
migrar (LOC de procedures/functions/packages/triggers), excluyendo datos semilla y DDL repetitivo.

### Sintaxis para conteos
- Comentarios a excluir: `--` y `/* … */` (en MySQL también `#`).
- Uso o dependencia entre objetos: llamadas `paquete.procedimiento(...)`, `EXEC` / `EXECUTE`,
  `CALL`, `PERFORM`, referencias en `FROM`/`JOIN`, triggers sobre tablas, sinónimos, `DBLINK`.
- SQL dinámico: la dependencia puede estar dentro de un string (`EXECUTE IMMEDIATE`,
  `sp_executesql`); repórtala como dependencia probable y márcala.
- Código comentado o deshabilitado (`/* … */` con sentencias, triggers `DISABLE`, jobs
  deshabilitados): no es evidencia de comportamiento activo; decláralo.

### Forma concreta de los patrones de defecto
| Patrón (prompt) | Cómo se ve en una base de datos |
|---|---|
| Vías de autenticación | Cada mecanismo es una vía con ficha propia: usuarios de BD con contraseña (por defecto o en scripts), autenticación externa o del sistema operativo (`IDENTIFIED EXTERNALLY`, autenticación de Windows, `trust`/`peer` en `pg_hba.conf`), usuarios proxy, credenciales guardadas en enlaces entre bases (`DBLINK`, linked servers, `USER MAPPING`); cuentas compartidas de aplicación; autenticación de aplicación implementada en tablas propias con hash débil o en claro |
| Cobertura de autorización | `GRANT … TO PUBLIC`; roles `DBA` / `sysadmin` / `ALL PRIVILEGES` sin necesidad; `EXECUTE` sobre paquetes sensibles a todos; ejecución con privilegios del definidor (`AUTHID DEFINER`, `SECURITY DEFINER`); acceso alternativo a la misma tabla por sinónimos públicos, vistas o enlaces entre bases con más privilegios que el acceso directo |
| Estado compartido y concurrencia | Folios generados con `SELECT MAX()+1` en lugar de secuencias o `IDENTITY`; tablas de trabajo globales sin clave de sesión; variables de paquete con estado |
| Compilación / evaluación dinámica | SQL dinámico construido por concatenación |
| Datos personales en logs | Tablas de auditoría o de log que guardan valores completos de PII |

## Reinterpretación de las secciones de Fase 2 (AS-IS)
| Término del prompt | Equivalente en este stack |
|---|---|
| Capas y componentes | Esquemas, paquetes y objetos agrupados por responsabilidad |
| Bounded contexts | Agrupación de tablas y procedures por área funcional (esquemas, prefijos, módulos) |
| Flujos críticos | Procedures/triggers que escriben en varias tablas o esquemas, jobs batch |
| Manejo de excepciones y compensación | `EXCEPTION WHEN …` (PL/SQL), `BEGIN TRY / BEGIN CATCH` (T-SQL), `EXCEPTION` (PL/pgSQL); `SAVEPOINT`, `ROLLBACK`, `COMMIT` dentro de procedures; `PRAGMA AUTONOMOUS_TRANSACTION` |
| Transacción distribuida | Escrituras a través de `DBLINK`, linked servers, FDW o colas de la BD |
| Ciclos de dependencia | Paquetes o procedures que se invocan mutuamente; triggers en cascada |
| Ruido en dependencias | Referencias en comentarios o en código muerto |
| Hilos y temporizadores | Jobs y schedulers (`DBMS_SCHEDULER`, SQL Agent, `pg_cron`, eventos de MySQL) |
| Bloque que traga el error | `WHEN OTHERS THEN NULL`, `BEGIN CATCH` sin `THROW`, `EXCEPTION WHEN OTHERS` que solo registra: el procedimiento termina con éxito y los parámetros `OUT` conservan el último valor asignado. Un manejador de un error concreto (`NO_DATA_FOUND`, `DUP_VAL_ON_INDEX`) deja pasar los demás: recórrelo hasta el manejador que realmente lo atrapa |
| Escrituras fuera de los procesos principales | Triggers que escriben en otras tablas, funciones invocadas desde `SELECT` que escriben (con `PRAGMA AUTONOMOUS_TRANSACTION` o equivalentes), jobs que modifican datos que otro proceso lee; inclúyelas en el inventario |
| Parseo de datos externos | `TO_NUMBER`/`CAST` sobre texto importado (separador decimal, notación científica, ceros a la izquierda), `SQL*Loader`/`BULK INSERT`/`COPY` con columnas extra o faltantes |

## Qué buscar como vulnerabilidad (Fase 1 · catálogo SEC-xx)
Adapta al dialecto detectado. Numeración estable SEC-xx igual que el resto del set:
- SQL dinámico por concatenación de strings (inyección) en procedures/functions (`EXECUTE
  IMMEDIATE`, `sp_executesql`, `EXECUTE`, `PREPARE`).
- Privilegios excesivos: `GRANT ... TO PUBLIC`, roles con `DBA`/`ALL PRIVILEGES`/`sysadmin` sin
  necesidad.
- Credenciales o cadenas de conexión hardcodeadas en jobs, scripts o enlaces entre bases.
- Datos sensibles (RUT, credenciales, datos de salud/financieros) sin cifrado en reposo ni
  enmascaramiento.
- Enlaces entre bases / acceso a sistema de archivos que exponen superficie externa no controlada.
- Ausencia de auditoría/trazabilidad en operaciones sensibles.
- Autorización implementada solo a nivel de BD (fácil de eludir si cambia el acceso).

## Diagramas (Fase 2 · AS-IS, Mermaid embebido)
- Modelo de datos real: `erDiagram` con entidades y relaciones inferidas del DDL.
- Flujos de negocio críticos que atraviesan procedures/triggers: `sequenceDiagram`.
- Grafo de dependencias entre objetos (packages/procedures/triggers) y su acoplamiento:
  `flowchart` marcando ciclos con `classDef`.
Los "bounded contexts" se infieren de la agrupación de tablas y procedures por área funcional
(esquemas, prefijos de nombres, módulos), no de clases de aplicación.

## Escenarios de destino a evaluar (Fase 3, en un ADR abierto)
La estructura del documento de opciones del prompt se mantiene, y los **cuatro escenarios** de
esta sección son los escenarios de su sección 3. Adapta las secciones al dominio de datos: las
restricciones giran en torno al motor, el modelo de datos y la lógica embebida; los patrones, al
schema y los procedures/functions/triggers; los diagramas priorizan `erDiagram` y el mapeo
objeto-legacy → componente-destino. Omite lo que no aplique (frontend, CDN, sesión web) en vez
de forzarlo. La recomendación es agnóstica al motor: detecta motor y dialecto desde el análisis
previo y sustenta cada escenario en las buenas prácticas actuales de ese proveedor, de la
comunidad y de los patrones prescriptivos de AWS, citando la fuente.

El consultor NO fija el destino: evalúa los cuatro escenarios contra la evidencia de las Fases 1
y 2 (volumen de datos, cantidad y complejidad del código procedural, acoplamiento, integridad
transaccional, patrones de acceso, características propietarias usadas), los compara en la
matriz y sugiere uno —o una combinación— como condición, en un ADR abierto (MADR) con opciones,
pros/contras, consecuencias y fuentes. Las buenas prácticas por escenario son AGNÓSTICAS: aplican al motor detectado.

### 1. Actualización de versión del mismo motor (in-place upgrade)
Cuándo: motor con soporte a futuro, código procedural sano, sin driver de negocio para cambiar de
tecnología. Complejidad baja/media, menor riesgo funcional.
Buenas prácticas a recomendar (verificar contra la doc del proveedor detectado):
- Determinar la versión actual y su **fecha de EOL**; un motor pasado de EOL queda sin parches de
  seguridad y es en sí un hallazgo crítico.
- Ejecutar la **herramienta de pre-check** del proveedor antes de decidir: PostgreSQL
  `pg_upgrade --check` (más auditoría manual de extensiones, que la verificación de binario no
  cubre); MySQL **Upgrade Checker** de MySQL Shell; Oracle **AutoUpgrade**/preupgrade; SQL Server
  Data Migration Assistant. Reportar los bloqueadores que arroje.
- Inventariar **features deprecadas o removidas** entre la versión origen y la destino: son lo que
  rompe el upgrade y debe corregirse antes.
- Verificar **compatibilidad de extensiones/complementos** (p. ej. PostGIS, pgvector, pg_cron en
  PostgreSQL) con la versión destino; una extensión sin build para el destino bloquea el upgrade.
- Backup verificado y plan de rollback antes de cualquier upgrade (varios motores no soportan
  downgrade). Definir estrategia: dump/restore, replicación lógica, o upgrade gestionado del
  proveedor cloud.

### 2. Refactorización a otro motor (migración heterogénea)
Cuándo: reducción de licenciamiento, alineación cloud-native, motor origen en EOL. Complejidad
media/alta. Ej. genérico: motor comercial → PostgreSQL/MySQL gestionado (RDS/Aurora).
Buenas prácticas a recomendar (verificar vía MCP de AWS Knowledge):
- Usar **AWS SCT / DMS Schema Conversion** para evaluar la complejidad y convertir schema y código;
  el reporte de conversión clasifica qué se convierte automáticamente y qué requiere reescritura
  manual (esa fracción manual es el driver de complejidad; se reporta como proporción de
  objetos, no como esfuerzo ni plazo).
- Usar **AWS DMS** para la migración de datos, con estrategia de mínimo downtime (carga completa +
  CDC) para volúmenes grandes.
- Mapear equivalencia de **tipos de dato** y traducir **características propietarias sin equivalente
  directo** (secuencias, tipos jerárquicos, paquetes nativos): cada una es un punto crítico.
- Si es una aplicación de terceros sobre la BD, verificar que el proveedor soporte el motor destino
  antes de proponerlo.

### 3. Mover lógica de negocio a middleware (descomposición)
Cuándo: la lógica procedural es extensa y es el activo a preservar y hacer evolucionable; se busca
desacoplar reglas del motor, habilitar pruebas y despliegue independientes. Alto valor y alta
complejidad/riesgo (pérdida de reglas no documentadas). Sigue el patrón prescriptivo de AWS de tres
fases: **analizar → clasificar → migrar** la lógica, con plan de rollback.
Buenas prácticas a recomendar:
- Documentar cada procedure/trigger/function: propósito, reglas de negocio, parámetros,
  dependencias (llamadas anidadas, referencias cross-schema, dependencias de datos implícitas).
- Clasificar la lógica por tipo (validación, cálculo, orquestación, integridad) para decidir qué va
  a servicio/Lambda y qué puede quedar como vista/consulta.
- Atender los tres desafíos típicos: **dependencias complejas**, **gestión transaccional**
  multi-paso en un sistema distribuido, y **rendimiento** de operaciones batch/bulk que hoy se
  benefician de estar junto a los datos.
- Extracción incremental tipo Strangler Fig por dominio; el orden sale del AS-IS.

### 4. Refactorización a híbrido SQL/NoSQL (persistencia poliglota)
Cuándo: patrones de acceso mixtos claros (transaccional fuerte + acceso clave-valor de alto
volumen o desnormalizable). Datos relacionales/transaccionales en RDS/Aurora; accesos de alto
volumen en DynamoDB u otro almacén purpose-built.
Buenas prácticas a recomendar (verificar vía MCP de AWS Knowledge):
- Decidir por **patrón de acceso**, no por moda: elegir DynamoDB solo cuando los patrones de acceso
  son conocidos, acotados y de alto volumen; DynamoDB no favorece consultas ad-hoc ni joins.
- Mapear **explícitamente qué entidad va a qué motor y por qué**; el diseño NoSQL parte de las
  queries, no del modelo relacional.
- Definir la estrategia de **consistencia entre almacenes** y el costo operativo de mantener dos
  tecnologías.
- Principio purpose-built: la capa de datos no tiene por qué ser una sola tecnología; se elige por
  necesidad de cada dominio.

Los escenarios NO son excluyentes: un destino real puede combinar, p. ej., cambio de motor (2) +
extracción parcial de lógica a middleware (3). El ADR documenta la combinación elegida y por qué se
descartan las alternativas.

## Fase 3 · TO-BE: recursos compartidos, vías y accesos (para los pasos de corte y la contención)
- Dominio de un objeto: las tablas que escribe. Por cada tabla: qué procedimientos, triggers,
  jobs y aplicaciones externas la escriben y cuáles la leen. Un objeto se migra después de todo
  lo que escribe las tablas que lee; los escritores de una misma tabla se migran a la vez o con
  un único dueño.
- Vías de autenticación, una por cada mecanismo (ver la tabla de la Fase 1), incluidas las
  credenciales de los enlaces entre bases y las cuentas que usan los jobs.
- Accesos alternativos al mismo dato: sinónimos (públicos o privados), vistas, enlaces entre
  bases, réplicas o exportaciones programadas que otros sistemas consumen; cada uno debe
  redirigirse o cerrarse en el corte.

## Validación
- Ninguna vulnerabilidad SEC-xx crítica/alta del catálogo queda sin remediación explícita en el TO-BE.
- Credenciales y secretos → Secrets Manager / SSM, nunca hardcodeados en el destino.
- SQL dinámico por concatenación → consultas parametrizadas; no se porta el patrón inseguro.
- Cada característica propietaria del motor sin equivalente directo queda registrada como punto
  crítico de migración con su tratamiento en el escenario elegido.
- Toda cifra de versión, EOL, límite o disponibilidad se cita de la doc del proveedor o de AWS,
  nunca de memoria.

## Fuentes de referencia (verificar vigencia al usarlas)
- AWS Prescriptive Guidance — Migrating business logic from the database to the application layer:
  https://docs.aws.amazon.com/prescriptive-guidance/latest/database-decomposition/logic.html
- AWS Prescriptive Guidance — Migration strategy for relational databases:
  https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-database-migration/
- Amazon DynamoDB — Migrating from a relational database:
  https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/migration-guide.html
- AWS — Oracle to Aurora PostgreSQL con DMS/SCT (patrón heterogéneo de referencia):
  https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/migrate-an-oracle-database-to-aurora-postgresql-using-aws-dms-and-aws-sct.html
- PostgreSQL — Upgrading a PostgreSQL Cluster (pg_upgrade): https://www.postgresql.org/docs/current/upgrading.html
- MySQL — Upgrade best practices / Upgrade Checker Utility: https://dev.mysql.com/doc/refman/8.4/en/upgrade-best-practices.html
- Oracle / SQL Server: usar la doc oficial de la versión detectada para EOL, features deprecadas y
  herramienta de pre-check.
Content was rephrased for compliance with licensing restrictions.
