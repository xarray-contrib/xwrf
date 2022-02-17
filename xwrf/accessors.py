from __future__ import annotations  # noqa: F401

import xarray as xr

from .postprocess import (
    _assign_coord_to_dim_of_different_name,
    _collapse_time_dim,
    _decode_times,
    _include_projection_coordinates,
    _make_units_pint_friendly,
    _modify_attrs_to_cf,
    _rename_dims,
)


class WRFAccessor:
    """
    Common Dataset and DataArray accessor functionality.
    """

    def __init__(self, xarray_obj: xr.Dataset | xr.DataArray) -> WRFAccessor:
        self.xarray_obj = xarray_obj


@xr.register_dataarray_accessor('xwrf')
class WRFDataArrayAccessor(WRFAccessor):
    """Adds a number of WRF specific methods to xarray.DataArray objects."""


@xr.register_dataset_accessor('xwrf')
class WRFDatasetAccessor(WRFAccessor):
    """Adds a number of WRF specific methods to xarray.Dataset objects."""

    def postprocess(self, decode_times=True) -> xr.Dataset:
        """
        Postprocess the dataset.

        Returns
        -------
        xarray.Dataset
            The postprocessed dataset.
        """
        ds = (
            self.xarray_obj.pipe(_modify_attrs_to_cf)
            .pipe(_make_units_pint_friendly)
            .pipe(_collapse_time_dim)
            .pipe(_include_projection_coordinates)
            .pipe(_assign_coord_to_dim_of_different_name)
        )
        if decode_times:
            ds = ds.pipe(_decode_times)

        return ds.pipe(_rename_dims)
