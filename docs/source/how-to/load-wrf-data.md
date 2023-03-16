# Load WRF data

As an `xarray` accessor, xWRF builds on top of the `xarray` data structures.
Therefore, loading WRF data is as easy as the following:

```python
import xarray as xr
import xwrf

ds = xr.open_mfdataset(
        "./wrfout_d01*",
        engine="netcdf4",
        concat_dim="Time",
        combine="nested",
    ).xwrf.postprocess()
```

At the moment, xWRF aims to support `met_em`, `wrfinput`, `wrfbdy` and `wrfout` files.
Should there be some problems with either, please open an [issue](https://github.com/xarray-contrib/xwrf/issues/new?assignees=&labels=bug%2Ctriage&template=bugreport.yml&title=%5BBug%5D%3A+).
