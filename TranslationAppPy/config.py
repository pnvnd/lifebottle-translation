import os
import json
from datetime import datetime


class GameConfig:
    def __init__(self, game=None):
        self.game = game
        self.folder_path = None
        self.iso_path = None
        self.last_folder_path = None
        self.last_time_loaded = None

    def to_dict(self):
        return {
            "game": self.game,
            "folderPath": self.folder_path,
            "isoPath": self.iso_path,
            "lastFolderPath": self.last_folder_path,
            "lastTimeLoaded": self.last_time_loaded.isoformat() if self.last_time_loaded else None,
        }

    @classmethod
    def from_dict(cls, d):
        gc = cls(d.get("game"))
        gc.folder_path = d.get("folderPath")
        gc.iso_path = d.get("isoPath")
        gc.last_folder_path = d.get("lastFolderPath")
        t = d.get("lastTimeLoaded")
        gc.last_time_loaded = datetime.fromisoformat(t) if t else None
        return gc


class Config:
    def __init__(self):
        self.games_config_list = []
        self._python_location = None
        self._python_lib = None

        app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
        config_dir = os.path.join(app_data, "TranslationApp")
        os.makedirs(config_dir, exist_ok=True)
        self._file_path = os.path.join(config_dir, "config.txt")

    @property
    def python_location(self):
        return self._python_location

    @python_location.setter
    def python_location(self, value):
        self._python_location = value
        self.save()

    @property
    def python_lib(self):
        return self._python_lib

    @python_lib.setter
    def python_lib(self, value):
        self._python_lib = value
        self.save()

    def load(self):
        if os.path.exists(self._file_path):
            try:
                with open(self._file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                games = data.get("gamesConfigList", [])
                self.games_config_list = [GameConfig.from_dict(g) for g in games] if games else [
                    GameConfig("TOR"), GameConfig("NDX")
                ]
                self._python_location = data.get("pythonLocation")
                self._python_lib = data.get("pythonLib")
            except Exception:
                if os.path.exists(self._file_path):
                    os.remove(self._file_path)
            self.save()

    def save(self):
        data = {
            "gamesConfigList": [g.to_dict() for g in self.games_config_list],
            "pythonLocation": self._python_location,
            "pythonLib": self._python_lib,
        }
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_game_config(self, game_name):
        for g in self.games_config_list:
            if g.game == game_name:
                return g
        return None

    def is_packing_visibility(self, game_name):
        gc = self.get_game_config(game_name)
        if gc:
            return bool(gc.folder_path and gc.iso_path and self._python_location and self._python_lib)
        return False

    def read_config_text(self):
        if os.path.exists(self._file_path):
            with open(self._file_path, "r", encoding="utf-8") as f:
                print(f.read())
