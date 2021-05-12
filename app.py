import logging
import os
import sys

from flask import Flask
import requests
import requests_cache
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

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
    "urllib3.connectionpool",
    "oauthlib",
    "citeproc",
]

for a_library in libraries_to_mum:
    the_logger = logging.getLogger(a_library)
    the_logger.setLevel(logging.WARNING)
    the_logger.propagate = True

requests.packages.urllib3.disable_warnings()

# error reporting with sentry
sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[FlaskIntegration()]
)

app = Flask(__name__)
