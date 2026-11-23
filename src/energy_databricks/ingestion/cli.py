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
    HOY = datetime(2026, 11, 23, 12, 42, tzinfo=UTC)  # "hoy" fijo para probar

    # 1. Sin fechas → ventana por defecto: ayer (22/11) y los 6 días anteriores (desde el 16/11)
    assert calcular_rango("", "", HOY) == (
        datetime(2026, 11, 16, 0, 0),
        datetime(2026, 11, 22, 23, 59),
    )

    # 2. Con las dos fechas → ese rango exacto, con el fin a las 23:59
    assert calcular_rango("2025-10-01", "2025-10-03", HOY) == (
        datetime(2025, 10, 1, 0, 0),
        datetime(2025, 10, 3, 23, 59),
    )

    # 3. Solo fin → los 7 días que acaban en esa fecha
    assert calcular_rango("", "2025-10-10", HOY) == (
        datetime(2025, 10, 4, 0, 0),
        datetime(2025, 10, 10, 23, 59),
    )

    # 4. Solo inicio → desde esa fecha hasta ayer
    assert calcular_rango("2025-10-01", "", HOY) == (
        datetime(2025, 10, 1, 0, 0),
        datetime(2026, 11, 22, 23, 59),
    )

    print("✅ calcular_rango OK")

    main()
