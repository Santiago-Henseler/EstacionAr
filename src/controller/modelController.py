from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

modelRout = APIRouter(prefix="/model", tags=["Model"])

@modelRout.get("/")
def get():
    return {"Hello": "World"}