# app.py
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from logic import Logic

logic: Logic = None
app = FastAPI()


class Item(BaseModel):
    addr: str


@app.get("/logic/xml")
def get_logic_xml():
    return logic.get_xml()


@app.post("/item/get")
def get_item(item: Item):
    print(item)
    return logic.get_item(item.addr)


def run(host, port, _logic: Logic):
    global app, logic
    logic = _logic
    print('REST server run')
    uvicorn.run(app, host='192.168.1.101', port=5000)
