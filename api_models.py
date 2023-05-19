from typing import Union

from pydantic import BaseModel, Field


class SetState(BaseModel):
    addr: str
    state: str


class DelItem(BaseModel):
    addr: str


class SetLogic(BaseModel):
    xml: str


class GetState(BaseModel):
    addr: Union[str, list[str]]


class SetItem(BaseModel):
    type: str = Field(title="Operation type (write, append, remove)")
    tag: str = Field(title="Tag of item ('item', 'area', etc.)")
    area: str = Field(title="Name of area. if set item in root - set 'smart-house'")
    data: dict = Field(title="Attributes and childs of added item in format key:value")


class GetHistory(BaseModel):
    addr: str
    range_time: list
    scale: int


class SendMessage(BaseModel):
    addr: str
    message_type: int
    message: str
