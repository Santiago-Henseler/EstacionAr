from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from service.feedBackService import saveFeedBack 

feedBackRout = APIRouter(prefix="/feedBack", tags=["feedBack"])

@feedBackRout.post("/")
def getStreetPrediction(street_name: str, level: int, confidence: int, proba: float) -> None:

    if street_name == "":
        raise HTTPException(status_code=400, detail="El nombre de la calle no puede estar vacio")
    if level < 0:
        raise HTTPException(status_code=400, detail="La altura de la calle no puede ser menor a 0")
    if confidence > 5 or confidence < 0:
        raise HTTPException(status_code=400, detail="La confianza no puede ser menor a 0 o mayor a 5")
    
    saveFeedBack(street_name, level, confidence, proba)
    
    return None