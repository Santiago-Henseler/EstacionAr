from fastapi import FastAPI
from controller.predictController import predictRout
from repository.predictRepository import setDatabase

setDatabase()

app = FastAPI()

app.include_router(predictRout)
