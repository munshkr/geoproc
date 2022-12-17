# geoproc

An open source toolkit for processing geospatial imagery with ease

[![CI](https://github.com/munshkr/geoproc/actions/workflows/ci.yml/badge.svg)](https://github.com/munshkr/geoproc/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/munshkr/geoproc/branch/main/graph/badge.svg?token=OI1L05MO4Y)](https://codecov.io/gh/munshkr/geoproc)
[![Issues](https://img.shields.io/github/issues-closed/munshkr/geoproc)](https://github.com/munshkr/geoproc/issues)
[![License](https://img.shields.io/github/license/munshkr/geoproc)](https://github.com/munshkr/geoproc/blob/main/LICENSE)

**This is mostly a proof of concept and is rapidly changing. Not suited for production!**

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

Run `make docs` to start Sphinx autobuild server.

## Contributing

Bug reports and pull requests are welcome on GitHub at the [issues
page](https://github.com/munshkr/geoproc/issues). This project is intended to be
a safe, welcoming space for collaboration, and contributors are expected to
adhere to the [Contributor Covenant](http://contributor-covenant.org) code of
conduct.

## License

This project is licensed under Apache 2.0. Refer to
[LICENSE](https://github.com/munshkr/geoproc/blob/main/LICENSE).
