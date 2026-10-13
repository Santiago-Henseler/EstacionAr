import os
import joblib
from pymongo import MongoClient
from model.predictModel import PredictedStreet

dbConection = None
model = None

def setDatabase() -> None:
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
   
def predict() -> list[int]:
   #model.predict()
   pass   
