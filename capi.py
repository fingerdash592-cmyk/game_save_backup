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

BASE_DIR = Path(__file__).parent.resolve()
dll_path = BASE_DIR / "game_packer.dll"

try:
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(BASE_DIR))

    packer_lib = ctypes.CDLL(str(dll_path))
    packer_lib.pack_file_to_memory.argtypes = [c_char_p]
    packer_lib.pack_file_to_memory.restype = POINTER(PackagedFile)
    packer_lib.free_packaged_file.argtypes = [POINTER(PackagedFile)]
    packer_lib.free_packaged_file.restype = None

    packer_lib.unpack_file_from_memory.argtypes = [POINTER(ctypes.c_ubyte), c_size_t, c_char_p]
    packer_lib.unpack_file_from_memory.restype = ctypes.c_int

except Exception as e:
    print("!!! ОШИБКА ЗАГРУЗКИ DLL:")
    import traceback
    traceback.print_exc()
    packer_lib = None

def do_single_game_backup(game_id, game_path):
    if not packer_lib: return False
    path_obj = Path(game_path)
    if not path_obj.exists(): return False

    backup_id = db.add_backup(game_id)
    success = False

    for file in path_obj.iterdir():
        if file.is_file():
            c_file_path = str(file).encode('utf-8')
            res_ptr = packer_lib.pack_file_to_memory(c_file_path)

            if not res_ptr: continue

            res = res_ptr.contents
            file_hash = res.md5.decode('utf-8')
            zip_bytes = bytes(res.zip_data[:res.zip_size])

            db.add_file(file_hash, zip_bytes)
            db.add_link(backup_id, file_hash)
            packer_lib.free_packaged_file(res_ptr)
            success = True

    return success

def restore_game_backup(backup_id, dest_dir):
    if not packer_lib: return False

    files_bytes = db.get_backup_files(backup_id)
    if not files_bytes: return False

    Path(dest_dir).mkdir(parents=True, exist_ok=True)

    for blob in files_bytes:
        size = len(blob)
        c_blob = (ctypes.c_ubyte * size).from_buffer_copy(blob)
        c_dest = str(dest_dir).encode('utf-8')
        packer_lib.unpack_file_from_memory(c_blob, size, c_dest)

    return True