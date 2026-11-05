from datetime import datetime, timedelta

FORMATO_FECHA= '%Y-%m-%dT%H:%M'

PENINSULAR= {
    'geo_trunc': 'electric_system',
    'geo_limit': 'peninsular',
    'geo_ids': '8741',
}

WIDGETS = {
    'precios': {
        'category': 'mercados',
        'widget': 'precios-mercados-tiempo-real',
        'time_trunc': 'hour',
        'geo': PENINSULAR,
        'max_dias': 30,
    },
    'demanda': {
        'category': 'demanda',
        'widget': 'evolucion',
        'time_trunc': 'hour',
        'geo': PENINSULAR,
        'max_dias': 30,
    },
    'generacion': {
        'category': 'generacion',
        'widget': 'estructura-generacion',
        'time_trunc': 'day',
        'geo': PENINSULAR,
        'max_dias': 30,   # provisional: falta probar el límite real con 'day'
    },
}


def trocear_rango(inicio: datetime, fin: datetime, max_dias: int) -> list[tuple[datetime, datetime]]:
    if max_dias <= 0:
        raise ValueError('los días deben ser mayores que 0')
    
    if inicio > fin:
        raise ValueError('inicio posterior a fin')

    tramos = []
    actual = inicio

    while actual <= fin:
        fin_tramo = (min(actual + timedelta(days=max_dias) - timedelta(minutes=1), fin)) # (actual + tam - 1) permite que un valor no salga en dos tramos distintos
        # tramos.append((actual.strftime('%Y-%m-%dT%H:%M'), fin_tramo.strftime('%Y-%m-%dT%H:%M'))) En caso de que se quieran devolver como texto
        tramos.append((actual, fin_tramo))
        actual = fin_tramo + timedelta(minutes=1)

    return tramos

def construir_params(confg: dict, inicio: datetime, fin: datetime) -> dict:
    params = {
        'start_date': inicio.strftime(FORMATO_FECHA), 
        'end_date': fin.strftime(FORMATO_FECHA),
        'time_trunc': confg['time_trunc']
    }

    if confg['geo'] is not None:
        params.update(confg['geo'])

    return params

if __name__ == '__main__':
    for t in trocear_rango(datetime(2025, 1, 1), datetime(2025, 3, 31, 23, 59), 30):
       print(t)

    print(construir_params(WIDGETS['demanda'], datetime(2025, 10, 1), datetime(2025, 10, 1, 23, 59)))