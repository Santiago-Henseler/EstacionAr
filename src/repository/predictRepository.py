import os

from pymongo import MongoClient

from model.predictModel import PredictedStreet

dbConection = None

def setDatabase() -> None:
   global dbConection
   CONNECTION_STRING = os.environ.get("MONGO_URL", "mongodb://root:secretpassword@localhost:27017")
   client = MongoClient(CONNECTION_STRING)
   dbConection = client['db']

def getRuledStreet(street: str) -> dict[dict[str]]:
   return dbConection["streets"].find_one({"_id": street})