const API_BASE = "http://localhost:5000/api";
const CHAT_URL = "http://localhost:5000/chat";

// Store local history for the session
let chatHistory = [];

async function fetchStats() {
    try {
        const response = await fetch(`${API_BASE}/dashboard/stats`);
        if (response.ok) {
            const data = await response.json();
            updateDashboard(data);
        }
    } catch (error) {
        // Console error suppressed to avoid spamming if backend is off
        // console.error("Error fetching stats:", error);
    }
}

async function sendScamMessage() {
    const input = document.getElementById("sim-input");
    const msg = input.value.trim();
    if (!msg) return;

    // 1. Show User Message Immediately
    addMessageToUI("scammer", msg);
    input.value = "";

    try {
        // 2. Send to Flask Backend
        const response = await fetch(CHAT_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: msg,
                history: chatHistory
            })
        });

        const data = await response.json();

        // 3. Update History
        chatHistory.push({ role: "user", parts: [{ text: msg }] });

        // 4. Show Agent Reply
        if (data && data.response) {
            addMessageToUI("agent", data.response);
            chatHistory.push({ role: "model", parts: [{ text: data.response }] });
        }

        // 5. Force refresh stats to show new extracted intel immediately
        fetchStats();

    } catch (e) {
        console.error("Error sending message:", e);
        addMessageToUI("scammer", "SYSTEM ERROR: Backend not reachable on port 5000.");
    }
}

function updateDashboard(data) {
    // 1. Update Counters
    document.getElementById("active-sessions").innerText = data.active_sessions;

    // Count total intel points
    // Check fields existence to avoid errors
    const upi = data.intelligence.upi_ids || [];
    const phone = data.intelligence.phone_numbers || [];
    const links = data.intelligence.links || [];
    const bank = data.intelligence.bank_accounts || [];

    const totalIntel = upi.length + links.length + phone.length + bank.length;
    document.getElementById("intel-count").innerText = totalIntel;

    // 2. Update Intelligence List
    const intelList = document.getElementById("intel-list");
    intelList.innerHTML = "";

    // Helper to add intel items
    const addIntel = (items, type) => {
        if (!items) return;
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
    addIntel(links, "link");
    addIntel(bank, "bank"); // Added Bank support in UI

    if (totalIntel === 0) {
        intelList.innerHTML = `<div class="data-item"><span class="item-subtitle">Scanning for intelligence...</span></div>`;
    }

    // 3. Update Session List (Right Panel)
    const sessionList = document.getElementById("session-list");
    sessionList.innerHTML = "";

    if (data.recent_logs) {
        data.recent_logs.forEach(log => {
            const li = document.createElement("li");
            li.className = "data-item";
            li.innerHTML = `
                <span class="item-title">#${log.sessionId}</span>
                <span class="item-subtitle">Active Monitoring...</span>
            `;
            sessionList.appendChild(li);
        });
    }
}

function addMessageToUI(role, text) {
    const chatContainer = document.getElementById("chat-container");
    const div = document.createElement("div");

    div.className = `message ${role}`;
    div.innerHTML = `
        <span class="msg-role">${role === 'scammer' ? 'YOU (SCAMMER)' : 'AGENT (RAMESH PRASAD)'}</span>
        ${text}
     `;

    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Add Event Listener for Enter key
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("sim-input");
    if (input) {
        input.addEventListener("keypress", function (event) {
            if (event.key === "Enter") {
                sendScamMessage();
            }
        });
    }
});

// Poll every 3 seconds for stats
setInterval(fetchStats, 3000);
fetchStats();
