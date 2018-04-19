import logging
import zipfile
import os.path
import json
from mc_launcher_core.web.util import get_download_url_path_for_minecraft_lib


logger = logging.getLogger(__name__)


def install_forge_from_jar(installerjar_path, libsdir, remove_installer=False):
    """
    Install Forge from a Jar Forge installer into bindir
    :param installerjar_path: string, path
    :param libsdir: string, path to libraries directory
    :param remove_installer: bool, whether to remove the installer file after installation is complete
    :return: dict forge install_profile.json parsed data
    """
    with zipfile.ZipFile(installerjar_path) as f:
        d = json.loads(f.read("install_profile.json").decode())

        # extract the modloader to the right place
        out_path = os.path.join(
            libsdir,
            *get_download_url_path_for_minecraft_lib(d["install"]["path"]).split("/")
        )

        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        with open(out_path, 'wb') as x:
            x.write(f.read(d["install"]["filePath"]))

    if remove_installer:
        os.remove(installerjar_path)

    return d
