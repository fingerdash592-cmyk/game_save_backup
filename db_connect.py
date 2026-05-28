import psycopg
import psycopg_pool
from psycopg.generators import execute, fetch


class ConnMang:
    def __init__(self, conninfo = "dbname=game_saves user=postgres password=adm"):
        self.pool = psycopg_pool.ConnectionPool(conninfo= conninfo, min_size= 1, max_size= 5, open= False)

    def open(self):
        self.pool.open()

    def getconnection(self):
        return self.pool.connection()

    def close(self):
        self.pool.close()

    def add_game (self, game_name):
        with self.getconnection() as conn:
            with conn.cursor() as cur:
                req = ("insert into games (name) values (%s) "
                       "on conflict (name) do update set name =  excluded.name "
                       "returning id;"
                       )

                cur.execute(req, [game_name])
                game_id  = cur.fetchone()[0]

                return game_id
    def add_path (self, game_id, path):
        with self.getconnection() as conn:
            with conn.cursor() as cur:
                req = ("insert into paths (game_id, path) values (%s, %s) "
                       "on conflict (path) do nothing"
                       )

                cur.execute(req, [game_id, path])
    def add_backup (self, game_id):
        with self.getconnection() as conn:
            with conn.cursor() as cur:
                req = ("insert into backups (game_id) values (%s)"
                       "returning id")

                cur.execute(req, [game_id])
                backup_id = cur.fetchone()[0]
                return backup_id

    def add_file(self, file_hash, file_bytes):
        with self.getconnection() as conn:
            with conn.cursor() as cur:
                cur.execute("select md5_hash from files where md5_hash = %s;", [file_hash])
                row = cur.fetchone()
                if row:
                    return row[0]
                req = ("insert into files (md5_hash, file) values (%s, %s);")
                cur.execute(req, [file_hash, file_bytes])

    def add_link(self, backup_id, file_hash):
        with self.getconnection() as conn:
            with conn.cursor() as cur:
                req = ("insert into link (backup_id, md5_hash) values (%s, %s) "
                       "on conflict do nothing")
                cur.execute(req, [backup_id, file_hash])

    def get_all_games_with_paths(self):
        with self.getconnection() as conn:
            with conn.cursor() as cur:
                req = ("SELECT game_id, path FROM paths;")
                cur.execute(req)

                return cur.fetchall()

    def get_all_games(self):
        with self.getconnection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name FROM games ORDER BY name;")
                return cur.fetchall()
    def get_game_paths(self, game_id):
        with self.getconnection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT path FROM paths WHERE game_id = %s;", [game_id])
                return [row[0] for row in cur.fetchall()]

    def get_backups_by_game(self, game_id):
        with self.getconnection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, btime FROM backups WHERE game_id = %s ORDER BY btime DESC;", [game_id])
                return cur.fetchall()

    def get_backup_files(self, backup_id):
        with self.getconnection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT f.file "
                            "FROM files f "
                            "JOIN link l ON f.md5_hash = l.md5_hash "
                            "WHERE l.backup_id = %s;", [backup_id])
                return [row[0] for row in cur.fetchall()]

    def delete_single_backup(self, backup_id):
        with self.getconnection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM backups WHERE id = %s;", [backup_id])