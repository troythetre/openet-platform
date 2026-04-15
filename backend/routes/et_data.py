import os

import requests
from fastapi import APIRouter, HTTPException

router = APIRouter()

OPENET_BASE_URL = "https://openet-api.org"


def detect_anomalies(data: list) -> list:
    values = [d["et"] for d in data]
    mean = sum(values) / len(values)
    std = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5

    result = []
    for d in data:
        z_score = (d["et"] - mean) / std if std > 0 else 0
        anomaly = abs(z_score) > 1.0
        result.append(
            {
                "time": d["time"],
                "et": d["et"],
                "mean": round(mean, 3),
                "z_score": round(z_score, 3),
                "anomaly": anomaly,
                "anomaly_type": "high"
                if z_score > 1.5
                else "low"
                if z_score < -1.5
                else "normal",
            }
        )
    return result


@router.get("/et/point")
def get_et_point(
    longitude: float = -121.36322,
    latitude: float = 38.87626,
    start_date: str = "2026-01-01",
    end_date: str = "2026-4-01",
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
        f"{OPENET_BASE_URL}/raster/timeseries/point",
        json=payload,
        headers=headers,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()
