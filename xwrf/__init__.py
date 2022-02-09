#!/usr/bin/env python3
# flake8: noqa
""" Top-level module. """

from pkg_resources import DistributionNotFound, get_distribution
from . import config
from .accessors import WRFDataArrayAccessor, WRFDatasetAccessor
from . import tutorial
from .io_plugin import WRFBackendEntrypoint

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:  # pragma: no cover
    __version__ = 'unknown'  # pragma: no cover
