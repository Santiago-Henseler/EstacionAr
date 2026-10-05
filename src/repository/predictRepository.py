from pymongo import MongoClient

from model.predictModel import PredictedStreet

dbConection = None

def setDatabase():
   global dbConection
   CONNECTION_STRING = "mongodb://root:secretpassword@mongodb:27017/?authSource=admin"
   client = MongoClient(CONNECTION_STRING)
   dbConection = client['db']

def getValue(street: str):
   return dbConection["streets"].find_one({"_id": street})