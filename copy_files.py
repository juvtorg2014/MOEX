import os
import shutil
import sys
from pathlib import Path

# Путь к папке с файлами
folder_path = os.getcwd()
folder_root = Path(folder_path)
MOEX_PATH = 'C:\\Quik'


def get_list_files(MOEX_PATH):
    moex_folder = Path(MOEX_PATH)
    exange_folder = Path(moex_folder / 'Мосбиржа')
    if not os.path.exists(exange_folder):
        exange_folder.mkdir(parents=True, exist_ok=True)

    for txt_file in moex_folder.rglob('*.png'):
        dir_name = txt_file.stem

        if '_' in dir_name:
            dir_name = dir_name.split('_')[0]
        elif ' ' in dir_name :
            dir_name = dir_name.split(' ')[0]
        new_dir = exange_folder / dir_name
        # Создаем папку (exist_ok=True пропускает, если папка уже есть)
        try:
            new_dir.mkdir(exist_ok=True)
            if os.path.exists(new_dir / txt_file.name):
                print(f"⚠ Файл {txt_file.stem} уже существует в {new_dir}, пропускаем.")
            else:
                shutil.copy2(txt_file, new_dir)
                print(f'Файл {txt_file.stem} скопирован!')
        except OSError as e:
            print(f"❌ Ошибка файловой системы: {e}")
        except Exception as e:
            print(f"❌ Неизвестная ошибка: {e}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        get_list_files(sys.argv[1])
    else:
        get_list_files(MOEX_PATH)