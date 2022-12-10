from __future__ import annotations

from typing import Optional, Union

from geoproc.types import Bounds


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
    def load(cls, url: str) -> "Image":
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
        path: str,
        *,
        bounds: Optional[Bounds] = None,
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

    def __abs__(self) -> Image:
        return Image({"name": "__abs__", "args": [self._graph]})

    def __add__(self, other: Union[int, float, Image]) -> Image:
        other = Image.constant(other) if not isinstance(other, Image) else other
        return Image({"name": "__add__", "args": [self._graph, other._graph]})

    def __sub__(self, other: Union[int, float, Image]) -> Image:
        other = Image.constant(other) if not isinstance(other, Image) else other
        return Image({"name": "__sub__", "args": [self._graph, other._graph]})

    def __mul__(self, other: Union[int, float, Image]) -> Image:
        other = Image.constant(other) if not isinstance(other, Image) else other
        return Image({"name": "__mul__", "args": [self._graph, other._graph]})

    def __truediv__(self, other: Union[int, float, Image]) -> Image:
        other = Image.constant(other) if not isinstance(other, Image) else other
        return Image({"name": "__truediv__", "args": [self._graph, other._graph]})

    def __floordiv__(self, other: Union[int, float, Image]) -> Image:
        other = Image.constant(other) if not isinstance(other, Image) else other
        return Image({"name": "__floordiv__", "args": [self._graph, other._graph]})

    @staticmethod
    def _load(url: str) -> dict:
        return {"name": "load", "args": [url]}

    @staticmethod
    def _constant(value: Union[int, float]) -> dict:
        return {"name": "constant", "args": [value]}
