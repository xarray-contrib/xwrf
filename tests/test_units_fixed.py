import os
import pathlib

import pytest
import xarray as xr

import xwrf

here = pathlib.Path(os.path.abspath(os.path.dirname(__file__)))

sample_file = here / 'sample-data' / 'wrfout_d03_2018-10-18_00:00:00_only_attrs.nc'


@pytest.fixture(scope='session', params=[sample_file])
def dataset(request):
    return xr.open_dataset(request.param, engine=xwrf.WRFBackendEntrypoint)


@pytest.mark.parametrize('var_name', ('THIS_IS_AN_IDEAL_RUN', 'SAVE_TOPO_FROM_REAL'))
def test_unit_is_removed(dataset, var_name):
    assert 'units' not in dataset[var_name].attrs
