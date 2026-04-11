import re
from pathlib import Path

def game_name (name):
    name = name.replace('_', ' ').replace('-', ' ')
    return re.sub(r'([a-z])([A-Z])', r'\1 \2', name)

cfgpath = Path(__file__).parent
if cfgpath.glob('cfg.txt'):
    p = Path("C:\\Users\\user")
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
    with open(str(cfgpath) + r"\cfg.txt", 'w', encoding="utf-8") as f:
        for i in dic.keys():
            f.write(i + "\n" + str(dic[i]) + "\n")
