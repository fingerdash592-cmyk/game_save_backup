import psycopg
from psycopg.errors import DuplicateDatabase

conn = psycopg.connect("dbname=postgres user=postgres password=adm")
conn.autocommit = True
with conn.cursor() as cur:

    req = "create database game_saves"
    ex = 0
    try:
        cur.execute (req)
    except DuplicateDatabase:
        ex = 1

with psycopg.connect("dbname=game_saves user=postgres password=adm") as conn:
    with conn.cursor() as cur:

        req =  (
                "create table if not exists games("
                "id serial primary key,"
                "name varchar(150) not null unique);"
                
                "create table if not exists paths("
                "id serial primary key,"
                "game_id integer references games(id) on delete cascade,"
                "path varchar(150) not null unique);"
                
                "create table if not exists backups("
                "id serial primary key,"
                "game_id integer references games(id) on delete cascade,"
                "btime timestamptz not null default now());"
                
                "create table if not exists files("
                "md5_hash varchar(32) primary key,"
                "file bytea not null);"
                
                "create table if not exists link("
                "md5_hash varchar(32) references files(md5_hash) on delete cascade,"
                "backup_id integer references backups (id) on delete cascade,"
                "primary key (md5_hash, backup_id));"
                )

        cur.execute_script(req)



