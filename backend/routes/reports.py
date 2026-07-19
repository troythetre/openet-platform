import csv
import io

from database import SessionLocal
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from routes.et_data import detect_anomalies, fetch_et_series

router = APIRouter()


# report generation endpoints
@router.get("/reports/csv")
def generate_csv(
    longitude: float,
    latitude: float,
    start_date: str,
    end_date: str,
    location_name: str = "Unknown Location",
):
    db = SessionLocal()
    try:
        raw_data = fetch_et_series(longitude, latitude, start_date, end_date, db)
    finally:
        db.close()

    data = detect_anomalies(raw_data)

    values = [d["et"] for d in data]
    mean = sum(values) / len(values)

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

    # Data columns — reuse the same monthly-seasonal anomaly detection
    # (z-score vs. same calendar month across years) used everywhere else
    # in the app, so the CSV matches what's shown on screen.
    writer.writerow(
        [
            "Month",
            "ET (inches)",
            "Monthly Mean ET",
            "Z-Score",
            "Anomaly",
            "Anomaly Type",
        ]
    )
    for d in data:
        writer.writerow(
            [
                d["time"][:7],
                round(d["et"], 3),
                d["mean"],
                d["z_score"],
                "Yes" if d["anomaly"] else "No",
                d["anomaly_type"].capitalize(),
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
