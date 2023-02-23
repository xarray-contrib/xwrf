import pandas as pd
import pytest
import xarray as xr

import xwrf

from . import importorskip


@pytest.fixture(scope='session')
def test_grid(request):
    return xwrf.tutorial.open_dataset(request.param)


@importorskip('cf_xarray')
@pytest.mark.parametrize(
    'name, cf_grid_mapping_name', [('lambert_conformal', 'lambert_conformal_conic')]
)
def test_postprocess(name, cf_grid_mapping_name):
    # Verify initial/raw state
    raw_ds = xwrf.tutorial.open_dataset(name)
    assert pd.api.types.is_string_dtype(raw_ds.Times.dtype)
    assert pd.api.types.is_numeric_dtype(raw_ds.Time.dtype)
    assert 'time' not in raw_ds.cf.coordinates
    assert raw_ds.cf.standard_names == {}

    # Postprocess without decoding times
    dsa = raw_ds.xwrf.postprocess(decode_times=False)
    assert pd.api.types.is_numeric_dtype(dsa.Time.dtype)

    # Postprocess
    ds = raw_ds.xwrf.postprocess()

    # Check for time coordinate handling
    assert pd.api.types.is_datetime64_dtype(ds.Time.dtype)
    assert 'time' in ds.cf.coordinates

    # Check for projection handling
    assert ds['wrf_projection'].attrs['grid_mapping_name'] == cf_grid_mapping_name

    # Check for standard name and variable handling
    standard_names = ds.cf.standard_names
    assert 'x' in standard_names['projection_x_coordinate']
    assert 'y' in standard_names['projection_y_coordinate']
    assert 'z' in standard_names['atmosphere_hybrid_sigma_pressure_coordinate']
    assert standard_names['time'] == ['Time']
    assert standard_names['humidity_mixing_ratio'] == ['Q2', 'QVAPOR']
    assert standard_names['air_temperature'] == ['T2']

    # Check for time dimension reduction
    assert ds['z'].shape == (39,)
    assert ds['z_stag'].shape == (40,)
    assert ds['XLAT'].shape == ds['XLONG'].shape == (29, 31)
    assert ds['XLAT_U'].shape == ds['XLONG_U'].shape == (29, 32)
    assert ds['XLAT_V'].shape == ds['XLONG_V'].shape == (30, 31)

    # Check for diagnostic variable calculation
    assert 'air_potential_temperature' in ds.data_vars
    assert 'air_pressure' in ds.data_vars
    assert 'geopotential' in ds.data_vars
    assert 'geopotential_height' in ds.data_vars
    assert 'T' not in ds.data_vars
    assert 'P' not in ds.data_vars
    assert 'PB' not in ds.data_vars
    assert 'PH' not in ds.data_vars
    assert 'PHB' not in ds.data_vars


@pytest.mark.parametrize('test_grid', ['lambert_conformal', 'mercator'], indirect=True)
def test_dataarray_destagger(test_grid):
    data = test_grid['U']
    destaggered = data.xwrf.destagger()

    # Check shape reduction and dim name adjustment
    assert destaggered.sizes['west_east'] == data.sizes['west_east_stag'] - 1

    # Check coordinate reduction
    xr.testing.assert_allclose(destaggered['XLAT'], test_grid['XLAT'])
    xr.testing.assert_allclose(destaggered['XLONG'], test_grid['XLONG'])

    # Check attributes are preserved
    assert set(destaggered.attrs.keys()) == set(data.attrs.keys()) - {
        'stagger',
    }


@pytest.mark.parametrize('test_grid', ['lambert_conformal', 'mercator'], indirect=True)
def test_dataarray_destagger_with_exclude(test_grid):
    data = test_grid['V']
    destaggered = data.xwrf.destagger(exclude_staggered_auxiliary_coords=True)

    # Check shape reduction and dim name adjustment
    assert destaggered.sizes['south_north'] == data.sizes['south_north_stag'] - 1

    # Verify that no XLAT/XLONG are present in output, but XTIME (which is auxiliary, but not
    # staggered) remains
    assert not any(coord_name.startswith('XL') for coord_name in destaggered.coords)
    assert 'XTIME' in destaggered.coords


@pytest.mark.parametrize('test_grid', ['lambert_conformal', 'mercator'], indirect=True)
def test_dataarray_destagger_with_postprocess(test_grid):
    postprocessed = test_grid.xwrf.postprocess()
    data = postprocessed['U']
    destaggered = data.xwrf.destagger(exclude_staggered_auxiliary_coords=True)

    # Check staggered to unstaggered dimension coordinate handling
    xr.testing.assert_allclose(destaggered['x'], postprocessed['x'])

    # Check attributes are preserved, other than those made invalid by destaggering
    assert set(destaggered.attrs.keys()) == set(data.attrs.keys()) - {
        'stagger',
    }
    assert 'c_grid_axis_shift' not in destaggered['x'].attrs


@pytest.mark.parametrize('test_grid', ['lambert_conformal', 'mercator'], indirect=True)
def test_dataset_destagger(test_grid):
    destaggered = (
        test_grid.isel(Time=slice(0, 2))
        .xwrf.postprocess(calculate_diagnostic_variables=False)
        .xwrf.destagger()
    )

    # Check elimination of staggered dims and "stagger" attr
    for varname in destaggered.data_vars:
        assert not {'x_stag', 'y_stag', 'z_stag'}.intersection(set(destaggered[varname].dims))
        assert (
            'stagger' not in destaggered[varname].attrs
            or destaggered[varname].attrs['stagger'] == ''
        )

    # Check preservation of variable attrs
    for varname in set(test_grid.data_vars).intersection(set(destaggered.data_vars)):
        # because of xwrf.postprocess, the destaggered attrs will include more information
        assert set(test_grid[varname].attrs.keys()) - {'stagger', 'units'} <= set(
            destaggered[varname].attrs.keys()
        )

    # Check that attrs are preserved
    assert destaggered.attrs == test_grid.attrs
