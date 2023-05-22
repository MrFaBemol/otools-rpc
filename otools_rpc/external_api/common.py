
# --------------------------------------------
#                DECORATORS
# --------------------------------------------

def model(fn):
    fn._api = 'model'
    return fn

def log_request(fn):
    def wrapper(self, *args, **kwargs):
        # Todo: add more infos about performance.
        self.env.log_request(self, *args, **kwargs)
        return fn(self, *args, **kwargs)
    return wrapper

def assert_same_model(op=None):
    def decorator(fn):
        def wrapper(self, other):
            if self._name != other._name:
                raise ValueError(f"Mixed apples and oranges => cannot {op or fn.__name__} on {self} and {other}")
            return fn(self, other)
        return wrapper
    return decorator

def cache(op=None):
    def decorator(fn):
        def wrapper(self, *args, **kwargs):
            print(f"Cache {op or fn.__name__} on {self}")
            return fn(self, *args, **kwargs)
        return wrapper
    return decorator
