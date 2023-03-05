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
from geoproc.types import Number, SingleOrRGBList

cache_redis = redis.Redis(host="localhost", port=6379, db=0)


app = FastAPI()

TILE_HEADERS = {"Cache-Control": "max-age=31536000, immutable"}


def set_map(uuid: str, image_dict: dict[str, Any]) -> None:
    body = json.dumps(image_dict)
    cache_redis.set(f"maps:{uuid}", body)


def set_vis_params(uuid: str, vis_params: VisualizationParams) -> None:
    body = json.dumps(vis_params.dict())
    cache_redis.set(f"vis_params:{uuid}", body)


def get_map(uuid: str) -> Optional[str]:
    body = cache_redis.get(f"maps:{uuid}")
    if not body:
        return
    return body.decode()


def get_vis_params(uuid: str) -> Optional[VisualizationParams]:
    body = cache_redis.get(f"vis_params:{uuid}")
    if not body:
        return
    body_dict = json.loads(body)
    return VisualizationParams(**body_dict)


def expand_scale_range(
    min_max: tuple[SingleOrRGBList, SingleOrRGBList], count: int
) -> list[tuple[Number, Number]]:
    min_v, max_v = min_max
    min_v = [min_v] * count if not isinstance(min_v, tuple) else min_v
    max_v = [max_v] * count if not isinstance(max_v, tuple) else max_v
    return list(zip(min_v, max_v))[:count]


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
async def map(
    image_graph: dict[str, Any],
    vis_params: VisualizationParams,
    request: Request,
):
    new_uuid = str(uuid.uuid4())
    set_map(new_uuid, image_graph)
    set_vis_params(new_uuid, vis_params)

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

    vis_params = get_vis_params(id) or VisualizationParams()

    image = eval_image(image_json)

    # Workaround: Do not render tiles of a lower zoom level than the minimum
    # zoom level of Image, to avoid performance issue with WarpedVRT.
    # See issue https://github.com/cogeotiff/rio-tiler/issues/348
    if image.min_zoom and z < image.min_zoom:
        return Response(status_code=204, headers=TILE_HEADERS)

    try:
        with ImageReader(image) as src:
            img = src.tile(x, y, z)

            # Select bands
            if vis_params.bands:
                indexes = [img.band_names.index(b) for b in vis_params.bands]
                img.data = img.data[indexes]
            else:
                indexes = list(range(len(img.band_names)))

            # Rescale using min and max
            if vis_params.min is not None and vis_params.max is not None:
                in_range = expand_scale_range(
                    (vis_params.min, vis_params.max), len(indexes)
                )
                out_range = expand_scale_range((0, 255), len(indexes))
                img.rescale(in_range=in_range, out_range=out_range)

            if vis_params.opacity < 1.0:
                img.mask *= round((1 - vis_params.opacity) * 255)

    except TileOutsideBounds:
        return Response(status_code=204, headers=TILE_HEADERS)

    profile = img_profiles.get("png") or {}
    content = img.render(img_format="PNG", **profile)
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
