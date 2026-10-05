from pydantic import BaseModel

class ruleModel(BaseModel):
    name: str
    rule: int
    aFin: int
    hInit: int
    hFin: int
    mano: str
    probability: float 