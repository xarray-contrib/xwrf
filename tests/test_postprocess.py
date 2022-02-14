import pytest

import xwrf


@pytest.fixture(scope='session', params=['dummy'])
def dummy_dataset(request):
    return xwrf.tutorial.open_dataset(request.param)


@pytest.fixture(scope='session', params=['dummy_attrs_only'])
def dummy_attrs_only_dataset(request):
    return xwrf.tutorial.open_dataset(request.param)


@pytest.mark.parametrize('variable', ('Q2', 'PSFC'))
def test_cf_attrs_added(dummy_dataset, variable):
    dataset = xwrf.postprocess._modify_attrs_to_cf(dummy_dataset)
    attrs = dataset[variable].attrs.keys()
    assert 'standard_name' in attrs
    assert 'long_name' in attrs


@pytest.mark.parametrize('variable', ('THIS_IS_AN_IDEAL_RUN', 'SAVE_TOPO_FROM_REAL'))
def test_remove_invalid_units(dummy_attrs_only_dataset, variable):
    dataset = xwrf.postprocess._remove_invalid_units(dummy_attrs_only_dataset)
    assert 'units' not in dataset[variable].attrs
