from __future__ import annotations

from copy import copy
from typing import Any, Callable, Iterable, Optional, Tuple, Union

import attr
import numpy as np
import numpy.typing as npt
import rasterio
import rasterio.transform
import rasterio.windows
from morecantile.commons import Tile
from morecantile.models import TileMatrixSet
from rasterio.coords import BoundingBox
from rasterio.enums import Resampling
from rasterio.warp import transform_bounds
from rasterio.windows import Window
from rio_tiler import reader
from rio_tiler.constants import CRS, WEB_MERCATOR_TMS, WGS84_CRS
from rio_tiler.errors import TileOutsideBounds
from rio_tiler.io.base import BaseReader
from rio_tiler.models import BandStatistics, ImageData, Info, PointData
from rio_tiler.profiles import img_profiles
from rio_tiler.types import BBox

from geoproc.types import Bounds

MAX_MEMORY = 2**28
WINDOW_SIZE = 2**12


@attr.s
class ImageReader(BaseReader):
    input: Image = attr.ib(default=None)
    bounds: Optional[BBox] = attr.ib(default=None, init=False)
    tms: TileMatrixSet = attr.ib(default=WEB_MERCATOR_TMS)

    dtype: npt.DTypeLike = attr.ib(init=False)
    count: int = attr.ib(default=1, init=False)

    def __init__(self, input: Image):
        self.input = input

    def __attrs_post_init__(self):
        self.bounds = self.input.bounds
        self.crs = self.input.crs
        self.dtype = self.input.dtype
        self.count = self.input.count

    def window_and_bounds(
        self,
        *,
        bounds: BBox,
        bounds_crs: CRS,
        crs: CRS,
        scale: int,
        window_size: int = WINDOW_SIZE,
    ) -> Iterable[Tuple[Window, BBox]]:
        proj_crs = crs if crs.is_projected else CRS.from_epsg(3857)
        proj_bounds = transform_bounds(bounds_crs, proj_crs, *bounds, densify_pts=21)
        proj_transform = rasterio.transform.from_origin(
            west=proj_bounds[0],
            north=proj_bounds[3],
            xsize=scale,
            ysize=scale,
        )
        window = rasterio.windows.from_bounds(
            *proj_bounds,
            transform=proj_transform,
        )
        height, width = round(window.height), round(window.width)

        out_bounds = transform_bounds(bounds_crs, crs, *bounds, densify_pts=21)
        out_transform = rasterio.transform.from_bounds(
            *out_bounds, width=width, height=height
        )

        h = w = window_size
        for i in range(0, height, h):
            for j in range(0, width, w):
                real_h = min(h, abs(height - i))
                real_w = min(w, abs(width - j))
                win = Window(j, i, real_w, real_h)
                win_bounds = rasterio.windows.bounds(
                    window=win, transform=out_transform
                )
                yield win, win_bounds

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
            bounds_crs=None,
        )

    def part(
        self,
        bounds: BBox,
        height: int,
        width: int,
        dst_crs: Optional[CRS] = None,
        bounds_crs: Optional[CRS] = WGS84_CRS,
    ) -> ImageData:
        if not dst_crs:
            dst_crs = bounds_crs
        if bounds_crs and bounds_crs != dst_crs:
            bounds = transform_bounds(bounds_crs, dst_crs, *bounds, densify_pts=21)
        return self.input.part(bounds, dst_crs, height, width)

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


PartCallable = Callable[[BBox, CRS, int, int], ImageData]


def read_raster_info(path: str) -> Tuple[BBox, CRS, npt.DTypeLike, int]:
    with rasterio.open(path) as src:
        return (src.bounds, src.crs, src.profile["dtype"], src.count)


def bounds_union(
    a: Optional[BBox], b: Optional[BBox], a_crs: CRS, b_crs: CRS
) -> Tuple[Optional[BBox], CRS]:
    if a is None and b is None:
        return None, a_crs
    if a is None:
        return b, b_crs
    if b is None:
        return a, a_crs
    if b_crs != a_crs:
        b = transform_bounds(b_crs, a_crs, *b)
    minx = min(a[0], b[0])
    miny = min(a[1], b[1])
    maxx = max(a[2], b[2])
    maxy = max(a[3], b[3])
    return (minx, miny, maxx, maxy), a_crs


class Image:
    def __init__(
        self,
        part: PartCallable,
        *,
        bounds: Optional[BBox] = None,
        crs: CRS = WGS84_CRS,
        dtype: npt.DTypeLike,
        count: int = 1,
    ):
        self.part = part
        self.bounds = bounds
        self.crs = crs
        self.dtype = dtype
        self.count = count

    @classmethod
    def load(cls, path: str) -> Image:
        def _load_part(
            bounds: BBox, dst_crs: CRS, height: int, width: int
        ) -> ImageData:
            with rasterio.open(path) as src:
                return reader.part(
                    src,
                    bounds=bounds,
                    height=height,
                    width=width,
                    dst_crs=dst_crs,
                )

        bounds, crs, dtype, count = read_raster_info(path)
        return cls(_load_part, bounds=bounds, crs=crs, dtype=dtype, count=count)

    @classmethod
    def constant(cls, value: Union[float, int]) -> Image:
        dtype = np.min_scalar_type(value)

        def _constant_part(
            bounds: BBox, dst_crs: CRS, height: int, width: int
        ) -> ImageData:
            ones = np.ones((1, height, width), dtype=dtype)
            data = ones * value
            mask = ones * 255
            return ImageData(
                data=data,
                mask=mask,
                bounds=BoundingBox(*bounds),
                crs=dst_crs,
                band_names=["CONSTANT"],
            )

        return cls(_constant_part, dtype=dtype, count=1)

    def abs(self) -> Image:
        def _part(*args):
            img = self.part(*args)
            img.data = np.abs(img.data)
            return img

        return Image(
            lambda *args: _part(*args),
            bounds=self.bounds,
            crs=self.crs,
            dtype=self.dtype,
            count=self.count,
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

    def __lt__(self, other: Union[Image, int, float]) -> Image:
        return self._operator("__lt__", other)

    def __le__(self, other: Union[Image, int, float]) -> Image:
        return self._operator("__le__", other)

    def __eq__(self, other: Union[Image, int, float]) -> Image:
        return self._operator("__eq__", other)

    def __ne__(self, other: Union[Image, int, float]) -> Image:
        return self._operator("__ne__", other)

    def __gt__(self, other: Union[Image, int, float]) -> Image:
        return self._operator("__gt__", other)

    def __ge__(self, other: Union[Image, int, float]) -> Image:
        return self._operator("__ge__", other)

    def _operator(self, method_name, other: Union[Image, int, float]) -> Image:
        other_img = other if isinstance(other, Image) else Image.constant(other)

        def _part(other: Image, *args) -> ImageData:
            img_data = self.part(*args)
            other_img_data = other.part(*args)
            new_img_data = copy(img_data)
            new_img_data.data = getattr(img_data.data, method_name)(other_img_data.data)
            new_img_data.mask = np.maximum(img_data.mask, other_img_data.mask)
            return new_img_data

        new_bounds, new_crs = bounds_union(
            self.bounds, other_img.bounds, self.crs, other_img.crs
        )

        return Image(
            lambda *args: _part(other_img, *args),
            bounds=new_bounds,
            crs=new_crs,
            dtype=np.float64,
            count=self.count,
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
