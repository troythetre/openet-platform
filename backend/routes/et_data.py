import os

import requests
from fastapi import APIRouter, HTTPException

router = APIRouter()

OPENET_BASE_URL = "https://openet-api.org"


@router.get("/et/timeseries")
def get_et_timeseries(field_id: str, start_date: str, end_date: str):
    headers = {
        "Authorization": os.getenv("OPENET_API_KEY"),
        "Content-Type": "application/json",
    }
    payload = {
        "date_range": [start_date, end_date],
        "interval": "monthly",
        "field_ids": [field_id],
        "model": "Ensemble",
        "variable": "ET",
        "units": "in",
    }
    response = requests.post(
        f"{OPENET_BASE_URL}/v2/geodatabase/timeseries/features/monthly",
        json=payload,
        headers=headers,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()
