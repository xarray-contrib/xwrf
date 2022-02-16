import pyproj
import pytest

import xwrf

from . import importorskip


@pytest.fixture(scope='session', params=['dummy'])
def dummy_dataset(request):
    return xwrf.tutorial.open_dataset(request.param)


@pytest.fixture(scope='session', params=['dummy_attrs_only'])
def dummy_attrs_only_dataset(request):
    return xwrf.tutorial.open_dataset(request.param)


@pytest.fixture(scope='session', params=['met_em_sample'])
def met_em_dataset(request):
    return xwrf.tutorial.open_dataset(request.param)


@pytest.fixture(scope='session')
def test_grid(request):
    return xwrf.tutorial.open_dataset(request.param)


@pytest.mark.parametrize('variable', ('Q2', 'PSFC'))
def test_cf_attrs_added(dummy_dataset, variable):
    dataset = xwrf.postprocess._modify_attrs_to_cf(dummy_dataset)
    attrs = dataset[variable].attrs.keys()
    assert 'standard_name' in attrs
    assert 'long_name' in attrs


@pytest.mark.parametrize('variable', ('THIS_IS_AN_IDEAL_RUN', 'SAVE_TOPO_FROM_REAL'))
def test_remove_invalid_units(dummy_attrs_only_dataset, variable):
    dataset = xwrf.postprocess._make_units_pint_friendly(dummy_attrs_only_dataset)
    assert 'units' not in dataset[variable].attrs


@pytest.mark.parametrize('variable', ('OL4', 'GREENFRAC'))
def test_met_em_parsing(met_em_dataset, variable):
    dataset = xwrf.postprocess._make_units_pint_friendly(met_em_dataset)
    assert dataset[variable].attrs['units'] == '1'


def test_include_projection_coordinates(dummy_dataset):
    dataset = xwrf.postprocess._include_projection_coordinates(dummy_dataset)
    assert dataset['south_north'].attrs['axis'] == 'Y'
    assert dataset['west_east'].attrs['axis'] == 'X'
    assert isinstance(dataset['wrf_projection'].item(), pyproj.CRS)
    assert dataset['Q2'].attrs['grid_mapping'] == 'wrf_projection'


@importorskip('xgcm')
@pytest.mark.parametrize('test_grid', ['lambert_conformal', 'mercator'], indirect=True)
def test_include_projection_coordinates_with_xgcm(test_grid):
    from xgcm import Grid

    dataset = xwrf.postprocess._include_projection_coordinates(test_grid)
    grid = Grid(dataset)

    assert grid.axes['Y'].coords['center'] == 'south_north'
    assert grid.axes['Y'].coords['outer'] == 'south_north_stag'
    assert grid.axes['X'].coords['center'] == 'west_east'
    assert grid.axes['X'].coords['outer'] == 'west_east_stag'


def test_warning_on_projection_coordinate_failure(dummy_attrs_only_dataset):
    with pytest.warns(UserWarning):
        dataset = xwrf.postprocess._include_projection_coordinates(dummy_attrs_only_dataset)
    assert dataset is dummy_attrs_only_dataset


def test_rename_dims(dummy_dataset):
    dataset = xwrf.postprocess._rename_dims(dummy_dataset)
    assert {'x', 'y'}.intersection(set(dataset.dims))
    assert not {'south_north', 'west_east'}.intersection(set(dataset.dims))
