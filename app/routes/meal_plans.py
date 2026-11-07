from fastapi import APIRouter, HTTPException
from app.models.schemas import MealPlanRequest, MealPlanResponse
from app.services.ai_service import generate_meal_plan_from_ai

router = APIRouter(prefix="/api/meal-plans", tags=["AI Menu"])

@router.post("/generate", response_model=MealPlanResponse)
async def generate_meal_plan(request: MealPlanRequest):
    try:
        # Ini kode untuk memanggil AI sungguhan dari ai_service.py
        ai_response = await generate_meal_plan_from_ai(request)
        return ai_response
    except Exception as e:
        # Jika AI gagal memproses
        raise HTTPException(status_code=500, detail=f"AI Menu Error: {str(e)}")