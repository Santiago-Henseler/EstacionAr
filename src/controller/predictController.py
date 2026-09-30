from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from model.predictModel import PredictedStreet
from service.predictSrevice import predictStreet

predictRout = APIRouter(prefix="/predict", tags=["Model"])

@predictRout.get("/")
def getStreetPrediction(street: str, level: int) -> list[PredictedStreet]:

    if street == "":
        raise HTTPException(status_code=400, detail="El nombre de la calle no puede estar vacio")
    if level < 0:
        raise HTTPException(status_code=400, detail="La altura de la calle no puede ser menor a 0")
    
    return predictStreet(street)