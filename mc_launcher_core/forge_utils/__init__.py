import os.path
import json
from mc_launcher_core.web.util import get_download_url_path_for_minecraft_lib


def convert_old_style_lib(lib):
    """
    converts an old-style library into a new-style one
    :param lib: dict
    :return: dict
    """
    DEFAULT_MOJANG_BASE_URL = "https://libraries.minecraft.net/"

    path = get_download_url_path_for_minecraft_lib(lib["name"])
    url = (lib["url"] if lib.get("url") else DEFAULT_MOJANG_BASE_URL) + path

    



def merge_forge_library_requirements(forgejson_path, bindir):
    """
    merges Forge libraries into the new format for minecraft.json - DOESN'T ACTUALLY INSTALL ANYTHING
    :param forgejson_path: string
    :param bindir: string
    :return: None
    """
    with open(forgejson_path) as f:
        libs = json.load(f)["libraries"]

    for lib in libs:
        if lib.get("clientreq") is True:
