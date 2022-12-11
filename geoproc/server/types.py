from typing import Callable

from rio_tiler.constants import CRS
from rio_tiler.models import ImageData
from rio_tiler.types import BBox

PartCallable = Callable[[BBox, CRS, int, int], ImageData]
