import os
import ctypes
from ctypes import c_char_p, c_size_t, Structure, POINTER
from pathlib import Path
from db_connect import ConnMang

db = ConnMang()
db.open()

class PackagedFile(Structure):
    _fields_ = [
        ("md5", ctypes.c_char * 33),
        ("zip_data", POINTER(ctypes.c_ubyte)),
        ("zip_size", c_size_t)
    ]

# 1. Получаем абсолютный путь к папке, где лежит capi.py
BASE_DIR = Path(__file__).parent.resolve()
dll_path = BASE_DIR / "game_packer.dll"

try:
    # 2. Говорим Windows искать зависимости (если они есть) в этой же папке
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(BASE_DIR))

    # 3. Загружаем DLL по строгому абсолютному пути
    packer_lib = ctypes.CDLL(str(dll_path))

    packer_lib.pack_file_to_memory.argtypes = [c_char_p]
    packer_lib.pack_file_to_memory.restype = POINTER(PackagedFile)
    packer_lib.free_packaged_file.argtypes = [POINTER(PackagedFile)]
    packer_lib.free_packaged_file.restype = None
except Exception as e:
    print("!!! ОШИБКА ЗАГРУЗКИ DLL:")
    import traceback
    traceback.print_exc()
    packer_lib = None
def do_games_backup():
    if not packer_lib:
        return 1

    games = db.get_all_games_with_paths()

    for game_id, game_path in games:
        path_obj = Path(game_path)
        if not path_obj.exists():
            continue

        backup_id = db.add_backup(game_id)

        for file in path_obj.iterdir():
            if file.is_file():
                c_file_path = str(file).encode('utf-8')
                res_ptr = packer_lib.pack_file_to_memory(c_file_path)

                if not res_ptr:
                    continue

                res = res_ptr.contents
                file_hash = res.md5.decode('utf-8')
                zip_bytes = bytes(res.zip_data[:res.zip_size])

                db.add_file(file_hash, zip_bytes)
                db.add_link(backup_id, file_hash)

                packer_lib.free_packaged_file(res_ptr)


try:
    do_games_backup()
    print("Backup process completed successfully!")
finally:
    db.close()