# Lokasi file: app/routes/meal_plans.py
from fastapi import APIRouter
from app.models.schemas import MealPlanRequest, MealPlanResponse

router = APIRouter(prefix="/api/meal-plans", tags=["AI Menu"])

@router.post("/generate", response_model=MealPlanResponse)
async def generate_meal_plan(request: MealPlanRequest):
    # Logika AI Menu akan dimasukkan ke sini nanti
    return MealPlanResponse(
        status="draft",
        meals=[],
        questions=["Apakah ada alergi tambahan?"],
        review_notes=["Periksa kembali budget fiktif"]
    )