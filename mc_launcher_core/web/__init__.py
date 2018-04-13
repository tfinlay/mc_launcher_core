import os.path
import json
import logging
import platform
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from mc_launcher_core.exceptions import InvalidLoginError, InvalidMinecraftVersionError
from mc_launcher_core.util import extract_file_to_directory, java_esque_string_substitutor, is_os_64bit, get_url_filename, do_get_library
from mc_launcher_core.web.install import save_minecraft_jar
from mc_launcher_core.web.util import chunked_file_download, get_download_url_path_for_minecraft_lib

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


def save_minecraft_libs(libdir, nativesdir, libraries):
    """
    Saves the library files into libdir, based off minecraft.json in bindir
    :param libdir: string
    :param nativesdir: string, where to put natives
    :param libraries: list<library>
    :return: None
    """
    '''
    def old_style_library_saver(lib):
        """
        Save old-style (e.g. Forge-style) libraries
        :param lib: dict<name:string, url: string, clientreq: bool>
        :return: None
        """
        DEFAULT_MOJANG_BASE_URL = "https://libraries.minecraft.net/"

        print(lib)
        url_path = get_download_url_path_for_minecraft_lib(lib["name"])
        url = (lib["url"] if lib.get("url") else DEFAULT_MOJANG_BASE_URL) + url_path

        logger.debug("Determined Download URL for old-style lib: {} to be: {}".format(lib["name"], url))
    '''

    system = platform.system().lower()

    for lib in libraries:
        logger.info("Checking library: {}".format(lib["name"]))
        '''if lib.get("clientreq") is True:
            # this is old-style and required for the client
            old_style_library_saver(lib)
            continue
        elif lib.get("serverreq") is not None or lib.get("downloads") is None:
            # old-style but we don't need to download it
            continue'''

        if not do_get_library(lib.get("rules")):
            logger.info("No need to download.")
            continue

        native_classifier_to_download = None
        logger.debug("Checking for natives...")
        if lib.get("natives"):
            logger.info("Checking for natives for {}bit system".format(("64" if is_os_64bit() else "32")))
            # this library has natives attached to it
            native_classifier_to_download = lib["natives"].get(system)
            if native_classifier_to_download is not None:
                native_classifier_to_download = java_esque_string_substitutor(
                    native_classifier_to_download,
                    arch=("64" if is_os_64bit() else "32")
                )
                logger.info("Found native")

        if native_classifier_to_download is not None:
            filepath = os.path.join(
                nativesdir,
                get_url_filename(lib["downloads"]["classifiers"][native_classifier_to_download]["path"])  # file name
            )
            logger.debug("Downloading native to: '{}'".format(filepath))

            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            chunked_file_download(
                lib["downloads"]["classifiers"][native_classifier_to_download]["url"],
                filepath
            )

            logger.debug("download complete")

            if lib.get("extract"):
                exclude_from_extract = lib["extract"].get("exclude")
                logger.debug("extracting files...")

                # extract the file
                extract_file_to_directory(
                    filepath,
                    os.path.dirname(filepath),
                    exclude_from_extract
                )

                # clean up afterwards
                os.remove(filepath)
                logger.debug("done")

        if lib["downloads"].get("artifact"):
            filepath = os.path.join(
                libdir,
                *lib["downloads"]["artifact"]["path"].split("/")
            )
            logger.debug("Checking if need to download artifact to: {}".format(filepath))
            if not os.path.isfile(filepath):
                # get that file, cos it's not there yet
                os.makedirs(os.path.dirname(filepath), exist_ok=True)

                logger.info("Downloading artifact from: {} to: {}".format(lib["downloads"]["artifact"]["url"], filepath))

                chunked_file_download(
                    lib["downloads"]["artifact"]["url"],
                    filepath
                )
                logger.info("download complete")


def check_minecraft_assets(assets_index_path, assetsdir):
    """
    THIS MIGHT NOT BE NEEDED AFTER ALL!

    Checks if the assets are there, if not, download them
    :param assets_index_path: string, path to the assets index file
    :param assetsdir: string, path to assets directory
    :return: None
    """
    with open(assets_index_path, 'r') as f:
        assets_index = json.load(f)

    for asset in assets_index:
        # download assets, see: http://wiki.vg/Game_files
        pass


def download_minecraft(bindir, assetsdir, libdir, nativesdir, mcversion):
    """
    Saves all of the files required for Minecraft to run
    :param bindir: string, path
    :param assetsdir: string, path
    :param libdir: string, path (usually <assetsdir>/../libraries
    :param nativesdir: string, path to the where natives should be saved (usually <bindir>/natives)
    :param mcversion: string, e.g. "1.7.10", "18w14b"
    :return: None
    """
    logger.info("Installing Minecraft version: '{}' with bindir: '{}', assetsdir: '{}', libdir: '{}'".format(mcversion, bindir, assetsdir, libdir))

    logger.info("Checking if files are already present...")

    if not os.path.isfile(os.path.join(bindir, "minecraft.jar")) or not os.path.isfile(os.path.join(bindir, "minecraft.json")):
        logger.info("Failed to find minecraft.jar or minecraft.json, downloading one of both")
        logger.debug("Searching for version data")
        manifest = get_available_minecraft_versions()

        for version in manifest["versions"]:
            if version["id"] == mcversion:
                logger.debug("Found Minecraft version data")
                version_data = version
                break
        else:
            logger.critical("Failed to file version data for Minecraft Version: {}".format(mcversion))
            raise InvalidMinecraftVersionError(mcversion)

        # save the minecraft jar
        if not os.path.isfile(os.path.join(bindir, "minecraft.jar")):
            logger.info("Saving Minecraft jar...")
            save_minecraft_jar(mcversion, os.path.join(bindir, 'minecraft.jar'))

        # save the minecraft json
        if not os.path.isfile(os.path.join(bindir, "minecraft.json")):
            logger.info("Saving Minecraft JSON")
            chunked_file_download(version["url"], os.path.join(bindir, 'minecraft.json'))

    logger.info("Loading Minecraft data")
    # save libraries
    with open(os.path.join(bindir, 'minecraft.json')) as f:
        minecraft_data = json.load(f)

    logger.info("Saving Minecraft libraries")
    save_minecraft_libs(libdir, nativesdir, minecraft_data["libraries"])

    assets_index_path = os.path.join(
        assetsdir,
        "indexes",
        "{}.json".format(mcversion)  # Minecraft will look for this using the --assetIndex flag specified, for compliance <mcversion> should be specified there
    )

    if not os.path.isfile(assets_index_path):
        logger.info("Saving assets index into: {}".format(assets_index_path))
        # download assets index
        chunked_file_download(
            minecraft_data["assetIndex"]["url"],
            assets_index_path
        )

    check_minecraft_assets(
        assets_index_path,
        assetsdir
    )

    return

    #check_minecraft_assets(
    #    assets_index_path,
    #    assetsdir
    #)
