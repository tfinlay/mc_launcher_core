import os.path
import json
import logging
import platform
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from mc_launcher_core.exceptions import InvalidLoginError, InvalidMinecraftVersionError
from mc_launcher_core.web.install import save_minecraft_jar
from mc_launcher_core.web.util import chunked_file_download

MINECRAFT_VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"


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
        return json.loads(urlopen(request).read().decode('utf-8'))
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

'''
class MinecraftVersion:
    def __init__(self, j):
        self.json = j

        self.id = j["id"]
        self.type = j["type"]
        self.time = j["time"]
        self.release_time = j["releaseTime"]
        self.meta_url = j["url"]
'''


def get_available_minecraft_versions():
    """
    Gets the list of all available Minecraft versions
    :return: dict<see JSON at URL>
    """
    request = Request(MINECRAFT_VERSION_MANIFEST_URL)
    try:
        return json.loads(urlopen(request).read().decode('utf-8'))
    except HTTPError as ex:
        logger.error("An HTTP error occurred (code: {})".format(ex.code))
        raise
    except URLError as ex:
        if ex.errno == 11001:
            logger.error("request failed due to URLError 11001. This can happen when the device is not connected to the internet.")
        raise


def save_minecraft_assets(assetsdir, bindir):
    """
    Saves the asset files into assetsdir, based off minecraft.json in bindir
    :param assetsdir: string
    :param bindir: string
    :return: None
    """
    with open(os.path.join(bindir, "minecraft.json")) as f:
        assets = json.load(f)["libraries"]

    system = platform.system().lower()

    for lib in assets:
        classifier_to_download = None
        if lib.get("natives"):
            # this library has natives attached to it
            classifier_to_download = lib["natives"][system]

          


def save_minecraft_bin(bindir, mcversion):
    """
    Saves the files usually in Minecrafts bin directory, into bindir
    :param bindir: string, path
    :param mcversion: string, e.g. "1.7.10", "18w14b"
    :return: None
    """
    manifest = get_available_minecraft_versions()

    for version in manifest["versions"]:
        if version["id"] == mcversion:
            version_data = version
            break
    else:
        raise InvalidMinecraftVersionError(mcversion)

    # save the minecraft jar
    save_minecraft_jar(mcversion, os.path.join(bindir, 'minecraft.jar'))

    # save the minecraft json
    chunked_file_download(version["url"], os.path.join(bindir, 'minecraft.json'))

    with open(os.path.join(bindir, 'minecraft.json')) as f:
        asset_index_data = json.load(f)["assetIndex"]

    for asset in asset_index_data:




if __name__ == "__main__":
    from pprint import pprint as pp
    pp(authenticate_user(input("username? "), input("password? "), True))
