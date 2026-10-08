from pydantic import BaseModel

class PredictedStreet(BaseModel):
    name: str
    WKT: list[float] = []
    probability: float
    level: int # altura
    rule: int # 1: permitido o -1: prohibido
    hInit: int # horario inicio de la regla "rule"
    hFin: int # horario fin de la regla "rule"
    aInit: int # altura inicial del tramo
    aFin: int # altura final del tramo