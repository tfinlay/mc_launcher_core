"""
web utilities
"""
import os
import hashlib
from urllib import request


def chunked_download(url, stream, chunk_size=(16*1024)):
    """
    download from URL in chunks, and write to a stream
    :param url: string
    :param stream: File / writable, anything that can be written to (NOTE: files should be opened with 'wb' parameter
    :param chunk_size: int, size of chunks to read
    :return: None
    """
    response = request.urlopen(url)
    while True:
        chunk = response.read(chunk_size)
        if not chunk:
            break

        stream.write(chunk)


def chunked_file_download(url, path, chunk_size=(16*1024), makedirs=True):
    """
    download from URL in chunks, and write to a file
    :param url: string
    :param path: string, absolute path to file
    :param chunk_size: int, size of chunks to read
    :param makedirs: bool, whether or not to make the directories required for this file
    :return: None
    """
    if makedirs:
        os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, 'wb') as f:
        chunked_download(url, f, chunk_size)


def verify_sha1(file, hash):
    """
    Verify that file has the right hash
    :param file: string, absolute path
    :param hash: string
    :return: bool
    """
    hasher = hashlib.sha1()
    with open(file, 'rb') as f:
        hasher.update(f.read())

    return hasher.hexdigest() == hash


def get_download_url_path_for_minecraft_lib(libname):
    """
    Gets the download path for a Minecraft library based off its name
    :param libname: string
    :return: string
    """
    pieces = libname.split(":")

    # split the start bit
    start = pieces.pop(0)
    pieces = start.split(".") + pieces

    pieces.append("{}-{}.jar".format(pieces[-2], pieces[-1]))

    return '/'.join(pieces)


def get_download_url_for_minecraft_lib(libname, base_url="https://libraries.minecraft.net/"):
    # TODO: probably this shouldn't exist
    """
    gets the download URL for a Minecraft library based off its name
    :param libname: string
    :param base_url: string, WITH A TRAILING '/', the base URL (including protocol etc.) of the site to download from
    :return: string
    """
    return base_url + get_download_url_path_for_minecraft_lib(libname)


class ForgivingDict(dict):
    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError:
            return None


if __name__ == "__main__":
    print(get_download_url_for_minecraft_lib("net.minecraft:launchwrapper:1.12"))