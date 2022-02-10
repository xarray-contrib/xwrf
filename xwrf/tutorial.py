"""
Useful for:
* users learning xwrf
* building tutorials in the documentation.
"""
from __future__ import annotations  # noqa: F401

import os
import pathlib

import xarray as xr

_default_cache_dir_name = 'xwrf_tutorial_data'
base_url = 'https://github.com/ncar-xdev/xwrf-data'
version = 'main'


def _construct_cache_dir(path):
    import pooch

    if isinstance(path, os.PathLike):
        path = os.fspath(path)
    elif path is None:
        path = pooch.os_cache(_default_cache_dir_name)

    return path


sample_datasets = {
    'dummy': 'data/dummy.nc',
    'dummy_attrs_only': 'data/dummy_attrs_only.nc',
    'polar_stereographic_1': 'data/geo_em_d01_polarstereo.nc',
    'polar_stereographic_2': 'data/geo_em_d02_polarstereo.nc',
    'lambert_conformal': 'data/lambert_conformal_sample.nc',
    'mercator': 'data/mercator_sample.nc',
    'tiny': 'data/tiny.nc',
}


# idea borrowed from Seaborn and Xarray
def open_dataset(
    name,
    cache=True,
    cache_dir=None,
    *,
    engine='netcdf4',
    **kws,
):
    """
    Open a dataset from the online repository (requires internet).
    If a local copy is found then always use that to avoid network traffic.
    Available datasets:
    * ``""``:
    Parameters
    """
    try:
        import pooch
    except ImportError as e:
        raise ImportError(
            'tutorial.open_dataset depends on pooch to download and manage datasets.'
            ' To proceed please install pooch.'
        ) from e

    logger = pooch.get_logger()
    logger.setLevel('WARNING')

    cache_dir = _construct_cache_dir(cache_dir)
    try:
        path = sample_datasets[name]
    except KeyError as exc:
        raise KeyError(
            f'{name} is not a valid dataset name. Valid names include: {list(sample_datasets.keys())}.'
        ) from exc
    url = f'{base_url}/raw/{version}/{path}'

    # retrieve the file
    filepath = pooch.retrieve(url=url, known_hash=None, path=cache_dir)
    ds = xr.open_dataset(filepath, engine=engine, **kws)
    if not cache:
        ds = ds.load()
        pathlib.Path(filepath).unlink()

    return ds


def load_dataset(*args, **kwargs):
    """
    Open, load into memory, and close a dataset from the online repository
    (requires internet)
    """
    with open_dataset(*args, **kwargs) as ds:
        return ds.load()
