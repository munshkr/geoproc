import uuid
from typing import Tuple

import rasterio
import rasterio.transform
import rasterio.windows
from fastapi import FastAPI
from pydantic import BaseModel
from pyproj import CRS, Transformer
from rio_cogeo.profiles import cog_profiles
from shapely.geometry import box
from shapely.ops import transform

from .image import compute


class ExportRequest(BaseModel):
    image: dict
    in_crs: str = "epsg:4326"
    crs: str = "epsg:4326"
    scale: int = 1000
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

    # Reproject bounds to a projected CRS. If the output CRS is already
    # projected, use it, otherwise use Web Mercator (epsg:3857).
    # This is because scale units are expected to be in meters.
    crs = CRS(req.crs)
    repr_crs = crs if crs.is_projected else CRS.from_epsg(3857)
    project = Transformer.from_crs(req.in_crs, repr_crs, always_xy=True).transform
    repr_bbox = transform(project, bbox)

    # Calculate affine transformation for scale and bounds
    minx, miny, maxx, maxy = repr_bbox.bounds
    affine = rasterio.transform.from_origin(
        west=minx,
        north=maxy,
        xsize=req.scale,
        ysize=req.scale,
    )
    # affine = rasterio.transform.from_bounds(
    #     west=minx, south=miny, east=maxx, north=maxy
    # )

    # Create a window to calculate width and height in pixels
    window = rasterio.windows.from_bounds(
        left=minx,
        bottom=miny,
        right=maxx,
        top=maxy,
        transform=affine,
    )
    width, height = round(window.width), round(window.height)

    # Compute image using that resolution
    img = compute(req.image, size=(width, height), bounds=bbox.bounds, crs=req.in_crs)

    # Recalculate affine transformation for output file (in output CRS)
    project = Transformer.from_crs(req.in_crs, req.crs, always_xy=True).transform
    out_bbox = transform(project, bbox)
    west, south, east, north = out_bbox.bounds
    out_transform = rasterio.transform.from_bounds(
        west, south, east, north, width, height
    )
    # out_transform = rasterio.transform.from_origin(
    #     west, north, xsize=req.scale, ysize=req.scale
    # )

    # Prepare GeoTIFF profile (COG, CRS, transform)
    profile = cog_profiles["deflate"].copy()
    profile.update(
        dtype=img.dtype,
        count=img.shape[0],
        height=img.shape[1],
        width=img.shape[2],
        crs=req.crs,
        transform=out_transform,
    )

    # Write to file
    # TODO: Use windowed writing (based on block size)
    # TODO: If it's too large, retile into multiple COG files
    with rasterio.open(req.path, "w", **profile) as dst:
        dst.write(img)

    return {"result": "ok"}
