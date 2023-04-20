# app.py
import waitress
from flask import Flask, request

from logic import Logic

logic: Logic = None

app = Flask(__name__)


def myprint():
    print("rest request: \n", request)
    if request.is_json:
        print(request.get_json())
    else:
        print(request.get_data())


@app.get("/logic/xml")
def get_logic_xml():
    return logic.get_xml()


@app.post("/item/get")
def get_item():
    if request.is_json:
        req_json = request.get_json()
        return logic.get_item(req_json['addr'])
    return {"error": "Request must be JSON"}, 415


def run(host, port, _logic: Logic):
    global app, logic
    logic = _logic
    app.before_request(myprint)
    server = waitress.create_server(app, host=host, port=port, map=None)
    print('REST server run')
    server.run()
