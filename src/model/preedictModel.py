from pydantic import BaseModel

class PredictedStreet(BaseModel):
    name: str
    WKT: list[float] = []
    probability: float 