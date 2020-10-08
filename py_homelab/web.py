import pymongo
import os
from flask import Flask, request
from .pm import ProcessManager
from .map import Map

db_client = pymongo.MongoClient(os.environ.get(
    "DB_URI") or "mongodb://localhost:27017/")

db = db_client[os.environ.get("DB_NAME") or "py-homelab"]

app = Flask(__name__)
pm = ProcessManager()


@app.route("/")
def hello_world():
    return {"message": "Hello world!"}


@app.route("/deploy", methods=['POST'])
def deploy():
    return pm.deploy(Map(request.json))


app.run(host="0.0.0.0")
