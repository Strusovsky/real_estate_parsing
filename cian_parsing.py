import requests
from bs4 import BeautifulSoup
import time
import random
from fake_useragent import UserAgent
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os


def get_html(url):
    req = requests.get(url, headers={"User-Agent": UserAgent().chrome})
    return req.text.encode(req.encoding)


def get_title(soup):
    try:
        title = soup.find("h1").text.strip()
    except Exception as e:
        print(str(e) + " title")
        title = "Не указано"
    return title


def get_address(soup):
    try:
        address = soup.find("address").text.strip()
        if "На карте" in address:
            address = address[:address.rfind("На карте")]
    except Exception as e:
        print(str(e) + " address")
        address = "Не указано"
    return address


def get_price(soup):
    try:
        price = soup.find("span", {"itemprop": "price"})
        if price is not None:
            price = price.text.strip()
        else:
            price = "от " + soup.find("span", {"itemprop": "lowPrice"}).text.strip() + \
                    " до " + soup.find("span", {"itemprop": "highPrice"}).text.strip() + "/мес."
    except Exception as e:
        print(str(e) + " price")
        price = "Не указано"
    return price


def get_selling_type(soup):
    try:
        paragraphs = [x for x in soup.find_all("p") if x.get("class") is not None
                      and len(x.get("class")) == 1 and x.get("class")[0].startswith("description--")]
        if paragraphs:
            selling_type = paragraphs[0].text.strip()
        else:
            selling_type = "Не указано"
    except Exception as e:
        print(str(e) + " selling_type")
        selling_type = "Не указано"
    return selling_type


def get_seller_type(soup):
    try:
        divs = [x for x in soup.find_all("div") if x.get("class") is not None
                and len(x.get("class")) == 1 and "honest-container" in x.get("class")[0]]
        if not divs:
            seller_type = "Не указано"
        else:
            seller_type = divs[0].text.strip()
            if seller_type is not None and seller_type.lower() == "собственник":
                seller_type = "Собственник"
            else:
                seller_type = "Посредник"
    except Exception as e:
        print(str(e) + " seller_type")
        seller_type = "Не указано"
    return seller_type


def get_photos(url):
    try:
        driver = webdriver.Chrome(executable_path=chrome_driver)
        driver.get(url)

        images = []
        images_list = driver.find_elements_by_class_name("fotorama__img")
        images_list = [x.get_attribute("src") for x in images_list if "-2." in x.get_attribute("src")]
        for image in images_list:
            link = image.replace("-2.", "-1.")
            images.append(link)
        images = "\n".join(images)
    except Exception as e:
        print(str(e) + " images")
        images = "Не указано"
    return images


def get_description(soup):
    try:
        paragraphs = [x for x in soup.find_all("p") if x.get("class") is not None
                      and len(x.get("class")) == 1 and x.get("class")[0].startswith("description-text--")]
        description = paragraphs[0].text.strip()
    except Exception as e:
        print(str(e) + " description")
        description = "Не указано"
    return description


def get_date(soup):
    try:
        date = soup.find("div", id="frontend-offer-card").find("main").find_all("div")[4].text.strip()
        if "вчера" in date:
            date = str(datetime.datetime.today() - datetime.timedelta(days=1)).split()[0]
        elif "сегодня" in date:
            date = str(datetime.datetime.today()).split()[0]
        else:
            date = "too old"
    except Exception as e:
        print(str(e) + " date")
        date = "Не указано"
    return date


def driver_get_phone_and_images(url):
    driver = webdriver.Chrome(executable_path=chrome_driver)
    driver.get(url)

    try:
        images = []
        images_list = driver.find_elements_by_class_name("fotorama__img")
        images_list = [x.get_attribute("src") for x in images_list if "-2." in x.get_attribute("src")]
        for image in images_list:
            link = image.replace("-2.", "-1.")
            images.append(link)
        images = "\n".join(images)
        if not images:
            # берем с обложки
            images = driver.find_element_by_class_name("fotorama__img").get_attribute("src")
    except Exception as e:
        print(str(e) + " images")
        images = "Не указано"

    try:
        button = [x for x in driver.find_elements_by_tag_name("button") if x.text.strip() == "Показать телефон"][-1]
        button.click()
        time.sleep(3)
        phone = "\n".join([x.text.strip() for x in driver.find_elements_by_tag_name("a") if x.get_attribute("class") is not None
                           and x.get_attribute("class").startswith("phone--")])
    except Exception as e:
        phone = "Не указано"
        print(str(e) + " phone")
    driver.quit()
    return images, phone


def get_apartment_params(soup):
    block_type, rooms_number, total_floors, total_area, material, year = ["Не указано"] * 6
    try:
        main_params = [x.text.strip() for x in soup.find_all("div") if x.get("class") is not None
                       and len(x.get("class")) == 1 and x.get("class")[0].startswith("info-title--")]
        main_values = [x.text.strip() for x in soup.find_all("div") if x.get("class") is not None
                       and len(x.get("class")) == 1 and x.get("class")[0].startswith("info-text--")]
        for i in range(len(main_params)):
            if "Общая" in main_params[i]:
                total_area = main_values[i]
            elif "Построен" in main_params[i]:
                year = main_values[i]

        desc_params = [x.text.strip() for x in soup.find_all("span") if x.get("class") is not None
                       and len(x.get("class")) == 1 and x.get("class")[0].startswith("name--")]
        desc_values = [x.text.strip() for x in soup.find_all("span") if x.get("class") is not None
                       and len(x.get("class")) == 1 and x.get("class")[0].startswith("value--")]
        for i in range(len(desc_params)):
            if "Тип жилья" in desc_params[i]:
                block_type = desc_values[i]
            elif "Количество комнат" in desc_params[i]:
                rooms_number = desc_values[i]
            elif "Этажей в доме" in desc_params[i]:
                total_floors = desc_values[i]
            elif "Тип дома" in desc_params[i]:
                material = desc_values[i]

        if year == "Не указано":
            building_params = [x.text.strip() for x in soup.find_all("div") if x.get("class") is not None
                               and len(x.get("class")) == 1 and x.get("class")[0].startswith("name--")]
            building_values = [x.text.strip() for x in soup.find_all("div") if x.get("class") is not None
                               and len(x.get("class")) == 1 and x.get("class")[0].startswith("value--")]
            for i in range(len(building_params)):
                if "Год постройки" in building_params[i]:
                    year = building_values[i]
                    break
    except Exception as e:
        print(str(e) + " apartment params")
    return block_type, rooms_number, total_floors, total_area, material, year


def get_cottage_params(soup):
    total_area, material, land_area, status, comforts = ["Не указано"] * 5
    try:
        main_params = [x.text.strip() for x in soup.find_all("div") if x.get("class") is not None
                       and len(x.get("class")) == 1 and x.get("class")[0].startswith("info-title--")]
        main_values = [x.text.strip() for x in soup.find_all("div") if x.get("class") is not None
                       and len(x.get("class")) == 1 and x.get("class")[0].startswith("info-text--")]
        for i in range(len(main_params)):
            if "Общая" in main_params[i]:
                total_area = main_values[i]
            elif "Участок" in main_params[i]:
                land_area = main_values[i]
            elif "Тип дома" in main_params[i]:
                material = main_values[i]

        comforts_list = [x.text.strip() for x in soup.find_all("li") if x.get("class") is not None
                         and len(x.get("class")) == 2 and x.get("class")[0].startswith("item--")]
        if comforts:
            comforts = "; ".join(comforts_list)

        desc_params = [x.text.strip() for x in soup.find_all("span") if x.get("class") is not None
                       and len(x.get("class")) == 1 and x.get("class")[0].startswith("name--")]
        desc_values = [x.text.strip() for x in soup.find_all("span") if x.get("class") is not None
                       and len(x.get("class")) == 1 and x.get("class")[0].startswith("value--")]
        for i in range(len(desc_params)):
            if "Статус участка" in desc_params[i]:
                status = desc_values[i]
            elif land_area == "Не указано" and "Площадь участка" in desc_params[i]:
                land_area = desc_values[i]
            elif material == "Не указано" and "Тип дома" in desc_params[i]:
                material = desc_values[i]
    except Exception as e:
        print(str(e) + " cottage params")
    return total_area, material, land_area, status, comforts


def get_commercial_params(soup):
    office_class, floor, furniture, entrance = ["Не указано"] * 4
    try:
        main_params = [x.text.strip() for x in soup.find_all("div") if x.get("class") is not None
                       and len(x.get("class")) == 1 and x.get("class")[0].startswith("info-title--")]
        main_values = [x.text.strip() for x in soup.find_all("div") if x.get("class") is not None
                       and len(x.get("class")) == 1 and x.get("class")[0].startswith("info-text--")]
        for i in range(len(main_params)):
            if "Класс" in main_params[i]:
                office_class = main_values[i]
            elif "Этаж" in main_params[i]:
                floor = main_values[i]

        desc_params = [x.text.strip() for x in soup.find_all("span") if x.get("class") is not None
                       and len(x.get("class")) == 1 and x.get("class")[0].startswith("name--")]
        desc_values = [x.text.strip() for x in soup.find_all("span") if x.get("class") is not None
                       and len(x.get("class")) == 1 and x.get("class")[0].startswith("value--")]
        for i in range(len(desc_params)):
            if "Вход" in desc_params[i]:
                entrance = desc_values[i]
            elif "Мебель" in desc_params[i]:
                furniture = desc_values[i]
    except Exception as e:
        print(str(e) + " commercials params")
    return office_class, floor, furniture, entrance


def get_apartment_data(html, url):
    soup = BeautifulSoup(html, "lxml")

    # title = get_title(soup)
    address = get_address(soup)
    price = get_price(soup)
    block_type, rooms_number, total_floors, total_area, material, year = get_apartment_params(soup)
    selling_type = get_selling_type(soup)
    seller_type = get_seller_type(soup)
    description = get_description(soup)
    date = get_date(soup)
    images, phone = driver_get_phone_and_images(url)

    return [address, block_type, rooms_number, price, total_area, total_floors, material,
            year, selling_type, images, description, seller_type, date, phone]


def get_cottage_data(html, url):
    soup = BeautifulSoup(html, "lxml")

    title = get_title(soup)
    address = get_address(soup)
    price = get_price(soup)
    cottage_type = title.split(",")[0]
    total_area, material, land_area, status, comforts = get_cottage_params(soup)
    selling_type = get_selling_type(soup)
    description = get_description(soup)
    date = get_date(soup)
    images, phone = driver_get_phone_and_images(url)

    return [address, cottage_type, price, total_area, material, land_area, status,
            comforts, selling_type, images, description, date, phone]


def get_commercial_data(html, url):
    soup = BeautifulSoup(html, "lxml")

    title = get_title(soup)
    address = get_address(soup)
    price = get_price(soup)

    if "офис" in title.lower():
        object_type = "Офисное помещение"
    elif "торговая площадь" in title.lower():
        object_type = "Торговая площадь"
    elif "склад" in title.lower():
        object_type = "Склад"
    elif "своб. назнач." in title.lower() or "свободное назначение" in title.lower():
        object_type = "Свободного назначения"
    elif "гараж" in title.lower():
        object_type = "Гараж"
    elif "автосервис" in title.lower():
        object_type = "Автосервис"
    elif "производство" in title.lower():
        object_type = "Производство"
    elif "готовый бизнес" in title.lower():
        object_type = "Готовый бизнес"
    else:
        object_type = "Не указано"

    office_class, floor, furniture, entrance = get_commercial_params(soup)
    if object_type != "Офисное помещение":
        office_class = "Не офис"
    description = get_description(soup)
    date = get_date(soup)
    images, phone = driver_get_phone_and_images(url)

    return [address, object_type, price, office_class, floor, furniture, entrance, images,
            description, date, phone]


def crawl_page(html, category, sell_type):
    soup = BeautifulSoup(html, "lxml")
    # так как пагинация динамическая и мы не можем получить число страниц, проверяем, есть ли на странице объявления
    offers = [x for x in soup.find("div", id="frontend-serp").find("div").find_all("div")
              if x.get("class") is not None and "offer-container" in x.get("class")[0]]
    for offer in offers:
        try:
            # TODO: проверить на дубликат
            # TODO: проверить, существует ли страница
            url = offer.find("a").get("href")
            print(url)
            data = []
            if category == "apartments":
                data = get_apartment_data(get_html(url), url)
            elif category == "cottages":
                data = get_cottage_data(get_html(url), url)
            elif category == "commercials":
                data = get_commercial_data(get_html(url), url)

            if data[-2] == "too old":
                return True

            data.insert(1, sell_type)
            print(*data, sep="\n")
            print("--------------------------------------")

        except Exception as e:
            print(e)
            print("Ошибка в crawl_page")

        time.sleep(random.uniform(5, 8))


def parse(category_url, category_name, sell_type):

    # for page in range(1, total_pages + 1):
    #     url_gen = base_url + page_part + str(page) + parameters_part
    #     crawl_page(get_html(url_gen))

    for page in range(1, 2):
        url_gen = category_url[:category_url.rfind("=") + 1] + str(page)
        completed = crawl_page(get_html(url_gen), category_name, sell_type)
        if completed:
            break


def main():
    url_apartments_sell = "https://saratov.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&region=4609&room1=1&room2=1&room3=1&room4=1&room5=1&room6=1&room7=1&room9=1&totime=86400&page=1"
    parse(url_apartments_sell, "apartments", "Продажа")

    url_apartments_rent = "https://saratov.cian.ru/cat.php?deal_type=rent&engine_version=2&offer_type=flat&region=4609&room1=1&room2=1&room3=1&room4=1&room5=1&room6=1&room7=1&room9=1&totime=86400&page=1"
    parse(url_apartments_rent, "apartments", "Аренда")

    url_cottages_sell = "https://saratov.cian.ru/cat.php?deal_type=sale&engine_version=2&object_type%5B0%5D=1&offer_type=suburban&region=4609&totime=86400&page=1"
    parse(url_cottages_sell, "cottages", "Продажа")

    url_cottages_rent = "https://saratov.cian.ru/cat.php?deal_type=rent&engine_version=2&object_type%5B0%5D=1&offer_type=suburban&region=4609&totime=86400&page=1"
    parse(url_cottages_rent, "cottages", "Аренда")

    url_commercials_sell = "https://saratov.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=offices&office_type%5B0%5D=1&office_type%5B10%5D=12&office_type%5B1%5D=2&office_type%5B2%5D=3&office_type%5B3%5D=4&office_type%5B4%5D=5&office_type%5B5%5D=6&office_type%5B6%5D=7&office_type%5B7%5D=9&office_type%5B8%5D=10&office_type%5B9%5D=11&region=4609&totime=86400&page=1"
    parse(url_commercials_sell, "commercials", "Продажа")

    url_commercials_rent = "https://saratov.cian.ru/cat.php?deal_type=rent&engine_version=2&offer_type=offices&office_type%5B0%5D=1&office_type%5B10%5D=12&office_type%5B1%5D=2&office_type%5B2%5D=3&office_type%5B3%5D=4&office_type%5B4%5D=5&office_type%5B5%5D=6&office_type%5B6%5D=7&office_type%5B7%5D=9&office_type%5B8%5D=10&office_type%5B9%5D=11&region=4609&totime=86400&page=1"
    parse(url_commercials_rent, "commercials", "Аренда")


if __name__ == "__main__":
    break_point = ""  # на каких записях скрипт остановился в прошлый раз

    # defining chrome options for selenium
    # options = Options()
    # options.add_experimental_option("excludeSwitches", ["ignore-certificate-errors"])
    # options.add_argument('--disable-gpu')
    # options.add_argument('--headless')
    #
    chrome_driver = os.getcwd() + "\\chromedriver.exe"

    main()