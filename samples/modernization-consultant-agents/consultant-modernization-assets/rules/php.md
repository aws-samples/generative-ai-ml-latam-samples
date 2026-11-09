# Reglas de origen: PHP (PHP plano, Laravel, Symfony, CodeIgniter)

Reglas específicas del stack PHP. Se inyectan como contexto a los agentes `modernization-assessment-*`.
Los prompts definen QUÉ analizar en cada fase; este archivo define CÓMO se manifiesta en PHP.
Complementan (no reemplazan) las instrucciones del prompt. Toda versión, fecha de EOL o CVE
mencionada aquí es orientativa: verifícala contra la fuente oficial antes de afirmarla.

## Detección (orquestador)
- Manifiestos: `composer.json` / `composer.lock`.
- Código: `.php`, `.phtml`, `.inc`; plantillas `.blade.php`, `.twig`, `.tpl`.
- Señales: `index.php`, `.htaccess`, `artisan` (Laravel), `bin/console` (Symfony).
- Stack dominante si la mayoría del código propio es PHP.

## Fase 1 · Discovery

### Manifiestos y dependencias
- `composer.json` (declaradas) y `composer.lock` (resueltas, versión exacta). Sin Composer, las
  dependencias suelen estar copiadas en el repositorio: inventaríalas igual, con su versión
  (cabecera de la librería o `CHANGELOG`).
- Versión de PHP: `require.php` en `composer.json`, `Dockerfile`, `.php-version`, sintaxis usada.
- `require-dev` instalado en producción (sin `--no-dev`) o `vendor/` versionado con paquetes de
  desarrollo: hallazgo.

### Sintaxis para conteos
- Uso: `use Namespace\…;`, `require` / `require_once` / `include` / `include_once` (resuelve
  rutas relativas y variables), llamadas a funciones de extensiones (`mysqli_*`, `curl_*`).
- Comentarios a excluir: `//`, `#`, `/* … */`; en HTML `<!-- -->` (se envía al navegador); en
  Blade `{{-- --}}` y en Twig `{# #}` (no se envían).
- Uso por configuración: proveedores y alias registrados en `config/app.php`, `bundles.php`,
  `services.yaml`, rutas en `routes/*.php` o anotaciones/atributos `#[Route]`.

### Código de terceros y generado
- `vendor/` (Composer), `node_modules/`, librerías copiadas a mano (`mpdf/`, `tcpdf/`, `fpdf/`,
  `phpmailer/`, `lib/`, `libs/`, `plugins/`) con su propia licencia.

### Productos de nombre confundible (CVE)
- Extensión `mysql_*` (eliminada en PHP 7) ≠ `mysqli` ≠ PDO.
- PHPMailer 5.x ≠ 6.x (cambio de API y de CVE).
- `laravel/framework` incluye los componentes `illuminate/*`; Symfony se publica por componentes
  (`symfony/http-kernel`, `symfony/security-http`, …): muchas CVE afectan a un componente;
  verifica cuál está instalado en `composer.lock`.
- Lo que aporta el servidor y no el repositorio (versión de PHP, extensiones, libxml, OpenSSL)
  condiciona varias CVE: decláralo como condición si no se puede confirmar.
- JS/CSS copiados (jQuery, Bootstrap): comprueba el límite inferior del rango de cada CVE.

### Forma concreta de los patrones de defecto
| Patrón (prompt) | Cómo se ve en PHP |
|---|---|
| Vías de autenticación | Cada mecanismo activo es una vía con ficha propia: rutas que registra el framework (`Auth::routes()`, Breeze, Fortify o Jetstream: login, registro, recuperación de contraseña, verificación); guards de Laravel (`web`, `api`, Sanctum, Passport); firewalls de Symfony (`form_login`, `http_basic`, `json_login`, `login_link`, `remember_me`, `switch_user`, `logout`); Basic de Apache (`AuthType Basic` en `.htaccess`); login propio que compara contra la BD sin hash o con `md5`/`sha1`; usuarios hardcodeados; "modo debug" que salta el login; cookies de "recordarme" propias; ausencia de `session_regenerate_id` tras el login |
| Cobertura de autorización | Control por página (`if (!isset($_SESSION[...]))`) no presente en todos los scripts accesibles; scripts AJAX sin verificación; scripts `.php` alcanzables directamente sin pasar por el front controller o el middleware; grupos de rutas sin middleware `auth`; `access_control` de Symfony sin regla por defecto |
| Exposición de fuentes | Archivos `.inc`, `.bak`, `.old`, `.sql`, `config.php~` servibles por el servidor web; `phpinfo()` accesible |
| Estado compartido | Archivos temporales o de salida con nombre fijo; cachés compartidas (APCu, archivos) sin clave por usuario. (Las variables globales viven por petición) |
| TLS deshabilitado | `CURLOPT_SSL_VERIFYPEER => false`, `CURLOPT_SSL_VERIFYHOST => 0`; contextos de stream con `verify_peer => false` |
| XXE | `simplexml_load_string` / `DOMDocument::loadXML` con `LIBXML_NOENT` o carga de entidades habilitada (según versión de libxml) |
| Deserialización | `unserialize()` sobre datos externos (cookies, parámetros) |
| Compilación / evaluación dinámica | `eval`, `assert` con strings, `preg_replace` con `/e` (versiones antiguas), `include($variable)`, `create_function` |
| XSS | `echo $_GET[...]` sin `htmlspecialchars` |
| SQL | Concatenación en `mysqli_query` / `mysql_query`; PDO sin parámetros |
| URL con datos de la petición | `$_SERVER['HTTP_HOST']`, `$_SERVER['SERVER_NAME']` en llamadas salientes o redirecciones |
| Errores expuestos | `display_errors=On`, `error_reporting(E_ALL)` en producción, `die(mysqli_error(...))` |

## Fase 2 · AS-IS

### Manejo de excepciones y compensaciones
- `try / catch` (PHP 5+); supresión con `@`; `or die(...)`; `exit` en medio de un flujo.
- Transacciones: `mysqli_begin_transaction`, `PDO::beginTransaction`; autocommit implícito.
- `catch (Exception $e)` no atrapa `Error` (`TypeError`, `Error` de llamada a método nulo) en
  PHP 7+: solo `Throwable` lo hace. Un `catch` de un tipo concreto (`SoapFault`, excepción del
  cliente HTTP) deja pasar los demás; recórrelo hasta el `catch` que realmente la atrapa.
- Funciones que devuelven `false` o `null` ante error (`mysqli_query`, `file_get_contents`,
  `json_decode`, `curl_exec`) tratadas como éxito; tras un `catch` o un `@` que traga, la
  variable conserva el último valor asignado.
- Parseo de archivos (`fgetcsv`, PhpSpreadsheet): números grandes como `float` en notación
  científica (`1.0E+7`), ceros a la izquierda perdidos, `intval` con desborde, columnas extra o
  faltantes que desplazan índices.
- Escrituras fuera de las acciones de guardar: endpoints AJAX disparados por `onchange`/`blur`,
  rutas `GET` que escriben, eventos y observers de Eloquent (`saving`, `created`), listeners de
  Doctrine; inclúyelas en el inventario.

### Ciclo de vida, hilos y concurrencia
- Modelo por petición: no hay estado en memoria entre peticiones salvo sesión y cachés externas.
- Tareas programadas: `cron` que invoca scripts; colas (Laravel queues).
- Concurrencia: `SELECT MAX(id)+1` o contadores en archivo para generar folios.
- Excepción al modelo por petición: Laravel Octane, Swoole, RoadRunner o FrankenPHP mantienen el
  proceso vivo: los `static`, singletons del contenedor y propiedades de servicios se comparten
  entre peticiones. Conexiones persistentes (`p:` en mysqli, `PDO::ATTR_PERSISTENT`).

### Ruido en el grafo de dependencias
- `include` de layout (header, footer, menú) no es dependencia de dominio.

### Interfaz web (si aplica)
- Dominio de una vista o script: las claves de `$_SESSION` (o `session()` / `SessionInterface`)
  que lee y los controladores o servicios que le pasan datos; una vista que usa datos de otro
  dominio se corta con ese dominio.
- `$_SERVER['HTTP_HOST']`, `REMOTE_ADDR`, `HTTP_X_FORWARDED_FOR`, `HTTPS`, `SERVER_PORT`, cookies
  de sesión (`session.cookie_httponly`, `session.cookie_secure`), `session.gc_maxlifetime`;
  `TrustProxies` (Laravel) o `trusted_proxies` (Symfony).

## Fase 3 · TO-BE

### Conceptos PHP → opciones destino (se comparan en escenarios y ADR abiertos, no por defecto)
| Concepto PHP | Opciones a evaluar |
|---|---|
| Archivo `.php` que mezcla HTML y lógica | Separar: servicio o función con la lógica; vista en SPA o SSR moderno |
| PHP plano en servidor propio | Contenedor con PHP vigente (ECS); reescritura de servicios en otro lenguaje; funciones Lambda |
| `$_SESSION` | Token de un IdP gestionado + estado externo si se necesita |
| `$_POST` / `$_GET` | Cuerpo y parámetros de un endpoint con validación de esquema |
| `header('Location: …')` | Navegación del cliente o redirect del servicio |
| mysqli / PDO a MySQL | RDS/Aurora (relacional) o almacén purpose-built según patrón de acceso |
| Persistencia en archivos | S3 o base de datos según naturaleza del dato |
| Includes de layout | Componentes de layout reutilizables |

### Riesgos típicos al migrar desde PHP legado
- Lógica de negocio incrustada en el HTML: identificarla y extraerla.
- SQL por concatenación: consultas parametrizadas en el destino.
- Falta de tipado: declarar contratos de request/response.
- Autenticación casera: reemplazar por un IdP gestionado; no replicar el esquema.
- Manejo de errores con `die()`/`exit()`: respuestas tipadas.
- Detrás de un balanceador: `$_SERVER['HTTPS']`, `SERVER_PORT` y `HTTP_HOST` cambian salvo que se
  configuren los proxies de confianza; las llamadas del servidor a sí mismo no llevan la cookie
  de afinidad.
- Sesión en cookie (driver `cookie` de Laravel) o campos ocultos grandes: el tamaño puede superar
  los límites de inspección o de tamaño de un WAF; mídelo en la PoC.

### Estado, vías de autenticación y rutas (para los pasos de corte y la contención)
- Estado de sesión según el framework: `$_SESSION` en PHP plano; `session()`, `Session::put/get`
  y `flash` en Laravel; `SessionInterface` y atributos de `Request` en Symfony; `$this->session`
  en CodeIgniter. Por cada clave: qué script o controlador la escribe y cuál la lee. Una vista,
  script, reporte o descarga pertenece al dominio de lo que lee y se corta después de todo lo que
  lo escribe.
- Vías de autenticación, una por cada mecanismo activo (ver la tabla de la Fase 1), incluidos los
  mecanismos que validan o renuevan una sesión ya creada (middleware, cookies de "recordarme",
  refresco de tokens).
- Rutas alternativas al mismo recurso: scripts `.php` accesibles directamente además de la ruta
  del front controller; reescrituras de `.htaccess` o del servidor web; rutas con y sin
  `index.php`; rutas por defecto de los paquetes de autenticación (`/login`, `/logout`,
  `/register`, `/password/reset`) que atienden antes que un script propio.

### Validación
- Toda entrada que se usaba sin validar se valida en el destino.
- Nunca portar credenciales hardcodeadas: Secrets Manager / Parameter Store.
