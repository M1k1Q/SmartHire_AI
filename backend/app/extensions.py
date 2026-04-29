"""
extensions.py — Flask extension instances (initialized without app context).
Using the application factory pattern to avoid circular imports.
"""
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt

mongo = PyMongo()
jwt = JWTManager()
cors = CORS()
bcrypt = Bcrypt()
