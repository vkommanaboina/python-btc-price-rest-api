# Third-party imports...
from nose.tools import assert_true
import requests


def test_request_response():
    # Send a request to the API server and store the response.
    response = requests.get('http://127.0.0.1/btc/price')

    # Confirm that the request-response cycle completed successfully.
    assert_true(response.ok)
