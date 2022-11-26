from eoproc.image import Image


def test_image_constant():
    img = Image.constant(1)
    assert img.graph == {"args": [1], "name": "Image.constant"}


def test_image_load():
    img = Image.load("tci.tif")
    assert img.graph == {"args": ["tci.tif"], "name": "Image.load"}


def test_image_init_contant():
    img = Image(1)
    assert img.graph == {"args": [1], "name": "Image.constant"}


def test_image_init_load():
    img = Image("tci.tif")
    assert img.graph == {"args": ["tci.tif"], "name": "Image.load"}


def test_image_abs():
    img = Image(-4)
    assert img.abs().graph == {
        "name": "Image.abs",
        "args": [{"name": "Image.constant", "args": [-4]}],
    }


def test_image_add():
    assert (Image(2) + Image(3)).graph == {
        "name": "Image.add",
        "args": [
            {"name": "Image.constant", "args": [2]},
            {"name": "Image.constant", "args": [3]},
        ],
    }


def test_image_sub():
    assert (Image(4) - Image(3)).graph == {
        "name": "Image.sub",
        "args": [
            {"name": "Image.constant", "args": [4]},
            {"name": "Image.constant", "args": [3]},
        ],
    }


def test_image_mult():
    assert (Image(2) * Image(2)).graph == {
        "name": "Image.mul",
        "args": [
            {"name": "Image.constant", "args": [2]},
            {"name": "Image.constant", "args": [2]},
        ],
    }


def test_image_truediv():
    assert (Image(10) / Image(2)).graph == {
        "name": "Image.truediv",
        "args": [
            {"name": "Image.constant", "args": [10]},
            {"name": "Image.constant", "args": [2]},
        ],
    }


def test_image_floordiv():
    assert (Image(9) // Image(2)).graph == {
        "name": "Image.floordiv",
        "args": [
            {"name": "Image.constant", "args": [9]},
            {"name": "Image.constant", "args": [2]},
        ],
    }
