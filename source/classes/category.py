from __future__ import annotations
from typing import TYPE_CHECKING, List

from classes.item import Item

if TYPE_CHECKING:
    from classes.shop import Shop
    from classes.types_base import Category as CategoryPayload


class Category:
    def __init__(self, shop: Shop, data: CategoryPayload) -> None:
        self.shop: Shop = shop
        self.name: str = data['name']
        self.items: List[Item] = [Item(category=self, data=d) for d in data.get('items', [])]

    def __str__(self) -> str:
        return self.name
