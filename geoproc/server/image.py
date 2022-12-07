from __future__ import annotations

from typing import Iterable, Optional, Tuple, Union

import attr
import numpy as np
import numpy.typing as npt
import rasterio
import rasterio.transform
import rasterio.windows
from morecantile import Tile
from pyproj import Transformer
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.windows import Window
from rio_tiler.constants import WGS84_CRS
from rio_tiler.errors import TileOutsideBounds
from rio_tiler.io.base import BaseReader
from rio_tiler.models import BandStatistics, ImageData, Info, PointData
from rio_tiler.types import BBox
from shapely.geometry import box
from shapely.ops import transform

from geoproc.types import Bounds

MAX_MEMORY = 2**28


@attr.s
class ImageReader(BaseReader):
    input: Image = attr.ib()
    geographic_crs: CRS = attr.ib(default=WGS84_CRS)

    def __init__(self, image: Image):
        self.input = image

    def __attrs_post_init__(self):
        self.bounds = self.input.bounds
        self.crs = self.input.crs

    def info(self) -> Info:
        pass

    def statistics(self) -> dict[str, BandStatistics]:
        pass

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
            dst_crs=self.tms.rasterio_crs,
            height=tilesize,
            width=tilesize,
        )

    def part(
        self,
        bbox: BBox,
        dst_crs: Optional[CRS] = None,
        height: Optional[int] = None,
        width: Optional[int] = None,
    ) -> ImageData:
        pass

    def point(self, lon: float, lat: float) -> PointData:
        pass

    def preview(self) -> ImageData:
        pass

    def feature(self, shape: dict) -> ImageData:
        pass

    def read(self, window: Window) -> npt.NDArray:
        return np.array([])


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


class Image:
    def __init__(self, arg: Union[str, int, float]):
        if isinstance(arg, str):
            self._kind = "file"
            self._path = arg
        elif isinstance(arg, int) or isinstance(arg, float):
            self._kind = "constant"
            self._value = arg

    @property
    def bounds(self) -> BBox:
        # TODO
        return (0, 0, 0, 0)

    @property
    def crs(self) -> CRS:
        # TODO
        return WGS84_CRS

    @classmethod
    def load(cls, path):
        return cls(path)

    @classmethod
    def constant(cls, value):
        return cls(value)


def compute(
    image: dict,
    size: Tuple[int, int],
    bounds: Tuple[float, float, float, float],
    crs,
) -> npt.NDArray:
    w, h = size

    fname = image["name"]
    args = [
        compute(arg, size=size, bounds=bounds, crs=crs)
        if isinstance(arg, dict)
        else arg
        for arg in image["args"]
    ]

    if fname == "Image.constant":
        value = args[0]
        return np.ones((1, h, w), dtype=np.min_scalar_type(value)) * value
    elif fname == "Image.load":
        path = args[0]
        with rasterio.open(path) as src:
            bbox = box(*bounds)
            project = Transformer.from_crs(crs, src.crs, always_xy=True).transform
            repr_bbox = transform(project, bbox)
            left, bottom, right, top = repr_bbox.bounds

            window = rasterio.windows.from_bounds(
                left,
                bottom,
                right,
                top,
                transform=src.transform,
            )
            return src.read(
                out_shape=(1, h, w),
                window=window,
                resampling=Resampling.nearest,
                indexes=[1],
            )
    elif fname == "Image.abs":
        return np.abs(args[0])
    elif fname == "Image.add":
        return args[0] + args[1]
    elif fname == "Image.sub":
        return args[0] - args[1]
    elif fname == "Image.mul":
        return args[0] * args[1]
    elif fname == "Image.truediv":
        return args[0] / args[1]
    elif fname == "Image.floordiv":
        return args[0] // args[1]

    raise NotImplementedError(
        f"unknown method {image['name']} with args {image['args']}"
    )


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
