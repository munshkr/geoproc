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
    assert abs(img).graph == {
        "name": "__abs__",
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


def test_image_lt():
    assert (Image(9) < Image(2)).graph == {
        "name": "__lt__",
        "args": [
            {"name": "constant", "args": [9]},
            {"name": "constant", "args": [2]},
        ],
    }


def test_image_le():
    assert (Image(9) <= Image(2)).graph == {
        "name": "__le__",
        "args": [
            {"name": "constant", "args": [9]},
            {"name": "constant", "args": [2]},
        ],
    }


def test_image_eq():
    assert (Image(42) == Image(43)).graph == {
        "name": "__eq__",
        "args": [
            {"name": "constant", "args": [42]},
            {"name": "constant", "args": [43]},
        ],
    }


def test_image_ne():
    assert (Image(42) != Image(43)).graph == {
        "name": "__ne__",
        "args": [
            {"name": "constant", "args": [42]},
            {"name": "constant", "args": [43]},
        ],
    }


def test_image_gt():
    assert (Image(9) > Image(2)).graph == {
        "name": "__gt__",
        "args": [
            {"name": "constant", "args": [9]},
            {"name": "constant", "args": [2]},
        ],
    }


def test_image_ge():
    assert (Image(9) >= Image(2)).graph == {
        "name": "__ge__",
        "args": [
            {"name": "constant", "args": [9]},
            {"name": "constant", "args": [2]},
        ],
    }
