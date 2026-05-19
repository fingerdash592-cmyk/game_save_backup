import re
from pathlib import Path
import json
from pydantic import BaseModel, Field

cfg_path = Path(__file__).parent / "cfg.json"
home_path = Path.home()

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

class Game_data(BaseModel):
    game_path : str
    name : str

    @property
    def game_id(self) -> int:
        game_id = hash(self.game_path)
        return game_id

class Games_cfg(BaseModel):
    games : list[Game_data] = Field(default_factory = list)

def load_cfg():
    if cfg_path.exists():
        with open(cfg_path, "r", encoding= "utf-8") as f:
            raw = json.load(f)
        if raw != None:
            return Games_cfg.model_validate(raw)
    return Games_cfg()

def save_cfg(cfg_obj):
    model_cfg = cfg_obj.model_dump()
    with open(cfg_path, "w", encoding= "utf-8") as f:
        json.dump(model_cfg, f)

def game_init():
    data = load_cfg()
    x = list(home_path.glob("**/*.sav"))
    seen_id = {i.game_id for i in data.games}
    for i in x:
        if hash(str(i.parent)) not in seen_id and not list(i.parent.glob("*.vdf")):
            new_game = Game_data(game_path= str(i.parent), name= game_name(i.parent))
            seen_id.add(new_game.game_id)
            data.games.append(new_game)
    save_cfg(data)

def game_add():
    print("Enter the path to the save files of your game")
    path = Path(input())
    if not path.exists():
        print("Path does not exist")
        return 1
    name = game_name(path)
    new_game = Game_data(game_path= path, name= name)
    data = load_cfg()
    data.games.append(new_game)
    save_cfg(data)

def game_del():
    data = load_cfg()
    print("Enter the name of the game you want to delete")
    name = input()
    cnt = len(data.games)
    data.games = [game for game in data.games if game.name.lower() != name.lower()]
    if cnt > len(data.games):
        save_cfg(data)
        print("Game successfully deleted")
    else:
        print("Game wasn't found")

def menu():
    print("Hello in game save backup!")
    while(True):
        print("Choose your action\n1. Search and add the games from your PC\n2. Add your game\n3. Delete saved game\n4. Close")
        inp = input()
        if inp == "1":
            game_init()
        if inp == "2":
            game_add()
        if inp == "3":
            game_del()
        if inp == "4":
            break

menu()


