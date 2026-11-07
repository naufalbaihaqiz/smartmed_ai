from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import meal_plans, schedules

app = FastAPI(
    title="TemanRawat Backend MVP",
    description="Perantara API AI untuk menyusun draf menu dan jadwal perawatan pasien.",
    version="1.0.0"
)

# CORS Middleware agar request dari Flutter (Web / Android / Desktop) selalu diterima
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrasi Router
app.include_router(meal_plans.router)
app.include_router(schedules.router)

@app.get("/")
def root():
    return {"message": "API TemanRawat berjalan lancar!"}