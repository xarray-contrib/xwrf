import pytest

import xwrf


@pytest.fixture(scope='session')
def config():
    return xwrf.config


def test_defaults_exist(config):
    assert config.get('cf_attribute_map.T2.standard_name') is not None
