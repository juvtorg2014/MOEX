import pandas as pd
import sqlite3
import os
from sqlite3 import OperationalError
from pandas import ExcelWriter
import openpyxl


DB_PATH = "d:/Projects/Course/MOEX/stocks.db"
start_date = '2010-02-01'
end_date = '2010-03-01'
symbol = 'Сбербанк'
OUTPUT_FILE = "stocks_data.xlsx"

def get_stock_data(db_path, date_start, date_end, one_symbol):
    conn = sqlite3.connect(DB_PATH)
    sql = "SELECT * FROM " + one_symbol + ' WHERE Date '
    query = f" BETWEEN date('{date_start}') AND date('{date_end}') "
    sql += query
    sql += " ORDER BY Date, Time"
    try:
        df = pd.read_sql(sql, conn)
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


# daily_highs = df.loc[df.groupby('Date')['High'].idxmax()]
# daily_highs = daily_highs[['Date', 'Time', 'High']]
# daily_highs.columns = ['Date', 'time_of_high', 'daily_high']

def make_name_stocks(base_name) -> list:
    name_stocks = []
    conn = sqlite3.connect(base_name)  # или :memory: для временной БД
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        name_stocks.append(table[0])
    cursor.close()
    conn.close()
    return name_stocks

stocks_name = make_name_stocks(DB_PATH)
for stock in stocks_name:
    print(stock)
    daily_highs, daily_lows = get_stock_data(DB_PATH, start_date, end_date, stock)
    output_file = os.path.join(os.getcwd(), OUTPUT_FILE)
    with ExcelWriter(output_file, engine='openpyxl') as writer:
        if not daily_highs.empty:
            daily_highs.to_excel(writer, sheet_name=stock, index=False)
        if not daily_lows.empty:
            daily_lows.to_excel(writer, sheet_name=stock, index=False)
    print(daily_highs)
    print(daily_lows)


