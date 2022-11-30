from typing import Tuple

import numpy as np
import numpy.typing as npt
import rasterio
import rasterio.transform
import rasterio.windows
from pyproj import Transformer
from rasterio.enums import Resampling
from shapely.geometry import box
from shapely.ops import transform


class Image:
    def __init__(self, arg):
        if isinstance(arg, str):
            self._kind = "file"
            self._path = arg
        elif isinstance(arg, int) or isinstance(arg, float):
            self._kind = "constant"
            self._value = arg

    def part(self, row, col, width, height):
        pass

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
