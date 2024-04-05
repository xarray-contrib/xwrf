"""Provide grid-related functionality specific to WRF datasets.
This submodule contains code reused with modification from Salem under the terms of the BSD
3-Clause License. Salem is Copyright (c) 2014-2021, Fabien Maussion and Salem Development Team All
rights reserved.
"""

from __future__ import annotations  # noqa: F401

from typing import Hashable, Mapping

import numpy as np
import pyproj
import xarray as xr

# Default CRS (lon/lat on WGS84, which is EPSG:4326)
wgs84 = pyproj.CRS(4326)


def _wrf_grid_from_dataset(ds: xr.Dataset) -> Mapping[Hashable, pyproj.CRS | np.ndarray]:
    """Get the WRF projection and dimension coordinates out of the file."""

    # Use standards from a typical WRF file
    cen_lon = ds.CEN_LON
    cen_lat = ds.CEN_LAT
    dx = ds.DX
    dy = ds.DY
    proj_id = ds.MAP_PROJ

    pargs = {
        'x_0': 0,
        'y_0': 0,
        'a': 6370000,
        'b': 6370000,
        'lat_1': ds.TRUELAT1,
        'lat_2': getattr(ds, 'TRUELAT2', ds.TRUELAT1),
        'lat_0': ds.MOAD_CEN_LAT,
        'lon_0': ds.STAND_LON,
        'center_lon': cen_lon,
    }

    if proj_id == 0:
        # Idealized Run, Cartesian grid
        pass
    elif proj_id == 1:
        # Lambert
        pargs['proj'] = 'lcc'
        del pargs['center_lon']
    elif proj_id == 2:
        # Polar stereo
        pargs['proj'] = 'stere'
        pargs['lat_ts'] = pargs['lat_1']
        pargs['lat_0'] = 90.0
        del pargs['lat_1'], pargs['lat_2'], pargs['center_lon']
    elif proj_id == 3:
        # Mercator
        pargs['proj'] = 'merc'
        pargs['lat_ts'] = pargs['lat_1']
        pargs['lon_0'] = pargs['center_lon']
        del pargs['lat_0'], pargs['lat_1'], pargs['lat_2'], pargs['center_lon']
    else:
        raise NotImplementedError(f'WRF proj not implemented yet: {proj_id}')

    if proj_id == 0:
        # As this is an idealized run, there is no physical CRS
        crs = None
        e, n = cen_lon, cen_lat
    else:
        # Construct the pyproj CRS (letting errors fail through)
        crs = pyproj.CRS(pargs)

        # Get grid specifications
        trf = pyproj.Transformer.from_crs(wgs84, crs, always_xy=True)
        e, n = trf.transform(cen_lon, cen_lat)

    nx = ds.sizes['west_east']
    ny = ds.sizes['south_north']
    x0 = -(nx - 1) / 2.0 * dx + e  # DL corner
    y0 = -(ny - 1) / 2.0 * dy + n  # DL corner

    return {
        'crs': crs,
        'south_north': y0 + np.arange(ny) * dy,
        'west_east': x0 + np.arange(nx) * dx,
        'south_north_stag': y0 + (np.arange(ny + 1) - 0.5) * dy,
        'west_east_stag': x0 + (np.arange(nx + 1) - 0.5) * dx,
    }
