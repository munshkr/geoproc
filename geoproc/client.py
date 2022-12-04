import httpx

from geoproc.image import Image
from geoproc.types import Bounds


class APIClient:
    def __init__(self, url: str = "http://localhost:8000"):
        self.url = url

    def get_map(self, image: Image) -> dict[str, str]:
        r = httpx.post(f"{self.url}/map", json=image.graph)
        res = r.json()
        return res["detail"]

    def export(
        self,
        image: Image,
        *,
        scale: float,
        in_crs: str,
        crs: str,
        bounds: Bounds,
        path: str,
    ) -> dict:
        data = {
            "image": image.graph,
            "scale": scale,
            "in_crs": in_crs,
            "crs": crs,
            "bounds": bounds,
            "path": path,
        }
        r = httpx.post(f"{self.url}/export", json=data)
        return r.json()
