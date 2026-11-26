from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp


def cargar_bronze(spark: SparkSession, ruta_landing: str, ruta_checkpoint: str, tabla: str) -> None:
    (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", ruta_checkpoint + "/schema")
        .option("cloudFiles.inferColumnTypes", "true")
        .load(ruta_landing)
        .select("*", col("_metadata.file_path").alias("_source_file"), current_timestamp().alias("_ingested_at"))
        .writeStream.option("checkpointLocation", ruta_checkpoint)
        .trigger(availableNow=True)
        .toTable(tabla)
        .awaitTermination()
    )
