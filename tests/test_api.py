from eotoolkit.api import APIClient
from eotoolkit.image import Image
import httpx


def test_api_client_default_url():
    client = APIClient()
    assert client.url == "http://localhost:8000"


def test_api_client_get_map(mocker):
    client = APIClient()
    img = Image(42)

    mocker.patch("httpx.post")

    client.get_map(img)

    httpx.post.assert_called_once_with(f"{client.url}/map", data=img.graph)
