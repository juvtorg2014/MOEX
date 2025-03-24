"""Файл базы данных должен лежать в одной папке с файлом.
Проверяем папки в текущем каталоге и переносим все новые данные в базу"""
import sqlite3
import os
import pandas as pd
from numpy.f2py.auxfuncs import flatlist

sql = ('INSERT INTO OPEN (DATE,INST,LP,CH_LP,QT_LP,SP,CH_SP,QT_SP,LC,CH_LC,QT_LC,SC,CH_SC,QT_SC,SUM,CH_SUM,QT_SUM)'
         'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)' )


def sql_insert(list_files):
    if os.path.exists('MOEX.db'):
        con = sqlite3.connect('MOEX.db')
    else:
        exit("Не найдена база данных!")
    cur = con.cursor()
    new_list = []
    for file in list_files:
        name_file = os.path.basename(file)[:-7]
        instr, date_file = name_file.split('_')
        date_f = date_file[0:4] + '-' + date_file[4:6] + '-' + date_file[-2:]
        new_list.append([date_f])
        new_list.append([instr])
        data = pd.read_csv(file, sep = ' ')
        df = data.dropna(axis=1)
        df.columns = ['LP', 'SP', 'LC', 'SC', 'SUMMA']
        for column in df.columns:
            new_list.append(df[column].tolist())
        fl_lst = [el for inner in new_list for el in inner]

        with con:
            cur_date = fl_lst[0]
            cur_inst = fl_lst[1]
            exist_line = cur.execute(f'SELECT EXISTS(SELECT 1 FROM OPEN WHERE DATE="{cur_date}"'
                           f' AND INST="{cur_inst}")').fetchone()
            if type(exist_line) == tuple:
                if exist_line[0] == 1:
                    print(f'Данные {cur_inst} за {cur_date} уже есть в базе данных!')
                else:
                    con.execute(sql, tuple(fl_lst))
                    con.commit()
                    print(f"Загрузка {fl_lst[1]} за {fl_lst[0]}")
            else:
                con.execute(sql, tuple(fl_lst))
                con.commit()
                print(f"Загрузка {fl_lst[1]} за {fl_lst[0]}")
        new_list.clear()
    con.execute('SELECT DATE, INST, LP,CH_LP,QT_LP,SP,CH_SP,QT_SP,LC,CH_LC,'
                'QT_LC,SC,CH_SC,QT_SC,SUM,CH_SUM,QT_SUM FROM OPEN ORDER BY DATE, INST ')
    con.commit()
    con.close
    print("База закрыта!")

def find_files(path_base) -> list:
    file_list = []
    for root, dirs, files in os.walk(path_base):
        for file in files:
            if file.endswith('_OI.csv'):
                file_list.append(os.path.join(root, file))
    return file_list



if __name__ == '__main__':
    list_files = find_files(os.getcwd())
    if len(list_files) > 0:
        sql_insert(list_files)
    else:
        exit("Нет файлов для загрузки")
