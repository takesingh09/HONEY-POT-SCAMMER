// Dashboad and Chat logic for Agentic Honey-Pot
const API_BASE = window.location.origin; // Dynamically use the current origin
const CHAT_URL = `${API_BASE}/`; // Logic is now handled at root '/'

// Store history in GUVI format: [{sender: "scammer", text: "..."}, {sender: "user", text: "..."}]
let chatHistory = [];
const sessionId = "session-" + Math.random().toString(36).substr(2, 9);

async function fetchStats() {
    try {
        const response = await fetch(`${API_BASE}/api/dashboard/stats`);
        if (response.ok) {
            const data = await response.json();
            updateDashboard(data);
        }
    } catch (error) {
        // Silently fail if dashboard stats endpoint isn't ready
    }
}

async function sendScamMessage() {
    const input = document.getElementById("sim-input");
    const msg = input.value.trim();
    if (!msg) return;

    // 1. Show User (Scammer) Message in UI
    addMessageToUI("scammer", msg);
    input.value = "";

    try {
        // 2. Prepare Payload matching main.py logic
        const payload = {
            sessionId: sessionId,
            message: {
                text: msg,
                sender: "scammer",
                timestamp: new Date().toISOString()
            },
            conversationHistory: chatHistory
        };

        // 3. Send to Backend
        const response = await fetch(CHAT_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "x-api-key": "guvi-hackathon-key" // Local testing key
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        // 4. Update Local History (Scammer's turn)
        chatHistory.push({ sender: "scammer", text: msg });

        // 5. Handle Agent Reply (using 'reply' key as per GUVI)
        if (data && data.reply) {
            addMessageToUI("agent", data.reply);
            // Update Local History (Agent's turn - represented as 'user' in history)
            chatHistory.push({ sender: "user", text: data.reply });
        } else if (data && data.status === "error") {
            addMessageToUI("agent", "SYSTEM: " + data.message);
        }

        // 6. Refresh stats to show any extracted intelligence
        fetchStats();

    } catch (e) {
        console.error("Error:", e);
        addMessageToUI("agent", "SYSTEM ERROR: Backend connection failed.");
    }
}

function updateDashboard(data) {
    // 1. Update Counters
    if (document.getElementById("active-sessions")) {
        document.getElementById("active-sessions").innerText = data.active_sessions || 0;
    }

    const intel = data.intelligence || {};
    const upi = intel.upi_ids || [];
    const phone = intel.phone_numbers || [];
    const bank = intel.bank_accounts || [];

    const totalIntel = upi.length + phone.length + bank.length;
    if (document.getElementById("intel-count")) {
        document.getElementById("intel-count").innerText = totalIntel;
    }

    // 2. Update Intelligence List
    const intelList = document.getElementById("intel-list");
    if (!intelList) return;

    intelList.innerHTML = "";

    const addIntel = (items, type) => {
        items.forEach(item => {
            const div = document.createElement("div");
            div.className = "data-item";
            div.innerHTML = `
                <span class="tag ${type}">${type.toUpperCase()}</span>
                <span class="item-title" style="font-family: 'JetBrains Mono'">${item}</span>
            `;
            intelList.appendChild(div);
        });
    };

    addIntel(upi, "upi");
    addIntel(phone, "phone");
    addIntel(bank, "bank");

    if (totalIntel === 0) {
        intelList.innerHTML = `<div class="data-item"><span class="item-subtitle">Scanning for intelligence...</span></div>`;
    }

    // 3. Update Session List
    const sessionList = document.getElementById("session-list");
    if (sessionList) {
        sessionList.innerHTML = `
            <li class="data-item active">
                <span class="item-title">#${sessionId}</span>
                <span class="item-subtitle">Live Interception...</span>
            </li>
        `;
    }
}

function addMessageToUI(role, text) {
    const chatContainer = document.getElementById("chat-container");
    if (!chatContainer) return;

    const div = document.createElement("div");
    div.className = `message ${role}`;

    const roleLabel = role === 'scammer' ? 'SCAMMER (YOU)' : 'AGENT (ASHOK KUMAR)';
    div.innerHTML = `
        <span class="msg-role">${roleLabel}</span>
        ${text}
     `;

    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function startNewSession() {
    chatHistory = [];
    const chatContainer = document.getElementById("chat-container");
    if (chatContainer) chatContainer.innerHTML = "";
    addMessageToUI("agent", "Acha beta... ruko, naya message aaya hai shayad.");
}

// Initial Setup
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("sim-input");
    if (input) {
        input.addEventListener("keypress", (e) => {
            if (e.key === "Enter") sendScamMessage();
        });
    }
    fetchStats();
    setInterval(fetchStats, 5000);
});
