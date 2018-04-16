import logging
import zipfile
import os.path
import json
from mc_launcher_core.web.util import get_download_url_path_for_minecraft_lib


def install_forge_from_jar(installerjar_path, libsdir):
    """
    Install Forge from a Jar Forge installer into bindir
    :param installerjar_path: string, path
    :param libsdir: string, path to libraries directory
    :return: dict forge install_profile.json parsed data
    """
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!UNZIPPING FORGE!!!!!!!!!!!!!!!!!!!!!!")

    with zipfile.ZipFile(installerjar_path) as f:
        d = json.loads(f.read("install_profile.json").decode())

        # extract the modloader to the right place
        out_path = os.path.join(
            libsdir,
            *get_download_url_path_for_minecraft_lib(d["install"]["path"]).split("/")
        )

        print(out_path)
        print(get_download_url_path_for_minecraft_lib(d["install"]["path"]))

        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        with open(out_path, 'wb') as x:
            x.write(f.read(d["install"]["filePath"]))

        #f.extract(
        #    d["install"]["filePath"],
        #    out_path
        #)

    return d
