# Проверка правильности заполнения тикеров
import os
import sys
from pathlib import Path

list_stocks = ['AFKS','AFLT','ALRS','ASTR','BSPB','CBOM','CHMF','ENPG','FEES','FLOT',
               'GAZP','GMKN','HEAD','HYDR','IRAO','LKOH','MAGN','MOEX','MTLR', 'MTSS',
               'NLMK', 'NVTK','PIKK','PLZL','POSI','RENI','ROSN','RTKM','RUAL','SBER',
               'SELG', 'SNGSP','SVCB', 'T','TATN','TRNFP','UGLD','UPRO','VKCO','VTBR','YDEX']


def check_files(path_check):
    folder_root = Path(path_check)
    list_errors = []

    for txt_file in folder_root.rglob('*.png'):
        dir_name = txt_file.stem
        begin_file = dir_name.split('_')[0]
        if begin_file:
            if begin_file not in list_stocks:
                file_name = dir_name.split('_')[1] + '.txt'
                list_errors.append(txt_file)

    for file in list_errors:
        print(file)

    if len(list_errors) > 0:
        output_file = os.path.join(os.getcwd(), file_name)
        with open(output_file,'w', encoding='utf-8') as f:
            for item in list_errors:
                f.write(f"{item}\n")
    else:
        print("Всё сделано хорошо! Молодец!")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        check_files(sys.argv[1])
    else:
        folder_path = os.getcwd()
        folder_root = Path(folder_path)
        check_files(folder_root)