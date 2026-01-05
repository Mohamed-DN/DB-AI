const API_URL = "http://localhost:8000/api";

// Navigation
function showSection(id) {
    document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    event.currentTarget.classList.add('active');

    const titles = {
        'dashboard': 'Dashboard Overview',
        'inventory': 'Database Inventory',
        'alerts': 'System Alerts',
        'chat': 'AI Assistant',
        'mailbox': 'Communications',
        'data': 'Knowledge Graph Explorer',
        'settings': 'Configuration'
    };
    document.getElementById('page-title').innerText = titles[id] || 'Nexi CMDB';

    if (id === 'dashboard') loadStats();
    if (id === 'inventory') loadInventory();
    if (id === 'alerts') loadAlerts();
    if (id === 'mailbox') loadEmails();
    if (id === 'data') loadExplorer('inventory_databases');
    if (id === 'settings') loadSettings();
}

async function loadStats() {
    try {
        const inv = await fetch(`${API_URL}/inventory`).then(r => r.json());
        const alerts = await fetch(`${API_URL}/alerts`).then(r => r.json());
        document.getElementById('stat-total-db').innerText = inv.length;
        document.getElementById('stat-critical').innerText = alerts.filter(a => a.state === 'CRITICAL' && !a.processed).length;
        document.getElementById('stat-healthy').innerText = inv.filter(d => d.state?.status === 'UP').length;
    } catch (e) { console.error(e); }
}

async function loadInventory() {
    try {
        const dbs = await fetch(`${API_URL}/inventory`).then(r => r.json());
        const tbody = document.getElementById('inventory-list');
        tbody.innerHTML = '';

        dbs.forEach(db => {
            const tr = document.createElement('tr');
            const status = db.state?.status || 'UNKNOWN';
            const name = db.identity.db_unique_name;
            const engine = db.identity.engine;
            const host = db.identity.host;
            const port = db.configuration.port;
            const env = db.identity.environment;

            let badgeClass = 'status-down';
            if (status === 'UP') badgeClass = 'status-up';

            tr.innerHTML = `
                <td><span class="status-badge ${badgeClass}">${status}</span></td>
                <td>${name}</td>
                <td><i class="fa-solid fa-database"></i> ${engine}</td>
                <td>${host}</td>
                <td>${port}</td>
                <td>${env}</td>
                <td>
                    <div style="display:flex; gap:5px;">
                        <button class="btn sm" onclick="connectDB('${name}', 'sql')" title="SQL Console"><i class="fa-solid fa-terminal"></i> psql</button>
                        <button class="btn sm" onclick="connectDB('${name}', 'bash')" title="Linux Shell" style="background:#4e5d6c;"><i class="fa-brands fa-linux"></i> bash</button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) { console.error(e); }
}

async function connectDB(name, mode = 'sql') {
    try {
        await fetch(`${API_URL}/action/connect/${name}?mode=${mode}`, { method: 'POST' });
    } catch (e) {
        alert("Impossibile aprire il terminale: " + e);
    }
}

async function loadAlerts() {
    try {
        const alerts = await fetch(`${API_URL}/alerts`).then(r => r.json());
        const container = document.getElementById('alerts-container');
        container.innerHTML = '';
        alerts.forEach(alert => {
            const div = document.createElement('div');
            div.className = `alert-card ${alert.state.toLowerCase()}`;
            div.innerHTML = `
                <div class="alert-info">
                    <h4>${alert.message}</h4>
                    <p>${alert.service} on ${alert.host_name}</p>
                </div>
                <div class="alert-time">${new Date(alert.timestamp).toLocaleTimeString()}</div>
            `;
            container.appendChild(div);
        });
    } catch (e) { console.error(e); }
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value;
    if (!msg) return;

    const history = document.getElementById('chat-history');
    const userDiv = document.createElement('div');
    userDiv.className = 'message user';
    userDiv.innerHTML = `<i class="fa-solid fa-user"></i><div class="bubble">${msg}</div>`;
    history.appendChild(userDiv);

    input.value = '';
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message ai';
    loadingDiv.innerHTML = `<i class="fa-solid fa-robot"></i><div class="bubble">...</div>`;
    history.appendChild(loadingDiv);
    history.scrollTop = history.scrollHeight;

    try {
        const res = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });
        const ans = await res.json();
        loadingDiv.remove();
        const aiDiv = document.createElement('div');
        aiDiv.className = 'message ai';
        aiDiv.innerHTML = `<i class="fa-solid fa-robot"></i><div class="bubble">${ans}</div>`;
        history.appendChild(aiDiv);
        history.scrollTop = history.scrollHeight;
    } catch (e) {
        loadingDiv.innerHTML = `<i class="fa-solid fa-robot"></i><div class="bubble text-danger">Error: ${e}</div>`;
    }
}

function handleChatKey(e) { if (e.key === 'Enter') sendMessage(); }

async function loadSettings() {
    try {
        const config = await fetch(`${API_URL}/config`).then(r => r.json());
        document.getElementById('setting-scout').value = config.scout_interval;
        document.getElementById('setting-check').value = config.check_interval;
    } catch (e) { console.error(e); }
}

async function saveSettings() {
    const scout = document.getElementById('setting-scout').value;
    const check = document.getElementById('setting-check').value;
    try {
        await fetch(`${API_URL}/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scout_interval: parseInt(scout), check_interval: parseInt(check) })
        });
        alert("✅ Configurazione Salvata!");
    } catch (e) { alert("❌ Errore nel salvataggio!"); }
}

async function triggerAction(action) {
    if (confirm(`Eseguire ${action}?`)) {
        try {
            await fetch(`${API_URL}/action/${action}`, { method: 'POST' });
            setTimeout(loadStats, 2000);
            alert(`✅ ${action} eseguito!`);
        } catch (e) { alert(`❌ Errore durante ${action}: ${e.message}`); }
    }
}

async function loadEmails() {
    try {
        const files = await fetch(`${API_URL}/emails`).then(r => r.json());
        const list = document.getElementById('email-list');
        list.innerHTML = '';
        if (files.length === 0) list.innerHTML = '<li style="text-align:center; padding:1rem;">No emails found</li>';
        files.forEach(f => {
            const li = document.createElement('li');
            li.innerText = f.replace('email_', '').replace('.html', '').replace(/_/g, ' ');
            li.onclick = () => viewEmail(f, li);
            list.appendChild(li);
        });
    } catch (e) { console.error(e); }
}

async function viewEmail(filename, el) {
    document.querySelectorAll('.email-list li').forEach(l => l.classList.remove('active'));
    if (el) el.classList.add('active');
    try {
        const res = await fetch(`${API_URL}/emails/content?filename=${filename}`).then(r => r.json());
        const iframe = document.getElementById('email-preview');
        iframe.contentWindow.document.open();
        iframe.contentWindow.document.write(res.content);
        iframe.contentWindow.document.close();
    } catch (e) { alert("Error loading email"); }
}

// --- EXPLORER ENGINE (Master/Detail) ---
let explorerItems = [];
let currentExplorerItem = null;
let transform = { x: 50, y: 50, scale: 1 };
let ctx = null, nodes = [], edges = [], isDragging = false, startPos = { x: 0, y: 0 };

async function loadExplorer(collection) {
    const list = document.getElementById('explorer-list');
    list.innerHTML = '<div style="padding:1rem; text-align:center; color:#888;">Loading...</div>';
    try {
        const data = await fetch(`${API_URL}/raw/${collection}`).then(r => r.json());
        explorerItems = data;
        list.innerHTML = '';
        if (data.length === 0) { list.innerHTML = '<div style="padding:1rem;">No items found.</div>'; return; }
        data.forEach((item, index) => {
            const div = document.createElement('div');
            div.className = 'explorer-list-item';
            let title = "Item " + index;
            let sub = item._id || "";
            if (item.identity) {
                title = item.identity.db_unique_name || item.identity.db_name;
                sub = `${item.identity.host}:${item.configuration?.port || '?'}`;
            } else if (item.service) { title = item.service; sub = item.message; }
            div.innerHTML = `<h4>${title}</h4><p>${sub}</p>`;
            div.onclick = () => selectExplorerItem(index, div);
            list.appendChild(div);
        });
    } catch (e) { list.innerHTML = `<div style="padding:1rem; color:var(--danger)">Error: ${e}</div>`; }
}

function selectExplorerItem(index, el) {
    document.querySelectorAll('.explorer-list-item').forEach(d => d.classList.remove('active'));
    if (el) el.classList.add('active');
    currentExplorerItem = explorerItems[index];
    document.getElementById('detail-empty').style.display = 'none';
    const content = document.getElementById('detail-content');
    content.style.display = 'flex';

    const item = currentExplorerItem;
    let title = "Item";
    if (item.identity) title = item.identity.db_unique_name;
    else if (item.service) title = item.service;

    document.getElementById('item-title').innerText = title;
    document.getElementById('item-meta').innerText = "ID: " + (item._id || "N/A");

    const jsonViewer = document.getElementById('json-viewer');
    jsonViewer.innerHTML = '';
    jsonViewer.appendChild(createJsonTree(item));

    resetGraphZoom();
    if (document.getElementById('tab-graph').classList.contains('active')) {
        setTimeout(() => renderGraph(item), 100);
    }
}

function switchExplorerTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    const btns = document.querySelectorAll('.tab-btn');
    if (tab === 'json') btns[0].classList.add('active');
    if (tab === 'graph') btns[1].classList.add('active');
    document.getElementById('tab-' + tab).classList.add('active');
    if (tab === 'graph' && currentExplorerItem) { setTimeout(() => renderGraph(currentExplorerItem), 50); }
}

function createJsonTree(data) {
    if (data === null) return createSpan('null', 'json-null');
    if (typeof data === 'boolean') return createSpan(data, 'json-boolean');
    if (typeof data === 'number') return createSpan(data, 'json-number');
    if (typeof data === 'string') return createSpan(`"${data}"`, 'json-string');
    if (Array.isArray(data) || typeof data === 'object') {
        const isArray = Array.isArray(data);
        const container = document.createElement('div');
        container.className = isArray ? 'json-arr' : 'json-obj';
        const open = document.createElement('span');
        open.innerHTML = isArray ? '[' : '{';
        open.className = 'json-bracket';
        const keys = Object.keys(data);
        if (keys.length > 0) {
            const toggle = document.createElement('span');
            toggle.className = 'json-toggle';
            toggle.innerText = '▼';
            toggle.onclick = (e) => {
                e.stopPropagation();
                toggle.classList.toggle('collapsed');
                container.querySelector('.json-children').classList.toggle('hidden');
            };
            container.appendChild(toggle);
        }
        container.appendChild(open);
        const childrenDiv = document.createElement('div');
        childrenDiv.className = 'json-children';
        keys.forEach((key, index) => {
            const childRow = document.createElement('div');
            if (!isArray) {
                const keySpan = document.createElement('span');
                keySpan.className = 'json-key';
                keySpan.innerText = `"${key}":`;
                childRow.appendChild(keySpan);
            }
            childRow.appendChild(createJsonTree(data[key]));
            if (index < keys.length - 1) childRow.appendChild(createSpan(',', 'json-bracket'));
            childrenDiv.appendChild(childRow);
        });
        container.appendChild(childrenDiv);
        container.appendChild(createSpan(isArray ? ']' : '}', 'json-bracket'));
        return container;
    }
    return document.createTextNode(String(data));
}
function createSpan(text, className) { const s = document.createElement('span'); s.innerText = text; s.className = className; return s; }

function resetGraphZoom() {
    transform = { x: 50, y: 50, scale: 1 };
    if (currentExplorerItem && document.getElementById('tab-graph').classList.contains('active')) {
        renderGraph(currentExplorerItem);
    }
}
function renderGraph(data) {
    const container = document.getElementById('tab-graph');
    const canvas = document.getElementById('detail-canvas');
    if (!container || !canvas) return;
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    ctx = canvas.getContext('2d');
    canvas.onmousedown = (e) => { isDragging = true; startPos = { x: e.offsetX - transform.x, y: e.offsetY - transform.y }; canvas.style.cursor = 'grabbing'; };
    canvas.onmousemove = (e) => { if (isDragging) { transform.x = e.offsetX - startPos.x; transform.y = e.offsetY - startPos.y; drawGraph(); } };
    canvas.onmouseup = () => { isDragging = false; canvas.style.cursor = 'default'; };
    canvas.onwheel = (e) => { e.preventDefault(); const delta = e.deltaY > 0 ? 0.9 : 1.1; transform.scale *= delta; drawGraph(); };
    processGraphData(data);
    drawGraph();
}
function processGraphData(data) { nodes = []; edges = []; traverseGraph(data, null, 0, "ROOT"); layoutGraph(); }
function traverseGraph(data, parentId, depth, key) {
    const id = nodes.length;
    let value = typeof data === 'object' && data !== null ? (Array.isArray(data) ? "Array" : "Object") : String(data);
    nodes.push({ id, key, value, depth, children: [] });
    if (parentId !== null) { edges.push({ from: parentId, to: id }); nodes[parentId].children.push(id); }
    if (typeof data === 'object' && data !== null) { Object.keys(data).forEach(k => traverseGraph(data[k], id, depth + 1, k)); }
}
function layoutGraph() {
    let currentY = 50;
    function setPos(nodeId) {
        const node = nodes[nodeId];
        if (node.children.length === 0) { node.y = currentY; currentY += 60; }
        else { node.children.forEach(c => setPos(c)); const first = nodes[node.children[0]]; const last = nodes[node.children[node.children.length - 1]]; node.y = (first.y + last.y) / 2; }
        node.x = 50 + (node.depth * 200);
    }
    if (nodes.length > 0) setPos(0);
}
function drawGraph() {
    if (!ctx) return;
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    ctx.save();
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.scale, transform.scale);
    ctx.strokeStyle = '#555'; ctx.lineWidth = 2;
    edges.forEach(e => {
        const f = nodes[e.from]; const t = nodes[e.to];
        ctx.beginPath(); const startX = f.x + 160; const startY = f.y + 20; const endX = t.x; const endY = t.y + 20;
        ctx.moveTo(startX, startY); ctx.bezierCurveTo(startX + 50, startY, endX - 50, endY, endX, endY); ctx.stroke();
    });
    nodes.forEach(n => {
        ctx.fillStyle = '#222'; ctx.fillRect(n.x, n.y, 160, 40); ctx.strokeStyle = '#3b82f6'; ctx.lineWidth = 1; ctx.strokeRect(n.x, n.y, 160, 40);
        ctx.fillStyle = '#e06c75'; ctx.font = 'bold 12px Inter'; let k = n.key.length > 12 ? n.key.substring(0, 12) + '..' : n.key; ctx.fillText(k, n.x + 10, n.y + 25);
        ctx.fillStyle = '#98c379'; let v = n.value.length > 10 ? n.value.substring(0, 10) + '..' : n.value; ctx.fillText(v, n.x + 90, n.y + 25);
    });
    ctx.restore();
}

window.onload = () => { loadStats(); loadSettings(); checkSystemStatus(); };

async function checkSystemStatus() {
    try {
        const res = await fetch(`${API_URL}/system/status`).then(r => r.json());
        updateSystemButton(res.status);
    } catch (e) { console.error("Status check failed", e); }
}

function updateSystemButton(status) {
    const btn = document.getElementById('btn-system-toggle');
    if (status === 'PAUSED') {
        btn.innerHTML = '<i class="fa-solid fa-play"></i> Resume System';
        btn.style.color = 'var(--accent)';
        document.querySelector('.status-indicator').innerHTML = '<span class="dot" style="background:orange; box-shadow:none;"></span> SYSTEM PAUSED';
    } else {
        btn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause System';
        btn.style.color = 'var(--warning)';
        document.querySelector('.status-indicator').innerHTML = '<span class="dot"></span> SYSTEM ONLINE';
    }
}

async function toggleSystem() {
    const btn = document.getElementById('btn-system-toggle');
    const isPaused = btn.innerText.includes('Resume');
    const newStatus = isPaused ? 'RUNNING' : 'PAUSED';

    if (confirm(`Confirm: ${newStatus} System?`)) {
        try {
            await fetch(`${API_URL}/system/status`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus })
            });
            updateSystemButton(newStatus);
        } catch (e) { alert("Error toggling system"); }
    }
}
