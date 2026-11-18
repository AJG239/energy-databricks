import time
from datetime import datetime

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
