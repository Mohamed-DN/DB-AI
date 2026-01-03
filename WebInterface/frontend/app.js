const API_URL = "http://localhost:8000/api";

// Navigation
function showSection(id) {
    document.querySelectorAll('.page-section').forEach(el => el.classList.remove('active'));
    document.getElementById(id).classList.add('active');

    document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
    event.currentTarget.classList.add('active');

    document.getElementById('page-title').innerText = id.charAt(0).toUpperCase() + id.slice(1);

    // Refresh data based on view
    if (id === 'dashboard') loadStats();
    if (id === 'inventory') loadInventory();
    if (id === 'alerts') loadAlerts();
}

// Stats & Dashboard
async function loadStats() {
    try {
        const inv = await fetch(`${API_URL}/inventory`).then(r => r.json());
        const alerts = await fetch(`${API_URL}/alerts`).then(r => r.json());

        document.getElementById('stat-total-db').innerText = inv.length;

        const criticalCount = alerts.filter(a => a.state === 'CRITICAL' && !a.processed).length;
        document.getElementById('stat-critical').innerText = criticalCount;

        const healthy = inv.length - criticalCount; // Approximation
        document.getElementById('stat-healthy').innerText = healthy;

        logActivity("Dashboard updated.");
    } catch (e) {
        logActivity("Error loading stats.", "error");
    }
}

// Inventory
async function loadInventory() {
    try {
        const data = await fetch(`${API_URL}/inventory`).then(r => r.json());
        const tbody = document.getElementById('inventory-list');
        tbody.innerHTML = '';

        data.forEach(db => {
            const tr = document.createElement('tr');
            const name = db.identity.db_unique_name;
            const engine = db.identity.engine;
            const host = db.identity.host;
            const port = db.configuration.port;
            const env = db.identity.environment;

            tr.innerHTML = `
                <td><span class="status-badge status-up">UP</span></td>
                <td>${name}</td>
                <td><i class="fa-solid fa-database"></i> ${engine}</td>
                <td>${host}</td>
                <td>${port}</td>
                <td>${env}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error(e);
    }
}

// Alerts
async function loadAlerts() {
    try {
        const data = await fetch(`${API_URL}/alerts`).then(r => r.json());
        const container = document.getElementById('alerts-container');
        container.innerHTML = '';

        data.forEach(alert => {
            const el = document.createElement('div');
            el.className = `alert-card ${alert.state === 'CRITICAL' ? 'critical' : 'warning'}`;

            el.innerHTML = `
                <div class="alert-info">
                    <h4>${alert.service}</h4>
                    <p>${alert.message}</p>
                </div>
                <div class="alert-time">${new Date(alert.timestamp).toLocaleTimeString()}</div>
            `;
            container.appendChild(el);
        });
    } catch (e) {
        console.error(e);
    }
}

// Actions
async function triggerAction(action) {
    if (confirm(`Wait for ${action}?`)) {
        logActivity(`Triggering ${action}...`);
        await fetch(`${API_URL}/action/${action}`, { method: 'POST' });
        logActivity(`${action} command sent.`);
        setTimeout(loadStats, 2000);
    }
}

function logActivity(msg, type = 'info') {
    const ul = document.getElementById('refresh-log');
    const li = document.createElement('li');
    li.innerText = `[${new Date().toLocaleTimeString()}] ${msg}`;
    if (type === 'error') li.style.color = 'red';
    ul.prepend(li);
}

// Chat
function handleChatKey(e) {
    if (e.key === 'Enter') sendMessage();
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text) return;

    // Add User Message
    addMessage(text, 'user');
    input.value = '';

    // Call API
    try {
        addMessage("Thinking...", 'ai', true); // Loading state
        const res = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });
        const data = await res.json();

        // Remove loading
        document.querySelector('.loading-msg')?.remove();

        addMessage(data, 'ai');
    } catch (e) {
        addMessage("Connection to Brain failed.", 'ai');
    }
}

function addMessage(text, role, isLoading = false) {
    const container = document.getElementById('chat-history');
    const div = document.createElement('div');
    div.className = `message ${role} ${isLoading ? 'loading-msg' : ''}`;

    const icon = role === 'ai' ? 'fa-robot' : 'fa-user';

    div.innerHTML = `
        <i class="fa-solid ${icon}"></i>
        <div class="bubble">${text}</div>
    `;

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// Init
loadStats();
// Auto Refresh Stats every 10s
setInterval(loadStats, 10000);
