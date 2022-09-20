---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.0
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

# Destaggering and vertically interpolating `dask` data using `xgcm`

+++

In this tutorial, we will show you how to leverage the `xWRF` accessors and the `xWRF`-provided [COMODO](https://web.archive.org/web/20160417032300/http://pycomodo.forge.imag.fr/norm.html)-compliant attributes in order to destagger the WRF output and interpolate it vertically using [`dask`](https://docs.dask.org/en/stable/) and [`xgcm`](https://xgcm.readthedocs.io/en/latest/).

+++

## Loading the data

+++

First of all, we load the data and use the simple `.xwrf.postprocess()` API and [`dask`](https://docs.dask.org/en/stable/)-enable the dataset by passing `open_dataset` the `chunkgs` kwarg. In a real-world scenario, you might want to spawn a [Cluster](https://distributed.dask.org/en/stable/api.html#cluster) in order to speed up calculations.

```{code-cell} ipython3
import xwrf
ds = xwrf.tutorial.open_dataset("wrfout", chunks='auto').xwrf.postprocess()
ds
```

+++ {"tags": []}

## Destaggering

+++

If we naively try to calculate the wind speed from the `U` and `V` components, we get an error due to them having different shapes.

```{code-cell} ipython3
:tags: [raises-exception]

from metpy.calc import wind_speed

wind_speed(ds.U, ds.V)
```

Upon investigating the wind components, we can see that they are defined on the [`WRF`](https://www.mmm.ucar.edu/weather-research-and-forecasting-model)-internal Arakawa-C grid, which causes the shapes to differ.

```{code-cell} ipython3
ds.U.sizes, ds.V.sizes
```

Destaggering is done in no time at all using the handy `.xwrf` accessor. We can now decide whether to destagger the whole `Dataset`...

```{code-cell} ipython3
destaggered = ds.xwrf.destagger().metpy.quantify()
destaggered['wind_speed'] = wind_speed(destaggered.U, destaggered.V)
destaggered.wind_speed
```

... or whether we just want to destagger the two individual `DataArrays`.

```{code-cell} ipython3
ds = ds.metpy.quantify()
wind_speed(ds.U.xwrf.destagger(), ds.V.xwrf.destagger())
```

## Vertical interpolation using `xgcm`

+++

We have now calculated the wind speed for the whole model domain. However, the z-layers are still in the native WRF sigma coordinate, which is of no practical use to us. So, in order to be able to analyze this data properly, we have to interpolate it onto pressure levels.

But, since `xWRF` prepared the dataset with the appropriate [COMODO](https://web.archive.org/web/20160417032300/http://pycomodo.forge.imag.fr/norm.html) (and `units`) attributes, we can simply use [`xgcm`](https://xgcm.readthedocs.io/en/latest/grids.html) with its `Grid.transform` function to solve this problem! However, since it doesn't understand units yet, we have to work around it a bit:

```{code-cell} ipython3
import xgcm
import numpy as np
import pint_xarray

target_levels = np.array([250.]) # in hPa
air_pressure = destaggered.air_pressure.pint.to('hPa').metpy.dequantify()

grid = xgcm.Grid(destaggered, periodic=False)
_wind_speed = grid.transform(destaggered.wind_speed.metpy.dequantify(), 'Z', target_levels, target_data=air_pressure, method='log')
_wind_speed = _wind_speed.compute()
```

Finally, we can plot the result using [`hvplot`](https://hvplot.holoviz.org/).

```{code-cell} ipython3
import hvplot.xarray

_wind_speed.hvplot.quadmesh(
    x='XLONG',
    y='XLAT',
    title='Wind speed at 250 hPa',
    geo=True,
    project=True,
    alpha=0.9,
    cmap='inferno',
    clim=(_wind_speed.min().item(), _wind_speed.max().item()),
    clabel='wind speed [m/s]',
    tiles='OSM',
    dynamic=False
)
```
