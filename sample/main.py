import requests

from requests import Request, Session
from request_miner import process_request
from requests.exceptions import RequestException

session = requests.Session()
get_req = Request(method="GET", url="https://www.google.com").prepare()
process_request(
    get_req,
    session,
    backoff_type = "expo", # default is constant, but you can override with existing backoff functions or your own
    max_tries = 3, # max tries of a single request
    max_time = 10, # max time of a request
    exception = RequestException, # exception types that can be handled
    raise_on_giveup = True # if you want to raise the exception on giveup
)