from typing import Union, Any
from simple_term_menu import TerminalMenu


BACK_MENU = "[b] Back"
QUIT_MENU = "[q] Quit"


class CLIMenu:



    def __init__(self, tree, obj = None):
        self._MENU_TREE = tree
        self._LOCATION_PATH = list()
        self._LOCATION_INFOS = {}
        self._RUN = False

        self._obj = obj
        if self._obj is not None:
            self._check_obj_methods(self._MENU_TREE)

        self._cd("")


    # --------------------------------------------
    #                   HELPERS
    # --------------------------------------------


    def get_location(self):
        return "/" + "/".join(self._LOCATION_PATH)

    def get_location_data(self, name: str = None, default=None) -> Any:
        return self._LOCATION_INFOS.get(name, default) if name else self._LOCATION_INFOS


    # --------------------------------------------
    #                   PRIVATE
    # --------------------------------------------

    def _get_action_callable(self, action):
        return getattr(self._obj, action, None) if isinstance(action, str) else action

    def _check_obj_methods(self, tree):
        if 'action' in tree:
            action = self._get_action_callable(tree['action'])
            assert callable(action), f"{self._obj} has no callable method named `{action or tree['action']}`"
        items = tree.get('items', dict())
        for sub_tree in items.values():
            self._check_obj_methods(sub_tree)



    def _get_location_menu_items(self) -> list[str]:
        """
        Create & return a list of string with menu items from the location.
        Add "Back" or "Quit" depending on the latest.
        :return: a list[str] with menu item labels
        """
        menu_items = self.get_location_data('labels').copy()
        menu_items.extend([None, BACK_MENU if self._LOCATION_PATH else QUIT_MENU])
        return menu_items

    def _cd(self, path: Union[list, str] = None) -> None:
        """
        Change directory in a relative way
        :param path: a string (or list) containing the to move to
        :return: None
        """
        # Go back to root menu if nothing is passed
        if path is None:
            self._LOCATION_PATH = list()
            path = list()

        # End of path > run from beginning to location & return infos
        if not path:
            target = self._MENU_TREE
            try:
                for next_item in self._LOCATION_PATH:
                    target = target.get('items').get(next_item)
            except TypeError:
                target = self._MENU_TREE

            if not target:
                return self._cd()

            self._LOCATION_INFOS = {
                **target,
                'labels': list(target.get('items', dict()).keys())
            }
            return

        if isinstance(path, str):
            path = path[1:] if path[0] == "/" else path
            path = path[:-1] if path[-1] == "/" else path
            path = path.split("/")

        next_menu = path[0]
        if next_menu == "..":
            self._LOCATION_PATH = self._LOCATION_PATH[:-1]
        else:
            self._LOCATION_PATH.append(next_menu)
        self._cd(path[1:])


    def _process(self, choice: str) -> None:
        """
        Process a _cd to location + an optional action if defined
        :param choice: generally a menu name, but can be a special command (back/quit)
        :return: None
        """
        if choice == BACK_MENU:
            return self._cd("../")
        elif choice == QUIT_MENU:
            self._RUN = False
            return

        # Move to selected path (might be a command only menu item)
        self._cd(choice)
        # Execute an action if defined
        if action := self.get_location_data('action'):
            fn = self._get_action_callable(action)
            fn(*self.get_location_data('args', []))
        # If there is no sub menu for this location, go back.
        if not self.get_location_data('items'):
            self._cd("../")




    # --------------------------------------------
    #                   PUBLIC
    # --------------------------------------------


    def run(self):
        self._RUN = True
        while self._RUN:
            menu_items = self._get_location_menu_items()
            menu = TerminalMenu(menu_items, title=self.get_location(), clear_screen=False)
            choice = menu.show()


            if choice is not None:
                self._process(menu_items[choice])

