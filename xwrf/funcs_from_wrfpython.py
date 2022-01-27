def _destag_single_var(datavar, stagger_dim=None, unstag_dim_name=None):

    # "de-stagger" function for a single xarray wrf data variable
    # returns the de-staggered and variable with renamed dimension

    # based off of the wrf-python destagger function
    # https://github.com/NCAR/wrf-python/blob/22fb45c54f5193b849fdff0279445532c1a6c89f/src/wrf/destag.py

    # datavar: xarary data array
    # stagger_dim: <str, optional> dimension to unstagger. fx will guess based on name (ends in "_stag")
    # unstag_dim_name: <str, optional> argument used to rename the dimension.
    #                  example would be "west_east" for "west_east_stag"
    #                  by default the dimenions will be renamed the text in front
    #                  of "_stag" from the "stagger_dim" field

    # ------------------------------------------------------

    # get the coordinate to unstagger
    # option 1) user has provided the dimension
    if stagger_dim:
        # check that the user-passed in stag dim is actually in there
        assert stagger_dim in datavar.dims, AttributeError(f'{stagger_dim} not in {datavar.dims}')

    # option 2) guess the staggered dimension
    else:
        # guess the name of the coordinate
        stagger_dim = [x for x in datavar.dims if x.endswith('_stag')]

        if len(stagger_dim) > 1:
            raise NotImplementedError('multiple destgger dimensions present?')

        # we need a string, not a list
        stagger_dim = stagger_dim[0]

    # get the size of the staggereed coordinate
    stagger_dim_size = datavar[stagger_dim].shape[0]

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

    # return a data array with renamed dimensions
    return center_mean.rename({stagger_dim: unstag_dim_name})
