import time
from datetime import datetime

import pytest
import requests
from fakes import CFG_PRUEBA, RespuestaFalsa

from energy_databricks.ingestion.config import WIDGETS
from energy_databricks.ingestion.ingestar import ingestar

INICIO = datetime(2025, 9, 1)
FIN = datetime(2025, 10, 31, 23, 59)
MOMENTO = datetime(2026, 11, 18, 14, 6, 23)


def test_ingestar_una_peticion_por_tramos(monkeypatch, tmp_path):
    llamadas = []

    def get_falso(url, params, timeout):
        llamadas.append(params)
        return RespuestaFalsa({"included": []})

    monkeypatch.setattr(requests, "get", get_falso)
    monkeypatch.setattr(time, "sleep", lambda segundos: None)

    monkeypatch.setitem(WIDGETS, "prueba", CFG_PRUEBA)
    rutas = ingestar("prueba", INICIO, FIN, tmp_path, MOMENTO)

    assert len(llamadas) == 3
    assert len(rutas) == 3
    assert all(r.exists() for r in rutas)
    assert len(list(tmp_path.rglob("*.json"))) == 3


def test_ingestar_continuar_si_falla_un_tramos_y_avisa_al_final(monkeypatch, tmp_path):
    llamadas = []

    def get_falso(url, params, timeout):
        llamadas.append(params)

        if params["start_date"] == "2025-10-01T00:00":
            return RespuestaFalsa({}, status=503)

        return RespuestaFalsa({"included": []})

    monkeypatch.setattr(requests, "get", get_falso)
    monkeypatch.setattr(time, "sleep", lambda segundos: None)

    monkeypatch.setitem(WIDGETS, "prueba", CFG_PRUEBA)

    with pytest.raises(RuntimeError):
        ingestar("prueba", INICIO, FIN, tmp_path, MOMENTO)

    assert len(llamadas) == 6
    assert len(list(tmp_path.rglob("*.json"))) == 2
    assert sorted(r.name for r in tmp_path.rglob("*.json")) == [
        "prueba_2025-09-01_2025-09-30_T140623.json",
        "prueba_2025-10-31_2025-10-31_T140623.json",
    ]


def test_ingestar_no_se_traga_errores_que_no_son_de_la_API(monkeypatch, tmp_path):
    llamadas = []

    def get_falso(url, params, timeout):
        llamadas.append(params)
        return RespuestaFalsa({"included": []})

    monkeypatch.setattr(requests, "get", get_falso)
    monkeypatch.setattr(time, "sleep", lambda segundos: None)

    monkeypatch.setitem(WIDGETS, "prueba", CFG_PRUEBA)

    ingestar("prueba", INICIO, FIN, tmp_path, MOMENTO)

    with pytest.raises(FileExistsError):
        ingestar("prueba", INICIO, FIN, tmp_path, MOMENTO)

    assert len(llamadas) == 4
