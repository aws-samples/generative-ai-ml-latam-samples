# Procesamiento de Video con AWS

En la industria de Media y Entertainment, el análisis manual de contenido audiovisual para identificar logos y marcas comerciales es un proceso que tradicionalmente consume muchos recursos y tiempo valioso. Este proyecto presenta una solución innovadora que utiliza servicioss de inteligencia artificial de AWS, principalmente Amazon Rekognition, para automatizar la detección de logos específicos en videos, transformando significativamente la eficiencia operativa de este proceso. 

## Amazon Rekognition y Custom Labels

### Amazon Rekognition
[Amazon Rekognition](https://aws.amazon.com/rekognition/) es un servicio de análisis de imágenes y videos basado en aprendizaje automático que puede identificar objetos, personas, texto, escenas y actividades en imágenes y videos, así como detectar contenido inapropiado.

### Amazon Rekognition Custom Labels
[Amazon Rekognition Custom Labels](https://aws.amazon.com/rekognition/custom-labels-features/) permite entrenar modelos personalizados de visión por computadora para identificar objetos y escenas específicos de su negocio. En este proyecto, se utiliza para detectar logos y marcas comerciales específicas en frames de video.

**Características principales:**
- Entrenamiento de modelos sin experiencia previa en ML
- Detección de objetos personalizados con alta precisión
- Integración nativa con otros servicios AWS
- Escalabilidad automática según demanda

## Estructura del Proyecto

El proyecto está organizado en tres notebooks principales:

1. `TFC Pre procesamiento.ipynb`: Preprocesamiento de videos
2. `TFC Creacion modelo.ipynb`: Creación y entrenamiento del modelo
3. `TFC Procesamiento.ipynb`: Procesamiento de frames

En este mismo orden se debe de ejecutar cada código. 

## Requisitos

### Dependencias Python
- opencv-python-headless
- boto3
- tqdm
- numpy
- pandas

### Configuración AWS
- Cuenta AWS con acceso a S3
- Credenciales AWS configuradas
- Buckets S3 configurados para:
  - Almacenamiento de videos de entrada
  - Almacenamiento de frames procesados

## Configuración

El proyecto utiliza la siguiente estructura de configuración en S3:
- Bucket de entrada: `bucket-video` (para videos)
  - Archivo de video: `video.mp4`
- Bucket de salida: `bucket-frames` (para frames procesados)

## Funcionalidades Principales
- Extracción de frames de video 
- Almacenamiento automático en S3
- Control de calidad de frames
- Nombrado sistemático de frames con timestamp

### Características
- Procesamiento asíncrono
- Barra de progreso para monitoreo
- Manejo de errores robusto
- Limpieza automática de archivos temporales

## Uso

1. Configurar las credenciales de su cuenta AWS
2. Ajustar los parámetros en la sección de configuración
3. Ejecutar los notebooks en orden:
   - Preprocesamiento
   - Procesamiento
   - Creación del modelo

## Parámetros Configurables

### Configuración de Preprocesamiento
```python
CONFIG = {
    # Configuración de AWS S3
    "AWS_REGION": "<REGION>",              # Región de AWS
    "INPUT_BUCKET": "<INPUT_BUCKET>",         # Bucket con el video
    "OUTPUT_BUCKET": "<OUTPUT_BUCKET>",       # Bucket para frames
    "VIDEO_KEY": "video.mp4",              # Nombre del video en S3
    "OUTPUT_FOLDER": "frames/",             # Carpeta destino para frames
    
    # Configuración de procesamiento
    "TEMP_DIR": "/tmp",                     # Directorio temporal
    "FRAME_INTERVAL": 1,                    # Intervalo entre frames (segundos)
    "FRAME_FORMAT": "jpg",                  # Formato de imagen
    "FRAME_QUALITY": 95,                    # Calidad de imagen (1-100)
}
```

### Configuración de Procesamiento con Rekognition
```python
CONFIG = {
    # Configuración AWS
    'SOURCE_BUCKET': '<SOURCE_BUCKET>',    # Nombre del bucket S3
    'SOURCE_PREFIX': 'frames/',             # Carpeta dentro del bucket
    'PROJECT_ARN': '<ARN_PROYECTO>',
    'MODEL_ARN': '<ARN_MODELO>',
    'AWS_REGION': '<REGION>',             # Región AWS
    'MIN_CONFIDENCE': 40,                  # Umbral de confianza para detecciones (%)
    'OUTPUT_JSON': 'resultados_detecciones.json'  # Archivo de salida
}
```

## Costos

### Amazon Rekognition Custom Labels
- **Entrenamiento del modelo**: $1.00 por hora de entrenamiento
- **Inferencia**: $4.00 por hora cuando el modelo está ejecutándose
- **Análisis de imágenes**: $0.001 por imagen analizada (después de las primeras 1M imágenes gratuitas por mes)

### Amazon S3
- **Almacenamiento estándar**: $0.023 por GB por mes
- **Solicitudes PUT/COPY/POST/LIST**: $0.0005 por 1,000 solicitudes
- **Solicitudes GET/SELECT**: $0.0004 por 1,000 solicitudes
- **Transferencia de datos**: Gratuita dentro de la misma región AWS

**Nota**: Los precios pueden variar según la región AWS. Para estimaciones precisas, utilice la [Calculadora de Precios de AWS](https://calculator.aws).

## Manejo de Errores

El sistema incluye manejo de errores para:
- Problemas de conexión con AWS
- Errores en el procesamiento de video
- Fallos en la carga/descarga de archivos

