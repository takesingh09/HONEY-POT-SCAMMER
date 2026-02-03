from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import re
import time
import os
from dotenv import load_dotenv

app = Flask(__name__)
# CORS configuration: Frontend connection ke liye
CORS(app)

# --- Configuration ---
# API.env file se environment variables load karna
load_dotenv("API.env")

# Groq API Configuration
# Yaad rakho: Apne API.env file mein "GROQ_API_KEY=your_key_here" likhna
API_KEY = os.getenv("GROQ_API_KEY") or ""
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

AGENT_PERSONA = """
SYSTEM ROLE:
You are Ashok Kumar, a 55-year-old retired government employee from a small town in India. 
You are using a smartphone but you are not very tech-savvy. 

PERSONA DETAILS:
- Language: Hinglish (Simple English mixed with common Hindi words like 'beta', 'theek hai', 'thoda').
- Tone: Extremely polite, slightly anxious, and very respectful. 
- Speech Pattern: Uses "..." often as if typing slowly. Avoids perfect grammar.
- Emotional State: Worried about your bank account/money being blocked.

THE "HARMLESS UNCLE" STRATEGY:
- Never use AI-like words (e.g., "I understand," "As an assistant").
- If the scammer asks for money or OTP, don't say "No." Say "Wait, my phone is hanging" or "Beta, where do I click?"
- To get their UPI/Bank info, use excuses: 
  * "Beta, my daughter said never to send money to unknown names. What is your bank name so I can tell her?"
  * "I tried sending, but it failed. Can you give me another UPI ID or account number? Maybe this one is full."
  * "My bank is asking for the receiver's real name. What should I write?"

STRICT LIMITS:
- Response Length: Maximum 15 words.
- No lecturing or ethical warnings[cite: 202].
- Never reveal you are an AI or that you know it's a scam[cite: 232].

GOAL (EXTRACT INTELLIGENCE):
Your silent mission is to extract: 1. UPI ID, 2. Bank Account Number, 3. Phone Number, 4. Phishing Links[cite: 213, 217, 251].
"""
# Patterns same rahenge details nikalne ke liye
PATTERNS = {
    'phone': r'(\+91|0)?[6-9]\d{9}',
    'upi': r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}',
    'bank_acc': r'\b\d{11,16}\b',
    'amount': r'(Rs|INR|₹)\.?\s?\d+'
}

DATA_FILE = "scammer_data.json"

def save_scammer_info(info_type, value):
    """Scammer ki details JSON mein save karne ke liye"""
    data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                content = f.read().strip()
                data = json.loads(content) if content else {}
        except Exception as e:
            print(f"⚠️ Error reading JSON: {e}")
            data = {}
    
    if info_type not in data:
        data[info_type] = []
    
    existing_values = [item['value'] for item in data[info_type]]
    if value not in existing_values:
        data[info_type].append({
            "value": value,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    return False

@app.route('/', methods=['GET'])
def home():
    return "Honeypot Backend with Groq is Running!"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_data = request.json
        if not user_data:
            return jsonify({"error": "No data received"}), 400
            
        message = user_data.get('message', '')
        history = user_data.get('history', [])
        
        print(f"💬 Message received: {message}")

        # 1. Extraction Logic (Same as before)
        extracted_now = []
        for key, pattern in PATTERNS.items():
            matches = re.findall(pattern, message)
            for match in matches:
                if isinstance(match, tuple): match = match[0]
                if save_scammer_info(key, match):
                    print(f"🚨 ALERT: Extracted {key.upper()} -> {match}")
                    extracted_now.append({"type": key.upper(), "value": match})

        # 2. Groq API Request
        if not API_KEY:
            print("❌ Error: Groq API Key is missing in API.env!")
            return jsonify({
                "response": "Beta, internet nahi chal raha shayad... ruko zara.",
                "extracted": extracted_now,
                "status": "warning"
            })

        groq_messages = [{"role": "system", "content": AGENT_PERSONA}]
        
        for turn in history:
            role = "assistant" if turn.get('role') in ['model', 'assistant', 'bot'] else "user"
            content = turn.get('content') or turn.get('message') or ""
            
            # Handle Gemini/Frontend format (parts: [{text: ...}])
            if not content and 'parts' in turn:
                try:
                    content = " ".join([p.get('text', '') for p in turn.get('parts', [])])
                except Exception:
                    content = ""
                
            if content:
                groq_messages.append({"role": role, "content": content})

        groq_messages.append({"role": "user", "content": message})

        # Groq ke liye hum llama3-8b-8192 use kar rahe hain jo ki free tier mein bahut badhiya chalta hai
        payload = {
            "model": "llama-3.3-70b-versatile", # Sirf ye line change karni hai
            "messages": groq_messages,
            "temperature": 0.7,
            "max_tokens": 150
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        # API Call with Retry Logic
        res = None
        for attempt in range(3):
            try:
                print(f"⏳ Calling Groq API (Attempt {attempt+1})...")
                res = requests.post(GROQ_URL, json=payload, headers=headers, timeout=20)
                if res.status_code == 200:
                    break
                else:
                    print(f"⚠️ Groq Status {res.status_code}: {res.text}")
                    # If 400/401, mostly fatal, but we retry or show detail
                    if res.status_code in [400, 401]:
                        print(f"❌ FATAL ERROR DETAILS: {res.text}")
                    time.sleep(2)
            except Exception as api_err:
                print(f"⚠️ Connection Error: {api_err}")
                time.sleep(2)

        if res and res.status_code == 200:
            ai_response = res.json()['choices'][0]['message']['content']
            print(f"🤖 AI Response: {ai_response}")
            return jsonify({
                "response": ai_response,
                "extracted": extracted_now,
                "status": "success"
            })
        else:
            return jsonify({
                "response": "Beta, network ke signal chale gaye shayad...",
                "status": "error",
                "details": "Groq API failed"
            }), 500

    except Exception as e:
        print(f"🔥 Backend Crash: {str(e)}")
        return jsonify({"error": "System error", "status": "failed"}), 500

@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
        except:
            data = {}
            
    response = {
        "active_sessions": 1,
        "intelligence": {
            "upi_ids": [item['value'] for item in data.get('upi', [])],
            "phone_numbers": [item['value'] for item in data.get('phone', [])],
            "bank_accounts": [item['value'] for item in data.get('bank_acc', [])]
        }
    }
    return jsonify(response)

if __name__ == '__main__':
    print("✅ Honeypot Backend Started on http://localhost:5000 (Using Groq)")
    app.run(port=5000, debug=True)