import xwrf


def test_xwrf_version_report():
    info = xwrf.show_versions(as_dict=True)
    assert set(info.keys()) == {'sys_info', 'packages_info'}
    assert info['packages_info']['xwrf'] == xwrf.__version__
