FORMATO_FECHA = "%Y-%m-%dT%H:%M"
BASE_URL = "https://apidatos.ree.es/es/datos/"

PENINSULAR = {
    "geo_trunc": "electric_system",
    "geo_limit": "peninsular",
    "geo_ids": "8741",
}

WIDGETS = {
    "precios": {
        "category": "mercados",
        "widget": "precios-mercados-tiempo-real",
        "time_trunc": "hour",
        "geo": PENINSULAR,
        "max_dias": 30,
    },
    "demanda": {
        "category": "demanda",
        "widget": "evolucion",
        "time_trunc": "hour",
        "geo": PENINSULAR,
        "max_dias": 30,
    },
    "generacion": {
        "category": "generacion",
        "widget": "estructura-generacion",
        "time_trunc": "day",
        "geo": PENINSULAR,
        "max_dias": 30,  # provisional: falta probar el límite real con 'day'
    },
}
