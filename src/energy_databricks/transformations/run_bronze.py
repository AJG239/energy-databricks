import argparse

from pyspark.sql import SparkSession

from energy_databricks.transformations.bronze import cargar_bronze


def main():
    parser = argparse.ArgumentParser(description="De landing a bronze con AutoLoader")

    parser.add_argument("--landing", default=True)
    parser.add_argument("--checkpoint", default=True)
    parser.add_argument("--tabla", default=True)

    args = parser.parse_args()

    spark = SparkSession.builder.getOrCreate()
    cargar_bronze(spark, args.landing, args.checkpoint, args.tabla)


if __name__ == "__main__":
    main()
