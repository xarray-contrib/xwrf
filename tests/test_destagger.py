from collections import Counter

import numpy as np
import pytest
import xarray as xr

from xwrf.destagger import _destag_variable, _drop_attrs, _rename_staggered_coordinate


@pytest.mark.parametrize(
    'input_attrs, output_attrs',
    [
        ({'a': 0, 'b': 1, 'c': 2}, {'a': 0, 'c': 2}),
        ({'b': 3}, {}),
        ({'a': 4, 'c': 5}, {'a': 4, 'c': 5}),
        (Counter(('a', 'a', 'b', 'c')), {'a': 2, 'c': 1}),
    ],
)
def test_drop_attrs_successful(input_attrs, output_attrs):
    result = _drop_attrs(input_attrs, ('b',))
    assert result == output_attrs
    assert isinstance(result, dict)


def test_drop_attrs_unsuccessful():
    assert _drop_attrs('not a Mapping', ('a',)) is None


@pytest.mark.parametrize(
    'input_name, stagger_dim, unstag_dim_name, output_name',
    [
        (
            'bottom_top',
            'bottom_top_stag',
            None,
            'bottom_top',
        ),
        ('bottom_top_stag', 'bottom_top_stag', 'z', 'z'),
        ('bottom_top_stag', 'bottom_top_stag', None, 'bottom_top'),
        ('XLAT_U', 'west_east', None, 'XLAT'),
        ('XLONG_V', 'south_north', None, 'XLONG'),
    ],
)
def test_rename_staggered_coordinate(input_name, stagger_dim, unstag_dim_name, output_name):
    assert _rename_staggered_coordinate(input_name, stagger_dim, unstag_dim_name) == output_name


def test_destag_variable_dataarray():
    with pytest.raises(ValueError) as exc_info:
        mock_da = xr.DataArray(
            np.zeros((2, 2)), dims=('x_stag', 'y'), coords={'x_stag': [0, 1], 'y': [0, 1]}
        )
        _destag_variable(mock_da)
    assert (
        exc_info.value.args[0] == f'Parameter datavar must be xarray.Variable, not {type(mock_da)}'
    )


def test_destag_variable_unstaggered():
    with pytest.raises(ValueError) as exc_info:
        _destag_variable(xr.Variable(('x', 'y'), np.zeros((2, 2))))
    assert (
        exc_info.value.args[0]
        == 'No dimension available to destagger. This variable does not appear to be staggered.'
    )


def test_destag_variable_missing_dim():
    with pytest.raises(ValueError):
        _destag_variable(xr.Variable(('x', 'y'), np.zeros((2, 2))), 'z_stag')


def test_destag_variable_multiple_dims():
    with pytest.raises(NotImplementedError):
        _destag_variable(xr.Variable(('x_stag', 'y_stag'), np.zeros((2, 2))))


@pytest.mark.parametrize(
    'unstag_dim_name, expected_output_dim_name',
    [
        ('z', 'z'),
        (None, 'bottom_top'),
    ],
)
def test_destag_variable_1d(unstag_dim_name, expected_output_dim_name):
    staggered = xr.Variable(
        ('bottom_top_stag',), np.arange(5), attrs={'foo': 'bar', 'stagger': 'Z'}
    )
    output = _destag_variable(staggered, unstag_dim_name=unstag_dim_name)
    # Check values
    np.testing.assert_array_almost_equal(output.values, 0.5 + np.arange(4))
    # Check dim name
    assert output.dims[0] == expected_output_dim_name
    # Check attrs
    assert output.attrs == {'foo': 'bar'}


def test_destag_variable_2d():
    staggered = xr.Variable(('x', 'y_stag'), np.arange(9).reshape(3, 3))
    expected = xr.Variable(('x', 'y'), [[0.5, 1.5], [3.5, 4.5], [6.5, 7.5]])
    xr.testing.assert_equal(_destag_variable(staggered), expected)
