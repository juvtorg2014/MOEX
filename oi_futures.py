"""
 Программа для скачивания данных открытого интереса фьючерсов Московской биржи
 со страницы ежедневных данных. История подгружается путем изменения даты.
 Доступ только пользователям личного кабинета.
"""
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
from datetime import datetime, timedelta
import pickle



COLUMN = [1, 2, 3, 4, 5]
ROW = [1, 2, 3]
URL = 'https://www.moex.com/ru/contract.aspx?code='
futures_1 = ['SBRF-9.24', 'GAZR-9.24', 'LKOH-9.24', 'SNGP-9.24', 'TCSI-9.24',
            'CNY-9.24', 'Si-9.24', 'CNYRUBF', 'GOLD-9.24', 'MIX-9.24', 'USDRUBF',
           'SILV-9.24', 'ED-9.24', 'SPYF-9.24']
futures = ['LKOH-9.24', 'GAZR-9.24', 'TCSI-9.24']
DIR_NAME = os.getcwd()
NEED_OPTIONS = ['Открытые позиции', 'Изменение', 'Количество лиц']


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
    list_ch = []
    list_qn = []
    list_dics = []
    name_keys = ['1_Long', '1_Short', '2_Long', '2_Short', 'Summa']
    if type(list_tag) == list:
        if len(list_tag) > 1:
            print('Чтение открытого интереса началось...')
    else:
        print("Не удалость получить ")

    for nomer, tag in enumerate(list_tag):
        if nomer > 1:
            list_items = tag.find_elements(By.TAG_NAME, 'td')
            for num, item in enumerate(list_items):
                if list_items[0].text == 'Открытые позиции':
                    if num > 0:
                        list_oi.append(int(item.text.replace(',', '')))
                elif list_items[0].text == 'Изменение':
                    if num > 0:
                        list_ch.append(int(item.text.replace(',', '')))
                elif list_items[0].text == 'Количество лиц':
                    if num > 0:
                        list_qn.append(int(item.text.replace(',', '')))

    oi = dict(zip(name_keys, list_oi))
    change = dict(zip(name_keys, list_ch))
    quant = dict(zip(name_keys, list_qn))
    list_dics.append(oi)
    list_dics.append(change)
    list_dics.append(quant)
    return list_dics


def connect(instrument):
    num = int('1')
    list_tag = []
    list_oi = []
    url_tiker = URL + instrument
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Firefox()
    driver.get(url_tiker)
    if driver is None:
        print(f" Нет ответа от сервера {url_tiker}")
        exit()
    driver.maximize_window()
    WebDriverWait(driver, 10)
    list_cookies = driver.get_cookies()
    for cookies in list_cookies:
        driver.add_cookie(cookies)
    button = driver.find_element(By.LINK_TEXT, "Согласен")
    WebDriverWait(driver, 10)
    if button is not None:
        button.send_keys(Keys.ENTER)
    else:
        print('Кнопка не найдена!')

    WebDriverWait(driver, 10)
    data = driver.find_element(By.ID, 'digest_refresh_time').text
    if data != '':
        data_need = data.split()[0]
        data_file = data_need[-4:] + data_need[3:5] + data_need[0:2]
        time_file = data.split()[1]
    else:
        data_need = datetime.today().date() - timedelta(days=1)
        data_file = data_need.strftime('%Y%m%d')
        time_file = datetime.today().time().strftime('%H:%M:%S')
    old_date = driver.find_element(By.ID, "optDate")
    #contracts = driver.find_element(By.CLASS_NAME, 'ui-row')
    list_web = driver.find_elements(By.CLASS_NAME, 'ui-table-cell')
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
    #list_tag = driver.find_elements(By.TAG_NAME, "td")
    #elements = driver.find_element(By.CLASS_NAME, 'ui-table__container').find_elements(By.CLASS_NAME, 'ui-table-row')
    elements_web = driver.find_element(By.CLASS_NAME, 'ContractTablesOptions_overflow_3zzJO').find_elements(By.TAG_NAME, 'tr')
    list_oi = get_oi(elements_web)
    file_name = DIR_NAME + '\\' + instrument + '_' + data_file
    save_file(list_oi, file_name + '_oi.csv', time_file)
    save_file(chunks, file_name + '_sum.csv', time_file)

    driver.close()
    driver.quit()

def save_file(list_data, name_file, time_file):
    with open(name_file, 'wr', encoding='utf-8') as f:
        f.write(name_file.split('_')[1] + '-' + time_file)
        f.write('\n')
        pickle.dump(list_data, f)

    # df = pd.DataFrame(list_data, f)
    # df.to_csv(name_file, index=False)
    # print(df)


if __name__ == '__main__':
    #instrument = input("Введите инструмент для сбора данных:\n")
    for futur in futures:
        connect(futur)

