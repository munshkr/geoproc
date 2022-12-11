from geoproc.server.image import eval_image, Image


def test_image_eval(mocker):
    mocker.patch("geoproc.server.image.Image.constant", return_value=Image.constant(42))
    image = eval_image({"args": [42], "name": "constant"})
    assert isinstance(image, Image)
    Image.constant.assert_called_once_with(42)
