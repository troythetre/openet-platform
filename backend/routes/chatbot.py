from fastapi import APIRouter
from pydantic import BaseModel
import anthropic
import os

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    et_data: list = []
    location: str = "Unknown location"
    date_range: str = ""

@router.post("/chat")
def chat(request: ChatRequest):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    et_context = ""
    if request.et_data:
        total = sum(d["et"] for d in request.et_data)
        avg = total / len(request.et_data)
        anomalies = [d for d in request.et_data if d.get("anomaly")]
        peak = max(request.et_data, key=lambda d: d["et"])
        low = min(request.et_data, key=lambda d: d["et"])
        et_context = f"""
Location: {request.location}
Date range: {request.date_range}
Total ET: {round(total, 2)} inches
Average monthly ET: {round(avg, 2)} inches
Peak month: {peak['time'][:7]} ({peak['et']} inches)
Lowest month: {low['time'][:7]} ({low['et']} inches)
Anomalies detected: {len(anomalies)}
Monthly breakdown:
"""
        for d in request.et_data:
            status = f" anomaly ({d['anomaly_type']})" if d.get("anomaly") else ""
            et_context += f"  {d['time'][:7]}: {d['et']} inches{status}\n"

    system_prompt = f"""You are an agricultural water use analyst assistant for the OpenET platform at Cornell University.
You help researchers and farmers understand evapotranspiration (ET) data from NASA satellites.
ET measures how much water evaporates from crops and soil - a key indicator of crop water use and irrigation needs.

Current data context:
{et_context if et_context else "No location selected yet."}

Keep responses concise and focused on water use insights. Use plain English."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system_prompt,
        messages=[{"role": "user", "content": request.message}]
    )

    return {"response": message.content[0].text}
