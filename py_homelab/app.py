import os
import string
import random
from flask_restx import Resource, Api
from flask_bcrypt import Bcrypt
from flask import Flask, request
from throw_out_py import Map
from .database.main import db
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from .resources.main import api as apiNs
from .pm import ProcessManager

load_dotenv()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["MONGOALCHEMY_DATABASE"] = os.getenv("DB_NAME") or "py-homelab"
app.config["MONGOALCHEMY_CONNECTION_STRING"] = os.getenv(
    "DB_URI") or "mongodb://localhost"
app.config['PROPAGATE_EXCEPTIONS'] = True

db.init_app(app)
jwt = JWTManager(app)

api = Api(app, catch_all_404s=True, version=0.1,
          title="REST HTTP API's Gateway",
          description="REST API gateway")
api.add_namespace(apiNs, path="/api")

bcrypt = Bcrypt(app)
