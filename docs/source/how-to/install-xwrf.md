# Install xWRF

xWRF can be installed in three ways:

```{eval-rst}

.. tab-set::

    .. tab-item:: pip

        Using the `pip <https://pypi.org/project/pip/>`__ package manager:

        .. code:: bash

            $ python -m pip install xwrf

    .. tab-item:: conda

        Using the `conda <https://conda.io/>`__ package manager that comes with the
        Anaconda/Miniconda distribution:

        .. code:: bash

            $ conda install xwrf --channel conda-forge

    .. tab-item:: Development version

        To install a development version from source:

        .. code:: bash

            $ git clone https://github.com/xarray-contrib/xwrf
            $ cd xwrf
            $ python -m pip install -e .

```
