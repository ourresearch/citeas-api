from flask import Flask

import logging
import sys
import os
import requests
import requests_cache
import bugsnag
from bugsnag.flask import handle_exceptions

requests_cache.install_cache('my_requests_cache', expire_after=60*60*24*1)  # expire_after is in seconds
requests_cache.clear()

# set up logging
# see http://wiki.pylonshq.com/display/pylonscookbook/Alternative+logging+configuration
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='%(name)s - %(message)s'
)
logger = logging.getLogger("citeas")

libraries_to_mum = [
    "requests.packages.urllib3",
    "requests.packages.urllib3.connectionpool",
    "requests_oauthlib",
    "urllib3.connectionpool"
    "stripe",
    "oauthlib",
    "boto",
    "citeproc",
    "newrelic",
    "RateLimiter",
]

for a_library in libraries_to_mum:
    the_logger = logging.getLogger(a_library)
    the_logger.setLevel(logging.WARNING)
    the_logger.propagate = True

requests.packages.urllib3.disable_warnings()

app = Flask(__name__)

# bugsnag for error reporting
bugsnag.configure(
  api_key = os.environ.get('BUGSNAG_API_KEY', ''),
  project_root = app.root_path,
)
handle_exceptions(app)
