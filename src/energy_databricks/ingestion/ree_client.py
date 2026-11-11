import time
from datetime import datetime, timedelta

import requests

from energy_databricks.ingestion.config import BASE_URL, FORMATO_FECHA, WIDGETS

"""
    Función que permite sacar las fechas pedidas en rangos de 'max_dias' para poder realizar las peticiones de forma
    más sencilla
"""


def trocear_rango(inicio: datetime, fin: datetime, max_dias: int) -> list[tuple[datetime, datetime]]:
    if max_dias <= 0:
        raise ValueError("los días deben ser mayores que 0")

    if inicio > fin:
        raise ValueError("inicio posterior a fin")

    tramos = []
    actual = inicio

    while actual <= fin:
        fin_tramo = min(
            actual + timedelta(days=max_dias) - timedelta(minutes=1), fin
        )  # (actual + tam - 1) permite que un valor no salga en dos tramos distintos
        # tramos.append((actual.strftime('%Y-%m-%dT%H:%M'), fin_tramo.strftime('%Y-%m-%dT%H:%M'))) En caso de que se quieran devolver como texto
        tramos.append((actual, fin_tramo))
        actual = fin_tramo + timedelta(minutes=1)

    return tramos


"""
    Primera versión de construcción de parámetros para poder enviarlos junto con la petición a la url
"""


def construir_params(cfg: dict, inicio: datetime, fin: datetime) -> dict:
    params = {
        "start_date": inicio.strftime(FORMATO_FECHA),
        "end_date": fin.strftime(FORMATO_FECHA),
        "time_trunc": cfg["time_trunc"],
    }

    if cfg["geo"] is not None:
        params.update(cfg["geo"])  # Se incluyen los valores de 'geo' en caso de que existan

    return params


"""
    Realizar petición a la url de ree para pedir los datos, en caso de que error
    guardar el error y la razón de este mismo
"""


def pedir_widget(cfg: dict, inicio: datetime, fin: datetime) -> dict:
    url = f"{BASE_URL}{cfg['category']}/{cfg['widget']}"
    params = construir_params(cfg, inicio, fin)

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()

    return resp.json()


"""

"""


def descargar(nombre: str, inicio: datetime, fin: datetime) -> list[dict]:
    if nombre not in WIDGETS:
        raise ValueError(f"Widget '{nombre}' no existe. Opciones: {list(WIDGETS)}")

    cfg = WIDGETS[nombre]

    tramos = trocear_rango(inicio, fin, cfg["max_dias"])
    res = []

    for ini, fi in tramos:
        res.append(pedir_widget(cfg, ini, fi))
        time.sleep(1)

    return res


if __name__ == "__main__":
    for t in trocear_rango(datetime(2025, 1, 1), datetime(2025, 3, 31, 23, 59), 30):
        print(t)

    print(construir_params(WIDGETS["demanda"], datetime(2025, 10, 1), datetime(2025, 10, 1, 23, 59)))

    datos = pedir_widget(WIDGETS["demanda"], datetime(2025, 10, 1), datetime(2025, 10, 1, 23, 59))
    print(len(datos["included"][0]["attributes"]["values"]))

    generacion_mal = {**WIDGETS["generacion"], "time_trunc": "hour"}
    try:
        pedir_widget(generacion_mal, datetime(2025, 10, 1), datetime(2025, 10, 1, 23, 59))
    except requests.HTTPError as e:
        print("Error esperado:", e.response.status_code, e.response.json())

    res = descargar("demanda", datetime(2025, 9, 1), datetime(2025, 10, 31, 23, 59))
    print(len(res))

    res = descargar("precios", datetime(2025, 10, 25), datetime(2025, 10, 27, 23, 59))
    valores = res[0]["included"][0]["attributes"]["values"]
    print(sum(1 for v in valores if v["datetime"].startswith("2025-10-26")))
