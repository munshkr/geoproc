from geoproc.image import Image


def test_image_constant():
    img = Image.constant(1)
    assert img.graph == {"args": [1], "name": "constant"}


def test_image_load():
    img = Image.load("tci.tif")
    assert img.graph == {"args": ["tci.tif"], "name": "load"}


def test_image_init_contant():
    img = Image(1)
    assert img.graph == {"args": [1], "name": "constant"}


def test_image_init_load():
    img = Image("tci.tif")
    assert img.graph == {"args": ["tci.tif"], "name": "load"}


def test_image_abs():
    img = Image(-4)
    assert img.abs().graph == {
        "name": "abs",
        "args": [{"name": "constant", "args": [-4]}],
    }


def test_image_add():
    assert (Image(2) + Image(3)).graph == {
        "name": "__add__",
        "args": [
            {"name": "constant", "args": [2]},
            {"name": "constant", "args": [3]},
        ],
    }


def test_image_sub():
    assert (Image(4) - Image(3)).graph == {
        "name": "__sub__",
        "args": [
            {"name": "constant", "args": [4]},
            {"name": "constant", "args": [3]},
        ],
    }


def test_image_mult():
    assert (Image(2) * Image(2)).graph == {
        "name": "__mul__",
        "args": [
            {"name": "constant", "args": [2]},
            {"name": "constant", "args": [2]},
        ],
    }


def test_image_truediv():
    assert (Image(10) / Image(2)).graph == {
        "name": "__truediv__",
        "args": [
            {"name": "constant", "args": [10]},
            {"name": "constant", "args": [2]},
        ],
    }


def test_image_floordiv():
    assert (Image(9) // Image(2)).graph == {
        "name": "__floordiv__",
        "args": [
            {"name": "constant", "args": [9]},
            {"name": "constant", "args": [2]},
        ],
    }
