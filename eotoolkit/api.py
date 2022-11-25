import httpx


class APIClient:
    def __init__(self, url="http://localhost:8000"):
        self.url = url

    def get_map(self, image):
        r = httpx.post(f"{self.url}/map", data=image.graph)
        return r.json()
