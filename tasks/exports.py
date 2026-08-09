import os
import csv
from datetime import datetime
from flask import current_app
from extensions import celery_app, database
from models import Booking, ExportJob

@celery_app.task(name="tasks.bookingHistory_csv", bind=True)
def bookingHistory_csv(self, export_job_id: int):
    job = ExportJob.query.get(export_job_id)
    if not job:
        return {"error": "export job not found"}
    job.status = "Running"
    database.session.commit()

    try:
        bookings = (Booking.query.filter_by(userId=job.userId).order_by(Booking.bookingDate.desc()).all())
        user_dir = os.path.join(current_app.config["EXPORTS_DIR"], str(job.userId))
        os.makedirs(user_dir, exist_ok=True)
        filename = f"booking_history_{job.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
        filepath = os.path.join(user_dir, filename)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["User ID", "Trek Name", "Location", "Booking Status", "Booking Date", "Start Date", "End Date"])
            for b in bookings:
                writer.writerow([
                    b.userId,
                    b.trek.name if b.trek else "",
                    b.trek.location if b.trek else "",
                    b.status,
                    b.bookingDate.strftime("%Y-%m-%d %H:%M") if b.bookingDate else "",
                    b.trek.startDate.isoformat() if b.trek and b.trek.startDate else "",
                    b.trek.endDate.isoformat() if b.trek and b.trek.endDate else "",
                ])

        job.status = "Done"
        job.file_path = filepath
        job.completedAt = datetime.utcnow()
        database.session.commit()
        return {"status": "Done", "file_path": filepath, "rows": len(bookings)}
    
    except Exception as exc:
        job.status = "Failed"
        database.session.commit()
        raise exc