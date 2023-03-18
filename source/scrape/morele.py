from to_thread import to_thread
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime
import re
from math import ceil
from classes.types_base import Category, Item


@to_thread
def get_items(category_name: str, category_link: str) -> Category:
    options = webdriver.FirefoxOptions()
    options.add_argument('-headless')
    browser = webdriver.Firefox(options=options)
    a = datetime.now()

    try:
        browser.get(f'{category_link}/,,,,,,,,0,,,,/1/')
        i_count_str = browser.find_element(By.CSS_SELECTOR,
                                           value="#category > div.category-title-wr.unique-category > span > span").text
    except:
        print(f"Error 1: Cannot find element: 'products count' in morele.get_item_list(), category_name = {category_name}")
        return Category(name=category_name)

    i_count_list = re.findall(r'\d+', i_count_str)

    if i_count_list:
        try:
            items_page = 30
            items_all = int(i_count_list[0])
            pages = ceil(items_all / items_page)
            counter = 0
            item_list = []
            for i in range(1, pages + 1):
                browser.get(f'{category_link}/,,,,,,,,0,,,,/{i}/')
                for j in range(1, items_page + 1):
                    obj = browser.find_element(By.XPATH,
                                               value=f"//div[@data-product-position='{j}']")
                    if not "basket" in obj.find_element(By.CSS_SELECTOR,
                                                        value=f"div > div.cat-product-content > div.cat-product-right > div.cat-product-buttons > a").get_attribute('href'):
                        counter += 1
                        if counter >= items_all:
                            break
                        continue
                    name = obj.get_attribute('data-product-name')
                    price = obj.find_element(By.CSS_SELECTOR,
                                             value=f"div > div.cat-product-content > div.cat-product-right > div.cat-product-price.price-box > div.price-new").text
                    link = obj.find_element(By.CSS_SELECTOR,
                                            value=f"div > div.cat-product-content > div.cat-product-center > div > div.cat-product-name > h2 > a").get_attribute('href')
                    item_list.append(Item(name=name, price=price, link=link))
                    counter += 1
                    if counter >= items_all:
                        break
            result: Category = Category(name=category_name, items=item_list)

        except Exception as e:
            print(f"Error 3: Cannot find element: 'product' in morele.get_item_list(), category_name = {category_name}")
            print(e)
            return Category(name=category_name)

    else:
        browser.close()
        print(
            f"Error 2: Cannot process element: 'products count' in morele.get_item_list(), category_name = {category_name}")
        return Category(name=category_name)

    b = datetime.now()
    print(f"morele.get_item_list(): {b - a}")
    browser.close()
    return result
