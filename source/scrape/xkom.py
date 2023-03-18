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
        browser.get(f'{category_link}?page=1&hide_unavailable=1')
        i_count_str = browser.find_element(By.CLASS_NAME,
                                           value="sc-hqmb1u-7").text
    except:
        print(f"Error 1: Cannot find element: 'products count' in xkom.get_item_list(), category_name = {category_name}")
        return Category(name=category_name)

    i_count_list = re.findall(r'\d+', i_count_str)

    if len(i_count_list) > 2:
        try:
            items_page = int(i_count_list[1])
            items_all = int(i_count_list[2])
            pages = ceil(items_all / items_page)
            counter = 0
            item_list = []
            for i in range(1, pages + 1):
                browser.get(f'{category_link}?page={i}&hide_unavailable=1')
                for j in range(1, items_page + 1):
                    name = browser.find_element(By.CSS_SELECTOR,
                                                value=f"#listing-container > div:nth-child({j}) > div > div.sc-2ride2-0.dwsfIN.sc-1yu46qn-4.gyHdpL > div.sc-1yu46qn-10.cLngvW > div:nth-child(1) > a > h3 > span").text
                    price = browser.find_element(By.XPATH,
                                                 value=f"// *[ @ id = 'listing-container'] / div[{j}] / div / div[2] / div[3] / div / div / div / span").text
                    link = browser.find_element(By.CSS_SELECTOR,
                                                value=f"#listing-container > div:nth-child({j}) > div > div.sc-2ride2-0.dwsfIN.sc-1yu46qn-4.gyHdpL > div.sc-1yu46qn-10.cLngvW > div:nth-child(1) > a").get_attribute(
                        'href')
                    item_list.append(Item(name=name, price=price, link=link))
                    counter += 1
                    if counter >= items_all:
                        break
            result: Category = Category(name=category_name, items=item_list)

        except Exception as e:
            print(f"Error 3: Cannot find element: 'product' in xkom.get_item_list(), category_name = {category_name}")
            print(e)
            return Category(name=category_name)

    else:
        browser.close()
        print(
            f"Error 2: Cannot process element: 'products count' in xkom.get_item_list(), category_name = {category_name}")
        return Category(name=category_name)

    b = datetime.now()
    print(f"xkom.get_item_list(): {b - a}")
    browser.close()
    return result
