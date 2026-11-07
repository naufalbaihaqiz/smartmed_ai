from fastapi import APIRouter, HTTPException
from app.models.schemas import ScheduleRequest, ScheduleResponse
from app.services.ai_service import generate_schedule_from_ai

router = APIRouter(prefix="/api/schedules", tags=["AI Jadwal"])

@router.post("/generate", response_model=ScheduleResponse)
async def generate_schedule(request: ScheduleRequest):
    try:
        # Ini kode untuk memanggil AI sungguhan dari ai_service.py
        ai_response = await generate_schedule_from_ai(request)
        return ai_response
    except Exception as e:
        # Jika AI gagal memproses atau token habis
        raise HTTPException(status_code=500, detail=f"AI Jadwal Error: {str(e)}")