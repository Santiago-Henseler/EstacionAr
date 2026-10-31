from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

feedBackRoute = APIRouter(prefix="/feedBack", tags=["feedBack"])

# Confidence => indica que tan buena fue la estimación de la respuesta [0:5]
# Proba => indica la probabilidad dada por el modelo
# si la confidence es 5 => la proba se guarda directo
# si la confidence es 2 => si la proba es menor a 0,5 se debe aumentar en 0,2
#                       => si la proba es mayor o igual a 0,5 se debe disminuir en 0,2
# si la confidence es 0 => si la proba es menor a 0,5 se debe aumentar en 0,3
#                       => si la proba es mayor o igual a 0,5 se debe disminuir en 0,3
@feedBackRoute.post("/")
def getStreetPrediction(street_name: str, level: int, confidence: int, proba: int) -> None:

    if street_name == "":
        raise HTTPException(status_code=400, detail="El nombre de la calle no puede estar vacio")
    if level < 0:
        raise HTTPException(status_code=400, detail="La altura de la calle no puede ser menor a 0")
    if confidence > 5 or confidence < 0:
        raise HTTPException(status_code=400, detail="La confianza no puede ser menor a 0 o mayor a 5")
    
    return None