---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.13.8
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

# Treating the WRF grid with `xgcm`

+++

In this tutorial, we will show you how to leverage the xWRF-provided [COMODO](https://web.archive.org/web/20160417032300/http://pycomodo.forge.imag.fr/norm.html)-compliant attributes with `xgcm` in order to destagger the [WRF](https://www.mmm.ucar.edu/weather-research-and-forecasting-model) output.

+++

## Loading the data

+++

First of all, we load the data and use the simple `.xwrf.postprocess()` API.

```{code-cell} ipython3
import xwrf

ds = xwrf.tutorial.open_dataset("wrfout").xwrf.postprocess()
ds
```

If we naively try to calculate the wind speed from the `U` and `V` components, we get an error due to them having different shapes.

```{code-cell} ipython3
:tags: [raises-exception]

from metpy.calc import wind_speed

wind_speed(ds.U, ds.V)
```

Upon investigating the wind components (here `U`), we can see that they are defined on the [WRF](https://www.mmm.ucar.edu/weather-research-and-forecasting-model)-internal Arakawa-C grid, which causes the shapes to differ.

```{code-cell} ipython3
ds.U
```

## Destaggering the WRF grid

+++

But, since xWRF prepared the dataset with the appropriate [COMODO](https://web.archive.org/web/20160417032300/http://pycomodo.forge.imag.fr/norm.html) (and `units`) attributes, we can simply use [`xgcm`](https://xgcm.readthedocs.io/en/latest/grids.html) to solve this problem!

```{code-cell} ipython3
from xgcm import Grid


def interp_and_keep_attrs(grid, da, axis):
    _attrs = da.attrs
    da = grid.interp(da, axis=axis)
    da.attrs = _attrs
    return da


grid = Grid(ds)
ds['U'], ds['V'] = interp_and_keep_attrs(grid, ds.U, 'X'), interp_and_keep_attrs(grid, ds.V, 'Y')
wind_speed(ds.U, ds.V)
```
