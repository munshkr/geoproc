class Image:
    def __init__(self, arg):
        if isinstance(arg, str):
            self._graph = self._load(arg)
        elif isinstance(arg, int) or isinstance(arg, float):
            self._graph = self._constant(arg)
        else:
            self._graph = arg

    @classmethod
    def load(cls, url):
        return cls(cls._load(url))

    @classmethod
    def constant(cls, value):
        return cls(cls._constant(value))

    @staticmethod
    def _load(url):
        return {"name": "load", "args": [url]}

    @staticmethod
    def _constant(value):
        return {"name": "constant", "args": [value]}
