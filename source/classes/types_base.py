from typing import TypedDict, List
from typing_extensions import NotRequired


class Item(TypedDict):
    name: str
    price: str
    link: str


class Category(TypedDict):
    name: str
    items: NotRequired[List[Item]]
