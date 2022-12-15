from geoproc.client import APIClient
from geoproc.image import Image
import httpx


def test_api_client_default_url():
    client = APIClient()
    assert client.url == "http://localhost:8000"


def test_api_client_get_map(mocker):
    client = APIClient()
    img = Image(42)

    mocker.patch(
        "httpx.post",
        return_value=httpx.Response(
            status_code=200,
            json={
                "detail": {
                    "id": "some-id",
                    "tiles_url": f"http://localhost:8000/tiles/some-id/{{z}}/{{x}}/{{y}}.png",
                }
            },
        ),
    )

    client.get_map(img)

    httpx.post.assert_called_once_with(
        f"{client.url}/map", json={"image_graph": img.graph, "vis_params": None}
    )
