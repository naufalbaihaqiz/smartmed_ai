# Lokasi file: app/routes/schedules.py
from fastapi import APIRouter
from app.models.schemas import ScheduleRequest, ScheduleResponse

router = APIRouter(prefix="/api/schedules", tags=["AI Jadwal"])

@router.post("/generate", response_model=ScheduleResponse)
async def generate_schedule(request: ScheduleRequest):
    # Logika AI Jadwal akan dimasukkan ke sini nanti
    return ScheduleResponse(
        status="draft",
        input_version=request.input_version,
        entries=[],
        conflicts=[],
        questions=[]
    )