from fastapi import APIRouter, Depends, status
from auth import get_current_user_id
from model.reportModel import ReportCreate, ReportResponse
from service.reportService import createReport, getUserReports

reportRout = APIRouter(prefix="/reports", tags=["Reports"])


@reportRout.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def saveReport(data: ReportCreate, user_id: int = Depends(get_current_user_id)):
    return createReport(user_id, data)


@reportRout.get("/me", response_model=list[ReportResponse])
def myReports(user_id: int = Depends(get_current_user_id)):
    return getUserReports(user_id)
