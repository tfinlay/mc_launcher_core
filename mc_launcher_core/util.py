import posixpath
import platform
import os.path
import logging
import zipfile
import json

logger = logging.getLogger(__name__)


def get_url_filename(path):
    """
    gets the filename from a unix-style path (like that from minecraft.json)
    :param path: string
    :return: string
    """
    return posixpath.basename(path)


def _lib_parser_OLD(lib_json):
    """
    processes lib raw JSON and returns something actually useful from it
    :param lib_json: dict
    :return: dict<name: string, download_link: string, do_extract: bool, extract_info: dict, path: string>
    """
    name = lib_json["name"]
    download = None
    path = None
    do_extract = False
    extract_info = dict()

    if "rules" in lib_json.keys():
        # there are rules!!!
        action = "disallow"
        for rule in lib_json["rules"]:
            try:
                if rule["os"]["name"] == platform.system():
                    action = rule["action"]
            except KeyError:
                action = "allow"

        if action == "disallow":
            return None

    if "extract" in lib_json.keys():
        do_extract = True
        extract_info = lib_json["extract"]

    if "downloads" in lib_json.keys():
        if "classifiers" in lib_json["downloads"]:
            for classifier in lib_json["downloads"]["classifiers"]:
                if classifier == "natives-{}".format(platform.system().lower()):
                    download = lib_json["downloads"]["classifiers"][classifier]["url"]
                    path = lib_json["downloads"]["classifiers"][classifier]["path"]

        if download is None:  # if it hasn't been defined yet, then there's nothing special going on here
            download = lib_json["downloads"]["artifact"]["url"]
            path = lib_json["downloads"]["artifact"]["path"]

    return dict(name=name, download_link=download, do_extract=do_extract, extract_info=extract_info, path=path)


def get_required_libraries(bindir):
    """
    Gets the required libraries for the minecraft in bindir (from the minecraft.json) for the hosts OS
    :param bindir: string
    :return: list<>
    """
    libs = []

    logger.info("Loading required libraries...")
    with open(os.path.join(bindir, "minecraft.json")) as f:
        libraries = json.load(f)["libraries"]

    host_os = platform.system()

    for lib in libraries:
        x = _lib_parser(lib)
        if x is not None:
            libs.append(x)

    return libs


def get_minecraft_launch_details(bindir):
    """
    Gets the required launch details for Minecraft
    :param bindir: string
    :return: dict<classpath: string, args: string, version_id: string, logging_arg: string>
    """
    with open(os.path.join(bindir, "minecraft.json")) as f:
        j = json.load(f)

    return dict(
        classpath=j["mainClass"],
        args=j["minecraftArguments"],
        version_id=j["id"],
        logging_arg=j["logging"]["client"]["argument"]
    )


def java_esque_string_substitutor(s, **kwargs):
    """
    Substitutes in a java-style kwargs into s
    :param s: string
    :param kwargs: dict
    :return: string
    """
    i = 0
    sentence = []
    while i < len(s):
        if s[i] == "$" and i < len(s)-1 and s[i+1] == "{":
            # start reading variable name
            start_index_name = i+2
            while s[i] != "}":
                i += 1
            variable_name = s[start_index_name:i]
            sentence.append(kwargs[variable_name])
        else:
            sentence.append(s[i])

        i += 1

    return ''.join(sentence)


def extract_file_to_directory(filepath, directory, exclude=()):
    """
    extracts the root-level contents of a file into directory
    :param filepath: path
    :param directory: path
    :param exclude: list of things not to extract
    :return: None
    """
    with zipfile.ZipFile(filepath) as z:
        names = z.namelist()
        for excluded in exclude:
            logger.debug("Removing name: {} from {}".format(excluded, names))
            try:
                names.remove(excluded)
            except ValueError:
                pass

        z.extractall(directory, names)


def is_os_64bit():
    return platform.machine().endswith('64')


if __name__ == "__main__":
    from pprint import pprint as pp
    pp(get_required_libraries("../practice/bin"))

    print(java_esque_string_substitutor("${test} hi there", test="hi there"))