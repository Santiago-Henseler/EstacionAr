from fastapi import FastAPI
from controller.predictController import predictRout

app = FastAPI()

app.include_router(predictRout)