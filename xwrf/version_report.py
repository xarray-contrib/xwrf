from __future__ import annotations

import importlib
import locale
import os
import pathlib
import platform
import struct
import subprocess
import sys


def get_sys_info() -> dict[str, str]:
    """Returns system information as a dict"""

    # get full commit hash
    commit = None
    if pathlib.Path('.git').is_dir() and pathlib.Path('xwrf').is_dir():
        try:
            pipe = subprocess.Popen(
                'git log --format="%H" -n 1'.split(' '),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            so, _ = pipe.communicate()
        except Exception:
            pass
        else:
            if pipe.returncode == 0:
                commit = so
                try:
                    commit = so.decode('utf-8')
                except ValueError:
                    pass
                commit = commit.strip().strip('"')

    blob = [('xWRF commit', commit)]
    try:
        (sysname, _nodename, release, _version, machine, processor) = platform.uname()
        blob.extend(
            [
                ('python', sys.version),
                ('python-bits', struct.calcsize('P') * 8),
                ('OS', f'{sysname}'),
                ('OS-release', f'{release}'),
                ('machine', f'{machine}'),
                ('processor', f'{processor}'),
                ('byteorder', f'{sys.byteorder}'),
                ('LC_ALL', f'{os.environ.get("LC_ALL", "None")}'),
                ('LANG', f'{os.environ.get("LANG", "None")}'),
                ('LOCALE', f'{locale.getlocale()}'),
            ]
        )
    except Exception:
        pass

    return blob


def show_versions(as_dict: bool = False) -> None | dict[str, str]:
    """Print out versions of xwrf and its dependencies"""
    packages = [
        ('xwrf', lambda mod: mod.__version__),
        ('xarray', lambda mod: mod.__version__),
        ('numpy', lambda mod: mod.__version__),
        ('pandas', lambda mod: mod.__version__),
        ('matplotlib', lambda mod: mod.__version__),
        ('dask', lambda mod: mod.__version__),
        ('netCDF4', lambda mod: mod.__version__),
        ('donfig', lambda mod: mod.__version__),
        ('xgcm', lambda mod: mod.__version__),
        ('pyproj', lambda mod: mod.__version__),
        ('metpy', lambda mod: mod.__version__),
        ('cf_xarray', lambda mod: mod.__version__),
        ('pint', lambda mod: mod.__version__),
        ('pooch', lambda mod: mod.__version__),
    ]

    packages_blob = {}
    for modname, version_func in packages:
        try:
            if modname in sys.modules:
                mod = sys.modules[modname]
            else:
                mod = importlib.import_module(modname)
        except Exception:
            packages_blob[modname] = None

        else:
            try:
                version = version_func(mod)
                packages_blob[modname] = version
            except Exception:
                packages_blob[modname] = 'installed'
    sys_info = get_sys_info()
    packages_info = sorted(packages_blob.items())
    print('\nSystem Information')
    print('------------------')
    print('\n'.join(f'{key:<12}: {value}' for (key, value) in sys_info))
    print('\nInstalled Python Packages')
    print('-------------------------')
    print('\n'.join(f'{modname:<12}: {version}' for (modname, version) in packages_info))

    if as_dict:
        return {'sys_info': sys_info, 'packages_info': packages_blob}
