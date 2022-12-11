from typing import Optional
from geoproc.types import SingleOrRGBList

from pydantic import BaseModel


class VisualizationParams(BaseModel):
    bands: Optional[list[str]] = None
    min: Optional[SingleOrRGBList] = None
    max: Optional[SingleOrRGBList] = None
    gain: SingleOrRGBList = 1.0
    bias: SingleOrRGBList = 0.0
    gamma: SingleOrRGBList = 1.0
    opacity: float = 1.0
