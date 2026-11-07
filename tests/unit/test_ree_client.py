from datetime import datetime, timedelta
from energy_databricks.ingestion.ree_client import trocear_rango

import pytest

INICIO = datetime(2025, 1, 1)
FIN = datetime(2025, 3, 31, 23, 59)

def test_rango_de_90_dias_de_tres_tramos():
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
    for (_, fin_anterior), (inicio_siguiente, _) in zip(tramos, tramos[1:]):
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

def test_sin_dias_maximos():
    with pytest.raises(ValueError):
        trocear_rango(INICIO, FIN, 0)
