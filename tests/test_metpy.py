import metpy
import pytest

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
