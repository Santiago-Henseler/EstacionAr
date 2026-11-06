import os
import hashlib
import joblib
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from model.predictModel import PredictedStreet
from zoneinfo import ZoneInfo

dbConection = None
model = None

TZ = ZoneInfo("America/Argentina/Buenos_Aires")
MAX_ESTACIONAMIENTOS = 15
PESO_MAX = 0.7 # del feedback sobre el modelo
K = 5 # con cuantos feedbacks se alcanza la mitad del peso maximo del feedback

adjustments = {}

def horaActual() -> int:
   return datetime.now(TZ).hour

def setAdjustments(newAdjustments: dict) -> None:
   global adjustments
   adjustments = newAdjustments

def setStreetsDataBase() -> None:
   global dbConection
   CONNECTION_STRING = os.environ.get("MONGO_URL", "mongodb://root:secretpassword@localhost:27017")
   client = MongoClient(CONNECTION_STRING)
   dbConection = client['db']

def getRuledStreet(street_name: str) -> dict[dict[str]]:
   return dbConection["streets"].find_one({"_id": street_name})

def getAllStreets() -> dict[str]:
   return dbConection["streets"].distinct("_id")

def setModel() -> None:
   global model
   model = joblib.load("modelo_estacionar.pkl")
   
def predict(street: str, aInit: int, aFin: int, hour: int | None = None) -> float:
   streetHash = int.from_bytes(hashlib.sha256(street.strip().upper().encode("utf-8")).digest()[:4])
   hour = hour if hour is not None else horaActual()
   row = pd.DataFrame([{
      'calle': streetHash,
      'aInicio': aInit,
      'aFin': aFin,
      'hora': hour
   }])

   base = float(model.predict(row)[0]) / MAX_ESTACIONAMIENTOS

   # promedio ponderado entre la base (modelo inicial) y el feedback obtenido
   adj = adjustments.get((street.strip().upper(), aInit, hour))
   if adj is not None:
      avg, n = adj
      w = PESO_MAX * n / (n + K)
      base = (1 - w) * base + w * avg

   return base