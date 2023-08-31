from typing import Union

from pydantic import BaseModel, Field


class SetState(BaseModel):
    addr: str = Field(title="Address of item")
    state: str = Field(title="Setter state")


class DelItem(BaseModel):
    addr: str = Field(title="Address of item")


class SetLogic(BaseModel):
    xml: str = Field(title="Xml data to be loaded into logic.xml")


class GetState(BaseModel):
    addr: Union[str, list[str]] = Field(title="Address of item or list of addresses of items")


class SetItem(BaseModel):
    type: str = Field(title="Operation type (write, append, remove)")
    tag: str = Field(title="Tag of item ('item', 'area', etc.)")
    area: str = Field(title="Name of area. if set item in root - set 'smart-house'")
    data: dict = Field(title="Attributes and childs of added item in format key:value")


class GetHistory(BaseModel):
    addr: str = Field(title="Address of item")
    range_time: list[int] = Field(title="List of timestamps, start-end time")
    scale: int = Field(title="Period in minutes between values")


class SendMessage(BaseModel):
    addr: str = Field(title="Address of device, which push-message will be sent")
    message_type: int = Field(title="Type of push-message")
    message: str = Field(title="Message text")


class GetToken(BaseModel):
    username: str
    password: str
