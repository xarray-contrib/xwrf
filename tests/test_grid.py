import numpy as np
import pyproj
import pytest

import xwrf
from xwrf.grid import _wrf_grid_from_dataset, wgs84


@pytest.fixture(scope='session', params=['dummy'])
def dummy_dataset(request):
    return xwrf.tutorial.open_dataset(request.param)


@pytest.fixture(scope='session', params=['dummy_salem_parsed'])
def dummy_salem(request):
    return xwrf.tutorial.open_dataset(request.param)


@pytest.fixture(scope='session')
def test_grid(request):
    return xwrf.tutorial.open_dataset(request.param)


@pytest.fixture(scope='session')
def cf_grid_mapping_name(request):
    """A no-op to allow parallel indirect use with open dataset fixture."""
    return request.param


def test_grid_construction_against_salem(dummy_dataset, dummy_salem):
    grid_params = _wrf_grid_from_dataset(dummy_dataset)

    # Projection coordinate values
    np.testing.assert_array_almost_equal(
        grid_params['south_north'], dummy_salem['south_north'].values
    )
    np.testing.assert_array_almost_equal(grid_params['west_east'], dummy_salem['west_east'].values)

    # Projection CRS
    assert grid_params['crs'] == pyproj.CRS(dummy_salem['Q2'].attrs['pyproj_srs'])


def test_raise_notimplemented_error(dummy_dataset):
    dummy_dataset.attrs['MAP_PROJ'] = 'invalid'
    with pytest.raises(NotImplementedError):
        _wrf_grid_from_dataset(dummy_dataset)


@pytest.mark.parametrize(
    'test_grid, cf_grid_mapping_name',
    [
        ('polar_stereographic_1', 'polar_stereographic'),
        ('polar_stereographic_2', 'polar_stereographic'),
        ('lambert_conformal', 'lambert_conformal_conic'),
        ('mercator', 'mercator'),
    ],
    indirect=True,
)
def test_grid_construction_against_own_latlon(test_grid, cf_grid_mapping_name):
    grid_params = _wrf_grid_from_dataset(test_grid)
    trf = pyproj.Transformer.from_crs(grid_params['crs'], wgs84, always_xy=True)
    recalculated = {}
    recalculated['XLONG'], recalculated['XLAT'] = trf.transform(
        *np.meshgrid(grid_params['west_east'], grid_params['south_north'])
    )
    recalculated['XLONG_U'], recalculated['XLAT_U'] = trf.transform(
        *np.meshgrid(grid_params['west_east_stag'], grid_params['south_north'])
    )
    recalculated['XLONG_V'], recalculated['XLAT_V'] = trf.transform(
        *np.meshgrid(grid_params['west_east'], grid_params['south_north_stag'])
    )

    assert grid_params['crs'].to_cf()['grid_mapping_name'] == cf_grid_mapping_name
    for varname, recalculated_values in recalculated.items():
        if varname in test_grid.data_vars:
            np.testing.assert_array_almost_equal(
                recalculated_values,
                test_grid[varname].values[0],
                decimal=2,
                err_msg=f'Computed {varname} does not match with raw output',
            )
        elif '_' not in varname and varname + '_M' in test_grid.data_vars:
            np.testing.assert_array_almost_equal(
                recalculated_values,
                test_grid[varname + '_M'].values[0],
                decimal=2,
                err_msg=f"Computed {varname + '_M'} does not match with raw output",
            )


@pytest.mark.parametrize(
    'test_grid',
    [
        'ideal',
    ],
    indirect=True,
)
def test_ideal_grid(test_grid):
    grid_params = _wrf_grid_from_dataset(test_grid)
    assert grid_params['crs'] is None
