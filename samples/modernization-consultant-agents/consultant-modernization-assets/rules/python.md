# Reglas de origen: Python (Django, Flask, FastAPI, scripts)

Reglas específicas del stack Python. Se inyectan como contexto a los agentes `modernization-assessment-*`.
Los prompts definen QUÉ analizar en cada fase; este archivo define CÓMO se manifiesta en Python.
Complementan (no reemplazan) las instrucciones del prompt. Toda versión, fecha de EOL o CVE
mencionada aquí es orientativa: verifícala contra la fuente oficial antes de afirmarla.

## Detección (orquestador)
- Manifiestos: `requirements*.txt`, `pyproject.toml`, `Pipfile` / `Pipfile.lock`, `setup.py`,
  `setup.cfg`, `poetry.lock`.
- Código: `.py`; señales: `manage.py` (Django), `wsgi.py` / `asgi.py`, `app.py`.
- Stack dominante si la mayoría del código propio es Python.

## Fase 1 · Discovery

### Manifiestos y dependencias
- Lee todos los manifiestos y archivos de bloqueo; distingue rangos (`>=`) de versiones fijadas.
- Versión de Python: `python_requires`, `pyproject.toml`, `runtime.txt`, `Dockerfile`, sintaxis.
- Dependencias de desarrollo o de pruebas instaladas en producción (un único `requirements.txt`
  con `pytest`, `debug-toolbar`): hallazgo.

### Sintaxis para conteos
- Uso: `import x`, `from x import y`, imports relativos (`from . import`), importación dinámica
  (`importlib.import_module`, `__import__`).
- Comentarios a excluir: `#`. Los docstrings no son código ejecutable: exclúyelos de los conteos
  de uso. En plantillas: `{# #}` (Jinja2, Django) y `{% comment %}` no se envían; `<!-- -->` sí.
- Uso por configuración: `INSTALLED_APPS`, `MIDDLEWARE`, `AUTHENTICATION_BACKENDS`,
  `REST_FRAMEWORK`, `urls.py`, blueprints de Flask, `include_router` de FastAPI.

### Código de terceros y generado
- `venv/`, `.venv/`, `env/`, `site-packages/` copiados al repositorio, paquetes vendorizados,
  código generado (protobuf `_pb2.py`, migraciones de Django autogeneradas).

### Productos de nombre confundible (CVE)
- `jwt` ≠ `PyJWT`; `crypto` / `pycrypto` (abandonado) ≠ `pycryptodome`; `PyYAML` (se importa
  como `yaml`).
- Django y Flask publican CVE por rama (p. ej. 3.2.x, 4.2.x): verifica la rama y el límite
  inferior del rango; `Werkzeug`, `Jinja2` y `urllib3` tienen CVE propias aunque lleguen como
  dependencias transitivas.
- Lo que aporta el entorno y no el repositorio (intérprete, OpenSSL, libxml2 del sistema)
  condiciona varias CVE: decláralo como condición si no se puede confirmar.

### Forma concreta de los patrones de defecto
| Patrón (prompt) | Cómo se ve en Python |
|---|---|
| Vías de autenticación | Cada mecanismo activo es una vía con ficha propia: `django.contrib.auth.urls` (login, logout, recuperación de contraseña) y `/admin/`; cada clase en `DEFAULT_AUTHENTICATION_CLASSES` de DRF (`SessionAuthentication`, `BasicAuthentication`, `TokenAuthentication`, JWT); cada entrada de `AUTHENTICATION_BACKENDS`; Flask-Login con cookie `remember`; `HTTPBasic` u `OAuth2PasswordBearer` de FastAPI; backends propios que devuelven el usuario sin verificar la contraseña; `SECRET_KEY` hardcodeada (permite forjar sesiones o tokens); `DEBUG=True` |
| Cobertura de autorización | Rutas Flask/FastAPI sin decorador o dependencia de autorización; vistas Django sin `@login_required` ni `LoginRequiredMixin`; `DEFAULT_PERMISSION_CLASSES` = `AllowAny`; `ALLOWED_HOSTS = ['*']` |
| Estado compartido | Variables globales de módulo mutables con servidores multi-hilo; cachés en proceso sin clave por usuario; archivos temporales con nombre fijo |
| TLS deshabilitado | `requests(..., verify=False)`; `ssl._create_unverified_context`; `urllib3.disable_warnings` |
| XXE | `xml.etree`, `lxml` con `resolve_entities=True`, `xml.dom.minidom` sobre entrada externa (preferible `defusedxml`) |
| Deserialización | `pickle.loads`, `yaml.load` sin `SafeLoader`, `marshal`, `shelve` sobre datos externos |
| Compilación / evaluación dinámica | `eval`, `exec`, plantillas construidas con entrada del usuario (`Template(user_input)`) |
| Comandos | `subprocess(..., shell=True)`, `os.system` con entrada externa |
| SQL | `cursor.execute(f"…{x}")` o `%` sobre el string; `raw()` / `extra()` de Django con concatenación |
| URL con datos de la petición | `request.host`, `request.get_host()`, `X-Forwarded-*` en llamadas salientes |

## Fase 2 · AS-IS

### Manejo de excepciones y compensaciones
- `try / except / else / finally`; `except:` desnudo o `except Exception: pass`.
- Transacciones: `transaction.atomic()` (Django), `session.commit()` / `rollback()` (SQLAlchemy).
- Context managers (`with`) para recursos; `open()` o conexiones sin `with` ni cierre.
- Un `except` de un tipo concreto (`requests.HTTPError`, una excepción del cliente SOAP) deja pasar
  `ConnectionError`, `Timeout` o `KeyError`: recórrelo hasta el `except` que realmente la atrapa.
  Tras un `except` que traga, la variable conserva el último valor asignado o queda sin definir
  (`UnboundLocalError` más adelante).
- Parseo de archivos (`csv`, `openpyxl`, `pandas`): identificadores leídos como `float`
  (notación científica, `NaN` en celdas vacías), ceros a la izquierda perdidos, fechas como
  número de serie, columnas extra que desplazan índices.
- Escrituras fuera de las acciones de guardar: señales (`post_save`, `pre_delete`), `save()`
  sobrescritos, vistas `GET` que escriben, endpoints AJAX disparados por eventos de la interfaz;
  inclúyelas en el inventario.

### Ciclo de vida, hilos y concurrencia
- Efectos al importar un módulo; hooks de arranque (`AppConfig.ready`, `before_first_request`,
  eventos `startup` de FastAPI).
- Tareas: Celery, RQ, `threading.Thread`, `asyncio` tasks, `cron`.
- Workers múltiples (Gunicorn, uWSGI): el estado de módulo no se comparte entre procesos pero sí
  entre hilos del mismo proceso.

### Ruido en el grafo de dependencias
- `logging.getLogger(__name__)` y constantes importadas no son dependencias de dominio.

### Interfaz web (si aplica)
- Dominio de una vista o plantilla: las claves de `request.session` (Django) o `session` (Flask)
  que lee y los datos que le pasa su vista o un context processor; una vista que usa datos de otro
  dominio se corta con ese dominio.
- `request.host`, `request.remote_addr`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SECURE`,
  `CSRF_COOKIE_*`, `SESSION_COOKIE_AGE`; `SECURE_PROXY_SSL_HEADER`, `USE_X_FORWARDED_HOST`,
  `ProxyFix` de Werkzeug.

## Fase 3 · TO-BE

### Conceptos Python → opciones destino (se comparan en escenarios y ADR abiertos, no por defecto)
| Concepto Python | Opciones a evaluar |
|---|---|
| Ruta Flask / vista Django / router FastAPI | Servicio contenedorizado (ECS/EKS) o API Gateway + Lambda |
| Django ORM / SQLAlchemy | RDS/Aurora o almacén purpose-built según patrón de acceso |
| Sesión de Django/Flask | Token de un IdP gestionado + estado externo si se necesita |
| Middleware de autenticación | Validación de tokens OIDC/JWT; authorizer en el borde |
| Modelos Pydantic / serializers DRF | Contratos de request/response explícitos (OpenAPI) |
| Plantillas Django/Jinja2 (SSR) | SPA o SSR moderno |
| `settings.py` / variables de entorno | Secrets Manager, Parameter Store o AppConfig |
| Tareas Celery | Colas gestionadas (SQS) + cómputo de workers, o Step Functions si es un flujo |

### Riesgos típicos al migrar desde Python legado
- Tipado dinámico: documentar los contratos implícitos de cada función.
- Estado global de módulo entre peticiones: externalizarlo.
- Dependencias pesadas y arranque en frío en funciones: empaquetado mínimo.
- `pickle` o `shell=True`: no portar patrones inseguros.
- Migraciones del ORM: mantener relacional o rediseñar el patrón de acceso.
- Detrás de un balanceador: esquema, host y puerto cambian salvo `SECURE_PROXY_SSL_HEADER` o
  `ProxyFix`; las llamadas del servidor a sí mismo no llevan la cookie de afinidad.
- Sesión en cookie (por defecto en Flask; `signed_cookies` en Django): el tamaño puede superar los
  límites de inspección o de tamaño de un WAF; mídelo en la PoC.

### Estado, vías de autenticación y rutas (para los pasos de corte y la contención)
- Estado de sesión según el framework: `request.session` (Django, con su backend: base de datos,
  caché o cookie firmada), `session` de Flask, estado guardado por dependencias de FastAPI. Por
  cada clave: qué vista la escribe y cuál la lee. Una vista, endpoint, reporte o descarga
  pertenece al dominio de lo que lee y se corta después de todo lo que lo escribe.
- Vías de autenticación, una por cada mecanismo activo (ver la tabla de la Fase 1), incluidos los
  mecanismos que validan o renuevan una sesión ya creada (middleware, cookies `remember`,
  refresco de tokens).
- Rutas alternativas al mismo recurso: patrones de `urls.py` que se solapan o se incluyen dos
  veces, `APPEND_SLASH`, blueprints montados en dos prefijos, archivos servidos desde `STATIC_ROOT`
  o `MEDIA_ROOT`, y rutas por defecto de los paquetes (`/admin/`, `/accounts/login/`, `/logout/`)
  que atienden antes que una vista propia.

### Validación
- Validación de entrada equivalente a la de Pydantic/DRF en el destino.
- Credenciales de `settings.py` → Secrets Manager / Parameter Store, nunca en código.
