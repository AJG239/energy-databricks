from datetime import UTC, datetime

import pytest

from energy_databricks.ingestion.cli import calcular_rango

HOY = datetime(2026, 11, 23, 12, 42, tzinfo=UTC)


@pytest.mark.parametrize(
    "inicio, fin, esperado",
    [
        ("", "", (datetime(2026, 11, 16, 0, 0), datetime(2026, 11, 22, 23, 59))),
        ("2025-10-01", "2025-10-03", (datetime(2025, 10, 1, 0, 0), datetime(2025, 10, 3, 23, 59))),
        ("", "2025-10-10", (datetime(2025, 10, 4, 0, 0), datetime(2025, 10, 10, 23, 59))),
        ("2025-10-01", "", (datetime(2025, 10, 1, 0, 0), datetime(2026, 11, 22, 23, 59))),
    ],
)
def test_calcular_rango(inicio, fin, esperado):
    assert calcular_rango(inicio, fin, HOY) == esperado
