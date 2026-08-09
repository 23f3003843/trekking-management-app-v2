from datetime import date, timedelta
from extensions import celery_app, database
from models import Trek, Booking, status_booked_booking, status_open_trek, status_approved_trek
from .notify import sendEmail

@celery_app.task(name="tasks.dailyTrek_reminders")
def dailyTrek_reminders(lookahead_days: int = 3):
    windowEnd = date.today() + timedelta(days=lookahead_days)
    upcomingTreks = Trek.query.filter(
        Trek.status.in_([status_open_trek, status_approved_trek]),
        Trek.startDate >= date.today(),
        Trek.startDate <= windowEnd,
    ).all()

    reminderSent = 0
    for trek in upcomingTreks:
        active_bookings = [b for b in trek.bookings if b.status == status_booked_booking]
        for booking in active_bookings:
            user = booking.trekker
            html = f"""
                <h2>Upcoming Trek Reminder</h2>
                <p>Hi {user.fullName},</p>
                <p>This is a reminder that your trek <strong>{trek.name}</strong> at
                {trek.location} starts on <strong>{trek.startDate}</strong>
                ({trek.durationOfDays} day(s), difficulty: {trek.difficulty}).</p>
                <p>Please arrive at the meeting point with appropriate gear and be on
                time. Available slots remaining for this batch: {trek.available_slots}.</p>
                <p>Safe travels!<br/>Trek Manager</p>
            """
            sendEmail(f"Reminder: {trek.name} starts on {trek.startDate}", [user.email], html)
            reminderSent += 1

    return {"treks_checked": len(upcomingTreks), "reminderSent": reminderSent}
