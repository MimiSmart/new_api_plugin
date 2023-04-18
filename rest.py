# app.py
from flask import Flask, request

from parse_logic import Logic

logic = Logic()

app = Flask(__name__)


@app.get("/logic/xml")
def get_logic_xml():
    return logic.get_xml()


@app.post("/item/get")
def get_item():
    if request.is_json:
        req_json = request.get_json()
        return logic.get_item(req_json['addr'])
        # country["id"] = _find_next_id()
        # countries.append(country)
        # return country, 201
    return {"error": "Request must be JSON"}, 415


def run():
    global app
    app.run(port=5000)
