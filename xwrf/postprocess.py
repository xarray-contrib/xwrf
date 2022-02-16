from __future__ import annotations  # noqa: F401

import warnings

import pandas as pd
import xarray as xr

from .config import config
from .grid import _wrf_grid_from_dataset


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
            if harmonized_unit == 'invalid':
                ds[variable].attrs.pop('units', None)
            else:
                ds[variable].attrs['units'] = harmonized_unit
    return ds


def _modify_attrs_to_cf(ds: xr.Dataset) -> xr.Dataset:
    """Modify the attributes of the dataset to comply with CF conventions."""
    # Universal updates
    vars_to_update = set(config.get('cf_attribute_map').keys()).intersection(set(ds.data_vars))
    for variable in vars_to_update:
        ds[variable].attrs.update(config.get(f'cf_attribute_map.{variable}'))

    # Conditional updates (right now just vertical coordinate type)
    hybrid_opt_condition = 'HYBRID_OPT==0' if getattr(ds, 'HYBRID_OPT', 0) == 0 else 'HYBRID_OPT!=0'
    vars_to_update = set(
        config.get(f'conditional_cf_attribute_map.{hybrid_opt_condition}').keys()
    ).intersection(set(ds.data_vars))
    for variable in vars_to_update:
        ds[variable].attrs.update(
            config.get(f'conditional_cf_attribute_map.{hybrid_opt_condition}.{variable}')
        )

    return ds


def _collapse_time_dim(ds: xr.Dataset) -> xr.Dataset:

    # This "time dimension collapsing" assumption is wrong with moving nests
    # and should be applied to static, nested domains.
    lat_lon_coords = set(config.get('latitude_coords') + config.get('longitude_coords'))
    vertical_coords = set(config.get('vertical_coords'))
    coords = set(ds.variables).intersection(lat_lon_coords.union(vertical_coords))
    ds = ds.set_coords(coords)

    for coord in ds.coords:
        data_to_reassign = None
        if coord in lat_lon_coords and ds[coord].ndim == 3:
            data_to_reassign = ds[coord].data[0, :, :]
        elif coord in vertical_coords and ds[coord].ndim == 2:
            data_to_reassign = ds[coord].data[0, :]

        if data_to_reassign is not None:
            attrs, encoding = ds[coord].attrs, ds[coord].encoding
            ds = ds.assign_coords({coord: (ds[coord].dims[1:], data_to_reassign)})
            ds[coord].attrs = attrs
            ds[coord].encoding = encoding

    return ds


def _include_projection_coordinates(ds: xr.Dataset) -> xr.Dataset:
    """Introduce projection dimension coordinate values and CRS."""
    try:
        grid_components = _wrf_grid_from_dataset(ds)
    except KeyError:
        warnings.warn(
            'Unable to create coordinate values and CRS due to insufficient dimensions or '
            'projection metadata.'
        )
        return ds
    horizontal_dims = set(config.get('horizontal_dims')).intersection(set(ds.dims))

    # Include dimension coordinates
    for dim in horizontal_dims:
        ds[dim] = (dim, grid_components[dim], config.get(f'cf_attribute_map.{dim}'))

    # Include CRS
    ds['wrf_projection'] = (tuple(), grid_components['crs'], grid_components['crs'].to_cf())
    for varname in ds.data_vars:
        if any(dim in ds[varname].dims for dim in horizontal_dims):
            ds[varname].attrs['grid_mapping'] = 'wrf_projection'

    return ds


def _assign_coord_to_dim_of_different_name(ds: xr.Dataset) -> xr.Dataset:
    for varname, dim in config.get('assign_coord_to_dim_map').items():
        ds[dim] = ds[varname]
        del ds[varname]
    return ds


def _rename_dims(ds: xr.Dataset) -> xr.Dataset:
    """Rename dims for more consistent semantics."""
    rename_dim_map = {k: v for k, v in config.get('rename_dim_map').items() if k in ds.dims}
    return ds.rename(rename_dim_map)
