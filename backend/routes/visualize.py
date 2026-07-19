import os

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/chart", response_class=HTMLResponse)
def chart():
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>OpenET Water Use Platform</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://accounts.google.com/gsi/client" async defer></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css"/>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body { height: 100%; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; background: #0d0d1a; color: white; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        header { background: linear-gradient(135deg, #1a237e 0%, #283593 100%); color: white; padding: 12px 24px; display: flex; align-items: center; gap: 16px; border-bottom: 2px solid #b22222; flex-shrink: 0; }
        .header-logo { width: 36px; height: 36px; background: #b22222; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
        .header-text h1 { font-size: 18px; font-weight: 600; letter-spacing: 0.3px; }
        .header-text p { font-size: 11px; opacity: 0.75; margin-top: 2px; }
        .header-badge { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 20px; padding: 3px 10px; font-size: 10px; opacity: 0.9; margin-left: 8px; }
        .controls { display: flex; gap: 8px; align-items: center; margin-left: auto; flex-wrap: wrap; }
        .controls label { font-size: 11px; opacity: 0.8; }
        .controls input { padding: 6px 10px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.2); font-size: 11px; width: 110px; background: rgba(255,255,255,0.1); color: white; }
        .controls input::placeholder { color: rgba(255,255,255,0.5); }
        .controls input:focus { outline: none; border-color: rgba(255,255,255,0.5); background: rgba(255,255,255,0.15); }
        .btn { padding: 6px 14px; border: none; border-radius: 6px; font-size: 11px; cursor: pointer; font-weight: 500; transition: all 0.15s; }
        .btn-go { background: rgba(255,255,255,0.15); color: white; border: 1px solid rgba(255,255,255,0.3); }
        .btn-go:hover { background: rgba(255,255,255,0.25); }
        .btn-heatmap { background: #4CAF50; color: white; }
        .btn-heatmap:hover { background: #388E3C; }
        .main { display: grid; grid-template-columns: 1fr 380px; flex: 1; min-height: 0; }
        #map { width: 100%; height: 100%; }
        .side-panel { background: #111827; display: flex; flex-direction: column; overflow: hidden; min-height: 0; border-left: 1px solid rgba(255,255,255,0.08); }
        .side-panel-header { padding: 16px 20px 12px; border-bottom: 1px solid rgba(255,255,255,0.08); }
        .side-panel-header h2 { font-size: 13px; font-weight: 600; color: #90caf9; letter-spacing: 0.5px; text-transform: uppercase; }
        .side-panel-body { padding: 16px 20px; flex: 1; display: flex; flex-direction: column; gap: 14px; overflow-y: auto; }
        .stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
        .stat-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 10px 12px; text-align: center; }
        .stat-card .val { font-size: 18px; font-weight: 600; color: #90caf9; }
        .stat-card .lbl { font-size: 10px; color: rgba(255,255,255,0.5); margin-top: 2px; }
        .stat-card.anomaly .val { color: #ef4444; }
        .stat-card.anomaly { border-color: rgba(239,68,68,0.3); background: rgba(239,68,68,0.05); }
        .annual-row { display: flex; gap: 8px; }
        .annual-card { flex: 1; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 10px 8px; text-align: center; }
        .annual-card .year-label { font-size: 10px; color: rgba(255,255,255,0.5); margin-bottom: 4px; }
        .annual-card .year-val { font-size: 20px; font-weight: 700; }
        .annual-card .year-unit { font-size: 9px; color: rgba(255,255,255,0.4); margin-top: 2px; }
        .coords { font-size: 11px; color: rgba(255,255,255,0.45); display: flex; align-items: center; gap: 6px; }
        .coords-dot { width: 6px; height: 6px; border-radius: 50%; background: #4CAF50; flex-shrink: 0; }
        .coords-dot.anomaly { background: #ef4444; }
        .legend { display: flex; gap: 12px; flex-wrap: wrap; }
        .legend-item { display: flex; align-items: center; gap: 5px; font-size: 11px; color: rgba(255,255,255,0.6); }
        .legend-dot { width: 10px; height: 10px; border-radius: 2px; }
        .anomaly-box { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.35); border-radius: 8px; padding: 10px 14px; font-size: 11px; color: #fca5a5; line-height: 1.5; }
        .anomaly-box.low { background: rgba(234,179,8,0.1); border-color: rgba(234,179,8,0.35); color: #fde047; }
        .loading-wrap { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; gap: 12px; }
        .spinner { width: 32px; height: 32px; border: 3px solid rgba(255,255,255,0.1); border-top-color: #90caf9; border-radius: 50%; animation: spin 0.8s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loading-text { font-size: 12px; color: rgba(255,255,255,0.45); }
        #chart-wrapper { flex: 1; min-height: 220px; }
        .btn-download { padding: 10px 16px; background: #1e5c2e; color: #4ade80; border: 1px solid #166534; border-radius: 8px; font-size: 12px; cursor: pointer; width: 100%; font-weight: 500; transition: all 0.15s; text-align: center; }
        .btn-download:hover { background: #166534; }
        .heatmap-status { font-size: 10px; color: rgba(255,255,255,0.35); text-align: center; padding: 4px 0; }
        .map-overlay { position: absolute; bottom: 30px; left: 10px; z-index: 1000; background: rgba(0,0,0,0.75); padding: 10px 14px; border-radius: 10px; font-size: 11px; color: white; backdrop-filter: blur(4px); border: 1px solid rgba(255,255,255,0.1); }
        .color-bar { width: 140px; height: 8px; border-radius: 4px; background: linear-gradient(to right, #000080, #0000ff, #00ffff, #00ff00, #ffff00, #ff0000); margin: 6px 0 4px; }
        .color-labels { display: flex; justify-content: space-between; font-size: 10px; opacity: 0.7; }
        .empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; gap: 8px; opacity: 0.4; }
        .empty-state .icon { font-size: 32px; }
        .empty-state p { font-size: 12px; text-align: center; line-height: 1.5; }
        .section-label { font-size: 10px; font-weight: 600; color: rgba(255,255,255,0.35); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: -6px; }
        .compare-panel { display:none; position:absolute; top:10px; right:10px; z-index:1000; background:rgba(0,0,0,0.85); padding:12px 14px; border-radius:10px; color:white; font-size:12px; max-width:240px; backdrop-filter: blur(4px); border: 1px solid rgba(255,255,255,0.1); }
        .compare-panel-title { font-weight:600; margin-bottom:8px; }
        .compare-item { display:flex; align-items:center; justify-content:space-between; gap:4px; background:rgba(255,255,255,0.05); padding:4px 6px; border-radius:4px; margin-bottom:6px; }
        .compare-item span.name { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:120px; }
        .compare-item .actions button { background:none; border:none; cursor:pointer; font-size:12px; }
        .compare-select { width:100%; font-size:11px; background:rgba(255,255,255,0.1); color:white; border:1px solid rgba(255,255,255,0.2); border-radius:4px; padding:4px; margin-top:8px; }
        .compare-run-btn { margin-top:8px; width:100%; padding:6px; background:#2563eb; color:white; border:none; border-radius:6px; cursor:pointer; font-size:12px; }
        .compare-modal-backdrop { display:none; position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.75); z-index:2000; align-items:center; justify-content:center; }
        .compare-modal-box { background:#111827; border-radius:12px; padding:24px; max-width:900px; width:90%; max-height:85vh; overflow-y:auto; border:1px solid rgba(255,255,255,0.1); }
        .compare-modal-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
        .compare-modal-header h2 { font-size:16px; color:#90caf9; }
        .compare-modal-close { background:none; border:none; color:white; font-size:20px; cursor:pointer; }
        #compare-table { width:100%; margin-top:20px; border-collapse:collapse; font-size:12px; }
    </style>
</head>
<body>
    <header>
        <div class="header-logo">🌿</div>
        <div class="header-text">
            <h1>OpenET Water Use Platform <span class="header-badge">Cornell M.Eng</span></h1>
            <p>Satellite-based agricultural evapotranspiration analysis — Finger Lakes Region</p>
        </div>
        <div class="controls">
            <input type="text" id="search" placeholder="Search location..." style="width:150px;"
                onkeydown="if(event.key==='Enter') searchLocation()"/>
            <button class="btn btn-go" onclick="searchLocation()">Go</button>
            <label>From</label>
            <input type="text" id="start" value="2022-01-01"/>
            <label>To</label>
            <input type="text" id="end" value="2023-12-31"/>
            <button class="btn btn-heatmap" id="heatmap-btn" onclick="toggleHeatmap()">Heatmap Off</button>
            <button class="btn" id="heatmap-mode-btn" onclick="toggleHeatmapMode()" style="background:rgba(255,255,255,0.08);color:rgba(255,255,255,0.7);border:1px solid rgba(255,255,255,0.2);display:none;">Mode: Intensity</button>
            <button class="btn" id="ndvi-btn" onclick="toggleNDVI()" style="background:rgba(74,222,128,0.2);color:#4ade80;border:1px solid rgba(74,222,128,0.5);">NDVI Off</button>
            <button class="btn" id="cdl-btn" onclick="toggleCDL()" style="background:rgba(251,191,36,0.2);color:#fbbf24;border:1px solid rgba(251,191,36,0.5);">Crop Type Off</button>
            <button class="btn" id="usdm-btn" onclick="toggleUSDM()" style="background:rgba(248,113,113,0.2);color:#f87171;border:1px solid rgba(248,113,113,0.5);">Drought Off</button>
            <button class="btn" id="compare-btn" onclick="toggleCompareMode()" style="background:rgba(96,165,250,0.2);color:#60a5fa;border:1px solid rgba(96,165,250,0.5);">Compare Off</button>
            <button class="btn" id="history-btn" onclick="toggleHistoryPanel()" style="background:rgba(167,139,250,0.2);color:#a78bfa;border:1px solid rgba(167,139,250,0.5);">History</button>
            <div id="auth-section" style="display:flex; align-items:center; gap:8px;"></div>
        </div>
    </header>

    <div class="main">
        <div style="position:relative;">
            <div id="map"></div>
            <div class="map-overlay">
                <div style="font-weight:500;margin-bottom:2px;" id="heatmap-legend-title">ET Intensity</div>
                <div class="color-bar"></div>
                <div class="color-labels" id="heatmap-legend-labels"><span>Low</span><span>High</span></div>
                <div id="ndvi-legend" style="display:none;margin-top:10px;">
                    <div style="font-weight:500;margin-bottom:2px;">NDVI (Vegetation)</div>
                    <div style="width:140px;height:8px;border-radius:4px;background:linear-gradient(to right,#8B4513,#d4a853,#90EE90,#228B22);margin:4px 0;"></div>
                    <div style="display:flex;justify-content:space-between;font-size:10px;opacity:0.7;"><span>Bare soil</span><span>Dense veg</span></div>
                </div>
                <div id="cdl-legend" style="display:none;margin-top:10px;">
                    <div style="font-weight:500;margin-bottom:4px;">USDA CDL — Crop Type</div>
                    <div style="display:flex;flex-direction:column;gap:3px;font-size:10px;">
                        <div><span style="display:inline-block;width:10px;height:10px;background:#ffd400;margin-right:4px;border-radius:2px;"></span>Corn</div>
                        <div><span style="display:inline-block;width:10px;height:10px;background:#267000;margin-right:4px;border-radius:2px;"></span>Soybeans</div>
                        <div><span style="display:inline-block;width:10px;height:10px;background:#e2007c;margin-right:4px;border-radius:2px;"></span>Grapes / Vineyard</div>
                        <div><span style="display:inline-block;width:10px;height:10px;background:#a87000;margin-right:4px;border-radius:2px;"></span>Orchard / Fruit</div>
                        <div><span style="display:inline-block;width:10px;height:10px;background:#dfd642;margin-right:4px;border-radius:2px;"></span>Hay / Pasture</div>
                        <div><span style="display:inline-block;width:10px;height:10px;background:#93cc93;margin-right:4px;border-radius:2px;"></span>Forest</div>
                        <div><span style="display:inline-block;width:10px;height:10px;background:#4970a3;margin-right:4px;border-radius:2px;"></span>Water</div>
                    </div>
                </div>
                <div id="usdm-legend" style="display:none;margin-top:10px;">
                    <div style="font-weight:500;margin-bottom:4px;">U.S. Drought Monitor</div>
                    <div style="display:flex;flex-direction:column;gap:3px;font-size:10px;">
                        <div><span style="display:inline-block;width:10px;height:10px;background:#FFFF00;margin-right:4px;border-radius:2px;"></span>D0 — Abnormally Dry</div>
                        <div><span style="display:inline-block;width:10px;height:10px;background:#FCD37F;margin-right:4px;border-radius:2px;"></span>D1 — Moderate Drought</div>
                        <div><span style="display:inline-block;width:10px;height:10px;background:#FFAA00;margin-right:4px;border-radius:2px;"></span>D2 — Severe Drought</div>
                        <div><span style="display:inline-block;width:10px;height:10px;background:#E60000;margin-right:4px;border-radius:2px;"></span>D3 — Extreme Drought</div>
                        <div><span style="display:inline-block;width:10px;height:10px;background:#730000;margin-right:4px;border-radius:2px;"></span>D4 — Exceptional Drought</div>
                    </div>
                </div>
            </div>
            <div class="compare-panel" id="compare-list-panel">
                <div class="compare-panel-title">Compare Fields (<span id="compare-count">0</span>)</div>
                <div id="compare-items"></div>
                <select class="compare-select" id="saved-fields-select" onchange="onSavedFieldSelected()">
                    <option value="">Load saved field...</option>
                </select>
                <select class="compare-select" id="comparison-sets-select" onchange="onComparisonSetSelected()">
                    <option value="">Load saved set...</option>
                </select>
                <button class="compare-run-btn" onclick="runComparison()">Run Comparison</button>
                <button class="compare-run-btn" onclick="saveComparisonSet()" style="background:#166534;margin-top:6px;">Save This Set</button>
            </div>
        </div>
        <div class="side-panel">
            <div class="side-panel-header">
                <h2>ET Analysis</h2>
            </div>
            <div class="side-panel-body">
                <div class="coords" id="coords">
                    <span class="coords-dot" id="coords-dot"></span>
                    <span id="coords-text">Click or draw a polygon on the map</span>
                </div>

                <!-- Monthly stats -->
                <div class="stats-row" id="stats-row" style="display:none;">
                    <div class="stat-card">
                        <div class="val" id="stat-total">—</div>
                        <div class="lbl">Total ET (in)</div>
                    </div>
                    <div class="stat-card">
                        <div class="val" id="stat-avg">—</div>
                        <div class="lbl">Avg Monthly</div>
                    </div>
                    <div class="stat-card" id="stat-anomaly-card">
                        <div class="val" id="stat-anomalies">—</div>
                        <div class="lbl">Anomalies</div>
                    </div>
                </div>

                <!-- Annual ET summary -->
                <div id="annual-section" style="display:none;">
                    <div class="section-label">Annual ET</div>
                    <div class="annual-row" id="annual-row"></div>
                </div>

                <div class="legend">
                    <div class="legend-item"><div class="legend-dot" style="background:rgba(37,99,235,0.8);"></div>Normal</div>
                    <div class="legend-item"><div class="legend-dot" style="background:#ef4444;"></div>High anomaly</div>
                    <div class="legend-item"><div class="legend-dot" style="background:#eab308;"></div>Low anomaly</div>
                </div>

                <div id="anomaly-alert" style="display:none;" class="anomaly-box"></div>

                <div class="empty-state" id="empty-state">
                    <div class="icon">🍇</div>
                    <p>Click a green dot or draw a polygon to load ET data</p>
                </div>
                <div class="loading-wrap" id="loading-wrap" style="display:none;">
                    <div class="spinner"></div>
                    <div class="loading-text" id="loading-text">Loading satellite data...</div>
                </div>
                <div id="chart-wrapper" style="display:none;">
                    <canvas id="chart"></canvas>
                </div>

                <button class="btn-download" id="download-btn" onclick="downloadReport()" style="display:none;">
                    ⬇ Download CSV Report
                </button>

                <div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 14px;">
                    <div style="font-size:12px; font-weight:600; color:#90caf9; margin-bottom:10px; text-transform:uppercase; letter-spacing:0.5px;">AI Assistant</div>
                    <div id="chat-messages" style="max-height:220px; overflow-y:auto; display:flex; flex-direction:column; gap:8px; margin-bottom:10px;"></div>
                    <div style="display:flex; flex-wrap:wrap; gap:6px;">
                        <button class="suggested-q" onclick="answerPreset('summarize')" style="padding:6px 12px; background:rgba(144,202,249,0.1); color:#90caf9; border:1px solid rgba(144,202,249,0.3); border-radius:12px; font-size:11px; cursor:pointer;">Summarize this field</button>
                        <button class="suggested-q" onclick="answerPreset('anomalies')" style="padding:6px 12px; background:rgba(144,202,249,0.1); color:#90caf9; border:1px solid rgba(144,202,249,0.3); border-radius:12px; font-size:11px; cursor:pointer;">Explain anomalies</button>
                        <button class="suggested-q" onclick="answerPreset('compare')" style="padding:6px 12px; background:rgba(144,202,249,0.1); color:#90caf9; border:1px solid rgba(144,202,249,0.3); border-radius:12px; font-size:11px; cursor:pointer;">Compare years</button>
                    </div>
                    <div style="font-size:10px; color:rgba(255,255,255,0.3); margin-top:8px;">Click a question above — answers are generated instantly from the loaded field data, no AI service required.</div>
                </div>
                <div class="heatmap-status" id="heatmap-status"></div>
            </div>
        </div>
    </div>

    <div class="compare-modal-backdrop" id="auth-modal">
        <div class="compare-modal-box" style="max-width:360px;">
            <div class="compare-modal-header">
                <h2>Sign In</h2>
                <button class="compare-modal-close" onclick="closeAuthModal()">×</button>
            </div>
            <div style="display:flex; gap:16px; margin-bottom:16px; font-size:13px;">
                <span id="auth-tab-login" onclick="setAuthMode('login')" style="cursor:pointer; font-weight:600; opacity:1;">Log In</span>
                <span id="auth-tab-signup" onclick="setAuthMode('signup')" style="cursor:pointer; font-weight:600; opacity:0.5;">Sign Up</span>
            </div>
            <div id="auth-error" style="display:none; background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); color:#fca5a5; font-size:12px; padding:8px 10px; border-radius:6px; margin-bottom:12px;"></div>
            <div id="auth-name-field" style="display:none; margin-bottom:10px;">
                <input type="text" id="auth-name" placeholder="Name (optional)" style="width:100%; padding:8px 10px; border-radius:6px; border:1px solid rgba(255,255,255,0.15); background:rgba(255,255,255,0.08); color:white; font-size:12px;"/>
            </div>
            <div style="margin-bottom:10px;">
                <input type="email" id="auth-email" placeholder="Email" style="width:100%; padding:8px 10px; border-radius:6px; border:1px solid rgba(255,255,255,0.15); background:rgba(255,255,255,0.08); color:white; font-size:12px;"/>
            </div>
            <div style="margin-bottom:14px;">
                <input type="password" id="auth-password" placeholder="Password" onkeydown="if(event.key==='Enter') submitAuthForm()" style="width:100%; padding:8px 10px; border-radius:6px; border:1px solid rgba(255,255,255,0.15); background:rgba(255,255,255,0.08); color:white; font-size:12px;"/>
            </div>
            <button id="auth-submit-btn" onclick="submitAuthForm()" style="width:100%; padding:10px; background:#1a237e; color:white; border:none; border-radius:6px; font-size:13px; cursor:pointer; font-weight:600;">Log In</button>
            <div style="display:flex; align-items:center; gap:10px; margin:16px 0; color:rgba(255,255,255,0.4); font-size:11px;">
                <div style="flex:1; height:1px; background:rgba(255,255,255,0.1);"></div>or<div style="flex:1; height:1px; background:rgba(255,255,255,0.1);"></div>
            </div>
            <div id="google-signin-btn" style="display:flex; justify-content:center;"></div>
        </div>
    </div>

    <div class="compare-panel" id="history-panel" style="display:none; top:70px;">
        <div class="compare-panel-title">Search History</div>
        <div id="history-items" style="max-height:240px; overflow-y:auto;"></div>
        <button class="compare-run-btn" onclick="clearHistoryList()" style="background:#7f1d1d; margin-top:8px;">Clear History</button>
    </div>

    <div class="compare-modal-backdrop" id="compare-modal">
        <div class="compare-modal-box">
            <div class="compare-modal-header">
                <h2>Field Comparison</h2>
                <button class="compare-modal-close" onclick="closeCompareModal()">×</button>
            </div>
            <canvas id="compare-chart" style="max-height:320px;"></canvas>
            <table id="compare-table"></table>
        </div>
    </div>

    <script>
        let chart;
        let marker;
        let heatLayer;
        let currentLng = null;
        let currentLat = null;
        let ndviVisible = false;
        let cdlVisible = false;
        let compareMode = false;
        let compareList = [];
        let compareChart;

        // ---------- Auth state ----------
        const GOOGLE_CLIENT_ID = '__GOOGLE_CLIENT_ID__';
        let authToken = localStorage.getItem('openet_token');
        let currentUser = null;

        function authHeaders() {
            return authToken ? { 'Authorization': 'Bearer ' + authToken } : {};
        }

        function r2(n) { return Math.round(parseFloat(n) * 100) / 100; }

        const map = L.map('map').setView([42.66, -77.05], 10);

        const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Tiles © Esri', maxZoom: 19
        });
        const labels = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png', {
            attribution: '© OpenStreetMap © CARTO', maxZoom: 19
        });
        satellite.addTo(map);
        labels.addTo(map);

        // Show cached locations as green dots
        async function loadCachedMarkers() {
            const start = document.getElementById('start').value;
            const end = document.getElementById('end').value;
            try {
                const res = await fetch('/api/et/cached?start_date=' + start + '&end_date=' + end);
                const locations = await res.json();
                locations.forEach(function(loc) {
                    L.circleMarker([loc.latitude, loc.longitude], {
                        radius: 8, color: '#4ade80', fillColor: '#4ade80',
                        fillOpacity: 0.7, weight: 2
                    }).addTo(map).bindTooltip('Cached ET data — click to load');
                });
                document.getElementById('heatmap-status').innerText = locations.length + ' cached locations ready — click green dots';
            } catch(e) {}
        }
        setTimeout(loadCachedMarkers, 500);

        const ndviLayer = L.tileLayer(
            'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_L3_NDVI_Monthly/default/2023-07-01/GoogleMapsCompatible_Level7/{z}/{y}/{x}.jpg',
            { attribution: 'NASA GIBS — MODIS NDVI July 2023', opacity: 1.0, maxZoom: 7 }
        );

        function toggleNDVI() {
            const btn = document.getElementById('ndvi-btn');
            const legend = document.getElementById('ndvi-legend');
            if (ndviVisible) {
                map.removeLayer(ndviLayer); ndviVisible = false;
                btn.innerText = 'NDVI Off'; btn.style.background = 'rgba(74,222,128,0.2)';
                legend.style.display = 'none';
            } else {
                ndviLayer.addTo(map); ndviVisible = true;
                btn.innerText = 'NDVI On'; btn.style.background = 'rgba(74,222,128,0.6)';
                legend.style.display = 'block';
                if (map.getZoom() > 7) map.setZoom(7);
            }
        }

        // CDL layer — this WMS server only supports EPSG:4326, not Leaflet's
        // default EPSG:3857 tile grid, so we request a single stretched
        // image matching the current viewport instead of tiling.
        let cdlOverlay = null;

        function updateCDLOverlay() {
            if (!cdlVisible) return;
            const b = map.getBounds();
            const size = map.getSize();
            const bbox = b.getWest() + ',' + b.getSouth() + ',' + b.getEast() + ',' + b.getNorth();
            const url = 'https://nassgeodata.gmu.edu/CropScapeService/wms_cdlall.cgi?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=cdl_2023&SRS=EPSG:4326&BBOX=' + bbox +
                '&WIDTH=' + Math.round(size.x) + '&HEIGHT=' + Math.round(size.y) + '&FORMAT=image/png&TRANSPARENT=TRUE';
            if (cdlOverlay) map.removeLayer(cdlOverlay);
            cdlOverlay = L.imageOverlay(url, b, { opacity: 0.75 }).addTo(map);
        }

        function toggleCDL() {
            const btn = document.getElementById('cdl-btn');
            const legend = document.getElementById('cdl-legend');
            if (cdlVisible) {
                if (cdlOverlay) map.removeLayer(cdlOverlay);
                cdlOverlay = null;
                map.off('moveend', updateCDLOverlay);
                cdlVisible = false;
                btn.innerText = 'Crop Type Off'; btn.style.background = 'rgba(251,191,36,0.2)';
                legend.style.display = 'none'; satellite.setOpacity(1.0);
            } else {
                satellite.setOpacity(0.5);
                cdlVisible = true;
                btn.innerText = 'Crop Type On'; btn.style.background = 'rgba(251,191,36,0.6)';
                legend.style.display = 'block';
                updateCDLOverlay();
                map.on('moveend', updateCDLOverlay);
            }
        }

        // USDM — U.S. Drought Monitor, served as a standard EPSG:3857 tile
        // service (unlike CDL's WMS), so this is a plain L.tileLayer, no
        // CRS workaround needed.
        const usdmLayer = L.tileLayer(
            'https://services5.arcgis.com/0OTVzJS4K09zlixn/ArcGIS/rest/services/US_Drought_Monitor/MapServer/tile/{z}/{y}/{x}',
            { attribution: 'NDMC / USDA / NOAA — U.S. Drought Monitor', opacity: 0.7, maxZoom: 19 }
        );
        let usdmVisible = false;

        function toggleUSDM() {
            const btn = document.getElementById('usdm-btn');
            const legend = document.getElementById('usdm-legend');
            if (usdmVisible) {
                map.removeLayer(usdmLayer); usdmVisible = false;
                btn.innerText = 'Drought Off'; btn.style.background = 'rgba(248,113,113,0.2)';
                legend.style.display = 'none';
            } else {
                usdmLayer.addTo(map); usdmVisible = true;
                btn.innerText = 'Drought On'; btn.style.background = 'rgba(248,113,113,0.6)';
                legend.style.display = 'block';
            }
        }

        // ---------- Compare Mode ----------

        function toggleCompareMode() {
            const btn = document.getElementById('compare-btn');
            const panel = document.getElementById('compare-list-panel');
            compareMode = !compareMode;
            if (compareMode) {
                btn.innerText = 'Compare On'; btn.style.background = 'rgba(96,165,250,0.6)';
                panel.style.display = 'block';
                loadSavedFieldsDropdown();
                loadComparisonSetsDropdown();
            } else {
                btn.innerText = 'Compare Off'; btn.style.background = 'rgba(96,165,250,0.2)';
                panel.style.display = 'none';
            }
        }

        async function loadSavedFieldsDropdown() {
            const select = document.getElementById('saved-fields-select');
            select.innerHTML = '<option value="">Load saved field...</option>';
            if (!authToken) return;
            try {
                const res = await fetch('/api/fields', { headers: authHeaders() });
                if (!res.ok) return;
                const fields = await res.json();
                fields.forEach(function(f) {
                    const opt = document.createElement('option');
                    opt.value = JSON.stringify(f);
                    opt.innerText = f.name;
                    select.appendChild(opt);
                });
            } catch(e) {}
        }

        function onSavedFieldSelected() {
            const select = document.getElementById('saved-fields-select');
            if (!select.value) return;
            const f = JSON.parse(select.value);
            addToCompareList(f.name, f.longitude, f.latitude);
            select.value = '';
        }

        function addToCompareList(label, lng, lat) {
            compareList.push({ label: label, longitude: lng, latitude: lat });
            renderCompareItems();
        }

        function removeFromCompareList(index) {
            compareList.splice(index, 1);
            renderCompareItems();
        }

        async function saveCompareItem(index) {
            if (!authToken) { alert('Sign in to save fields.'); openAuthModal(); return; }
            const item = compareList[index];
            try {
                await fetch('/api/fields', {
                    method: 'POST',
                    headers: Object.assign({ 'Content-Type': 'application/json' }, authHeaders()),
                    body: JSON.stringify({ name: item.label, longitude: item.longitude, latitude: item.latitude })
                });
                loadSavedFieldsDropdown();
            } catch(e) {
                alert('Failed to save field.');
            }
        }

        async function saveComparisonSet() {
            if (!authToken) { alert('Sign in to save comparison sets.'); openAuthModal(); return; }
            if (compareList.length === 0) { alert('Add at least one field first.'); return; }
            const name = prompt('Name this comparison set:', 'My Comparison ' + new Date().toLocaleDateString());
            if (!name) return;
            try {
                await fetch('/api/comparison-sets', {
                    method: 'POST',
                    headers: Object.assign({ 'Content-Type': 'application/json' }, authHeaders()),
                    body: JSON.stringify({
                        name: name,
                        fields: compareList.map(function(item) { return { label: item.label, longitude: item.longitude, latitude: item.latitude }; })
                    })
                });
                loadComparisonSetsDropdown();
            } catch(e) {
                alert('Failed to save comparison set.');
            }
        }

        async function loadComparisonSetsDropdown() {
            const select = document.getElementById('comparison-sets-select');
            select.innerHTML = '<option value="">Load saved set...</option>';
            if (!authToken) return;
            try {
                const res = await fetch('/api/comparison-sets', { headers: authHeaders() });
                if (!res.ok) return;
                const sets = await res.json();
                sets.forEach(function(s) {
                    const opt = document.createElement('option');
                    opt.value = JSON.stringify(s.fields);
                    opt.innerText = s.name;
                    select.appendChild(opt);
                });
            } catch(e) {}
        }

        function onComparisonSetSelected() {
            const select = document.getElementById('comparison-sets-select');
            if (!select.value) return;
            const fields = JSON.parse(select.value);
            fields.forEach(function(f) { addToCompareList(f.label, f.longitude, f.latitude); });
            select.value = '';
        }

        function renderCompareItems() {
            document.getElementById('compare-count').innerText = compareList.length;
            const container = document.getElementById('compare-items');
            container.innerHTML = compareList.map(function(item, i) {
                return '<div class="compare-item">' +
                    '<span class="name">' + item.label + '</span>' +
                    '<span class="actions">' +
                    '<button onclick="saveCompareItem(' + i + ')" title="Save field" style="color:#4ade80;">💾</button>' +
                    '<button onclick="removeFromCompareList(' + i + ')" title="Remove" style="color:#ef4444;">×</button>' +
                    '</span></div>';
            }).join('');
        }

        async function runComparison() {
            if (compareList.length === 0) { alert('Add at least one field first.'); return; }
            if (compareList.length > 8) { alert('Maximum 8 fields per comparison.'); return; }
            const start = document.getElementById('start').value;
            const end = document.getElementById('end').value;
            const points = compareList.map(function(item) {
                return { label: item.label, longitude: item.longitude, latitude: item.latitude };
            });
            try {
                const res = await fetch('/api/et/compare', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ points: points, start_date: start, end_date: end })
                });
                const data = await res.json();
                renderCompareModal(data.fields);
            } catch(e) {
                alert('Comparison failed — check console.');
            }
        }

        function renderCompareModal(fields) {
            document.getElementById('compare-modal').style.display = 'flex';
            const monthLabels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
            const palette = ['#60a5fa','#4ade80','#f472b6','#fbbf24','#a78bfa','#fb923c','#34d399','#f87171'];

            const datasets = fields.filter(function(f){ return !f.error; }).map(function(f, i) {
                return {
                    label: f.label,
                    data: f.monthly_avg,
                    borderColor: palette[i % palette.length],
                    backgroundColor: palette[i % palette.length],
                    fill: false,
                    tension: 0.3
                };
            });

            if (compareChart) compareChart.destroy();
            compareChart = new Chart(document.getElementById('compare-chart'), {
                type: 'line',
                data: { labels: monthLabels, datasets: datasets },
                options: {
                    responsive: true,
                    plugins: { legend: { labels: { color: '#aaa' } } },
                    scales: {
                        y: { ticks: { color: '#aaa' }, grid: { color: 'rgba(255,255,255,0.06)' }, title: { display: true, text: 'Avg ET (in)', color: '#aaa' } },
                        x: { ticks: { color: '#aaa' }, grid: { color: 'rgba(255,255,255,0.06)' } }
                    }
                }
            });

            const table = document.getElementById('compare-table');
            let html = '<tr style="border-bottom:1px solid rgba(255,255,255,0.15);color:#90caf9;text-align:left;">' +
                '<th style="padding:6px;">Field</th><th style="padding:6px;">Total ET (in)</th><th style="padding:6px;">Avg Monthly (in)</th><th style="padding:6px;">Anomalies</th></tr>';
            fields.forEach(function(f) {
                if (f.error) {
                    html += '<tr><td style="padding:6px;">' + f.label + '</td><td colspan="3" style="padding:6px;color:#ef4444;">' + f.error + '</td></tr>';
                } else {
                    html += '<tr style="border-bottom:1px solid rgba(255,255,255,0.05);"><td style="padding:6px;">' + f.label + '</td><td style="padding:6px;">' + f.total_et + '</td><td style="padding:6px;">' + f.avg_monthly_et + '</td><td style="padding:6px;' + (f.anomaly_count > 0 ? 'color:#ef4444;' : '') + '">' + f.anomaly_count + '</td></tr>';
                }
            });
            table.innerHTML = html;
        }

        function closeCompareModal() {
            document.getElementById('compare-modal').style.display = 'none';
        }

        const drawnItems = new L.FeatureGroup();
        map.addLayer(drawnItems);
        const drawControl = new L.Control.Draw({
            draw: {
                polygon: { allowIntersection: false, showArea: true, shapeOptions: { color: '#4CAF50', fillOpacity: 0.2 } },
                rectangle: { shapeOptions: { color: '#4CAF50', fillOpacity: 0.2 } },
                polyline: false, circle: false, circlemarker: false, marker: false
            },
            edit: { featureGroup: drawnItems }
        });
        map.addControl(drawControl);

        // Cap how large a field a user can draw. Beyond this, the 9-point
        // sampling stops being representative of a single "field" and just
        // burns API quota across an increasingly coarse average.
        const MAX_POLYGON_AREA_M2 = 5000000; // 5 km²

        map.on(L.Draw.Event.CREATED, function(e) {
            const latlngs = e.layer.getLatLngs ? e.layer.getLatLngs()[0] : null;
            if (latlngs && window.L.GeometryUtil && window.L.GeometryUtil.geodesicArea) {
                const areaM2 = L.GeometryUtil.geodesicArea(latlngs);
                if (areaM2 > MAX_POLYGON_AREA_M2) {
                    alert('That area is too large (' + (areaM2 / 1000000).toFixed(1) + ' km²). Please draw a smaller field — max is 5 km².');
                    return;
                }
            }

            const bounds = e.layer.getBounds();
            const center = bounds.getCenter();
            const lat = r2(center.lat).toFixed(2);
            const lng = r2(center.lng).toFixed(2);

            if (compareMode) {
                drawnItems.addLayer(e.layer);
                const label = prompt('Name this field:', 'Field ' + (compareList.length + 1));
                if (label) addToCompareList(label, parseFloat(lng), parseFloat(lat));
                return;
            }

            drawnItems.clearLayers();
            drawnItems.addLayer(e.layer);
            currentLat = lat;
            currentLng = lng;
            const samplePoints = [{ lat: lat, lng: lng }];
            document.getElementById('coords-text').innerText = 'Polygon center: ' + lat + ', ' + lng;
            loadPolygonChart(samplePoints, center);
        });

        map.on('click', function(e) {
            const lat = r2(e.latlng.lat).toFixed(2);
            const lng = r2(e.latlng.lng).toFixed(2);

            if (compareMode) {
                const label = prompt('Name this field:', 'Field ' + (compareList.length + 1));
                if (label) addToCompareList(label, parseFloat(lng), parseFloat(lat));
                return;
            }

            currentLat = lat;
            currentLng = lng;
            loadChart(lng, lat);
        });

        // Heatmap: two explicit modes.
        // "Intensity" = total ET summed over the date range (raw water use magnitude).
        // "Anomaly"   = worst z-score seen at that location (how unusual its most
        //               extreme month was) — this is the one that actually answers
        //               "does the heatmap show anomalies?"
        let heatmapVisible = false;
        let heatmapMode = 'intensity'; // 'intensity' | 'anomaly'

        function toggleHeatmap() {
            const btn = document.getElementById('heatmap-btn');
            const modeBtn = document.getElementById('heatmap-mode-btn');
            heatmapVisible = !heatmapVisible;
            if (heatmapVisible) {
                btn.innerText = 'Heatmap On';
                modeBtn.style.display = 'inline-block';
                loadHeatmapData();
            } else {
                btn.innerText = 'Heatmap Off';
                modeBtn.style.display = 'none';
                if (heatLayer) { map.removeLayer(heatLayer); heatLayer = null; }
                document.getElementById('heatmap-status').innerText = '';
            }
        }

        function toggleHeatmapMode() {
            heatmapMode = heatmapMode === 'intensity' ? 'anomaly' : 'intensity';
            const modeBtn = document.getElementById('heatmap-mode-btn');
            const title = document.getElementById('heatmap-legend-title');
            const labels = document.getElementById('heatmap-legend-labels');
            if (heatmapMode === 'anomaly') {
                modeBtn.innerText = 'Mode: Anomaly';
                title.innerText = 'Anomaly Severity';
                labels.innerHTML = '<span>Normal</span><span>Extreme</span>';
            } else {
                modeBtn.innerText = 'Mode: Intensity';
                title.innerText = 'ET Intensity';
                labels.innerHTML = '<span>Low</span><span>High</span>';
            }
            if (heatmapVisible) loadHeatmapData();
        }

        async function loadHeatmapData() {
            document.getElementById('heatmap-status').innerText = 'Loading heatmap from cache...';
            const start = document.getElementById('start').value;
            const end = document.getElementById('end').value;

            try {
                const res = await fetch('/api/et/cached?start_date=' + start + '&end_date=' + end);
                const locations = await res.json();

                if (locations.length === 0) {
                    document.getElementById('heatmap-status').innerText = 'No cached data available.';
                    return;
                }

                const results = [];
                let loaded = 0;
                for (const loc of locations) {
                    try {
                        const r = await fetch('/api/et/point?longitude=' + loc.longitude + '&latitude=' + loc.latitude + '&start_date=' + start + '&end_date=' + end);
                        if (r.ok) {
                            const data = await r.json();
                            if (Array.isArray(data)) {
                                let value;
                                if (heatmapMode === 'anomaly') {
                                    // worst-case |z-score| at this location — this is
                                    // what actually represents "how anomalous"
                                    value = data.reduce(function(max, d) { return Math.max(max, Math.abs(d.z_score || 0)); }, 0);
                                } else {
                                    value = data.reduce(function(sum, d) { return sum + d.et; }, 0);
                                }
                                results.push([loc.latitude, loc.longitude, value]);
                                loaded++;
                                document.getElementById('heatmap-status').innerText = 'Loading heatmap... ' + loaded + ' / ' + locations.length;
                            }
                        }
                    } catch(e) {}
                }

                if (heatLayer) map.removeLayer(heatLayer);
                if (results.length > 0) {
                    heatLayer = L.heatLayer(results, {
                        radius: 80, blur: 60, maxZoom: 12,
                        gradient: { 0.0: '#000080', 0.2: '#0000ff', 0.4: '#00ffff', 0.6: '#00ff00', 0.8: '#ffff00', 1.0: '#ff0000' }
                    }).addTo(map);
                    const modeLabel = heatmapMode === 'anomaly' ? 'anomaly severity' : 'ET intensity';
                    document.getElementById('heatmap-status').innerText = 'Heatmap (' + modeLabel + ') loaded from ' + results.length + ' cached locations — no quota used!';
                }
            } catch(e) {
                document.getElementById('heatmap-status').innerText = 'Error loading heatmap.';
            }
        }

        async function loadChart(lng, lat) {
            const start = document.getElementById('start').value;
            const end = document.getElementById('end').value;
            document.getElementById('coords-text').innerText = 'Lat: ' + lat + ', Lng: ' + lng;
            document.getElementById('empty-state').style.display = 'none';
            document.getElementById('loading-wrap').style.display = 'flex';
            document.getElementById('loading-text').innerText = 'Loading satellite data...';
            document.getElementById('chart-wrapper').style.display = 'none';
            document.getElementById('anomaly-alert').style.display = 'none';
            document.getElementById('stats-row').style.display = 'none';
            document.getElementById('annual-section').style.display = 'none';
            document.getElementById('download-btn').style.display = 'none';
            try {
                const res = await fetch('/api/et/point?longitude=' + lng + '&latitude=' + lat + '&start_date=' + start + '&end_date=' + end, { headers: authHeaders() });
                const data = await res.json();
                if (!Array.isArray(data)) throw new Error('Invalid response');
                renderChart(data, lat, lng);
            } catch(e) {
                document.getElementById('loading-wrap').style.display = 'none';
                document.getElementById('empty-state').style.display = 'flex';
                document.getElementById('empty-state').querySelector('p').innerText = 'No data for this location. Try clicking a green dot.';
            }
        }

        async function loadPolygonChart(points, center) {
            const start = document.getElementById('start').value;
            const end = document.getElementById('end').value;
            document.getElementById('empty-state').style.display = 'none';
            document.getElementById('loading-wrap').style.display = 'flex';
            document.getElementById('loading-text').innerText = 'Loading polygon data...';
            document.getElementById('chart-wrapper').style.display = 'none';
            document.getElementById('anomaly-alert').style.display = 'none';
            document.getElementById('stats-row').style.display = 'none';
            document.getElementById('annual-section').style.display = 'none';
            document.getElementById('download-btn').style.display = 'none';

            try {
                const allData = [];
                for (const p of points) {
                    try {
                        const res = await fetch('/api/et/point?longitude=' + p.lng + '&latitude=' + p.lat + '&start_date=' + start + '&end_date=' + end, { headers: authHeaders() });
                        if (res.ok) {
                            const data = await res.json();
                            if (Array.isArray(data) && data.length > 0) allData.push(data);
                        }
                    } catch(e) {}
                }

                if (allData.length === 0) throw new Error('No data');

                const timeMap = {};
                allData.forEach(function(pointData) {
                    pointData.forEach(function(d) {
                        if (!timeMap[d.time]) timeMap[d.time] = [];
                        timeMap[d.time].push(d.et);
                    });
                });

                const mergedData = allData[0].map(function(d) {
                    const vals = timeMap[d.time] || [d.et];
                    const avgET = vals.reduce(function(a, b) { return a + b; }, 0) / vals.length;
                    return Object.assign({}, d, { et: Math.round(avgET * 100) / 100 });
                });

                currentLat = r2(center.lat).toFixed(2);
                currentLng = r2(center.lng).toFixed(2);
                renderChart(mergedData, currentLat, currentLng, true, allData.length);
            } catch(e) {
                document.getElementById('loading-wrap').style.display = 'none';
                document.getElementById('empty-state').style.display = 'flex';
                document.getElementById('empty-state').querySelector('p').innerText = 'No data for this area. Try clicking a green dot instead.';
            }
        }

        function renderChart(data, lat, lng, isPolygon, numPoints) {
            document.getElementById('loading-wrap').style.display = 'none';
            document.getElementById('chart-wrapper').style.display = 'block';
            document.getElementById('stats-row').style.display = 'grid';
            document.getElementById('annual-section').style.display = 'block';
            document.getElementById('download-btn').style.display = 'block';

            window.currentETData = data;
            const values = data.map(function(d) { return d.et; });
            const total = values.reduce(function(a, b) { return a + b; }, 0);
            const avg = total / values.length;
            const anomalies = data.filter(function(d) { return d.anomaly; });

            document.getElementById('stat-total').innerText = total.toFixed(1);
            document.getElementById('stat-avg').innerText = avg.toFixed(2);
            document.getElementById('stat-anomalies').innerText = anomalies.length;

            const anomalyCard = document.getElementById('stat-anomaly-card');
            if (anomalies.length > 0) { anomalyCard.classList.add('anomaly'); }
            else { anomalyCard.classList.remove('anomaly'); }

            let anomalyMsg = '';
            if (anomalies.length > 0) {
                const alertBox = document.getElementById('anomaly-alert');
                const highAnomalies = anomalies.filter(function(d) { return d.anomaly_type === 'high'; });
                const lowAnomalies = anomalies.filter(function(d) { return d.anomaly_type === 'low'; });
                const prefix = isPolygon ? 'Polygon anomaly: ' : 'Anomaly detected: ';
                anomalyMsg = prefix;
                if (highAnomalies.length > 0) anomalyMsg += 'unusually high ET in ' + highAnomalies.map(function(d) { return d.time.slice(0,7) + ' (' + d.normalized + '%)'; }).join(', ') + '. ';
                if (lowAnomalies.length > 0) anomalyMsg += 'unusually low ET in ' + lowAnomalies.map(function(d) { return d.time.slice(0,7) + ' (' + d.normalized + '%)'; }).join(', ') + '.';
                alertBox.innerText = anomalyMsg;
                alertBox.className = highAnomalies.length > 0 ? 'anomaly-box' : 'anomaly-box low';
                alertBox.style.display = 'block';
            }

            if (marker) marker.remove();
            const coordsDot = document.getElementById('coords-dot');
            if (anomalies.length > 0) {
                coordsDot.className = 'coords-dot anomaly';
                marker = L.circleMarker([lat, lng], { radius: 14, color: 'white', fillColor: '#ef4444', fillOpacity: 0.9, weight: 2 }).addTo(map);
                marker.bindPopup('<b style="color:#ef4444;">⚠ Anomaly Detected</b><br>' + anomalyMsg + '<br><small>Lat: ' + lat + ', Lng: ' + lng + '</small>').openPopup();
            } else {
                coordsDot.className = 'coords-dot';
                marker = L.circleMarker([lat, lng], { radius: 8, color: 'white', fillColor: '#4CAF50', fillOpacity: 1, weight: 2 }).addTo(map);
                marker.bindPopup('<b style="color:#4CAF50;">✓ Normal ET levels</b><br><small>Lat: ' + lat + ', Lng: ' + lng + '</small>');
            }

            // Group by year
            const years = {};
            data.forEach(function(d) {
                const year = d.time.slice(0, 4);
                if (!years[year]) years[year] = [];
                years[year].push({ et: d.et, anomaly: d.anomaly, anomaly_type: d.anomaly_type, normalized: d.normalized });
            });

            const yearColors = { '2021': 'rgba(99,179,237,0.85)', '2022': 'rgba(154,205,100,0.85)', '2023': 'rgba(246,173,85,0.85)', '2024': 'rgba(203,139,255,0.85)' };
            const yearList = Object.keys(years).sort();

            // Annual ET summary cards
            const annualRow = document.getElementById('annual-row');
            annualRow.innerHTML = yearList.map(function(year) {
                const annualTotal = years[year].reduce(function(sum, d) { return sum + d.et; }, 0).toFixed(1);
                const color = yearColors[year] || '#90caf9';
                const hasAnom = years[year].some(function(d) { return d.anomaly; });
                return '<div class="annual-card" style="border-color:' + (hasAnom ? 'rgba(239,68,68,0.3)' : 'rgba(255,255,255,0.08)') + '">' +
                    '<div class="year-label">' + year + '</div>' +
                    '<div class="year-val" style="color:' + color + '">' + annualTotal + '"</div>' +
                    '<div class="year-unit">in/year</div>' +
                    '</div>';
            }).join('');

            if (chart) chart.destroy();

            const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const datasets = yearList.map(function(year) {
                return {
                    label: year,
                    data: years[year].map(function(d) { return d.et; }),
                    backgroundColor: years[year].map(function(d) {
                        if (d.anomaly && d.anomaly_type === 'high') return 'rgba(239,68,68,0.85)';
                        if (d.anomaly && d.anomaly_type === 'low') return 'rgba(234,179,8,0.85)';
                        return yearColors[year] || 'rgba(37,99,235,0.8)';
                    }),
                    borderColor: yearColors[year] || 'rgba(37,99,235,0.8)',
                    borderWidth: 1, borderRadius: 3
                };
            });

            chart = new Chart(document.getElementById('chart'), {
                type: 'bar',
                data: { labels: monthLabels, datasets: datasets },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: true, labels: { color: '#aaa', font: { size: 11 } } },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    const year = ctx.dataset.label;
                                    const val = ctx.parsed.y.toFixed(2);
                                    const d = years[year][ctx.dataIndex];
                                    let label = year + ': ' + val + ' in';
                                    if (d && d.normalized) label += ' (' + d.normalized + '% of avg)';
                                    if (d && d.anomaly) label += ' ⚠ ' + d.anomaly_type;
                                    return label;
                                }
                            }
                        }
                    },
                    scales: {
                        y: { beginAtZero: true, ticks: { color: '#aaa' }, grid: { color: 'rgba(255,255,255,0.06)' }, title: { display: true, text: 'ET (inches)', color: '#aaa', font: { size: 11 } } },
                        x: { ticks: { color: '#aaa', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.06)' }, title: { display: true, text: 'Month', color: '#aaa' } }
                    }
                }
            });
        }

        function downloadReport() {
            if (!currentLng || !currentLat) return;
            const start = document.getElementById('start').value;
            const end = document.getElementById('end').value;
            const location = document.getElementById('search').value || 'Finger Lakes';
            window.open('/api/reports/csv?longitude=' + currentLng + '&latitude=' + currentLat + '&start_date=' + start + '&end_date=' + end + '&location_name=' + encodeURIComponent(location));
        }

        async function searchLocation() {
            const query = document.getElementById('search').value;
            if (!query) return;
            const res = await fetch('https://nominatim.openstreetmap.org/search?q=' + encodeURIComponent(query) + '&format=json&limit=1');
            const data = await res.json();
            if (data.length > 0) { map.setView([parseFloat(data[0].lat), parseFloat(data[0].lon)], 10); }
            else { alert('Location not found.'); }
        }

        // ---------- Auth UI ----------

        function renderAuthUI() {
            const container = document.getElementById('auth-section');
            if (currentUser) {
                container.innerHTML =
                    '<span style="font-size:11px;opacity:0.85;">' + (currentUser.name || currentUser.email) + '</span>' +
                    '<button class="btn" onclick="logout()" style="background:rgba(255,255,255,0.1);color:white;border:1px solid rgba(255,255,255,0.2);">Log Out</button>';
            } else {
                container.innerHTML = '<button class="btn" onclick="openAuthModal()" style="background:rgba(255,255,255,0.15);color:white;border:1px solid rgba(255,255,255,0.3);">Sign In</button>';
            }
        }

        function logout() {
            authToken = null;
            currentUser = null;
            localStorage.removeItem('openet_token');
            renderAuthUI();
        }

        function openAuthModal() {
            document.getElementById('auth-modal').style.display = 'flex';
        }

        function closeAuthModal() {
            document.getElementById('auth-modal').style.display = 'none';
            document.getElementById('auth-error').style.display = 'none';
        }

        let authMode = 'login';
        function setAuthMode(mode) {
            authMode = mode;
            document.getElementById('auth-name-field').style.display = mode === 'signup' ? 'block' : 'none';
            document.getElementById('auth-submit-btn').innerText = mode === 'signup' ? 'Sign Up' : 'Log In';
            document.getElementById('auth-tab-login').style.opacity = mode === 'login' ? '1' : '0.5';
            document.getElementById('auth-tab-signup').style.opacity = mode === 'signup' ? '1' : '0.5';
        }

        async function submitAuthForm() {
            const email = document.getElementById('auth-email').value.trim();
            const password = document.getElementById('auth-password').value;
            const name = document.getElementById('auth-name').value.trim();
            const errorBox = document.getElementById('auth-error');
            errorBox.style.display = 'none';
            if (!email || !password) return;

            const endpoint = authMode === 'signup' ? '/api/auth/signup' : '/api/auth/login';
            const body = authMode === 'signup' ? { email: email, password: password, name: name } : { email: email, password: password };
            try {
                const res = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                const data = await res.json();
                if (!res.ok) {
                    errorBox.innerText = data.detail || 'Something went wrong.';
                    errorBox.style.display = 'block';
                    return;
                }
                authToken = data.token;
                currentUser = data.user;
                localStorage.setItem('openet_token', authToken);
                closeAuthModal();
                renderAuthUI();
                loadSavedFieldsDropdown();
                loadComparisonSetsDropdown();
            } catch(e) {
                errorBox.innerText = 'Network error — try again.';
                errorBox.style.display = 'block';
            }
        }

        async function handleGoogleCredential(response) {
            try {
                const res = await fetch('/api/auth/google', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id_token: response.credential })
                });
                const data = await res.json();
                if (!res.ok) {
                    alert(data.detail || 'Google sign-in failed.');
                    return;
                }
                authToken = data.token;
                currentUser = data.user;
                localStorage.setItem('openet_token', authToken);
                closeAuthModal();
                renderAuthUI();
                loadSavedFieldsDropdown();
                loadComparisonSetsDropdown();
            } catch(e) {
                alert('Google sign-in failed — try again.');
            }
        }

        async function checkAuth() {
            if (!authToken) { renderAuthUI(); return; }
            try {
                const res = await fetch('/api/auth/me', { headers: authHeaders() });
                if (res.ok) {
                    currentUser = await res.json();
                } else {
                    authToken = null;
                    localStorage.removeItem('openet_token');
                }
            } catch(e) {}
            renderAuthUI();
        }

        window.addEventListener('load', function() {
            checkAuth();
            if (window.google && GOOGLE_CLIENT_ID) {
                google.accounts.id.initialize({ client_id: GOOGLE_CLIENT_ID, callback: handleGoogleCredential });
                google.accounts.id.renderButton(document.getElementById('google-signin-btn'), { theme: 'outline', size: 'medium', width: 240 });
            }
        });

        // ---------- History panel ----------

        let historyVisible = false;
        function toggleHistoryPanel() {
            if (!authToken) { alert('Sign in to view search history.'); openAuthModal(); return; }
            historyVisible = !historyVisible;
            document.getElementById('history-panel').style.display = historyVisible ? 'block' : 'none';
            if (historyVisible) loadHistory();
        }

        async function loadHistory() {
            const container = document.getElementById('history-items');
            container.innerHTML = '<div style="font-size:11px;opacity:0.5;">Loading...</div>';
            try {
                const res = await fetch('/api/history', { headers: authHeaders() });
                if (!res.ok) { container.innerHTML = '<div style="font-size:11px;opacity:0.5;">Could not load history.</div>'; return; }
                const entries = await res.json();
                if (entries.length === 0) {
                    container.innerHTML = '<div style="font-size:11px;opacity:0.5;">No searches yet — click any field on the map.</div>';
                    return;
                }
                container.innerHTML = entries.map(function(h) {
                    const dateLabel = new Date(h.created_at).toLocaleDateString();
                    return '<div class="compare-item" style="cursor:pointer;" onclick="loadFromHistory(' + h.longitude + ',' + h.latitude + ',\\'' + h.start_date + '\\',\\'' + h.end_date + '\\')">' +
                        '<span class="name">' + h.latitude.toFixed(2) + ', ' + h.longitude.toFixed(2) + '</span>' +
                        '<span style="font-size:9px;opacity:0.5;">' + dateLabel + '</span>' +
                        '</div>';
                }).join('');
            } catch(e) {
                container.innerHTML = '<div style="font-size:11px;opacity:0.5;">Could not load history.</div>';
            }
        }

        function loadFromHistory(lng, lat, start, end) {
            document.getElementById('start').value = start;
            document.getElementById('end').value = end;
            loadChart(lng, lat);
        }

        async function clearHistoryList() {
            if (!confirm('Clear all search history?')) return;
            try {
                await fetch('/api/history', { method: 'DELETE', headers: authHeaders() });
                loadHistory();
            } catch(e) {}
        }

        // AI Assistant (free tier): no external API call at all. Every
        // answer is computed locally from window.currentETData, which is
        // already loaded whenever a field's chart is showing. Zero cost,
        // zero dependency on any funded API key.

        function addChatBubble(text, fromUser) {
            const messages = document.getElementById('chat-messages');
            const style = fromUser
                ? 'background:rgba(37,99,235,0.2);border-radius:8px;padding:8px 10px;font-size:12px;align-self:flex-end;max-width:85%;'
                : 'background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:8px 10px;font-size:12px;max-width:95%;line-height:1.5;';
            messages.innerHTML += '<div style="' + style + '">' + text + '</div>';
            messages.scrollTop = messages.scrollHeight;
        }

        function answerPreset(type) {
            const data = window.currentETData;
            const questionLabels = {
                summarize: 'Summarize this field',
                anomalies: 'Explain anomalies',
                compare: 'Compare years'
            };
            addChatBubble(questionLabels[type], true);

            if (!data || data.length === 0) {
                addChatBubble('No field is loaded yet — click a green dot or draw a polygon on the map first, then ask again.', false);
                return;
            }

            if (type === 'summarize') {
                const total = data.reduce(function(sum, d) { return sum + d.et; }, 0);
                const avg = total / data.length;
                const anomalyCount = data.filter(function(d) { return d.anomaly; }).length;
                const start = document.getElementById('start').value;
                const end = document.getElementById('end').value;
                addChatBubble(
                    'From ' + start + ' to ' + end + ', total evapotranspiration was <b>' + total.toFixed(1) + ' inches</b>, ' +
                    'averaging <b>' + avg.toFixed(2) + ' inches/month</b>. ' +
                    (anomalyCount > 0
                        ? anomalyCount + ' month' + (anomalyCount > 1 ? 's' : '') + ' showed anomalous water use — see "Explain anomalies" for details.'
                        : 'No anomalous months were detected in this period.'),
                    false
                );
            }

            if (type === 'anomalies') {
                const anomalies = data.filter(function(d) { return d.anomaly; });
                if (anomalies.length === 0) {
                    addChatBubble('No anomalies detected — every month fell within the normal range compared to that same month in other years.', false);
                    return;
                }
                const lines = anomalies.map(function(d) {
                    return d.time.slice(0, 7) + ': ' + (d.anomaly_type === 'high' ? 'unusually high' : 'unusually low') + ' ET (' + d.normalized + '% of typical)';
                });
                addChatBubble(
                    '<b>' + anomalies.length + ' anomal' + (anomalies.length > 1 ? 'ies' : 'y') + ' detected:</b><br>' + lines.join('<br>'),
                    false
                );
            }

            if (type === 'compare') {
                const years = {};
                data.forEach(function(d) {
                    const year = d.time.slice(0, 4);
                    if (!years[year]) years[year] = 0;
                    years[year] += d.et;
                });
                const yearList = Object.keys(years).sort();
                if (yearList.length < 2) {
                    addChatBubble('Only one year (' + yearList[0] + ') is in the selected date range — pick a wider range to compare across years.', false);
                    return;
                }
                const lines = yearList.map(function(y) { return y + ': ' + years[y].toFixed(1) + ' in'; });
                const first = years[yearList[0]];
                const last = years[yearList[yearList.length - 1]];
                const pctChange = first > 0 ? (((last - first) / first) * 100).toFixed(1) : 'N/A';
                addChatBubble(
                    lines.join('<br>') + '<br><br>' +
                    yearList[yearList.length - 1] + ' vs ' + yearList[0] + ': ' +
                    (last >= first ? '+' : '') + pctChange + '% change in total annual ET.',
                    false
                );
            }
        }
    </script>
</body>
</html>
"""
    html = html.replace("__GOOGLE_CLIENT_ID__", os.getenv("GOOGLE_CLIENT_ID", ""))
    return html
