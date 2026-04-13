from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/chart", response_class=HTMLResponse)
def chart():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>OpenET Water Use Chart</title>
     <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
     <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; background: #f9f9f9; }
        h1 { color: #1a237e; font-size: 22px; }
        p { color: #555; font-size: 14px; }
        canvas { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); }
        .controls { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
        input, button { padding: 8px 12px; border-radius: 6px; border: 1px solid #ccc; font-size: 13px; }
        button { background: #1a237e; color: white; border: none; cursor: pointer; }
        button:hover { background: #283593; }
        .loading { color: #888; font-size: 13px; margin-top: 8px; }
    </style>
</head>
<body>
    <h1>OpenET Water Use Platform</h1>
    <p>Monthly evapotranspiration (ET) data from satellite imagery.</p>

    <div class="controls">
        <input type="number" id="lng" value="-121.36322" placeholder="Longitude" step="0.001"/>
        <input type="number" id="lat" value="38.87626" placeholder="Latitude" step="0.001"/>
        <input type="text" id="start" value="2023-01-01" placeholder="Start date"/>
        <input type="text" id="end" value="2023-12-31" placeholder="End date"/>
        <button onclick="loadData()">Load Data</button>
    </div>
    <div class="loading" id="loading"></div>

    <canvas id="chart" height="100"></canvas>

    <script>
        let chart;
        async function loadData() {
            const lng = document.getElementById('lng').value;
            const lat = document.getElementById('lat').value;
            const start = document.getElementById('start').value;
            const end = document.getElementById('end').value;

            document.getElementById('loading').innerText = 'Loading...';

            const res = await fetch(`/api/et/point?longitude=${lng}&latitude=${lat}&start_date=${start}&end_date=${end}`);
            const data = await res.json();

            document.getElementById('loading').innerText = '';

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
                        title: {
                            display: true,
                            text: `Monthly ET — Lat: ${lat}, Lng: ${lng}`,
                            font: { size: 14 }
                        },
                        tooltip: {
                            callbacks: {
                                label: ctx => `${ctx.parsed.y.toFixed(2)} inches`
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Evapotranspiration (inches)' }
                        },
                        x: {
                            title: { display: true, text: 'Month' }
                        }
                    }
                    }
                });
            }

            loadData();
    </script>
</body>
</html>
"""
