import metpy
import pytest
import xarray as xr

import xwrf


@pytest.fixture(scope='session')
def sample_dataset(request):
    return xwrf.tutorial.open_dataset(request.param)


@pytest.mark.parametrize('sample_dataset', ['met_em_sample'], indirect=True)
def test_metpy_quantify(sample_dataset):
    ds = sample_dataset.xwrf.postprocess(decode_times=False).metpy.quantify()
    assert str(ds.PRES.data.units) == 'pascal'
    assert str(ds.MAPFAC_U.data.units) == 'dimensionless'


@pytest.mark.parametrize('sample_dataset', ['met_em_sample'], indirect=True)
def test_metpy_parse_cf(sample_dataset):
    ds = sample_dataset.xwrf.postprocess().metpy.parse_cf()
    assert 'metpy_crs' in ds.coords
    assert isinstance(ds.metpy_crs.data.item(), metpy.plots.mapping.CFProjection)
    assert ds['wrf_projection'].item() == ds['metpy_crs'].metpy.pyproj_crs


@pytest.mark.parametrize('sample_dataset', ['lambert_conformal', 'mercator'], indirect=True)
def test_metpy_coordinate_identification(sample_dataset):
    ds = sample_dataset.xwrf.postprocess()
    # U staggered
    xr.testing.assert_identical(ds['U'].metpy.x, ds['x_stag'])
    xr.testing.assert_identical(ds['U'].metpy.y, ds['y'])
    xr.testing.assert_identical(ds['U'].metpy.time, ds['Time'])
    xr.testing.assert_identical(ds['U'].metpy.longitude, ds['XLONG_U'])
    xr.testing.assert_identical(ds['U'].metpy.latitude, ds['XLAT_U'])
    # V staggered
    xr.testing.assert_identical(ds['V'].metpy.x, ds['x'])
    xr.testing.assert_identical(ds['V'].metpy.y, ds['y_stag'])
    xr.testing.assert_identical(ds['V'].metpy.time, ds['Time'])
    xr.testing.assert_identical(ds['V'].metpy.longitude, ds['XLONG_V'])
    xr.testing.assert_identical(ds['V'].metpy.latitude, ds['XLAT_V'])


@pytest.mark.parametrize(
    'sample_dataset, axis_mapping, test_varname',
    [('lambert_conformal', {'x': 3, 'y': 2, 'vertical': 1, 'time': 0}, 'QVAPOR')],
    indirect=['sample_dataset'],
)
def test_metpy_axis_identification(sample_dataset, axis_mapping, test_varname):
    da = sample_dataset.xwrf.postprocess()[test_varname]
    for axis_type, axis_number in axis_mapping.items():
        assert da.metpy.find_axis_number(axis_type) == axis_number
        assert da.metpy.find_axis_name(axis_type) == da.dims[axis_number]
