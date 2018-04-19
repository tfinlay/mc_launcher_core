"""
Future note: if this stops working in future, switch to https://files.minecraftforge.net/maven/net/minecraftforge/forge/promotions.json as promotions source
"""
import base64
import hashlib
import time
import os
import json
import urllib.request, urllib.error
import logging
from mc_launcher_core.web.util import chunked_file_download

logger = logging.getLogger(__name__)

FORGE_PROMOTION_URL = "https://files.minecraftforge.net/maven/net/minecraftforge/forge/promotions_slim.json"
_forge_promotions_maybe = None


def _get_forge_promotions():
    """
    Downloads the Forge promotions and saves them into _forge_promotions_maybe
    :return: None
    """
    global _forge_promotions_maybe
    logger.debug("Getting forge promotions")
    if _forge_promotions_maybe is not None:
        logger.debug("Already downloaded promotions")
    else:
        logger.info("Attempting to fetch forge promotions...")
        try:
            response = urllib.request.urlopen(FORGE_PROMOTION_URL)
        except urllib.error.URLError as ex:
            logger.error("Failed to fetch Forge promotions, URLError: {} occurred".format(ex))
            raise
        else:
            if response.getcode() == 200:
                _forge_promotions_maybe = json.load(response)
            else:
                logger.warning("Failed to load Minecraft releases, maybe the server is temporarily offline?")
                raise Exception("Bad response code when getting Forge promotions: {}".format(response.getcode()))


def _get_forge_version_url(mcversion, forgeversion, forge_homepage):
    """
    Gets a Forge download URL for a specific Minecraft and Forge version
    :param mcversion: string
    :param forgeversion: string
    :param forge_homepage: string, URL to Forge homepage as specified in promotions JSON
    :return: string
    """
    if mcversion == "1.7.10":  # weird thing happens with 1.7.10 download URLs making them different from all the rest
        forgeversion += "-1.7.10"

    return forge_homepage + "{}-{}/".format(mcversion, forgeversion) + "forge-{}-{}-installer.jar".format(mcversion, forgeversion)


def download_forge_installer(mcversion, tempdir):
    """
    Downloads the appropriate Forge installer for mcversion into tempdir
    :param mcversion: string, e.g. "1.7.10"
    :param tempdir: string, path to temporary storage directory (remember to clear this after forge has been installed)
    :return: string, path to installer
    """
    if _forge_promotions_maybe is None:
        _get_forge_promotions()

    query_key = "{}-recommended".format(mcversion)
    backup_query_key = "{}-latest".format(mcversion)

    logger.debug("Getting Forge version with key: {}, and backup_key: {}".format(query_key, backup_query_key))

    forge_version = _forge_promotions_maybe["promos"].get(query_key) or _forge_promotions_maybe["promos"].get(backup_query_key)

    logger.debug("Got Forge version of: {}".format(forge_version))

    hash = hashlib.sha224()
    hash.update(str(time.time()).encode())

    forge_save_path = os.path.join(
        tempdir,
        base64.b64encode(hash.digest()).decode().replace("/", "_"),
        "forge_installer_{}.jar".format(mcversion)
    )

    forge_url = _get_forge_version_url(
        mcversion,
        forge_version,
        _forge_promotions_maybe["homepage"]
    )

    logger.info("Downloading Forge version: {} from url: {} into: {}".format(forge_version, forge_url, forge_save_path))

    if os.path.isfile(forge_save_path):
        os.remove(forge_save_path)

    chunked_file_download(
        forge_url,
        forge_save_path
    )

    return forge_save_path


if __name__ == "__main__":
    print(_get_forge_version_url("1.12.2", "14.23.3.2655", "http://files.minecraftforge.net/maven/net/minecraftforge/forge/"))
    print(_get_forge_version_url("1.7.10", "10.13.4.1558", "http://files.minecraftforge.net/maven/net/minecraftforge/forge/"))

    print(os.getenv("TEMP"))

    download_forge_installer("1.7.10", os.path.join(os.getenv("TEMP"), "tfff1", "SimpleModInstaller"))
