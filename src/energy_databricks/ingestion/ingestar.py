import time
from datetime import UTC, datetime
from pathlib import Path

import requests

from energy_databricks.ingestion.config import WIDGETS
from energy_databricks.ingestion.landing import guardar_en_landing
from energy_databricks.ingestion.ree_client import pedir_widget, trocear_rango


def ingestar(nombre: str, inicio: datetime, fin: datetime, base: Path, momento: datetime | None = None) -> list[Path]:
    if nombre not in WIDGETS:
        raise ValueError(f"Widget '{nombre}' no existe. Opciones: {list(WIDGETS)}")

    if momento is None:
        momento = datetime.now(UTC)

    cfg = WIDGETS[nombre]

    tramos = trocear_rango(inicio, fin, cfg["max_dias"])

    rutas, fallidos = [], []

    for ini, fi in tramos:
        try:
            datos = pedir_widget(cfg, ini, fi)

            ruta = guardar_en_landing(datos, base, nombre, ini, fi, momento)
            rutas.append(ruta)

            time.sleep(1)
        except requests.RequestException as e:
            fallidos.append((ini, fi, str(e)))
            continue

    if fallidos:
        raise RuntimeError(f"{len(fallidos)} tramos fallidos {fallidos}")

    return rutas
