# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import time
import random
from fake_useragent import UserAgent
import datetime
from selenium import webdriver
from xvfbwrapper import Xvfb
from selenium.webdriver.chrome.options import Options
from database import DataBase

db = DataBase()
db.create_table("youla_apartments")
db.create_table("youla_cottages")

# defining chrome options for selenium
options = Options()
options.add_argument("--no-sandbox")


def get_html(url):
    req = requests.get(url, headers={"User-Agent": UserAgent().chrome})
    return req.text.encode(req.encoding)


def get_date(html, k):
    soup = BeautifulSoup(html, "lxml")

    try:
        date = soup.find_all("span", class_="hidden-xs")[k].text.strip()
        if "сегодня" in date:
            return str(datetime.datetime.today()).split()[0]
        elif "вчера" in date:
            return str(datetime.datetime.today() - datetime.timedelta(days=1)).split()[0]
        else:
            return "too old"
    except Exception as e:
        date = "Не указано"
        with open("logs.txt", "a", encoding="utf8") as file:
            file.write(str(e) + " youla get_date\n")
    return date


def get_category(html, k):
    soup = BeautifulSoup(html, "lxml")

    try:
        title = soup.find_all("div", class_="product_item__title")[k].text.split(",")[0].strip()
        if "Квартира" in title:
            return "Квартира"
        elif "Дом" in title:
            return "Дом"
        elif "Коттедж" in title:
            return "Коттедж"
        elif "Таунхаус" in title:
            return "Таунхаус"
        elif "Дача" in title:
            return "Дача"
        elif "Участок" in title:
            return "Участок"
    except Exception as e:
        with open("logs.txt", "a", encoding="utf8") as file:
            file.write(str(e) + " youla get_category\n")
    return None


def get_address(driver):
    try:
        address = driver.find_element_by_tag_name("table").find_elements_by_tag_name("tbody")[0].find_elements_by_tag_name("span")[0].text.strip()
    except Exception as e:
        with open("logs.txt", "a", encoding="utf8") as file:
            file.write(str(e) + " youla get_address\n")
        address = "Не указано"
    return address


def get_selling_type(url):
    if "prodaja" in url:
        return "Продажа"
    elif "arenda" in url:
        if "posutochno" in url:
            return "Аренда (посуточно)"
        return "Аренда (длительный срок)"
    return "Не указано"


def get_price(driver):
    try:
        price = driver.find_element_by_css_selector("div[class='sticky-inner-wrapper']").find_element_by_tag_name("span").text.strip()
    except Exception as e:
        with open("logs.txt", "a", encoding="utf8") as file:
            file.write(str(e) + " youla get_price\n")
        price = "Не указано"
    return price


def get_seller_info(driver):
    seller_type, seller_name = "Не указано", "Не указано"
    try:
        block = driver.find_element_by_css_selector("div[data-test-component='ProductOwner']").find_element_by_tag_name("div")
        seller_name = block.find_element_by_tag_name("a").text.strip()
        seller_name = seller_name[:seller_name.rfind("(")]
        seller_type = block.find_element_by_tag_name("div").text.strip()
    except Exception as e:
        with open("logs.txt", "a", encoding="utf8") as file:
            file.write(str(e) + " youla get_seller_info\n")
    return seller_type, seller_name


def get_photos(driver):
    try:
        images = "\n".join([x.get_attribute("src") for x in driver.find_elements_by_tag_name("div")
                            if x.get_attribute("src") is not None])
        if not images:
            images = driver.find_element_by_css_selector("div[data-test-component='ProductGallery']").find_element_by_tag_name("img").get_attribute("src")
    except Exception as e:
        images = "Не указано"
        with open("logs.txt", "a", encoding="utf8") as file:
            file.write(str(e) + " youla get_photos\n")
    return images


def get_description(driver):
    try:
        description = driver.find_element_by_tag_name("table").find_elements_by_tag_name("tbody")[1].find_element_by_tag_name("td").text.strip()
    except Exception as e:
        description = "Не указано"
        with open("logs.txt", "a", encoding="utf8") as file:
            file.write(str(e) + " youla get_description\n")
    return description


def get_seller_phone(driver):
    try:
        button = driver.find_element_by_css_selector("button[data-test-action='PhoheNumberClick']")
        button.click()
        time.sleep(3)
        phone = driver.find_element_by_xpath('//*[@id="app"]/div[2]/div[10]/div/div/div/div[2]/div[2]/div/a').text.strip()
    except Exception as e:
        phone = "Не указано"
        with open("logs.txt", "a", encoding="utf8") as file:
            file.write(str(e) + " youla get_seller_phone\n")
    return phone


def get_apartment_params(driver):
    material, lift, year, rooms_number, floor, total_floors, total_area, kitchen_area, repair = ["Не указано"] * 9
    try:
        expand = driver.find_element_by_tag_name("table").find_elements_by_tag_name("tbody")[2].find_element_by_tag_name("div")
        expand.click()
        params = driver.find_element_by_tag_name("table").find_elements_by_tag_name("tbody")[2].find_elements_by_tag_name("th")
        values = driver.find_element_by_tag_name("table").find_elements_by_tag_name("tbody")[2].find_elements_by_tag_name("td")
        for i in range(len(params)):
            if "Комнат в квартире" in params[i].text.strip():
                rooms_number = values[i].text.strip()
            elif "Общая площадь" in params[i].text.strip():
                total_area = values[i].text.strip()
            elif "Этаж" in params[i].text.strip():
                floor = values[i].text.strip()
            elif "Этажность дома" in params[i].text.strip():
                total_floors = values[i].text.strip()
            elif "Площадь кухни" in params[i].text.strip():
                kitchen_area = values[i].text.strip()
            elif "Ремонт" in params[i].text.strip():
                repair = values[i].text.strip()
            elif "Лифт" in params[i].text.strip():
                lift = values[i].text.strip()
            elif "Тип дома" in params[i].text.strip():
                material = values[i].text.strip()
            elif "Год постройки" in params[i].text.strip():
                year = values[i].text.strip()
    except Exception as e:
        with open("logs.txt", "a", encoding="utf8") as file:
            file.write(str(e) + " youla get_apartment_params\n")
    return material, lift, year, rooms_number, floor, total_floors, total_area, kitchen_area, repair


def get_cottage_params(driver):
    total_area, material, total_floors, bedrooms, land_area, status, comforts = ["Не указано"] * 7
    try:
        expand = driver.find_element_by_tag_name("table").find_elements_by_tag_name("tbody")[2].find_element_by_tag_name("div")
        expand.click()
        params = driver.find_element_by_tag_name("table").find_elements_by_tag_name("tbody")[2].find_elements_by_tag_name("th")
        values = driver.find_element_by_tag_name("table").find_elements_by_tag_name("tbody")[2].find_elements_by_tag_name("td")
        for i in range(len(params)):
            if "Площадь дома" in params[i].text.strip():
                total_area = values[i].text.strip()
            elif "Материал дома" in params[i].text.strip():
                material = values[i].text.strip()
            elif "Количество спален" in params[i].text.strip():
                bedrooms = values[i].text.strip()
            elif "Площадь участка" in params[i].text.strip():
                land_area = values[i].text.strip()
            elif "Этажей" in params[i].text.strip():
                total_floors = values[i].text.strip()
            elif "Тип участка" in params[i].text.strip():
                status = values[i].text.strip()
            elif any(x in params[i].text.strip() for x in ["Электричество", "Газ", "Водоснабжение", "Отопление", "Гараж", "Санузлы"]):
                if comforts == "Не указано":
                    comforts = params[i].text.strip() + " - " + values[i].text.strip().lower() + "; "
                else:
                    comforts += params[i].text.strip() + " - " + values[i].text.strip().lower() + "; "
    except Exception as e:
        with open("logs.txt", "a", encoding="utf8") as file:
            file.write(str(e) + " youla get_cottage_params\n")
    return total_area, material, total_floors, bedrooms, land_area, status, comforts


def get_apartment_data(url):
    vdisplay = Xvfb()
    vdisplay.start()
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)
    driver.get(url)

    address = get_address(driver)
    selling_type = get_selling_type(url)
    material, lift, year, rooms_number, floor, total_floors, total_area, kitchen_area, repair = get_apartment_params(driver)
    price = get_price(driver)
    if "Аренда" in selling_type:
        if "posutochno" in url:
            price += "/день"
        else:
            price += "/мес."
    seller_type, seller_name = get_seller_info(driver)
    images = get_photos(driver)
    description = get_description(driver)
    phone = get_seller_phone(driver)

    driver.quit()
    vdisplay.stop()

    return [address, price, selling_type, material, lift, year, rooms_number, floor, total_floors, total_area,
            kitchen_area, repair, seller_type, images, description, seller_name, phone]


def get_cottage_data(url, category):
    vdisplay = Xvfb()
    vdisplay.start()
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)
    driver.get(url)

    address = get_address(driver)
    selling_type = get_selling_type(url)
    price = get_price(driver)
    if "Аренда" in selling_type:
        if "posutochno" in url:
            price += "/день"
        else:
            price += "/мес."
    total_area, material, total_floors, bedrooms, land_area, status, comforts = get_cottage_params(driver)
    images = get_photos(driver)
    description = get_description(driver)
    phone = get_seller_phone(driver)

    driver.quit()
    vdisplay.stop()

    if category == "Участок":
        material, total_floors = "Участок", "Участок"

    return [address, price, selling_type, category, total_area, material, total_floors, bedrooms,
            land_area, status, comforts, images, description, phone]


def crawl_page(html):
    soup = BeautifulSoup(html, "lxml")
    # так как пагинация динамическая и мы не можем получить число страниц, проверяем, есть ли на странице объявления
    offers = soup.find_all("li", class_="product_item")
    if offers is None or not offers:
        print("Парсинг завершен youla")
        return True
    k = 0
    for offer in offers:
        try:
            category = get_category(html, k)
            date = get_date(html, k)
            if date == "too old" and len(offer.get("class")) == 1:
                print("Парсинг завершен youla")
                return True
            k += 1
            url = "https://youla.ru" + offer.find("a").get("href")
            #print(url)
            if category is None or "saratov" not in url:
                time.sleep(random.uniform(5, 8))
                continue
            data = []
            if category == "Квартира":
                data = get_apartment_data(url)
                db.insert_data("youla_apartments", data)
                with open("total_data.txt", "a", encoding="utf8") as file:
                    file.write("%s--%s--%s--%s\n" % (data[0], data[6], data[9], url))
            elif any(x in category for x in ["Дом", "Коттедж", "Таунхаус", "Дача", "Участок"]):
                data = get_cottage_data(url, category)
                data.append(date)
                db.insert_data("youla_cottages", data)
                with open("total_data.txt", "a", encoding="utf8") as file:
                    file.write("%s--%s--%s--%s\n" % (data[0], data[3], data[4], url))

            #print(*data, sep="\n")
            #print("--------------------------------------")
            print("parsed page youla")

        except Exception as e:
            with open("logs.txt", "a", encoding="utf8") as file:
                file.write(str(e) + " youla crawl_page\n")
            #print(e)
            #print("Ошибка в crawl_page")


def parse(url):
    completed = False
    page = 1
    while not completed:
        url_gen = url[:url.rfind("=") + 1] + str(page)
        completed = crawl_page(get_html(url_gen))
        page += 1


def main():
    url = "https://youla.ru/saratov/nedvijimost?attributes[sort_field]=date_published&attributes[term_of_placement][from]=-1%20day&attributes[term_of_placement][to]=now&page=1"
    parse(url)


if __name__ == "__main__":
    main()
