#!/usr/bin/env python3
# flake8: noqa
""" Top-level module. """

from pkg_resources import DistributionNotFound, get_distribution

from .io_plugin import WRFBackendEntrypoint
from .tutorial import open_dataset

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:  # pragma: no cover
    __version__ = 'unknown'  # pragma: no cover
