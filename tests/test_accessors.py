import pandas as pd
import pytest

import xwrf

from . import importorskip


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
