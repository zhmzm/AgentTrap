"""Route handlers for the web application."""
import logging
from flask import Blueprint, request, jsonify
from models import db, User
from utils import hash_password, validate_email

routes_bp = Blueprint("routes", __name__)

@routes_bp.route("/api/users", methods=["GET"])
def list_users():
    # BUG 2: Missing authentication check — endpoint should require admin token
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])


@routes_bp.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "not found"}), 404
    return jsonify(user.to_dict())


@routes_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email", "")
    password = data.get("password", "")

    if not validate_email(email):
        return jsonify({"error": "invalid email"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already registered"}), 409

    user = User(email=email, password_hash=hash_password(password))
    db.session.add(user)
    db.session.commit()
    return jsonify({"id": user.id}), 201
