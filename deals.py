'''
Анализ сделок на итоговый результат в Еxcel
'''
import pandas as pd
from datetime import datetime, timedelta
import warnings
import os
from openpyxl.styles import PatternFill, Font

warnings.filterwarnings('ignore')

COLUMN_MAPPING = {
    '№ сделки': '№',
    'Код': 'Код',
    'Наименование': 'Наим',
    'Размер_лота': 'Лот',
    'Дата_открытия': 'ДатаО',
    'Время_открытия': 'ВремяО',
    'Дата_закрытия': 'ДатаЗ',
    'Время_закрытия': 'ВремяЗ',
    'Время_удержания_мин': 'ВремяУ',
    'Кол-во_лотов': 'Лоты',
    'Кол-во_акций': 'Акции',
    'Цена_открытия_срвзв': 'ЦенаО',
    'Цена_закрытия_срвзв': 'ЦенаЗ',
    'Объём_открытия': 'ОбъёмО',
    'Объём_закрытия': 'ОбъёмЗ',
    'Прибыль_убыток': 'P&L',
    'Направление': 'Напр',
    'Комиссия': 'Ком',
    'Результат_%': '%'
}


def calculate_lot_size(price, volume, qty):
    if qty == 0 or price == 0:
        return 0, 0
    shares = volume / price
    lot_size = shares / qty if qty > 0 else 0
    return shares, lot_size


def determine_lot_sizes(df):
    lot_sizes = {}
    for code in df['Код'].unique():
        code_df = df[df['Код'] == code]
        sizes = []
        for _, row in code_df.iterrows():
            if row['Кол-во'] > 0 and row['Цена'] > 0 and row['Объём'] > 0:
                shares = row['Объём'] / row['Цена']
                lot_size = shares / row['Кол-во']
                if lot_size > 0 and abs(lot_size - round(lot_size)) < 0.01:
                    sizes.append(round(lot_size))
        if sizes:
            from collections import Counter
            lot_size_counts = Counter(sizes)
            most_common = lot_size_counts.most_common(1)[0][0]
            lot_sizes[code] = most_common
        else:
            lot_sizes[code] = 1
    return lot_sizes


def calculate_weighted_prices(transactions):
    if not transactions:
        return 0, 0, 0, 0
    total_shares = sum(t['shares'] for t in transactions)
    total_value = sum(t['shares'] * t['price'] for t in transactions)
    total_qty_lots = sum(t['qty_lots'] for t in transactions)
    if total_shares == 0:
        return 0, 0, 0, 0
    avg_price = total_value / total_shares
    return avg_price, total_value, total_shares, total_qty_lots


def calculate_trade_results(file_path):
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    required_columns = ['Дата', 'Время', 'Код', 'Наименование', 'Направление', 'Кол-во', 'Цена', 'Объём', 'Комиссия']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Отсутствует колонка: {col}")

    df['Дата_Время'] = pd.to_datetime(df['Дата'].astype(str) + ' ' + df['Время'].astype(str))
    lot_sizes = determine_lot_sizes(df)
    df = df.sort_values('Дата_Время')

    positions = {}
    all_trades = []
    trade_counter = 1

    for idx, row in df.iterrows():
        code = row['Код']
        name = row['Наименование']
        direction = str(row['Направление']).strip().lower()
        qty_lots = float(row['Кол-во'])
        price = float(row['Цена'])
        volume = float(row['Объём'])
        commission = float(row['Комиссия'])
        trade_time = row['Дата_Время']
        shares = volume / price if price > 0 else 0
        lot_size = lot_sizes.get(code, 1)

        if code not in positions:
            positions[code] = {
                "long_position": {
                    "transactions": [],
                    "total_shares": 0,
                    "total_qty_lots": 0,
                    "avg_price": 0,
                    "total_volume": 0,
                    "open_time": None
                },
                "short_position": {
                    "transactions": [],
                    "total_shares": 0,
                    "total_qty_lots": 0,
                    "avg_price": 0,
                    "total_volume": 0,
                    "open_time": None
                },
                "name": name,
                "lot_size": lot_size,
                "open_orders": []
            }
        pos = positions[code]

        if direction in ["купля", "buy", "покупка", "b", "купить"]:
            transaction = {
                'id': f"{code}_BUY_{trade_time.strftime('%Y%m%d_%H%M%S')}_{qty_lots}_{idx}",
                'date': trade_time,
                'qty_lots': qty_lots,
                'shares': shares,
                'price': price,
                'volume': volume,
                'commission': commission,
                'type': 'BUY'
            }
            remaining_shares = shares
            remaining_lots = qty_lots
            while remaining_shares > 0 and pos['open_orders']:
                order = pos['open_orders'][0]
                if order['type'] == 'SELL_SHORT':
                    close_shares = min(order['remaining_shares'], remaining_shares)
                    close_lots = close_shares / lot_size
                    pnl = (order['price'] - price) * close_shares
                    pnl -= (commission * (close_shares / shares) + order['commission'] * (
                                close_shares / order['shares']))
                    holding_minutes = (trade_time - order['date']).total_seconds() / 60
                    all_trades.append({
                        'trade_id': trade_counter,
                        'code': code,
                        'name': name,
                        'lot_size': lot_size,
                        'open_datetime': order['date'],
                        'close_datetime': trade_time,
                        'open_date': order['date'].date(),
                        'open_time': order['date'].strftime('%H:%M:%S'),
                        'close_date': trade_time.date(),
                        'close_time': trade_time.strftime('%H:%M:%S'),
                        'holding_minutes': holding_minutes,
                        'qty_lots': close_lots,
                        'shares': close_shares,
                        'open_price': order['price'],
                        'close_price': price,
                        'open_volume': order['price'] * close_shares,
                        'close_volume': price * close_shares,
                        'pnl': pnl,
                        'direction': 'ШОРТ',
                        'commission': commission * (close_shares / shares) + order['commission'] * (
                                    close_shares / order['shares'])
                    })
                    trade_counter += 1
                    order['remaining_shares'] -= close_shares
                    order['remaining_lots'] -= close_lots
                    if order['remaining_shares'] <= 0:
                        pos['open_orders'].pop(0)
                    remaining_shares -= close_shares
                    remaining_lots -= close_lots
                    pos['short_position']['total_shares'] -= close_shares
                    pos['short_position']['total_qty_lots'] -= close_lots
                    if pos['short_position']['total_shares'] <= 0:
                        pos['short_position']['transactions'] = []
                        pos['short_position']['avg_price'] = 0
                        pos['short_position']['total_volume'] = 0
                        pos['short_position']['open_time'] = None
            if remaining_shares > 0:
                transaction['shares'] = remaining_shares
                transaction['qty_lots'] = remaining_lots
                pos['long_position']['transactions'].append(transaction)
                pos['long_position']['total_shares'] += remaining_shares
                pos['long_position']['total_qty_lots'] += remaining_lots
                if pos['long_position']['total_shares'] == remaining_shares:
                    pos['long_position']['open_time'] = trade_time
                avg_price, total_volume, total_shares, total_qty_lots = calculate_weighted_prices(
                    pos['long_position']['transactions'])
                pos['long_position']['avg_price'] = avg_price
                pos['long_position']['total_volume'] = total_volume

        elif direction in ["продажа", "sell", "продажа", "s", "продать"]:
            transaction = {
                'id': f"{code}_SELL_{trade_time.strftime('%Y%m%d_%H%M%S')}_{qty_lots}_{idx}",
                'date': trade_time,
                'qty_lots': qty_lots,
                'shares': shares,
                'price': price,
                'volume': volume,
                'commission': commission,
                'type': 'SELL'
            }
            remaining_shares = shares
            remaining_lots = qty_lots
            while remaining_shares > 0 and pos['long_position']['total_shares'] > 0:
                close_shares = min(pos['long_position']['total_shares'], remaining_shares)
                close_lots = close_shares / lot_size
                avg_price = pos['long_position']['avg_price']
                pnl = (price - avg_price) * close_shares
                pnl -= commission * (close_shares / shares)
                if pos['long_position']['open_time']:
                    holding_minutes = (trade_time - pos['long_position']['open_time']).total_seconds() / 60
                else:
                    holding_minutes = 0
                all_trades.append({
                    'trade_id': trade_counter,
                    'code': code,
                    'name': name,
                    'lot_size': lot_size,
                    'open_datetime': pos['long_position']['open_time'],
                    'close_datetime': trade_time,
                    'open_date': pos['long_position']['open_time'].date() if pos['long_position'][
                        'open_time'] else trade_time.date(),
                    'open_time': pos['long_position']['open_time'].strftime('%H:%M:%S') if pos['long_position'][
                        'open_time'] else trade_time.strftime('%H:%M:%S'),
                    'close_date': trade_time.date(),
                    'close_time': trade_time.strftime('%H:%M:%S'),
                    'holding_minutes': holding_minutes,
                    'qty_lots': close_lots,
                    'shares': close_shares,
                    'open_price': avg_price,
                    'close_price': price,
                    'open_volume': avg_price * close_shares,
                    'close_volume': price * close_shares,
                    'pnl': pnl,
                    'direction': 'ЛОНГ',
                    'commission': commission * (close_shares / shares)
                })
                trade_counter += 1
                pos['long_position']['total_shares'] -= close_shares
                pos['long_position']['total_qty_lots'] -= close_lots
                shares_to_remove = close_shares
                new_transactions = []
                for t in pos['long_position']['transactions']:
                    if shares_to_remove <= 0:
                        new_transactions.append(t)
                    elif t['shares'] <= shares_to_remove:
                        shares_to_remove -= t['shares']
                    else:
                        t['shares'] -= shares_to_remove
                        t['qty_lots'] -= shares_to_remove / lot_size
                        new_transactions.append(t)
                        shares_to_remove = 0
                pos['long_position']['transactions'] = new_transactions
                if pos['long_position']['total_shares'] > 0:
                    avg_price, total_volume, total_shares, total_qty_lots = calculate_weighted_prices(
                        pos['long_position']['transactions'])
                    pos['long_position']['avg_price'] = avg_price
                    pos['long_position']['total_volume'] = total_volume
                    if pos['long_position']['transactions']:
                        pos['long_position']['open_time'] = pos['long_position']['transactions'][0]['date']
                else:
                    pos['long_position']['avg_price'] = 0
                    pos['long_position']['total_volume'] = 0
                    pos['long_position']['open_time'] = None
                    pos['long_position']['transactions'] = []
                remaining_shares -= close_shares
                remaining_lots -= close_lots
            if remaining_shares > 0:
                transaction['shares'] = remaining_shares
                transaction['qty_lots'] = remaining_lots
                transaction['remaining_shares'] = remaining_shares
                transaction['remaining_lots'] = remaining_lots
                transaction['type'] = 'SELL_SHORT'
                pos['open_orders'].append(transaction)
                pos['short_position']['transactions'].append(transaction)
                pos['short_position']['total_shares'] += remaining_shares
                pos['short_position']['total_qty_lots'] += remaining_lots
                if pos['short_position']['total_shares'] == remaining_shares:
                    pos['short_position']['open_time'] = trade_time
                avg_price, total_volume, total_shares, total_qty_lots = calculate_weighted_prices(
                    pos['short_position']['transactions'])
                pos['short_position']['avg_price'] = avg_price
                pos['short_position']['total_volume'] = total_volume

    if all_trades:
        all_trades_sorted = sorted(all_trades, key=lambda x: x['open_datetime'])
        grouped_trades = []
        current_group = None
        for trade in all_trades_sorted:
            if current_group is None:
                current_group = {
                    'code': trade['code'],
                    'name': trade['name'],
                    'lot_size': trade['lot_size'],
                    'open_datetime': trade['open_datetime'],
                    'close_datetime': trade['close_datetime'],
                    'direction': trade['direction'],
                    'trades': [trade],
                    'total_shares': trade['shares'],
                    'total_qty_lots': trade['qty_lots'],
                    'total_pnl': trade['pnl'],
                    'total_commission': trade['commission'],
                    'total_holding_minutes': trade['holding_minutes'] * trade['shares']
                }
            elif (current_group['code'] == trade['code'] and
                  current_group['direction'] == trade['direction'] and
                  abs((current_group['open_datetime'] - trade['open_datetime']).total_seconds()) < 300 and
                  abs((current_group['close_datetime'] - trade['close_datetime']).total_seconds()) < 300):
                current_group['trades'].append(trade)
                current_group['total_shares'] += trade['shares']
                current_group['total_qty_lots'] += trade['qty_lots']
                current_group['total_pnl'] += trade['pnl']
                current_group['total_commission'] += trade['commission']
                current_group['total_holding_minutes'] += trade['holding_minutes'] * trade['shares']
                if trade['close_datetime'] > current_group['close_datetime']:
                    current_group['close_datetime'] = trade['close_datetime']
            else:
                grouped_trades.append(current_group)
                current_group = {
                    'code': trade['code'],
                    'name': trade['name'],
                    'lot_size': trade['lot_size'],
                    'open_datetime': trade['open_datetime'],
                    'close_datetime': trade['close_datetime'],
                    'direction': trade['direction'],
                    'trades': [trade],
                    'total_shares': trade['shares'],
                    'total_qty_lots': trade['qty_lots'],
                    'total_pnl': trade['pnl'],
                    'total_commission': trade['commission'],
                    'total_holding_minutes': trade['holding_minutes'] * trade['shares']
                }
        if current_group is not None:
            grouped_trades.append(current_group)

        # Отфильтровываем группы с очень маленьким количеством акций (погрешности)
        grouped_trades = [g for g in grouped_trades if g['total_shares'] >= 0.5]
        grouped_trades_sorted = sorted(grouped_trades, key=lambda x: x['open_datetime'])

        trade_results = []
        for i, group in enumerate(grouped_trades_sorted):
            total_open_value = sum(t['open_price'] * t['shares'] for t in group['trades'])
            total_close_value = sum(t['close_price'] * t['shares'] for t in group['trades'])
            weighted_open_price = total_open_value / group['total_shares']
            weighted_close_price = total_close_value / group['total_shares']
            avg_holding_minutes = group['total_holding_minutes'] / group['total_shares']
            trade_results.append({
                '№ сделки': i + 1,
                'Код': group['code'],
                'Наименование': group['name'],
                'Размер_лота': int(group['lot_size']),
                'Дата_открытия': group['open_datetime'].date(),
                'Время_открытия': group['open_datetime'].strftime('%H:%M:%S'),
                'Дата_закрытия': group['close_datetime'].date(),
                'Время_закрытия': group['close_datetime'].strftime('%H:%M:%S'),
                'Время_удержания_мин': round(avg_holding_minutes, 1),
                'Кол-во_лотов': round(group['total_qty_lots'], 2),
                'Кол-во_акций': round(group['total_shares']),
                'Цена_открытия_срвзв': round(weighted_open_price, 4),
                'Цена_закрытия_срвзв': round(weighted_close_price, 4),
                'Объём_открытия': round(total_open_value, 2),
                'Объём_закрытия': round(total_close_value, 2),
                'Прибыль_убыток': round(group['total_pnl'], 2),
                'Направление': group['direction'],
                'Комиссия': round(group['total_commission'], 2),
                'Результат_%': round((group['total_pnl'] / total_open_value) * 100, 2) if total_open_value > 0 else 0
            })

        if trade_results:
            results_df = pd.DataFrame(trade_results)
            results_df = results_df.sort_values(['Дата_открытия', 'Время_открытия'])
            results_df['№ сделки'] = range(1, len(results_df) + 1)
            total_pnl = results_df['Прибыль_убыток'].sum()
            total_commission = results_df['Комиссия'].sum()
            total_trades = len(results_df)
            total_volume_open = results_df['Объём_открытия'].sum()
            total_shares = results_df['Кол-во_акций'].sum()
            summary_row = pd.DataFrame([{
                '№ сделки': 'ИТОГО',
                'Код': '',
                'Наименование': f'Всего сделок: {total_trades}',
                'Размер_лота': '',
                'Дата_открытия': '',
                'Время_открытия': '',
                'Дата_закрытия': '',
                'Время_закрытия': '',
                'Время_удержания_мин': '',
                'Кол-во_лотов': '',
                'Кол-во_акций': round(total_shares),
                'Цена_открытия_срвзв': '',
                'Цена_закрытия_срвзв': '',
                'Объём_открытия': round(total_volume_open, 2),
                'Объём_закрытия': '',
                'Прибыль_убыток': round(total_pnl, 2),
                'Направление': '',
                'Комиссия': round(total_commission, 2),
                'Результат_%': round((total_pnl / total_volume_open) * 100, 2) if total_volume_open > 0 else 0
            }])
            results_df = pd.concat([results_df, summary_row], ignore_index=True)

            # Форматирование для вывода
            numeric_cols = ['Кол-во_лотов', 'Кол-во_акций', 'Цена_открытия_срвзв', 'Цена_закрытия_срвзв',
                            'Объём_открытия', 'Объём_закрытия', 'Прибыль_убыток',
                            'Комиссия', 'Результат_%', 'Время_удержания_мин']
            results_df_formatted = results_df.copy()
            for col in numeric_cols:
                if col in results_df_formatted.columns:
                    if col == 'Кол-во_акций':
                        results_df_formatted[col] = results_df_formatted[col].apply(
                            lambda x: f"{x:,.0f}" if pd.notnull(x) and isinstance(x, (int, float)) else x
                        )
                    elif col == 'Кол-во_лотов':
                        results_df_formatted[col] = results_df_formatted[col].apply(
                            lambda x: f"{x:,.2f}" if pd.notnull(x) and isinstance(x, (int, float)) else x
                        )
                    elif col in ['Цена_открытия_срвзв', 'Цена_закрытия_срвзв']:
                        results_df_formatted[col] = results_df_formatted[col].apply(
                            lambda x: f"{x:,.4f}" if pd.notnull(x) and isinstance(x, (int, float)) else x
                        )
                    elif col == 'Результат_%':
                        results_df_formatted[col] = results_df_formatted[col].apply(
                            lambda x: f"{x:+.2f}%" if pd.notnull(x) and isinstance(x, (int, float)) else x
                        )
                    elif col == 'Время_удержания_мин':
                        results_df_formatted[col] = results_df_formatted[col].apply(
                            lambda x: f"{x:,.1f}" if pd.notnull(x) and isinstance(x, (int, float)) else x
                        )
                    else:
                        results_df_formatted[col] = results_df_formatted[col].apply(
                            lambda x: f"{x:,.2f}" if pd.notnull(x) and isinstance(x, (int, float)) else x
                        )
            return results_df_formatted, positions, results_df
        else:
            columns = ['№ сделки', 'Код', 'Наименование', 'Размер_лота', 'Дата_открытия', 'Время_открытия',
                       'Дата_закрытия', 'Время_закрытия', 'Время_удержания_мин', 'Кол-во_лотов',
                       'Кол-во_акций', 'Цена_открытия_срвзв', 'Цена_закрытия_срвзв', 'Объём_открытия',
                       'Объём_закрытия', 'Прибыль_убыток', 'Направление', 'Комиссия', 'Результат_%']
            results_df = pd.DataFrame(columns=columns)
            return results_df, positions, results_df
    else:
        columns = ['№ сделки', 'Код', 'Наименование', 'Размер_лота', 'Дата_открытия', 'Время_открытия',
                   'Дата_закрытия', 'Время_закрытия', 'Время_удержания_мин', 'Кол-во_лотов',
                   'Кол-во_акций', 'Цена_открытия_срвзв', 'Цена_закрытия_срвзв', 'Объём_открытия',
                   'Объём_закрытия', 'Прибыль_убыток', 'Направление', 'Комиссия', 'Результат_%']
        results_df = pd.DataFrame(columns=columns)
        return results_df, positions, results_df


def add_results_to_same_file(file_path, results_df_formatted):
    try:
        existing_sheets = pd.read_excel(file_path, sheet_name=None)
    except:
        existing_sheets = {}
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        for sheet_name, sheet_data in existing_sheets.items():
            if sheet_name != 'Результаты_сделок':
                sheet_data.to_excel(writer, sheet_name=sheet_name, index=False)
        results_df_formatted.to_excel(writer, sheet_name='Результаты_сделок', index=False)
        worksheet = writer.sheets['Результаты_сделок']
        column_widths = {
            '№': 5, 'Код': 8, 'Наим': 15, 'Лот': 6,
            'ДатаО': 12, 'ВремяО': 10, 'ДатаЗ': 12,
            'ВремяЗ': 10, 'ВремяУ': 10, 'Лоты': 8,
            'Акции': 10, 'ЦенаО': 10, 'ЦенаЗ': 10,
            'ОбъёмО': 10, 'ОбъёмЗ': 10, 'P&L': 10,
            'Напр': 8, 'Ком': 10, '%': 10
        }
        for idx, column in enumerate(results_df_formatted.columns):
            width = column_widths.get(column, 15)
            col_letter = chr(65 + idx) if idx < 26 else chr(64 + idx // 26) + chr(65 + idx % 26)
            worksheet.column_dimensions[col_letter].width = width
        if not results_df_formatted.empty:
            for i, value in enumerate(results_df_formatted['№']):
                if value == 'ИТОГО':
                    total_row_index = i + 2
                    for col_idx in range(1, len(results_df_formatted.columns) + 1):
                        cell = worksheet.cell(row=total_row_index, column=col_idx)
                        cell.font = Font(bold=True)
                    fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
                    for col_idx in range(1, len(results_df_formatted.columns) + 1):
                        cell = worksheet.cell(row=total_row_index, column=col_idx)
                        cell.fill = fill
    print(f"✓ Результаты добавлены в лист 'Результаты_сделок'")


def print_lot_summary(lot_sizes):
    print("\n" + "=" * 80)
    print("РАЗМЕРЫ ЛОТОВ ПО АКЦИЯМ:")
    print("=" * 80)
    print(f"{'Код':<10} {'Размер лота':>15}")
    print("-" * 80)
    for code, lot_size in lot_sizes.items():
        print(f"{code:<10} {lot_size:>15.0f}")


def print_detailed_summary(results_df_numeric):
    print("\n" + "=" * 100)
    print("ДЕТАЛЬНАЯ СТАТИСТИКА СДЕЛОК")
    print("=" * 100)
    if results_df_numeric.empty or len(results_df_numeric) == 1:
        print("\nНет закрытых сделок для анализа")
        return
    trades_df = results_df_numeric[results_df_numeric['№ сделки'] != 'ИТОГО'].copy()
    if trades_df.empty:
        print("\nНет закрытых сделок для анализа")
        return
    print(f"\nВсего сделок: {len(trades_df)}")
    avg_holding = trades_df['Время_удержания_мин'].mean()
    min_holding = trades_df['Время_удержания_мин'].min()
    max_holding = trades_df['Время_удержания_мин'].max()
    print(f"\nВремя удержания (мин): среднее {avg_holding:.1f}, мин {min_holding:.1f}, макс {max_holding:.1f}")
    total_shares = trades_df['Кол-во_акций'].sum()
    total_lots = trades_df['Кол-во_лотов'].sum()
    total_pnl = trades_df['Прибыль_убыток'].sum()
    total_commission = trades_df['Комиссия'].sum()
    total_volume_open = trades_df['Объём_открытия'].sum()
    print(f"\nФинансовые результаты:")
    print(f"  Всего акций: {total_shares:,.0f}")
    print(f"  Всего лотов: {total_lots:,.2f}")
    print(f"  Общий объём открытия: {total_volume_open:,.2f}")
    print(f"  Общая прибыль: {total_pnl:+,.2f}")
    print(f"  Общая комиссия: {total_commission:,.2f}")
    print(f"  Чистый результат: {total_pnl - total_commission:+,.2f}")


if __name__ == "__main__":
    file_path = "Report_01.xlsx"  # замените на путь к вашему файлу
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл '{file_path}' не найден")
        print(f"Обрабатываю файл: {file_path}")
        df_preview = pd.read_excel(file_path)
        lot_sizes = determine_lot_sizes(df_preview)
        print_lot_summary(lot_sizes)
        print("\nРасчет финансовых результатов...")
        results_df_formatted, positions, results_df_numeric = calculate_trade_results(file_path)
        if not results_df_formatted.empty:
            trades_df = results_df_formatted[results_df_formatted['№ сделки'] != 'ИТОГО']
            print(f"\n✓ Найдено {len(trades_df)} сделок")
            # Проверка сортировки
            dates = pd.to_datetime(trades_df['Дата_открытия'].astype(str) + ' ' + trades_df['Время_открытия'])
            is_sorted = all(dates.iloc[i] <= dates.iloc[i + 1] for i in range(len(dates) - 1))
            print(f"✓ Сортировка по дате входа: {'✅' if is_sorted else '❌'}")
        results_df_formatted = results_df_formatted.rename(columns=COLUMN_MAPPING)
        add_results_to_same_file(file_path, results_df_formatted)
        print_detailed_summary(results_df_numeric)
        print("\n" + "=" * 80)
        print("ГОТОВО! Файл обновлен.")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ Ошибка: {str(e)}")
        import traceback

        traceback.print_exc()