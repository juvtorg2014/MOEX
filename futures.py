"""
 Программа для скачивания данных открытого интереса фьючерсов Московской биржи
 со страницы ежедневных данных. Доступ только пользователям личного кабинета.
 В файле <config.py> должны находиться <username = *******> и <password = *******>
"""

import json
import os
from datetime import datetime, timedelta
from time import sleep
import calendar
from config import username, password
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as COptions
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options as FOptions

COUNT_REPEAT = 5
MAIN_HTML = 'https://www.moex.com/ru/contract.aspx?code='
TRIPLE_D = [{'Z4': '19-12-2024'}, {'H5': '20-03-2025'}, {'M5': '18-06-2025'}, {'U5': '17-09-2025'}, {'Z5': '18-12-2025'}]


CODE_FUTURES = {'1':'F','2':'G','3':'H','4':'J','5':'K','6':'M',
               '7':'N','8':'Q','9':'U','10':'V','11':'X','12':'Z'}

# 57 фьючерсных контракта на акции
CONTRACTS = ['AF', 'AK', 'AL', 'AS', 'BN', 'BS', 'CH', 'CM', 'FE', 'FL', 'FS', 'GK', 'GZ', 'HY', 'IR', 'IS',
             'KM', 'LE', 'LK', 'MC', 'ME', 'MG', 'MN', 'MT', 'MV', 'NB', 'NK', 'NM', 'PH', 'PI', 'PS', 'PZ',
             'RA', 'RL', 'RN', 'RT', 'RU', 'S0', 'SC', 'SE', 'SG', 'SH', 'SN','SO', 'SP', 'SR', 'SS', 'SZ',
             'TB', 'TI', 'TN', 'TP', 'TT', 'VB', 'VK', 'WU', 'YD']

# 46 контракт на 3-х месячные фьючерсы
FUTURES = ['AE', 'AN', 'BB', 'BD', 'BR', 'CE', 'CF', 'CR', 'DJ', 'DX', 'ED', 'EM','EU', 'FN', 'GD', 'GL',
           'GU', 'HK', 'HO', 'HS', 'I2', 'IP', 'JP', 'KZ', 'MA', 'MM', 'MX', 'MY', 'N2', 'NA', 'NC', 'ND',
           'OG', 'PD', 'PT', 'R2', 'RB', 'RI', 'RM', 'SF', 'SI', 'SV', 'SX', 'SI', 'TY', 'UC']

# Вечные фьючерсы
LONG_FUTURES = ['CNYRUBF', 'EURRUBF', 'GLDRUBF', 'IMOEXF', 'USDRUBF']
BIG_CONTRACTS = CONTRACTS + FUTURES
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) + '\\'

CURRENT_YEAR = datetime.today().date().year
CODE_YEAR = str(CURRENT_YEAR - 2020)
THIRD_THURSDAY = ['2025-05-15','2025-07-17','2025-09-16', '2025-12-19']


def write_csv(path_dir, contract, op, cp, qt):
    """Запись в файл данных одного контракта"""
    date = path_dir.split('\\')[-3]
    name_file = contract + '_' + date + '_OI.csv'
    with open(path_dir + name_file, 'w', encoding='utf-8') as fo:
        fo.writelines("LP;SP;LC;SC;SUMMA")
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
                    open_pos.append(item.text)
        elif row.text[:9] == 'Изменение':
            data = row.find_elements(By.TAG_NAME, 'td')
            for item in data:
                if item.text != 'Изменение':
                    change_pos.append(item.text)
        elif row.text[:14] == 'Количество лиц':
            data = row.find_elements(By.TAG_NAME, 'td')
            for item in data:
                if item.text != 'Количество лиц':
                    quantity.append(item.text)
    open_pos = ';'.join(open_pos)
    change_pos = ';'.join(change_pos)
    quantity = ';'.join(quantity)
    return open_pos, change_pos, quantity


def get_selenium_page(html) -> int:
    """Основной модуль получения данных"""

    options = FOptions()
    options.add_argument('--headless')
    try:
        driver = webdriver.Firefox(options=options)
        wait = WebDriverWait(driver, 5)
        driver.get(html)
    except Exception as e:
        options = COptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 5)
        print("Firefox dosn't work")
        print(e)

    if "Московская биржа" in driver.title:
        print("Страница загружена")
        driver.implicitly_wait(5)
        try:
            print("Способ 1: Ищу кнопку по классу '_desktopButton_m2mc9_738'...")
            login_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "._desktopButton_m2mc9_738"))
            )
            print(f"✓ Кнопка найдена по CSS-классу")

        except Exception as e:
            print(f"Способ 1 не сработал: {e}")

            try:
                print("Способ 2: Ищу кнопку по тексту 'Войти'...")
                login_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Войти')]"))
                )
                print(f"✓ Кнопка найдена по тексту")

            except Exception as e2:
                print(f"Способ 2 не сработал: {e2}")

                print("Способ 3: Анализирую все кнопки на странице...")
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                print(f"Найдено кнопок: {len(all_buttons)}")

                for i, btn in enumerate(all_buttons):
                    btn_text = btn.text.strip()
                    btn_class = btn.get_attribute('class') or ''
                    print(f"Кнопка {i + 1}: текст='{btn_text}', класс='{btn_class}'")

                    if btn_text == "Войти" or "войти" in btn_text.lower():
                        login_button = btn
                        print(f"✓ Найдена подходящая кнопка: {btn_text}")
                        break

                if 'login_button' not in locals():
                    raise Exception("Кнопка 'Войти' не найдена")
        login_button.click()

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
        file_cookies = open(CURRENT_DIR + 'cookies.json', 'w')
        json.dump(cookies, file_cookies)
        sleep(3)
        try:
            today = driver.find_element(By.ID, 'digest_refresh_time').text.split(' ')[0]
            today = datetime.strptime(today.replace('.', ''), '%d%m%Y').date() - timedelta(days=1)
            last_day = check_weekday(today.day, today.month)
            if last_day < 10:
                last_day = '0' + str(last_day)
            else:
                last_day = str(last_day)
            if today.month < 10:
                time_page = str(today.year) + '0' + str(today.month) + last_day
            else:
                time_page = str(today.year) + str(today.month) + last_day
        except Exception:
            print("Не удалось получить дату со страницы !!!")
            today = datetime.today().date()-timedelta(days=1)
            last_day = check_weekday(today.day, today.month)
            if last_day < 10:
                last_day = '0' + str(last_day)
            else:
                last_day = str(last_day)
            if today.month < 10:
                time_page = str(today.year) + '0' + str(today.month) + last_day
            else:
                time_page = str(today.year) + str(today.month) + last_day

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
# Главная процедура загрузки контрактов
        unload_items = []
        all_contracts = []
        unusual_futures = unusual_contract(today)
        big_contracts = list(map(lambda x: x + MAIN_CONTRACT, BIG_CONTRACTS))
        all_contracts = big_contracts + LONG_FUTURES + unusual_futures
        for item in all_contracts:
            try:
                if item[:-2] in CONTRACTS:
                    sub_dir = new_dir_stocks
                else:
                    sub_dir = new_dir_futures
                driver.get(MAIN_HTML + item)
                # with open(CURRENT_DIR + 'cookies.json', 'r') as file:
                #     cookies = json.load(file)
                #     for cookie in cookies:
                #         driver.add_cookie(cookie)
                driver.refresh()
                print(driver.current_url)
                sleep(2)
                open_, change, qt = get_data_contract(driver)
                sleep(2)
                if not os.path.exists(sub_dir + item + '_' + time_page + '_OI.csv'):
                    write_csv(sub_dir, item, open_, change, qt)
            except Exception:
                print(f"Не удалось скачать данные {item}")
                unload_items.append(item)
                continue
            except FileExistsError:
                print('Файл <cookies.json не найден>')
                continue
        if len(unload_items) > 0:
            file_error = new_dir + time_page + "_unloaded.csv"
            with open(file_error, 'w', encoding='utf-8') as fw:
                for item in unload_items:
                    fw.writelines(item)
                    fw.write('\n')
            for item in unload_items:
                try:
                    print(f"Этот контракт {item} не скачался! Но пробуем ещё раз!")
                    if item[:-2] in [CONTRACTS]:
                        sub_dir = new_dir_stocks
                    else:
                        sub_dir = new_dir_futures
                    driver.get(MAIN_HTML + item)
                    driver.refresh()
                    sleep(2)
                    print(driver.current_url)
                    open_, change, qt = get_data_contract(driver)
                    sleep(2)
                    write_csv(sub_dir, item, open_, change, qt)
                except Exception:
                    print(f'Повторно не удалось скачать контракт {item}')
                    continue
    else:
        print("Не удалось войти на главную страницу")
        driver.quit()
        return 0

    if driver.session_id is not None:
        driver.quit()
    # if os.path.exists('cookies.json'):
    #     try:
    #        os.remove(CURRENT_DIR + 'cookies.json')
    #     except FileExistsError:
    #        print('Файл <cookies.json> уже закрыт !!!')
    print("Браузер закрыт!")
    if len(os.listdir(new_dir + 'futures\\')) > 0\
            and  len(os.listdir(new_dir + 'futures\\')) > 0:
        return 1
    else:
        return 0

def unusual_contract(date) -> list:
    """ Нестандартныe фьючерсы по 1 и 2 месяца """
    list_contracts = []
    code_brent = ''
    code_cocoa = ''
    month = date.month
    middle_work_day = check_weekday(15, month)
    last_day = calendar.monthrange(CURRENT_YEAR, month)[1]
    last_work_day = check_weekday(last_day, month)

    date_str = datetime.strftime(date, '%Y-%m-%d')
    if date.day >= 1:
        if month == 12:
            code_brent  = 'BR' + CODE_FUTURES.get(str(1)) + CODE_YEAR
        else:
            code_brent = 'BR' + CODE_FUTURES.get(str(month + 1)) + CODE_YEAR
        list_contracts.append(code_brent)

    if date.day >= middle_work_day:
        if month == 12:
            code_sugar = 'SU' + CODE_FUTURES.get(str(3)) + CODE_YEAR
        else:
            code_sugar = 'SU' + CODE_FUTURES.get(str(month + 1)) + CODE_YEAR
        list_contracts.append(code_sugar)
    else:
        code_sugar = 'SU' + CODE_FUTURES.get(str(month)) + CODE_YEAR
        list_contracts.append(code_sugar)

    if date.day <= last_work_day:
        if month == 12:
            code_wheat = 'WH' + CODE_FUTURES.get(str(1)) + CODE_YEAR
        else:
            code_wheat = 'WH' + CODE_FUTURES.get(str(month)) + CODE_YEAR
    list_contracts.append(code_wheat)

    if date_str < THIRD_THURSDAY[0]:
        code_cocoa = 'CC' + 'K' + CODE_YEAR
    elif date_str >= THIRD_THURSDAY[0] and date_str < THIRD_THURSDAY[1]:
        code_cocoa = 'CC' + 'N' + CODE_YEAR
    elif date_str >= THIRD_THURSDAY[1] and date_str < THIRD_THURSDAY[2]:
        code_cocoa = 'CC' + 'U' + CODE_YEAR
    else:
        code_cocoa = 'CC' + 'X' + CODE_YEAR
    list_contracts.append(code_cocoa)
    return list_contracts


def get_main_contract():
    """Получения близжайшего суффикса фьючерса"""
    today = datetime.now().date()
    for item in TRIPLE_D:
        for key, value in item.items():
            day = datetime.strptime((value), '%d-%m-%Y').date()
            if today < day:
                return key


def check_weekday(day, month):
    """Проверка дат из-за субботы и воскресенья"""
    if calendar.weekday(CURRENT_YEAR, month, day) == 6:
        new_day = day - 2
    elif calendar.weekday(CURRENT_YEAR, month, day) == 5:
        new_day = day - 1
    else:
        new_day = day
    return new_day


if __name__ == '__main__':
    start_time = datetime.now()
    MAIN_CONTRACT = get_main_contract()
    count = 0
    while count < COUNT_REPEAT:
        count += 1
        result = get_selenium_page(MAIN_HTML + CONTRACTS[0] + MAIN_CONTRACT)
        if result == 0:
            print(f"Осталось ещё до {COUNT_REPEAT - count} попыток")
            result = get_selenium_page(MAIN_HTML + CONTRACTS[0] + MAIN_CONTRACT)
        else:
            break
    print("--- %s времени прошло ---" % (datetime.now() - start_time))
    sleep(15)
