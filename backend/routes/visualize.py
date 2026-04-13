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
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Arial, sans-serif; background: #f9f9f9; }
        header { background: #1a237e; color: white; padding: 16px 24px; }
        header h1 { font-size: 20px; }
        header p { font-size: 13px; opacity: 0.8; margin-top: 4px; }
        .container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; padding: 20px; height: calc(100vh - 70px); }
        .panel { background: white; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); overflow: hidden; }
        #map { width: 100%; height: 100%; }
        .chart-panel { padding: 20px; display: flex; flex-direction: column; gap: 12px; }
        .chart-panel h2 { font-size: 15px; color: #1a237e; }
        .coords { font-size: 12px; color: #888; }
        .loading { font-size: 13px; color: #888; text-align: center; margin-top: 40px; }
        canvas { flex: 1; }
        .date-controls { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
        .date-controls label { font-size: 12px; color: #555; }
        .date-controls input { padding: 6px 10px; border-radius: 6px; border: 1px solid #ccc; font-size: 12px; width: 120px; }
        .date-controls button { padding: 6px 14px; background: #1a237e; color: white; border: none; border-radius: 6px; font-size: 12px; cursor: pointer; }
        .date-controls button:hover { background: #283593; }
    </style>
</head>
<body>
    <header>
        <h1>OpenET Water Use Platform</h1>
        <p>Click anywhere on the map to view monthly ET data for that location</p>
    </header>

    <div class="container">
        <div class="panel">
            <div id="map"></div>
        </div>
        <div class="panel chart-panel">
            <h2>Monthly Evapotranspiration (ET)</h2>
            <div class="coords" id="coords">Click on the map to select a location</div>
            <div class="date-controls">
                <label>From</label>
                <input type="text" id="start" value="2023-01-01"/>
                <label>To</label>
                <input type="text" id="end" value="2023-12-31"/>
                <button onclick="reloadData()">Reload</button>
            </div>
            <div class="loading" id="loading">Click on the map to get started</div>
            <canvas id="chart" style="display:none;"></canvas>
        </div>
    </div>

    <script>
        let chart;
        let marker;
        let currentLng = null;
        let currentLat = null;

        // Init map centered on US farmland
        const map = L.map('map').setView([38.5, -121.5], 8);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        // Click handler
        map.on('click', function(e) {
            currentLat = e.latlng.lat.toFixed(5);
            currentLng = e.latlng.lng.toFixed(5);

            if (marker) marker.remove();
            marker = L.marker([currentLat, currentLng]).addTo(map);

            loadData(currentLng, currentLat);
        });

        function reloadData() {
            if (currentLng && currentLat) loadData(currentLng, currentLat);
        }

        async function loadData(lng, lat) {
            const start = document.getElementById('start').value;
            const end = document.getElementById('end').value;

            document.getElementById('coords').innerText = `Lat: ${lat}, Lng: ${lng}`;
            document.getElementById('loading').innerText = 'Loading satellite data...';
            document.getElementById('chart').style.display = 'none';

            try {
                const res = await fetch(`/api/et/point?longitude=${lng}&latitude=${lat}&start_date=${start}&end_date=${end}`);
                const data = await res.json();

                document.getElementById('loading').innerText = '';
                document.getElementById('chart').style.display = 'block';

                const labels = data.map(d => d.time.slice(0, 7));
                const values = data.map(d => d.et);
                const maxVal = Math.max(...values);
                const colors = values.map(v => v === maxVal ? 'rgba(239,68,68,0.8)' : 'rgba(37,99,235,0.7)');

                if (chart) chart.destroy();
                chart = new Chart(document.getElementById('chart'), {
                    type: 'bar',
                    data: {
                        labels,
                        datasets: [{
                            label: 'ET (inches)',
                            data: values,
                            backgroundColor: colors,
                            borderRadius: 6,
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: ctx => `${ctx.parsed.y.toFixed(2)} inches`
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: { display: true, text: 'ET (inches)' }
                            },
                            x: {
                                title: { display: true, text: 'Month' }
                            }
                        }
                    }
                });
            } catch(e) {
                document.getElementById('loading').innerText = 'Error loading data. Try another location.';
            }
        }
    </script>
</body>
</html>
"""
