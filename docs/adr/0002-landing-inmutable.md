# ADR 0001: Landing inmutable con idempotencia en silver

- Estado: Aceptado
- Fecha: 17/11/2026

## Contexto

El proyecto necesita un lugar para guardar los datos que se descarguen de la API de REE. Ahora mismo la función 'descargar' devuelve los JSON en memoria y, si el proceso termina, se pierden. Este lugar es el Volume 'landing', la capa 'raw' de la arquitectura medallion (ADR 0001), y desde ahí los leerán los pipelines siguientes.

Hay que tener en cuenta que REE revisa los datos después de publicarlos. En la exploración se ha visto que en octubre de 2025 tenían 'last-update' de marzo y mayo de 2026. Por lo que para un mismo día se descargará más de una vez y con valores distintos.

Además, el Auto Loader nos permite procesar ficheros sola un vez, siendo el que lea landing para cargar en bronze, y si un fichero se sobrescribe con el mismo nombre, por defecto no lo vuelve a leer.

## Posibilidades
1. Guardar un fichero por petición con la hora de descarga del nombre: Se descarga cada uno de los archivos en una ruta en concreto con el intervalo de la petición y la fecha y hora de descarga. Se mantienen durante N días, después se borran.

2. Guardar un fichero por día sobrescribiendo el allegado: Se reparten en varias carpetas con la fecha específica los datos establecidos por día, permitiendo un acceso a los datos del día exacto pero perdiendo datos anteriores debido a la sobrescritura cada vez que se realiza la descarga.

3. Saltarse directamente landing y escribir directamente en una tabla Delta desde Python: Se crearían directamente las tablas sin necesidad de guardar los datos en ningún sitio, esto generaría que los cambios que se realicen en la API se aplicarían directamente en la tabla generando una perdida de información debido a que sobrescribiría.

## Decisión

Se escoge la primero alternativa. Cada respuesta de la API se guarda sin modificar como un fichero JSON en el Volume landing:

`landing/fuente=ree/widget=<nombre>/ingesta=<AAAA-MM-DD>/<nombre>_<inicio>_<fin>_T<HHMMSS>.json`

- Landing solo crece nunca se sobrescribe ni se edita un fichero.
- Los duplicados y las revisiones se resuelven en silver con MERGE, por la clave indicador + timestamp UTC.
- Los ficheros de landing con más de N días, ya cargados en bronze, se borran. 

## Ventajas

- Cada petición es un solo fichero: no hace falta abrir un fichero por día para leer un tramo.
- Encaja con Auto Loader: cada descarga es un fichero nuevo y la carga a bronze es incremental.
- El JSON llega crudo y sin variar, así que siempre se puede volver a procesar desde el original.
- Se conservan todas las revisiones de REE, lo que permite medir cuánto y cuándo cambian los datos.

## Desventajas

- Silver queda obligado a resolver los duplicados con MERGE. Si no, se vería el mismo día dos veces.
- Los ficheros se solapan: el mismo día aparece en varias descargas.
- Hay que mantener una tarea de limpieza para landing.