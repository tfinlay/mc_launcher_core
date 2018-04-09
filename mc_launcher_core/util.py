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


def do_get_library(rules):
    """
    Whether to allow a library to be downloaded
    :param rules: list
    :return: bool
    """
    if rules is None:
        return True

    action = "disallow"

    for rule in rules:
        if rule.get("os"):
            if rule["os"]["name"] == platform.system().lower():
                action = rule["action"]
        else:
            action = rule["action"]

    return action == "allow"


def get_lib_file_path(lib):
    """
    Gets a libraries file path (if it's installed at all)
    :param lib: dict
    :return: None / string
    """
    if lib.get("rules") is None or (lib.get("rules") is not None and do_get_library(lib["rules"])):
        # this one is supposed to be installed
        if lib["downloads"].get("artifact"):
            return lib["downloads"]["artifact"]["path"]


def get_required_libraries_paths(bindir):
    """
    Gets the required libraries for the minecraft in bindir (from the minecraft.json) for the hosts OS
    :param bindir: string
    :return: list<string>
    """
    libs = []

    logger.info("Loading required libraries...")
    with open(os.path.join(bindir, "minecraft.json")) as f:
        libraries = json.load(f)["libraries"]

    for lib in libraries:
        x = get_lib_file_path(lib)
        if x is not None:
            libs.append(x)

    return libs


def get_minecraft_launch_details(bindir):
    """
    Gets the required launch details for Minecraft
    :param bindir: string
    :return: dict<classpath: string, args: string, version_id: string, logging_arg: string>
    """
    file_to_get_details_from = "modloader.json" if os.path.isfile(os.path.join(bindir, "modloader.json")) else "minecraft.json"

    with open(os.path.join(bindir, file_to_get_details_from)) as f:
        j = json.load(f)

    return dict(
        classpath=j["mainClass"],
        args=j["minecraftArguments"],
        version_id=j["id"],
        version_type=j["type"]
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

        for filename in names:
            if not any((f in filename for f in exclude)):
                out_file = os.path.join(directory, get_url_filename(filename))
                logger.debug("Extracting file: {} to: {}".format(filename, out_file))
                z.extract(filename, directory)


def is_os_64bit():
    return platform.machine().endswith('64')


def escape_path_for_popen(path):
    """
    Escapes a path for use as part of a Popen command
    :param path:
    :return:
    """

if __name__ == "__main__":
    from pprint import pprint as pp
    pp(get_required_libraries_paths("../practice/bin"))

    print(java_esque_string_substitutor("${test} hi there", test="hi there"))