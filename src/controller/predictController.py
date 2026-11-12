from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from model.predictModel import PredictedStreet, PredictResponse
from service.predictSrevice import predictStreet

predictRout = APIRouter(prefix="/predict", tags=["Model"])

@predictRout.get("/")
def getStreetPrediction(street_name: str, level: int, hour: int, depth: int) -> PredictResponse:

    if street_name == "":
        raise HTTPException(status_code=400, detail="El nombre de la calle no puede estar vacio")
    if level < 0:
        raise HTTPException(status_code=400, detail="La altura de la calle no puede ser menor a 0")
    if depth < 0:
        raise HTTPException(status_code=400, detail="La profundidad no puede ser menor a 0")
    if hour < 0 or hour > 23:
        raise HTTPException(status_code=400, detail="La hora no puede ser menor a 0 o mayor a 23")

    result = predictStreet(street_name, level, hour, depth)

    if result is None:
        raise HTTPException(status_code=404, detail="Calle no encontrada")
    
    return result