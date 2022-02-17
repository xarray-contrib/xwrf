import numpy as np
import pyproj
import pytest
import xarray as xr

import xwrf

from . import importorskip


@pytest.fixture(scope='session')
def sample_dataset(request):
    return xwrf.tutorial.open_dataset(request.param)


@pytest.mark.parametrize('sample_dataset', ['dummy'], indirect=True)
@pytest.mark.parametrize('variable', ('Q2', 'PSFC'))
def test_cf_attrs_added(sample_dataset, variable):
    dataset = xwrf.postprocess._modify_attrs_to_cf(sample_dataset)
    attrs = dataset[variable].attrs.keys()
    assert 'standard_name' in attrs
    assert 'long_name' in attrs


@pytest.mark.parametrize('sample_dataset', ['dummy_attrs_only'], indirect=True)
@pytest.mark.parametrize('variable', ('THIS_IS_AN_IDEAL_RUN', 'SAVE_TOPO_FROM_REAL'))
def test_remove_invalid_units(sample_dataset, variable):
    dataset = xwrf.postprocess._make_units_pint_friendly(sample_dataset)
    assert 'units' not in dataset[variable].attrs


@pytest.mark.parametrize('sample_dataset', ['met_em_sample'], indirect=True)
@pytest.mark.parametrize('variable', ('OL4', 'GREENFRAC'))
def test_met_em_parsing(sample_dataset, variable):
    dataset = xwrf.postprocess._make_units_pint_friendly(sample_dataset)
    assert dataset[variable].attrs['units'] == '1'


@pytest.mark.parametrize('sample_dataset', ['dummy'], indirect=True)
def test_include_projection_coordinates(sample_dataset):
    dataset = xwrf.postprocess._include_projection_coordinates(sample_dataset)
    assert dataset['south_north'].attrs['axis'] == 'Y'
    assert dataset['west_east'].attrs['axis'] == 'X'
    assert isinstance(dataset['wrf_projection'].item(), pyproj.CRS)
    assert dataset['Q2'].attrs['grid_mapping'] == 'wrf_projection'


@importorskip('xgcm')
@pytest.mark.parametrize('sample_dataset', ['lambert_conformal', 'mercator'], indirect=True)
def test_include_projection_coordinates_with_xgcm(sample_dataset):
    from xgcm import Grid

    dataset = xwrf.postprocess._include_projection_coordinates(sample_dataset)
    grid = Grid(dataset)

    assert grid.axes['Y'].coords['center'] == 'south_north'
    assert grid.axes['Y'].coords['outer'] == 'south_north_stag'
    assert grid.axes['X'].coords['center'] == 'west_east'
    assert grid.axes['X'].coords['outer'] == 'west_east_stag'


@pytest.mark.parametrize('sample_dataset', ['dummy_attrs_only'], indirect=True)
def test_warning_on_projection_coordinate_failure(sample_dataset):
    with pytest.warns(UserWarning):
        dataset = xwrf.postprocess._include_projection_coordinates(sample_dataset)
    assert dataset is sample_dataset


@pytest.mark.parametrize('sample_dataset', ['dummy'], indirect=True)
def test_rename_dims(sample_dataset):
    dataset = xwrf.postprocess._rename_dims(sample_dataset)
    assert {'x', 'y'}.intersection(set(dataset.dims))
    assert not {'south_north', 'west_east'}.intersection(set(dataset.dims))


@pytest.mark.parametrize('times', [[b'2005-08-28_12:00:00'], [b'2005-08-28T12:00:00']])
def test_decode_times(times):
    ds = xr.Dataset({'Times': times})
    dsa = xwrf.postprocess._decode_times(ds)
    assert dsa['Time'].dtype == 'datetime64[ns]'
    assert dsa['Time'].attrs['long_name'] == 'Time'
    assert dsa['Time'].attrs['standard_name'] == 'time'


@pytest.mark.parametrize('sample_dataset', ['lambert_conformal'], indirect=True)
def test_assign_coord_to_dim_of_different_name(sample_dataset):
    dataset = sample_dataset.pipe(xwrf.postprocess._collapse_time_dim).pipe(
        xwrf.postprocess._assign_coord_to_dim_of_different_name
    )
    assert 'ZNU' not in dataset.dims
    assert 'ZNW' not in dataset.dims
    assert 'bottom_top' in dataset.dims
    assert 'bottom_top_stag' in dataset.dims
    sample_dataset_w_collapsed_time = sample_dataset.pipe(xwrf.postprocess._collapse_time_dim)
    np.testing.assert_equal(sample_dataset_w_collapsed_time['ZNU'].data, dataset['bottom_top'].data)
    np.testing.assert_equal(
        sample_dataset_w_collapsed_time['ZNW'].data, dataset['bottom_top_stag'].data
    )


@pytest.mark.parametrize('sample_dataset', ['met_em_sample'], indirect=True)
def test_assign_coord_to_dim_of_different_name_keyerror(sample_dataset):
    ds = sample_dataset.pipe(xwrf.postprocess._collapse_time_dim)
    dataset = ds.pipe(xwrf.postprocess._assign_coord_to_dim_of_different_name)
    xr.testing.assert_equal(ds, dataset)
