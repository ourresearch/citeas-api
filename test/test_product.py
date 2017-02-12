import unittest
from nose.tools import nottest
from nose.tools import assert_equals
from nose.tools import assert_not_equals
from nose.tools import assert_true
import requests
from ddt import ddt, data
import requests_cache

from software import Software

requests_cache.install_cache('my_requests_cache', expire_after=60*60*24*7)  # expire_after is in seconds

test_urls = [
    ("https://github.com/pvlib/pvlib-python", "10.5281/zenodo.50141", "Will Holmgren et al., 2016. pvlib-python: 0.3.1. Available at: https://doi.org/10.5281/zenodo.50141."),
    ("https://github.com/gcowan/hyperk", "10.5281/zenodo.160400", "G. A. Cowan, 2016. Gcowan/Hyperk: Mcp Data Processing Code. Available at: https://doi.org/10.5281/zenodo.160400."),
    ("https://github.com/NSLS-II-XPD/xpdView", "10.5281/zenodo.60479", "Caleb Duff & Joseph Kaming-Thanassi, 2016. xpdView: xpdView initial release. Available at: https://doi.org/10.5281/zenodo.60479."),
]



@ddt
class MyTestCase(unittest.TestCase):
    _multiprocess_can_split_ = True

    @data(*test_urls)
    def test_the_urls(self, test_data):
        (url, doi, expected) = test_data
        my_software = Software()
        my_software.url = url
        my_software.set_citation()
        assert_equals(my_software.citation, expected)

    @data(*test_urls)
    def test_the_dois(self, test_data):
        (url, doi, expected) = test_data
        my_software = Software()
        my_software.doi = doi
        my_software.set_citation()
        assert_equals(my_software.citation, expected)
