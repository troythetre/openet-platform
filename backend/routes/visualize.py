from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/chart", response_class=HTMLResponse)
def chart():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>OpenET Water Use Platform</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; background: #0d0d1a; color: white; }
        header { background: linear-gradient(135deg, #1a237e 0%, #283593 100%); color: white; padding: 12px 24px; display: flex; align-items: center; gap: 16px; border-bottom: 2px solid #b22222; }
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
        .main { display: grid; grid-template-columns: 1fr 380px; height: calc(100vh - 64px); }
        #map { width: 100%; height: 100%; }
        .side-panel { background: #111827; display: flex; flex-direction: column; overflow: hidden; border-left: 1px solid rgba(255,255,255,0.08); }
        .side-panel-header { padding: 16px 20px 12px; border-bottom: 1px solid rgba(255,255,255,0.08); }
        .side-panel-header h2 { font-size: 13px; font-weight: 600; color: #90caf9; letter-spacing: 0.5px; text-transform: uppercase; }
        .side-panel-body { padding: 16px 20px; flex: 1; display: flex; flex-direction: column; gap: 14px; overflow-y: auto; }
        .stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
        .stat-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 10px 12px; text-align: center; }
        .stat-card .val { font-size: 18px; font-weight: 600; color: #90caf9; }
        .stat-card .lbl { font-size: 10px; color: rgba(255,255,255,0.5); margin-top: 2px; }
        .stat-card.anomaly .val { color: #ef4444; }
        .stat-card.anomaly { border-color: rgba(239,68,68,0.3); background: rgba(239,68,68,0.05); }
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
        .quota-warning { background: rgba(234,179,8,0.1); border: 1px solid rgba(234,179,8,0.3); border-radius: 8px; padding: 8px 12px; font-size: 11px; color: #fde047; text-align: center; }
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
            <input type="text" id="start" value="2021-01-01"/>
            <label>To</label>
            <input type="text" id="end" value="2023-12-31"/>
            <button class="btn btn-heatmap" onclick="refreshHeatmap()">Load Heatmap</button>
        </div>
    </header>

    <div class="main">
        <div style="position:relative;">
            <div id="map"></div>
            <div class="map-overlay">
                <div style="font-weight:500;margin-bottom:2px;">ET Intensity</div>
                <div class="color-bar"></div>
                <div class="color-labels"><span>Low</span><span>High</span></div>
            </div>
        </div>
        <div class="side-panel">
            <div class="side-panel-header">
                <h2>Monthly ET Analysis</h2>
            </div>
            <div class="side-panel-body">
                <div class="coords" id="coords">
                    <span class="coords-dot" id="coords-dot"></span>
                    <span id="coords-text">Click on the map to select a location</span>
                </div>

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

                <div class="legend">
                    <div class="legend-item"><div class="legend-dot" style="background:rgba(37,99,235,0.8);"></div>Normal</div>
                    <div class="legend-item"><div class="legend-dot" style="background:#ef4444;"></div>High anomaly</div>
                    <div class="legend-item"><div class="legend-dot" style="background:#eab308;"></div>Low anomaly</div>
                </div>

                <div id="anomaly-alert" style="display:none;" class="anomaly-box"></div>

                <div class="empty-state" id="empty-state">
                    <div class="icon">🍇</div>
                    <p>Click anywhere on the map to load ET data for that location</p>
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
                    <div id="chat-messages" style="max-height:180px; overflow-y:auto; display:flex; flex-direction:column; gap:8px; margin-bottom:10px;"></div>
                    <div style="display:flex; gap:6px;">
                        <input type="text" id="chat-input" placeholder="Ask about the ET data..."
                            style="flex:1; padding:8px 10px; border-radius:6px; border:1px solid rgba(255,255,255,0.15); background:rgba(255,255,255,0.08); color:white; font-size:12px;"
                            onkeydown="if(event.key==='Enter') sendChat()"/>
                        <button onclick="sendChat()" style="padding:8px 12px; background:#1a237e; color:white; border:none; border-radius:6px; font-size:12px; cursor:pointer;">Send</button>
                    </div>
                </div>
                <div class="heatmap-status" id="heatmap-status"></div>
            </div>
        </div>
    </div>

    <script>
        let chart;
        let marker;
        let heatLayer;
        let currentLng = null;
        let currentLat = null;

        // Default: Finger Lakes wine region — confirmed OpenET coverage
        const map = L.map('map').setView([42.66, -77.05], 10);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '© OpenStreetMap © CARTO', maxZoom: 19
        }).addTo(map);

        // Only load chart on explicit click — never auto-trigger
        map.on('click', function(e) {
            currentLat = e.latlng.lat.toFixed(5);
            currentLng = e.latlng.lng.toFixed(5);
            loadChart(currentLng, currentLat);
        });

        // Heatmap only loads when user explicitly clicks button — never on moveend
        async function refreshHeatmap() {
            await loadHeatmap(map.getBounds());
        }

        async function loadHeatmap(bounds) {
            document.getElementById('heatmap-status').innerText = 'Loading heatmap... (uses API quota)';
            const start = document.getElementById('start').value;
            const end = document.getElementById('end').value;
            const north = bounds.getNorth(), south = bounds.getSouth();
            const east = bounds.getEast(), west = bounds.getWest();
            const gridSize = 3;
            const latStep = (north - south) / gridSize;
            const lngStep = (east - west) / gridSize;
            const points = [];
            for (let i = 0; i <= gridSize; i++)
                for (let j = 0; j <= gridSize; j++)
                    points.push({ lat: south + i * latStep, lng: west + j * lngStep });

            const results = [];
            for (const p of points) {
                try {
                    const res = await fetch('/api/et/point?longitude=' + p.lng.toFixed(4) + '&latitude=' + p.lat.toFixed(4) + '&start_date=' + start + '&end_date=' + end);
                    if (res.ok) {
                        const data = await res.json();
                        const totalET = data.reduce(function(sum, d) { return sum + d.et; }, 0);
                        results.push([p.lat, p.lng, totalET]);
                        document.getElementById('heatmap-status').innerText = 'Loading... ' + results.length + ' / ' + points.length + ' points';
                    }
                } catch(e) {}
                await new Promise(r => setTimeout(r, 400));
            }
            if (heatLayer) map.removeLayer(heatLayer);
            if (results.length > 0) {
                heatLayer = L.heatLayer(results, {
                    radius: 80, blur: 60, maxZoom: 12,
                    gradient: { 0.0: '#000080', 0.2: '#0000ff', 0.4: '#00ffff', 0.6: '#00ff00', 0.8: '#ffff00', 1.0: '#ff0000' }
                }).addTo(map);
                document.getElementById('heatmap-status').innerText = 'Heatmap loaded — ' + results.length + ' points (cached for next time)';
            } else {
                document.getElementById('heatmap-status').innerText = 'No data available for this area.';
            }
        }

        async function loadChart(lng, lat) {
            const start = document.getElementById('start').value;
            const end = document.getElementById('end').value;

            document.getElementById('coords-text').innerText = 'Lat: ' + lat + ', Lng: ' + lng;
            document.getElementById('empty-state').style.display = 'none';
            document.getElementById('loading-wrap').style.display = 'flex';
            document.getElementById('chart-wrapper').style.display = 'none';
            document.getElementById('anomaly-alert').style.display = 'none';
            document.getElementById('stats-row').style.display = 'none';
            document.getElementById('download-btn').style.display = 'none';

            try {
                const res = await fetch('/api/et/point?longitude=' + lng + '&latitude=' + lat + '&start_date=' + start + '&end_date=' + end);
                const data = await res.json();

                if (!Array.isArray(data)) {
                    throw new Error('Invalid response');
                }

                document.getElementById('loading-wrap').style.display = 'none';
                document.getElementById('chart-wrapper').style.display = 'block';
                document.getElementById('stats-row').style.display = 'grid';
                document.getElementById('download-btn').style.display = 'block';

                const values = data.map(function(d) { return d.et; });
                window.currentETData = data;
                const total = values.reduce(function(a, b) { return a + b; }, 0);
                const avg = total / values.length;
                const anomalies = data.filter(function(d) { return d.anomaly; });

                document.getElementById('stat-total').innerText = total.toFixed(1);
                document.getElementById('stat-avg').innerText = avg.toFixed(2);
                document.getElementById('stat-anomalies').innerText = anomalies.length;

                const anomalyCard = document.getElementById('stat-anomaly-card');
                if (anomalies.length > 0) {
                    anomalyCard.classList.add('anomaly');
                } else {
                    anomalyCard.classList.remove('anomaly');
                }

                const labels = data.map(function(d) { return d.time.slice(0, 7); });
                const colors = data.map(function(d) {
                    if (d.anomaly && d.anomaly_type === 'high') return 'rgba(239,68,68,0.85)';
                    if (d.anomaly && d.anomaly_type === 'low') return 'rgba(234,179,8,0.85)';
                    return 'rgba(37,99,235,0.8)';
                });

                let anomalyMsg = '';
                if (anomalies.length > 0) {
                    const alertBox = document.getElementById('anomaly-alert');
                    const highAnomalies = anomalies.filter(function(d) { return d.anomaly_type === 'high'; });
                    const lowAnomalies = anomalies.filter(function(d) { return d.anomaly_type === 'low'; });
                    anomalyMsg = 'Anomaly detected: ';
                    if (highAnomalies.length > 0) anomalyMsg += 'unusually high ET in ' + highAnomalies.map(function(d) { return d.time.slice(0,7); }).join(', ') + '. ';
                    if (lowAnomalies.length > 0) anomalyMsg += 'unusually low ET in ' + lowAnomalies.map(function(d) { return d.time.slice(0,7); }).join(', ') + '.';
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

                if (chart) chart.destroy();
                chart = new Chart(document.getElementById('chart'), {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{ label: 'ET (inches)', data: values, backgroundColor: colors, borderRadius: 4 }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        const d = data[ctx.dataIndex];
                                        let label = ctx.parsed.y.toFixed(2) + ' inches';
                                        if (d.anomaly) label += ' (' + d.anomaly_type + ', z=' + d.z_score + ')';
                                        return label;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: { beginAtZero: true, ticks: { color: '#aaa' }, grid: { color: 'rgba(255,255,255,0.06)' }, title: { display: true, text: 'ET (inches)', color: '#aaa', font: { size: 11 } } },
                            x: { ticks: { color: '#aaa', maxRotation: 45, font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.06)' } }
                        }
                    }
                });
            } catch(e) {
                document.getElementById('loading-wrap').style.display = 'none';
                document.getElementById('empty-state').style.display = 'flex';
                document.getElementById('empty-state').querySelector('p').innerText = 'No data for this location. Try clicking on farmland or vineyard areas.';
            }
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
            if (data.length > 0) {
                map.setView([parseFloat(data[0].lat), parseFloat(data[0].lon)], 10);
            } else {
                alert('Location not found.');
            }
        }

        async function sendChat() {
            const input = document.getElementById('chat-input');
            const msg = input.value.trim();
            if (!msg) return;
            input.value = '';
            const messages = document.getElementById('chat-messages');
            messages.innerHTML += '<div style="background:rgba(37,99,235,0.2);border-radius:8px;padding:8px 10px;font-size:12px;align-self:flex-end;max-width:85%;">' + msg + '</div>';
            messages.innerHTML += '<div id="chat-loading" style="font-size:11px;color:rgba(255,255,255,0.4);">Thinking...</div>';
            messages.scrollTop = messages.scrollHeight;
            try {
                const etData = window.currentETData || [];
                const location = document.getElementById('search').value || 'Finger Lakes';
                const start = document.getElementById('start').value;
                const end = document.getElementById('end').value;
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: msg, et_data: etData, location: location, date_range: start + ' to ' + end })
                });
                const data = await res.json();
                document.getElementById('chat-loading').remove();
                messages.innerHTML += '<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:8px 10px;font-size:12px;max-width:90%;line-height:1.5;">' + data.response + '</div>';
                messages.scrollTop = messages.scrollHeight;
            } catch(e) {
                document.getElementById('chat-loading').remove();
                messages.innerHTML += '<div style="color:#ef4444;font-size:11px;">Error — try again.</div>';
            }
        }
    </script>
</body>
</html>
"""
