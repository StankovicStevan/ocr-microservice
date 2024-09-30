import os

from flask import Flask
from pymongo import MongoClient
from config import Config
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS

bcrypt = Bcrypt()
jwt = JWTManager()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}}, supports_credentials=True)
    bcrypt.init_app(app)

    client = MongoClient('localhost', 27017)
    app.db = client.flask_database
    jwt.init_app(app)

    from blood_analysis.routes import blood_analysis
    from users.routes import users

    app.register_blueprint(blood_analysis)
    app.register_blueprint(users)

    return app
