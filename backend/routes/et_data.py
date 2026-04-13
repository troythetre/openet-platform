import os

import requests
from fastapi import APIRouter, HTTPException

router = APIRouter()

OPENET_BASE_URL = "https://openet-api.org"


@router.get("/et/point")
def get_et_point(
    longitude: float = -121.36322,
    latitude: float = 38.87626,
    start_date: str = "2023-01-01",
    end_date: str = "2023-12-31",
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
