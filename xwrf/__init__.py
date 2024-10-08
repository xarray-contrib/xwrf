#!/usr/bin/env python3
# flake8: noqa
""" Top-level module. """

from importlib.metadata import PackageNotFoundError, version

from . import postprocess, tutorial
from .accessors import WRFDataArrayAccessor, WRFDatasetAccessor
from .config import config
from .version_report import show_versions

try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    __version__ = 'unknown'  # pragma: no cover
