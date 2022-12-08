import uuid

import rasterio
import rasterio.transform
import rasterio.windows
from fastapi import FastAPI, HTTPException, Request, Response
from pyproj import Transformer
from rasterio.crs import CRS
from rio_cogeo.profiles import cog_profiles
from rio_tiler.errors import TileOutsideBounds
from rio_tiler.io.rasterio import Reader
from rio_tiler.profiles import img_profiles
from shapely.geometry import box
from rio_tiler.types import BBox
from shapely.ops import transform

from geoproc.server.image import Image, image_eval, tile as _tile, export as _export
from geoproc.server.models import ExportRequest

# FIXME: This should be stored in Redis or something
maps: dict[str, Image] = {}


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/map")
async def map(json: dict, request: Request):
    id = uuid.uuid4()
    image = image_eval(json)
    maps[str(id)] = image

    return {
        "detail": {
            "id": id,
            "tiles_url": f"{request.base_url}tiles/{id}/{{z}}/{{x}}/{{y}}.png",
        }
    }


@app.get(
    r"/tiles/{id}/{z}/{x}/{y}.png",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Return an image.",
        }
    },
    description="Read COG and return a tile",
)
def tile(
    id: str,
    z: int,
    x: int,
    y: int,
):
    """Handle tile requests."""
    image = maps.get(id)
    if not image:
        raise HTTPException(status_code=404, detail=f"Map id {id} not found")

    content = _tile(image, x=x, y=y, z=z)
    return Response(content, media_type="image/png")

    # if image["name"] != "Image.load":
    #     raise HTTPException(
    #         status_code=400, detail=f"Only Image.load is implemented for now"
    #     )

    # path: str = image["args"][0]
    # with Reader(input=path) as cog:  # type: ignore
    #     try:
    #         img = cog.tile(x, y, z)
    #     except TileOutsideBounds:
    #         return Response(status_code=204)
    # content = img.render(img_format="PNG", **img_profiles.get("png"))  # type: ignore
    # return Response(content, media_type="image/png")


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

    image = image_eval(req.image)

    # Compute image using that resolution
    data = image.part(req.bounds, req.in_crs, width, height)

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
        dtype=data.dtype,
        count=data.shape[0],
        height=data.shape[1],
        width=data.shape[2],
        crs=req.crs,
        transform=out_transform,
    )

    # Write to file
    # TODO: Use windowed writing (based on block size)
    # TODO: If it's too large, retile into multiple COG files
    with rasterio.open(req.path, "w", **profile) as dst:
        dst.write(data)

    return {"result": "ok"}
