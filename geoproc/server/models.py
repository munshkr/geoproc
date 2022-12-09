from typing import Optional

from pydantic import BaseModel
from rasterio.crs import CRS
from rio_tiler.constants import WGS84_CRS
from rio_tiler.types import BBox


class ExportRequest(BaseModel):
    image: dict
    in_crs: str = str(WGS84_CRS)
    crs: str = str(WGS84_CRS)
    scale: int = 1000
    bounds: Optional[BBox]
    path: str
