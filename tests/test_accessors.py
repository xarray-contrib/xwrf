import pandas as pd
import pytest

import xwrf

from . import importorskip


@importorskip('cf_xarray')
@pytest.mark.parametrize('name', ['lambert_conformal'])
def test_postprocess(name):

    raw_ds = xwrf.tutorial.open_dataset(name)
    assert pd.api.types.is_string_dtype(raw_ds.Times.dtype)
    assert pd.api.types.is_numeric_dtype(raw_ds.Time.dtype)
    assert 'time' not in raw_ds.cf.coordinates
    assert raw_ds.cf.standard_names == {}
    ds = raw_ds.xwrf.postprocess()
    assert pd.api.types.is_datetime64_dtype(ds.Time.dtype)
    assert 'time' in ds.cf.coordinates
    standard_names = ds.cf.standard_names

    assert standard_names['time'] == ['Time']
    assert standard_names['humidity_mixing_ratio'] == ['Q2', 'QVAPOR']
    assert standard_names['air_temperature'] == ['T2']
