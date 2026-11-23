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
    recentReports: int = 0 # usuarios distintos que reportaron "no había lugar" en la ultima hora
    lowAvailability: bool = False # poca disponibilidad segun reportes recientes


class PredictResponse(BaseModel):
    street: PredictedStreet
    neighbors: list["PredictResponse"] = []