import backoff
import logging

from requests import Request, Session
from requests.api import request
from requests.exceptions import RequestException

logging.basicConfig(level=logging.INFO)
logging.getLogger("backoff").setLevel(logging.INFO)

def failing_request(content):
    """
    Message processor for failing request
    :param content: The content of the request.
    :return: None    
    """
    logging.error(f"Request failed {content['args'][0].method} at destination: {content['args'][0].url}")
    
    headers = {}

    for i in range(0, 2):
        for header in content['args'][i].headers.items():
            headers[header[0]] = header[1]

    logging.error(f"Request headers: {headers}")
    logging.error(f"Request body: {content['args'][0].body}")
    


def process_backoff_params(**kwargs):
    if not type(kwargs.get('backoff_type')).__name__ == "function":
        backoff_type = kwargs.pop('backoff_type', 'constant').replace("backoff.", "")
        backoff_type = getattr(backoff, backoff_type)
    else:
        backoff_type = kwargs.pop('backoff_type')
    
    backoff_conf = {
        "max_tries": kwargs.pop('max_tries', 5),
        "max_time": kwargs.pop('max_time', 10),
        "exception": kwargs.pop('exception', RequestException),
        "raise_on_giveup": kwargs.pop('raise_on_giveup', False),
    }

    if backoff_type.__name__ == "exponential":
        backoff_conf["base"] = kwargs.pop("base")
        backoff_conf["factor"] = kwargs.pop("factor")
    
    return kwargs, backoff_conf, backoff_type


def process_request(prepped_request, session=Session(), **kwargs):
    """
    Function that process a prepared request creating or using an existing session.
    :param prepped_request: The prepared request to process.
    :param session: The session to use. If not provided, a new one will be created.
    :type session: requests.Session

    :return: The response from the request.
    """

    kwargs, backoff_conf, backoff_type = process_backoff_params(**kwargs)

    @backoff.on_exception(
        backoff_type,
        **backoff_conf,
        on_giveup=failing_request
    )
    def decorated_request(prepped_request, session, **kwargs):
        req = session.send(prepped_request, **kwargs)
        req.raise_for_status()
        return req
    
    return decorated_request(prepped_request, session, **kwargs)


def mine(method="GET", url="", **kwargs):
    """
    Function that generates a prepared request and process it.
    :param method: The HTTP method to use.
    :param url: The URL to request.
    :param body: The body to use on the request.
    :param header: The header to use on the request.
    :param params: The params to use on the request.
    :param kwargs: The arguments to pass to the request.
    """
    session_kwargs = {}
    for param in [
        "backoff_type",
        "max_tries",
        "max_time",
        "exception",
        "raise_on_giveup",
        "base",
        "factor"
    ]:
        if kwargs.get(param):
            session_kwargs[param] = kwargs.pop(param)

    req = Request(method, url, **kwargs)
    prepped_request = req.prepare()
    process_request(prepped_request, **session_kwargs)
