"""
 Программа для скачивания данных открытого интереса фьючерсов Московской биржи
 со страницы ежедневных данных. Доступ только пользователям личного кабинета.
 В файле <config.py> должны находиться <username = *******> и <password = *******>
"""

import json
import os
from datetime import datetime, timedelta
from time import sleep
from config import username, password
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as COptions
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FOptions

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

    options = FOptions()
    options.add_argument('--headless')
    try:
        driver = webdriver.Firefox(options=options)
        driver.get(html)
    except Exception as e:
        options = COptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        print("Firefox dosn't work")
        print(e)

    if "Московская биржа" in driver.title:
        driver.implicitly_wait(3)
        ch = driver.find_element(By.CLASS_NAME, 'disclaimer__header').find_element(By.CLASS_NAME, 'disclaimer__buttons')
        button = ch.find_element(By.TAG_NAME, 'a')
        if button.text == 'Согласен':
            button.click()
        else:
            print("Не нажата кнопка <Согласен>")
        driver.implicitly_wait(3)
        enter = driver.find_element(By.CLASS_NAME, 'header-user-profile')
        if enter.text == "Войти":
            enter.click()
        else:
            print("Не удалось сразу войти в личный кабинет")
            enter2 = driver.find_element(By.CLASS_NAME, 'cabinet-text-container')
            text_enter = enter2.find_element(By.CLASS_NAME, 'cabinet-text').text
            if text_enter == 'Войти':
                enter.click()
            else:
                print('Не найдена кнопка <<Войти>>')
        driver.implicitly_wait(3)
        if driver.title == 'Вход SSO':
            name = driver.find_element(By.NAME, 'credentials')
            if name.accessible_name == 'Электронная почта *':
                name.clear()
                name.send_keys(username)
            else:
                print('Не найдено поле <Имя пользователя>')
            passw = driver.find_element(By.NAME, 'password')

            if passw.accessible_name == 'Пароль *':
                passw.clear()
                passw.send_keys(password)
            else:
                print('Не найдено поле <Пароль>')
            try:
                driver.find_element(By.CLASS_NAME, 'submit-button').click()
            except Exception:
                print("Вход не выполнен!!!")
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

        unload_items = []
        for item in ALL_CONTRACTS:
            try:
                contract, sub_dir = get_name_and_dir(item, new_dir_futures, new_dir_stocks)
                driver.get(MAIN_HTML + contract)
                with open(CURRENT_DIR + 'cookies.json', 'r') as file:
                    cookies = json.load(file)
                    for cookie in cookies:
                        driver.add_cookie(cookie)
                driver.refresh()
                print(driver.current_url)
                open_, change, qt = get_data_contract(driver)
                sleep(1)
                write_csv(sub_dir, contract, open_, change, qt)
            except Exception:
                print(f"Не удалось скачать данные {contract}")
                unload_items.append(contract)
                continue
            except FileExistsError:
                print('Файл <cookies.json не найден>')
                continue
        if len(unload_items) > 0:
            file_error = new_dir + "unloaded.csv"
            with open(file_error, 'w', encoding='utf-8') as fw:
                for item in unload_items:
                    fw.writelines(item)
            for item in unload_items:
                try:
                    print(f"Этот контракт {item} не скачался! Но пробуем ещё раз!")
                    contract, sub_dir = get_name_and_dir(item, new_dir_futures, new_dir_stocks)
                    driver.get(MAIN_HTML + contract)
                    driver.refresh()
                    print(driver.current_url)
                    open_, change, qt = get_data_contract(driver)
                    sleep(1)
                    write_csv(sub_dir, contract, open_, change, qt)
                except Exception:
                    print(f'Повторно не удалось скачать контракт {item}')
                    continue
    else:
        print("Не удалось войти на главную страницу")
        driver.quit()

    if driver.session_id is not None:
        driver.quit()
    if os.path.exists('cookies.json'):
        try:
           os.remove(CURRENT_DIR + 'cookies.json')
        except FileExistsError:
           print('Файл <cookies.json> уже закрыт !!!')
    print("Браузер закрыт!")


def get_name_and_dir(item, dir_futures,dir_stocks) -> list:
    """Получение имени контракта и директории для записи файла"""
    return_list = []
    if item in long_futures:
        contract = item
        sub_dir = dir_futures
    elif item in futures:
        contract = item + MAIN_CONTRACT
        sub_dir = dir_futures
    else:
        contract = item + MAIN_CONTRACT
        sub_dir = dir_stocks
    return_list.append(contract)
    return_list.append(sub_dir)
    return return_list


def get_main_contract():
    """Получения близжайшего суффикса фьючерса"""
    today = datetime.now().date()
    for item in TRIPLE_D:
        for key, value in item.items():
            day = datetime.strptime((value), '%d-%m-%Y').date()
            if today < day:
                return key


def check_weekday(today):
    """Проверка дат из-за субботы и воскресенья"""
    if today.weekday() == 5:
        return datetime.strftime(today - timedelta(days=1), '%Y%m%d')
    elif today.weekday() == 6:
        return datetime.strftime(today - timedelta(days=2), '%Y%m%d')
    else:
        return datetime.strftime(today, '%Y%m%d')


if __name__ == '__main__':
    start_time = datetime.now()
    MAIN_CONTRACT = get_main_contract()
    get_selenium_page(MAIN_HTML + contracts[0] + MAIN_CONTRACT)
    print("--- %s времени прошло ---" % (datetime.now() - start_time))
    sleep(15)
