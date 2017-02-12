import unittest
from nose.tools import nottest
from nose.tools import assert_equals
from nose.tools import assert_not_equals
from nose.tools import assert_true
import requests
from ddt import ddt, data
import requests_cache

from views import get_zenodo_doi_from_github

requests_cache.install_cache('my_requests_cache', expire_after=60*60*24*7)  # expire_after is in seconds

test_urls = [
    ("https://github.com/pvlib/pvlib-python", "http://doi.org/10.5281/zenodo.50141"),
]




@ddt
class MyTestCase(unittest.TestCase):
    _multiprocess_can_split_ = True

    @data(*test_urls)
    def test_the_urls(self, test_data):
        (url, expected) = test_data
        response = get_zenodo_doi_from_github(url)

        # print u'\n\n("{}", "{}", "{}"),\n\n'.format(my_product.doi, my_product.fulltext_url, my_product.license)
        # print u"\n\nwas looking for {}, got {}".format(fulltext_url, my_product.fulltext_url)
        # print u"doi: {}".format(doi)
        # print u"title: {}\n\n".format(my_product.best_title)
        assert_equals(expected, response)

