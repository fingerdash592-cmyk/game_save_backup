import re
from pathlib import Path

cfgpath = Path(__file__).parent / "cfg.txt"
p = Path("C:\\Users\\user")


def game_name (name):
    name = name.replace('_', ' ').replace('-', ' ')
    return re.sub(r'([a-z])([A-Z0-9])', r'\1 \2', name)
def start():
    if not cfgpath.exists():
        x = list(p.glob('**/*.sav'))
        dic = {}
        for i in x:
            s = 0
            while 'save' in i.parent.name.lower():
                if i.parent.name != 'Users':
                    i = i.parent
                else:
                    s = 1
                    break
            if not s:
                dic[game_name(i.parent.name)] = i.parent
        with open(cfgpath, 'w', encoding="utf-8") as f:
            for i in dic.keys():
                f.write(i + "\n" + str(dic[i]) + "\n")
def add_game():
    print("Enter the name of the game you want to add:")
    name = game_name(input().replace(" ", ""))
    print("Enter the path where the .sav files are saved:")
    way = input().replace(" ", "")
    with open(cfgpath, 'a', encoding="utf-8") as f:
            f.write("\n" + name + "\n" + way, )

def delete_game():
    if not cfgpath.exists():
        print("Файл настроек не найден.")
        return
    print("Enter the name of the game you want to delete:")
    name = game_name(input().replace(" ", ""))
    skip = False
    new_data = []
    for i in cfgpath.read_text().splitlines():
        if skip:
            skip = False
            continue
        if i == name:
            skip = True
            continue
        new_data.append(i)
    res = [i for i in new_data]
    cfgpath.write_text("\n".join (res), encoding="utf-8")

