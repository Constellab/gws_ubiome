
import json
import os

__cdir__ = os.path.dirname(os.path.realpath(__file__))
CURRENT_SETTINGS_PATH = os.path.join(__cdir__, "../../settings.json")


class Settings:
    """
    Settings class
    """

    @classmethod
    def read(cls) -> dict:
        with open(CURRENT_SETTINGS_PATH, "r", encoding="utf-8") as fp:
            return json.load(fp)
