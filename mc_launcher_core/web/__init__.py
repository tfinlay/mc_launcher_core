import os.path
import json
import logging
import platform
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from mc_launcher_core.exceptions import InvalidLoginError, InvalidMinecraftVersionError
from mc_launcher_core.util import extract_file_to_directory, java_esque_string_substitutor, is_os_64bit
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


def do_get_library(rules):
    """
    Whether to allow assets to be downloaded
    :param rules: list
    :return: bool
    """
    if rules is None:
        return True

    action = "disallow"

    for rule in rules:
        if rule.get("os"):
            if rule["os"]["name"] == platform.system().lower():
                action = rule["action"]
        else:
            action = rule["action"]

    return action == "allow"


def save_minecraft_libs(libdir, libraries):
    """
    Saves the library files into libdir, based off minecraft.json in bindir
    :param libdir: string
    :param libraries: list<library>
    :return: None
    """
    system = platform.system().lower()

    for lib in libraries:
        if not do_get_library(lib.get("rules")):
            continue

        classifier_to_download = None
        if lib.get("natives"):
            # this library has natives attached to it
            classifier_to_download = lib["natives"].get(system)
            if classifier_to_download is not None:
                classifier_to_download = java_esque_string_substitutor(
                    classifier_to_download,
                    arch=("64" if is_os_64bit() else "32")
                )

        if classifier_to_download is not None:
            filepath = os.path.join(
                libdir,
                *lib["downloads"]["classifiers"][classifier_to_download]["path"].split("/")
            )

            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            chunked_file_download(
                lib["downloads"]["classifiers"][classifier_to_download]["url"],
                filepath
            )

            if lib.get("extract"):
                exclude_from_extract = lib["extract"].get("exclude")

                # extract the file
                extract_file_to_directory(
                    filepath,
                    os.path.dirname(filepath),
                    exclude_from_extract
                )

        if lib["downloads"].get("artifact"):
            filepath = os.path.join(
                libdir,
                *lib["downloads"]["artifact"]["path"].split("/")
            )
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            chunked_file_download(
                lib["downloads"]["artifact"]["url"],
                filepath
            )


def check_minecraft_assets(assets_index_path, assetsdir):
    """
    Checks if the assets are there, if not, download them
    :param assets_index_path: string, path to the assets index file
    :param assetsdir: string, path to assetsdir
    :return: None
    """
    with open(assets_index_path, 'r') as f:
        assets_index = json.load(f)

    for asset in assets_index:
        # download assets, see: http://wiki.vg/Game_files
        pass


def install_minecraft(bindir, assetsdir, libdir, mcversion):
    """
    Saves all of the files required for Minecraft to run
    :param bindir: string, path
    :param assetsdir: string, path
    :param libdir: string, path (usually <assetsdir>/../libraries
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

    # save libraries
    with open(os.path.join(bindir, 'minecraft.json')) as f:
        minecraft_data = json.load(f)

    save_minecraft_libs(libdir, minecraft_data["libraries"])

    # download assets index
    chunked_file_download(
        minecraft_data["assetIndex"]["url"],
        os.path.join(assetsdir, "index.json")
    )

    check_minecraft_assets(
        os.path.join(assetsdir, "index.json"),
        assetsdir
    )
