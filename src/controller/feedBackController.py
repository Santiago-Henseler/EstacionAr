from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from service.feedBackService import saveFeedBack, updateProbabilities 

feedBackRout = APIRouter(prefix="/feedBack", tags=["feedBack"])

@feedBackRout.post("/")
def saveStreetFeedBack(street_name: str, level: int, error: int) -> dict:
    if street_name == "":
        raise HTTPException(status_code=400, detail="El nombre de la calle no puede estar vacio")
    if level < 0:
        raise HTTPException(status_code=400, detail="La altura de la calle no puede ser menor a 0")
    if error < -5 or error > 5:
        raise HTTPException(status_code=400, detail="El error no puede ser menor a -5 o mayor a 5")
    
    if not saveFeedBack(street_name, level, error):
        raise HTTPException(status_code=404, detail="Calle no encontrada")
    
    return {"status": "success", "message": "Feedback registrado correctamente"}

# endpoint temporal para actualizar las probabilidades en base al feedback obtenido
@feedBackRout.post("/update")
def updateModel() -> dict:
    total = updateProbabilities()
    return {"status": "success", "message": "Probabilidades actualizadas", "adjustments": total}