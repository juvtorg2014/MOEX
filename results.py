""" Получение результатов анализа базы данных.
    Каждая функция - отдельный запрос.
    Планируется сделать окно и вывод графика.
"""
import pandas as pd
import sqlite3
import os
from sqlite3 import OperationalError
from stats import trim_mean


DB_PATH = "d:/Projects/MOEX/stocks.db"
symbol = 'Сбербанк'
OUTPUT_FILE = "stocks_data.csv"
PROCENT = 0.2

def connect_to_db(db_path, dat_s, dat_e):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)['name'].tolist()
    all_data = pd.DataFrame()
    for table in tables:
        try:
            sql = "SELECT * FROM " + table
            query = f" WHERE Date BETWEEN Date('{dat_s}') AND Date('{dat_e}') "
            sql += query
            sql += " ORDER BY Date, Time"
            df = pd.read_sql(sql, conn)

            if df.size != 0:
                df = df.rename(columns={'ATR': 'Ticker'})
                df['Ticker'] = table
                all_data = pd.concat([all_data, df], ignore_index=True)
        except sqlite3.Error as e:
            print(f"Ошибка при обработке таблицы {table}: {e}")
    conn.close()
    return all_data


def get_high_low_hours(db_path, date_start, date_end, one_symbol):
    '''Получение статисики по High и Low дня по часам каждой акции'''
    conn = sqlite3.connect(DB_PATH)
    sql = "SELECT * FROM " + one_symbol + ' WHERE Date '
    query = f" BETWEEN date('{date_start}') AND date('{date_end}') "
    sql += query
    sql += " ORDER BY Date, Time"
    sql2 = "SELECT * FROM " + one_symbol
    try:
        df = pd.read_sql(sql, conn)
        if df.size == 0:
            # df = pd.read_sql(sql2, conn)
            # if df[date_start].size:
            #     df = df[(df['date'] >= date_start) & (df['date'] <= date_end)]
            return [0], [0]
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
    except OperationalError as e:
        print(f"Нет диапазона дат в таблице {one_symbol}")
    finally:
        conn.close()

    df['is_daily_high'] = df['High'] == df.groupby('Date')['High'].transform('max')
    df['is_daily_low'] = df['Low'] == df.groupby('Date')['Low'].transform('min')

    result = df.groupby(df['Time'].str.extract(r'(\d{2}):')[0].astype(int)).agg(
        total_hours=('is_daily_high', 'count'), high_count=('is_daily_high', 'sum'),
        low_count=('is_daily_low', 'sum')).reset_index()

    result['high_percent'] = (result['high_count'] / result['total_hours'] * 100).round(2)
    result['low_percent'] = (result['low_count'] / result['total_hours'] * 100).round(2)

    res_high = result.sort_values('high_percent', ascending=False)
    res_low = result.sort_values('low_percent', ascending=False)

    res_high = res_high.iloc[:,[0,1,2,4]]
    res_low = res_low.iloc[:,[0,1,3,5]]
    res_high.columns = ['Hour','Total','High','Percent']
    res_low.columns = ['Hour', 'Total', 'Low', 'Percent']
    return res_high, res_low


def make_name_stocks(base_name) -> list:
    name_stocks = []
    try:
        conn = sqlite3.connect(base_name)  # или :memory: для временной БД
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
    except OperationalError as e:
        print(f"Не удалось подключиться к базе данных {base_name}")
        exit()
    for table in tables:
        name_stocks.append(table[0])
    cursor.close()
    conn.close()
    return name_stocks


def set_high_low_hours(start_date, end_date):
    '''Запись статисики по High и Low дня по часам каждой акции в файлы'''
    stocks_name = make_name_stocks(DB_PATH)
    new_dir = start_date.replace('-', '') + '_' + end_date.replace('-', '')
    if not os.path.exists(new_dir):
       os.mkdir(new_dir)
    for stock in stocks_name:
        try:
            daily_highs, daily_lows = get_high_low_hours(DB_PATH, start_date, end_date, stock)
            if len(daily_highs) > 1:
                daily_highs.to_csv(new_dir + '/' + stock + '_High.csv', index=False)
                daily_lows.to_csv(new_dir + '/' + stock + '_Low.csv', index=False)
            else:
                print(f"Нет данных за период с {start_date} по {end_date} акции> {stock}")
        except Exception as e:
            print(f"Ошибка получения данных акции {stock} за период с <{start_date}> по <{end_date}>")
            continue
    print(f"Файлы записаны в папку {new_dir}")


def get_high_low_day(start_date, end_date):
    """Получение дневного АТР за любой промежуток времени"""
    df = connect_to_db(DB_PATH, start_date, end_date)

    if '-' in start_date:
        new_dir = start_date.replace('-', '') + '_' + end_date.replace('-', '')
        new_dir = 'ATR_' + new_dir
    else:
        new_dir = start_date + '_' + end_date
        new_dir = 'ATR_' + new_dir
    if not os.path.exists(new_dir):
        os.mkdir(new_dir)
    new_dir = os.getcwd() + '\\' + new_dir + '\\'

    # Группируем по дате и находим High/Low
    daily_h_l = df.groupby(['Date', 'Ticker']).agg({
                                    'High': 'max', 'Low': 'min'}).reset_index()
    daily_h_l['ATR'] = (((daily_h_l['High'] - daily_h_l['Low']) / daily_h_l['Low']) * 100)
    daily_h_l['ATR'] = daily_h_l['ATR'].round(2)

    columns = ['Date', 'Ticker', 'ATR']
    group_df = daily_h_l[columns].groupby('Ticker')
    new_df = group_df.apply(lambda x: x.sort_values('Date', ascending=True))
    new_df = new_df.copy().reset_index(drop=True)
    list_tickers = sorted(list(set(new_df.iloc[:,1].tolist())), key=None, reverse=False)

    # Вычесляем разные средние
    mean_ser = group_df['ATR'].mean().round(2)
    median_ser = group_df['ATR'].median().round(2)
    robust_ser = new_df.groupby('Ticker')['ATR'].apply(lambda x: trim_mean(x, proportiontocut=PROCENT)).round(2)
    iqr_ser = new_df.groupby('Ticker')['ATR'].agg(calculate_iqr).round(2)

    # Записываем средние значения в файл
    mean_df = pd.concat([mean_ser, median_ser, robust_ser, iqr_ser], axis=1)
    mean_df.columns = ['Mean', 'Median', 'Robust', 'IQR']
    mean_file = os.path.join(os.getcwd(), start_date + '_' + end_date + '_ATR.csv')
    mean_df.to_csv(mean_file, header=True)

    for ticker, group in group_df:
        new_name = new_dir + ticker + '_ATR.csv'
        group.to_csv(new_name, index=False)
        print(f'Записан файл {new_name}')


def calculate_iqr(series) -> float:
    # Функция для расчёта IQR
    q1 = series.quantile(0.2)
    q3 = series.quantile(0.8)
    iqr = q3 - q1
    return iqr


if __name__ == '__main__':
    # date_start = input('Введите дату начала в формате <2020-01-31>\n')
    # end_date = input('Введите дату окончания в формате <2020-12-31>\n')
    date_start = '2025-06-01'
    end_date = '2025-06-31'
    # set_high_low_hours(date_start, end_date)
    get_high_low_day(date_start, end_date)