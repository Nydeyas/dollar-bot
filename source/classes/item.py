from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from classes.category import Category
    from classes.types_base import Item as ItemPayload


class Item:
    def __init__(self, category: Category, data: ItemPayload) -> None:
        self.category: Category = category
        self.name: str = data['name']
        self.price: str = data['price']
        self.link: str = data['link']

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Item) and [self.name, self.price, self.link] == [other.name, other.price, other.link]
