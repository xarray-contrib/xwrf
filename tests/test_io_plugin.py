import xarray as xr


def test_plugin():
    engines = xr.backends.list_engines()
    for item in ['wrf', 'xwrf']:
        entrypoint = engines[item]
        assert entrypoint.__module__ == 'xwrf.io_plugin'
