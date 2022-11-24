import rioxarray
import dask

class ImageCollection:
    def __init__(self, id):
        self.id = id

class Image:
    def __init__(self, id_or_data):
        if isinstance(id_or_data, str):
            self.id = id_or_data
        else:
            self.data = id_or_data

    @classmethod
    def load(cls, url, **kwargs):
        rds = rioxarray.open_rasterio(url, **kwargs)
        return cls(rds)
