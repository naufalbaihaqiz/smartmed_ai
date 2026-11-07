# Lokasi file: app/services/ai_service.py
import os
import json
from datetime import datetime, timedelta
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
    4. FORMAT DETERMINISTIK & BAHASA: Keluarkan output HANYA dalam bentuk JSON yang valid. Key "status", "meals", "questions", dan "review_notes" WAJIB selalu ada di dalam JSON. Semua nilai teks WAJIB menggunakan Bahasa Indonesia baku. Jangan gunakan blok kode markdown (```json).

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
            {"role": "system", "content": "You are a deterministic clinical dietician API. You strictly follow rules, output EXACTLY 3 meals, enforce a STRICT minimum budget of 10000 IDR (reject if lower), strictly output in Indonesian language, and output ONLY raw JSON data containing status, meals, questions, and review_notes."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.0, 
        seed=42, 
    )
    
    ai_data = json.loads(response.choices[0].message.content)
    ai_data.setdefault("status", "draft")
    ai_data.setdefault("meals", [])
    ai_data.setdefault("questions", [])
    ai_data.setdefault("review_notes", [])
    
    return MealPlanResponse(**ai_data)

def _meal_name_from_time(dt: datetime) -> str:
    hour = dt.hour
    if hour < 11:
        return "Waktu Sarapan"
    elif hour < 16:
        return "Waktu Makan Siang"
    else:
        return "Waktu Makan Malam"

def _parse_time_from_str(schedule_str: str) -> datetime:
    try:
        return datetime.fromisoformat(schedule_str.replace("Z", "+00:00"))
    except Exception:
        today = datetime.now().date()
        parts = schedule_str.strip().split(":")
        h = int(parts[0]) if len(parts) > 0 else 8
        m = int(parts[1]) if len(parts) > 1 else 0
        return datetime(today.year, today.month, today.day, h, m)

def post_process_schedules(request: ScheduleRequest, ai_reminders: list) -> list:
    has_prescriptions = any(len(p.medications) > 0 for p in request.prescriptions)
    
    # 1. Kasus Tanpa Resep Dokter:
    # Hanya hasilkan jadwal makan tanpa nama masakan, dan TIDAK BOLEH ada kategori yang sama dalam 1 hari!
    if not has_prescriptions:
        clean_reminders = []
        seen_day_categories = set()
        for rem in ai_reminders:
            dt = _parse_time_from_str(rem.get("schedule_at", "07:00:00"))
            meal_cat = _meal_name_from_time(dt)
            if meal_cat == "Waktu Makan Malam" and "jam_tidur" in request.rutinitas:
                try:
                    parts = str(request.rutinitas["jam_tidur"]).strip().split(":")
                    sh = int(parts[0]) if len(parts) > 0 else 22
                    sm = int(parts[1]) if len(parts) > 1 else 0
                    max_dinner_dt = datetime(dt.year, dt.month, dt.day, sh, sm) - timedelta(hours=2)
                    if dt > max_dinner_dt:
                        dt = max_dinner_dt
                except Exception:
                    pass
            day_key = (dt.date(), meal_cat)
            if day_key in seen_day_categories:
                continue
            seen_day_categories.add(day_key)
            clean_reminders.append({
                "prescription_id": None,
                "title": meal_cat,
                "schedule_at": dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "status": rem.get("status", "pending"),
                "reminder_items": []
            })
        clean_reminders.sort(key=lambda r: _parse_time_from_str(r["schedule_at"]))
        return clean_reminders

    # Kumpulkan kamus informasi obat untuk lookup cepat
    med_info = {}
    for p in request.prescriptions:
        for m in p.medications:
            if m.id is not None:
                med_info[m.id] = m
            med_info[m.medicine_name.lower().strip()] = m

    # 2. Ambil hanya reminder obat dari AI
    raw_med_reminders = []
    for rem in ai_reminders:
        items = rem.get("reminder_items", [])
        title = rem.get("title", "").lower()
        is_med = len(items) > 0 or rem.get("prescription_id") is not None or "minum" in title or "obat" in title
        if is_med:
            raw_med_reminders.append(rem)

    # Ekstrak data obat & status isAfterEat per reminder
    parsed_meds = []
    for rem in raw_med_reminders:
        dt = _parse_time_from_str(rem.get("schedule_at", "08:00:00"))
        items = rem.get("reminder_items", [])
        title = rem.get("title", "")
        
        matched_meds = []
        for it in items:
            m_id = it.get("medication_id")
            if m_id in med_info:
                matched_meds.append(med_info[m_id])
        if not matched_meds:
            for m_key, m_obj in med_info.items():
                if isinstance(m_key, str) and m_key in title.lower():
                    matched_meds.append(m_obj)
        
        is_after_eat = True
        if matched_meds:
            is_after_eat = matched_meds[0].isAfterEat
            
        parsed_meds.append({
            "dt": dt,
            "prescription_id": rem.get("prescription_id") or (request.prescriptions[0].id if request.prescriptions else None),
            "med_objs": matched_meds,
            "is_after_eat": is_after_eat,
            "title": title
        })

    # 3. Kelompokkan per tanggal dan per sesi (Pagi, Siang, Malam).
    # Dalam 1 hari HANYA ada 3 kategori makan (Sarapan, Makan Siang, Makan Malam).
    # Tidak boleh ada kategori makan yang sama dalam 1 hari!
    days_dict = {}
    for pm in parsed_meds:
        d = pm["dt"].date()
        if d not in days_dict:
            days_dict[d] = []
        days_dict[d].append(pm)

    final_reminders = []

    for d, day_meds in days_dict.items():
        # 3 sesi per hari:
        # Pagi: jam < 11 -> Waktu Sarapan
        # Siang: 11 <= jam < 16 -> Waktu Makan Siang
        # Malam: jam >= 16 -> Waktu Makan Malam
        sessions = [
            ("pagi", "Waktu Sarapan", [m for m in day_meds if m["dt"].hour < 11]),
            ("siang", "Waktu Makan Siang", [m for m in day_meds if 11 <= m["dt"].hour < 16]),
            ("malam", "Waktu Makan Malam", [m for m in day_meds if m["dt"].hour >= 16]),
        ]

        for s_id, meal_title, s_meds in sessions:
            if not s_meds:
                continue

            before_eat = [m for m in s_meds if not m["is_after_eat"]]
            after_eat = [m for m in s_meds if m["is_after_eat"]]

            # Tentukan SATU waktu makan tunggal untuk sesi ini
            if before_eat:
                earliest_before = min(m["dt"] for m in before_eat)
                meal_time = earliest_before + timedelta(minutes=5)
            else:
                earliest_after = min(m["dt"] for m in after_eat)
                meal_time = earliest_after - timedelta(minutes=30)

            # Pastikan aturan klinis: Makan malam paling lama 2 jam sebelum jam tidur
            if s_id == "malam" and "jam_tidur" in request.rutinitas:
                try:
                    parts = str(request.rutinitas["jam_tidur"]).strip().split(":")
                    sh = int(parts[0]) if len(parts) > 0 else 22
                    sm = int(parts[1]) if len(parts) > 1 else 0
                    max_dinner_dt = datetime(meal_time.year, meal_time.month, meal_time.day, sh, sm) - timedelta(hours=2)
                    if meal_time > max_dinner_dt:
                        meal_time = max_dinner_dt
                except Exception:
                    pass

            # A. Obat sebelum makan: disinkronkan tepat 5 menit sebelum waktu makan sesi ini
            if before_eat:
                med_time = meal_time - timedelta(minutes=5)
                med_ids = []
                med_names = []
                presc_id = before_eat[0]["prescription_id"]
                for m in before_eat:
                    for obj in m["med_objs"]:
                        if obj.id is not None and obj.id not in med_ids:
                            med_ids.append(obj.id)
                        if obj.medicine_name not in med_names:
                            med_names.append(obj.medicine_name)
                med_str = ", ".join(med_names) if med_names else "Obat Sebelum Makan"
                final_reminders.append({
                    "prescription_id": presc_id,
                    "title": f"Minum Obat: {med_str}",
                    "schedule_at": med_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "status": "pending",
                    "reminder_items": [{"medication_id": mid} for mid in med_ids]
                })

            # B. Tambahkan TEPAT 1 JADWAL MAKAN untuk sesi ini (tidak boleh ada kategori yang sama dalam 1 hari)
            final_reminders.append({
                "prescription_id": None,
                "title": meal_title,
                "schedule_at": meal_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "status": "pending",
                "reminder_items": []
            })

            # C. Obat sesudah makan: disinkronkan tepat 30 menit setelah waktu makan sesi ini
            if after_eat:
                med_time = meal_time + timedelta(minutes=30)
                med_ids = []
                med_names = []
                presc_id = after_eat[0]["prescription_id"]
                for m in after_eat:
                    for obj in m["med_objs"]:
                        if obj.id is not None and obj.id not in med_ids:
                            med_ids.append(obj.id)
                        if obj.medicine_name not in med_names:
                            med_names.append(obj.medicine_name)
                med_str = ", ".join(med_names) if med_names else "Obat Sesudah Makan"
                final_reminders.append({
                    "prescription_id": presc_id,
                    "title": f"Minum Obat: {med_str}",
                    "schedule_at": med_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "status": "pending",
                    "reminder_items": [{"medication_id": mid} for mid in med_ids]
                })

    final_reminders.sort(key=lambda r: _parse_time_from_str(r["schedule_at"]))
    return final_reminders

def _generate_synthetic_reminders(request: ScheduleRequest) -> list:
    today = datetime.now().date()
    wake_str = request.rutinitas.get("jam_bangun", "06:00")
    sleep_str = request.rutinitas.get("jam_tidur", "21:00")
    try:
        wh, wm = [int(x) for x in str(wake_str).split(":")[:2]]
    except Exception:
        wh, wm = 6, 0
    try:
        sh, sm = [int(x) for x in str(sleep_str).split(":")[:2]]
    except Exception:
        sh, sm = 21, 0

    max_dinner_dt = datetime(today.year, today.month, today.day, sh, sm) - timedelta(hours=2)
    b_dt = datetime(today.year, today.month, today.day, min(wh + 1, 9), wm)
    l_dt = datetime(today.year, today.month, today.day, 12, 30)
    d_dt = max_dinner_dt

    has_prescriptions = any(len(p.medications) > 0 for p in request.prescriptions)
    if not has_prescriptions:
        return [
            {"prescription_id": None, "title": "Waktu Sarapan", "schedule_at": b_dt.strftime("%Y-%m-%dT%H:%M:%S"), "status": "pending", "reminder_items": []},
            {"prescription_id": None, "title": "Waktu Makan Siang", "schedule_at": l_dt.strftime("%Y-%m-%dT%H:%M:%S"), "status": "pending", "reminder_items": []},
            {"prescription_id": None, "title": "Waktu Makan Malam", "schedule_at": d_dt.strftime("%Y-%m-%dT%H:%M:%S"), "status": "pending", "reminder_items": []},
        ]

    reminders = []
    for p in request.prescriptions:
        for m in p.medications:
            freq_str = (m.frequency or "1").lower()
            if "3" in freq_str or "tiga" in freq_str:
                target_times = [b_dt, l_dt, d_dt]
            elif "2" in freq_str or "dua" in freq_str:
                target_times = [b_dt, d_dt]
            else:
                target_times = [b_dt]

            for base_time in target_times:
                med_time = base_time + timedelta(minutes=30) if m.isAfterEat else base_time - timedelta(minutes=5)
                reminders.append({
                    "prescription_id": p.id,
                    "title": f"Minum Obat: {m.medicine_name}",
                    "schedule_at": med_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "status": "pending",
                    "reminder_items": [{"medication_id": m.id}] if m.id is not None else []
                })
    return post_process_schedules(request, reminders)

async def generate_schedule_from_ai(request: ScheduleRequest) -> ScheduleResponse:
    prompt = f"""
    Anda adalah Sistem Pakar Penjadwalan TemanRawat yang bekerja dengan presisi logis mutlak dan menggunakan Bahasa Indonesia.
    Berdasarkan data rutinitas, menu makan, dan resep obat pasien berikut, buatkan daftar pengingat (reminders) harian.

    --- DATA INPUT PENGGUNA ---
    {request.model_dump_json(indent=2)}
    
    --- INSTRUKSI DAN LOGIKA PENJADWALAN MUTLAK (WAJIB DIPATUHI TANPA KECUALI) ---
    1. KONDISI ADA RESEP OBAT:
       - AI HANYA AKAN MENGENERATE JADWAL MINUM OBAT. JANGAN buat jadwal makan di output AI (backend akan menambahkannya otomatis).
       - ATURAN INTERVAL WAKTU KONSISTEN ANTARA JAM BANGUN DAN JAM TIDUR:
         Frekuensi obat harian digunakan untuk membagi waktu aktif antara jam bangun tidur dan jam tidur pasien, menghasilkan jarak waktu yang konsisten antar jadwal minum obat:
         * 1x sehari: 1 kali sehari di waktu yang sesuai (pagi saat sarapan, siang, atau malam).
         * 2x sehari: 2 kali sehari berjarak konsisten (pagi sekitar sarapan dan malam sekitar makan malam, misal jeda 12 jam: 07:00 dan 19:00).
         * 3x sehari: 3 kali sehari berjarak konsisten (pagi sekitar sarapan, siang sekitar makan siang, dan malam sekitar makan malam, misal jeda konsisten 6 jam: 07:00, 13:00, dan 19:00).
         * 4x sehari: 4 kali sehari berjarak konsisten (misal jeda konsisten 4 jam: 07:00, 11:00, 15:00, 19:00).
       - Obat dengan status `isAfterEat` SAMA yang diminum di waktu yang sama boleh dijadwalkan pada jam yang sama.
       - Obat dengan status `isAfterEat` BERBEDA (sebelum makan vs setelah makan) DILARANG KERAS dijadwalkan di jam yang sama!
       - Jika ada obat sebelum makan dan obat sesudah makan di sesi yang sama (pagi, siang, atau malam), jadwalnya HARUS berjarak MINIMAL 35 MENIT (contoh: sebelum makan jam 07:00, sesudah makan jam 07:35).
    2. ATURAN MAKAN MALAM (MUTLAK):
       - Waktu makan malam HARUS PALING LAMA (PALING LAMBAT) 2 JAM SEBELUM JAM TIDUR (contoh: jika jam_tidur 21:00, makan malam maksimal jam 19:00; jika jam_tidur 22:00, makan malam maksimal jam 20:00). Dilarang menjadwalkan makan malam kurang dari 2 jam sebelum tidur!
       - DILARANG membuat jadwal pada saat jam tidur pasien!
    4. RELASI DATA & FORMAT:
       - Pastikan `medication_id` dimasukkan ke dalam array `reminder_items` untuk pengingat minum obat.
       - Output HANYA raw JSON valid dengan keys: status, input_version, reminders, conflicts, questions.

    --- FORMAT OUTPUT JSON WAJIB (SESUAI SCHEMA) ---
    {{
        "status": "draft",
        "input_version": {request.input_version},
        "reminders": [
            {{
                "prescription_id": 1,
                "title": "Minum Obat: Omeprazole",
                "schedule_at": "2026-11-08T07:00:00",
                "status": "pending",
                "reminder_items": [
                    {{"medication_id": 101}}
                ]
            }},
            {{
                "prescription_id": 1,
                "title": "Minum Obat: Paracetamol",
                "schedule_at": "2026-11-08T07:35:00",
                "status": "pending",
                "reminder_items": [
                    {{"medication_id": 102}}
                ]
            }}
        ],
        "conflicts": [],
        "questions": []
    }}
    """
    
    raw_reminders = []
    ai_data = {}
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a strict deterministic healthcare scheduling API. "
                        "When prescriptions exist, generate ONLY medication reminders (never meal reminders). "
                        "Medications with the same isAfterEat can share the same time. "
                        "Medications with different isAfterEat MUST NOT be at the same time and MUST have at least 35 minutes gap in the same session. "
                        "When NO prescriptions exist, generate meal reminders without recipe dish names (use 'Waktu Sarapan', 'Waktu Makan Siang', 'Waktu Makan Malam'). "
                        "Respect sleep routines, strictly output in Indonesian language, "
                        "and output ONLY raw JSON data containing status, input_version, reminders, conflicts, and questions."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0, 
            seed=42, 
        )
        ai_data = json.loads(response.choices[0].message.content)
        raw_reminders = ai_data.get("reminders", [])
    except Exception:
        ai_data = {}

    ai_data["input_version"] = request.input_version
    ai_data.setdefault("status", "draft")
    
    # Lakukan deterministic post-processing untuk menjamin kepatuhan 100% pada aturan 35 menit & jadwal makan otomatis
    processed_reminders = post_process_schedules(request, raw_reminders)
    if not processed_reminders:
        processed_reminders = _generate_synthetic_reminders(request)

    ai_data["reminders"] = processed_reminders
    ai_data.setdefault("conflicts", [])
    ai_data.setdefault("questions", [])
    
    return ScheduleResponse(**ai_data)