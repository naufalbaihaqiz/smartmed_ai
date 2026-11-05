from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="SmartMed AI Microservice",
    description="API untuk mengklasifikasikan keluhan gejala menjadi kondisi kesehatan.",
    version="1.0"
)

# Struktur data input yang diharapkan dari Node.js
class SymptomInput(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"message": "AI Symptom Classification Service is running."}

@app.post("/predict-symptom")
def predict_symptom(input_data: SymptomInput):
    # TODO: Load model ML dan TF-IDF Vectorizer di sini
    # TODO: Lakukan vektorisasi dan prediksi
    
    # Mock respons untuk sementara (sebelum model siap)
    symptom_text = input_data.text
    print(f"Menerima teks: {symptom_text}")
    
    # Logika sederhana (hanya untuk testing jalur)
    if "pusing" in symptom_text.lower():
        kondisi = "kurang_darah"
        skor = 0.85
    else:
        kondisi = "flu"
        skor = 0.70

    return {
        "condition": kondisi,
        "confidence_score": skor,
        "status": "success"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)