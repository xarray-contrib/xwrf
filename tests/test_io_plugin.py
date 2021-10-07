import os
import pathlib

import numpy as np
import pytest
import wrf
import xarray as xr
from netCDF4 import Dataset

here = pathlib.Path(os.path.abspath(os.path.dirname(__file__)))

sample_file = here / 'sample-data' / 'wrfout_d03_2012-04-22_23_00_00_subset.nc'


def test_plugin():
    engines = xr.backends.list_engines()
    for item in ['wrf', 'xwrf']:
        entrypoint = engines[item]
        assert entrypoint.__module__ == 'xwrf.io_plugin'


@pytest.mark.parametrize('variable', ['Q2', 'PSFC'])
def test_xr_open_dataset(variable):
    ds = xr.open_dataset(sample_file, engine='wrf')
    dataset = Dataset(sample_file)
    wrf_output = wrf.getvar(dataset, variable)
    np.testing.assert_array_equal(ds[variable].squeeze(), wrf_output)
