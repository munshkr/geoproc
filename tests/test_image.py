from eotoolkit.image import Image


def test_image_constant():
    img = Image.constant(1)
    assert img._graph == {"args": [1], "name": "constant"}


def test_image_load():
    img = Image.load("tci.tif")
    assert img._graph == {"args": ["tci.tif"], "name": "load"}


def test_image_init_contant():
    img = Image(1)
    assert img._graph == {"args": [1], "name": "constant"}


def test_image_init_load():
    img = Image("tci.tif")
    assert img._graph == {"args": ["tci.tif"], "name": "load"}
