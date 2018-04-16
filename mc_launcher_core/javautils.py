"""
Java utilities
"""
import subprocess


class JavaVersion:
    def __init__(self, version):
        self.version = version

    def version_is_atleast(self, v):
        for this, that in zip(self.version.split('.'), v.split('.')):
            if int(this) > int(that):
                return True

        return False


def unpack200(file, out, unpack200_exe):
    """
    Unpack a .pack file into <out> jarfile
    :param file: string, path to input
    :param out: string, path to output
    :param unpack200_exe: string, path to the unpack200 executable file
    :return: int, unpack200 return code
    """
    p = subprocess.Popen([
        unpack200_exe,
        file,
        out
    ])
    return p.wait()


def version_at(path):
    """
    Gets the Java version installed at path
    :param path: string
    :return: JavaVersion
    """
