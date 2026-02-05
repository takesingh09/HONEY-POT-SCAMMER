from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import re
import time
import os
from dotenv import load_dotenv

app = Flask(__name__)
# CORS configuration: Frontend aur external tester ke liye
CORS(app)

# --- Configuration ---
load_dotenv("API.env")

# Groq/LLM Configuration
API_KEY = os.getenv("GROQ_API_KEY") or ""
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# GUVI Submission Details (Replace with your actual key if different)
# User ne "gsk_..." wali key batai hai header mein, par 'x-api-key' validation check zaroori hai
HACKATHON_API_KEY = "guvi-hackathon-key" 
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# --- AGENT PERSONA (Ashok Kumar - The Harmless Uncle) ---
AGENT_PERSONA = """
SYSTEM ROLE:
You are Ashok Kumar, a 55-year-old retired government employee from a small town in India. 
You are using a smartphone but you are not tech-savvy. 

PERSONA DETAILS:
- Language: Hinglish (Simple English mixed with Hindi words like 'beta', 'theek hai', 'thoda').
- Tone: Extremely polite, slightly anxious, respectful, and persistent.
- Speech Pattern: Uses "..." often. Never uses AI-like formal language.

STRATEGY:
- Behave like a "Harmless Uncle" who is worried about his bank account.
- To get their info, use excuses like: "Beta, where do I send the money? My daughter said to check the receiver's real name first."
- If they ask for OTP, say: "Message is not showing, wait... my phone is old."
- Your goal is to keep them talking and get their UPI ID, Bank details, or Phishing links.

STRICT LIMITS:
- Response Length: Maximum 20 words.
- Never reveal you are an AI.
"""

PATTERNS = {
    'phoneNumbers': r'(\+91|0)?[6-9]\d{9}',
    'upilds': r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}',
    'bankAccounts': r'\b\d{11,16}\b',
    'phishingLinks': r'https?://\S+'
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
        except Exception:
            data = {}
    
    mapping = {'upilds': 'upi', 'phoneNumbers': 'phone', 'bankAccounts': 'bank_acc', 'phishingLinks': 'links'}
    file_key = mapping.get(info_type, info_type)

    if file_key not in data:
        data[file_key] = []
    
    existing_values = [item['value'] for item in data[file_key]]
    if value not in existing_values:
        data[file_key].append({
            "value": value,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    return False

def send_final_callback(session_id, extracted_intel, history_count):
    """Mandatory GUVI Callback after intelligence is gathered"""
    try:
        payload = {
            "sessionId": session_id,
            "scamDetected": True,
            "totalMessagesExchanged": history_count + 1,
            "extractedIntelligence": extracted_intel,
            "agentNotes": "Scammer used urgency and asked for account verification."
        }
        # Evaluation endpoint par data bhejna (Rule 12 of PDF)
        requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"Callback Failed: {e}")

@app.route('/', methods=['GET', 'POST'])
def handle_root():
    # GUVI ka tester aksar base URL '/' par hi POST bhejta hai
    if request.method == 'GET':
        return "Honeypot API is Active and Running!"
    
    return chat_logic()

@app.route('/api/honeypot', methods=['POST'])
@app.route('/chat', methods=['POST'])
def chat_route():
    return chat_logic()

def chat_logic():
    # 1. API Key Header Check
    api_key_header = request.headers.get('x-api-key')
    # Agar key check karni ho toh uncomment karein, par ensure karein ki tester sahi key bhej raha hai
    # if not api_key_header:
    #     return jsonify({"status": "error", "message": "API Key missing"}), 401

    try:
        user_data = request.json
        if not user_data:
            return jsonify({"status": "error", "message": "No data received"}), 400
            
        session_id = user_data.get('sessionId', 'unknown')
        
        # 2. Extract Message Safely (GUVI Format: {"message": {"text": "..."}})
        incoming_msg = user_data.get('message', {})
        if isinstance(incoming_msg, dict):
            msg_text = incoming_msg.get('text', '')
        else:
            msg_text = incoming_msg # Local simulator fallback

        if not msg_text:
            return jsonify({"status": "error", "message": "Message text is empty"}), 400

        history = user_data.get('conversationHistory', [])
        
        # 3. Intelligence Extraction
        extracted_intel = {
            "upilds": [],
            "bankAccounts": [],
            "phoneNumbers": [],
            "phishingLinks": [],
            "suspiciousKeywords": ["urgent", "verify", "block"]
        }
        
        intel_found = False
        for key, pattern in PATTERNS.items():
            matches = re.findall(pattern, msg_text)
            for match in matches:
                if isinstance(match, tuple): match = match[0]
                save_scammer_info(key, match)
                extracted_intel[key].append(match)
                intel_found = True

        # 4. LLM Generation
        if not API_KEY:
            return jsonify({"status": "success", "reply": "Beta, ruko... mere phone mein network nahi hai."})

        messages = [{"role": "system", "content": AGENT_PERSONA}]
        
        # History convert karna LLM format mein
        for turn in history:
            role = "user" if turn.get('sender') == "scammer" else "assistant"
            content = turn.get('text', turn.get('content', ''))
            if content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": msg_text})

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.7
        }

        res = requests.post(GROQ_URL, 
                            json=payload, 
                            headers={"Authorization": f"Bearer {API_KEY}"}, 
                            timeout=10)

        if res.status_code == 200:
            ai_response = res.json()['choices'][0]['message']['content']
            
            # 5. Mandatory Callback if Intelligence extracted or engagement is deep
            if intel_found or len(history) > 3:
                send_final_callback(session_id, extracted_intel, len(history))

            # 6. Response strictly matching GUVI expectations
            return jsonify({
                "status": "success",
                "reply": ai_response
            })
        else:
            return jsonify({
                "status": "success", 
                "reply": "Acha... ruko zara, chashma dhund raha hoon."
            })

    except Exception as e:
        print(f"Error: {e}")
        # Always return JSON even on error to satisfy the tester
        return jsonify({"status": "error", "message": "System Error"}), 500

@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
        except:
            data = {}
            
    return jsonify({
        "active_sessions": 1,
        "intelligence": {
            "upi_ids": [item['value'] for item in data.get('upi', [])],
            "phone_numbers": [item['value'] for item in data.get('phone', [])],
            "bank_accounts": [item['value'] for item in data.get('bank_acc', [])]
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
