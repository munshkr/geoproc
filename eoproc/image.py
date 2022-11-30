from __future__ import annotations

from typing import Union

from .types import Bounds


class Image:
    def __init__(self, arg: Union[str, int, dict]):
        if isinstance(arg, str):
            self._graph = self._load(arg)
        elif isinstance(arg, int) or isinstance(arg, float):
            self._graph = self._constant(arg)
        else:
            self._graph = arg

    @property
    def graph(self) -> dict:
        return self._graph.copy()

    @classmethod
    def load(cls, url: str) -> Image:
        return cls(cls._load(url))

    @classmethod
    def constant(cls, value: Union[int, float]) -> Image:
        return cls(cls._constant(value))

    def get_map(self, vis_params: dict = {}) -> dict:
        from .client import APIClient

        client = APIClient()
        return client.get_map(self)

    def export(
        self,
        *,
        path: str,
        bounds: Bounds,
        scale: float = 1000,
        in_crs: str = "epsg:4326",
        crs: str = "epsg:4326",
    ):
        from .client import APIClient

        client = APIClient()
        return client.export(
            self,
            path=path,
            bounds=bounds,
            scale=scale,
            in_crs=in_crs,
            crs=crs,
        )

    def abs(self) -> Image:
        return Image({"name": "Image.abs", "args": [self._graph]})

    def __add__(self, other: Image) -> Image:
        return Image({"name": "Image.add", "args": [self._graph, other._graph]})

    def __sub__(self, other: Image) -> Image:
        return Image({"name": "Image.sub", "args": [self._graph, other._graph]})

    def __mul__(self, other: Image) -> Image:
        return Image({"name": "Image.mul", "args": [self._graph, other._graph]})

    def __truediv__(self, other: Image) -> Image:
        return Image({"name": "Image.truediv", "args": [self._graph, other._graph]})

    def __floordiv__(self, other: Image) -> Image:
        return Image({"name": "Image.floordiv", "args": [self._graph, other._graph]})

    @staticmethod
    def _load(url: str) -> dict:
        return {"name": "Image.load", "args": [url]}

    @staticmethod
    def _constant(value: Union[int, float]) -> dict:
        return {"name": "Image.constant", "args": [value]}
