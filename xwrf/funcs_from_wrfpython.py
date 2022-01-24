def _destag_single_var(datavar, 
                       stagger_dim, 
                       unstag_dim_name=None):
    
    # based off of the wrf-python destagger function 
    # https://github.com/NCAR/wrf-python/blob/22fb45c54f5193b849fdff0279445532c1a6c89f/src/wrf/destag.py

    # datavar: xarary data array 
    # stagger_dim: str
    # unstag_dim_name: <str, optional> argument used to rename the dimension 
    
    
    # check that the stagger_dim is in fact in the datavar
    # ...
    assert stagger_dim in datavar.dims, AttributeError("%s not in %s"%(stagger_dim, datavar.dims))
    
    # get the number of dimensions 
    num_dims = datavar.ndim 
    
    # get the size of the staggereed dim 
    stagger_dim_size = datavar[stagger_dim].shape[0]
        
    # I think the "dict(a="...")"  format is preferrable... but you cant stick an fx arg string 
    # into that...

    left_or_bottom_cells = datavar.isel({stagger_dim:slice(1,stagger_dim_size)})
    right_or_top_cells   = datavar.isel({stagger_dim:slice(0,stagger_dim_size-1)})
    center_mean          = (left_or_bottom_cells+right_or_top_cells)*2
    
    # now change the variable name of the unstaggered dimension....
    # we can pass this in if we want for 
    stagger_dim_name_split = stagger_dim.split("_stag")[0] # get the part of the name before the "_stag"
    
    # return the mean of the cell 
    return center_mean.rename({stagger_dim :stagger_dim_name_split})
