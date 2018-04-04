import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from mc_launcher_core.exceptions import InvalidLoginError


logger = logging.getLogger(__name__)


def authenticate_user(username, password, request_user_data=False, client_token=None):
    """
    Gets client access token and clientToken.
    See: http://wiki.vg/Authentication#Response
    :param username: string
    :param password: string
    :param request_user_data: bool, whether or not to get extra client info in the response payload
    :param client_token: string, should only ever be None on first run, otherwise it should be saved and specified.
    :return: json data
    """
    AUTHENTICATION_URL = "https://authserver.mojang.com/authenticate"
    HEADERS = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    payload = dict(
        agent=dict(
            name="Minecraft",
            version=1
        ),
        username=username,
        password=password,
        requestUser=request_user_data
    )

    if client_token is not None:
        payload["clientToken"] = client_token

    request = Request(
        AUTHENTICATION_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers=HEADERS
    )

    try:
        return urlopen(request).read().decode('utf-8')
    except HTTPError as ex:
        if ex.code == 403:
            # invalid login details
            logger.warning("Login details are invalid")
            raise InvalidLoginError()
        logger.error("An HTTP error occurred (code: {})".format(ex.code))
        raise
    except URLError as ex:
        if ex.errno == 11001:
            logger.error("Login failed due to URLError 11001. This can happen when the device is not connected to the internet.")
            raise


if __name__ == "__main__":
    print(authenticate(input("username? "), input("password? "), True, "5880d0fd9985432fa13cfd7192625038"))
