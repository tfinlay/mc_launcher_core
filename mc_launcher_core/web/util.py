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
    with open(file) as f:
        hasher.update(f.read())

    return hasher.hexdigest() == hash


class ForgivingDict(dict):
    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError:
            return None