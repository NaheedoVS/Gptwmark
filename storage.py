import json
import os
from config import Config

class Storage:
    def __init__(self):
        self.file_path = Config.DB_FILE
        self._data = {}
        self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    self._data = json.load(f)
            except:
                self._data = {}

    def _save(self):
        with open(self.file_path, "w") as f:
            json.dump(self._data, f)

    def set_watermark(self, uid, text):
        uid = str(uid)
        if uid not in self._data:
            self._data[uid] = {}
        self._data[uid]["text"] = text
        self._save()

    def get_watermark(self, uid):
        return self._data.get(str(uid), {}).get("text", Config.DEFAULT_WATERMARK)

    def set_color(self, uid, color):
        uid = str(uid)
        if uid not in self._data:
            self._data[uid] = {}
        self._data[uid]["color"] = color
        self._save()

    def get_color(self, uid):
        return self._data.get(str(uid), {}).get("color", Config.DEFAULT_COLOR)

db = Storage()
