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
        browser.get(f'{category_link}?showBuyActiveOnly=1&p=1')
        i_count_str = browser.find_element(By.CLASS_NAME,
                                           value="tests-product-count").text
    except:
        print(f"Error 1: Cannot find element: 'products count' in komputronik.get_item_list(), category_name = {category_name}")
        return Category(name=category_name)

    i_count_list = re.findall(r'\d+', i_count_str)

    if i_count_list:
        try:
            items_page = 20
            items_all = int(i_count_list[0])
            pages = ceil(items_all / items_page)
            counter = 0
            item_list = []
            for i in range(1, pages + 1):
                browser.get(f'{category_link}?page={i}&hide_unavailable=1')
                for j in range(1, items_page + 1):
                    obj = browser.find_element(By.CSS_SELECTOR,
                                            value=f"#products-list > div.lg\:col-span-9 > div.mt-10-mobile > div:nth-child({j})")
                    name = obj.find_element(By.TAG_NAME,value="a").text
                    price = obj.find_element(By.XPATH,
                                            value="div[1]/div[3]/div[2]/div/div").text
                    link = obj.find_element(By.TAG_NAME,
                                            value=f"a").get_attribute('href')
                    item_list.append(Item(name=name, price=price, link=link))
                    counter += 1
                    if counter >= items_all:
                        break
            result: Category = Category(name=category_name, items=item_list)

        except Exception as e:
            print(f"Error 3: Cannot find element: 'product' in komputronik.get_item_list(), category_name = {category_name}")
            print(e)
            return Category(name=category_name)

    else:
        browser.close()
        print(
            f"Error 2: Cannot process element: 'products count' in komputronik.get_item_list(), category_name = {category_name}")
        return Category(name=category_name)

    b = datetime.now()
    print(f"komputronik.get_item_list(): {b - a}")
    browser.close()
    return result
