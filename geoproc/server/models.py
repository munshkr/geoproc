from pydantic import BaseModel
from typing import Tuple


class ExportRequest(BaseModel):
    image: dict
    in_crs: str = "epsg:4326"
    crs: str = "epsg:4326"
    scale: int = 1000
    bounds: Tuple[float, float, float, float]
    path: str
