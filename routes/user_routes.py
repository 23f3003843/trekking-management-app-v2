from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import or_
from extensions import database, cache_manager
from models import (Trek, Booking, ExportJob, roleOfTrekker, status_blacklisted_trekker, status_open_trek, DIFFICULTY, status_booked_booking, status_cancelled_booking, status_completed_booking)
from decorators import check_roles
userBP = Blueprint("user", __name__)

def _current_userId():
    return int(get_jwt_identity())

def _cache_key():
    return "open_treks::" + request.query_string.decode("utf-8")

@userBP.route("/treks", methods=["GET"])
@check_roles(roleOfTrekker)
@cache_manager.cached(timeout=120, key_prefix=_cache_key)  # Redis-backed cache, 2 min expiry
def list_open_treks():
    search = (request.args.get("search") or "").strip()
    difficulty = (request.args.get("difficulty") or "").strip()
    location = (request.args.get("location") or "").strip()

    q = Trek.query.filter_by(status=status_open_trek)
    if search:
        q = q.filter(or_(Trek.name.ilike(f"%{search}%"), Trek.location.ilike(f"%{search}%")))
    if difficulty in difficulty:
        q = q.filter_by(difficulty=difficulty)
    if location:
        q = q.filter(Trek.location.ilike(f"%{location}%"))

    treks = q.order_by(Trek.start_date).all()
    return jsonify(treks=[t.to_dict("trekker") for t in treks])

@userBP.route("/treks/<int:trekId>", methods=["GET"])
@check_roles(roleOfTrekker)
def trek_details(trekId):
    trek = Trek.query.get_or_404(trekId)
    #Check whether the current user already has an active booking
    existing = Booking.query.filter_by(userId=_current_userId(), trekId=trekId, status=status_booked_booking).first()
    return jsonify(trek=trek.to_dict("trekker"), already_booked=bool(existing))

@userBP.route("/treks/<int:trekId>/book", methods=["POST"])
@check_roles(roleOfTrekker)
def book_trek(trekId):
    userId = _current_userId()
    trek = Trek.query.get_or_404(trekId)

    if trek.status != status_open_trek:
        return jsonify(error="This trek is not open for bookings."), 400
    if trek.slotsAvailable <= 0:
        return jsonify(error="No slots available for this trek."), 400
    #Prevent duplicate active bookings for the same trek
    if Booking.query.filter_by(userId=userId, trekId=trekId, status=status_booked_booking).first():
        return jsonify(error="You already have an active booking for this trek."), 409

    booking = Booking(userId=userId, trekId=trekId)
    trek.slotsAvailable -= 1
    database.session.add(booking)
    database.session.commit()
    cache_manager.clear()
    return jsonify(message=f"'{trek.name}' booked successfully!", booking=booking.to_dict()), 201

@userBP.route("/bookings", methods=["GET"])
@check_roles(roleOfTrekker)
def my_bookings():
    userId = _current_userId()
    active = Booking.query.filter_by(userId=userId, status=status_booked_booking).order_by(Booking.bookingDate.desc()).all()
    completed = Booking.query.filter_by(userId=userId, status=status_completed_booking).order_by(Booking.bookingDate.desc()).all()
    cancelled = Booking.query.filter_by(userId=userId, status=status_cancelled_booking).order_by(Booking.bookingDate.desc()).all()
    return jsonify(
        active=[b.to_dict() for b in active],
        completed=[b.to_dict() for b in completed],
        cancelled=[b.to_dict() for b in cancelled],
    )

@userBP.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@check_roles(roleOfTrekker)
def cancel_booking(booking_id):
    booking = Booking.query.filter_by(id=booking_id, userId=_current_userId()).first_or_404()
    if booking.status != status_booked_booking:
        return jsonify(error="Only an active booking can be cancelled."), 400
    booking.status = status_cancelled_booking
    booking.trek.slotsAvailable += 1
    database.session.commit()
    #Refresh cached trek listings after a slot becomes available
    cache_manager.clear()
    return jsonify(message="Booking cancelled.", booking=booking.to_dict())

@userBP.route("/exports", methods=["POST"])
@check_roles(roleOfTrekker)
def trigger_export():
    from tasks import export_booking_history_csv
    #Create a record before starting the background export task
    job = ExportJob(userId=_current_userId(), status="Pending")
    database.session.add(job)
    database.session.commit()

    async_result = export_booking_history_csv.delay(job.id)
    job.celery_task_id = async_result.id
    database.session.commit()

    return jsonify(message="Export started. We'll let you know when it's ready.", job=job.to_dict()), 202

@userBP.route("/exports", methods=["GET"])
@check_roles(roleOfTrekker)
#Return export jobs belonging only to the logged-in user
def list_exports():
    jobs = ExportJob.query.filter_by(userId=_current_userId()).order_by(ExportJob.created_at.desc()).all()
    return jsonify(jobs=[j.to_dict() for j in jobs])

@userBP.route("/exports/<int:job_id>", methods=["GET"])
@check_roles(roleOfTrekker)
def export_status(job_id):
    job = ExportJob.query.filter_by(id=job_id, userId=_current_userId()).first_or_404()
    return jsonify(job=job.to_dict())

@userBP.route("/exports/<int:job_id>/download", methods=["GET"])
@check_roles(roleOfTrekker)
def download_export(job_id):
    job = ExportJob.query.filter_by(id=job_id, userId=_current_userId()).first_or_404()
    if job.status != "Done" or not job.file_path:
        return jsonify(error="Export is not ready yet."), 409
    return send_file(job.file_path, as_attachment=True, download_name="booking_history.csv")
