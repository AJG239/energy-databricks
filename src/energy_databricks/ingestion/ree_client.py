from datetime import datetime, timedelta

import requests
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from energy_databricks.ingestion.config import BASE_URL, FORMATO_FECHA, WIDGETS


def trocear_rango(inicio: datetime, fin: datetime, max_dias: int) -> list[tuple[datetime, datetime]]:
    """
    Función que permite sacar las fechas pedidas en rangos de 'max_dias' para poder realizar las peticiones de forma
    más sencilla
    """

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


def construir_params(cfg: dict, inicio: datetime, fin: datetime) -> dict:
    """
    Primera versión de construcción de parámetros para poder enviarlos junto con la petición a la url
    """

    params = {
        "start_date": inicio.strftime(FORMATO_FECHA),
        "end_date": fin.strftime(FORMATO_FECHA),
        "time_trunc": cfg["time_trunc"],
    }

    if cfg["geo"] is not None:
        params.update(cfg["geo"])  # Se incluyen los valores de 'geo' en caso de que existan

    return params


def es_transitorio(exc: Exception) -> bool:
    if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
        return True

    if isinstance(exc, requests.HTTPError):
        if exc.response is None:
            return False

        cod = exc.response.status_code
        return cod == 429 or (500 <= cod <= 599)

    return False


@retry(
    retry=retry_if_exception(
        es_transitorio
    ),  # en caso de que se devuelva un error la función es_transitorio decide si se repite o no
    stop=stop_after_attempt(4),  # se realiza un máximo de 4 intentos
    wait=wait_exponential(multiplier=1, min=1, max=30),  # espera desde 1 segundo hasta 30 como máximo
    reraise=True,  # si se agotan los intentos, lanza el error original
)
def pedir_widget(cfg: dict, inicio: datetime, fin: datetime) -> dict:
    """
    Realizar petición a la url de ree para pedir los datos, en caso de que error
    guardar el error y la razón de este mismo
    """

    url = f"{BASE_URL}{cfg['category']}/{cfg['widget']}"
    params = construir_params(cfg, inicio, fin)

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()

    return resp.json()


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
