from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from service.feedBackService import saveFeedBack, updateProbabilities 

feedBackRout = APIRouter(prefix="/feedBack", tags=["feedBack"])

@feedBackRout.post("/")
def getStreetPrediction(street_name: str, level: int, confidence: int, proba: float, hour: int | None = None) -> dict:

    if street_name == "":
        raise HTTPException(status_code=400, detail="El nombre de la calle no puede estar vacio")
    if level < 0:
        raise HTTPException(status_code=400, detail="La altura de la calle no puede ser menor a 0")
    if confidence > 5 or confidence < 0:
        raise HTTPException(status_code=400, detail="La confianza no puede ser menor a 0 o mayor a 5")
    if proba < 0 or proba > 1:
       raise HTTPException(status_code=400, detail="La probabilidad debe estar entre 0 y 1")
    if hour is not None and (hour < 0 or hour > 23):
        raise HTTPException(status_code=400, detail="La hora debe estar entre 0 y 23")

    
    if not saveFeedBack(street_name, level, confidence, proba, hour):
        raise HTTPException(status_code=404, detail="Calle no encontrada")
    
    return {"status": "success", "message": "Feedback registrado correctamente"}

# endpoint temporal para actualizar las probabilidades en base al feedback obtenido
@feedBackRout.post("/update")
def updateModel() -> dict:
    total = updateProbabilities()
    from repository.predictRepository import adjustments
    print("Ajustes actualizados:", adjustments)
    return {"status": "success", "message": "Probabilidades actualizadas", "adjustments": total}