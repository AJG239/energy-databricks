import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path

from energy_databricks.ingestion.ingestar import ingestar

MAX_DIAS = 7


def calcular_rango(inicio: str, fin: str, hoy: datetime) -> tuple[datetime, datetime]:

    if fin:
        fin_dt = datetime.strptime(fin, "%Y-%m-%d")
    else:
        fin_dt = hoy.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None) - timedelta(days=1)

    if inicio:
        inicio_dt = datetime.strptime(inicio, "%Y-%m-%d")
    else:
        inicio_dt = fin_dt - timedelta(days=MAX_DIAS - 1)

    return inicio_dt, fin_dt + timedelta(hours=23, minutes=59)


def main():
    parser = argparse.ArgumentParser(description="Ingesta de REE a landing")

    parser.add_argument("--widgets", default="precios,demanda,generacion")
    parser.add_argument("--inicio", default="")
    parser.add_argument("--fin", default="")
    parser.add_argument("--base", required=True)

    args = parser.parse_args()

    inicio, fin = calcular_rango(args.inicio, args.fin, datetime.now(UTC))
    print(f"Ingest de {args.widgets} del {inicio:%Y-%m-%d} al {fin:%Y-%m-%d}")

    errores = []

    for wid in args.widgets.split(","):
        try:
            ruta = ingestar(wid, inicio, fin, Path(args.base))
            print(f"{wid}: {len(ruta)} ficheros guardados")
        except RuntimeError as e:
            errores.append(f"{wid}: {e}")

    if errores:
        raise RuntimeError(f"Ingesta incompleta: {errores}")


if __name__ == "__main__":
    main()
