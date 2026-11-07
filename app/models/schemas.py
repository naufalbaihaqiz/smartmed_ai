# Lokasi file: app/models/schemas.py
from pydantic import BaseModel
from typing import List, Optional

# --- INPUT SCHEMAS ---
class MealPlanRequest(BaseModel):
    request_id: str
    input_version: int
    arahan_makan: list[str]
    alergi: list[str]
    preferensi: list[str]
    budget: float
    stok_bahan: list[str]

class ScheduleRequest(BaseModel):
    request_id: str
    input_version: int
    menu_disetujui: list[str]
    aturan_obat: list[dict]
    rutinitas: dict
    ketersediaan_caregiver: dict

# --- OUTPUT SCHEMAS ---
class Meal(BaseModel):
    waktu_makan: str
    recipe_id: str
    servings: int
    alasan: str

class MealPlanResponse(BaseModel):
    status: str 
    meals: List[Meal]
    questions: List[str]
    review_notes: List[str]

class ScheduleEntry(BaseModel):
    category: str
    source_instruction_id: str
    proposed_time: str
    duration_minutes: Optional[int] = None
    needs_confirmation: bool

class ScheduleResponse(BaseModel):
    status: str
    input_version: int
    entries: List[ScheduleEntry]
    conflicts: List[str]
    questions: List[str]