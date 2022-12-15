from typing import Optional
from geoproc.types import SingleOrRGBList

from pydantic import BaseModel, validator


class VisualizationParams(BaseModel):
    bands: Optional[list[str]] = None
    min: Optional[SingleOrRGBList] = None
    max: Optional[SingleOrRGBList] = None
    gain: SingleOrRGBList = 1.0
    bias: SingleOrRGBList = 0.0
    gamma: SingleOrRGBList = 1.0
    opacity: float = 1.0

    @validator("bands")
    def bands_contains_one_or_three_names(cls, v):
        if len(v) != 1 and len(v) != 3:
            raise ValueError(f"must contain either 1 or 3 band names, but has {len(v)}")
        return [n.lower() for n in v]
