from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from extensions import database, cache_manager
from models import (Trek, Booking, roleOfStaff, status_approved_staff, status_booked_booking, status_completed_booking, trek_status)
from decorators import check_roles

staffBP = Blueprint("staff", __name__)

def _current_staffId():
    return int(get_jwt_identity())

@staffBP.route("/dashboard", methods=["GET"])
@check_roles(roleOfStaff)
def dashboard():
    staffId = _current_staffId()
    #Get treks assigned to the logged-in staff member
    treks = Trek.query.filter_by(staffId=staffId).order_by(Trek.start_date).all()
    payload = []
    for t in treks:
        d = t.to_dict("staff")
        d["registered_users"] = t.active_booking_count
        payload.append(d)
    return jsonify(treks=payload)

@staffBP.route("/treks/<int:trekId>", methods=["GET"])
@check_roles(roleOfStaff)
def trek_details(trekId):
    trek = Trek.query.get_or_404(trekId)
    if trek.staffId != _current_staffId():
        return jsonify(error="You are not assigned to this trek."), 403
    #Get users with active or completed bookings for the trek
    participants = Booking.query.filter(Booking.trekId == trek.id, Booking.status.in_([status_booked_booking, status_completed_booking])).all()
    return jsonify(trek=trek.to_dict("staff"), participants=[p.to_dict() for p in participants])


@staffBP.route("/treks/<int:trekId>", methods=["PUT"])
@check_roles(roleOfStaff)
def update_trek(trekId):
    trek = Trek.query.get_or_404(trekId)
    #Staff can only update treks assigned to them
    if trek.staffId != _current_staffId():
        return jsonify(error="You are not assigned to this trek."), 403

    data = request.get_json(silent=True) or {}
    new_status = data.get("status", trek.status)
    if new_status not in ("Open", "Closed", "Completed"):
        return jsonify(error="Status must be Open, Closed, or Completed."), 400

    if "slotsAvailable" in data:
        try:
            slots = int(data["slotsAvailable"])
        except (TypeError, ValueError):
            return jsonify(error="slotsAvailable must be an integer."), 400
        if slots < 0 or slots > trek.total_slots:
            return jsonify(error=f"slotsAvailable must be between 0 and {trek.total_slots}."), 400
        trek.slotsAvailable = slots

    trek.status = new_status
    #Mark all active bookings as completed when the trek is completed
    if trek.status == "Completed":
        for b in trek.bookings:
            if b.status == status_booked_booking:
                b.status = status_completed_booking

    database.session.commit()
    cache_manager.clear()
    return jsonify(message="Trek updated.", trek=trek.to_dict("staff"))