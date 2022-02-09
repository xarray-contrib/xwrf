import os
import pathlib

import pytest
import xarray as xr

import xwrf

here = pathlib.Path(os.path.abspath(os.path.dirname(__file__)))

sample_file = here / 'sample-data' / 'wrfout_d03_2012-04-22_23_00_00_subset.nc'


@pytest.fixture(scope='session', params=[sample_file])
def dataset(request):
    return xr.open_dataset(request.param, engine=xwrf.WRFBackendEntrypoint)


@pytest.mark.parametrize('var_name', ('Q2', 'PSFC'))
def test_cf_attrs_added(dataset, var_name):
    value_list = dataset[var_name].attrs.keys()
    assert ('standard_name' in value_list) and ('long_name' in value_list)
