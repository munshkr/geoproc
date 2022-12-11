from typing import Optional

from pydantic import BaseModel
from rio_tiler.constants import WGS84_CRS

from geoproc.server.types import BBox


class ExportRequest(BaseModel):
    image: dict
    in_crs: str = str(WGS84_CRS)
    crs: str = str(WGS84_CRS)
    scale: int = 1000
    bounds: Optional[BBox]
    path: str
