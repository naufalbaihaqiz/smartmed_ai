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
    Anda adalah Sistem Pakar Diet Klinis TemanRawat yang bekerja dengan presisi matematis dan menggunakan Bahasa Indonesia.
    Berdasarkan data profil pasien berikut, rancang rencana menu makan harian.

    --- DATA INPUT PENGGUNA ---
    {request.model_dump_json(indent=2)}
    
    --- INSTRUKSI DAN LOGIKA KLINIS MUTLAK ---
    1. BATAS MENU: Buat TEPAT 3 (tiga) menu di dalam array 'meals' (yaitu: Sarapan, Makan Siang, dan Makan Malam). Jangan lebih dan jangan kurang jika budget mencukupi.
    2. ANALISIS ALERGI & PENYAKIT: 
       - Anda dilarang keras memasukkan bahan yang tercantum di dalam daftar `allergies`.
       - Sesuaikan nilai gizi (`nutrition`) dan bahan dengan `condition_name` (misal: jika Hipertensi, kurangi garam/natrium; jika Diabetes, kurangi karbohidrat sederhana).
    3. PENYESUAIAN ANGGARAN (BUDGET):
       - Batas MINIMAL budget harian adalah Rp 10.000.
       - Jika `budget` di bawah Rp 10.000, Anda DILARANG membuat menu. Ubah "status" menjadi "needs_clarification", KOSONGKAN array "meals", dan isi "review_notes" dengan pesan peringatan untuk menaikkan budget menjadi minimal Rp 10.000.
       - Jika `budget` Rp 10.000 atau lebih, Anda WAJIB membuatkan 3 menu (status "draft"). Gunakan bahan lokal super murah (tahu, tempe, telur, bayam) jika budget ngepas di angka belasan ribu.
    4. FORMAT DETERMINISTIK & BAHASA: Keluarkan output HANYA dalam bentuk JSON yang valid. Semua nilai teks (nama resep, deskripsi, bahan, instruksi) WAJIB menggunakan Bahasa Indonesia baku. Jangan gunakan blok kode markdown (```json).

    --- FORMAT OUTPUT JSON WAJIB (SESUAI SCHEMA) ---
    {{
        "status": "draft",
        "meals": [
            {{
                "recipe_name": "Sup Tahu Bayam Bening",
                "description": "Menu sarapan hemat tinggi zat besi dan protein nabati.",
                "servings": 1,
                "cooking_time": 15,
                "instructions": "1. Didihkan air... 2. Masukkan bawang merah dan bawang putih... 3. Tambahkan tahu dan bayam...",
                "source": "Sistem AI TemanRawat",
                "ingredients": [
                    {{"ingredient_name": "Tahu Putih", "quantity": "1 potong"}},
                    {{"ingredient_name": "Bayam", "quantity": "1 ikat kecil"}}
                ],
                "nutrition": {{"calories": 120.0, "protein": 10.0, "carbohydrates": 5.0, "fat": 3.0}}
            }}
        ],
        "questions": [],
        "review_notes": []
    }}
    """
    
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You are a deterministic clinical dietician API. You strictly follow rules, output EXACTLY 3 meals, enforce a STRICT minimum budget of 10000 IDR (reject if lower), strictly output in Indonesian language, and output ONLY raw JSON data."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.0, 
        seed=42, 
    )
    
    return MealPlanResponse.model_validate_json(response.choices[0].message.content)

async def generate_schedule_from_ai(request: ScheduleRequest) -> ScheduleResponse:
    prompt = f"""
    Anda adalah Sistem Pakar Penjadwalan TemanRawat yang bekerja dengan presisi logis dan menggunakan Bahasa Indonesia.
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
    4. FORMAT DETERMINISTIK & BAHASA: Keluarkan output HANYA dalam bentuk JSON yang valid. Semua judul dan catatan WAJIB menggunakan Bahasa Indonesia. Jangan gunakan blok kode markdown (```json).

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
            {"role": "system", "content": "You are a deterministic healthcare scheduling API. You map medication constraints to meal times, respect sleeping routines, strictly output in Indonesian language, and output ONLY raw JSON data."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.0, 
        seed=42, 
    )
    
    ai_data = json.loads(response.choices[0].message.content)
    ai_data["input_version"] = request.input_version 
    
    return ScheduleResponse(**ai_data)