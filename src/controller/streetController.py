from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from service.predictSrevice import getStreets

streetRout = APIRouter(prefix="/streets", tags=["Streets"])

@streetRout.get("/")
def getStreetNames() -> dict[str, list[str]]:
    return getStreets()