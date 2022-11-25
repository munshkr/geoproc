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

# from .image import Image


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

    # Get ceiling from width and height
    width, height = math.ceil(window.width), math.ceil(window.height)

    # Compute image using that resolution
    # TODO: Compute image based on image computation graph
    img = np.ones((1, width, height), dtype=np.uint8)

    # Recalculate affine transformation for output file (in output CRS)
    west, south, east, north = bbox.bounds
    affine = rasterio.transform.from_bounds(west, south, east, north, width, height)

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
