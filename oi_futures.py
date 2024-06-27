import re
import time
import os
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd


COLUMN = [1, 2, 3, 4, 5]
ROW = [1, 2, 3]
URL = 'https://www.moex.com/ru/contract.aspx?code='
DIR_NAME = os.getcwd()
def split_dict(dic, nom):
    """Разделение словаря на несколько словарей"""
    keys = list(dic.keys())
    for i in range(0, len(keys), nom):
        yield {k: dic[k] for k in keys[i: i + nom]}


def change_keys(chunks) -> list:
    """Замена цифрового ключа на символьный"""
    replacements = ['Code', 'Price', 'D_Pr', 'Vol_rub', 'Vol_con', 'OI', 'D_OI', 'Ras', 'Day']
    new_dict_1 = {}
    new_dict_2 = {}
    new_dict_3 = {}
    new_dict_4 = {}
    new_chunks = []

    for nn, item in enumerate(chunks, start=1):
        if nn == 1:
            new_dict_1 = dict(zip(replacements, list(item.values())))
            new_chunks.append(new_dict_1)
        elif nn == 2:
            new_dict_2 = dict(zip(replacements, list(item.values())))
            new_chunks.append(new_dict_2)
        elif nn == 3:
            new_dict_3 = dict(zip(replacements, list(item.values())))
            new_chunks.append(new_dict_3)
        elif nn == 4:
            new_dict_4 = dict(zip(replacements, list(item.values())))
            new_chunks.append(new_dict_4)
    return new_chunks


def connection(url):
    num = int('1')
    list_tag = []
    url_tiker = URL + url
    driver = webdriver.Firefox()
    driver.get(url_tiker)
    if driver is None:
        print(f" Нет ответа от сервера {url_tiker}")
        exit()
    driver.maximize_window()
    WebDriverWait(driver, 5)
    button = driver.find_element(By.LINK_TEXT, "Согласен")
    WebDriverWait(driver, 5)
    if button is not None:
        button.send_keys(Keys.ENTER)
    # Создание таблицы pandas
    mydata = pd.read_csv('sample.txt')
    OI = []
    Change = []
    Quantity = []
    mydata = pd.read_csv('sample.txt')
    # driver.refresh()
    WebDriverWait(driver, 10)
    data = driver.find_element(By.TAG_NAME, "td").text.split()[0]
    data_file = data[-4:] + '_' + data[3:5] + '_' + data[0:2]
    #date_date = driver.find_element(By.ID, "optDate")
    contracts = driver.find_element(By.CLASS_NAME, 'ui-row')
    #list_tbody = contracts.find_element(By.TAG_NAME, 'tbody').text.split('\n')
    list_web = contracts.find_elements(By.CLASS_NAME, 'ui-table-cell')

    new_dic = {}
    chunk = []
    chunks = []
    for nn, item in enumerate(list_web, start=1):
        if item.text[-1] == '%':
            new_cifer = item.text.replace(',', '.')
            new_dic[nn] = float(new_cifer[0:-1])
        else:
            new_dic[nn] = item.text

    for item in split_dict(new_dic, 9):
        chunk.append(item)

    chunks = change_keys(chunk)
    df = pd.DataFrame(chunks)
    file_name = DIR_NAME + '\\' + instrument + '_' + data_file + '_sum.csv'
    df.to_csv(file_name, index=False)
    print(df)

    list_tag = driver.find_elements(By.TAG_NAME, "td")
    for num, tag in enumerate(list_tag):
        if tag.text == 'Открытые позиции': # list_tag[78]
            oi_long_p = list_tag[num + 1].text
            oi_short_p = list_tag[num + 2].text
            oi_long_c = list_tag[num + 3].text
            oi_short_c = list_tag[num + 4].text
            oi_summ = list_tag[num + 5].text
        elif tag.text == 'Изменение': # list_tag[78]
            ch_long_p = list_tag[num + 1].text
            ch_short_p = list_tag[num + 2].text
            ch_long_c = list_tag[num + 3].text
            ch_short_c = list_tag[num + 4].text
            ch_summ = list_tag[num + 5].text
        elif tag.text == 'Количество лиц':
            qty_long_p = list_tag[num + 1].text
            qty_short_p = list_tag[num + 2].text
            qty_long_c = list_tag[num + 3].text
            qty_short_c = list_tag[num + 4].text
            qty_summ = list_tag[num + 5].text
    OI = [int(oi_long_p), oi_short_p, oi_long_c, oi_short_c, oi_summ]
    Change = [ch_long_p, ch_short_p, ch_long_c, ch_short_c, ch_summ]
    Quantity = [qty_long_p, qty_short_p, qty_long_c, qty_short_c, qty_summ]
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    # table = soup.find('table', class_="contract-open-positions table1")
    # if table is not None:
    #     for row in ROW:
    #         for column in COLUMN:
    #             if row == 1:
    #                 oi = int(table)
    #             elif row == 2:
    #                 change = int(table.find_all('tr')[1:][ROW].contents[COLUMN].text)
    #                 Change.append(change)
    #             elif row == 3:
    #                 quantity = int(table.find_all('tr')[1:][ROW].contents[COLUMN].text)
    #                 Quantity.append(quantity)

    #mydata.to_csv(data_file +'.csv', index=False)
    driver.close()

if __name__ == '__main__':
    #instrument = input("Введите инструмент для сбора данных:\n")
    instrument = 'SBRF-9.24'
    connection(instrument)

