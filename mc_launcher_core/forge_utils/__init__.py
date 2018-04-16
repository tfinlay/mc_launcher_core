import os.path
import json
from mc_launcher_core.web.util import get_download_url_for_minecraft_lib, get_download_url_path_for_minecraft_lib
from mc_launcher_core.forge_utils.install import install_forge_from_jar


def convert_old_style_lib(lib, existence_guaranteed=False):
    """
    converts an old-style library into a new-style one
    :param lib: dict
    :param existence_guaranteed: bool, whether or not to specify the fu_ flag so the mc launcher doesn't attempt to install this one
    :return: dict
    """
    DEFAULT_MOJANG_BASE_URL = "https://libraries.minecraft.net/"

    path = get_download_url_path_for_minecraft_lib(lib["name"])

    url = get_download_url_for_minecraft_lib(lib["name"], (lib["url"] if lib.get("url") else DEFAULT_MOJANG_BASE_URL))

    xz_unpack = False
    alt_url = None
    if lib.get("url") and not existence_guaranteed:  # coming from Forge mirror
        #path += ".pack"
        xz_unpack = True
        alt_url = url
        url += ".pack.xz"

    return dict(
        name=lib["name"],
        extract=dict(
            fu_xz_unpack=xz_unpack
        ),
        fu_existence_guaranteed=existence_guaranteed,  # if True, don't try to download using data below:
        downloads=dict(
            artifact=dict(
                size=0,
                sha1="UNKNOWN",
                path=path,
                url=url,
                fu_alt_url=alt_url
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
        if lib.get("clientreq") in (True, None):
            if not lib["name"].startswith("net.minecraftforge:forge"):
                mcjson["libraries"].append(convert_old_style_lib(lib))
            else:
                # special Forge things...
                mcjson["libraries"].append(convert_old_style_lib(lib, existence_guaranteed=True))

    mcjson["mainClass"] = forgejson["versionInfo"]["mainClass"]
    mcjson["minecraftArguments"] = forgejson["versionInfo"]["minecraftArguments"]

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
