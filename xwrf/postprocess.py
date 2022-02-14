from __future__ import annotations  # noqa: F401

import pandas as pd
import xarray as xr

from .config import config


def _decode_times(ds: xr.Dataset) -> xr.Dataset:
    """
    Decode the time variable to datetime64.
    """
    try:
        _time = pd.to_datetime(
            ds.Times.data.astype('str'), errors='raise', format='%Y-%m-%d_%H:%M:%S'
        )
    except ValueError:
        _time = pd.to_datetime(
            ds.Times.data.astype('str'), errors='raise', format='%Y-%m-%dT%H:%M:%S.%f'
        )
    ds = ds.assign_coords({'Time': _time})
    ds.Time.attrs = {'long_name': 'Time', 'standard_name': 'time'}
    return ds


def _make_units_pint_friendly(ds: xr.Dataset) -> xr.Dataset:
    """
    Harmonizes awkward WRF units into pint-friendly ones
    """
    # We have to invert the mapping from "new_unit -> wrf_units" to "wrf_unit -> new_unit"
    wrf_units_map = {
        v: k for (k, val_list) in config.get('unit_harmonization_map').items() for v in val_list
    }
    for variable in ds.data_vars:
        if ds[variable].attrs.get('units') in wrf_units_map:
            harmonized_unit = wrf_units_map[ds[variable].attrs['units']]
            if harmonized_unit == "invalid":
                ds[variable].attrs.pop('units', None)
            else:
                ds[variable].attrs['units'] = harmonized_unit
    return ds


def _modify_attrs_to_cf(ds: xr.Dataset) -> xr.Dataset:
    """Modify the attributes of the dataset to comply with CF conventions."""
    vars_to_update = set(config.get('cf_attribute_map').keys()).intersection(set(ds.data_vars))
    for variable in vars_to_update:
        ds[variable].attrs.update(config.get(f'cf_attribute_map.{variable}'))
    return ds


def _collapse_time_dim(ds: xr.Dataset) -> xr.Dataset:

    # This "time dimension collapsing" assumption is wrong with moving nests
    # and should be applied to static, nested domains.
    lat_lon_coords = set(config.get('latitude_coords') + config.get('longitude_coords'))
    coords = set(ds.variables).intersection(lat_lon_coords)
    ds = ds.set_coords(coords)

    for coord in ds.coords:
        if coord in lat_lon_coords and ds[coord].ndim == 3:
            attrs, encoding = ds[coord].attrs, ds[coord].encoding
            ds = ds.assign_coords({coord: (ds[coord].dims[1:], ds[coord].data[0, :, :])})
            ds[coord].attrs = attrs
            ds[coord].encoding = encoding

    return ds
