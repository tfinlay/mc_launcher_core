"""
All the web requests related to installing a version of Minecraft
"""
import os.path
import logging
import platform
import shutil
import unpack200
from urllib.error import URLError, HTTPError
from mc_launcher_core.exceptions import HashMatchError
from mc_launcher_core.util import extract_file_to_directory, java_esque_string_substitutor, is_os_64bit, get_url_filename, do_get_library, extract_xz_to_file
from mc_launcher_core.web.util import chunked_file_download, verify_sha1, get_sha1_hash


MINECRAFT_VERSIONS_ROOT = "https://s3.amazonaws.com/Minecraft.Download/versions"
logger = logging.getLogger(__name__)
system = platform.system().lower()


def save_minecraft_jar(mcversion, path, hash=None, raise_on_hash_mismatch=False):
    """
    Downloads and saves the Minecraft.jar (from Mojang source) into path
    :param mcversion: string, e.g. "1.7.10", "18w14b"
    :param path: string, absolute path to the location where this file should be saved
    :param hash: string, sha1 hash of the Jar file
    :param raise_on_hash_mismatch: bool
    :return: None
    """
    url = "{0}/{1}/{1}.jar".format(MINECRAFT_VERSIONS_ROOT, mcversion)

    attempt_count = 0

    while (not os.path.isfile(path) or os.path.getsize(path) == 0 or (hash is not None and not verify_sha1(path, hash))) and attempt_count <= 4:
        logger.info("Downloading Minecraft.jar from URL: {}... (attempt: {})".format(url, attempt_count))
        chunked_file_download(url, path)
        attempt_count += 1

    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        logging.critical("Failed to download Minecraft.jar")
        raise Exception("Minecraft.jar not downloading correctly (file is either 0 bytes or non-existent)")

    with open(path, 'rb') as f:
        h = get_sha1_hash(f)

    if hash is not None and h != hash:  # hashes don't match!!!
        logger.critical("Failed to download minecraft.jar. Hash of file: '{}' doesn't match expected hash: '{}'".format(
            h,
            hash
        ))

        if raise_on_hash_mismatch:
            raise HashMatchError("minecraft.jar", "Hashes don't match. Expected: '{}' but got '{}'".format(h, hash))


def save_minecraft_lib(lib, libdir, nativesdir, raise_on_hash_mismatch=False):
    """
    Save a specific Minecraft lib
    :param lib: dict, library JSON format
    :param libdir: string
    :param nativesdir: string, where to put natives
    :param raise_on_hash_mismatch: bool, whether to raise an exception when hashes don't match
    :return: None
    """
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
        return

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

        if not verify_sha1(filepath, lib["downloads"]["classifiers"][native_classifier_to_download]["sha1"]):
            logger.warning("Hashes don't match. Expected: {}".format(lib["downloads"]["classifiers"][native_classifier_to_download]["sha1"]))
            if raise_on_hash_mismatch:
                raise HashMatchError(lib, "Failed to download native as hashes don't match!")

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
        if lib.get("fu_existence_guaranteed") in (None, False):
            logger.debug("Checking if need to download artifact to: {}".format(filepath))
            if not os.path.isfile(filepath):
                # get that file, cos it's not there yet
                using_alt_url = False

                os.makedirs(os.path.dirname(filepath), exist_ok=True)

                logger.info(
                    "Downloading artifact from: {} to: {}".format(lib["downloads"]["artifact"]["url"], filepath))
                try:
                    chunked_file_download(
                        lib["downloads"]["artifact"]["url"],
                        filepath
                    )
                except HTTPError:
                    if lib["downloads"]["artifact"].get("fu_alt_url"):
                        # download from alt URL
                        using_alt_url = True
                        chunked_file_download(
                            lib["downloads"]["artifact"]["fu_alt_url"],
                            filepath
                        )

                if lib["downloads"]["artifact"].get("sha1") is not None:  # let's verify this file
                    if not verify_sha1(filepath, lib["downloads"]["artifact"]["sha1"]):
                        logger.warning("library file at: {} sha1 hash doesn't match".format(
                            lib["downloads"]["artifact"]["sha1"]
                        ))
                        if raise_on_hash_mismatch:
                            HashMatchError(lib)

                logger.info("download complete")

                if lib.get("extract") and lib["extract"].get("fu_xz_unpack") and (
                        not using_alt_url or lib["extract"].get("fu_xz_unpack_on_alt_url")):
                    logger.debug("unzipping .pack.xz file...")

                    if os.path.isfile(filepath + ".pack.xz"):
                        os.remove(filepath + ".pack.xz")

                    if os.path.isfile(filepath + ".pack"):
                        os.remove(filepath + ".pack")

                    os.rename(filepath, filepath + ".pack.xz")
                    extract_xz_to_file(
                        filepath + ".pack.xz",
                        filepath + ".pack"
                    )
                    os.remove(filepath + ".pack.xz")

                    logger.debug("Unzipped, unpacking...")
                    unpack200.unpack(
                        filepath + ".pack",
                        filepath,
                        remove_source=True
                    )

                    logger.debug("done")


def save_minecraft_asset(asset, assetname, assetsdir, raise_on_hash_mismatch=False):
    """
    Downloads an asset into the correct locations
    :param asset: dict
    :param assetsdir: string
    :param assetname: string, name of asset
    :param raise_on_hash_mismatch: bool, whether to raise if the hash doesn't match
    :return: None
    """
    MINECRAFT_RESOURCES_ROOT = "https://resources.download.minecraft.net/"

    path = (asset["hash"][:2], asset["hash"])

    filepath = os.path.join(
        assetsdir,
        "objects",
        *path
    )

    url = MINECRAFT_RESOURCES_ROOT + "/".join(path)

    logger.debug("Downloading Asset from: {} to: {}".format(url, filepath))

    # download file
    if not os.path.isfile(filepath):
        chunked_file_download(
            url,
            filepath
        )

        # check hash
        if not verify_sha1(filepath, asset["hash"]):
            logger.warning("Hash for asset doesn't match. Expected: {}".format(asset["hash"]))
            if raise_on_hash_mismatch:
                raise HashMatchError(asset, type="asset")

    # copy file
    legacy_path = os.path.join(
        assetsdir,
        "virtual",
        "legacy",
        *assetname.split("/")
    )

    if not os.path.isfile(legacy_path):
        logger.debug("Copying from: {} to legacy path: {}".format(filepath, legacy_path))

        os.makedirs(os.path.dirname(legacy_path), exist_ok=True)

        shutil.copyfile(filepath, legacy_path)
