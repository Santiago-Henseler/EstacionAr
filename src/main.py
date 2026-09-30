from fastapi import FastAPI
from controller.modelController import modelRout

app = FastAPI()

app.include_router(modelRout)

@app.get("/a")
def read_root():
    return {"Hello": "World"}