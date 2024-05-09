import numpy as np
import pyproj
import pytest
import xarray as xr

import xwrf

from . import importorskip


@pytest.fixture(scope='session')
def sample_dataset(request):
    return xwrf.tutorial.open_dataset(request.param)


@pytest.fixture(scope='session')
def sample_dataset_with_kwargs(request):
    return xwrf.tutorial.open_dataset(request.param[0], **request.param[1])


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


@pytest.mark.parametrize('bad_units', list(xwrf.config.get('unit_harmonization_map').values()))
def test_successful_unit_parsing(bad_units):
    synthetic_dataset = xr.Dataset(coords=dict(x=(['x'], np.random.rand(5))))
    for i, unit in enumerate(bad_units):
        synthetic_dataset[chr(i)] = xr.Variable(
            dims='x', data=np.random.rand(5), attrs={'units': unit}
        )
    xwrf.postprocess._make_units_pint_friendly(synthetic_dataset)


@pytest.mark.parametrize('sample_dataset', ['dummy'], indirect=True)
def test_include_projection_coordinates(sample_dataset):
    dataset = xwrf.postprocess._include_projection_coordinates(sample_dataset)
    assert dataset['south_north'].attrs['axis'] == 'Y'
    assert dataset['west_east'].attrs['axis'] == 'X'
    assert isinstance(dataset['wrf_projection'].item(), pyproj.CRS)
    assert dataset['Q2'].attrs['grid_mapping'] == 'wrf_projection'


@pytest.mark.parametrize(
    'sample_dataset', set(xwrf.tutorial.sample_datasets.keys()) - {'tiny', 'ideal'}, indirect=True
)
def test_grid_mapping_is_in_all_vars(sample_dataset):
    dataset = xwrf.postprocess._include_projection_coordinates(sample_dataset)
    horizontal_dims = set(xwrf.config.get('horizontal_dims')).intersection(set(dataset.dims))
    for var in dataset.data_vars:
        if any(dim in dataset[var].dims for dim in horizontal_dims):
            assert dataset[var].attrs['grid_mapping'] == 'wrf_projection'


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
    assert np.issubdtype(dsa['Time'].dtype, np.datetime64)
    assert dsa['Time'].attrs['long_name'] == 'Time'
    assert dsa['Time'].attrs['standard_name'] == 'time'


@pytest.mark.parametrize(
    'sample_dataset_with_kwargs,xtime_dtype',
    [
        (('mercator', {'decode_times': True}), np.datetime64),
        (('mercator', {'decode_times': False}), np.float32),
    ],
    indirect=['sample_dataset_with_kwargs'],
)
def test_xtime_handling(sample_dataset_with_kwargs, xtime_dtype):
    dataset = xwrf.postprocess._decode_times(sample_dataset_with_kwargs)
    assert np.issubdtype(dataset.XTIME.dtype, xtime_dtype)


@pytest.mark.parametrize(
    'sample_dataset_with_kwargs,xtime_dtype',
    [
        (('wrfout', {'decode_times': True}), np.datetime64),
        pytest.param(
            ('wrfout', {'decode_times': False}),
            np.datetime64,
            marks=pytest.mark.xfail(raises=ValueError, strict=True),
        ),
    ],
    indirect=['sample_dataset_with_kwargs'],
)
def test_xtime_fallback(sample_dataset_with_kwargs, xtime_dtype):
    dataset_fallback = xwrf.postprocess._decode_times(sample_dataset_with_kwargs.drop_vars('Times'))
    dataset = xwrf.postprocess._decode_times(sample_dataset_with_kwargs)
    assert dataset_fallback.Time.equals(dataset.Time)


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


@pytest.mark.parametrize('sample_dataset', ['lambert_conformal'], indirect=True)
def test_bracket_units_transl(sample_dataset):
    assert {'QNRAIN', 'NOAHRES'}.issubset(set(sample_dataset.variables))
    xwrf.postprocess._make_units_pint_friendly(sample_dataset)


@pytest.mark.parametrize('sample_dataset', ['lambert_conformal'], indirect=True)
def test_calc_base_diagnostics(sample_dataset):
    subset = (
        sample_dataset[
            ['T', 'P', 'PB', 'PH', 'PHB', 'U', 'V', 'U10', 'V10', 'SINALPHA', 'COSALPHA']
        ]
        .isel(Time=0)
        .load()
    )
    ds_dropped = subset.copy().pipe(xwrf.postprocess._calc_base_diagnostics)
    ds_undropped = subset.copy().pipe(xwrf.postprocess._calc_base_diagnostics, drop=False)

    for ds in (ds_dropped, ds_undropped):
        # Potential temperature
        np.testing.assert_allclose(ds['air_potential_temperature'].max().item(), 508.78415)
        np.testing.assert_allclose(ds['air_potential_temperature'].min().item(), 270.265106)
        assert ds['air_potential_temperature'].attrs['units'] == 'K'
        assert ds['air_potential_temperature'].attrs['standard_name'] == 'air_potential_temperature'

        # Air pressure
        np.testing.assert_allclose(ds['air_pressure'].max().item(), 101824.89)
        np.testing.assert_allclose(ds['air_pressure'].min().item(), 5269.97)
        assert ds['air_pressure'].attrs['units'] == 'Pa'
        assert ds['air_pressure'].attrs['standard_name'] == 'air_pressure'

        # Geopotential
        np.testing.assert_allclose(ds['geopotential'].max().item(), 196788.02)
        np.testing.assert_allclose(ds['geopotential'].min().item(), 0.0)
        assert ds['geopotential'].attrs['units'] == 'm**2 s**-2'
        assert ds['geopotential'].attrs['standard_name'] == 'geopotential'

        # Geopotential height
        np.testing.assert_allclose(ds['geopotential_height'].max().item(), 20059.941)
        np.testing.assert_allclose(ds['geopotential_height'].min().item(), 0.0)
        assert ds['geopotential_height'].attrs['units'] == 'm'
        assert ds['geopotential_height'].attrs['standard_name'] == 'geopotential_height'

        # Earth-relative eastward winds
        np.testing.assert_allclose(ds['wind_east'].max().item(), 34.492916)
        np.testing.assert_allclose(ds['wind_east'].min().item(), -3.2876422)
        assert ds['wind_east'].attrs['units'] == 'm s-1'
        assert ds['wind_east'].attrs['standard_name'] == 'eastward_wind'

        # Earth-relative northward winds
        np.testing.assert_allclose(ds['wind_north'].max().item(), 33.849540)
        np.testing.assert_allclose(ds['wind_north'].min().item(), -13.434467)
        assert ds['wind_north'].attrs['units'] == 'm s-1'
        assert ds['wind_north'].attrs['standard_name'] == 'northward_wind'

        # Earth-relative 10m eastward winds
        np.testing.assert_allclose(ds['wind_east_10'].max().item(), 10.115304)
        np.testing.assert_allclose(ds['wind_east_10'].min().item(), -0.918889)
        assert ds['wind_east_10'].attrs['units'] == 'm s-1'

        # Earth-relative 10m northward winds
        np.testing.assert_allclose(ds['wind_north_10'].max().item(), 1.8683547)
        np.testing.assert_allclose(ds['wind_north_10'].min().item(), -10.904247)
        assert ds['wind_north_10'].attrs['units'] == 'm s-1'

    # Check dropped or not
    assert 'T' not in ds_dropped
    assert 'P' not in ds_dropped
    assert 'PB' not in ds_dropped
    assert 'PH' not in ds_dropped
    assert 'PHB' not in ds_dropped
    assert 'T' in ds_undropped
    assert 'P' in ds_undropped
    assert 'PB' in ds_undropped
    assert 'PH' in ds_undropped
    assert 'PHB' in ds_undropped


@pytest.mark.parametrize('sample_dataset', ['wrfout'], indirect=True)
def test_calc_base_diagnostics_coords(sample_dataset):
    ds = sample_dataset.pipe(xwrf.postprocess._calc_base_diagnostics)
    assert sample_dataset.bottom_top.attrs == ds.bottom_top.attrs


@pytest.mark.parametrize(
    'sample_dataset', ['dummy', 'polar_stereographic_1', 'tiny', 'met_em_sample'], indirect=True
)
def test_calc_base_diagnostics_skipping(sample_dataset):
    ds = sample_dataset.pipe(xwrf.postprocess._calc_base_diagnostics)
    xr.testing.assert_identical(sample_dataset, ds)
