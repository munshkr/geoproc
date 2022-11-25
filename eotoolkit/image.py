from .api import APIClient


class Image:
    def __init__(self, arg):
        if isinstance(arg, str):
            self._graph = self._load(arg)
        elif isinstance(arg, int) or isinstance(arg, float):
            self._graph = self._constant(arg)
        else:
            self._graph = arg

    @property
    def graph(self):
        return self._graph.copy()

    @classmethod
    def load(cls, url):
        return cls(cls._load(url))

    @classmethod
    def constant(cls, value):
        return cls(cls._constant(value))

    def get_map(self):
        api = APIClient()
        self._map = api.get_map(self._graph)

    def abs(self):
        return Image({"name": "Image.abs", "args": [self._graph]})

    def __add__(self, other):
        return Image({"name": "Image.add", "args": [self._graph, other._graph]})

    def __sub__(self, other):
        return Image({"name": "Image.sub", "args": [self._graph, other._graph]})

    def __mul__(self, other):
        return Image({"name": "Image.mul", "args": [self._graph, other._graph]})

    def __truediv__(self, other):
        return Image({"name": "Image.truediv", "args": [self._graph, other._graph]})

    def __floordiv__(self, other):
        return Image({"name": "Image.floordiv", "args": [self._graph, other._graph]})

    @staticmethod
    def _load(url):
        return {"name": "Image.load", "args": [url]}

    @staticmethod
    def _constant(value):
        return {"name": "Image.constant", "args": [value]}
