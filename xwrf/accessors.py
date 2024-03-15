from __future__ import annotations  # noqa: F401

import xarray as xr

from .destagger import _destag_variable, _rename_staggered_coordinate
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

    def destagger(
        self,
        stagger_dim: str | None = None,
        unstaggered_dim_name: str | None = None,
        exclude_staggered_auxiliary_coords: bool = False,
    ) -> xr.DataArray:
        """
        Destagger a single WRF xarray.DataArray

        Parameters
        ----------
        stagger_dim : str, optional
            Name of dimension to unstagger. Defaults to guessing based on name (ends in "_stag")
        unstaggered_dim_name : str, optional
            String to which to rename the dimension after destaggering. Example would be
            "west_east" for "west_east_stag". By default the dimenions will be renamed the text in
            front of "_stag" from the "stagger_dim" field.
        exclude_staggered_auxiliary_coords : bool, optional
            If True, auxiliary coordinates (such as latitude and longitude) that originally include
            staggered dimensions are excluded from being destaggered along with this DataArray's
            data. If False, auxiliary coordinates are destaggered in the same fashion as the data
            (average of cell boundary values), which may introduce error in comparison to the
            analogous non-staggered coordinates from the original WRF data. Defaults to False.

        Returns
        -------
        xarray.DataArray
            The destaggered DataArray with renamed dimension and adjusted coordinates.

        Notes
        -----
        While destaggered coordinate variables are made available by default
        (exclude_staggered_auxiliary_coords=False), these are approximations made from the
        staggered coordinate values and may not be sufficiently accurate for all grid projections
        and/or use cases. For full accuracy, auxiliary coordinates should be re-computed from
        dimension coordinates or obtained from the original dataset.
        """
        new_variable = _destag_variable(
            self.xarray_obj.variable, stagger_dim=stagger_dim, unstag_dim_name=unstaggered_dim_name
        )

        # Need to recalculate staggered coordinates, as they don't already exist independently
        # in a DataArray context
        new_coords = {}
        for coord_name, coord_data in self.xarray_obj.coords.items():
            if set(coord_data.dims).difference(set(new_variable.dims)):
                # Has a dimension not in the destaggered output (and so still staggered)
                new_name = _rename_staggered_coordinate(
                    coord_name, stagger_dim=stagger_dim, unstag_dim_name=unstaggered_dim_name
                )
                if not exclude_staggered_auxiliary_coords or new_name in new_variable.dims:
                    # Skip if excluding and this isn't a dimension coordinate of output
                    new_coords[new_name] = _destag_variable(
                        coord_data.variable,
                        stagger_dim=stagger_dim,
                        unstag_dim_name=unstaggered_dim_name,
                    )
            else:
                new_coords[coord_name] = coord_data.variable

        return xr.DataArray(new_variable, coords=new_coords)


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
            Calculates essential diagnostic variables (potential temperature, air pressure,
            geopotential, and geopotential height) that are otherwise only present in wrfout files
            as split components or dependent upon special adjustments. Also calculates earth-relative
            wind fields, as winds by default are grid-relative. Defaults to True. If the
            underlying fields on which any of these calculated fields depends is missing, that
            calculated variable is skipped. These will be eagerly evalulated, unless your data has
            been chunked with Dask, in which case these fields will also be Dask arrays.
        drop_diagnostic_variable_components : bool, optional
            Determine whether to drop the underlying fields used to calculate the diagnostic
            variables. Defaults to True. Never drops grid-relative wind fields.

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

    def destagger(self, staggered_to_unstaggered_dims: dict[str, str] | None = None) -> xr.Dataset:
        """
        Destagger all data variables in a WRF xarray.Dataset

        Parameters
        ----------
        staggered_to_unstaggered_dims : dict, optional
            Mapping of target staggered dimensions to corresponding unstaggered dimensions

        Returns
        -------
        xarray.Dataset
            The destaggered dataset.

        Notes
        -----
        Does not alter coordinates, only data variables. Staggered coordinates will remain on the
        dataset, but will not be associated with any data variables.
        """
        staggered_dims = (
            {dim for dim in self.xarray_obj.dims if dim.endswith('_stag')}
            if staggered_to_unstaggered_dims is None
            else set(staggered_to_unstaggered_dims)
        )
        new_data_vars = {}
        for var_name, var_data in self.xarray_obj.data_vars.items():
            if this_staggered_dims := set(var_data.dims).intersection(staggered_dims):
                # Found a staggered dim
                # TODO: should we raise an error if somehow end up with more than just one
                # staggered dim, or just pick one from the set like below?
                this_staggered_dim = this_staggered_dims.pop()
                new_data_vars[var_name] = _destag_variable(
                    var_data.variable,
                    stagger_dim=this_staggered_dim,
                    unstag_dim_name=(
                        None
                        if staggered_to_unstaggered_dims is None
                        else staggered_to_unstaggered_dims[this_staggered_dim]
                    ),
                )
            else:
                # No staggered dims
                new_data_vars[var_name] = var_data.variable

        return xr.Dataset(new_data_vars, self.xarray_obj.coords, self.xarray_obj.attrs)
