import pytest
import xarray as xr
from xarray import DataArray

from xwrf import tutorial

network = pytest.mark.network


@network
class TestLoadDataset:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.testfile = 'dummy'

    def test_download_from_github(self, tmp_path) -> None:
        cache_dir = tmp_path / tutorial._default_cache_dir_name
        ds = tutorial.open_dataset(self.testfile, cache_dir=cache_dir).load()
        dummy = DataArray(range(5), name='dummy').to_dataset()
        xr.assert_identical(ds, dummy)

    def test_download_from_github_load_without_cache(self, tmp_path, monkeypatch) -> None:
        cache_dir = tmp_path / tutorial._default_cache_dir_name

        ds_nocache = tutorial.open_dataset(self.testfile, cache=False, cache_dir=cache_dir).load()
        ds_cache = tutorial.open_dataset(self.testfile, cache_dir=cache_dir).load()
        xr.assert_identical(ds_cache, ds_nocache)
