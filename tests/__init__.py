from __future__ import annotations

import importlib
import typing

import packaging
import pytest


def importorskip(module_name, minversion: str = None) -> typing.Callable:
    try:
        module = importlib.import_module(module_name)
        has = True

        if minversion and packaging.version.parse(module.__version__) < packaging.version.parse(
            minversion
        ):
            raise ValueError(
                f'{module_name} version {module.__version__} is less than {minversion}'
            )
    except (ImportError, ValueError):
        has = False

    return pytest.mark.skipif(
        not has, reason=f'requires {module_name} with minimum version={minversion}'
    )
