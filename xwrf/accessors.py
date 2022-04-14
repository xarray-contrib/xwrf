from __future__ import annotations  # noqa: F401

import xarray as xr

from .postprocess import (
    _assign_coord_to_dim_of_different_name,
    _calc_base_diagnostics,
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

    def postprocess(
        self,
        decode_times: bool = True,
        calculate_diagnostic_variables: bool = True,
        drop_diagnostic_variable_components: bool = True,
    ) -> xr.Dataset:
        """
        Postprocess the dataset. This method will perform the following operations:

        - Rename dimensions to match the CF conventions.
        - Rename variables to match the CF conventions.
        - Rename variable attributes to match the CF conventions.
        - Convert units to Pint-friendly units.
        - Decode times.
        - Include projection coordinates.
        - Collapse time dimension.

        Parameters
        ----------
        decode_times : bool, optional
            Decode the string-like wrfout times to xarray-friendly Pandas types. Defaults to True.
        calculate_diagnostic_variables : bool, optional
            Calculate four essential diagnostic variables (potential temperature, air pressure,
            geopotential, and geopotential height) that are otherwise only present in wrfout files
            as split components or dependent upon special adjustments. Defaults to True. If the
            underlying fields on which any of these calculated fields depends is missing, that
            calculated variable is skipped. These will be eagerly evalulated, unless your data has
            been chunked with Dask, in which case these fields will also be Dask arrays.
        drop_diagnostic_variable_components : bool, optional
            Determine whether to drop the underlying fields used to calculate the diagnostic
            variables. Defaults to True.

        Returns
        -------
        xarray.Dataset
            The postprocessed dataset.
        """
        ds = (
            self.xarray_obj.pipe(_modify_attrs_to_cf)
            .pipe(_make_units_pint_friendly)
            .pipe(_collapse_time_dim)
            .pipe(_assign_coord_to_dim_of_different_name)
        )
        if decode_times:
            ds = ds.pipe(_decode_times)
        if calculate_diagnostic_variables:
            ds = ds.pipe(_calc_base_diagnostics, drop=drop_diagnostic_variable_components)

        ds = ds.pipe(_include_projection_coordinates)

        return ds.pipe(_rename_dims)
