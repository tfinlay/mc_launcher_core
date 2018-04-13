import zipfile
import os.path
import json


def get_lib_path_for_forge(path):
    """
    :param path: string, e.g. "net.minecraftforge:forge:1.7.10-10.13.4.1614-1.7.10"
    :return: list<string>
    """
    p = path.split(":")
    start = p.pop(0).split(".")
    p = start + p

    return p


def install_forge_from_jar(installerjar_path, libsdir):
    """
    Install Forge from a Jar Forge installer into bindir
    :param installerjar_path: string, path
    :param libsdir: string, path to libraries directory
    :return: dict forge install_profile.json parsed data
    """
    with zipfile.ZipFile(installerjar_path) as f:
        d = json.loads(f.read("install_profile.json").decode())

        # extract the modloader to the right place
        out_path = os.path.join(
            libsdir,
            *get_lib_path_for_forge(d["install"]["path"])[:-1],
            d["install"]["target"],
            d["install"]["filePath"]
        )

        f.extract(
            d["install"]["filePath"],
            out_path
        )

    return d
