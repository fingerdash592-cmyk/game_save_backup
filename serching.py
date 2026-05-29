import re
from pathlib import Path
import psycopg
from db_connect import ConnMang

home_path = Path.home()

db = ConnMang()
db.open()

def game_name(path):
    path = Path(path)
    if path.is_file():
        path = path.parent
    while 'save' in path.name.lower():
        if path.parent.name != 'Users':
            path = path.parent
        else:
            break
    name = re.sub(r'[_\-\s]', '', str(path.name))
    return re.sub(r'([a-z])([A-Z0-9])', r'\1 \2', name)


def game_init():
    print("Searching save files")
    x = list(home_path.glob("**/*.sav"))

    for i in x:
        if not list(i.parent.glob("*.vdf")):
            g_path = str(i.parent)
            g_name = game_name(i.parent)

            game_id = db.add_game(g_name)
            db.add_path(game_id, g_path)

    print("Scanning successfully complete")


def game_add():
    print("Enter the path to the save files of your game")
    path = Path(input())
    if not path.exists():
        print("Path does not exist")
        return 1

    g_path = str(path)
    g_name = game_name(path)
    game_id = db.add_game(g_name)
    db.add_path(game_id, g_path)
    print(f"Game '{g_name}' successfully added/updated in Database.")


def game_del():
    print("Enter the name of the game you want to delete")
    name = input()

    # ИСПРАВЛЕНО: Теперь удаляем из БД одним SQL-запросом через сессию пула
    with db.getconnection() as conn:
        with conn.cursor() as cur:
            # Благодаря ON DELETE CASCADE в структуре таблиц,
            # удаление игры автоматически сотрет все её пути и бэкапы!
            cur.execute("DELETE FROM games WHERE lower(name) = lower(%s) RETURNING id;", [name])
            deleted_row = cur.fetchone()

            if deleted_row:
                print("Game successfully deleted from Database (with all paths and backups)")
            else:
                print("Game wasn't found in Database")


