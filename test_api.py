import os
from dotenv import load_dotenv
from groq import Groq

# Memuat .env
load_dotenv()

# Mengambil API Key dari .env
api_key = os.getenv("GROQ_API_KEY")
print(f"Status API Key terbaca: {'Ya' if api_key else 'Tidak (Periksa file .env)'}")

try:
    # Mencoba mengirim pesan ke Groq
    client = Groq(api_key=api_key)
    print("Sedang mengirim pesan ke Groq...")
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "user", "content": "Halo Groq, apakah kamu bisa mendengar saya? Jawab dengan singkat dalam bahasa Indonesia."}
        ]
    )
    print("\n✅ API KEY BEKERJA! Ini balasan dari Groq:")
    print("🤖 Groq:", response.choices[0].message.content)
    
except Exception as e:
    print("\n❌ API KEY GAGAL BEKERJA. Berikut errornya:")
    print(e)