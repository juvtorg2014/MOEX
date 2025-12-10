import sqlite3
import pandas as pd
import glob
import os


def create_database_from_csv(csv_folder, db_name):
    """
    Создает базу данных SQLite из CSV-файлов без заголовков.
    Предполагаемый порядок колонок: Date, Time, Open, High, Low, Close, Volume, ATR.
    """

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    csv_files = glob.glob(os.path.join(csv_folder, '*.csv'))

    if not csv_files:
        print(f"В папке '{csv_folder}' не найдено CSV-файлов.")
        return

    column_names = ['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'ATR']

    for csv_file in csv_files:
        # Извлекаем имя акции из имени файла
        stock_name = os.path.splitext(os.path.basename(csv_file))[0]
        print(stock_name)
        try:
            # Читаем CSV-файл без заголовка и назначаем колонки
            df = pd.read_csv(csv_file, header=None, names=column_names)

            # Проверяем, что все колонки имеют правильный тип данных
            df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
            df = df.dropna(subset=['Date', 'Time'])
            if df['Time'].dtype == 'int64':
                # Если время в формате HHMMSS (целое число)
                df['Time'] = df['Time'].astype(str).str.zfill(6)
                df['Time'] = df['Time'].str[:2] + ':' + df['Time'].str[2:4] + ':' + df['Time'].str[4:6]
            else:
                df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.strftime('%H:%M:%S')
            df['Open'] = (pd.to_numeric(df['Open'])).round(2)
            df['High'] = (pd.to_numeric(df['High'])).round(2)
            df['Low'] = (pd.to_numeric(df['Low'])).round(2)
            df['Close'] = (pd.to_numeric(df['Close'])).round(2)
            df['Volume'] = pd.to_numeric(df['Volume']).astype('int64')
            df['ATR'] = (df['High'] - df['Low']).round(6)

            # Создаем таблицу для акции
            cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS "{stock_name}" (
                Date DATE,
                Time TIME,
                Open REAL,
                High REAL,
                Low REAL,
                Close REAL,
                Volume INTEGER,
                ATR REAL,
                PRIMARY KEY (Date, Time)                
            )
            ''')

            # Загрузка данных с проверкой дубликатов
            for _, row in df.iterrows():
                try:
                    cursor.execute(f'''
                               INSERT OR IGNORE INTO "{stock_name}"
                               (Date, Time, Open, High, Low, Close, Volume, ATR)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                               ''', tuple(row))
                except sqlite3.Error as e:
                    print(f"Ошибка при вставке данных: {e}")
                    continue

            # Сортировка сначала по дате (date), затем по времени (time)
            cursor.execute(f'''
            SELECT " FROM {stock_name}" 
            ORDER BY Date ASC, Time ASC
            ''')

            # df.to_sql(name=stock_name, con=conn, if_exists='append', index=False)
            print(f"Данные для акции {stock_name} успешно загружены из {csv_file}")

        except Exception as e:
            print(f"Ошибка при обработке файла {csv_file}: {str(e)}")
            continue

    # Оптимизируем базу данных
    #  cursor.execute("VACUUM")
    conn.commit()
    conn.close()
    print(f"\nБаза данных '{db_name}' успешно создана. Загружено {len(csv_files)} файлов.")


if __name__ == '__main__':
    csv_folder = 'csv_data'
    db_name = 'MOEX_HOUR'
    create_database_from_csv(csv_folder, db_name)