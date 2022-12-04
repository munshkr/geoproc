# geoproc

An open source toolkit for processing geospatial imagery with ease

## Features

* Work with multiple datasets in a straightforward and consistent way
* Make it easy to manipulate images (band concatenation, resampling,
  reprojecting, clipping, vectorization and rasterization, etc.)
* Efficient image processing (multiprocessing)
* Use it either from your laptop or in a computing cluster in the cloud

## Development

Run `poetry install` to install dependencies.

Run `make run` to start development API server.

Run `poetry run pytest` to run tests. You can also do `poetry run ptw -- -v` to
watch for files and run tests automatically on changes.
