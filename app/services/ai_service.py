# Lokasi file: app/services/ai_service.py
import os
import json
from dotenv import load_dotenv
from groq import Groq
from app.models.schemas import MealPlanRequest, MealPlanResponse, ScheduleRequest, ScheduleResponse

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = "openai/gpt-oss-20b"

async def generate_meal_plan_from_ai(request: MealPlanRequest) -> MealPlanResponse:
    prompt = f"""
    Anda adalah sistem AI TemanRawat, perencana diet medis dan anggaran yang sangat kaku dan sistematis.
    Berdasarkan input JSON berikut, buatkan rencana makan beserta komposisi gizi dan bahan resepnya.
    
    Input Pengguna:
    {request.model_dump_json(indent=2)}
    
    ATURAN MUTLAK (HARUS DIPATUHI):
    1. Anda HANYA diizinkan membuat MAKSIMAL 5 (lima) rekomendasi menu (objek di dalam array 'meals'). Jangan pernah lebih dari 5.
    2. Jika budget kurang atau bahan dasar tidak masuk akal untuk memenuhi preferensi, JANGAN mencoba membuat menu fiktif. Langsung ubah status menjadi "needs_clarification" dan kosongkan array 'meals'.
    3. Anda tidak boleh berimprovisasi di luar data kondisi pasien dan alergi.
    4. Anda harus selalu mengembalikan JSON deterministik. Jangan mengubah urutan key atau memodifikasi format contoh.
    
    Keluarkan HANYA JSON valid dengan format PERSIS seperti ini (ini adalah format wajib):
    {{
        "status": "draft",
        "meals": [
            {{
                "recipe_name": "Sup Ayam Lunak",
                "description": "Menu sarapan tinggi protein",
                "servings": 1,
                "cooking_time": 30,
                "instructions": "1. Rebus air... 2. Masukkan bahan...",
                "source": "AI TemanRawat",
                "ingredients": [
                    {{"ingredient_name": "Daging Ayam", "quantity": "100 gr"}},
                    {{"ingredient_name": "Wortel", "quantity": "50 gr"}}
                ],
                "nutrition": {{"calories": 150.5, "protein": 15.0, "carbohydrates": 5.0, "fat": 3.5}}
            }}
        ],
        "questions": [],
        "review_notes": []
    }}
    """
    
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You are a deterministic medical diet assistant. You strictly follow rules, limit output to a maximum of 5 meals, and output ONLY valid JSON without any markdown formatting or extra text."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.0, 
        seed=42, 
    )
    
    return MealPlanResponse.model_validate_json(response.choices[0].message.content)

async def generate_schedule_from_ai(request: ScheduleRequest) -> ScheduleResponse:
    prompt = f"""
    Anda adalah sistem AI TemanRawat, perencana agenda harian perawatan.
    Berdasarkan input JSON berikut, buatkan jadwal pengingat (reminders) untuk makan dan minum obat.
    
    Input Pengguna:
    {request.model_dump_json(indent=2)}
    
    Tugas Anda:
    1. Jadwalkan reminders untuk waktu makan (berdasarkan menu_disetujui).
    2. Jadwalkan reminders untuk minum obat (berdasarkan prescriptions). Sambungkan medication_id ke dalam reminder_items.
    3. Jangan buat jadwal di luar ketersediaan caregiver. Masukkan bentrok di `conflicts`.
    
    Keluarkan HANYA JSON valid dengan format persis seperti ini:
    {{
        "status": "draft",
        "input_version": {request.input_version},
        "reminders": [
            {{
                "prescription_id": null,
                "title": "Makan Pagi: Sup Ayam Lunak",
                "schedule_at": "07:00",
                "status": "pending",
                "reminder_items": []
            }},
            {{
                "prescription_id": 1,
                "title": "Minum Paracetamol",
                "schedule_at": "07:30",
                "status": "pending",
                "reminder_items": [
                    {{"medication_id": 1}}
                ]
            }}
        ],
        "conflicts": [],
        "questions": []
    }}
    """
    
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You are a deterministic schedule planning assistant that outputs strictly structured JSON without any markdown or extra text."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.0, 
        seed=42, 
    )
    
    ai_data = json.loads(response.choices[0].message.content)
    ai_data["input_version"] = request.input_version 
    
    return ScheduleResponse(**ai_data)