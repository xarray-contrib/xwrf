import numpy as np
import pyproj
import pytest

import xwrf

from . import importorskip

datasets_to_test = xwrf.tutorial.sample_datasets.keys()

@pytest.fixture(scope='session')
def sample_dataset(request):
    return xwrf.tutorial.open_dataset(request.param)

@importorskip('metpy')
@pytest.mark.parametrize('sample_dataset', set(datasets_to_test) - {'tiny'}, indirect=True)
def test_metpy_quantify(sample_dataset):
    sample_dataset.xwrf.postprocess(decode_times=False).metpy.quantify()

@importorskip('metpy')
@pytest.mark.parametrize('sample_dataset', datasets_to_test, indirect=True)
def test_metpy_parse_cf(sample_dataset):
    sample_dataset.metpy.parse_cf()
