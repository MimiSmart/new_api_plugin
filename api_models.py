from typing import Union

from pydantic import BaseModel, Field


class DelItem(BaseModel):
    addr: str


class GetState(BaseModel):
    addr: Union[str, list[str]]


class SetItem(BaseModel):
    type: str = Field(title="Operation type (write, append, remove)")
    tag: str = Field(title="Tag of item ('item', 'area', etc.)")
    area: str = Field(title="Name of area. if set item in root - set 'smart-house'")
    data: dict = Field(title="Attributes and childs of added item in format key:value")
