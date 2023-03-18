from datetime import datetime
from math import ceil
import pandas as pd
import importlib
import pickle

from typing import Dict, Tuple, List

from classes.shop import Shop
from classes.types_base import Category as CategoryPayload


async def collect_data() -> Tuple[List[str], List[str], List[Shop]]:
    active_data = {
        "xkom": {
            "karty graficzne": "https://www.x-kom.pl/g-5/c/345-karty-graficzne.html",
            "procesory": "https://www.x-kom.pl/g-5/c/11-procesory.html",
            "płyty główne": "https://www.x-kom.pl/g-5/c/14-plyty-glowne.html"
        },
        "morele": {
            "karty graficzne": "https://www.morele.net/kategoria/karty-graficzne-12",
            "procesory": "https://www.morele.net/kategoria/procesory-45",
            "płyty główne": "https://www.morele.net/kategoria/plyty-glowne-42"
        },
        "komputronik": {
            "karty graficzne": "https://www.komputronik.pl/category/1099/karty-graficzne.html",
            "procesory": "https://www.komputronik.pl/category/401/procesory.html",
            "płyty główne": "https://www.komputronik.pl/category/757/plyty-glowne.html",
        }
    }

    assert all(
        map(lambda v: True if v.keys() == list(active_data.values())[0].keys() else False, active_data.values())), \
        "Error: All shops must have the same categories!"

    shops = [s for s in active_data.keys()]
    categories = [c for c in list(active_data.values())[0]]

    # await scrape_data(active_data)

    data = get_data_for_bot(shops, categories)

    return shops, categories, data


async def scrape_data(data: Dict[str, Dict[str, str]]) -> None:
    counter = 0
    tasks_count = (len(data) * len(list(data.values())[0]))
    print("Collecting products data...")
    st = datetime.now()
    for shop, categories in data.items():
        for category, link in categories.items():
            module = importlib.import_module(fr"scrape.{shop}")
            data = await module.get_items(category, fr'{link}')
            save_csv(data, fr'data/csv/{shop}/{category}.csv')
            save_pkl(data, fr'data/pkl/{shop}/{category}.pkl')
            counter += 1
            et = datetime.now()
            time_remain = (et - st) * ((tasks_count - counter) / counter)
            print(f"Done {counter}/{tasks_count} operations.")
            print(f"Remaining time approx: {ceil(time_remain.total_seconds() / 60)} min.")
    print("Data collected successfully.")


def get_data_for_bot(shops: List[str], categories: List[str]) -> List[Shop]:
    """Loads data to bot"""
    data = []
    for s in shops:
        categories_data: List[CategoryPayload] = []
        for c in categories:
            payload: CategoryPayload = load_pkl(fr'data/pkl/{s}/{c}.pkl')
            categories_data.append(payload)
        shop = Shop(s, categories_data)
        data.append(shop)
    return data


def save_pkl(obj: CategoryPayload, filename: str) -> None:
    """Saves Python object as a pickle file."""
    with open(filename, 'wb') as out:  # Overwrites any existing file.
        pickle.dump(obj, out, pickle.HIGHEST_PROTOCOL)


def load_pkl(filename: str) -> CategoryPayload:
    """Loads saved Python object from local data."""
    with open(filename, 'rb') as inp:
        return pickle.load(inp)


def save_csv(data: CategoryPayload, filename: str) -> None:
    """Saves Category type class object as a csv type file."""
    columns = ["product", "price", "link"]
    obj_df = pd.DataFrame([[d['name'], d['price'], d['link']] for d in data.get('items', [])], columns=columns)
    obj_df.to_csv(filename, index=False)
