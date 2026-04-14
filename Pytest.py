import re
from pathlib import Path
import yaml
from pydantic import BaseModel, Field

cfg_path = Path(__file__).parent / "cfg.yaml"
home_path = Path.home()

def game_name (path):
    path = Path(path)
    while 'save' in path.parent.name.lower():
        if path.parent.name != 'Users':
            path = path.parent
        else:
            s = 1
            break
    name = re.sub(r'[_\-\s]', '', str(path))
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
            raw = yaml.safe_load(f)
        if raw != None:
            return Games_cfg.model_validate(raw)
    return Games_cfg()

def save_cfg(cfg_obj):
    model_cfg = cfg_obj.model_dump()
    with open(cfg_path, "w", encoding= "utf-8") as f:
        yaml.dump(model_cfg, f)

def game_init ():
    data = load_cfg()
    x = list(home_path.glob("**/*.sav"))
    seen_id = {i.game_id for i in data.games}
    for i in x:
        if hash(str(i.parent)) not in seen_id:
            new_game = Game_data(game_path= str(i.parent), name= game_name(i.parent))
            seen_id.add(new_game.game_id)
            data.games.append(new_game)
    save_cfg(data)

