# Reglas de origen: Java (Java SE / Java EE / Jakarta EE / Spring)

Reglas específicas del stack Java. Se inyectan como contexto a los agentes `modernization-assessment-*`.
Los prompts definen QUÉ analizar en cada fase; este archivo define CÓMO se manifiesta en Java.
Complementan (no reemplazan) las instrucciones del prompt. Toda versión, fecha de EOL o CVE
mencionada aquí es orientativa: verifícala contra la fuente oficial antes de afirmarla.

## Detección (orquestador)
- Manifiestos: `pom.xml` (Maven), `build.gradle` / `build.gradle.kts` (Gradle), `settings.gradle`.
- Código: `.java`; web: `WEB-INF/web.xml`, `*.jsp`, `*.xhtml` (JSF/Facelets), `weblogic.xml`,
  `jboss-web.xml`, `application.xml` (EAR).
- Stack dominante si la mayoría del código propio es `.java`.

## Fase 1 · Discovery

### Manifiestos y dependencias
- Lee **todos** los `pom.xml` (raíz, módulos, `<parent>`): las `<dependencies>` del POM padre se
  heredan; `<dependencyManagement>` solo fija versiones. Indica en qué POM se declara cada una.
- Un parent POM corporativo no disponible puede fijar versiones adicionales: decláralo.
- Scopes: `compile` (se empaqueta), `provided` (lo aporta el servidor), `runtime`, `test`. Una API
  de plataforma en `compile` se empaqueta en el WAR (hallazgo).
- Gradle: configuraciones `implementation`, `api`, `compileOnly`, `runtimeOnly`.
- Propiedades de versión (`<version.x>`) y BOM importados.

### Sintaxis para conteos
- Uso por prefijo de paquete: `grep -rh "^import <paquete>" --include='*.java'`. Cuenta también
  `import static`, imports comodín (`import x.y.*;`) y **nombres calificados** en el código
  (`org.x.Clase.metodo(...)`) o en descriptores XML (`web.xml`, `applicationContext.xml`,
  `faces-config.xml`).
- Comentarios a excluir: `//`, `/* … */`, Javadoc `/** … */`; en XML y XHTML `<!-- … -->` (con
  `FACELETS_SKIP_COMMENTS=true` ni siquiera se envían al navegador).
- Código comentado: líneas `//` con sintaxis de código (`;`, `{`, `}`); Javadoc no es código
  comentado.
- Anotaciones como evidencia de uso (`@Autowired`, `@Inject`, `@ManagedBean`, `@WebServlet`,
  `@WebFilter`).

### Código de terceros y generado
- JAR copiados en `WEB-INF/lib/` o `lib/`; JS/CSS vendorizado en `webapp/resources/`,
  `static/`, `public/`.
- Código **generado** (stubs `wsimport`/CXF, clases JAXB, MapStruct, Lombok delombok): clasifícalo
  como generado, no como propio.

### Productos de nombre confundible (CVE)
- `commons-httpclient` 3.x (retirado) ≠ HttpComponents `httpclient` 4.x / `httpclient5`.
- Log4j 1.x (`org.apache.log4j`) ≠ Log4j 2 (`org.apache.logging.log4j`): CVE distintas.
- Spring Framework se publica por módulos (`spring-core`, `spring-web`, `spring-webmvc`,
  `spring-messaging`, …): muchas CVE afectan a un solo módulo; verifica que esté declarado.
- `javax.*` (Java EE) ≠ `jakarta.*` (Jakarta EE 9+).
- Algunas CVE requieren una versión de JDK concreta (p. ej. JDK 9+); anota la JVM del proyecto.
- JSF: Mojarra (`com.sun.faces`, `jsf-impl`, CPE `eclipse:mojarra`) ≠ JSF de GlassFish / Oracle
  Fusion Middleware (CPE `oracle:*`). En WebLogic, si `weblogic.xml` no incluye `javax.faces.*` /
  `com.sun.faces.*` en `prefer-application-packages`, la JSF efectiva puede ser la del servidor:
  decláralo como condición.
- Jasper: `jasperreports` (Library) ≠ JasperReports Server; Bootstrap 3.x ≠ 4.x y jQuery < 1.12
  quedan fuera de varias CVE de XSS conocidas: comprueba el límite inferior del rango.

### Forma concreta de los patrones de defecto
| Patrón (prompt) | Cómo se ve en Java |
|---|---|
| Vías de autenticación | Spring Security `form-login` / `http-basic` activos (`auto-config="true"` habilita `form-login`, `http-basic` y `logout`: cada uno es una vía con ficha propia); `UserDetailsService` en memoria o mock; `UsernamePasswordAuthenticationToken(principal, credentials, authorities)` (constructor de 3 argumentos = ya autenticado) puesto en el `SecurityContext` sin pasar por `AuthenticationManager`; login propio en un managed bean o servlet; JWT validado con clave literal (jjwt, java-jwt) |
| Cobertura de autorización | `intercept-url` / `requestMatchers` sin regla por defecto (`/**`); `@WebFilter(urlPatterns=…)` que no cubre todos los `servlet-mapping` del `FacesServlet` (`*.jsf`, `*.faces`, `/faces/*`, `/views/*`); `web.xml` sin `metadata-complete` (las anotaciones cuentan) |
| Exposición de fuentes | Vistas `*.xhtml`/`*.jsp` servidas por el servlet por defecto cuando el `FacesServlet` no las mapea; `welcome-file` apuntando a una vista sin procesar |
| Estado compartido | Campos de instancia en `HttpServlet` (una instancia por contenedor); beans Spring `singleton` con estado; `static` mutable; JSF `@ApplicationScoped`; archivos de salida con nombre fijo bajo un directorio común |
| TLS deshabilitado | `X509TrustManager` vacío; `HostnameVerifier` que retorna `true`; `HttpsURLConnection.setDefaultSSLSocketFactory/HostnameVerifier` (afecta a **toda la JVM**); `TrustStrategy` que acepta todo; `NoopHostnameVerifier` |
| XXE | `DocumentBuilderFactory`, `SAXParserFactory`, `XMLInputFactory`, `TransformerFactory`, `SchemaFactory` sin `disallow-doctype-decl` / `FEATURE_SECURE_PROCESSING` |
| Deserialización | `ObjectInputStream.readObject` sobre datos externos; JSF `javax.faces.STATE_SAVING_METHOD=client` sin cifrado/MAC del estado (parámetros según implementación: Mojarra, MyFaces); XStream; Jackson con default typing |
| Logging peligroso | Log4j 2 en rango Log4Shell (verificar rango en NVD) con datos del usuario en el mensaje; Log4j 1.x (EOL); `System.out`/`printStackTrace`; interceptores que registran cuerpos SOAP completos |
| Compilación / evaluación dinámica | `JasperCompileManager.compileReport*` en cada petición; `ScriptEngine`; Expression Language construido con entrada del usuario |
| XSS | JSF `escape="false"`; JSP `<%= %>` sin `fn:escapeXml`; `out.print` de entrada |
| SQL | `Statement` con concatenación; JPQL/HQL concatenado; `createNativeQuery` con concatenación |
| URL con datos de la petición | `request.getServerName()`, `getScheme()`, `getHeader("Host")`, `X-Forwarded-*` usados para construir llamadas salientes |

## Fase 2 · AS-IS

### Manejo de excepciones y compensaciones
- `try / catch / finally`; `catch (Exception)` o `catch (Throwable)` genéricos; `catch` vacíos.
- Tras un `catch` que traga, el método devuelve el **último valor asignado** a la variable de
  retorno (p. ej. la respuesta exitosa de un paso anterior), no un objeto vacío: compruébalo.
- Parseo de archivos (POI, CSV): `String.valueOf(double)` produce notación científica desde 10^7;
  arreglos de tamaño fijo por fila lanzan `ArrayIndexOutOfBoundsException` con columnas extra.
- Escrituras fuera de las acciones de guardar: listeners de JSF (`valueChangeListener`,
  `<p:ajax listener>`, `on…Change`) y métodos de consulta que invocan operaciones de escritura
  (p. ej. `ingresar…`, `actualizar…`) de otra integración; inclúyelas en el inventario.
- Una integración que solo captura su excepción tipada (p. ej. `XxxException` del stub) deja pasar
  `RuntimeException`, `WebServiceException` o `SOAPFaultException`: el `catch` externo decide el
  resultado. Recórrelo hasta el `catch` que realmente la atrapa.
- Recursos sin `try-with-resources` ni cierre en `finally` (streams, conexiones).

### Ciclo de vida, hilos y concurrencia
- Hooks: `@PostConstruct`, `@PreDestroy`, `ServletContextListener`, `HttpSessionListener`,
  constructores de managed beans.
- Hilos y tareas: `new Timer()`, `ExecutorService`, `@Scheduled`, `@Asynchronous`, `new Thread`.
  Un `Timer` creado por sesión que actúa sobre estado estático afecta a todos los usuarios.
- Scopes: JSF/CDI `@RequestScoped`, `@ViewScoped`, `@SessionScoped`, `@ApplicationScoped`; Spring
  `singleton` (por defecto), `prototype`, `request`, `session`.
- Clientes SOAP (`*PortType`, `Service`) guardados en campos `static` y reconfigurados en
  constructores: estado compartido entre hilos.

### Ruido en el grafo de dependencias
- `Logger.getLogger(OtraClase.class)` / `LoggerFactory.getLogger(OtraClase.class)`: import sin
  dependencia arquitectónica.
- Un campo `new XxxIntegracion()` sin llamadas en la clase no es dependencia: cita la llamada.
- Imports usados solo en constantes, Javadoc (`@see`, `{@link}`) o código comentado.
- Instanciación directa (`new XxxFacade()`) frente a inyección (`@Autowired`, `@Inject`,
  `@ManagedProperty`, `@Resource`): la primera es dependencia real.

### Interfaz web (si aplica)
- Dominio de una vista: los managed beans que usa (`#{bean.…}` en el `.xhtml`) y los atributos que
  sus servlets leen de la sesión (`getSession().getAttribute(...)`); una vista con beans de otro
  dominio se corta con ese dominio.
- Comportamientos dependientes de la petición: `getServerName()`, `getServerPort()`, `isSecure()`,
  `getRemoteAddr()`, cookies (`Cookie`, `HttpOnly`, `Secure`), callbacks construidos con esos
  valores.
- Timeout de sesión en `web.xml` (`<session-timeout>`), `create-session` de Spring Security.

## Fase 3 · TO-BE

### Conceptos Java → opciones destino (se comparan en escenarios y ADR abiertos, no por defecto)
| Concepto Java | Opciones a evaluar |
|---|---|
| WAR en servidor de aplicaciones (WebLogic, WebSphere, JBoss) | Servicios en contenedores (ECS/EKS) con un framework vigente (p. ej. Spring Boot); funciones Lambda por operación; replatform del WAR a Jakarta EE vigente |
| `@RestController` / JAX-RS | Endpoint en el servicio contenedorizado o API Gateway + Lambda |
| Lógica en managed beans JSF / servlets | Servicio de dominio con reglas explícitas y testeables |
| JSF / JSP / Thymeleaf (SSR) | SPA o SSR moderno; Jakarta Faces vigente si se conserva SSR |
| Clientes JAX-WS / CXF | Clientes regenerados desde WSDL con un stack Jakarta vigente, aislados en un ACL |
| JPA / Hibernate / JDBC | RDS/Aurora o almacén purpose-built según patrón de acceso |
| `HttpSession` con estado de proceso | Sin estado en el servidor de aplicación: token + estado externo (base de datos o caché) |
| Spring Security / filtros propios | Validación de tokens OIDC/JWT emitidos por un IdP gestionado; autorización por operación |
| `application.properties` / XML externo / JNDI | Secrets Manager, Parameter Store o AppConfig |
| AWS SDK for Java 1.x | AWS SDK for Java 2.x (verificar el estado de soporte de 1.x en la doc de AWS) |
| JasperReports / iText / POI | Versiones vigentes (verificar licencias, p. ej. AGPL de iText) o alternativas |

### Riesgos típicos al migrar desde Java legado
- Salto `javax.*` → `jakarta.*` en todas las capas al actualizar servidor o frameworks.
- Inyección de dependencias de Spring en Lambda: evitar arrancar todo el contexto en cada
  invocación; evaluar SnapStart o empaquetado mínimo (verificar runtimes compatibles).
- Estado en memoria entre peticiones (singletons, `static`, sesión): externalizarlo.
- Transacciones JPA multi-tabla: mantenerlas en un relacional o rediseñar el patrón de acceso.
- Stubs y librerías internas del cliente no disponibles: bloquean la compilación de módulos que
  los reutilicen.
- WebLogic detrás de un balanceador: `getServerName()`, `getServerPort()` e `isSecure()` devuelven
  los valores del servidor salvo `FrontendHost` / `FrontendHTTPSPort` o `WL-Proxy-SSL`; las
  llamadas de servidor a la misma aplicación no llevan la cookie de afinidad del balanceador.
- JSF con `STATE_SAVING_METHOD=client`: el ViewState viaja en cada POST y puede superar los
  límites de inspección o de tamaño de un WAF; mídelo en la PoC.

### Estado, vías de autenticación y rutas (para los pasos de corte y la contención)
- Estado de sesión o de conversación, según el framework: managed beans JSF o CDI
  (`@SessionScoped`, `@ViewScoped`, `@ConversationScoped`, `#{bean.…}` en `.xhtml`/`.jsp`); beans de
  Spring con `@SessionScope` o `scope="session"` y `@SessionAttributes` de Spring MVC; Spring Web
  Flow; `ActionForm` de Struts con scope de sesión; `HttpSession.setAttribute`/`getAttribute` en
  servlets, JSP y filtros. Por cada atributo o bean: quién lo escribe y quién lo lee. Una vista,
  servlet, reporte o descarga pertenece al dominio de lo que lee y se corta después de todo lo que
  lo escribe.
- Vías de autenticación, una por cada mecanismo activo: Spring Security en XML
  (`<http auto-config="true">` habilita form-login, http-basic y logout; `<remember-me>`, `<x509>`)
  o en Java config (`formLogin()`, `httpBasic()`, `rememberMe()`, `oauth2Login()`); contenedor
  (`<login-config>` de `web.xml` con BASIC, FORM o CLIENT-CERT; realms de WebLogic, Tomcat o JBoss);
  JAAS, Shiro, adaptadores de SSO o Keycloak; filtros propios que aceptan cookies, tokens o
  cabeceras; y los mecanismos que validan o renuevan una sesión ya creada.
- Rutas alternativas al mismo recurso: mapeos de servlet duplicados (`*.jsf`, `*.faces`,
  `/faces/*`, `*.do`, `*.action`), solapes entre `@WebServlet` y `<servlet-mapping>`, recursos
  accesibles fuera de `WEB-INF`, y URL por defecto de los frameworks (`/login`, `/logout`,
  `/j_security_check`) que interceptan antes que un servlet propio.

### Validación
- Contratos tipados explícitos en el lenguaje destino (DTO / esquemas OpenAPI).
- Credenciales de `properties` o XML → Secrets Manager o Parameter Store, nunca en código.
