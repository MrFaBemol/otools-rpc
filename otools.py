from models.cli_menu import CLIMenu
from datetime import datetime

import os
import uuid
import pickle
import json

import logging
logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)



# ------------------------------- CONFIG
SAVE_FILE = ".otsave"
DATE_FORMAT = "%d %B %Y"
TIME_FORMAT = "%H:%M:%S"
REAL_PATH = os.path.realpath(os.path.dirname(__file__))


def get_session():
    if os.path.isfile(f"{REAL_PATH}/{SAVE_FILE}"):
        with open(f"{REAL_PATH}/{SAVE_FILE}", "rb") as f:
            ot = pickle.load(f)
    else:
        ot = OTools()
    ot.start()
    return ot



class OTools:


    def __init__(self):
        self.menu = False
        self.uuid = uuid.uuid4()
        self.create_date = datetime.now()
        self.write_date = datetime.now()
        self.mdr = True

    def __str__(self):
        return f"oTools<{self.uuid}>"

    def start(self):
        self._mount_menu()
        infos = {
            'UUID': self.uuid,
            'Creation': self.create_date.strftime(f"{DATE_FORMAT} at {TIME_FORMAT}"),
            'Last save': self.write_date.strftime(f"{DATE_FORMAT} at {TIME_FORMAT}"),
        }
        infos_str = "\n".join([f"--- {k}: {v}" for k, v in infos.items()])
        _logger.info(f"Loading session for {self} ...\n{infos_str}")

    def save(self):
        _logger.info(f"Saving session for {self} ...")
        with open(f"{REAL_PATH}/{SAVE_FILE}", "w+b") as f:
            self.write_date = datetime.now()
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)

    def _mount_menu(self):
        print("mounting menu")
        with open(f"{REAL_PATH}/data/menu.json") as f:
            menu_tree = json.load(f)
            self.menu = CLIMenu(menu_tree, self)

    def faux(self):
        self.mdr = False
    def vrai(self):
        self.mdr = True
    def test(self):
        print("tesst")

    def method_test(self, text="DEFAULT"):
        print(text)


    def run(self):
        self.menu.run()







