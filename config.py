import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    DEFAULT_WATERMARK = "@Pglinsan"
    DEFAULT_COLOR = "White"

    DB_FILE = "user_data.json"

    FONT_SIZE = 36
    OPACITY = 200
    MARGIN_X = 20
    MARGIN_Y = 20

    COLORS = {
        "White": (255,255,255),
        "Black": (0,0,0),
        "Red": (255,0,0),
        "Blue": (0,0,255),
        "Green": (0,255,0),
        "Yellow": (255,255,0),
        "Orange": (255,165,0),
        "Purple": (128,0,128),
    }
  
