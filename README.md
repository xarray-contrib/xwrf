# xwrf

A lightweight interface for reading in output from the Weather Research and Forecasting (WRF) model into xarray Dataset. The primary objective of `xwrf` is to replicate crucial I/O functionality from the [wrf-python](https://github.com/NCAR/wrf-python) package in a way that is **more convenient** for users and provides **seamless integration** with the rest of the Pangeo software stack.

| CI          | [![GitHub Workflow Status][github-ci-badge]][github-ci-link] [![GitHub Workflow Status][github-lint-badge]][github-lint-link] [![Code Coverage Status][codecov-badge]][codecov-link] |
| :---------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| **License** |                                                                        [![License][license-badge]][repo-link]                                                                        |

## _✨ This code is highly experimental! Let the buyer beware ⚠️ ;) ✨_

## Installation

`xwrf` may be installed with pip:

```bash
python -m pip install git+https://github.com/NCAR/xwrf.git
```

## What is it?

The native WRF output files are not [CF compliant](http://cf-pcmdi.llnl.gov/). This makes these files [not the easiest NetCDF files to use](<(https://sundowner.colorado.edu/wrfout_to_cf/overview.html#:~:text=http%3A//cf-pcmdi.llnl.gov/)>) with tools like xarray. This package provides a simple interface for reading in the WRF output files into xarray Dataset objects using xarray's [flexible and extensible I/O backend API](https://xarray.pydata.org/en/stable/internals/how-to-add-new-backend.html). For example, the following code reads in a WRF output file:

```python
In [1]: import xarray as xr

In [2]: path = "./tests/sample-data/wrfout_d03_2012-04-22_23_00_00_subset.nc"

In [3]: ds = xr.open_dataset(path, engine="xwrf")

In [4]: # or

In [5]: # ds = xr.open_dataset(path, engine="wrf")

In [6]: ds
Out[6]:
<xarray.Dataset>
Dimensions:  (Time: 1, south_north: 546, west_east: 480)
Coordinates:
    XLONG    (south_north, west_east) float32 ...
    XLAT     (south_north, west_east) float32 ...
Dimensions without coordinates: Time, south_north, west_east
Data variables:
    Q2       (Time, south_north, west_east) float32 ...
    PSFC     (Time, south_north, west_east) float32 ...
Attributes: (12/86)
    TITLE:                            OUTPUT FROM WRF V3.3.1 MODEL
    START_DATE:                      2012-04-20_00:00:00
    SIMULATION_START_DATE:           2012-04-20_00:00:00
    WEST-EAST_GRID_DIMENSION:        481
    SOUTH-NORTH_GRID_DIMENSION:      547
    BOTTOM-TOP_GRID_DIMENSION:       32
    ...                              ...
    NUM_LAND_CAT:                    24
    ISWATER:                         16
    ISLAKE:                          -1
    ISICE:                           24
    ISURBAN:                         1
    ISOILWATER:                      14
```

In addition to being able to use `xr.open_dataset`, `xwrf` also allows reading in multiple WRF output files at once via `xr.open_mfdataset` function:

```python

ds = xr.open_mfdataset(list_of_files, engine="xwrf", parallel=True,
                       concat_dim="Time", combine="nested")
```

### Why not just a preprocess function?

One can achieve the same functionality with a preprocess function. However, there are some additional I/O features that [wrf-python](https://github.com/NCAR/wrf-python) implements under the hood that we think would be worth implementing as part of a backend engine instead of a regular preprocess function.

[github-ci-badge]: https://img.shields.io/github/workflow/status/NCAR/xwrf/CI?label=CI&logo=github&style=for-the-badge
[github-lint-badge]: https://img.shields.io/github/workflow/status/NCAR/xwrf/linting?label=linting&logo=github&style=for-the-badge
[github-ci-link]: https://github.com/NCAR/xwrf/actions?query=workflow%3ACI
[github-lint-link]: https://github.com/NCAR/xwrf/actions?query=workflow%3Alinting
[codecov-badge]: https://img.shields.io/codecov/c/github/NCAR/xwrf.svg?logo=codecov&style=for-the-badge
[codecov-link]: https://codecov.io/gh/NCAR/xwrf
[license-badge]: https://img.shields.io/github/license/NCAR/xwrf?style=for-the-badge
[repo-link]: https://github.com/NCAR/xwrf
