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
    # get the coordinate to unstagger
    # option 1) user has provided the dimension
    if stagger_dim and stagger_dim not in datavar.dims:
        # check that the user-passed in stag dim is actually in there
        raise ValueError(f'{stagger_dim} not in {datavar.dims}')

    # option 2) guess the staggered dimension
    else:
        # guess the name of the coordinate
        stagger_dim = [x for x in datavar.dims if x.endswith('_stag')]

        if len(stagger_dim) > 1:
            raise NotImplementedError(
                'Expected a single destagger dimensions. Found multiple destagger dimensions: '
                f'{stagger_dim}'
            )

        # we need a string, not a list
        stagger_dim = stagger_dim[0]

    # get the size of the staggereed coordinate
    stagger_dim_size = datavar.sizes[stagger_dim]

    # I think the "dict(a="...")"  format is preferrable... but you cant stick an fx arg string
    # into that...
    left_or_bottom_cells = datavar.isel({stagger_dim: slice(0, stagger_dim_size - 1)})
    right_or_top_cells = datavar.isel({stagger_dim: slice(1, stagger_dim_size)})
    center_mean = (left_or_bottom_cells + right_or_top_cells) * 0.5

    # now change the variable name of the unstaggered coordinate
    # we can pass this in if we want to, for whatever reason
    if not unstag_dim_name:
        unstag_dim_name = stagger_dim.split('_stag')[
            0
        ]  # get the part of the name before the "_stag"

    # return a data variable with renamed dimensions
    return xr.Variable(
        dims=tuple(str(unstag_dim_name) if dim == stagger_dim else dim for dim in center_mean.dims),
        data=center_mean.data,
        attrs=_drop_attrs(center_mean.attrs, ('stagger',)),
        encoding=center_mean.encoding,
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
