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

# Using `metpy` for WRF analysis

+++

In this tutorial, we will show you how `xWRF` enables a seamless integration of [`WRF`](https://www.mmm.ucar.edu/weather-research-and-forecasting-model) data with [`metpy`](https://unidata.github.io/MetPy/latest/). In the end, we will have a Skew-T plot at a lat-lon location in the simulation domain. Much of this tutorial was adapted from [`metpy`](https://unidata.github.io/MetPy/latest/tutorials/upperair_soundings.html).

+++

## Loading the data

+++

First of all, we load the data and use a simple `.xwrf.postprocess()` call.

```{code-cell} ipython3
import xwrf

ds = xwrf.tutorial.open_dataset("wrfout").xwrf.postprocess()
ds
```

## Sampling

+++

Then, we sample the dataset at the desired location using `pyproj`. Let's use San Francisco for now.

```{code-cell} ipython3
import numpy as np
from pyproj import Transformer, CRS


def sample_wrf_ds_at_latlon(ds, lat, long):
    trf = Transformer.from_crs(CRS.from_epsg(4326), ds.wrf_projection.item(), always_xy=True)
    x, y = trf.transform(long, lat)
    return ds.interp(x=x, y=y, x_stag=x, y_stag=y)
```

```{code-cell} ipython3
ds_sampled = sample_wrf_ds_at_latlon(ds, 37.773972, -122.431297)
ds_sampled
```

## Computation of desired quantities

+++

Now we have to compute the quantities [`metpy`](https://unidata.github.io/MetPy/latest/) uses for the skewT. For that we have to first quantify the [`WRF`](https://www.mmm.ucar.edu/weather-research-and-forecasting-model) data and then convert the data to the desired units.

```{code-cell} ipython3
import metpy
import metpy.calc as mpcalc
import pint_xarray


ds_sampled = ds_sampled.metpy.quantify()
ds_sampled['dew_point_temperature'] = mpcalc.dewpoint(
    mpcalc.vapor_pressure(ds_sampled.air_pressure, ds_sampled.QVAPOR)
).pint.to("degC")
ds_sampled['air_temperature'] = mpcalc.temperature_from_potential_temperature(
    ds_sampled.air_pressure, ds_sampled.air_potential_temperature
).pint.to("degC")
ds_sampled['air_pressure'] = ds_sampled.air_pressure.pint.to("hPa")
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
ds_sampled = ds_sampled.squeeze()

# Plot the data using normal plotting functions, in this case using
# log scaling in Y, as dictated by the typical meteorological plot
skew.plot(ds_sampled.air_pressure, ds_sampled.air_temperature, 'r', linewidth=2, label='Temperature')
skew.plot(
    ds_sampled.air_pressure, ds_sampled.dew_point_temperature, 'g', linewidth=2, label='Dew Point Temperature'
)
skew.plot_barbs(ds_sampled.air_pressure, ds_sampled.wind_east, ds_sampled.wind_north)

# Make the plot a bit prettier
plt.xlim([-50, 30])
plt.xlabel('Temperature [C]')
plt.ylabel('Pressure [hPa]')
plt.legend().set_zorder(1)
plt.title("Skew-T plot for San Francisco")

# Show the plot
plt.show()
```
