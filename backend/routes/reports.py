import csv
import io
import os

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter()

OPENET_BASE_URL = "https://openet-api.org"


# report generation endpoints
@router.get("/reports/csv")
def generate_csv(
    longitude: float,
    latitude: float,
    start_date: str,
    end_date: str,
    location_name: str = "Unknown Location",
):
    headers = {
        "Authorization": os.getenv("OPENET_API_KEY"),
        "Content-Type": "application/json",
    }
    payload = {
        "date_range": [start_date, end_date],
        "interval": "monthly",
        "geometry": [longitude, latitude],
        "model": "Ensemble",
        "variable": "ET",
        "reference_et": "gridMET",
        "units": "in",
        "file_format": "JSON",
    }
    response = requests.post(
        f"{OPENET_BASE_URL}/raster/timeseries/point", json=payload, headers=headers
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    data = response.json()

    # Calculate mean and std for anomaly detection
    values = [d["et"] for d in data]
    mean = sum(values) / len(values)
    std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header info
    writer.writerow(["OpenET Water Use Platform — ET Report"])
    writer.writerow(["Location", location_name])
    writer.writerow(["Coordinates", f"Lat: {latitude}, Lng: {longitude}"])
    writer.writerow(["Date Range", f"{start_date} to {end_date}"])
    writer.writerow(["Model", "Ensemble Mean"])
    writer.writerow(["Units", "inches"])
    writer.writerow([])

    # Data columns
    writer.writerow(
        ["Month", "ET (inches)", "Mean ET", "Z-Score", "Anomaly", "Anomaly Type"]
    )
    for d in data:
        z_score = (d["et"] - mean) / std if std > 0 else 0
        anomaly = abs(z_score) > 1.5
        anomaly_type = (
            "High" if z_score > 1.5 else "Low" if z_score < -1.5 else "Normal"
        )
        writer.writerow(
            [
                d["time"][:7],
                round(d["et"], 3),
                round(mean, 3),
                round(z_score, 3),
                "Yes" if anomaly else "No",
                anomaly_type,
            ]
        )

    writer.writerow([])
    writer.writerow(["Total ET (inches)", round(sum(values), 3)])
    writer.writerow(["Average Monthly ET (inches)", round(mean, 3)])

    output.seek(0)
    filename = (
        f"ET_Report_{location_name.replace(' ', '_')}_{start_date}_{end_date}.csv"
    )
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
