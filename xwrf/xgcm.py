import xgcm


def to_xgcm(ds):
    """
    Helper function to convert an xwrf dataset to an XGCM grid object
    """
    _required_coords = ['XLAT_M', 'XLAT_C', 'XLONG_M', 'XLONG_C']

    if not set(_required_coords).issubset(list(ds.coords)):
        raise ValueError(f'Missing Required Coordinates: {_required_coords}')

    grid = xgcm.Grid(
        ds,
        coords={
            'X': {'inner': 'XLAT_M', 'outer': 'XLAT_C'},
            'Y': {'inner': 'XLONG_M', 'outer': 'XLONG_C'},
        },
    )
    return grid
