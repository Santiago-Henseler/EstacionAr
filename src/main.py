from fastapi import FastAPI
from controller.predictController import predictRout
from controller.streetController import streetRout
from repository.predictRepository import setDatabase, setModel

setDatabase()
setModel()

app = FastAPI()

app.include_router(predictRout)
app.include_router(streetRout)
