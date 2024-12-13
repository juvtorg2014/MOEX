"""
 Программа для скачивания данных открытого интереса фьючерсов Московской биржи
 со страницы ежедневных данных. Доступ только пользователям личного кабинета.
 В файле <config.py> должны находиться <username=*******> и <password=*******>
"""

import os
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from config import username, password
from time import sleep
from datetime import datetime, timedelta

MAIN_CONTRACT = ''
MAIN_HTML = 'https://www.moex.com/ru/contract.aspx?code='
TRIPLE_D = [{'Z4': '20-12-2024'}, {'H5': '21-03-2025'}, {'M5': '20-06-2025'}, {'U5': '19-09-2025'}, {'Z5': '19-12-2025'}]

contracts = ['AF', 'AK', 'AL', 'AS', 'BN', 'BS', 'CH', 'CM', 'FE', 'FL', 'FS', 'GK', 'GZ', 'HY', 'IR', 'IS',
             'KM', 'LE', 'LK', 'MC', 'ME', 'MG', 'MN', 'MT', 'MV', 'NK', 'NM', 'PH', 'PI', 'PS', 'PZ', 'RA',
             'RL', 'RN', 'RT', 'RU', 'SO', 'SC', 'SE', 'SG', 'SH', 'SO', 'SP', 'SR', 'SS', 'SZ', 'TI', 'TN',
             'TP', 'TT', 'VB', 'VK', 'WU', 'YD']

futures = ['AE', 'BB', 'BD', 'BR', 'CC', 'CF', 'CR', 'DJ', 'DX', 'ED', 'EU', 'FN', 'GD', 'GL', 'HS', 'IP',
           'JP', 'MA', 'MM', 'MX', 'NA', 'NG', 'OG', 'PD', 'PT', 'R2', 'RB', 'RI', 'RM', 'SF', 'SV', 'SX',
           'SI', 'SU', 'TY', 'UC', 'W4']

long_futures = ['CNYRUBF', 'EURRUBF', 'GLDRUBF', 'IMOEXF', 'USDRUBF']

ALL_CONTRACTS = contracts + futures + long_futures

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) + '\\'


def write_csv(path_dir, contract, op, cp, qt):
    """Запись в файл данных одного контракта"""
    date = path_dir.split('\\')[-3]
    name_file = contract + '_' + date + '_OI.csv'
    with open(path_dir + name_file, 'w', encoding='utf-8') as fo:
        fo.writelines("LP    SP    LC    SC    SUMMA")
        fo.write('\n')
        fo.writelines(op)
        fo.write('\n')
        fo.writelines(cp)
        fo.write('\n')
        fo.writelines(qt)
        print(f'Все записано за контракт {contract} и число {date}!!!')


def get_data_contract(driver):
    """Получение данных одного контракта"""
    common_table = driver.find_element(By.CLASS_NAME, 'ContractTablesOptions_overflow_3zzJO')
    tables = common_table.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')
    open_pos = []
    change_pos = []
    quantity = []

    for row in tables:
        if row.text[:16] == 'Открытые позиции':
            data = row.find_elements(By.TAG_NAME, 'td')
            for item in data:
                if item.text != 'Открытые позиции':
                    open_pos.append(item.text.replace(',', '') + ' ')
        elif row.text[:9] == 'Изменение':
            data = row.find_elements(By.TAG_NAME, 'td')
            for item in data:
                if item.text != 'Изменение':
                    change_pos.append(item.text.replace(',', '') + ' ')
        elif row.text[:14] == 'Количество лиц':
            data = row.find_elements(By.TAG_NAME, 'td')
            for item in data:
                if item.text != 'Количество лиц':
                    quantity.append(item.text.replace(',', '') + ' ')
    return open_pos, change_pos, quantity


def get_selenium_page(html):
    """Основной модуль получения данных"""

    options = Options()
    options.add_argument('--headless')

    driver = webdriver.Firefox(options=options)
    driver.get(html)

    if driver.title == 'Основные параметры срочного контракта — Московская Биржа | Рынки':
        driver.implicitly_wait(3)
        ch = driver.find_element(By.CLASS_NAME, 'disclaimer__header').find_element(By.CLASS_NAME, 'disclaimer__buttons')
        button = ch.find_element(By.TAG_NAME, 'a')
        if button.text == 'Согласен':
            button.click()
        else:
            print("Не нажата кнопка <Согласен>")
        driver.implicitly_wait(3)
        enter = driver.find_element(By.CLASS_NAME, 'cabinet-text')
        if enter.text == 'Вход':
            enter.click()
        else:
            print("Не удалось сразу войти в личный кабинет")
            enter = driver.find_element(By.CLASS_NAME, 'cabinet-text-container')
            enter.find_element(By.CLASS_NAME, 'cabinet-text')
            if enter.text == 'Вход':
                enter.click()
        driver.implicitly_wait(3)
        if driver.title == 'Вход SSO':
            name = driver.find_element(By.NAME, 'credentials')
            if name.accessible_name == 'Имя пользователя или E-mail':
                name.clear()
                name.send_keys(username)
            else:
                print('Не найдено поле <Имя пользователя>')
            passw = driver.find_element(By.NAME, 'password')

            if passw.accessible_name == 'Пароль':
                passw.clear()
                passw.send_keys(password)
            else:
                print('Не найдено поле <Пароль>')
            driver.find_elements(By.CLASS_NAME, 'form-group')[2].click()
        else:
            print('Не был выполнен вход по паролю')
        cookies = driver.get_cookies()
        with open(CURRENT_DIR + 'cookies.json', 'w') as file:
            json.dump(cookies, file)
        sleep(3)
        try:
            today = driver.find_element(By.ID, 'digest_refresh_time').text.split(' ')[0]
            today = datetime.strptime(today.replace('.', ''), '%d%m%Y').date() - timedelta(days=1)
            time_page = check_weekday(today)
        except Exception:
            print("Не удалось получить дату со страницы !!!")
            today = datetime.today().date()-timedelta(days=1)
            time_page = check_weekday(today)

        new_dir = CURRENT_DIR + time_page + '\\'
        new_dir_stocks = new_dir + 'stocks' + '\\'
        new_dir_futures = new_dir + 'futures' + '\\'
        if not os.path.exists(new_dir):
            os.mkdir(new_dir)
            print('Создана папка: ' + new_dir)
        if not os.path.exists(new_dir_stocks):
            os.mkdir(new_dir_stocks)
            print('Создана папка: ' + new_dir_stocks)
        if not os.path.exists(new_dir_futures):
            os.mkdir(new_dir_futures)
            print('Создана папка: ' + new_dir_futures)

        for item in ALL_CONTRACTS:
            try:
                if item in long_futures:
                    contract = item
                    sub_dir = new_dir_futures
                elif item in futures:
                    contract = item + MAIN_CONTRACT
                    sub_dir = new_dir_futures
                else:
                    contract = item + MAIN_CONTRACT
                    sub_dir = new_dir_stocks
                driver.get(MAIN_HTML + contract)
                with open(CURRENT_DIR + 'cookies.json', 'r') as file:
                    cookies = json.load(file)
                    for cookie in cookies:
                        driver.add_cookie(cookie)
                driver.refresh()
                print(driver.current_url)
                sleep(1)
                open_, change, qt = get_data_contract(driver)
                sleep(1)
                write_csv(sub_dir, contract, open_, change, qt)
                sleep(1)
            except Exception:
                print(f"Не удалось скачать данные {contract}")
                continue
            except FileExistsError:
                print('Файл <cookies.json не найден>')
                continue
    else:
        print("Не удалось войти на главную страницу")
        driver.quit()
    if driver.session_id is not None:
        driver.quit()
    try:
        os.remove(CURRENT_DIR + 'cookies.json')
    except FileExistsError:
        print('Файл <cookies.json> уже закрыт !!!')
    print("Браузер закрыт!")


def get_main_contract():
    """Получения близжайшего суффикса фьючерса"""
    today = datetime.now().date()
    for item in TRIPLE_D:
        for key, value in item.items():
            day = datetime.strptime((value), '%d-%m-%Y').date()
            if today < day:
                return key


def check_weekday(today):
    """Проверка субботы и воскресенья"""
    if today.weekday() == 5:
        return datetime.strftime(today - timedelta(days=1), '%Y%m%d')
    elif today.weekday() == 6:
        return datetime.strftime(today - timedelta(days=1), '%Y%m%d')
    else:
        return datetime.strftime(today, '%Y%m%d')


if __name__ == '__main__':
    MAIN_CONTRACT = get_main_contract()
    start_time = datetime.now()
    get_selenium_page(MAIN_HTML + contracts[0] + MAIN_CONTRACT)
    print("--- %s времени прошло ---" % (datetime.now() - start_time))
