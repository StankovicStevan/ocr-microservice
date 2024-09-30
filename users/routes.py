from flask import Flask, request, jsonify, Blueprint, current_app
from __init__ import bcrypt
from pymongo import MongoClient
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import datetime

users = Blueprint('users', __name__)


@users.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    if not username or not password or role not in ['admin', 'user']:
        return jsonify({"message": "Missing or incorrect parameters"}), 400

    return create_user(username, password, role)


def create_user(username, password, role):
    users = current_app.db.users
    # Check if user already exists
    if users.find_one({"username": username}):
        return jsonify({"message": "User already exists!"}), 400

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Store the user in MongoDB
    user = {
        "username": username,
        "password": hashed_password,
        "role": role,
        "created_at": datetime.datetime.utcnow()
    }
    result = users.insert_one(user)
    current_app.logger.info(f"User id: {result.inserted_id}")

    return jsonify({"message": f"User with username {username} has been created successfully."}), 201


@users.route('/login', methods=['POST'])
def login():
    users = current_app.db.users
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = users.find_one({"username": username})
    current_app.logger.info(user)

    if user and bcrypt.check_password_hash(user['password'], password):
        access_token = create_access_token(
            identity={"user_id": str(user["_id"]), "username": username, "role": user['role']})

        return jsonify({"message": "User successfully logged in.", "access_token": access_token}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401


@users.route('/admin-only', methods=['GET'])
@jwt_required()
def admin_only():
    current_user = get_jwt_identity()

    if current_user['role'] != 'admin':
        return {"msg": "Admins only!"}, 403

    return {"msg": "Welcome, Admin!"}, 200


@users.route('/profile', methods=['GET'])
@jwt_required()  # Ensure the user is authenticated
def profile():
    current_user = get_jwt_identity()  # Get the user identity from the JWT token
    return jsonify(logged_in_as=current_user), 200
