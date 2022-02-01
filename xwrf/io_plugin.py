import itertools
import os
import pathlib
import re
import warnings

import pandas as pd
import xarray as xr

from .config import config

_LAT_COORDS = ('XLAT', 'XLAT_M', 'XLAT_U', 'XLAT_V', 'CLAT', 'XLAT_C')

_LON_COORDS = ('XLONG', 'XLONG_M', 'XLONG_U', 'XLONG_V', 'CLONG', 'XLONG_C')

_TIME_COORD_VARS = ('XTIME', 'Times', 'Time', 'time')

_ALL_COORDS = set(itertools.chain(*[_LAT_COORDS, _LON_COORDS, _TIME_COORD_VARS]))

_BOOLEAN_UNITS_ATTRS = ('-', 'flag')


def is_remote_uri(path: str) -> bool:
    """Finds URLs of the form protocol:// or protocol::
    This also matches for http[s]://, which were the only remote URLs
    supported in <=v0.16.2.
    """
    return bool(re.search(r'^[a-z][a-z0-9]*(\://|\:\:)', path))


def _normalize_path(path):
    if isinstance(path, pathlib.Path):
        path = str(path)

    if isinstance(path, str) and not is_remote_uri(path):
        path = os.path.abspath(os.path.expanduser(path))

    return path


def clean(dataset):
    """
    Clean up the dataset.
    """
    coords = set(dataset.variables).intersection(_ALL_COORDS)
    dataset = dataset.set_coords(coords)
    for coord in dataset.coords:
        attrs = dataset[coord].attrs
        encoding = dataset[coord].encoding
        if coord in _TIME_COORD_VARS:
            try:
                dataset[coord].data = pd.to_datetime(
                    list(map(lambda x: x.decode('utf-8'), dataset[coord].data.tolist())),
                    format='%Y-%m-%d_%H:%M:%S',
                )
            except:
                warnings.warn(f'Failed to parse time coordinate: {coord}', stacklevel=2)

        elif coord in (_LON_COORDS + _LAT_COORDS) and dataset[coord].ndim == 3:

            attrs = dataset[coord].attrs
            encoding = dataset[coord].encoding
            dataset = dataset.assign_coords(
                {coord: (dataset[coord].dims[1:], dataset[coord].data[0, :, :])}
            )
        dataset[coord].attrs = attrs
        dataset[coord].encoding = encoding

    return dataset


def make_units_quantify_ready(dataset):
    for var in dataset.data_vars:
        if dataset[var].attrs.get('units') in _BOOLEAN_UNITS_ATTRS:
            dataset[var].attrs.pop('units', None)


def modify_attrs_to_cf(dataset):
    vars_to_update = set(config.get('cf_attribute_map').keys()).intersection(set(dataset.keys()))

    for var in vars_to_update:
        dataset[var].attrs.update(config.get(f'cf_attribute_map.{var}'))


class WRFBackendEntrypoint(xr.backends.BackendEntrypoint):
    def open_dataset(
        self,
        filename_or_obj,
        mask_and_scale=True,
        decode_times=True,
        concat_characters=True,
        decode_coords=True,
        drop_variables=None,
        use_cftime=None,
        decode_timedelta=None,
        group=None,
        mode='r',
        format='NETCDF4',
        clobber=True,
        diskless=False,
        persist=False,
        lock=None,
        autoclose=False,
    ):

        filename_or_obj = _normalize_path(filename_or_obj)
        store = xr.backends.NetCDF4DataStore.open(
            filename_or_obj,
            mode=mode,
            format=format,
            clobber=clobber,
            diskless=diskless,
            persist=persist,
            lock=lock,
            autoclose=autoclose,
        )

        store_entrypoint = xr.backends.store.StoreBackendEntrypoint()

        with xr.core.utils.close_on_error(store):
            dataset = store_entrypoint.open_dataset(
                store,
                mask_and_scale=mask_and_scale,
                decode_times=decode_times,
                concat_characters=concat_characters,
                decode_coords=decode_coords,
                drop_variables=drop_variables,
                use_cftime=use_cftime,
                decode_timedelta=decode_timedelta,
            )

        make_units_quantify_ready(dataset)
        modify_attrs_to_cf(dataset)
        return clean(dataset)
