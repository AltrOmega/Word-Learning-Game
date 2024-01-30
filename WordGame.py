from copy import deepcopy
from datetime import datetime
from enum import Enum
from os import listdir, system
from os.path import join
from random import choice, shuffle
from typing import List
import json
import shlex

GENERAL_SETTINGS_PATH = "general_settings.json"

SETTINGS_PATH = "settings.json"

GAME_HISTORY_PATH = "game_history.json"

GAME_SAVES_PATH = "game_saves.json"

############################# Basic file load func

def save_data_to_json(data: dict, file_path: str):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        return None



def load_data_from_json(file_path: str):
    try:
        with open(file_path, 'r') as f:
            loaded_data = json.load(f)
        return loaded_data
    except Exception as e:
        return None
    


def init_default(file_path: str, else_default):
    ld = load_data_from_json(file_path)
    if ld != None:
        return ld
    else:
        save_data_to_json(else_default, file_path)
        return deepcopy(else_default) 

############################# Settings

GENERAL_SETTINGS = {
    # Default variables
    "settings_path": SETTINGS_PATH,
    "game_history_path": GAME_HISTORY_PATH,   
    "game_saves_path": GAME_SAVES_PATH,
    # Info
    "show_score": True,
    "show_mistake_count": True,
    "show_position": True,
    # Afixes
    "split": " - ",
    "comment": "#"
}

general_settings = init_default(GENERAL_SETTINGS_PATH, GENERAL_SETTINGS)

settings_path = general_settings["settings_path"]
game_history_path = general_settings["game_history_path"]
game_saves_path = general_settings["game_saves_path"]

class SideChoice(Enum):
    RANDOM = 0
    LEFT = 1
    RIGHT = 2

def side_random_handle(side: SideChoice):
    if side == SideChoice.RANDOM:
        return choice([side.LEFT, side.RIGHT])
    return side



GAME_SETTINGS = {
    # Typing mode specific
    "typing_mode": False,
    "case_senstive": False,
    "white_space_senstive": False,
    # General
    "only_once": True,
    "random_line": False,
    "from_side": SideChoice.RANDOM.value,
    "line_whitelist": [],
    "line_blacklist": []
}

default_settings = init_default(settings_path, GAME_SETTINGS)

############################# Game data

GAME_DATA = {
    "begin_date_and_time": 0,
    "time_length": 0,
    "mistake_count": 0,
    "current_line": 0,
    "repeating_lines": [],
    "remaining_lines": [],
    "settings": default_settings
}



def save_game_data_list(gdl, file_path: str):
    try:
        for gd in gdl:
            gd['remaining_lines'] = [line.to_dict() for line in gd['remaining_lines']]
    except Exception as e:
        return None
    return save_data_to_json(gdl, file_path)



def load_game_data_list(file_path: str) -> List[dict]:
    if file_path == None or file_path == "":
        return []
    
    game_data_list = load_data_from_json(file_path)
    if game_data_list == None:
        return []
    
    try:
        for gd in game_data_list:       # TODO: Add error handling
            gd['remaining_lines'] = [Line.from_dict(line) for line in gd['remaining_lines']]    
    except Exception as e:
        return []

    return game_data_list
    


def get_default_game_data():
    return deepcopy(GAME_DATA)

############################# Lines

class Line:
    def __init__(self, left: str, right: str, side_answer: SideChoice = SideChoice.RANDOM):
        self.left = left
        self.right = right
        self.side_answer = side_random_handle(side_answer)
        self.index:int = None

    def __str__(self):
        return f"{self.left} - {self.right}"

    def side_as_string(self, side: SideChoice = SideChoice.RANDOM, show_split:bool = True):
        side = side_random_handle(side)

        if side == SideChoice.LEFT:
            ret =  f"{self.left}"
            ret += general_settings["split"] if show_split == True else ""
            return ret
        #elif side == SideChoice.RIGHT:
        ret =  f"{self.right}"
        ret = general_settings["split"] + ret if show_split == True else ret
        return ret

    def to_dict(self):
        return {
            "left": self.left,
            "right": self.right,
            "index": self.index,
            "correct_answer_side": self.correct_answer_side,
            "show_user_side": self.show_user_side,
        }

    @classmethod
    def from_dict(cls, data):
        line = cls(data["left"], data["right"], None)
        line.index = data["index"]
        line.correct_answer_side = data["correct_answer_side"]
        line.show_user_side = data["show_user_side"]
        return line



# TODO: Add error handling? Add Whitelist. Change the defaults to work with settings
# but not necesairly here
def raw_lines_to_line_list(raw_lines: List[str], 
blacklist = [], comment = "#", multi_line_comment = '"""',
split_ = " - ", side = SideChoice.RANDOM) -> List[Line]:
    lines = list()
    inside_ml_com = False
    for index, line in enumerate(raw_lines, start=1):
        if index not in blacklist:

            to_remove = None
            while multi_line_comment in line:
                start_index = line.find(multi_line_comment)

                if inside_ml_com:
                    to_remove = line[:start_index + len(multi_line_comment)]
                    inside_ml_com = False
                elif (end_index := line.find(multi_line_comment,
                start_index + len(multi_line_comment))) != -1:
                    to_remove = line[start_index:end_index + len(multi_line_comment)]
                else:
                    to_remove = line[start_index:]
                    inside_ml_com = True

                if to_remove is not None:
                    line = line.replace(to_remove, '', 1)
                    to_remove = None

            if comment in line:
                line = line[:line.index(comment)]

            if split_ in line:
                left, right = line.strip().split(split_)
                append_line = Line(left, right, side)
                append_line.index = index
                lines.append(append_line)
    return lines


# TODO: Add error handling
def load_files_on_dir(directory: str = "\\Saves", whitelist: list = [],
                      blacklist: list = []) -> List[Line]:
    dir_content = listdir(directory)

    if blacklist:
        dir_content = [item for item in dir_content if item not in blacklist]

    if whitelist:
        dir_content = [item for item in dir_content if item in whitelist]

    file_list = list()
    for file_name in dir_content:
        file_path_ = join(directory, file_name)
        with open(file_path_, 'r', encoding='utf-8') as f:
            file_list.extend(raw_lines_to_line_list(f.readlines()))

    return file_list

############################# Game engine

class GameEngine:
    def __init__(self, game_data: dict):
        if game_data["begin_date_and_time"] == 0:
            self.begin_date_and_time = datetime.now()
        else: self.begin_date_and_time = datetime.fromisoformat(game_data["begin_date_and_time"])
        
        self.time_length: float = game_data["time_length"]
        self.mistake_count: int = game_data["mistake_count"]
        self.current_line: int = game_data["current_line"]
        self.remaining_lines: List[Line] = game_data["remaining_lines"]
        self.original_lines_len = len(self.remaining_lines)
        self.settings = game_data["settings"]

    def shuffle_with_check(self):
        if self.settings["random_line"] == True:
            shuffle(self.remaining_lines)

    def extract_game_data(self) -> dict:
        gd = get_default_game_data()
        gd["begin_date_and_time"] = self.begin_date_and_time.isoformat()
        gd["time_length"] = self.time_length
        gd["mistake_count"] = self.mistake_count
        gd["current_line"] = self.current_line
        #gd["repeating_lines"] = self.repeating_lines # acts like a whitelist
        gd["remaining_lines"] = self.remaining_lines
        gd["settings"] = self.settings
        return gd
    
    def len_check(self):
        if len(self.remaining_lines) <= 0:
            return False
        else: return True

    def _step_forward(self):
        self.current_line += 1
        self.remaining_lines.pop(0)
        # False = End of game
        # True = Game is ongoing
        return self.len_check()
    
    def _mistake(self):
        self.mistake_count += 1
        if self.settings["only_once"] == False:
            self.remaining_lines.append(self.get_curent_line())

    def get_curent_line(self):
        return self.remaining_lines[0]
    
    def get_lines_len(self):
            return len(self.remaining_lines)
    
    def _answer_handle(self, user_input, correct_answer_side):
        if user_input != correct_answer_side: #Incorect answer
            self._mistake()           

        return self._step_forward()

    def progress_game_typing_mode(self, user_input = ""):
        line_current = self.get_curent_line()
        side_answer: str = line_current.side_as_string(line_current.side_answer, False)

        if self.settings["case_senstive"] == False:
            side_answer = side_answer.lower()
            user_input = user_input.lower()
        if self.settings["white_space_senstive"] == False:
            side_answer = ''.join(side_answer.split())
            user_input = ''.join(user_input.split())

        return self._answer_handle(user_input, side_answer)

    def progress_game_simple_mode(self, user_input = ""):
        return self._answer_handle(user_input, "")

############################# Game history

game_history = load_game_data_list(game_history_path)

############################# Game Master

class GameMaster:
    def __init__(self, game_saves_path=GAME_SAVES_PATH):
        self.game_data_list = load_game_data_list(game_saves_path)
        self.game_id = None
        self.game_engine: GameEngine
        self.game_state = False

    def new_game_from_data(self, game_data: dict):
        white_set = set(game_data["settings"]["line_whitelist"])
        black_set = set(game_data["settings"]["line_blacklist"])
        all_set = white_set - black_set
        if white_set - black_set != set([]):
            rl = game_data["remaining_lines"]
            rl = [rl[i] for i in all_set]
            game_data["remaining_lines"] = rl
        ge = self.game_engine = GameEngine(game_data)
        return ge

    def new_game(self, lines: List[Line] = [], settings = None):
        default_game_data = get_default_game_data()
        if settings != None:
            default_game_data["settings"] = settings
        #can we perhaps funcionize those parts of load and new game?
        default_game_data["remaining_lines"] = lines
        ge = self.new_game_from_data(default_game_data)
        self.game_state = ge.len_check()
        ge.shuffle_with_check()
        return ge


    def load_game_with_id(self, id: int):
        if len(self.game_data_list) <= id+2:    #Error here on this check for sure
            ge = self.new_game_from_data(self.game_data_list[id])
            self.game_state = ge.len_check()
            ge.shuffle_with_check()
            self.game_id = id
        else:
            return None
        
    def commit_game_auto(self):
        if self.game_id == None:
            self.commit_game_into_data_list()
        else:
            self.commit_game_on_id(self.game_id)

    def commit_game_on_id(self, id: int):
        self.game_data_list[id] = self.game_engine.extract_game_data()

    def commit_game_into_data_list(self):
        self.game_data_list.append(self.game_engine.extract_game_data())

    def save_game_data_list(self, file_path: str):
        self.commit_game_auto()
        save_game_data_list(self.game_data_list, file_path)

############################# Other

def get_score_percent(mistake_count: int, total_len: int, round_to: int = None) -> float:
    """
    Calculate the score as a percentage.
    
    Parameters:
    - mistake_count (int): The number of mistakes made.
    - total_len (int): The total number of items.
    - round_to (int, optional): The number of decimal places to round the result to. Defaults to None.
    
    Returns:
    - float: The score as a percentage.
    """
    if mistake_count < 0 or total_len < 0:
        raise ValueError("Invalid input values")
    
    if mistake_count == 0:
        return 100.0
    
    percent = 100 * (total_len - mistake_count) / total_len
    
    if round_to is not None:
        return round(percent, round_to)
    
    return percent

############################# Commands
    
if __name__ == "__main__":
    import argparse

    def parse_commands(input:str):
        parser = argparse.ArgumentParser(description='Game Commands')
        subparsers = parser.add_subparsers(dest='command')

        exit_parser = subparsers.add_parser('exit', help='Exit the game')

        game_parser = subparsers.add_parser('game', help='Start a new game')
        game_parser.add_argument('folder_path', type=str, help='', nargs='?', default='')
        game_parser.add_argument('-w', '--whitelist', type=str, nargs='+', help='Whitelisted files', default=[])
        game_parser.add_argument('-b', '--blacklist', type=str, nargs='+', help='Blacklisted files', default=[])


        load_parser = subparsers.add_parser('load', help='')
        load_parser.add_argument('id', type=str, help='', nargs='?', default='0')

        save_parser = subparsers.add_parser('save', help='')
        save_parser.add_argument('file_path', type=str, help='', nargs='?',
                                    default='game_history.json')
        
        history_parcer = subparsers.add_parser('history', help='')

        continue_parser = subparsers.add_parser('continue', help='')

        restart_parser = subparsers.add_parser('restart', help='')

        return parser.parse_args(shlex.split(input))
    
    def get_info():
        ret = ""
        sp = general_settings["show_score"]
        smc = general_settings["show_mistake_count"]
        if sp == True:
            adjust = gen.mistake_count if gen.settings["only_once"] == False else 0
            ret += f"""{gen.current_line}/{gen.original_lines_len+adjust}"""
        if sp and smc:
            ret += " - "
        if smc == True:
            ret += f"""{gen.mistake_count}/{
                get_score_percent(gen.mistake_count, gen.current_line, 2)}%"""
        
        ret = None if ret == "" else ret
        return ret

    restart_folder_path = ""
    restart_whitelist = []
    restart_blacklist = []

    gm = GameMaster(game_saves_path)
    def start_game(folder_path:str, whitelist:list, blacklist:list):
        if folder_path == "": raise ValueError("folder_path empty")
        restart_folder_path = folder_path
        gm.new_game(load_files_on_dir(folder_path,
                                      whitelist=restart_whitelist, 
                                      blacklist=restart_blacklist))
        gen = gm.game_engine
        return gen

    show_cmd = True
    game_is_running = True
    while game_is_running == True:
        if show_cmd == True or gm.game_state == False:
            # TODO: make it so info apears after enering cmd from game
            '''if gen.current_line > 0:
                print(f"Info: {get_info()}")
            '''
            user_input = input("Enter command: ")
            args = parse_commands(user_input)

            if args.command == 'game':
                restart_folder_path = args.folder_path
                restart_whitelist = args.whitelist
                restart_blacklist = args.blacklist
                system("cls")
                gen = start_game(restart_folder_path, restart_whitelist, restart_blacklist)
                gen = gm.game_engine
                show_cmd = False
                game_is_running = True
            if args.command == "history":
                pass
            if args.command == 'load':
                gm.load_game_with_id(int(args.id))
            if args.command == 'save':
                gm.save_game_data_list(args.file_path)
            if args.command == 'exit':
                game_is_running = False
            if args.command == 'restart':
                system("cls")
                gen = start_game(restart_folder_path, restart_whitelist, restart_blacklist)
                gen = gm.game_engine
                show_cmd = False
                game_is_running = True
            if args.command == 'continue':
                show_cmd = False
                system("cls")

        if gm.game_state == True and show_cmd == False:
            gi = get_info()
            if gi != None:
                print(f"Info: {gi}")

            # will need to put this in cmd
            from_side = SideChoice(gen.settings["from_side"])
            typing_mode = gen.settings["typing_mode"]
            split = general_settings["split"]

            side_answer = side_random_handle(from_side)
            line_current = gen.get_curent_line()
            line_current.side_answer = side_answer

            if side_answer == SideChoice.LEFT:
                side_show = SideChoice.RIGHT
            else: side_show = SideChoice.LEFT

            if typing_mode == False:
                print(line_current.side_as_string(side_show), end = "")
                input()
                print(line_current)
                inp = input()
                if ":cmd" in inp:
                    show_cmd = True
                    inp = inp.replace(":cmd", "")
                system("cls")

                gm.game_state = gen.progress_game_simple_mode(inp)

            else:   # typing mode == True
                print(gen.get_curent_line().side_as_string(side_show, False)
                      + general_settings["split"], end = "")
                inp = input()
                print(gen.get_curent_line())
                cmd_ = input()
                if cmd_ == ":cmd":
                    show_cmd = True
                system("cls")
                gm.game_state = gen.progress_game_typing_mode(inp)
            
############################# TODO:
#   Add learning "mode"
#
#   Add a reload function that does what restart but
#   loads from the file insted
#
#   add a multi line coment capability
#
#   show_position and show_score settings got mixed up, fix em and implement
#       the one that is not currenlty working yet
#
#   implement history
#       implement the simple graph
#
#   implement standard saving
#       game history and saves files apear to not create themselves
#       repair the saving mechanisms we broke when redoing some code
#       make the game savable no matter whats happening
#
#   re-clean the code when we finish doing all the features
#       make the logger easier to use
#       refine the full loging capbilities



### when we finish this remember to have a more comperhensive
#       plan of how things should work before doing
#       any coding