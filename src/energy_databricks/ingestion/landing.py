import json
from datetime import datetime
from pathlib import Path


def guardar_en_landing(
    datos: dict, base: Path, nombre: str, inicio: datetime, fin: datetime, momento: datetime
) -> Path:
    carpeta = base / "fuente=ree" / f"widget={nombre}" / f"ingesta={momento:%Y-%m-%d}"
    nombre_fichero = f"{nombre}_{inicio:%Y-%m-%d}_{fin:%Y-%m-%d}_T{momento:%H%M%S}.json"

    ruta = carpeta / nombre_fichero
    carpeta.mkdir(parents=True, exist_ok=True)

    with open(ruta, "x", encoding="utf-8") as f:
        f.write(json.dumps(datos, ensure_ascii=False))

    return ruta


if __name__ == "__main__":
    ruta = guardar_en_landing(
        {"prueba": 1},
        Path("scratch"),
        "demanda",
        datetime(2025, 9, 1),
        datetime(2025, 9, 30, 23, 59),
        datetime(2026, 11, 17, 12, 51, 0),
    )
    print(ruta)
