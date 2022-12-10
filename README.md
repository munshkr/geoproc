# geoproc

An open source toolkit for processing geospatial imagery with ease

[![CI](https://github.com/munshkr/geoproc/actions/workflows/ci.yml/badge.svg)](https://github.com/munshkr/geoproc/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/munshkr/geoproc/branch/main/graph/badge.svg?token=OI1L05MO4Y)](https://codecov.io/gh/munshkr/geoproc)
[![Issues](https://img.shields.io/github/issues-closed/munshkr/geoproc)](https://github.com/munshkr/geoproc/issues)

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
