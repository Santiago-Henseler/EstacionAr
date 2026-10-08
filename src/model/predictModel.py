from pydantic import BaseModel

class PredictedStreet(BaseModel):
    name: str
    probability: float
    level: int # altura
    rule: int # 1: permitido o -1: prohibido
    hInit: int # horario inicio de la regla "rule"
    hFin: int # horario fin de la regla "rule"
    latitudeInit: float
    longitudeInit: float
    latitudeEnd: float
    longitudeEnd: float


class PredictResponse(BaseModel):
    street: PredictedStreet
    neighbors: list[PredictedStreet]