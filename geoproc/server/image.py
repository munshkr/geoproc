from __future__ import annotations

from typing import Callable, Iterable, Optional, Tuple, Union, Any

import attr
import numpy as np
import numpy.typing as npt
import rasterio
import rasterio.transform
import rasterio.windows
from morecantile.commons import Tile
from morecantile.models import TileMatrixSet
from rasterio.coords import BoundingBox
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.windows import Window
from rio_tiler import reader
from rio_tiler.constants import WEB_MERCATOR_TMS, WGS84_CRS
from rio_tiler.errors import TileOutsideBounds
from rio_tiler.io.base import BaseReader
from rio_tiler.models import BandStatistics, ImageData, Info, PointData
from rio_tiler.profiles import img_profiles
from rio_tiler.types import BBox

from geoproc.types import Bounds

MAX_MEMORY = 2**28


@attr.s
class ImageReader(BaseReader):
    input: Image = attr.ib(default=None)
    bounds: Optional[BBox] = attr.ib(default=None, init=False)
    tms: TileMatrixSet = attr.ib(default=WEB_MERCATOR_TMS)

    def __init__(self, input: Image):
        self.input = input

    def __attrs_post_init__(self):
        self.bounds = self.input.bounds
        self.crs = self.input.crs

    def info(self) -> Info:
        ...

    def statistics(self) -> dict[str, BandStatistics]:
        ...

    def tile(
        self, tile_x: int, tile_y: int, tile_z: int, tilesize: int = 256
    ) -> ImageData:
        if not self.tile_exists(tile_x, tile_y, tile_z):
            raise TileOutsideBounds(
                f"Tile {tile_z}/{tile_x}/{tile_y} is outside {self.input} bounds"
            )

        tile_bounds = self.tms.xy_bounds(Tile(x=tile_x, y=tile_y, z=tile_z))

        return self.part(
            tile_bounds,
            height=tilesize,
            width=tilesize,
            dst_crs=self.tms.rasterio_crs,
        )

    def part(
        self,
        bbox: BBox,
        height: int,
        width: int,
        dst_crs: Optional[CRS] = None,
    ) -> ImageData:
        data = self.input.part(bbox, dst_crs, height, width)
        return ImageData(
            data=data,
            bounds=BoundingBox(*bbox),
            crs=dst_crs,
            band_names=["DATA"],
        )  # type: ignore

    def point(self, lon: float, lat: float) -> PointData:
        ...

    def preview(self) -> ImageData:
        ...

    def feature(self, shape: dict) -> ImageData:
        ...

    def read(self, window: Window) -> npt.NDArray:
        ...


class ImageWriter:
    def __init__(self, image: Image, path: str):
        self.path = path
        self.image = image

    def __enter__(self) -> ImageWriter:
        return self

    def __exit__(self, type, value, traceback) -> None:
        pass

    def write(self, array: npt.NDArray, *, window: Optional[Window] = None) -> None:
        pass

    def build_windows(
        self,
        *,
        in_crs: str,
        crs: str,
        scale: int,
        bounds: Bounds,
        max_memory: int = 2**28,
    ) -> Iterable[Window]:
        yield Window()


PartCallable = Callable[[BBox, CRS, int, int], npt.NDArray]


def read_bounds_and_crs(path: str) -> Tuple[BBox, CRS]:
    with rasterio.open(path) as src:
        return (src.bounds, src.crs)


def bounds_union(a: Optional[BBox], b: Optional[BBox]) -> Optional[BBox]:
    if a is None and b is None:
        return
    if a is None:
        return b
    if b is None:
        return a
    minx = min(a[0], b[0])
    miny = min(a[1], b[1])
    maxx = max(a[2], b[2])
    maxy = max(a[3], b[3])
    return (minx, miny, maxx, maxy)


class Image:
    def __init__(
        self,
        part: PartCallable,
        *,
        bounds: Optional[BBox] = None,
        crs: CRS = WGS84_CRS,
    ):
        self.part = part
        self.bounds = bounds
        self.crs = crs

    @classmethod
    def load(cls, path: str) -> Image:
        def _load_part(
            bounds: BBox, dst_crs: CRS, height: int, width: int
        ) -> npt.NDArray:
            with rasterio.open(path) as src:
                image = reader.part(
                    src,
                    bounds=bounds,
                    height=height,
                    width=width,
                    dst_crs=dst_crs,
                )
                return image.data

        bounds, crs = read_bounds_and_crs(path)
        return cls(_load_part, bounds=bounds, crs=crs)

    @classmethod
    def constant(cls, value: Union[float, int]) -> Image:
        def _constant_part(
            bounds: BBox, dst_crs: CRS, height: int, width: int
        ) -> npt.NDArray:
            return np.ones((1, height, width), dtype=np.min_scalar_type(value)) * value

        return cls(_constant_part)

    def abs(self) -> Image:
        return Image(
            lambda *args: np.abs(self.part(*args)), bounds=self.bounds, crs=self.crs
        )

    def __add__(self, other: Union[Image, int, float]) -> Image:
        return self._operator("__add__", other)

    def __sub__(self, other: Union[Image, int, float]) -> Image:
        return self._operator("__sub__", other)

    def __mul__(self, other: Union[Image, int, float]) -> Image:
        return self._operator("__mul__", other)

    def __truediv__(self, other: Union[Image, int, float]) -> Image:
        return self._operator("__truediv__", other)

    def __floordiv__(self, other: Union[Image, int, float]) -> Image:
        return self._operator("__floordiv__", other)

    def _operator(self, method_name, other: Union[Image, int, float]) -> Image:
        other_img = other if isinstance(other, Image) else Image.constant(other)
        return Image(
            lambda *args: getattr(self.part(*args), method_name)(other_img.part(*args)),
            bounds=bounds_union(self.bounds, other_img.bounds),
            crs=self.crs,
        )


def image_eval(
    image_attr: dict[str, Any],
) -> Image:
    method: Callable[..., Image] = getattr(Image, image_attr["name"])
    args = [
        image_eval(arg) if isinstance(arg, dict) else arg for arg in image_attr["args"]
    ]
    return method(*args)


def export(
    image: Image,
    *,
    path: str,
    in_crs: str = "epsg:4326",
    crs: str = "epsg:4326",
    scale: int = 1000,
    bounds: Bounds,
) -> None:
    with ImageReader(image) as src:
        with ImageWriter(image, path) as dst:
            for window in dst.build_windows(
                in_crs=in_crs,
                crs=crs,
                scale=scale,
                bounds=bounds,
                max_memory=MAX_MEMORY,
            ):
                img = src.read(window)
                dst.write(img, window=window)


def tile(image: Image, *, x: int, y: int, z: int):
    with ImageReader(image) as src:
        img = src.tile(x, y, z)
    return img.render(img_format="PNG", **img_profiles.get("png"))  # type: ignore
