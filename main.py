from fastapi import FastAPI
from app.routes import meal_plans, schedules

app = FastAPI(
    title="TemanRawat Backend MVP",
    description="Perantara API AI untuk menyusun draf menu dan jadwal perawatan pasien.",
    version="1.0.0"
)

# Registrasi Router
app.include_router(meal_plans.router)
app.include_router(schedules.router)

@app.get("/")
def root():
    return {"message": "API TemanRawat berjalan lancar!"}