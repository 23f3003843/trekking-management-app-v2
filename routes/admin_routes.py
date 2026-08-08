from datetime import date, datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
from extensions import database, cache_manager
from models import (
    User, Trek, Booking, roleOfAdmin, roleOfStaff, roleOfTrekker,
    status_pendingStaff, status_approved_staff, status_blacklisted_staff,
    status_active_trekker, status_blacklisted_trekker,
    status_pending_trek, status_approved_trek, status_open_trek, trek_status, difficulty,
    status_booked_booking, status_completed_booking,
)
from decorators import check_roles

adminBP = Blueprint("admin", __name__)

def _invalidate_trek_cache():
    cache_manager.clear()

@adminBP.route("/dashboard", methods=["GET"])
@check_roles(roleOfAdmin)
def dashboard():
    stats = {
        "totalTreks": Trek.query.count(),
        "openTreks": Trek.query.filter_by(status=status_open_trek).count(),
        "totalStaff": User.query.filter_by(role=roleOfStaff).count(),
        "pendingStaff": User.query.filter_by(role=roleOfStaff, status=status_pendingStaff).count(),
        "totalTrekkers": User.query.filter_by(role=roleOfTrekker).count(),
        "totalBookings": Booking.query.count(),
    }
    recent = (Booking.query.order_by(Booking.booking_date.desc()).limit(10).all())
    return jsonify(stats=stats, recent_bookings=[b.to_dict() for b in recent])

@adminBP.route("/treks", methods=["GET"])
@check_roles(roleOfAdmin)
def list_treks():
    treks = Trek.query.order_by(Trek.created_at.desc()).all()
    return jsonify(treks=[t.to_dict(for_role="admin") for t in treks])

def _parse_trek_payload(data, existing=None):
    errors = {}
    name = (data.get("name") or "").strip()
    location = (data.get("location") or "").strip()
    difficulty = data.get("difficulty") or "Easy"
    description = (data.get("description") or "").strip()
    try:
        durationOfDays = int(data.get("durationOfDays"))
        if not (1 <= durationOfDays <= 90):
            raise ValueError()
    except (TypeError, ValueError):
        errors["durationOfDays"] = "Duration must be an integer between 1 and 90."
        durationOfDays = None

    try:
        totalSlots = int(data.get("totalSlots"))
        if totalSlots < 1:
            raise ValueError()
    except (TypeError, ValueError):
        errors["totalSlots"] = "Total slots must be a positive integer."
        totalSlots = None

    try:
        startDate = datetime.strptime(data.get("startDate", ""), "%Y-%m-%d").date()
        endDate = datetime.strptime(data.get("endDate", ""), "%Y-%m-%d").date()
        if endDate < startDate:
            errors["endDate"] = "End date cannot be before start date."
    except ValueError:
        errors["startDate"] = "startDate/endDate must be in YYYY-MM-DD format."
        startDate = endDate = None

    if not name:
        errors["name"] = "Trek name is required."
    if not location:
        errors["location"] = "Location is required."
    if difficulty not in difficulty:
        errors["difficulty"] = f"Difficulty must be one of {difficulty}."

    return errors, {
        "name": name, "location": location, "difficulty": difficulty,
        "durationOfDays": durationOfDays, "totalSlots": totalSlots,
        "startDate": startDate, "endDate": endDate,
        "description": description,
    }

@adminBP.route("/treks", methods=["POST"])
@check_roles(roleOfAdmin)
def create_trek():
    data = request.get_json(silent=True) or {}
    errors, fields = _parse_trek_payload(data)
    if errors:
        return jsonify(error="Validation failed.", fields=errors), 400

    trek = Trek(
        name=fields["name"], location=fields["location"], difficulty=fields["difficulty"],
        durationOfDays=fields["durationOfDays"], totalSlots=fields["totalSlots"],
        slotsAvailable=fields["totalSlots"], startDate=fields["startDate"],
        endDate=fields["endDate"], description=fields["description"],
        status=status_pending_trek,
    )
    database.session.add(trek)
    database.session.commit()
    _invalidate_trek_cache_manager()
    return jsonify(message=f"Trek '{trek.name}' created.", trek=trek.to_dict("admin")), 201

@adminBP.route("/treks/<int:trek_id>", methods=["PUT"])
@check_roles(roleOfAdmin)
def update_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    data = request.get_json(silent=True) or {}
    errors, fields = _parse_trek_payload(data)
    if errors:
        return jsonify(error="Validation failed.", fields=errors), 400

    slots_diff = fields["totalSlots"] - trek.totalSlots
    trek.name = fields["name"]
    trek.location = fields["location"]
    trek.difficulty = fields["difficulty"]
    trek.durationOfDays = fields["durationOfDays"]
    trek.totalSlots = fields["totalSlots"]
    trek.slotsAvailable = max(0, trek.slotsAvailable + slots_diff)
    trek.startDate = fields["startDate"]
    trek.endDate = fields["endDate"]
    trek.description = fields["description"]
    database.session.commit()
    _invalidate_trek_cache_manager()
    return jsonify(message=f"Trek '{trek.name}' updated.", trek=trek.to_dict("admin"))

@adminBP.route("/treks/<int:trek_id>", methods=["DELETE"])
@check_roles(roleOfAdmin)
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    name = trek.name
    database.session.delete(trek)
    database.session.commit()
    _invalidate_trek_cache_manager()
    return jsonify(message=f"Trek '{name}' deleted.")

@adminBP.route("/treks/<int:trek_id>/assign", methods=["POST"])
@check_roles(roleOfAdmin)
def assign_staff(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    data = request.get_json(silent=True) or {}
    staffId = data.get("staffId")
    staff = User.query.filter_by(id=staffId, role=roleOfStaff, status=status_approved_staff).first()
    if not staff:
        return jsonify(error="A valid, approved staff member is required."), 400

    trek.staffId = staff.id
    if trek.status == status_pending_trek:
        trek.status = status_approved_trek
    database.session.commit()
    _invalidate_trek_cache_manager()
    return jsonify(message=f"{staff.full_name} assigned to '{trek.name}'.", trek=trek.to_dict("admin"))

@adminBP.route("/staff", methods=["GET"])
@check_roles(roleOfAdmin)
def list_staff():
    staff = User.query.filter_by(role=roleOfStaff).order_by(User.created_at.desc()).all()
    return jsonify(staff=[s.to_dict() for s in staff])

@adminBP.route("/trekkers", methods=["GET"])
@check_roles(roleOfAdmin)
def list_trekkers():
    trekkers = User.query.filter_by(role=roleOfTrekker).order_by(User.created_at.desc()).all()
    return jsonify(trekkers=[t.to_dict() for t in trekkers])

@adminBP.route("/staff/<int:user_id>/approve", methods=["POST"])
@check_roles(roleOfAdmin)
def approve_staff(user_id):
    staff = User.query.filter_by(id=user_id, role=roleOfStaff).first_or_404()
    staff.status = status_approved_staff
    database.session.commit()
    return jsonify(message=f"{staff.full_name} approved.", user=staff.to_dict())

@adminBP.route("/users/<int:user_id>/blacklist", methods=["POST"])
@check_roles(roleOfAdmin)
def blacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == roleOfAdmin:
        return jsonify(error="The admin account cannot be blacklisted."), 400
    user.status = status_blacklisted_staff if user.role == roleOfStaff else status_blacklisted_trekker
    database.session.commit()
    return jsonify(message=f"{user.full_name} blacklisted.", user=user.to_dict())

@adminBP.route("/users/<int:user_id>/reinstate", methods=["POST"])
@check_roles(roleOfAdmin)
def reinstate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = status_approved_staff if user.role == roleOfStaff else status_active_trekker
    database.session.commit()
    return jsonify(message=f"{user.full_name} reinstated.", user=user.to_dict())

@adminBP.route("/search", methods=["GET"])
@check_roles(roleOfAdmin)
def search():
    q = (request.args.get("q") or "").strip()
    category = request.args.get("category", "treks")
    results = []

    if q:
        by_id = q.isdigit()
        if category == "treks":
            base = Trek.query
            results = [t.to_dict("admin") for t in (
                base.filter(Trek.id == int(q)).all() if by_id else
                base.filter(or_(Trek.name.ilike(f"%{q}%"), Trek.location.ilike(f"%{q}%"))).all()
            )]
        elif category == "staff":
            base = User.query.filter_by(role=roleOfStaff)
            results = [u.to_dict() for u in (
                base.filter(User.id == int(q)).all() if by_id else
                base.filter(or_(User.full_name.ilike(f"%{q}%"), User.email.ilike(f"%{q}%"))).all()
            )]
        elif category == "trekkers":
            base = User.query.filter_by(role=roleOfTrekker)
            results = [u.to_dict() for u in (
                base.filter(User.id == int(q)).all() if by_id else
                base.filter(or_(User.full_name.ilike(f"%{q}%"), User.email.ilike(f"%{q}%"))).all()
            )]
        else:
            return jsonify(error="category must be one of treks/staff/trekkers"), 400

    return jsonify(query=q, category=category, results=results)

@adminBP.route("/bookings", methods=["GET"])
@check_roles(roleOfAdmin)
def all_bookings():
    bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    return jsonify(bookings=[b.to_dict() for b in bookings])