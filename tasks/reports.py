from datetime import date
from calendar import month_name
from sqlalchemy import func
from extensions import celery_app, database
from models import User, Trek, Booking, roleOfAdmin, status_booked_booking, status_completed_booking, status_completed_trek
from .notify import sendEmail

def previous_month_date(today: date):
    # Calculate the first and last day of the previous month
    first_of_this_month = today.replace(day=1)
    last_day_prev_month = first_of_this_month - date.resolution
    first_day_prev_month = last_day_prev_month.replace(day=1)
    return first_day_prev_month, last_day_prev_month

@celery_app.task(name="tasks.monthly_report")
def monthly_report():
    start, end = previous_month_date(date.today())
    treks_conducted = Trek.query.filter(Trek.status == status_completed_trek, Trek.endDate >= start, Trek.endDate <= end).all()

    #Get bookings made during the reporting period
    bookings_in_range = Booking.query.filter(Booking.bookingDate >= start, Booking.bookingDate <= end, Booking.status.in_([status_booked_booking, status_completed_booking])).all()
    participant_ids = {b.userId for b in bookings_in_range}

    #Five most booked treks during the reporting period
    popularity = (
        database.session.query(Trek.name, func.count(Booking.id).label("cnt"))
        .join(Booking, Booking.trekId == Trek.id)
        .filter(Booking.bookingDate >= start, Booking.bookingDate <= end)
        .group_by(Trek.id)
        .order_by(func.count(Booking.id).desc())
        .limit(5)
        .all()
    )

    rows = "".join(f"<tr><td>{name}</td><td>{cnt}</td></tr>" for name, cnt in popularity) or \
        "<tr><td colspan='2'>No bookings this period</td></tr>"

    html = f"""
        <h2>Trek Manager - Monthly Activity Report</h2>
        <p>Period: {start.strftime('%d %b %Y')} - {end.strftime('%d %b %Y')} ({month_name[start.month]})</p>
        <ul>
          <li><strong>Treks conducted (completed):</strong> {len(treks_conducted)}</li>
          <li><strong>Unique users who participated:</strong> {len(participant_ids)}</li>
          <li><strong>Total bookings made:</strong> {len(bookings_in_range)}</li>
        </ul>
        <h3>Most popular treks</h3>
        <table border="1" cellpadding="6" cellspacing="0">
          <tr><th>Trek</th><th>Bookings</th></tr>
          {rows}
        </table>
        <p>This is an automatically generated report from Trek Manager.</p>
    """

    admins = User.query.filter_by(role=roleOfAdmin).all()
    recipients = [a.email for a in admins]
    result = "no admin recipients"
    if recipients:
        result = sendEmail(
            f"Trek Manager - Monthly Report ({month_name[start.month]} {start.year})",
            recipients, html,
        )
    return {
        "period": f"{start} to {end}",
        "treks_conducted": len(treks_conducted),
        "unique_participants": len(participant_ids),
        "total_bookings": len(bookings_in_range),
        "email_result": result,
    }
