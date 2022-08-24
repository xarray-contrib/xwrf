import pytest

import xwrf

from . import importorskip


@pytest.fixture(scope='session')
def sample_dataset(request):
    return xwrf.tutorial.open_dataset(request.param)


@importorskip('cf_units')
@pytest.mark.parametrize('sample_dataset', ['lambert_conformal'], indirect=True)
@pytest.mark.parametrize(
    'variable,cf_definition_string',
    (
        ('QNRAIN', 'kg-1'),
        ('NOAHRES', 'kg.s-3'),
        ('THIS_IS_AN_IDEAL_RUN', '?'),
        ('SAVE_TOPO_FROM_REAL', '?'),
        ('OL4', '?'),
        ('VAR_SSO', 'm2'),
        ('SEAICE', '?'),
    ),
)
def test_problematic_units_against_udunits_wrfout(sample_dataset, variable, cf_definition_string):
    from cf_units import Unit

    ds = sample_dataset.xwrf.postprocess()
    assert Unit(ds[variable].attrs.get('units', '')).definition == cf_definition_string


@importorskip('cf_units')
@pytest.mark.parametrize('sample_dataset', ['met_em_sample'], indirect=True)
@pytest.mark.parametrize(
    'variable,cf_definition_string',
    (
        ('OL4', '1'),
        ('GREENFRAC', '1'),
        ('PRES', 'm-1.kg.s-2'),
        ('ST', 'K'),
        ('SOILTEMP', 'K'),
        ('RH', '0.01 1'),
    ),
)
def test_problematic_units_against_udunits_met_em(sample_dataset, variable, cf_definition_string):
    from cf_units import Unit

    ds = sample_dataset.xwrf.postprocess()
    assert Unit(ds[variable].attrs.get('units', '')).definition == cf_definition_string
