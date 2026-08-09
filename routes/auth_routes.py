import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from extensions import database
from models import User, roleOfStaff, roleOfTrekker, roleOfAdmin, status_pending_staff, status_active_trekker

authenticationBP = Blueprint("auth", __name__)

#Email format to be followed
email_regex = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def _validate_registration(data):
    errors = {}
    fullName = (data.get("fullName") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role") or roleOfTrekker

    if not fullName or len(fullName) > 120:
        errors["fullName"] = "Full name is required (max 120 chars)."
    if not email or not email_regex.match(email):
        errors["email"] = "A valid email is required."
    if not password or len(password) < 6:
        errors["password"] = "Password must be at least 6 characters."
    #Admin accounts are created seperately 
    if role not in (roleOfStaff, roleOfTrekker):
        errors["role"] = "Role must be 'staff' or 'trekker' (admin cannot self-register)."
    return errors, fullName, email, password, role


@authenticationBP.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    errors, fullName, email, password, role = _validate_registration(data)
    if errors:
        return jsonify(error="Validation failed.", fields=errors), 400

    #Prevent duplicate accounts
    if User.query.filter_by(email=email).first():
        return jsonify(error="An account with this email already exists."), 409

    #Staff accounts require admin approval; trekkers can login immediately
    user = User(
        fullName=fullName,
        email=email,
        phone=(data.get("phone") or "").strip() or None,
        role=role,
        status=status_pending_staff if role == roleOfStaff else status_active_trekker,
    )
    user.set_password(password)
    database.session.add(user)
    database.session.commit()

    message = (
        "Staff application submitted. You may log in once an Admin approves your account."
        if role == roleOfStaff else
        "Account created successfully. You may now log in."
    )
    return jsonify(message=message, user=user.to_dict()), 201

@authenticationBP.route("/login", methods=["POST"])
def login():
    #Authenticate a user and issue a JWT access token
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    #Staff members must be approved
    if not user or not user.check_password(password):
        return jsonify(error="Invalid email or password."), 401
    if user.is_blacklisted():
        return jsonify(error="This account has been blacklisted."), 403
    if user.role == roleOfStaff and user.status == status_pending_staff:
        return jsonify(error="Your staff account is awaiting Admin approval."), 403

    additional_claims = {"role": user.role, "status": user.status, "fullName": user.fullName}
    token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
    return jsonify(access_token=token, user=user.to_dict()), 200

@authenticationBP.route("/me", methods=["GET"])
@jwt_required()
def me():
    #Currently authenticated user's details
    user = User.query.get_or_404(int(get_jwt_identity()))
    return jsonify(user=user.to_dict())

@authenticationBP.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user = User.query.get_or_404(int(get_jwt_identity()))
    data = request.get_json(silent=True) or {}
    fullName = (data.get("fullName") or "").strip()
    phone = (data.get("phone") or "").strip()

    if fullName:
        if len(fullName) > 120:
            return jsonify(error="Full name too long."), 400
        user.fullName = fullName
    user.phone = phone or None

    #Update the password only when a new one is provided
    new_password = data.get("password")
    if new_password:
        if len(new_password) < 6:
            return jsonify(error="Password must be at least 6 characters."), 400
        user.set_password(new_password)

    database.session.commit()
    return jsonify(message="Profile updated.", user=user.to_dict())