import xarray as xr


def _drop_attrs(attrs_dict, attrs_to_drop):
    try:
        return {k: v for k, v in attrs_dict.items() if k not in attrs_to_drop}
    except AttributeError:
        return None


def _destag_variable(datavar, stagger_dim=None, unstag_dim_name=None):
    """
    Destaggering function for a single wrf xarray.Variable

    Based off of the wrf-python destagger function
    https://github.com/NCAR/wrf-python/blob/22fb45c54f5193b849fdff0279445532c1a6c89f/src/wrf/destag.py
    Copyright 2016 University Corporation for Atmospheric Research, reused with modification
    according to the terms of the Apache License, Version 2.0

    Parameters
    ----------
    datavar : xarray.Variable
        Data variable to be destaggered
    stagger_dim : str, optional
        Name of dimension to unstagger. Defaults to guessing based on name (ends in "_stag")
    unstag_dim_name : str, option
        String to which to rename the dimension after destaggering. Example would be
        "west_east" for "west_east_stag". By default the dimenions will be renamed the text in
        front of "_stag" from the "stagger_dim" field.

    Returns
    -------
    xarray.Variable
        The destaggered variable with renamed dimension
    """
    if not isinstance(datavar, xr.Variable):
        # Implementation expects a Variable; don't want a DataArray or other type to slip through
        raise ValueError(f'Parameter datavar must be xarray.Variable, not {type(datavar)}')

    # Determine dimension to unstagger
    if stagger_dim and stagger_dim not in datavar.dims:
        # If user provided, but not actually there, error out
        raise ValueError(f'{stagger_dim} not in {datavar.dims}')
    elif stagger_dim is None:
        # If not provided, guess based on name
        stagger_dim = [x for x in datavar.dims if x.endswith('_stag')]

        if len(stagger_dim) > 1:
            raise NotImplementedError(
                'Expected a single destagger dimensions. Found multiple destagger dimensions: '
                f'{stagger_dim}'
            )
        elif len(stagger_dim) == 0:
            raise ValueError(
                'No dimension available to destagger. This variable does not appear to be '
                'staggered.'
            )

        # we need a string, not a list containing a string
        stagger_dim = stagger_dim[0]
    # Otherwise, we have a valid user provided stagger dimension

    # Destagger by mean of offset slices representing each side with respect to the stagger_dim
    stagger_dim_size = datavar.sizes[stagger_dim]
    left_or_bottom_cells = datavar.isel({stagger_dim: slice(0, stagger_dim_size - 1)})
    right_or_top_cells = datavar.isel({stagger_dim: slice(1, stagger_dim_size)})
    center_mean = (left_or_bottom_cells + right_or_top_cells) * 0.5

    # Determine new dimension name; if not given, use part of original name before "_stag"
    if unstag_dim_name is None:
        unstag_dim_name = stagger_dim.split('_stag')[0]

    # Return a Variable with renamed dimensions, updated data and attrs, and original encoding
    return xr.Variable(
        dims=tuple(str(unstag_dim_name) if dim == stagger_dim else dim for dim in center_mean.dims),
        data=center_mean.data,
        attrs=_drop_attrs(datavar.attrs, ('stagger', 'c_grid_axis_shift')),
        encoding=datavar.encoding,
        fastpath=True,
    )


def _rename_staggered_coordinate(name, stagger_dim=None, unstag_dim_name=None):
    if name == stagger_dim and unstag_dim_name is not None:
        return unstag_dim_name
    elif name[-2:].lower() in ('_u', '_v'):
        return name[:-2]
    elif name[-5:].lower() == '_stag':
        return name[:-5]
    else:
        return name
