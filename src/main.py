from fastapi import FastAPI
from controller.modelController import modelRout

app = FastAPI(title="Users API")

app.include_router(modelRout)
