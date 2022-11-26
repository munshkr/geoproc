import httpx


class APIClient:
    def __init__(self, url="http://localhost:8000"):
        self.url = url

    def get_map(self, image):
        r = httpx.post(f"{self.url}/map", json=image.graph)
        res = r.json()
        return res["detail"]

    def export(self, image, *, scale, in_crs, crs, bounds, path):
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
