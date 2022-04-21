from __future__ import annotations

import importlib
import typing

import packaging
import pytest


def importorskip(module_name, minversion: str = None) -> typing.Callable:
    try:
        module = importlib.import_module(module_name)

        if minversion and packaging.version.parse(module.__version__) < packaging.version.parse(
            minversion
        ):
            raise ValueError(
                f'{module_name} version {module.__version__} is less than {minversion}'
            )

    except ImportError:
        skip = True
        reason = f'could not import optional module {module_name}'

    except ValueError as err:
        skip = True
        reason = str(err)

    except:
        skip = True
        reason = f'failure in optional module {module_name}'

    else:
        skip = False
        reason = ''

    return pytest.mark.skipif(skip, reason=reason)
