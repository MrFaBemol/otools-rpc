
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



# --------------------------------------------
#               frozendict stuff
# --------------------------------------------
def remove(fn):
    def decorator(self, *args, **kwargs):
        raise NotImplementedError(f'{fn.__name__} not allowed on {self.__name__}')
    return decorator


class frozendict(dict):
    """ A class that allow you to lock dictionary so no option will be available other than get """

    @remove
    def __delitem__(self, *args) -> None:
        ...

    @remove
    def __setitem__(self, *args) -> None:
        ...

    @remove
    def clear(self, *args) -> None:
        ...

    @remove
    def pop(self, *args) -> None:
        ...

    @remove
    def popitem(self, *args) -> None:
        ...

    @remove
    def setdefault(self, *args) -> None:
        ...

    @remove
    def update(self, *args) -> None:
        ...

    def copy(self, **kw) -> "frozendict":
        return frozendict({
            **self,
            **kw,
        })

