import sqlite3
import pandas as pd
import glob
import os

PERIODS = 'D'
LITERALS = 'Date'

def clear_list(list_name):
    new_list = []
    path = os.getcwd() + '\\' + csv_folder + '\\'
    for file in list_name:
        #file= file.rsplit('.',1)[0]
        file = os.path.basename(file)[:-4]
        if '-' in file:
            new_file = file.replace('-','_')
            new_list.append(path + new_file + '.csv')
            os.rename(path + file + '.csv', path + new_file + '.csv')
        elif file[0] == '+':
            new_file = file.replace('+', '')
            new_list.append(path + new_file + '.csv')
            os.rename(path + file + '.csv', path + new_file + '.csv')
        elif '+' in file:
            new_file = file.replace('+', '_')
            new_list.append(path + new_file + '.csv')
            os.rename(path + file + '.csv', path + new_file + '.csv')
        elif '.' in file:
            new_file = file.replace('.', '_')
            new_list.append(path + new_file + '.csv')
            os.rename(path + file + '.csv', path + new_file + '.csv')
        else:
            new_list.append(path + file + '.csv')
    return new_list


def fill_database_from_csv(csv_folder, db_name, time_frame):
    """
      Предполагаемый порядок колонок: Date, Time, Open, High, Low, Close, Volume.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    files = glob.glob(os.path.join(csv_folder, '*.csv'))
    csv_files = clear_list(files)
    if not csv_files:
        print(f"В папке '{csv_folder}' не найдено CSV-файлов.")
        return
    if time_frame == 'D':
        column_names = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    else:
        column_names = ['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    for csv_file in csv_files:
        # Извлекаем имя акции из имени файла
        stock_name = os.path.splitext(os.path.basename(csv_file))[0]
        print(stock_name)
        try:
            # Читаем первую строку без заголовков
            first_row = pd.read_csv(csv_file, header=None, nrows=1).values.tolist()[0]
            if first_row[0].lower() == 'date':
                df = pd.read_csv(csv_file, skiprows=1, names=column_names)
            else:
                df = pd.read_csv(csv_file, header=False, names=column_names)

            # Проверяем, что все колонки имеют правильный тип данных
            #df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
            df = df.dropna(subset=['Date'])

            if time_frame != 'D':
                df = df.dropna(subset=['Date', 'Time'])
                if df['Time'].dtype == 'int64':
                    # Если время в формате HHMMSS (целое число)
                    df['Time'] = df['Time'].astype(str).str.zfill(6)
                    df['Time'] = df['Time'].str[:2] + ':' + df['Time'].str[2:4] + ':' + df['Time'].str[4:6]
                else:
                    df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.strftime('%H:%M:%S')
            df['Open'] = (pd.to_numeric(df['Open'],errors='coerce')).round(6)
            df['High'] = (pd.to_numeric(df['High'],errors='coerce')).round(6)
            df['Low'] = (pd.to_numeric(df['Low'],errors='coerce')).round(6)
            df['Close'] = (pd.to_numeric(df['Close'],errors='coerce')).round(6)
            df['Volume'] = pd.to_numeric(df['Volume'],errors='coerce').round(0)

            # Получение последней даты
            try:
                cursor.execute(f"SELECT * FROM {stock_name} ORDER BY Date DESC LIMIT 1")
                last_day = cursor.fetchone()[0]
                last_day = '2025-08-01'
                start_day = pd.to_datetime(last_day)
            except sqlite3.Error as e:
                print(f"Ошибка получения последней даты: {e}")
            df['Date'] = pd.to_datetime(df['Date'])
            df_new = df[df['Date'] > start_day]

            # Загрузка данных с проверкой дубликатов
            if not df.empty:
                for _, row in df.iterrows():
                    try:
                        if time_frame == 'D':
                            cursor.execute(f'''
                                        INSERT OR IGNORE INTO "{stock_name}"
                                        (Date, Open, High, Low, Close, Volume)
                                        VALUES (?, ?, ?, ?, ?, ?)
                                        ''', tuple(row))
                            #df.to_sql(stock_name, conn, if_exists='append', index=False)
                        else:
                            cursor.execute(f'''
                                        INSERT OR IGNORE INTO "{stock_name}"
                                        (Date, Time, Open, High, Low, Close, Volume)
                                        VALUES (?, ?, ?, ?, ?, ?, ?)
                                        ''', tuple(row))
                            #df.to_sql(stock_name, conn, if_exists='append', index=False)
                    except sqlite3.Error as e:
                        print(f"Ошибка при вставке данных: {e}")
                        continue

                # Сортировка сначала по дате (date), затем по времени (time)
                cursor.execute(f'SELECT * FROM {stock_name} ORDER BY Date ASC, Time ASC')
                print(f"Данные для акции '{stock_name}' успешно загружены из папки {csv_file}")
        except Exception as e:
            print(f"{str(e)}")
            continue
    conn.commit()
    conn.close()
    print(f"\nБаза данных '{db_name}' успешно создана. Загружено {len(csv_files)} файлов.")


if __name__ == '__main__':
    # csv_folder = input('Введите папку с файлами:\n')
    csv_folder = 'micex'
    # db_name = input('Введите имя базы без разширения:\n')
    db_name = 'micex.db'
    fill_database_from_csv(os.getcwd() + '\\' + csv_folder,  db_name, PERIODS)