import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd


COLUMN = [1, 2, 3, 4, 5]
ROW = [1, 2, 3]
URL = 'https://www.moex.com/ru/contract.aspx?code='
futures_1 = ['SBRF-9.24', 'GAZR-9.24', 'LKOH-9.24', 'SNGP-9.24', 'TCSI-9.24',
            'CNY-9.24', 'Si-9.24', 'CNYRUBF', 'GOLD-9.24', 'MIX-9.24', 'USDRUBF'
           'SILV-9.24', 'ED-9.24', 'SPYF-9.24']
futures = ['SBRF-9.24', 'GAZR-9.24', 'LKOH-9.24']
DIR_NAME = os.getcwd()


def split_dict(dic, nom):
    """Разделение словаря на несколько словарей"""
    keys = list(dic.keys())
    for i in range(0, len(keys), nom):
        yield {k: dic[k] for k in keys[i: i + nom]}



def change_keys(chunks) -> list:
    """Замена цифрового ключа на символьный"""
    replacements = ['Code', 'Price', 'D_Pr', 'Vol_rub', 'Vol_con', 'OI', 'D_OI', 'Ras', 'Day']
    len_list = len(chunks)
    new_dict_1 = {}
    new_dict_2 = {}
    new_dict_3 = {}
    new_dict_4 = {}
    new_chunks = []

    for nn, item in enumerate(chunks, start=1):
        if nn == 1 and nn <= len_list:
            new_dict_1 = dict(zip(replacements, list(item.values())))
            new_chunks.append(new_dict_1)
        elif nn == 2 and nn <= len_list:
            new_dict_2 = dict(zip(replacements, list(item.values())))
            new_chunks.append(new_dict_2)
        elif nn == 3 and nn <= len_list:
            new_dict_3 = dict(zip(replacements, list(item.values())))
            new_chunks.append(new_dict_3)
        elif nn == 4 and nn <= len_list:
            new_dict_4 = dict(zip(replacements, list(item.values())))
            new_chunks.append(new_dict_4)
    return new_chunks


def get_oi(list_tag) -> list:
    """Получение данных по открытому интересу"""
    list_oi = []
    for num, tag in enumerate(list_tag):
        if tag.text == 'Открытые позиции': # list_tag[78]
            oi_long_p = list_tag[num + 1].text.replace(',', '')
            oi_short_p = list_tag[num + 2].text.replace(',', '')
            oi_long_c = list_tag[num + 3].text.replace(',', '')
            oi_short_c = list_tag[num + 4].text.replace(',', '')
            oi_summ = list_tag[num + 5].text.replace(',', '')
        elif tag.text == 'Изменение': # list_tag[78]
            ch_long_p = list_tag[num + 1].text.replace(',', '')
            ch_short_p = list_tag[num + 2].text.replace(',', '')
            ch_long_c = list_tag[num + 3].text.replace(',', '')
            ch_short_c = list_tag[num + 4].text.replace(',', '')
            ch_summ = list_tag[num + 5].text.replace(',', '')
        elif tag.text == 'Количество лиц':
            qty_long_p = list_tag[num + 1].text.replace(',', '')
            qty_short_p = list_tag[num + 2].text.replace(',', '')
            qty_long_c = list_tag[num + 3].text.replace(',', '')
            qty_short_c = list_tag[num + 4].text.replace(',', '')
            qty_summ = list_tag[num + 5].text.replace(',', '')

    OI = {'1_Long': int(oi_long_p), '1_Short': int(oi_short_p), '2_Long': int(oi_long_c),'2_Short': int(oi_short_c),'Summa': int(oi_summ)}
    Change = {'1_Long': int(ch_long_p),'1_Short': int(ch_short_p),'2_Long': int(ch_long_c),'2_Short': int(ch_short_c),'Summa': int(ch_summ)}
    Quantity = {'1_Long': int(qty_long_p),'1_Short': int(qty_short_p),'2_Long': int(qty_long_c),'2_Short': int(qty_short_c),'Summa': int(qty_summ)}
    list_oi.append(OI)
    list_oi.append(Change)
    list_oi.append(Quantity)
    return list_oi


def connect(instrument):
    num = int('1')
    list_tag = []
    list_oi = []
    url_tiker = URL + instrument
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Firefox(options=options)
    driver.get(url_tiker)
    if driver is None:
        print(f" Нет ответа от сервера {url_tiker}")
        exit()
    driver.maximize_window()
    WebDriverWait(driver, 5)
    list_cookies = driver.get_cookies()
    for cookies in list_cookies:
        driver.add_cookie(cookies)
    button = driver.find_element(By.LINK_TEXT, "Согласен")
    WebDriverWait(driver, 5)
    if button is not None:
        button.send_keys(Keys.ENTER)

    WebDriverWait(driver, 10)
    data = driver.find_element(By.TAG_NAME, "td")
    if data.text != '':
        data_need = data.text.split()[0]
        data_file = data_need[-4:] + '_' + data_need[3:5] + '_' + data_need[0:2]
    else:
        data_need = driver.find_element(By.ID, "digest_refresh_time").text.split()[0]
        data_file = data_need[-4:] + '_' + data_need[3:5] + '_' + data_need[0:2]
    contracts = driver.find_element(By.CLASS_NAME, 'ui-row')
    list_web = contracts.find_elements(By.CLASS_NAME, 'ui-table-cell')
    print(url_tiker)

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
    file_name_1 = DIR_NAME + '\\' + instrument + '_' + data_file + '_sum.csv'
    save_file(chunks, file_name_1)

    list_tag = driver.find_elements(By.TAG_NAME, "td")
    list_oi = get_oi(list_tag)
    file_name_2 = DIR_NAME + '\\' + instrument + '_' + data_file + '_oi.csv'
    save_file(list_oi, file_name_2)

    driver.close()
    driver.quit()

def save_file(list_data, name_file):
    df = pd.DataFrame(list_data)
    df.to_csv(name_file, index=False)
    print(df)


if __name__ == '__main__':
    #instrument = input("Введите инструмент для сбора данных:\n")
    for futur in futures:
        connect(futur)

