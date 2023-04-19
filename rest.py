# app.py
from flask import Flask, request

from logic import Logic

logic : Logic = None

app = Flask(__name__)


@app.get("/logic/xml")
def get_logic_xml():
    return logic.get_xml()


@app.post("/item/get")
def get_item():
    if request.is_json:
        req_json = request.get_json()
        return logic.get_item(req_json['addr'])
    return {"error": "Request must be JSON"}, 415


def run(port, _logic: Logic):
    global app, logic
    logic = _logic
    app.run(port=port)
