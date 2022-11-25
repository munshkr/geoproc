import math
import uuid
from typing import Tuple

import numpy as np
import rasterio
import rasterio.transform
import rasterio.windows
from fastapi import FastAPI
from pydantic import BaseModel
from pyproj import CRS, Transformer
from rio_cogeo.profiles import cog_profiles
from shapely.geometry import box
from shapely.ops import transform
from rasterio.enums import Resampling

# from .image import Image


def compute(
    image: dict,
    size: Tuple[int, int],
    bounds: Tuple[float, float, float, float],
    crs,
) -> np.array:
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
        return np.ones((1, w, h), dtype=np.min_scalar_type(value)) * value
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
                out_shape=(1, w, h),
                window=window,
                resampling=Resampling.average,
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


class ExportRequest(BaseModel):
    image: dict
    crs: str
    scale: int
    bounds: Tuple[float, float, float, float]
    path: str


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/map")
async def map():
    id = uuid.uuid4()
    return {
        "detail": {
            "id": id,
            "tiles_url": "http://localhost:8000/tiles/{id}/{{z}}/{{x}}/{{y}}.png",
        }
    }


@app.post("/export")
async def export(req: ExportRequest):
    bbox = box(*req.bounds)
    dst_crs = CRS.from_epsg(3857)

    # Reproject bounds to epsg:3857 to match scale units (meters)
    project = Transformer.from_crs(req.crs, dst_crs, always_xy=True).transform
    repr_box = transform(project, bbox)

    minx, miny, maxx, maxy = repr_box.bounds

    # Calculate affine transformation for scale and bounds
    affine = rasterio.transform.from_origin(
        west=minx,
        north=maxy,
        xsize=req.scale,
        ysize=req.scale,
    )
    # Create a window to calculate width and height in pixels
    window = rasterio.windows.from_bounds(
        left=minx,
        bottom=miny,
        right=maxx,
        top=maxy,
        transform=affine,
    )
    width, height = int(window.width), int(window.height)

    # Recalculate affine transformation for output file (in output CRS)
    west, south, east, north = bbox.bounds
    affine = rasterio.transform.from_bounds(west, south, east, north, width, height)

    # Compute image using that resolution
    img = compute(req.image, size=(width, height), bounds=bbox.bounds, crs=req.crs)

    # Prepare GeoTIFF profile (COG, CRS, transform)
    profile = cog_profiles["deflate"].copy()
    profile.update(
        dtype=img.dtype,
        count=img.shape[0],
        crs=req.crs,
        transform=affine,
        width=img.shape[1],
        height=img.shape[2],
    )

    # Write to file
    # TODO: Use windowed writing (based on block size)
    # TODO: If it's too large, retile into multiple COG files
    with rasterio.open(req.path, "w", **profile) as dst:
        dst.write(img)

    return {"result": "ok"}
