# Agentic Honey-Pot for Scam Detection 🕵️‍♂️💻

Yeh project **HCL GUVI Hackathon** ke liye banaya gaya hai. Yeh ek AI-powered system hai jo scammers ko detect karta hai, unse baat karta hai, aur intelligence (UPI, Bank details) extract karta hai.

## 📂 Project Structure
- `main.py`: Backend ka heart (FastAPI).
- `schema.py`: Data models aur logic.
- `index.html` & `script.js`: Real-time Dashboard.
- `requirements.txt`: Python libraries list.
- `API.env`: Aapki secret keys.

## 🚀 Setup Instructions (Step-by-Step)

### 1. Python Install Karein
Make sure aapke system mein Python installed hai.

### 2. Dependencies Install Karein
Command prompt (terminal) open karein aur yeh command run karein:
```bash
pip install -r requirements.txt
```

### 3. API Keys Set Karein
`API.env` file mein apni **Gemini API Key** daalein:
```env
GEMINI_API_KEY=AIzaSy...
```
(Agar aapke paas Gemini key hai, toh code mein thoda change karke use kar sakte hain, par default OpenAI set hai).

### 4. Backend Server Start Karein
Terminal mein yeh command likhein:
```bash
uvicorn main:app --reload
```
Ab server `http://127.0.0.1:8000` par chal raha hai.

### 5. Dashboard Open Karein
Bas `index.html` file ko apne browser (Chrome/Edge) mein double-click karke open karein. Aapko dashboard dikh jayega.

## 🧪 Testing (Kaise Check Karein?)

Kyuki yeh API hai, aap Postman ya Curl se request bhej sakte hain backend ko test karne ke liye.

**Endpoint:** `POST http://127.0.0.1:8000/api/honeypot`
**Headers:**
- `Content-Type`: `application/json`
- `x-api-key`: `guvi-hackathon-key`

**Body (JSON Example):**
```json
{
  "sessionId": "scam-101",
  "message": "Sir you won lottery! Send 500rs to upi example@ybl to claim.",
  "platform": "WhatsApp",
  "senderId": "+919876543210"
}
```

Jese hi aap yeh request bhejenge:
1. Dashboard par "Active Scammers" increase hoga.
2. AI reply generate karega.
3. "example@ybl" Intel panel mein show hoga.

## ⚠️ Note
Ethical use ke liye hi banaya gaya hai. Real scammers ke saath direct connect karne se pehle sandboxed environment use karein.
