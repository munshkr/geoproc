import httpx


class APIClient:
    def __init__(self, url="http://localhost:8000"):
        self.url = url

    def get_map(self, image):
        r = httpx.post(f"{self.url}/map", json=image.graph)
        return r.json()

    def export(self, image, *, scale, crs, bounds, path):
        data = {
            "image": image.graph,
            "scale": scale,
            "crs": crs,
            "bounds": bounds,
            "path": path,
        }
        r = httpx.post(f"{self.url}/export", json=data)
        return r.json()
