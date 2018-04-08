"""
All the web requests related to installing a version of Minecraft
"""
from urllib.error import URLError, HTTPError
from mc_launcher_core.web.util import chunked_file_download


MINECRAFT_VERSIONS_ROOT = "https://s3.amazonaws.com/Minecraft.Download/versions"


def save_minecraft_jar(mcversion, path):
    """
    Downloads and saves the Minecraft.jar (from Mojang source) into path
    :param mcversion: string, e.g. "1.7.10", "18w14b"
    :param path: string, absolute path to the location where this file should be saved
    :return: None
    """
    url = "{0}/{1}/{1}.jar".format(MINECRAFT_VERSIONS_ROOT, mcversion)

    chunked_file_download(url, path)

