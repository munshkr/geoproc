import functools
import json
import uuid
from typing import Any, Optional

import redis
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from rasterio.crs import CRS
from rio_tiler.errors import TileOutsideBounds
from rio_tiler.profiles import img_profiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from geoproc.models import VisualizationParams
from geoproc.server.image import Image, ImageReader
from geoproc.server.image import eval_image as _eval_image
from geoproc.server.models import ExportRequest

cache_redis = redis.Redis(host="localhost", port=6379, db=0)


app = FastAPI()

TILE_HEADERS = {"Cache-Control": "max-age=31536000, immutable"}


def set_map(uuid: str, image_dict: dict[str, Any]) -> None:
    body = json.dumps(image_dict)
    cache_redis.set(f"maps:{uuid}", body)


def get_map(uuid: str) -> Optional[str]:
    body = cache_redis.get(f"maps:{uuid}")
    if not body:
        return
    return body.decode()


@functools.lru_cache(maxsize=64, typed=False)
def eval_image(image_json: str) -> Image:
    image_dict = json.loads(image_json)
    return _eval_image(image_dict)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        jsonable_encoder({"code": 400, "detail": str(exc.detail)}),
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        jsonable_encoder({"code": 400, "detail": str(exc)}), status_code=400
    )


@app.exception_handler(500)
async def internal_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        jsonable_encoder({"code": 500, "detail": "Internal Server Error"}),
        status_code=500,
    )


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/map")
async def map(image_json: dict, vis_params: VisualizationParams, request: Request):
    new_uuid = str(uuid.uuid4())
    set_map(new_uuid, image_json)

    return {
        "detail": {
            "id": new_uuid,
            "tiles_url": f"{request.base_url}tiles/{new_uuid}/{{z}}/{{x}}/{{y}}.png",
        }
    }


@app.post("/info")
async def info(image_json: dict, request: Request):
    image = _eval_image(image_json)
    info = image.info.copy()
    info["crs"] = str(info["crs"])
    info["dtype"] = str(info["dtype"])
    return {"detail": info}


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
def tile(id: str, z: int, x: int, y: int):
    """Handle tile requests."""
    image_json = get_map(id)
    if image_json is None:
        raise HTTPException(status_code=404, detail=f"Map id {id} not found")

    image = eval_image(image_json)
    try:
        with ImageReader(image) as src:
            data = src.tile(x, y, z)
    except TileOutsideBounds:
        return Response(status_code=204, headers=TILE_HEADERS)

    profile = img_profiles.get("png") or {}
    content = data.render(img_format="PNG", **profile)
    return Response(content, media_type="image/png", headers=TILE_HEADERS)


@app.post("/export")
async def export(req: ExportRequest):
    image = _eval_image(req.image)

    in_crs = req.in_crs and CRS.from_string(req.in_crs)
    crs = CRS.from_string(req.crs)

    try:
        image.export(
            path=req.path, bounds=req.bounds, scale=req.scale, in_crs=in_crs, crs=crs
        )
    except RuntimeError as err:
        return Response({"detail": str(err)}, status_code=400)

    return {"result": "ok"}


@app.get("/cache-info")
async def cache_info():
    return {
        "image_eval": eval_image.cache_info()._asdict(),
    }
