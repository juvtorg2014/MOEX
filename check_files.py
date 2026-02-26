# Проверка правильности заполнения тикеров
import os
import sys
from pathlib import Path

list_stocks = ['AFKS','AFLT','ALRS','BSPB','CBOM','CHMF','ENPG','FLOT', 'GAZP','GMKN',
               'HEAD','IRAO','LKOH','MAGN','MDMG', 'MOEX','MSNG', 'MTSS','NLMK','NVTK',
               'PHOR', 'PIKK','PLZL','POSI','RENI','ROSN','RTKM','RUAL','SBER', 'SBERP',
               'SNGS', 'SNGSP','SVCB', 'T','TATN', 'TATNP', 'TRNFP', 'UGLD', 'UPRO','VKCO',
               'VTBR','X5', 'YDEX']


def check_files(path_check):
    folder_root = Path(path_check)
    list_errors = []

    for txt_file in folder_root.rglob('*.png'):
        dir_name = txt_file.stem
        if '_' not in dir_name:
            file_name = dir_name.split('-')[1] + '.txt'
            list_errors.append(txt_file)
        else:
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
        folder_path = os.getcwd() + '\\2025-09-08'
        folder_root = Path(folder_path)
        check_files(folder_root)