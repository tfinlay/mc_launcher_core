import os.path
import json
from mc_launcher_core.web.util import get_download_url_for_minecraft_lib
from mc_launcher_core.forge_utils.install import get_lib_path_for_forge, install_forge_from_jar


def convert_old_style_lib(lib):
    """
    converts an old-style library into a new-style one
    :param lib: dict
    :return: dict
    """
    DEFAULT_MOJANG_BASE_URL = "https://libraries.minecraft.net/"

    path = '/'.join(get_lib_path_for_forge(lib["name"]))

    url = get_download_url_for_minecraft_lib(lib["name"], DEFAULT_MOJANG_BASE_URL)#(lib["url"] if lib.get("url") else DEFAULT_MOJANG_BASE_URL))

    return dict(
        name=lib["name"],
        downloads=dict(
            artifact=dict(
                size=0,
                sha1="UNKNOWN",
                path=path,
                url=url
            )
        )
    )


def merge_forge_library_requirements(forgejson, bindir):
    """
    merges Forge libraries into the new format for minecraft.json - DOESN'T ACTUALLY INSTALL ANYTHING
    :param forgejson: dict, install_profile.json from forge installer jar
    :param bindir: string
    :return: None
    """
    print(forgejson)

    with open(os.path.join(bindir, "minecraft.json")) as f:
        mcjson = json.load(f)

    for lib in forgejson["versionInfo"]["libraries"]:
        if lib.get("clientreq") is True:
            mcjson["libraries"].append(convert_old_style_lib(lib))

    with open(os.path.join(bindir, "minecraft.json"), 'w') as f:
        json.dump(mcjson, f)


def install_forge(p, libsdir, bindir):
    """
    Install forge with Jar installer at <p>
    :param p: string, path
    :param libsdir: string, path
    :param bindir: string, path
    :return: None
    """
    # extract key Forge data
    data = install_forge_from_jar(p, libsdir)

    # merge Forge data
    merge_forge_library_requirements(data, bindir)
