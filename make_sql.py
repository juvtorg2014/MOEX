import sqlite3
import random
from datetime import datetime, timedelta


def create_database(db_name='stocks.db'):
    # Список акций MOEX
    stocks = [
        'AFKS', 'AFLT', 'AKRN', 'ALRS', 'BANE', 'BANEP', 'BSPB', 'CBOM', 'CHMF', 'FEES', 'GAZP',
        'GCHE', 'GMKN', 'HYDR', 'IRAO', 'KMAZ', 'LKOH', 'LSRG', 'MAGN', 'MOEX', 'MSNG',
        'MLTR', 'MTSS', 'NLMK', 'NVTK', 'PHOR', 'PIKK', 'PLZL', 'POSI', 'RENI', 'ROSN',
        'RTKM', 'RUAL', 'SBER', 'SBERP', 'SELG', 'SNGS', 'SNGSP', 'SVCB', 'T', 'TATN',
        'TATNP', 'TRNFP', 'UGLD', 'UPRO', 'VKCO', 'VTBR', 'YDEX'
    ]

    # Подключаемся к базе данных (или создаем новую)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Создаем таблицу для каждой акции
    for stock in stocks:
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {stock} (
            Date DATE,
            Time TIME,
            Open REAL,
            High REAL,
            Low REAL,
            Close REAL,
            Volume INTEGER
        )
        ''')

        # Генерируем случайные данные за последние 3 дней
        start_date = datetime.now() - timedelta(days=10000)
        for i in range(3):
            date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            time = '16:00:00'  # Время закрытия торгов

            # Генерируем случайные значения цен
            base_price = random.uniform(50, 500)
            open_price = round(base_price, 2)
            close_price = round(open_price * random.uniform(0.95, 1.05), 2)
            high_price = round(max(open_price, close_price) * random.uniform(1.0, 1.03), 2)
            low_price = round(min(open_price, close_price) * random.uniform(0.97, 1.0), 2)
            volume = random.randint(1000000, 10000000)

            # Вставляем данные в таблицу
            cursor.execute(f'''
            INSERT INTO {stock} (Date, Time, Open, High, Low, Close, Volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (date, time, open_price, high_price, low_price, close_price, volume))

    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()
    print(f"База данных '{db_name}' успешно создана с акциями MOEX.")


if __name__ == '__main__':
    create_database()