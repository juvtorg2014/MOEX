import datetime

import datetime
import calendar

from futures import CURRENT_DIR

TRIPLE_D = [{'Z4': '19-12-2024'}, {'H5': '20-03-2025'}, {'M5': '19-06-2025'}, {'U5': '18-09-2025'}, {'Z5': '18-12-2025'}]




code_futures = {'1':'F','2':'G','3':'H','4':'J','5':'K','6':'M',
               '7':'N','8':'Q','9':'U','10':'V','11':'X','12':'Z'}

# 57 фьючерсных контракта на акции
contracts = ['AF', 'AK', 'AL', 'AS', 'BN', 'BS', 'CH', 'CM', 'FE', 'FL', 'FS', 'GK', 'GZ', 'HY', 'IR', 'IS',
             'KM', 'LE', 'LK', 'MC', 'ME', 'MG', 'MN', 'MT', 'MV', 'NB', 'NK', 'NM', 'PH', 'PI', 'PS', 'PZ',
             'RA', 'RL', 'RN', 'RT', 'RU', 'S0', 'SC', 'SE', 'SG', 'SH', 'SN','SO', 'SP', 'SR', 'SS', 'SZ',
             'T', 'TI', 'TN', 'TP', 'TT', 'VB', 'VK', 'WU', 'YD']

# 41 контракт на 3-х месячные фьючерсы
futures = ['AE', 'BB', 'BD', 'BR', 'CF', 'CR', 'CS','DJ', 'DX', 'ED', 'EM','EU', 'FN', 'GD', 'GL', 'GU',
           'HK', 'HO', 'HS', 'IP', 'JP', 'KZ','MA', 'MM', 'MX', 'N2', 'NA', 'OG', 'PD', 'PT', 'R2', 'RB',
           'RI', 'RM', 'SF', 'SV', 'SX', 'SI', 'TY', 'UC', 'W4']

# Не стандартные фьючерсы: 2-х и 1-месячные
commodities_1 = ['AL', 'BR','CO', 'NG', 'NI', 'SU', 'WH', 'ZN']

# Вечные фьючерсы
long_futures = ['CNYRUBF', 'EURRUBF', 'GLDRUBF', 'IMOEXF', 'USDRUBF']

BIG_CONTRACTS = contracts + futures
MAIN_CONTRACT = 'M5'

usual_fufures = contracts + futures + long_futures

CURRENT_YEAR = datetime.datetime.today().date().year
CODE_YEAR = str(CURRENT_YEAR - 2020)
THIRD_THURSDAY = ['2025-05-15','2025-07-17','2025-09-16']

def make_code(date) -> str:
    ''' Определение кода фьючерса для контракта '''
    date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
    day_week = date_obj.isoweekday()
    current_year = str(date_obj.year - 2020)
    current_month = str(date_obj.month)
    current_code = code_futures.get(current_month) + current_year
    return current_code

def check_weekday(day, month) -> int:
    ''' Проверка на выходной '''
    if calendar.weekday(CURRENT_YEAR, month,day) == 6:
        new_day = day - 2
    elif calendar.weekday(CURRENT_YEAR, month,day) == 5:
        new_day = day - 1
    else:
        new_day = day
    return new_day


def unusual_contract(date) -> list:
    ''' Нестандартныe фьючерсы по 1 и 2 месяца '''
    list_contracts = []
    month = int(date[5:7])
    middle_work_day = check_weekday(15, month)
    last_day = calendar.monthrange(CURRENT_YEAR, int(date[5:7]))[1]
    last_work_day = check_weekday(last_day, month)

    date_today = datetime.datetime.strptime(date, '%Y-%m-%d')
    if date_today.day > 1:
        code_gl  = 'BR' + code_futures.get(str(date_today.month + 1)) + CODE_YEAR
    list_contracts.append(code_gl)

    if date_today.day > middle_work_day:
        code_sugar = 'SU' + code_futures.get(str(date_today.month + 1)) + CODE_YEAR
        list_contracts.append(code_sugar)
    else:
        code_sugar = 'SU' + code_futures.get(str(date_today.month)) + CODE_YEAR
        list_contracts.append(code_sugar)

    if date_today.day < last_work_day:
        code_wheat = 'WH' + code_futures.get(str(date_today.month)) + CODE_YEAR
        list_contracts.append(code_wheat)

    if date < THIRD_THURSDAY[0]:
        code_cocoa = 'CC' + 'K' + CODE_YEAR
    elif date >= THIRD_THURSDAY[0] and date < THIRD_THURSDAY[1]:
        code_cocoa = 'CC' + 'N' + CODE_YEAR
    elif date >= THIRD_THURSDAY[1] and date < THIRD_THURSDAY[2]:
        code_cocoa = 'CC' + 'U' + CODE_YEAR
    else:
        code_cocoa = 'CC' + 'X' + CODE_YEAR
    list_contracts.append(code_cocoa)

    print(f'День средний {middle_work_day}')
    print(f'День последний {last_work_day}')
    print(list_contracts)
    return list_contracts


#unusual_futures = unusual_contract('2025-09-16')
#print(usual_fufures + unusual_futures)
new_list = list(map(lambda x: x + MAIN_CONTRACT, BIG_CONTRACTS))
for item in new_list:
    print(item)