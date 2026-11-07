# Lokasi file: app/models/schemas.py
from pydantic import BaseModel
from typing import List, Optional

# ==========================================
# 1. ENTITAS DATABASE (BASE MODELS)
# ==========================================

class HealthCondition(BaseModel):
    id: Optional[int] = None
    condition_name: str
    name: str
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    age: int
    weight: float
    height: float
    isTherePrescription: bool

class Allergy(BaseModel):
    id: Optional[int] = None
    type: str

class Medication(BaseModel):
    id: Optional[int] = None
    prescription_id: Optional[int] = None
    medicine_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    instruction: Optional[str] = None
    quantity: Optional[int] = 10
    notes: Optional[str] = None
    isAfterEat: bool = False
    dose_type: Optional[str] = "TABLET"

class Prescription(BaseModel):
    id: Optional[int] = None
    prescription_date: str
    notes: Optional[str] = None
    status: str = "active"
    start_at: Optional[str] = "08:00"
    medications: List[Medication] = []

class RecipeIngredient(BaseModel):
    id: Optional[int] = None
    recipe_id: Optional[int] = None
    ingredient_name: str
    quantity: Optional[str] = None

class RecipeNutrition(BaseModel):
    id: Optional[int] = None
    recipe_id: Optional[int] = None
    calories: Optional[float] = 0.0
    protein: Optional[float] = 0.0
    carbohydrates: Optional[float] = 0.0
    fat: Optional[float] = 0.0

class Recipe(BaseModel):
    id: Optional[int] = None
    recipe_name: str
    description: Optional[str] = None
    servings: Optional[int] = 1
    cooking_time: Optional[int] = 30
    instructions: Optional[str] = None
    source: Optional[str] = None
    ingredients: List[RecipeIngredient] = []
    nutrition: Optional[RecipeNutrition] = None

class ReminderItem(BaseModel):
    id: Optional[int] = None
    reminder_id: Optional[int] = None
    medication_id: Optional[int] = None

class Reminder(BaseModel):
    id: Optional[int] = None
    prescription_id: Optional[int] = None
    title: str
    schedule_at: str
    status: Optional[str] = "pending"
    reminder_items: List[ReminderItem] = []


# ==========================================
# 2. INPUT SCHEMAS (REQUEST DARI ANDROID)
# ==========================================

class MealPlanRequest(BaseModel):
    request_id: str
    input_version: int
    health_condition: HealthCondition
    allergies: List[Allergy] = []
    budget: float
    preferensi: List[str] = []

class ScheduleRequest(BaseModel):
    request_id: str
    input_version: int
    menu_disetujui: List[Recipe] = []
    prescriptions: List[Prescription] = []
    rutinitas: dict = {}


# ==========================================
# 3. OUTPUT SCHEMAS (RESPONSE AI KE ANDROID)
# ==========================================

class MealPlanResponse(BaseModel):
    status: str = "draft"  # "draft" atau "needs_clarification"
    meals: List[Recipe] = []
    questions: List[str] = []
    review_notes: List[str] = []

class ScheduleResponse(BaseModel):
    status: str = "draft"
    input_version: int = 1
    reminders: List[Reminder] = []
    conflicts: List[str] = []
    questions: List[str] = []