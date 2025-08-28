'''
Создание базы данных из папки с котироваками инструментов.
Базу потом можно переименовать.
Есть 2 типа котировок: дневные и внутридневные (типа 1,5,30 минут и т.д.)
'''
import sqlite3
from datetime import datetime, timedelta
import os

PERIODS = 'D'

def clear_list(list_name):
    new_list = []
    path = os.getcwd() + '\\' + name_base + '\\'
    for file in list_name:
        file= file.rsplit('.',1)[0]
        if '-' in file:
            new_file = file.replace('-','_')
            new_list.append(new_file)
            os.rename(path + file + '.csv', path + new_file + '.csv')
        elif file[0] == '+':
            new_file = file.replace('+', '')
            new_list.append(new_file)
            os.rename(path + file + '.csv', path + new_file + '.csv')
        elif '+' in file:
            new_file = file.replace('+', '_')
            new_list.append(file.replace('+', '_'))
            os.rename(path + file + '.csv', path + new_file + '.csv')
        elif '.' in file:
            new_file = file.replace('.', '_')
            new_list.append(file.replace('.', '_'))
            os.rename(path + file + '.csv', path + new_file + '.csv')
        else:
            new_list.append(file)
    return new_list


def fill_database(stocks, time_frame):
    db_path = os.path.join(os.getcwd(), new_name_base)
    clear_stocks = clear_list(stocks)
    # Подключаемся к базе данных (или создаем новую)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Создаем таблицу для каждой акции
    if time_frame == 'D':
        for stock in clear_stocks:
            print(stock)
            cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {stock} (
                Date DATE PRIMARY KEY, Open REAL NOT NULL, High REAL NOT NULL, Low REAL NOT NULL, Close REAL NOT NULL, Volume INTEGER)
            ''')
    else:
        for stock in clear_stocks:
            cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {stock} (
                Date DATE PRIMARY KEY, Time TIME PRIMARY KEY, Open REAL NOT NULL, High REAL NOT NULL, Low REAL NOT NULL, Close REAL NOT NULL, Volume INTEGER)
            ''')
    date = datetime.strptime('1970-01-01', "%Y-%m-%d").date()
    time = '06:00:00'
    open_price = float(100.50)
    close_price = float(100.75)
    high_price = float(101.00)
    low_price = float(100.00)
    volume = int(1000)

    for stock in clear_stocks:
        if time_frame == 'D':
            cursor.execute(f'''
                INSERT INTO {stock} (Date, Open, High, Low, Close, Volume)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (date, open_price, high_price, low_price, close_price, volume))
            conn.commit()
        else:
            cursor.execute(f'''
                    INSERT INTO {stock} (Date, Time, Open, High, Low, Close, Volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (date, time, open_price, high_price, low_price, close_price, volume))
            conn.commit()

    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()
    print(f"База данных '{new_name_base}' успешно создана с акциями MOEX.")


def get_name_instruments(name_path):
    list_names = []
    for root, dirs, filenames in os.walk(name_path):
        for filename in filenames:
            if filename.endswith('.csv'):
                list_names.append(filename)
    return list_names


if __name__ == '__main__':
    name_base = input("Введите имя папки с файлами:\n")
    new_name_base = name_base + '.db'
    stocks = get_name_instruments(name_base)
    fill_database(stocks, PERIODS)