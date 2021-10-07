import os
import pathlib
import re
from collections import OrderedDict

import numpy as np
import xarray as xr

_COORD_PAIR_MAP = {
    'XLAT': ('XLAT', 'XLONG'),
    'XLONG': ('XLAT', 'XLONG'),
    'XLAT_M': ('XLAT_M', 'XLONG_M'),
    'XLONG_M': ('XLAT_M', 'XLONG_M'),
    'XLAT_U': ('XLAT_U', 'XLONG_U'),
    'XLONG_U': ('XLAT_U', 'XLONG_U'),
    'XLAT_V': ('XLAT_V', 'XLONG_V'),
    'XLONG_V': ('XLAT_V', 'XLONG_V'),
    'CLAT': ('CLAT', 'CLONG'),
    'CLONG': ('CLAT', 'CLONG'),
}


_COORD_VARS = (
    'XLAT',
    'XLONG',
    'XLAT_M',
    'XLONG_M',
    'XLAT_U',
    'XLONG_U',
    'XLAT_V',
    'XLONG_V',
    'CLAT',
    'CLONG',
)

_LAT_COORDS = ('XLAT', 'XLAT_M', 'XLAT_U', 'XLAT_V', 'CLAT')

_LON_COORDS = ('XLONG', 'XLONG_M', 'XLONG_U', 'XLONG_V', 'CLONG')

_TIME_COORD_VARS = ('XTIME',)


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


def _get_coord_names(ds, varname):
    """Returns a tuple of coordinate names for a given variable."""

    lat_coord = None
    lon_coord = None
    time_coord = None

    # WRF variables will have a coordinates attribute.  MET_EM files have
    # a stagger attribute which indicates the coordinate variable.
    try:
        # WRF files
        coord_attr = getattr(ds[varname], 'coordinates')
    except AttributeError:
        if varname in _COORD_VARS:
            lat_coord, lon_coord = _COORD_PAIR_MAP[varname]
            if 'XTIME' in ds.variables:
                time_coord = 'XTIME'

        elif varname in _TIME_COORD_VARS:
            lat_coord = lon_coord = time_coord = None

        else:
            try:
                # met_em files or old WRF files
                stag_attr = getattr(ds[varname], 'stagger')
            except AttributeError:
                lat_coord = lon_coord = None

                # Let's just check for xlat and xlong in this case
                if 'XLAT' in ds.variables:
                    lat_coord, lon_coord = 'XLAT', 'XLONG'

            else:
                # For met_em files, use the stagger name to get the lat/lon var
                lat_coord = f'XLAT_{stag_attr}'
                lon_coord = f'XLONG_{stag_attr}'

                # If this coord name is missing, it might be an old WRF file
                if lat_coord not in ds.variables:
                    lat_coord = lon_coord = None
                    if 'XLAT' in ds.variables:
                        lat_coord, lon_coord = 'XLAT', 'XLONG'

    else:
        if isinstance(coord_attr, str):
            coord_names = coord_attr.split()
        else:
            coord_names = coord_attr.decode().split()

        for name in coord_names:
            if name in _LAT_COORDS:
                lat_coord = name
                continue
            if name in _LON_COORDS:
                lon_coord = name
                continue
            if name in _TIME_COORD_VARS:
                time_coord = name
                continue

        if time_coord is not None:
            # Make sure the time variable wasn't removed
            try:
                ds.variables[time_coord]
            except KeyError:
                time_coord = None
    return lat_coord, lon_coord, time_coord


def is_time_coord_variable(variable):
    """Returns True if the variable is a time coordinate variable."""
    return variable.name in _TIME_COORD_VARS


class WRFBackendEntrypoint(xr.backends.BackendEntrypoint):
    def build_data_array(self, dataset, varname, multitime=False, timeidx=0):
        variable = dataset[varname]
        time_idx_or_slice = timeidx if not multitime else slice(None)
        if len(variable.shape) > 1:
            data = variable[time_idx_or_slice, :]
        else:
            data = variable[time_idx_or_slice]

        # Want to preserve the time dimension
        if not multitime:
            data = data[np.newaxis, :] if len(variable.shape) > 1 else data[np.newaxis]
        attrs = OrderedDict()
        for key in variable.ncattrs():
            attrs[key] = variable.getncattr(key)

        dims = variable.dimensions[-data.ndim :]

        lat_coord = lon_coord = time_coord = None
        try:
            if dims[-2] == 'south_north' and dims[-1] == 'west_east':
                lat_coord, lon_coord, time_coord = _get_coord_names(dataset, varname)
        except IndexError:
            pass

        coords = OrderedDict()

        # Handle lat/lon coordinates and projection information if available
        if lon_coord is not None and lat_coord is not None:
            lon_variable = dataset.variables[lon_coord]
            lat_variable = dataset.variables[lat_coord]
            lon_coord_dims = lon_variable.dimensions
            lat_coord_dims = lat_variable.dimensions

            if time_coord is not None:
                coords[time_coord] = dataset.variables[time_coord][:]

            coords[lon_coord] = lon_coord_dims[1:], lon_variable[:][0, :]
            coords[lat_coord] = lat_coord_dims[1:], lat_variable[:][0, :]

        result = xr.DataArray(variable, attrs=attrs, dims=dims)
        result = result.assign_coords(coords)
        return result

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
        arrays = [self.build_data_array(store.ds, varname) for varname in store.ds.variables.keys()]
        filtered_arrays = list(filter(lambda x: x.name not in _COORD_VARS, arrays))

        return xr.merge(filtered_arrays).squeeze()
