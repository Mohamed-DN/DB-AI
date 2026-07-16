const API_URL = "http://localhost:8000/api";

// Navigation
function showSection(id) {
    document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    // Update nav pills - only buttons in nav-buttons div
    document.querySelectorAll('.nav-buttons .nav-pill').forEach(b => b.classList.remove('active'));
    if (event && event.currentTarget) event.currentTarget.classList.add('active');

    const titles = {
        'dashboard': 'Dashboard Overview',
        'inventory': 'Database Inventory',
        'hosts': 'Host Inventory',
        'alerts': 'System Alerts',
        'chat': 'AI Assistant',
        'mailbox': 'Communications',
        'data': 'Data Explorer',
        'agents': 'Agent Control Panel',
        'settings': 'Configuration'
    };
    document.getElementById('page-title').innerText = titles[id] || 'M-DN CMDB';

    if (id === 'dashboard') loadStats();
    if (id === 'inventory') loadInventory();
    if (id === 'hosts') loadHosts();
    if (id === 'alerts') loadAlerts();
    if (id === 'mailbox') loadEmails();
    if (id === 'data') loadExplorer('inventory_databases');
    if (id === 'settings') loadSettings();
    if (id === 'chat') { loadCurrentModel(); loadGpuStatus(); }
    if (id === 'agents') { loadAgentsStatus(); loadRagStatus(); }
}

// Open MongoDB Express
function openMongoDB() {
    window.open('http://localhost:8081', '_blank');
}

// Theme Toggle (Dark/Light Mode)
function toggleTheme() {
    const body = document.body;
    const icon = document.getElementById('theme-icon');

    if (body.classList.contains('light-mode')) {
        body.classList.remove('light-mode');
        icon.className = 'fa-solid fa-moon';
        localStorage.setItem('m-dn-theme', 'dark');
    } else {
        body.classList.add('light-mode');
        icon.className = 'fa-solid fa-sun';
        localStorage.setItem('m-dn-theme', 'light');
    }
}

// Apply saved theme on load
function applyStoredTheme() {
    const savedTheme = localStorage.getItem('m-dn-theme');
    const icon = document.getElementById('theme-icon');
    if (savedTheme === 'light') {
        document.body.classList.add('light-mode');
        if (icon) icon.className = 'fa-solid fa-sun';
    }
}

// Init on page load
document.addEventListener('DOMContentLoaded', () => {
    applyStoredTheme();
    loadStats();
});

// --- LLM MODEL MANAGEMENT ---
async function loadCurrentModel() {
    try {
        const res = await fetch(`${API_URL}/llm/current`).then(r => r.json());
        const select = document.getElementById('model-selector');
        if (select && res.model) {
            select.value = res.model;
        }
    } catch (e) { console.error('Failed to load model:', e); }
}

async function switchModel() {
    const select = document.getElementById('model-selector');
    const newModel = select.value;
    try {
        const res = await fetch(`${API_URL}/llm/switch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: newModel })
        });
        if (res.ok) {
            const data = await res.json();
            console.log('Model switched to:', data.model);
            // Update GPU status after switch
            setTimeout(loadGpuStatus, 2000);
        }
    } catch (e) { showAlert('Error', 'Failed to switch model: ' + e); }
}

async function loadGpuStatus() {
    try {
        const res = await fetch(`${API_URL}/gpu/status`).then(r => r.json());
        const el = document.getElementById('gpu-status');
        if (el && !res.error) {
            const usedGB = (res.memory_used_mb / 1024).toFixed(1);
            const totalGB = (res.memory_total_mb / 1024).toFixed(1);
            el.innerHTML = `GPU: ${usedGB}/${totalGB}GB (${res.utilization_pct}%)`;
        } else if (el && res.error) {
            el.innerHTML = 'GPU: N/A';
        }
    } catch (e) { console.error('GPU status error:', e); }
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
            const name = db.identity?.db_unique_name || 'UNKNOWN';
            const engine = db.identity?.engine || 'UNKNOWN';
            const host = db.identity?.host || 'N/A';
            const port = db.identity?.port || db.configuration?.port || 'N/A';
            const env = db.identity?.environment || 'N/A';

            let badgeClass = 'status-down';
            if (status === 'UP') badgeClass = 'status-up';

            const isOracle = engine === 'ORACLE';
            const sqlLabel = isOracle ? 'sqlplus' : 'psql';
            const sqlIcon = isOracle ? 'fa-solid fa-server' : 'fa-solid fa-terminal';

            // Main Row
            tr.innerHTML = `
                <td><span class="status-badge ${badgeClass}">${status}</span></td>
                <td><div style="font-weight:bold;">${name}</div><div style="font-size:0.8em; opacity:0.7;">${db.identity?.topology || ''}</div></td>
                <td><i class="fa-solid fa-database"></i> ${engine}</td>
                <td>${host}</td>
                <td>${port}</td>
                <td>${env}</td>
                <td>
                    <div style="display:flex; gap:5px;">
                        <button class="btn sm" onclick="connectDB('${name}', 'sql')" title="SQL Console"><i class="${sqlIcon}"></i> ${sqlLabel}</button>
                        <button class="btn sm" onclick="connectDB('${name}', 'bash')" title="Linux Shell" style="background:#4e5d6c;"><i class="fa-brands fa-linux"></i> bash</button>
                        ${status !== 'UP' ? `<button class="btn sm btn-danger" onclick="deleteDB('${name}')" title="Delete from Inventory"><i class="fa-solid fa-trash"></i></button>` : ''}
                    </div>
                </td>
            `;
            tbody.appendChild(tr);

            // Render PDBs if available
            if (db.configuration?.oracle_specific?.pdbs) {
                db.configuration.oracle_specific.pdbs.forEach(pdb => {
                    const pdbRow = document.createElement('tr');
                    pdbRow.style.background = 'rgba(255,255,255,0.02)';
                    const pdbName = pdb.name;
                    const pdbMode = pdb.open_mode || 'N/A'; // Actually we removed open_mode from query, so careful. Collector might not have it.
                    // Collector patch removed OPEN_MODE to fix ORA error. So we rely on status.
                    const pdbStatus = pdb.status || 'UNKNOWN';
                    let pdbBadge = 'status-down';
                    if (pdbStatus === 'READ WRITE') pdbBadge = 'status-up';

                    pdbRow.innerHTML = `
                        <td style="text-align:right;"><span style="color:var(--text-secondary); font-size:0.8rem;">↳</span></td>
                        <td><div style="display:flex; align-items:center; gap:5px;"><i class="fa-solid fa-plug" style="font-size:0.7rem;"></i> ${pdbName}</div></td>
                        <td colspan="4" style="font-size:0.85rem; color:var(--text-secondary);">
                            <span class="status-badge ${pdbBadge}" style="transform:scale(0.8);">${pdbStatus}</span>
                        </td>
                        <td>
                             <button class="btn sm" onclick="connectDB('${name}/${pdbName}', 'sql')" title="Connect to PDB" style="opacity:0.7; transform:scale(0.9);"><i class="fa-solid fa-arrow-right-to-bracket"></i> Connect</button>
                        </td>
                    `;
                    tbody.appendChild(pdbRow);
                });
            }
        });
    } catch (e) { console.error(e); }
}

async function loadHosts() {
    try {
        const dbs = await fetch(`${API_URL}/inventory`).then(r => r.json());
        const tbody = document.getElementById('host-list');
        tbody.innerHTML = '';

        // Extract unique hosts
        const hosts = {};
        dbs.forEach(db => {
            const h = db.state?.metrics?.hostname || db.identity?.host || db.connection?.host;
            if (!h) return;
            if (!hosts[h]) {
                hosts[h] = {
                    name: h,
                    os: db.state?.metrics?.os?.name || 'Unknown',
                    cpu: db.state?.metrics?.cpu?.cores || '?',
                    mem: db.state?.metrics?.memory?.total_gb || 0,
                    dbs: []
                };
            }
            hosts[h].dbs.push(db.identity.db_unique_name);
        });

        Object.values(hosts).forEach(h => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><i class="fa-solid fa-server"></i> ${h.name}</td>
                <td><i class="fa-brands fa-linux"></i> ${h.os}</td>
                <td>${h.cpu} Cores / ${parseFloat(h.mem).toFixed(1)} GB RAM</td>
                <td>${h.dbs.map(d => `<span style="font-size:0.8rem; background:rgba(255,255,255,0.1); padding:2px 6px; border-radius:4px; margin-right:4px;">${d}</span>`).join('')}</td>
                <td>
                    <button class="btn sm" onclick="alert('Simulated SSH to host ' + '${h.name}')" title="SSH"><i class="fa-solid fa-terminal"></i> SSH</button>
                    ${h.name === '172.20.3.10' || h.name === '192.168.56.101' ? '<span class="status-badge status-up" style="font-size:0.7rem">GW: MAESDN</span>' : ''}
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
        showAlert("Error", "Impossibile aprire il terminale: " + e);
    }
}

async function deleteDB(name) {
    showModal(
        'Delete Database?',
        `Are you sure you want to remove ${name} from the inventory? This will NOT delete the Docker container.`,
        async () => {
            try {
                const res = await fetch(`${API_URL}/inventory/${name}`, { method: 'DELETE' });
                const data = await res.json();
                if (res.ok) {
                    loadInventory(); // Refresh list
                } else {
                    showAlert("Error", "Error: " + data.detail);
                }
            } catch (e) {
                showAlert("Error", "Delete failed: " + e);
            }
        }
    );
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
        // Load all agent intervals
        const agents = ['scout', 'criticalalert', 'watcher', 'forensicanalyzer', 'checkmk_bridge', 'collector'];
        agents.forEach(agent => {
            const input = document.getElementById(`setting-${agent}`);
            if (input && config[`${agent}_interval`]) {
                input.value = config[`${agent}_interval`];
            }
        });
    } catch (e) { console.error(e); }
}

async function saveSettings() {
    // Collect all agent intervals
    const agents = ['scout', 'criticalalert', 'watcher', 'forensicanalyzer', 'checkmk_bridge', 'collector'];
    const config = {};

    agents.forEach(agent => {
        const input = document.getElementById(`setting-${agent}`);
        if (input) {
            config[`${agent}_interval`] = parseInt(input.value) || 60;
        }
    });

    try {
        await fetch(`${API_URL}/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        showProcessLog('Configuration Saved');
        addProcessLogEntry('Settings', true, 'All agent intervals saved to database');
    } catch (e) {
        showProcessLog('Error');
        addProcessLogEntry('Settings', false, 'Failed to save configuration');
    }
}

async function triggerAction(action) {
    showModal(
        'Confirm Action',
        `Are you sure you want to execute: ${action}?`,
        async () => {
            try {
                await fetch(`${API_URL}/action/${action}`, { method: 'POST' });
                setTimeout(loadStats, 2000);
                showAlert("Success", `✅ ${action} executed!`);
            } catch (e) { showAlert("Error", `❌ Error executing ${action}: ${e.message}`); }
        }
    );
}

async function loadEmails() {
    try {
        const files = await fetch(`${API_URL}/emails`).then(r => r.json());
        const list = document.getElementById('email-list');
        list.innerHTML = '';
        if (files.length === 0) {
            list.innerHTML = '<div style="text-align:center; padding:2rem; color:#666;"><i class="fa-solid fa-inbox" style="font-size:2rem; margin-bottom:1rem; opacity:0.3;"></i><br>No emails</div>';
            return;
        }
        files.forEach(f => {
            const div = document.createElement('div');
            div.className = 'email-item';
            // Removed inline styles, now handled by CSS

            // Parse filename for display
            const displayName = f.replace('alert_', '').replace('.html', '').replace(/_/g, ' ');

            div.innerHTML = `
                <button class="email-btn" onclick="viewEmail('${f}', this.parentElement)">
                    <i class="fa-solid fa-envelope" style="color:var(--accent); margin-right:8px;"></i>${displayName}
                </button>
                <button class="btn-delete-email" onclick="event.stopPropagation(); deleteEmail('${f}')" title="Delete">
                    <i class="fa-solid fa-trash"></i>
                </button>
            `;
            // Removed inline onmouseover/out handlers

            list.appendChild(div);
        });
    } catch (e) { console.error(e); }
}

async function viewEmail(filename, el) {
    // Use classes for active state
    document.querySelectorAll('.email-item').forEach(l => l.classList.remove('active'));
    if (el) el.classList.add('active');

    try {
        const res = await fetch(`${API_URL}/emails/content?filename=${filename}`).then(r => r.json());
        const iframe = document.getElementById('email-preview');
        iframe.contentWindow.document.open();
        iframe.contentWindow.document.write(res.content);
        iframe.contentWindow.document.close();
    } catch (e) { showAlert("Error", "Error loading email"); }
}

async function deleteEmail(filename) {
    try {
        const res = await fetch(`${API_URL}/emails/${filename}`, { method: 'DELETE' });
        if (res.ok) {
            loadEmails();
            document.getElementById('email-preview').contentWindow.document.open();
            document.getElementById('email-preview').contentWindow.document.write('<html><body style="background:#000;color:#666;display:flex;align-items:center;justify-content:center;height:100%;margin:0;">Email deleted</body></html>');
            document.getElementById('email-preview').contentWindow.document.close();
        }
    } catch (e) { showAlert("Error", 'Failed to delete email: ' + e); }
}

async function deleteAllEmails() {
    showModal(
        'Delete All Emails?',
        'Are you sure you want to delete ALL emails from the inbox? This cannot be undone.',
        async () => {
            try {
                const res = await fetch(`${API_URL}/emails/all`, { method: 'DELETE' });
                if (res.ok) {
                    loadEmails();
                    document.getElementById('email-preview').contentWindow.document.open();
                    document.getElementById('email-preview').contentWindow.document.write('<html><body style="background:#000;color:#666;display:flex;align-items:center;justify-content:center;height:100%;margin:0;">All emails deleted</body></html>');
                    document.getElementById('email-preview').contentWindow.document.close();
                }
            } catch (e) { showAlert("Error", 'Failed to delete emails: ' + e); }
        }
    );
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

    // Draw edges with gradient
    edges.forEach(e => {
        const f = nodes[e.from]; const t = nodes[e.to];
        ctx.beginPath();
        ctx.strokeStyle = '#4a5568';
        ctx.lineWidth = 2;
        const startX = f.x + 140; const startY = f.y + 18;
        const endX = t.x; const endY = t.y + 18;
        ctx.moveTo(startX, startY);
        ctx.bezierCurveTo(startX + 40, startY, endX - 40, endY, endX, endY);
        ctx.stroke();
    });

    // Draw rounded rectangle nodes
    nodes.forEach(n => {
        const nodeWidth = 140;
        const nodeHeight = 36;
        const radius = 12; // Corner radius

        // Rounded rectangle shape
        ctx.beginPath();
        ctx.roundRect(n.x, n.y, nodeWidth, nodeHeight, radius);

        // Fill with gradient
        const gradient = ctx.createLinearGradient(n.x, n.y, n.x + nodeWidth, n.y + nodeHeight);
        gradient.addColorStop(0, '#1a1a2e');
        gradient.addColorStop(1, '#0f1724');
        ctx.fillStyle = gradient;
        ctx.fill();

        // Border
        ctx.strokeStyle = '#4ade80';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Key text (pink)
        ctx.fillStyle = '#f472b6';
        ctx.font = 'bold 10px Inter';
        let k = n.key.length > 12 ? n.key.substring(0, 12) + '..' : n.key;
        ctx.fillText(k, n.x + 8, n.y + 22);

        // Value text (green)
        ctx.fillStyle = '#a7f3d0';
        ctx.font = '10px Inter';
        let v = n.value.length > 10 ? n.value.substring(0, 10) + '..' : n.value;
        ctx.fillText(v, n.x + 75, n.y + 22);
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
    const action = isPaused ? 'Starting' : 'Stopping';

    showModal(
        'System Status Change',
        `Do you want to ${action.toLowerCase()} all Docker containers?`,
        async () => {
            // Show process log
            showProcessLog(action + ' Docker Containers...');

            try {
                const res = await fetch(`${API_URL}/system/status`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus })
                });
                const data = await res.json();

                // Display results
                if (data.results) {
                    displayProcessResults(data.results);
                }

                updateSystemButton(newStatus);
            } catch (e) {
                addProcessLogEntry('Error', false, e.message);
            }
        }
    );
}

// --- PROCESS LOG FUNCTIONS ---
function showProcessLog(title) {
    const overlay = document.getElementById('process-log-overlay');
    const titleEl = document.getElementById('process-log-title');
    const content = document.getElementById('process-log-content');

    titleEl.innerText = title;
    content.innerHTML = '<div id="process-log-initializing" class="process-log-entry pending"><span class="icon"><i class="fa-solid fa-spinner fa-spin"></i></span><span class="name">Initializing...</span><span class="status">PENDING</span></div>';

    overlay.style.display = 'flex';
    overlay.style.opacity = '1';
    overlay.style.visibility = 'visible';
}

function displayProcessResults(results) {
    const content = document.getElementById('process-log-content');
    content.innerHTML = '';

    results.forEach(r => {
        const entry = document.createElement('div');
        entry.className = `process-log-entry ${r.success ? 'success' : 'error'}`;
        entry.innerHTML = `
            <span class="icon"><i class="fa-solid ${r.success ? 'fa-check' : 'fa-xmark'}"></i></span>
            <span class="name">${r.container}</span>
            <span class="status">${r.success ? (r.action === 'start' ? 'STARTED' : 'STOPPED') : 'FAILED'}</span>
        `;
        content.appendChild(entry);
    });
}

function addProcessLogEntry(name, success, message) {
    const content = document.getElementById('process-log-content');

    // Remove the initializing spinner if present
    const initSpinner = document.getElementById('process-log-initializing');
    if (initSpinner) initSpinner.remove();

    const entry = document.createElement('div');
    entry.className = `process-log-entry ${success ? 'success' : 'error'}`;
    entry.innerHTML = `
        <span class="icon"><i class="fa-solid ${success ? 'fa-check' : 'fa-xmark'}"></i></span>
        <span class="name">${name}</span>
        <span class="status">${message || (success ? 'OK' : 'ERROR')}</span>
    `;
    content.appendChild(entry);
}

function closeProcessLog() {
    const overlay = document.getElementById('process-log-overlay');
    overlay.style.opacity = '0';
    overlay.style.visibility = 'hidden';
    setTimeout(() => { overlay.style.display = 'none'; }, 300);
}

// --- CUSTOM MODAL ---
function showModal(title, message, onConfirm, isAlert = false) {
    const overlay = document.getElementById('custom-modal-overlay');
    const titleEl = document.getElementById('modal-title');
    const msgEl = document.getElementById('modal-message');
    const btnConfirm = document.getElementById('modal-btn-confirm');
    const btnCancel = document.getElementById('modal-btn-cancel');

    titleEl.innerText = title;
    msgEl.innerText = message;

    // Reset Buttons
    btnConfirm.innerText = isAlert ? "Ok" : "Confirm";
    btnCancel.style.display = isAlert ? "none" : "inline-block";

    // Clear old listeners
    const newConfirm = btnConfirm.cloneNode(true);
    const newCancel = btnCancel.cloneNode(true);
    btnConfirm.parentNode.replaceChild(newConfirm, btnConfirm);
    btnCancel.parentNode.replaceChild(newCancel, btnCancel);

    // Add new listeners
    newConfirm.addEventListener('click', () => {
        closeModal();
        if (onConfirm) onConfirm();
    });

    newCancel.addEventListener('click', closeModal);
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeModal();
    });

    overlay.classList.add('active');
}

function showAlert(title, message) {
    showModal(title, message, null, true);
}

function closeModal() {
    document.getElementById('custom-modal-overlay').classList.remove('active');
}

// =============================================================================
// AGENT CONTROL FUNCTIONS
// =============================================================================

async function loadAgentsStatus() {
    try {
        const response = await fetch(`${API_URL}/agents/status`);
        const data = await response.json();

        const grid = document.getElementById('agents-grid');
        grid.innerHTML = '';

        for (const [name, info] of Object.entries(data.agents)) {
            const card = document.createElement('div');
            card.className = 'stat-card';
            card.style.padding = '1rem';
            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-weight:bold; margin-bottom:0.5rem;">${name}</div>
                        <div style="font-size:0.8rem; color:#666;">${info.script}</div>
                    </div>
                    <div style="display:flex; flex-direction:column; align-items:flex-end; gap:5px;">
                        <span class="status-badge ${info.running ? 'running' : 'stopped'}">
                            ${info.running ? '● Running' : '○ Stopped'}
                        </span>
                        <button class="btn btn-primary sm" onclick="startAgent('${name}')" ${info.running ? 'disabled' : ''}>
                            <i class="fa-solid fa-play"></i> Start
                        </button>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        }
    } catch (e) {
        console.error('Error loading agents:', e);
    }
}

async function loadRagStatus() {
    try {
        const response = await fetch(`${API_URL}/rag/status`);
        const data = await response.json();

        const ollamaEl = document.getElementById('rag-ollama-status');
        const qdrantEl = document.getElementById('rag-qdrant-status');

        if (data.ollama.connected) {
            ollamaEl.innerHTML = `<span style="color:var(--success)">● Connected</span><br><small>${data.ollama.models.length} models</small>`;
        } else {
            ollamaEl.innerHTML = `<span style="color:var(--danger)">● Offline</span>`;
        }

        if (data.qdrant.connected) {
            qdrantEl.innerHTML = `<span style="color:var(--success)">● Connected</span><br><small>${data.qdrant.collections} collections</small>`;
        } else {
            qdrantEl.innerHTML = `<span style="color:var(--danger)">● Offline</span>`;
        }
    } catch (e) {
        console.error('Error loading RAG status:', e);
    }
}

async function startAgent(name) {
    // Show loading state in process log
    showProcessLog(`Running ${name}...`);
    addProcessLogEntry(name, null, 'Starting...');

    try {
        const response = await fetch(`${API_URL}/agents/start/${name}`, { method: 'POST' });
        const data = await response.json();

        // Clear and show results
        document.getElementById('process-log-content').innerHTML = '';

        if (data.output && data.output.length > 0) {
            data.output.forEach(line => {
                const isSuccess = line.includes('✅') || line.includes('ALLOWED') || line.includes('Complete');
                const isError = line.includes('❌') || line.includes('Error') || line.includes('BLOCKED');
                addProcessLogEntry('', isError ? false : (isSuccess ? true : null), line);
            });
        }

        // Add summary line
        addProcessLogEntry(
            name,
            data.success,
            data.success ? 'Execution completed successfully' : `Exited with code ${data.exit_code}`
        );

        // Refresh agent status after delay
        setTimeout(loadAgentsStatus, 1000);
    } catch (e) {
        addProcessLogEntry(name, false, `Error: ${e}`);
    }
}

async function triggerAgentAction(action) {
    try {
        let endpoint = '';
        switch (action) {
            case 'checkmk': endpoint = '/agents/trigger/checkmk'; break;
            case 'forensic': endpoint = '/agents/trigger/forensic'; break;
            case 'watcher': endpoint = '/agents/trigger/watcher'; break;
            default: return;
        }

        const response = await fetch(`${API_URL}${endpoint}`, { method: 'POST' });
        const data = await response.json();
        alert(data.status);
    } catch (e) {
        alert(`Error: ${e}`);
    }
}
