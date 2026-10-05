from pymongo import MongoClient

from model.predictModel import PredictedStreet

dbConection = None

def setDatabase():
   global dbConection

def getValue():
   CONNECTION_STRING = "mongodb://root:secretpassword@mongodb:27017/?authSource=admin"
   client = MongoClient(CONNECTION_STRING)
   dbConection = client['db']
   print(dbConection["streets"].find_one({"_id": "MERCEDES"}))