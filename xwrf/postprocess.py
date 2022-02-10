from __future__ import annotations  # noqa: F401

import pandas as pd
import xarray as xr

from .config import config


def _decode_times(ds: xr.Dataset) -> xr.Dataset:
    """
    Decode the time variable to datetime64.
    """
    ds = ds.assign_coords(
        {
            'Time': pd.to_datetime(
                ds.Times.data.astype('str'), errors='raise', format='%Y-%m-%d_%H:%M:%S'
            )
        }
    )
    ds.Time.attrs = {'long_name': 'Time', 'standard_name': 'time'}
    return ds


def _remove_units_from_bool_arrays(ds: xr.Dataset) -> xr.Dataset:
    boolean_units_attrs = config.get('boolean_units_attrs')
    for variable in ds.data_vars:
        if ds[variable].attrs.get('units') in boolean_units_attrs:
            ds[variable].attrs.pop('units', None)
    return ds


def _modify_attrs_to_cf(ds: xr.Dataset) -> xr.Dataset:
    """Modify the attributes of the dataset to comply with CF conventions."""
    vars_to_update = set(config.get('cf_attribute_map').keys()).intersection(set(ds.data_vars))
    for variable in vars_to_update:
        ds[variable].attrs.update(config.get(f'cf_attribute_map.{variable}'))
    return ds
