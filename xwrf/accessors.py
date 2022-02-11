from __future__ import annotations  # noqa: F401

import xarray as xr

from .postprocess import _decode_times, _modify_attrs_to_cf, _remove_units_from_bool_arrays


class WRFAccessor:
    """
    Common Dataset and DataArray accessor functionality.
    """

    def __init__(self, xarray_obj: xr.Dataset | xr.DataArray) -> WRFAccessor:
        self.xarray_obj = xarray_obj


@xr.register_dataarray_accessor('wrf')
@xr.register_dataarray_accessor('xwrf')
class WRFDataArrayAccessor(WRFAccessor):
    """Adds a number of WRF specific methods to xarray.DataArray objects."""


@xr.register_dataset_accessor('wrf')
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
        ds = self.xarray_obj.pipe(_modify_attrs_to_cf).pipe(_remove_units_from_bool_arrays)
        if decode_times:
            ds = ds.pipe(_decode_times)

        return ds
