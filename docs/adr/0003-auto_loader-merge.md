# ADR 0003: Auto Loader con MERGE en un job frente a Lakeflow Declarative Pipelines

- Estado: Aceptado
- Fecha: 2026-11-26

## Contexto

Landing contiene los JSON sin modificaciones de la API de REE(Red Eléctrica de España): se añaden ficheros cada día, nunca se modifican y el mismo periodo puede aparecer en varias descargas (como se nombra en el ADR 0002). 
Se deben incluir en una tabla bronze en la que los datos se añadirán tal cual junto con metadatos de carga, y se creará una tabla silver con una fila por indicador y hora, en UTC, sin duplicados, quedándose con la descarga más reciente.

Requisitos:
- Incremental: procesar solo los ficheros nuevos, no releer todo landing cada día.
- Idempotente: volver a procesar no debe duplicar filas en silver.
- Poder realizar tests con pytest, como en el resto del proyecto.
- Ejecutable en Databricks Free Edition (serverless) y desplegable con el bundle.

## Alternativas considerada

1. Lectura completa con `spark.read` en cada ejecución, esto sería lo más sencillo ya que lo lee completo pero el problema es que no es incremental. Ya que al incluir documentos nuevos cada día, relee todos los existentes más los nuevos generando un coste muy elevado que iría incrementando con el paso del tiempo.

2. Auto Loader con `MERGE` como tareas de un job: AutoLoader nos permite recibir ficheros nuevos y recordar cuales ha leído para no volver a procesarlos, esto se debe a dos piezas fundamentales que serían `cloudFiles`, que nos permite la lectura, y los `checkpoints`, los cuales sirven como memoria para que no se relean los archivos antiguos y solo los nuevos. El checkpoint hace que sea incremental y el `MERGE` en silver lo hace idempotente, con control total sobre cada paso. La lectura no se puede probar en local, pero la lógica de transformación va en funciones aparte que sí se prueban con pytest.

3. Lakeflow Declarative Pipelines (antes Delta Live Tables): Se declaran las tablas y Databricks gestiona la actualización incremental, los checkpoints y las dependencias. Esto permite que Databricks lleve el control total a través de una serie de especificaciones impuestas y sin tener que gestionar checkpoints, dependencias ni el estado incremental. Permitiendo una calidad del dato integrada, `AUTO CDC` para los duplicados y un buen seguimiento visual del pipeline. El único problema es que tenemos menos control sobre lo que ocurre por debajo y más difícil de comprobar en local.

## Decisión

Se elige la alternativa 2:

- Landing ${\rightarrow}$ bronze: Auto Loader con `trigger(availableNow=True)`: cada ejecución procesa los ficheros nuevos y termina, como un proceso por lotes.
- Bronze ${\rightarrow}$ silver: `MERGE` por la clave *indicador + timestamp UTC*; si la fila ya existe, se actualiza con la descarga más reciente.
- Ambos pasos son tareas del job del bundle, después de la ingesta.
- La lógica de transformación (aplanar el JSON, pasar a UTC) se realiza mediante diferentes funciones, separadas de la lectura y la escritura, para poder comprobarlas.

## Consecuencias

### Ventajas
- Se entiende y se controla cada paso (Auto Loader, checkpoints, `MERGE`).
- Las transformaciones se prueban con pytest, igual que la ingesta.
- Se mantiene un único estilo en todo el proyecto: funciones del paquete + tareas del job.

### Desventajas
- Más código propio que mantener: checkpoints, `MERGE` y calidad del dato.
- Sin el seguimiento visual ni las *expectations* integradas de Lakeflow; la calidad se implementa a mano (checks y tabla de cuarentena).
- Si en el futuro se migra a Lakeflow, habrá que adaptar bronze y silver (las funciones de transformación sí se podrían reutilizar).



