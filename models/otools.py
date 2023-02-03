from models.menu import OToolsMenu



class OTools:

    def __init__(self, menu_tree):
        self.menu = OToolsMenu(menu_tree)



    def run(self):
        self.menu.run()
