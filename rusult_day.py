""" Получение результатов анализа базы данных по дневным данным.
    Каждая функция - отдельный запрос.
"""

import pandas as pd
import numpy as np
import sqlite3
import os
from sqlite3 import OperationalError
from collections import Counter
from scipy.stats import trim_mean

SELECTED = ['СБЕРБАНК', 'ГАЗПРОМАО', 'ЛУКОЙЛ', 'РОСНЕФТЬ', 'ВТБАО', 'НОВАТЭКАО', 'ГМКНОРНИК', 'Т-ТЕХНОАО', 'МЕЧЕЛАО',
        'АЛРОСААО', 'АЭРОФЛОТ', 'БСПАО', 'ГАЗПРНЕФТЬ', 'ИНАРКТИКА', 'ИНТЕРРАОАО', 'МАГНИТАО', 'МКБАО', 'ММК',
        'МОСБИРЖА ', 'МОСЭНЕРГО', 'МТС_АО', 'НЛМКАО', 'НОВАТЭКАО', 'ПОЛЮС', 'РОСНЕФТЬ', 'РОССЕТИ', 'РОСТЕЛ_АО',
        'РУСГИДРО', 'СБЕРБАНК_П', 'СЕВСТ_АО', 'СИСТЕМААО', 'СУРГУТНФГЗ', 'СУРГУТНФГЗ_П', 'ТАТНФТЗАО', 'ТАТНФТЗАП',
        'ТРАНСФАП', 'ФОСАГРОАО ', 'ЭН_ГРУПАО', 'ЭТАЛОНГРУП', 'ЮНИПРОАО']

PERCENT = 0.2
RANGE_PERCENT = 0.5

def connect_to_db(db_path, date_start, date_end):
    try:
        conn = sqlite3.connect(db_path)
    except OperationalError:
        print('База не нашласть в папке', db_path)
    cursor = conn.cursor()
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)['name'].tolist()
    all_data = pd.DataFrame()
    for table in tables:
        cursor.execute(
            f"SELECT COUNT(*) FROM {table} WHERE Date = ?",(date_end,)        )
        count = cursor.fetchone()
        if count[0] > 0:
            sql = "SELECT * FROM " + table
            query = f" WHERE Date BETWEEN Date('{date_start}') AND Date('{date_end}') "
            sql += query
            sql += " ORDER BY Date"

            try:
                df = pd.read_sql(sql, conn)

                if df.size != 0:
                    df['Ticker'] = table
                    all_data = pd.concat([all_data, df], ignore_index=True)
            except sqlite3.Error as e:
                print(f"Ошибка при обработке таблицы {table}: {e}")
    conn.close()
    return all_data


def result_atr_day(date_start, end_date, name_base):
    df = connect_to_db(name_base, date_start, end_date)
    if '-' in date_start:
        new_dir = date_start.replace('-', '') + '_' + end_date.replace('-', '')
        new_dir = 'ATR_' + new_dir
    else:
        new_dir = date_start + '_' + end_date
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
    robust_ser = new_df.groupby('Ticker')['ATR'].apply(lambda x: trim_mean(x, proportiontocut=PERCENT)).round(2)
    iqr_ser = new_df.groupby('Ticker')['ATR'].agg(calculate_iqr).round(2)

    # Записываем средние значения в файл
    mean_df = pd.concat([mean_ser, median_ser, robust_ser, iqr_ser], axis=1)
    mean_df.columns = ['Mean', 'Median', 'Robust', 'IQR']
    mean_file = os.path.join(os.getcwd(), date_start + '_' + end_date + '_ATR.csv')
    mean_df.to_csv(mean_file, header=True)

    result = new_df.groupby('Ticker')['ATR'].agg(['min', 'max']).reset_index()

    result2 = new_df.groupby('Ticker')['ATR'].apply(calculate_range_frequency).reset_index()
    sorted_df = result2.groupby('Ticker', group_keys=False).apply(
                lambda x: x.sort_values('ATR', ascending=False)).reset_index(drop=True)
    result3 = sorted_df.groupby('Ticker').head(10)
    percent_file = os.path.join(os.getcwd(), date_start + '_' + end_date + '_percent.csv')
    result3.to_csv(percent_file, header=True)

    for symbol in new_df['Ticker']:
        min_val = result.loc[result['Ticker'] == symbol, 'min'].values[0]
        max_val = result.loc[result['Ticker'] == symbol, 'max'].values[0]
        symbol_data = new_df[new_df['Ticker'] == symbol]['ATR']

        bins = np.linspace(min_val, max_val, 11)
        frequency = pd.cut(symbol_data, bins=bins, include_lowest=True)

    for ticker, group in group_df:
        new_name = new_dir + ticker + '_ATR.csv'
        group.to_csv(new_name, index=False)
        print(f'Записан файл {new_name}')


def calculate_range_frequency(series):
    min_val = series.min()
    max_val = series.max()
    bins = np.arange(min_val, max_val + RANGE_PERCENT, RANGE_PERCENT)
    return pd.cut(series, bins=bins, include_lowest=True).value_counts().sort_index()


def calculate_iqr(series) -> float:
    # Функция для расчёта IQR
    q1 = series.quantile(0.2)
    q3 = series.quantile(0.8)
    iqr = q3 - q1
    return iqr


def day_of_week(date_start, end_date, name_base):
    df = connect_to_db(name_base, date_start, end_date)

    if '-' in date_start:
        new_file = date_start[2:].replace('-', '') + '_' + end_date[2:].replace('-', '')
        new_file = 'week_' + new_file
    else:
        new_file = date_start[2:] + '_' + end_date[2:]
        new_file = 'week_' + new_file
    new_dir = os.getcwd() + '\\' + new_file + '.csv'

    # Добавить день недели
    df['day_of_week'] = pd.to_datetime(df['Date']).dt.day_name().str[:3]

    df['signal'] = np.where(df['Close'] > df['Close'].shift(1), 'Long', 'Short')
    new_df = df[['Date', 'day_of_week', 'Close', 'signal','Ticker']].copy()
    new_df['Date'] = pd.to_datetime(new_df['Date'])

    # Статистика по дням недели для каждой акции
    day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    new_df['day_of_week'] = pd.Categorical(new_df['day_of_week'], categories=day_order, ordered=True)
    new_df = new_df.groupby(['Ticker', 'day_of_week'], observed=True)['signal'].value_counts().unstack(fill_value=0).reset_index()

    # Добавляем итоги
    new_df['Long_%'] = (new_df['Long'] / (new_df['Long'] + new_df['Short']) * 100).round(2)
    new_df['Short_%'] = (new_df['Short'] / (new_df['Long'] + new_df['Short']) * 100).round(2)
    save_to_file(new_dir, new_df)


def analyze_price_sequences(df):
    """    Анализирует последовательности плюсов и минусов для акций """
    file = os.getcwd()
    results = []
    df = df[['Ticker', 'Date', 'Close']].copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(['Ticker', 'Date'])

    # Группируем по тикеру
    for ticker, group in df.groupby('Ticker'):
        group = group.sort_values('Date')

        # Вычисляем изменение относительно предыдущего дня
        group['change'] = group['Close'].pct_change() * 100
        group['direction'] = np.where(group['change'] > 0, '+',
                                      np.where(group['change'] < 0, '-', '0'))

        # Создаем последовательность
        sequence = ''.join(group['direction'].dropna().tolist())

        # Находим все подпоследовательности длиной от 2 до 5
        sequences_counter = Counter()

        # Анализируем последовательности разной длины
        for length in range(2, 3):  # от 2 до 5 символов
            for i in range(len(sequence) - length + 1):
                subseq = sequence[i:i + length]
                sequences_counter[subseq] += 1

        # Находим однотипные последовательности
        homogeneous_seqs = find_homogeneous_sequences(sequence)

        # Группируем по типу и длине
        plus_sequences = Counter()
        minus_sequences = Counter()

        for seq_info in homogeneous_seqs:
            if seq_info['type'] == '+':
                plus_sequences[seq_info['length']] += 1
            else:
                minus_sequences[seq_info['length']] += 1

            # Находим самую длинную последовательность каждого типа
        max_plus = max(plus_sequences.keys(), default=0)
        max_minus = max(minus_sequences.keys(), default=0)

        # Добавляем результаты
        results.append({
            'ticker': ticker,
            'total_days': len(sequence),
            'up_days': sequence.count('+'),
            'down_days': sequence.count('-'),
            'neutral_days': sequence.count('0'),
            'most_common_seqs': sequences_counter.most_common(10)
        })
    return results


def find_homogeneous_sequences(sequence):
    """
    Находит только однотипные последовательности (только '+' или только '-')
    и возвращает их длину и позиции
    """
    sequences = []
    current_char = None
    current_length = 0
    start_index = 0

    for i, char in enumerate(sequence):
        if char in ['+', '-']:  # учитываем только плюсы и минусы
            if char == current_char:
                current_length += 1
            else:
                # Сохраняем предыдущую последовательность если она была
                if current_length > 1 and current_char in ['+', '-']:
                    sequences.append({
                        'type': current_char,
                        'length': current_length,
                        'start': start_index,
                        'end': i - 1,
                        'sequence': current_char * current_length
                    })

                # Начинаем новую последовательность
                current_char = char
                current_length = 1
                start_index = i
        else:
            # Прерываем последовательность при нейтральном символе
            if current_length > 1 and current_char in ['+', '-']:
                sequences.append({
                    'type': current_char,
                    'length': current_length,
                    'start': start_index,
                    'end': i - 1,
                    'sequence': current_char * current_length
                })
            current_char = None
            current_length = 0

    # Добавляем последнюю последовательность
    if current_length > 1 and current_char in ['+', '-']:
        sequences.append({
            'type': current_char,
            'length': current_length,
            'start': start_index,
            'end': len(sequence) - 1,
            'sequence': current_char * current_length
        })

    return sequences


def analysis_results(date_start, end_date,  df):
    # Анализируем данные последовательностей
    analysis_results = analyze_price_sequences(df)
    new_df = pd.DataFrame(analysis_results)
    date_start = date_start.replace("-", "")[2:]
    end_date = end_date.replace("-", "")[2:]
    new_file = os.path.join(os.getcwd(), date_start + '_' + end_date + '_seq.csv')
    # Выводим результаты
    for result in analysis_results:
        print(f"\nТикер: {result['ticker']}")
        print(f"Всего дней: {result['total_days']}")
        print(f"Дней в плюсе: {result['up_days']}")
        print(f"Дней в минусе: {result['down_days']}")
        print(f"Нейтральных дней: {result['neutral_days']}")
        print("\nСамые частые последовательности:")
        for seq, count in result['most_common_seqs']:
            print(f"  {seq}: {count} раз")
    save_to_file(new_file, new_df)


def save_to_file(new_dir, df):
    df.to_csv(new_dir, index=False)
    print(f'Файл {new_dir} сохранен')


if __name__ == '__main__':
    # date_start = input('Введите дату начала в формате <2020-01-31>\n')
    # end_date = input('Введите дату окончания в формате <2020-12-31>\n')
    date_start = '2025-05-01'
    end_date = '2025-07-31'
    #name_base = input('Ведите имя базы данных: \n')
    name_base = 'micex.db'
    df = connect_to_db(name_base, date_start, end_date)
    analysis_results(date_start, end_date,  df)
    day_of_week(date_start, end_date, name_base)
    #result_atr_day(date_start, end_date, name_base)