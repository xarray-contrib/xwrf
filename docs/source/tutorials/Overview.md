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

+++ {"tags": []}

# `xWRF` overview

+++

`xWRF` is a package designed to make the post-processing of [`WRF`](https://www.mmm.ucar.edu/weather-research-and-forecasting-model) output data more pythonic. It's aim is to smooth the rough edges around the unique, non CF-compliant [`WRF`](https://www.mmm.ucar.edu/weather-research-and-forecasting-model) output data format and make the data accessible to utilities like [`dask`](https://dask.org/) and the wider [Pangeo](https://pangeo.io/) universe.

It is built as an [Accessor](https://xarray.pydata.org/en/stable/internals/extending-xarray.html) on top of [`xarray`](https://xarray.pydata.org/en/stable/index.html), providing a very simple user interface.

+++ {"tags": []}

## Examining the data

+++

When opening up a normal [`WRF`](https://www.mmm.ucar.edu/weather-research-and-forecasting-model) output file with the simple [`xarray`](https://docs.xarray.dev/en/stable/#) netcdf backend, one can see that it does not provide a lot of useful information.

```{code-cell} ipython3
import xwrf

ds_old = xwrf.tutorial.open_dataset("wrfout")
ds_old
```

While all variables are present, e.g. the information about the projection is still in the metadata and also for some fields, there are non-[`metpy`](https://unidata.github.io/MetPy/latest/index.html) compliant units attributes.

So let's try to use the standard `xWRF.postprocess()` function in order to make this information useable.

```{code-cell} ipython3
ds_new = xwrf.tutorial.open_dataset("wrfout").xwrf.postprocess()
ds_new
```

As you see, `xWRF` added some coordinate data, reassigned some dimensions and generally increased the amount of information available in the dataset.

+++

## Projection treatment

+++

`xWRF` has determined the correct projection from the netCDF metadata and has added a `wrf_projection` variable to the dataset storing the [`pyproj`](https://pyproj4.github.io/pyproj/stable/) projection object.

```{code-cell} ipython3
ds_new['wrf_projection'].item()
```

Using this projection `xWRF` has also calculated the regular model grid, which the WRF simulation is performed on and which can be used for e.g. bilinear interpolation.

```{code-cell} ipython3
ds_new[['x', 'y']]
```

## Attribute changes

+++

`xWRF` adds additional attributes to variables in order to make them [CF](https://cfconventions.org/)- and [COMODO](https://web.archive.org/web/20160417032300/http://pycomodo.forge.imag.fr/norm.html)-compliant. It also amends `unit` attributes to work with [`metpy`](https://unidata.github.io/MetPy/latest/index.html) units, enabling a seamless integration with the [Pangeo](https://pangeo.io/) software stack.

Here, for example the x-wind component gets the correct [CF](https://cfconventions.org/) `standard_name` and a [COMODO](https://web.archive.org/web/20160417032300/http://pycomodo.forge.imag.fr/norm.html) `grid_mapping` attribute indicating the respective projection.

```{code-cell} ipython3
ds_old['U'].attrs, ds_new['U'].attrs
```

Also, the `units` attribute of the `PSN` variable was cleaned up to conform to [`metpy`](https://unidata.github.io/MetPy/latest/index.html) unit conventions.

:::{note}
As of now, unit translations are implemented on a manual basis, so please raise an [issue](https://github.com/xarray-contrib/xwrf/issues/new?assignees=&labels=bug%2Ctriage&template=bugreport.yml&title=%5BBug%5D%3A+) with us if you encounter any problems in this regard. In the future, this will be implemented in a more structured manner.
:::

```{code-cell} ipython3
ds_old['PSN'].attrs['units'], ds_new['PSN'].attrs['units']
```

```{code-cell} ipython3
import metpy

try:
    ds_old['PSN'].metpy.quantify()
except metpy.units.UndefinedUnitError as e:
    print(e)
ds_new['PSN'].metpy.quantify()
```

## Diagnostic variables

+++

Because some [`WRF`](https://www.mmm.ucar.edu/weather-research-and-forecasting-model) output fields are quite raw, essential diagnostic variables like `air_pressure` or `air_potential_temperature` are missing. Also wind fields are natively in grid-space and not oriented in west-east, north-south direction, so the `wind_east` and `wind_north` fields are added. These useful variables get added by `xWRF` by default. Users can choose to keep the fields after the computation of diagnostics is done by using `.xwrf.postprocess(drop_diagnostic_variable_components=False)`, however grid-relative winds are always retained.

```{code-cell} ipython3
ds_new['air_pressure']
```

```{code-cell} ipython3
ds_new['wind_east']
```
