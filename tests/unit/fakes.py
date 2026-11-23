import requests

CFG_PRUEBA = {
    "category": "cat",
    "widget": "wid",
    "time_trunc": "hour",
    "geo": {"geo_trunc": "electric_system", "geo_limit": "peninsular", "geo_ids": "8741"},
    "max_dias": 30,
}


class RespuestaFalsa:
    def __init__(self, datos, status=200):
        self.datos = datos
        self.status_code = status

    def json(self):
        return self.datos

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"Error: {self.status_code}", response=self)


def error_http(cod: int) -> requests.HTTPError:
    resp = requests.Response()
    resp.status_code = cod
    return requests.HTTPError(response=resp)
