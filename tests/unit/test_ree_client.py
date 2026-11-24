import time
from datetime import datetime, timedelta
from itertools import pairwise

import pytest
import requests
from fakes import CFG_PRUEBA, RespuestaFalsa, error_http

from energy_databricks.ingestion.config import BASE_URL, WIDGETS
from energy_databricks.ingestion.ree_client import (
    construir_params,
    es_transitorio,
    pedir_widget,
    trocear_rango,
)

INICIO = datetime(2025, 1, 1)
FIN = datetime(2025, 3, 31, 23, 59)

"""
    Test de trocear_rango
"""


def test_rango_de_90_dias_da_tres_tramos():
    tramos = trocear_rango(INICIO, FIN, 30)
    assert len(tramos) == 3


def test_inicio_posterior_a_fin_lanza_error():
    with pytest.raises(ValueError):
        trocear_rango(datetime(2025, 2, 1), datetime(2025, 1, 1), 30)


def test_empieza_en_inicio_y_acaba_en_fin():
    tramos = trocear_rango(INICIO, FIN, 30)
    assert tramos[0][0] == INICIO
    assert tramos[-1][-1] == FIN


def test_tramos_consecutivos_sin_huecos_ni_solapados():
    tramos = trocear_rango(INICIO, FIN, 30)
    for (_, fin_anterior), (inicio_siguiente, _) in pairwise(tramos):
        assert inicio_siguiente == fin_anterior + timedelta(minutes=1)


def test_ningun_tramo_dura_30_dias_o_mas():
    tramos = trocear_rango(INICIO, FIN, 30)
    for ini, fi in tramos:
        assert fi - ini < timedelta(days=30)


def test_rango_3_dias_un_tramo():
    tramos = trocear_rango(datetime(2025, 1, 1), datetime(2025, 1, 4, 23, 59), 30)
    assert len(tramos) == 1


def test_mismo_dia_un_tramo():
    tramos = trocear_rango(INICIO, INICIO, 30)
    assert len(tramos) == 1


def test_max_dias_cero_lanza_error():
    with pytest.raises(ValueError):
        trocear_rango(INICIO, FIN, 0)


"""
    Tests de construir_params
"""


def test_formato_fechas():
    params = construir_params(CFG_PRUEBA, INICIO, FIN)

    assert params["start_date"] == "2025-01-01T00:00"
    assert params["end_date"] == "2025-03-31T23:59"


@pytest.mark.parametrize("trunc", ["hour", "day", "month"])
def test_time_trunc_viene_del_cfg(trunc):
    params = construir_params({**CFG_PRUEBA, "time_trunc": trunc}, INICIO, FIN)
    assert params["time_trunc"] == trunc


def test_comprobar_geo_lleno():
    params = construir_params(CFG_PRUEBA, INICIO, FIN)
    assert params["geo_trunc"] == "electric_system"
    assert params["geo_limit"] == "peninsular"
    assert params["geo_ids"] == "8741"


def test_comprobar_ningun_valor_en_geo():
    params = construir_params({**CFG_PRUEBA, "geo": None}, INICIO, FIN)
    for key in ("geo_trunc", "geo_limit", "geo_ids"):
        assert key not in params


def test_no_se_modifica_cfg_original():
    geo_temp = dict(CFG_PRUEBA["geo"])
    construir_params(CFG_PRUEBA, INICIO, FIN)
    assert CFG_PRUEBA["geo"] == geo_temp


@pytest.mark.parametrize("nombre", list(WIDGETS))
def test_widgets_del_catalogo_es_valido(nombre):
    cfg = WIDGETS[nombre]

    if cfg["time_trunc"] == "hour":
        assert cfg["max_dias"] <= 28

    assert cfg["time_trunc"] in {"hour", "day", "month", "year"}
    assert cfg["max_dias"] > 0
    assert cfg["category"] in {"demanda", "mercados", "generacion"}


"""
    Tests de pedir_widget
"""


def test_pedir_widget_llama_a_la_url_correcta_y_devuelve_json(monkeypatch):
    llamadas = []

    def get_falso(url, params, timeout):
        llamadas.append({"url": url, "params": params})
        return RespuestaFalsa({"included": []})

    monkeypatch.setattr(requests, "get", get_falso)

    datos = pedir_widget(CFG_PRUEBA, INICIO, FIN)
    assert datos == {"included": []}
    assert len(llamadas) == 1
    assert llamadas[0]["url"] == f"{BASE_URL}cat/wid"
    assert llamadas[0]["params"]["time_trunc"] == "hour"


def test_pedir_widget_lanzar_error_si_la_api_da_400(monkeypatch):
    def get_falso(url, params, timeout):
        return RespuestaFalsa({}, status=400)

    monkeypatch.setattr(requests, "get", get_falso)

    with pytest.raises(requests.HTTPError):
        pedir_widget(CFG_PRUEBA, INICIO, FIN)


def test_pedir_widget_reintenta_errores(monkeypatch):
    llamadas = []
    esperas = []

    respuestas = iter(
        [
            RespuestaFalsa({}, status=503),
            RespuestaFalsa({}, status=503),
            RespuestaFalsa({}, status=503),
            RespuestaFalsa({"included": []}),
        ]
    )

    def get_falso(url, params, timeout):
        llamadas.append(params)
        return next(respuestas)

    monkeypatch.setattr(requests, "get", get_falso)
    monkeypatch.setattr(time, "sleep", lambda segundos: esperas.append(segundos))

    datos = pedir_widget(CFG_PRUEBA, INICIO, FIN)

    assert len(llamadas) == 4
    assert esperas == [1, 2, 4]
    assert datos == {"included": []}


def test_pedir_widget_no_reintenta_un_400(monkeypatch):
    llamadas = []

    def get_falso(url, params, timeout):
        llamadas.append(params)
        return RespuestaFalsa({}, status=400)

    monkeypatch.setattr(requests, "get", get_falso)
    monkeypatch.setattr(time, "sleep", lambda segundos: None)

    with pytest.raises(requests.HTTPError):
        pedir_widget(CFG_PRUEBA, INICIO, FIN)

    assert len(llamadas) == 1


def test_pedir_widget_se_rinde_tras_4_intentos(monkeypatch):
    llamadas = []
    esperas = []

    def get_falso(url, params, timeout):
        llamadas.append(params)
        return RespuestaFalsa({}, status=503)

    monkeypatch.setattr(requests, "get", get_falso)
    monkeypatch.setattr(time, "sleep", lambda segundos: esperas.append(segundos))

    with pytest.raises(requests.HTTPError):
        pedir_widget(CFG_PRUEBA, INICIO, FIN)

    assert len(llamadas) == 4
    assert esperas == [1, 2, 4]


"""
    Tests de es_transitorio
"""


@pytest.mark.parametrize("codigo, esperado", [(400, False), (404, False), (429, True), (500, True), (503, True)])
def test_es_transitorio_segun_codigo_http(codigo, esperado):
    assert es_transitorio(error_http(codigo)) == esperado


@pytest.mark.parametrize("error", [requests.Timeout(), requests.ConnectionError()])
def test_errores_de_red_son_transitorios(error):
    assert es_transitorio(error) is True


def test_errores_de_red_no_son_transitorios():
    assert es_transitorio(ValueError("cualquier cosa")) is False


def test_http_error_sin_respuesta_no_es_transitorio():
    assert es_transitorio(requests.HTTPError("sin respuesta")) is False
