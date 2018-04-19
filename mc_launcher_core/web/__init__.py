import os.path
import json
import logging
import platform
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from mc_launcher_core.exceptions import InvalidLoginError, InvalidMinecraftVersionError
from mc_launcher_core.web.install import save_minecraft_jar, save_minecraft_lib, save_minecraft_asset
from mc_launcher_core.web.util import chunked_file_download, get_download_url_path_for_minecraft_lib, verify_sha1

MINECRAFT_VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"


logger = logging.getLogger(__name__)

_minecraft_versions_maybe = None  # this is populated after the first attempt to access. Access using get_available_minecraft_versions()


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


def get_available_minecraft_versions():
    """
    Gets the list of all available Minecraft versions
    :return: dict<see JSON at URL>
    """
    global _minecraft_versions_maybe
    if _minecraft_versions_maybe is None:
        request = Request(MINECRAFT_VERSION_MANIFEST_URL)
        try:
            _minecraft_versions_maybe = json.loads(urlopen(request).read().decode('utf-8'))
            return _minecraft_versions_maybe
        except HTTPError as ex:
            logger.error("An HTTP error occurred (code: {})".format(ex.code))
            raise
        except URLError as ex:
            if ex.errno == 11001:
                logger.error("request failed due to URLError 11001. This can happen when the device is not connected to the internet.")
            raise
    else:
        return _minecraft_versions_maybe


def save_minecraft_libs(libdir, nativesdir, libraries, raise_on_hash_mismatch=False):
    """
    Saves the library files into libdir, based off minecraft.json in bindir
    :param libdir: string
    :param nativesdir: string, where to put natives
    :param libraries: list<library>
    :param raise_on_hash_mismatch: bool, whether to raise an exception when hashes don't match
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
        save_minecraft_lib(lib, libdir, nativesdir, raise_on_hash_mismatch)


def save_minecraft_assets(assets_index_path, assetsdir, raise_on_hash_mismatch=False):
    """
    Checks if the assets are there, if not, download them
    :param assets_index_path: string, path to the assets index file
    :param assetsdir: string, path to assets directory
    :param raise_on_hash_mismatch: bool
    :return: None
    """
    with open(assets_index_path, 'r') as f:
        assets_index = json.load(f)

    for asset in assets_index["objects"].keys():
        # download assets, see: http://wiki.vg/Game_files
        save_minecraft_asset(assets_index["objects"][asset], asset, assetsdir, raise_on_hash_mismatch)


def download_minecraft_bin(bindir, mcversion, raise_on_hash_mismatch=False):
    """
    Downloads minecraft.jar and minecraft.json into the Minecraft bin directory
    :param bindir: string, path to the bin directory
    :param mcversion: string, e.g. "1.7.10", "18w14b"
    :param raise_on_hash_mismatch: bool
    :return: None
    """
    if not os.path.isfile(os.path.join(bindir, "minecraft.jar")) or not os.path.isfile(os.path.join(bindir, "minecraft.json")):
        logger.info("Failed to find minecraft.jar or minecraft.json, downloading one or both")
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

        # save the minecraft json
        if not os.path.isfile(os.path.join(bindir, "minecraft.json")):
            logger.info("Saving Minecraft JSON")
            chunked_file_download(version["url"], os.path.join(bindir, 'minecraft.json'))

        with open(os.path.join(bindir, "minecraft.json"), 'r') as f:
            hash = json.load(f)["downloads"]["client"]["sha1"]

        # save the minecraft jar
        if not os.path.isfile(os.path.join(bindir, "minecraft.jar")):
            logger.info("Saving Minecraft jar...")
            save_minecraft_jar(mcversion, os.path.join(bindir, 'minecraft.jar'), hash, raise_on_hash_mismatch)


def download_minecraft(bindir, assetsdir, libdir, nativesdir, mcversion, raise_on_hash_mismatch=False):
    """
    Saves all of the files required for Minecraft to run
    :param bindir: string, path
    :param assetsdir: string, path
    :param libdir: string, path (usually <assetsdir>/../libraries
    :param nativesdir: string, path to the where natives should be saved (usually <bindir>/natives)
    :param mcversion: string, e.g. "1.7.10", "18w14b"
    :param raise_on_hash_mismatch: bool
    :return: None
    """
    logger.info("Installing Minecraft version: '{}' with bindir: '{}', assetsdir: '{}', libdir: '{}', raise_on_hash_mismatch: '{}'".format(mcversion, bindir, assetsdir, libdir, raise_on_hash_mismatch))

    logger.info("Installing Binaries and core data...")
    download_minecraft_bin(bindir, mcversion, raise_on_hash_mismatch)

    logger.info("Loading Minecraft data")
    # save libraries
    with open(os.path.join(bindir, 'minecraft.json')) as f:
        minecraft_data = json.load(f)

    logger.info("Saving Minecraft libraries")
    save_minecraft_libs(libdir, nativesdir, minecraft_data["libraries"], raise_on_hash_mismatch)

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

    save_minecraft_assets(
        assets_index_path,
        assetsdir,
        raise_on_hash_mismatch
    )

    return

    #check_minecraft_assets(
    #    assets_index_path,
    #    assetsdir
    #)
