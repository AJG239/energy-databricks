from datetime import datetime

from energy_databricks.ingestion.landing import guardar_en_landing

INICIO = datetime(2025, 9, 1)
FIN = datetime(2025, 9, 30, 23, 59)
MOMENTO = datetime(2026, 11, 17, 12, 51, 0)


def test_guardar_en_la_ruta_esperada(tmp_path):
    ruta = guardar_en_landing({"a": 1}, tmp_path, "demanda", INICIO, FIN, MOMENTO)

    esperada = (
        tmp_path
        / "fuente=ree"
        / "widget=demanda"
        / "ingesta=2026-11-17"
        / "demanda_2025-09-01_2025-09-30_2026-11-17.json"
    )

    assert ruta == esperada
    assert ruta.exists()
