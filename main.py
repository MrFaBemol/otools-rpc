from models.otools import OTools



def method_test(text="DEFAULT"):
    print(text)



_MENU_TREE = {
    'items': {
        'Sub 1': {
                'items': {
                    'Sub 1.1': {
                        'action': method_test,
                        'args': ["j'appelle dans sub 1"]
                    },
                    'Sub 1.2': {
                        'action': method_test,
                    }
                }
            },
            'Sub 2': {
                'items': {
                    'Sub 2.1': {
                        'action': method_test,
                    },
                    'Sub 2.2': {
                        'action': method_test,
                    }
                }
            },
            'Sub 3': {
                'action': method_test,
            }
    },

}


test = OTools(_MENU_TREE)
test.run()
