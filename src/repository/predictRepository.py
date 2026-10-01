from pymongo import MongoClient

from model.predictModel import PredictedStreet

dbConection = None

def setDatabase():
   CONNECTION_STRING = "mongodb://root:secretpassword@localhost:27017"
   client = MongoClient(CONNECTION_STRING)
   dbConection = client['db']

def getValue():
   print(dbConection["calle"].find())