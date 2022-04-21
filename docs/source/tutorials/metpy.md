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

# Using `metpy` for WRF analysis

+++

In this tutorial, we will show you how xWRF enables a seamless integration of [WRF](https://www.mmm.ucar.edu/weather-research-and-forecasting-model) data with [`metpy`](https://unidata.github.io/MetPy/latest/). In the end, we will have a skewT plot at a lat-lon location in the simulation domain. Much of this tutorial was adapted from [`metpy`](https://unidata.github.io/MetPy/latest/tutorials/upperair_soundings.html).

+++

## Loading the data

+++

First of all, we load the data and use the simple `.xwrf.postprocess()` API.

```{code-cell} ipython3
import xwrf

ds = xwrf.tutorial.open_dataset("wrfout").xwrf.postprocess()
ds
```

## Sampling

+++

Then, we sample the dataset at the desired location using `pyproj`. I selected the German Weather Service station at Mannheim, which is close to the middle of the simulation domain.

```{code-cell} ipython3
import numpy as np
from pyproj import Transformer, CRS


def sample_wrf_ds_at_latlon(ds, lat, long):
    trf = Transformer.from_crs(CRS.from_epsg(4326), ds.wrf_projection.item(), always_xy=True)
    x, y = ([var] if np.isscalar(var) else var for var in trf.transform(long, lat))
    return ds.interp(x=x, y=y, x_stag=x, y_stag=y)
```

```{code-cell} ipython3
ds = sample_wrf_ds_at_latlon(ds, 49.5091090731333, 8.553966628049963)
ds
```

## Computation of desired quantities

+++

Now we have to compute the quantities [`metpy`](https://unidata.github.io/MetPy/latest/) uses for the skewT. For that we have to first quantify the [WRF](https://www.mmm.ucar.edu/weather-research-and-forecasting-model) data and then convert the data to the desired units.

```{code-cell} ipython3
import metpy
import metpy.calc as mpcalc
import pint_xarray


ds = ds.metpy.quantify()
ds['dew_point_temperature'] = mpcalc.dewpoint(
    mpcalc.vapor_pressure(ds.air_pressure, ds.QVAPOR)
).pint.to("degC")
ds['air_temperature'] = mpcalc.temperature_from_potential_temperature(
    ds.air_pressure, ds.air_potential_temperature
).pint.to("degC")
ds['air_pressure'] = ds.air_pressure.pint.to("hPa")
```

## Plotting

+++

Finally, we can create the skew-T plot using the computed quantities.

```{code-cell} ipython3
import matplotlib.pyplot as plt
from metpy.plots import SkewT

# Create a new figure. The dimensions here give a good aspect ratio
fig = plt.figure(figsize=(9, 9))
skew = SkewT(fig)

# Make the dimensions of the data palatable to metpy
if len(ds.dims) > 1:
    ds = ds.isel(x=0, x_stag=0, y=0, y_stag=0)

# Plot the data using normal plotting functions, in this case using
# log scaling in Y, as dictated by the typical meteorological plot
skew.plot(ds.air_pressure, ds.air_temperature, 'r', linewidth=2, label='Temperature')
skew.plot(
    ds.air_pressure, ds.dew_point_temperature, 'g', linewidth=2, label='Dew Point Temperature'
)
skew.plot_barbs(ds.air_pressure, ds.U, ds.V)

# Make the plot a bit prettier
plt.xlim([-50, 30])
plt.xlabel('Temperature [C]')
plt.ylabel('Pressure [hPa]')
plt.legend().set_zorder(1)

# Show the plot
plt.show()
```
