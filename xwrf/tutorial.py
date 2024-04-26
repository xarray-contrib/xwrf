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
base_url = 'https://github.com/xarray-contrib/xwrf-data'
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
    'dummy_salem_parsed': 'data/dummy_salem_parsed.nc',
    'polar_stereographic_1': 'data/geo_em_d01_polarstereo.nc',
    'polar_stereographic_2': 'data/geo_em_d02_polarstereo.nc',
    'lambert_conformal': 'data/lambert_conformal_sample.nc',
    'mercator': 'data/mercator_sample.nc',
    'tiny': 'data/tiny.nc',
    'met_em_sample': 'data/met_em.d01.2005-08-28_12:00:00.nc',
    'wrfout': 'data/wrfout_d01_2099-10-01_00:00:00.nc',
    'ideal': 'data/ideal.nc',
}


# idea borrowed from Seaborn and Xarray
def open_dataset(
    name: str,
    cache: bool = True,
    cache_dir: str | pathlib.Path = None,
    *,
    engine: str = 'netcdf4',
    **kws,
) -> xr.Dataset:
    """
    Open a dataset from the online repository (requires internet).
    If a local copy is found then always use that to avoid network traffic.

    Available datasets:

    * ``"dummy"``
    * ``"dummy_attrs_only"``
    * ``"dummy_salem_parsed"``
    * ``"polar_stereographic_1"``
    * ``"polar_stereographic_2"``
    * ``"lambert_conformal"``
    * ``"mercator"``
    * ``"met_em_sample"``
    * ``"wrfout"``
    * ``"ideal"``

    Parameters
    ----------
    name : str
        Name of the dataset.
        e.g. 'mercator'
    cache : bool, optional
        If True, then cache data locally for use on subsequent calls
    cache_dir : path-like, optional
        The directory in which to search for and write cached data.
    engine : str, optional
        Name of the backend engine to use.
    **kws : dict, optional
        Additional keyword arguments passed through to the :py:func:`~xarray.open_dataset` function.

    Returns
    -------
    xarray.Dataset
        The dataset.
    """

    try:
        import pooch
    except ImportError as e:
        raise ImportError(
            'tutorial.open_dataset depends on pooch to download and manage datasets.'
            ' To proceed please install pooch using:'
            ' `python -m pip install pooch` or `conda install -c conda-forge pooch`.'
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


def load_dataset(*args, **kwargs) -> xr.Dataset:
    """
    Open, load into memory, and close a dataset from the online repository
    (requires internet)
    """
    with open_dataset(*args, **kwargs) as ds:
        return ds.load()
