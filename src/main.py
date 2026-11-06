from fastapi import FastAPI
from controller.predictController import predictRout
from controller.streetController import streetRout
from controller.feedBackController import feedBackRout
from repository.predictRepository import setStreetsDataBase, setModel
from repository.feedBackRepository import setFeedBackDataBase
from sqlalchemy import create_engine
from service.feedBackService import updateProbabilities

setStreetsDataBase()
setModel()
setFeedBackDataBase()
updateProbabilities()

app = FastAPI()

app.include_router(predictRout)
app.include_router(streetRout)
app.include_router(feedBackRout)
