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
        body { font-family: Arial, sans-serif; background: #111; color: white; }
        header { background: #1a237e; color: white; padding: 16px 24px; display: flex; align-items: center; gap: 20px; }
        header h1 { font-size: 20px; }
        header p { font-size: 13px; opacity: 0.8; }
        .controls { display: flex; gap: 8px; align-items: center; margin-left: auto; flex-wrap: wrap; }
        .controls label { font-size: 12px; opacity: 0.8; }
        .controls input { padding: 6px 10px; border-radius: 6px; border: 1px solid #555; font-size: 12px; width: 110px; background: #2a2a4a; color: white; }
        .controls button { padding: 6px 14px; background: #4CAF50; color: white; border: none; border-radius: 6px; font-size: 12px; cursor: pointer; }
        .controls button:hover { background: #388E3C; }
        .main { display: grid; grid-template-columns: 1fr 380px; height: calc(100vh - 70px); }
        #map { width: 100%; height: 100%; }
        .side-panel { background: #1a1a2e; padding: 20px; display: flex; flex-direction: column; gap: 14px; overflow-y: auto; }
        .side-panel h2 { font-size: 14px; color: #90caf9; }
        .coords { font-size: 12px; color: #aaa; }
        .loading { font-size: 13px; color: #aaa; text-align: center; margin-top: 40px; }
        .anomaly-box { background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.5); border-radius: 8px; padding: 10px 14px; font-size: 12px; color: #fca5a5; }
        .anomaly-box.low { background: rgba(234,179,8,0.15); border-color: rgba(234,179,8,0.5); color: #fde047; }
        .legend { display: flex; gap: 12px; font-size: 11px; color: #aaa; flex-wrap: wrap; }
        .legend-dot { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 4px; vertical-align: middle; }
        #chart-wrapper { flex: 1; min-height: 220px; }
        .heatmap-status { font-size: 11px; color: #aaa; text-align: center; }
        .color-scale { display: flex; align-items: center; gap: 8px; font-size: 11px; color: #aaa; }
        .color-bar { height: 12px; flex: 1; border-radius: 4px; background: linear-gradient(to right, #000080, #0000ff, #00ffff, #00ff00, #ffff00, #ff0000); }
        .map-overlay { position: absolute; bottom: 30px; left: 10px; z-index: 1000; background: rgba(0,0,0,0.7); padding: 8px 12px; border-radius: 8px; font-size: 11px; color: white; }
    </style>
</head>
<body>
    <header>
        <div>
            <h1>OpenET Water Use Platform</h1>
            <p>Click map to view ET data — heatmap shows annual ET across the region</p>
        </div>
        <div class="controls">
            <input type="text" id="search" placeholder="Search location..." style="width:160px;"
                onkeydown="if(event.key==='Enter') searchLocation()"/>
            <button onclick="searchLocation()" style="background:#555;">Go</button>
            <label>From</label>
            <input type="text" id="start" value="2023-01-01"/>
            <label>To</label>
            <input type="text" id="end" value="2023-12-31"/>
            <button onclick="refreshHeatmap()">Update Heatmap</button>
        </div>
    </header>

    <div class="main">
        <div style="position:relative;">
            <div id="map"></div>
            <div class="map-overlay">
                <div style="margin-bottom:4px;">ET Intensity</div>
                <div class="color-bar" style="width:140px;height:10px;border-radius:3px;background:linear-gradient(to right,#000080,#0000ff,#00ffff,#00ff00,#ffff00,#ff0000);"></div>
                <div style="display:flex;justify-content:space-between;width:140px;margin-top:2px;">
                    <span>Low</span><span>High</span>
                </div>
            </div>
        </div>
        <div class="side-panel">
            <h2>Monthly ET Chart</h2>
            <div class="coords" id="coords">Click on the map to select a location</div>
            <div class="legend">
                <span><span class="legend-dot" style="background:rgba(37,99,235,0.8);"></span>Normal</span>
                <span><span class="legend-dot" style="background:rgba(239,68,68,0.85);"></span>High anomaly</span>
                <span><span class="legend-dot" style="background:rgba(234,179,8,0.85);"></span>Low anomaly</span>
            </div>
            <div id="anomaly-alert" style="display:none;" class="anomaly-box"></div>
            <div id="loading" class="loading">Click on the map to get started</div>
            <div id="chart-wrapper" style="display:none;">
                <canvas id="chart"></canvas>
            </div>
            <div class="heatmap-status" id="heatmap-status"></div>
        </div>
    </div>

    <script>
        let chart;
        let marker;
        let heatLayer;
        let currentLng = null;
        let currentLat = null;

        const map = L.map('map').setView([38.5, -121.5], 7);

        // Dark tile layer
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '© OpenStreetMap © CARTO',
            maxZoom: 19
        }).addTo(map);

        map.on('click', function(e) {
            currentLat = e.latlng.lat.toFixed(5);
            currentLng = e.latlng.lng.toFixed(5);
            if (marker) marker.remove();
            marker = L.circleMarker([currentLat, currentLng], {
                radius: 8,
                color: 'white',
                fillColor: '#4CAF50',
                fillOpacity: 1,
                weight: 2
            }).addTo(map);
            loadChart(currentLng, currentLat);
        });

        async function refreshHeatmap() {
            const center = map.getCenter();
            const bounds = map.getBounds();
            await loadHeatmap(bounds);
        }

        map.on('moveend', function() {
            const zoom = map.getZoom();
            if (zoom >= 6) {
                loadHeatmap(map.getBounds());
            }
        });

        async function loadHeatmap(bounds) {
            document.getElementById('heatmap-status').innerText = 'Loading heatmap data...';
            const start = document.getElementById('start').value;
            const end = document.getElementById('end').value;

            // Sample a grid of points across the visible bounds
            const north = bounds.getNorth();
            const south = bounds.getSouth();
            const east = bounds.getEast();
            const west = bounds.getWest();

            const gridSize = 5;
            const latStep = (north - south) / gridSize;
            const lngStep = (east - west) / gridSize;

            const points = [];
            for (let i = 0; i <= gridSize; i++) {
                for (let j = 0; j <= gridSize; j++) {
                    points.push({
                        lat: south + i * latStep,
                        lng: west + j * lngStep
                    });
                }
            }

            // Fetch ET for each point
            const results = [];
            for (const p of points) {
                try {
                    const res = await fetch('/api/et/point?longitude=' + p.lng.toFixed(4) + '&latitude=' + p.lat.toFixed(4) + '&start_date=' + start + '&end_date=' + end);
                    if (res.ok) {
                        const data = await res.json();
                        const totalET = data.reduce(function(sum, d) { return sum + d.et; }, 0);
                        results.push([p.lat, p.lng, totalET]);
                        document.getElementById('heatmap-status').innerText = 'Loading... ' + results.length + ' points done';
                    }
                } catch(e) {}
                await new Promise(r => setTimeout(r, 500));
            }

            const validResults = results;

            if (heatLayer) map.removeLayer(heatLayer);
            heatLayer = L.heatLayer(validResults, {
                radius: 80,
                blur: 60,
                maxZoom: 12,
                gradient: {
                    0.0: '#000080',
                    0.2: '#0000ff',
                    0.4: '#00ffff',
                    0.6: '#00ff00',
                    0.8: '#ffff00',
                    1.0: '#ff0000'
                }
            }).addTo(map);

            document.getElementById('heatmap-status').innerText = 'Heatmap loaded — ' + validResults.length + ' points sampled';
        }

        async function loadChart(lng, lat) {
            const start = document.getElementById('start').value;
            const end = document.getElementById('end').value;

            document.getElementById('coords').innerText = 'Lat: ' + lat + ', Lng: ' + lng;
            document.getElementById('loading').innerText = 'Loading satellite data...';
            document.getElementById('loading').style.display = 'block';
            document.getElementById('chart-wrapper').style.display = 'none';
            document.getElementById('anomaly-alert').style.display = 'none';

            try {
                const res = await fetch('/api/et/point?longitude=' + lng + '&latitude=' + lat + '&start_date=' + start + '&end_date=' + end);
                const data = await res.json();

                document.getElementById('loading').style.display = 'none';
                document.getElementById('chart-wrapper').style.display = 'block';

                const labels = data.map(function(d) { return d.time.slice(0, 7); });
                const values = data.map(function(d) { return d.et; });
                const colors = data.map(function(d) {
                    if (d.anomaly && d.anomaly_type === 'high') return 'rgba(239,68,68,0.85)';
                    if (d.anomaly && d.anomaly_type === 'low') return 'rgba(234,179,8,0.85)';
                    return 'rgba(37,99,235,0.8)';
                });

                const anomalies = data.filter(function(d) { return d.anomaly; });
                if (anomalies.length > 0) {
                    const alertBox = document.getElementById('anomaly-alert');
                    const highAnomalies = anomalies.filter(function(d) { return d.anomaly_type === 'high'; });
                    const lowAnomalies = anomalies.filter(function(d) { return d.anomaly_type === 'low'; });
                    let msg = 'Anomaly detected: ';
                    if (highAnomalies.length > 0) msg += 'unusually high ET in ' + highAnomalies.map(function(d) { return d.time.slice(0,7); }).join(', ') + '. ';
                    if (lowAnomalies.length > 0) msg += 'unusually low ET in ' + lowAnomalies.map(function(d) { return d.time.slice(0,7); }).join(', ') + '.';
                    alertBox.innerText = msg;
                    alertBox.className = highAnomalies.length > 0 ? 'anomaly-box' : 'anomaly-box low';
                    alertBox.style.display = 'block';
                }

                if (chart) chart.destroy();
                chart = new Chart(document.getElementById('chart'), {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'ET (inches)',
                            data: values,
                            backgroundColor: colors,
                            borderRadius: 4
                        }]
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
                                        if (d.anomaly) label += ' - ' + d.anomaly_type + ' anomaly (z=' + d.z_score + ')';
                                        return label;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: { color: '#aaa' },
                                grid: { color: 'rgba(255,255,255,0.1)' },
                                title: { display: true, text: 'ET (inches)', color: '#aaa' }
                            },
                            x: {
                                ticks: { color: '#aaa', maxRotation: 45 },
                                grid: { color: 'rgba(255,255,255,0.1)' },
                                title: { display: true, text: 'Month', color: '#aaa' }
                            }
                        }
                    }
                });
            } catch(e) {
                document.getElementById('loading').innerText = 'Error loading data. Try another location.';
                document.getElementById('loading').style.display = 'block';
            }
        }

        // Load initial heatmap on page load
        setTimeout(function() {
            loadHeatmap(map.getBounds());
        }, 1000);

        async function searchLocation() {
            const query = document.getElementById('search').value;
            if (!query) return;

            const res = await fetch('https://nominatim.openstreetmap.org/search?q=' + encodeURIComponent(query) + '&format=json&limit=1');
            const data = await res.json();

            if (data.length > 0) {
                const lat = parseFloat(data[0].lat);
                const lng = parseFloat(data[0].lon);
                map.setView([lat, lng], 10);
                setTimeout(function() {
                    loadHeatmap(map.getBounds());
                }, 500);
            } else {
                alert('Location not found. Try a different search.');
            }
        }
    </script>
</body>
</html>
"""
