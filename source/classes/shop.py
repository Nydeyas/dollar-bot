from __future__ import annotations
from typing import TYPE_CHECKING, List

from classes.category import Category

if TYPE_CHECKING:
    from classes.types_base import Category as CategoryPayload


class Shop:
    def __init__(self, name: str, data: List[CategoryPayload]) -> None:
        self.name: str = name
        self.categories: List[Category] = [Category(shop=self, data=d) for d in data]

    def __str__(self) -> str:
        return self.name
