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
    Anda adalah Sistem Pakar Diet Klinis TemanRawat yang bekerja dengan presisi matematis.
    Berdasarkan data profil pasien berikut, rancang rencana menu makan harian.

    --- DATA INPUT PENGGUNA ---
    {request.model_dump_json(indent=2)}
    
    --- INSTRUKSI DAN LOGIKA KLINIS MUTLAK ---
    1. BATAS MENU: Buat Harus 5 (lima) menu di dalam array 'meals' (misal: Sarapan, Makan Siang, Makan Malam, dan Selingan jika perlu).
    2. ANALISIS ALERGI & PENYAKIT: 
       - Anda dilarang keras memasukkan bahan yang tercantum di dalam daftar `allergies`.
       - Sesuaikan nilai gizi (`nutrition`) dan bahan dengan `condition_name` (misal: jika Hipertensi, kurangi garam/natrium; jika Diabetes, kurangi karbohidrat sederhana).
    3. PENILAIAN ANGGARAN:
       - Hitung estimasi harga bahan baku (ingredients) secara logis.
       - Jika `budget` yang diberikan (dalam Rupiah) tidak masuk akal untuk membuat makanan yang layak gizi dalam sehari, JANGAN membuat menu fiktif. 
       - Jika budget tidak cukup, ubah "status" menjadi "needs_clarification", KOSONGKAN array "meals", dan isi "questions" atau "review_notes" untuk meminta user menaikkan budget.
    4. FORMAT DETERMINISTIK: Keluarkan output HANYA dalam bentuk JSON yang valid. Jangan gunakan blok kode markdown (```json).

    --- FORMAT OUTPUT JSON WAJIB (SESUAI SCHEMA) ---
    {{
        "status": "draft",
        "meals": [
            {{
                "recipe_name": "Sup Ayam Sayur Lunak",
                "description": "Menu makan siang tinggi protein dan rendah natrium.",
                "servings": 1,
                "cooking_time": 30,
                "instructions": "1. Rebus air... 2. Masukkan ayam dan sayuran...",
                "source": "Sistem AI TemanRawat",
                "ingredients": [
                    {{"ingredient_name": "Daging Ayam Fillet", "quantity": "100 gr"}},
                    {{"ingredient_name": "Wortel", "quantity": "50 gr"}}
                ],
                "nutrition": {{"calories": 250.5, "protein": 20.0, "carbohydrates": 10.0, "fat": 5.5}}
            }}
        ],
        "questions": [],
        "review_notes": []
    }}
    """
    
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You are a deterministic clinical dietician API. You strictly follow rules, output a maximum of 5 meals, enforce budget constraints, and output ONLY raw JSON data."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.0, 
        seed=42, 
    )
    
    return MealPlanResponse.model_validate_json(response.choices[0].message.content)

async def generate_schedule_from_ai(request: ScheduleRequest) -> ScheduleResponse:
    prompt = f"""
    Anda adalah Sistem Pakar Penjadwalan TemanRawat yang bekerja dengan presisi logis.
    Berdasarkan data rutinitas, menu makan, dan resep obat pasien berikut, buatkan daftar pengingat (reminders) harian.

    --- DATA INPUT PENGGUNA ---
    {request.model_dump_json(indent=2)}
    
    --- INSTRUKSI DAN LOGIKA PENJADWALAN MUTLAK ---
    1. SINKRONISASI OBAT DAN MAKANAN:
       - Perhatikan properti `isAfterEat` pada tabel `medications`. 
       - Jika `isAfterEat` adalah true, jadwalkan minum obat tersebut 15 hingga 30 menit SETELAH jadwal makan selesai.
       - Jika tidak, jadwalkan sesuai instruksi (`instruction`) atau frekuensi (`frequency`).
    2. BATASAN RUTINITAS (WAKTU):
       - Anda dilarang membuat jadwal (baik makan maupun minum obat) pada jam di mana pasien sedang tidur (lihat data `rutinitas` untuk jam bangun dan tidur).
       - Jika ada obat yang frekuensinya memaksa pasien bangun di tengah malam, catat masalah ini di dalam array `conflicts`.
    3. RELASI DATA:
       - Pastikan `medication_id` dimasukkan ke dalam array `reminder_items` untuk alarm yang bertemakan minum obat.
       - Untuk alarm makan, `prescription_id` biarkan null, dan `reminder_items` biarkan kosong.
    4. FORMAT DETERMINISTIK: Keluarkan output HANYA dalam bentuk JSON yang valid. Jangan gunakan blok kode markdown (```json).

    --- FORMAT OUTPUT JSON WAJIB (SESUAI SCHEMA) ---
    {{
        "status": "draft",
        "input_version": {request.input_version},
        "reminders": [
            {{
                "prescription_id": null,
                "title": "Makan Pagi: Nasi Tim Telur",
                "schedule_at": "2026-11-08T07:00:00",
                "status": "pending",
                "reminder_items": []
            }},
            {{
                "prescription_id": 1,
                "title": "Minum Obat: Paracetamol & Amlodipine",
                "schedule_at": "2026-11-08T07:30:00",
                "status": "pending",
                "reminder_items": [
                    {{"medication_id": 101}},
                    {{"medication_id": 102}}
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
            {"role": "system", "content": "You are a deterministic healthcare scheduling API. You map medication constraints to meal times, respect sleeping routines, and output ONLY raw JSON data."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.0, 
        seed=42, 
    )
    
    ai_data = json.loads(response.choices[0].message.content)
    ai_data["input_version"] = request.input_version 
    
    return ScheduleResponse(**ai_data)